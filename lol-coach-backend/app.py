from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import jwt
import os
import re
import secrets
import hashlib
import hmac

app = Flask(__name__)

# Configuração de CORS mais restritiva
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173').split(','),
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Rate Limiting para prevenir ataques de força bruta
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Configurações de Segurança
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///lol_coach.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Chave para criptografia de dados sensíveis
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', secrets.token_hex(32))

db = SQLAlchemy(app)

# Funções de Criptografia
def encrypt_data(data):
    """Criptografa dados sensíveis usando HMAC-SHA256"""
    if not data:
        return None
    return hmac.new(
        ENCRYPTION_KEY.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()

def verify_encrypted_data(data, encrypted):
    """Verifica se os dados correspondem ao hash criptografado"""
    if not data or not encrypted:
        return False
    return hmac.compare_digest(encrypt_data(data), encrypted)

# Validação de Senha
def validate_password_strength(password):
    """Valida a força da senha"""
    if len(password) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres"
    if not re.search(r"[A-Z]", password):
        return False, "A senha deve conter pelo menos uma letra maiúscula"
    if not re.search(r"[a-z]", password):
        return False, "A senha deve conter pelo menos uma letra minúscula"
    if not re.search(r"\d", password):
        return False, "A senha deve conter pelo menos um número"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "A senha deve conter pelo menos um caractere especial"
    return True, "Senha válida"

# Validação de Email
def validate_email(email):
    """Valida o formato do email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Sanitização de Input
def sanitize_input(text):
    """Remove caracteres potencialmente perigosos"""
    if not text:
        return text
    # Remove tags HTML e caracteres especiais perigosos
    text = re.sub(r'<[^>]*>', '', text)
    text = re.sub(r'[;&|`$]', '', text)
    return text.strip()

# Modelos de Banco de Dados
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    discord_id = db.Column(db.String(100), unique=True, nullable=True, index=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    subscription_status = db.Column(db.String(20), default='inactive')
    subscription_end_date = db.Column(db.DateTime, nullable=True)
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """Define a senha com hashing bcrypt"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    
    def check_password(self, password):
        """Verifica a senha"""
        return check_password_hash(self.password_hash, password)
    
    def is_locked(self):
        """Verifica se a conta está bloqueada"""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    def increment_failed_login(self):
        """Incrementa tentativas de login falhadas"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
        db.session.commit()
    
    def reset_failed_login(self):
        """Reseta tentativas de login falhadas"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self, include_sensitive=False):
        """Converte o usuário para dicionário"""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email if include_sensitive else self.email[:3] + '***@' + self.email.split('@')[1],
            'discord_id': self.discord_id,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'subscription_status': self.subscription_status,
            'subscription_end_date': self.subscription_end_date.isoformat() if self.subscription_end_date else None,
            'email_verified': self.email_verified,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat()
        }
        return data

class DiscordGuild(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    owner = db.relationship('User', backref='guilds')

class PaymentConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stripe_secret_key_encrypted = db.Column(db.String(255), nullable=True)
    stripe_publishable_key = db.Column(db.String(255), nullable=True)
    paypal_client_id = db.Column(db.String(255), nullable=True)
    paypal_secret_encrypted = db.Column(db.String(255), nullable=True)
    webhook_secret = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(db.Model):
    """Log de auditoria para rastrear ações importantes"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    user = db.relationship('User', backref='audit_logs')

class SecurityEvent(db.Model):
    """Registro de eventos de segurança"""
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)  # low, medium, high, critical
    description = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    user = db.relationship('User', backref='security_events')

# Criar tabelas e usuário admin
with app.app_context():
    db.create_all()
    
    admin = User.query.filter_by(username='yurifrdf').first()
    if not admin:
        admin = User(
            username='yurifrdf',
            email='admin@lolcoach.com',
            is_admin=True,
            is_active=True,
            email_verified=True,
            subscription_status='active',
            subscription_end_date=datetime(2099, 12, 31)
        )
        admin.set_password('Isacnoahjade@131312')
        db.session.add(admin)
        db.session.commit()
        print("✅ Conta de administrador criada com sucesso!")

# Funções de Log
def log_audit(user_id, action, details=None):
    """Registra uma ação no log de auditoria"""
    log = AuditLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(log)
    db.session.commit()

def log_security_event(event_type, severity, description, user_id=None):
    """Registra um evento de segurança"""
    event = SecurityEvent(
        event_type=event_type,
        severity=severity,
        description=description,
        ip_address=request.remote_addr,
        user_id=user_id
    )
    db.session.add(event)
    db.session.commit()

# Funções de Token JWT
def generate_token(user_id, token_type='access'):
    """Gera um token JWT"""
    expiration = timedelta(hours=1) if token_type == 'access' else timedelta(days=30)
    payload = {
        'user_id': user_id,
        'type': token_type,
        'exp': datetime.utcnow() + expiration,
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    """Verifica e decodifica um token JWT"""
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id'], payload.get('type', 'access')
    except jwt.ExpiredSignatureError:
        return None, 'expired'
    except jwt.InvalidTokenError:
        return None, 'invalid'

# Decoradores de Autenticação
def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            log_security_event('unauthorized_access', 'medium', 'Tentativa de acesso sem token')
            return jsonify({'error': 'Token não fornecido'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        user_id, token_type = verify_token(token)
        
        if not user_id:
            log_security_event('invalid_token', 'medium', f'Token inválido ou expirado: {token_type}')
            return jsonify({'error': 'Token inválido ou expirado'}), 401
        
        user = User.query.get(user_id)
        if not user or not user.is_active:
            log_security_event('inactive_user_access', 'high', f'Tentativa de acesso com usuário inativo: {user_id}')
            return jsonify({'error': 'Usuário não encontrado ou inativo'}), 404
        
        request.current_user = user
        return f(*args, **kwargs)
    
    return wrapper

def require_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not request.current_user.is_admin:
            log_security_event('unauthorized_admin_access', 'high', 
                             f'Tentativa de acesso administrativo por usuário não-admin: {request.current_user.id}')
            return jsonify({'error': 'Acesso negado. Privilégios de administrador necessários.'}), 403
        return f(*args, **kwargs)
    
    return wrapper

# Rotas de Autenticação
@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("5 per hour")
def register():
    """Registro de novo usuário"""
    data = request.json
    
    # Sanitização de inputs
    username = sanitize_input(data.get('username', ''))
    email = sanitize_input(data.get('email', ''))
    password = data.get('password', '')
    
    # Validações
    if not username or len(username) < 3:
        return jsonify({'error': 'Nome de usuário deve ter pelo menos 3 caracteres'}), 400
    
    if not validate_email(email):
        return jsonify({'error': 'Email inválido'}), 400
    
    is_valid, message = validate_password_strength(password)
    if not is_valid:
        return jsonify({'error': message}), 400
    
    # Verificar duplicatas
    if User.query.filter_by(username=username).first():
        log_security_event('duplicate_username', 'low', f'Tentativa de registro com username duplicado: {username}')
        return jsonify({'error': 'Nome de usuário já existe'}), 400
    
    if User.query.filter_by(email=email).first():
        log_security_event('duplicate_email', 'low', f'Tentativa de registro com email duplicado: {email}')
        return jsonify({'error': 'Email já cadastrado'}), 400
    
    # Criar usuário
    user = User(
        username=username,
        email=email,
        verification_token=secrets.token_urlsafe(32)
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    log_audit(user.id, 'user_registered', f'Novo usuário registrado: {username}')
    
    # Gerar tokens
    access_token = generate_token(user.id, 'access')
    refresh_token = generate_token(user.id, 'refresh')
    
    return jsonify({
        'message': 'Usuário registrado com sucesso',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }), 201

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """Login de usuário"""
    data = request.json
    
    username = sanitize_input(data.get('username', ''))
    password = data.get('password', '')
    
    user = User.query.filter_by(username=username).first()
    
    if not user:
        log_security_event('failed_login', 'low', f'Tentativa de login com usuário inexistente: {username}')
        return jsonify({'error': 'Credenciais inválidas'}), 401
    
    # Verificar se a conta está bloqueada
    if user.is_locked():
        log_security_event('locked_account_access', 'medium', f'Tentativa de acesso a conta bloqueada: {user.id}')
        return jsonify({'error': 'Conta temporariamente bloqueada devido a múltiplas tentativas de login falhadas'}), 403
    
    # Verificar senha
    if not user.check_password(password):
        user.increment_failed_login()
        log_security_event('failed_login', 'medium', f'Senha incorreta para usuário: {user.id}')
        return jsonify({'error': 'Credenciais inválidas'}), 401
    
    # Verificar se a conta está ativa
    if not user.is_active:
        log_security_event('inactive_account_login', 'high', f'Tentativa de login em conta inativa: {user.id}')
        return jsonify({'error': 'Conta desativada. Entre em contato com o suporte.'}), 403
    
    # Login bem-sucedido
    user.reset_failed_login()
    log_audit(user.id, 'user_login', f'Login bem-sucedido: {username}')
    
    # Gerar tokens
    access_token = generate_token(user.id, 'access')
    refresh_token = generate_token(user.id, 'refresh')
    
    return jsonify({
        'message': 'Login realizado com sucesso',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict(include_sensitive=True)
    }), 200

@app.route('/api/auth/refresh', methods=['POST'])
@limiter.limit("20 per hour")
def refresh_token():
    """Renova o token de acesso"""
    data = request.json
    refresh_token = data.get('refresh_token')
    
    if not refresh_token:
        return jsonify({'error': 'Refresh token não fornecido'}), 401
    
    user_id, token_type = verify_token(refresh_token)
    
    if not user_id or token_type != 'refresh':
        return jsonify({'error': 'Refresh token inválido'}), 401
    
    user = User.query.get(user_id)
    if not user or not user.is_active:
        return jsonify({'error': 'Usuário não encontrado ou inativo'}), 404
    
    # Gerar novo access token
    new_access_token = generate_token(user.id, 'access')
    
    return jsonify({
        'access_token': new_access_token
    }), 200

@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    """Retorna informações do usuário atual"""
    return jsonify({'user': request.current_user.to_dict(include_sensitive=True)}), 200

# Rotas de Usuário
@app.route('/api/user/link-discord', methods=['POST'])
@require_auth
def link_discord():
    """Vincula Discord ID à conta"""
    data = request.json
    discord_id = sanitize_input(data.get('discord_id', ''))
    
    if not discord_id:
        return jsonify({'error': 'Discord ID não fornecido'}), 400
    
    # Verificar se já está vinculado
    existing_user = User.query.filter_by(discord_id=discord_id).first()
    if existing_user and existing_user.id != request.current_user.id:
        log_security_event('duplicate_discord_id', 'medium', 
                         f'Tentativa de vincular Discord ID já em uso: {discord_id}')
        return jsonify({'error': 'Este Discord ID já está vinculado a outra conta'}), 400
    
    request.current_user.discord_id = discord_id
    db.session.commit()
    
    log_audit(request.current_user.id, 'discord_linked', f'Discord ID vinculado: {discord_id}')
    
    return jsonify({
        'message': 'Discord ID vinculado com sucesso',
        'user': request.current_user.to_dict(include_sensitive=True)
    }), 200

# Rotas do Bot Discord
@app.route('/api/bot/check-subscription', methods=['GET'])
@limiter.limit("100 per minute")
def check_subscription():
    """Verifica status de assinatura para o bot"""
    discord_guild_id = request.args.get('discord_guild_id')
    
    if not discord_guild_id:
        return jsonify({'error': 'Guild ID não fornecido'}), 400
    
    guild = DiscordGuild.query.filter_by(guild_id=discord_guild_id, is_active=True).first()
    
    if not guild:
        return jsonify({'status': 'inactive'}), 200
    
    owner = User.query.get(guild.owner_user_id)
    
    if not owner or not owner.is_active:
        return jsonify({'status': 'inactive'}), 200
    
    # Verificar assinatura
    if owner.subscription_status == 'active':
        if owner.subscription_end_date and owner.subscription_end_date > datetime.utcnow():
            return jsonify({'status': 'active'}), 200
    
    return jsonify({'status': 'inactive'}), 200

@app.route('/api/bot/register-guild', methods=['POST'])
@limiter.limit("10 per hour")
def register_guild():
    """Registra uma guild do Discord"""
    data = request.json
    discord_guild_id = sanitize_input(data.get('discord_guild_id', ''))
    inviter_discord_id = sanitize_input(data.get('inviter_discord_id', ''))
    
    if not discord_guild_id or not inviter_discord_id:
        return jsonify({'error': 'Dados incompletos'}), 400
    
    user = User.query.filter_by(discord_id=inviter_discord_id).first()
    
    if not user:
        log_security_event('guild_register_no_user', 'low', 
                         f'Tentativa de registro de guild sem usuário vinculado: {inviter_discord_id}')
        return jsonify({'error': 'Usuário não encontrado. Por favor, vincule seu Discord ID no site.'}), 404
    
    existing_guild = DiscordGuild.query.filter_by(guild_id=discord_guild_id).first()
    
    if existing_guild:
        return jsonify({'error': 'Este servidor já está registrado'}), 400
    
    guild = DiscordGuild(
        guild_id=discord_guild_id,
        owner_user_id=user.id
    )
    
    db.session.add(guild)
    db.session.commit()
    
    log_audit(user.id, 'guild_registered', f'Guild registrada: {discord_guild_id}')
    
    return jsonify({'message': 'Servidor registrado com sucesso'}), 200

# Rotas de Administração
@app.route('/api/admin/users', methods=['GET'])
@require_auth
@require_admin
def get_all_users():
    """Lista todos os usuários"""
    users = User.query.all()
    return jsonify({'users': [user.to_dict(include_sensitive=True) for user in users]}), 200

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@require_auth
@require_admin
def update_user(user_id):
    """Atualiza um usuário"""
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    data = request.json
    
    if 'subscription_status' in data:
        user.subscription_status = data['subscription_status']
    
    if 'subscription_end_date' in data:
        user.subscription_end_date = datetime.fromisoformat(data['subscription_end_date'])
    
    if 'is_admin' in data:
        user.is_admin = data['is_admin']
    
    if 'is_active' in data:
        user.is_active = data['is_active']
    
    db.session.commit()
    
    log_audit(request.current_user.id, 'user_updated', f'Usuário {user_id} atualizado')
    
    return jsonify({
        'message': 'Usuário atualizado com sucesso',
        'user': user.to_dict(include_sensitive=True)
    }), 200

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@require_auth
@require_admin
def delete_user(user_id):
    """Deleta um usuário"""
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    if user.is_admin and User.query.filter_by(is_admin=True).count() == 1:
        return jsonify({'error': 'Não é possível deletar o único administrador'}), 400
    
    db.session.delete(user)
    db.session.commit()
    
    log_audit(request.current_user.id, 'user_deleted', f'Usuário {user_id} deletado')
    log_security_event('user_deleted', 'high', f'Usuário {user_id} deletado por admin {request.current_user.id}')
    
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200

@app.route('/api/admin/payment-config', methods=['GET'])
@require_auth
@require_admin
def get_payment_config():
    """Retorna configurações de pagamento (sem dados sensíveis)"""
    config = PaymentConfig.query.first()
    
    if not config:
        config = PaymentConfig()
        db.session.add(config)
        db.session.commit()
    
    return jsonify({
        'stripe_publishable_key': config.stripe_publishable_key,
        'paypal_client_id': config.paypal_client_id,
        'has_stripe_secret': bool(config.stripe_secret_key_encrypted),
        'has_paypal_secret': bool(config.paypal_secret_encrypted)
    }), 200

@app.route('/api/admin/payment-config', methods=['PUT'])
@require_auth
@require_admin
def update_payment_config():
    """Atualiza configurações de pagamento"""
    config = PaymentConfig.query.first()
    
    if not config:
        config = PaymentConfig()
        db.session.add(config)
    
    data = request.json
    
    if 'stripe_secret_key' in data and data['stripe_secret_key']:
        config.stripe_secret_key_encrypted = encrypt_data(data['stripe_secret_key'])
    
    if 'stripe_publishable_key' in data:
        config.stripe_publishable_key = data['stripe_publishable_key']
    
    if 'paypal_client_id' in data:
        config.paypal_client_id = data['paypal_client_id']
    
    if 'paypal_secret' in data and data['paypal_secret']:
        config.paypal_secret_encrypted = encrypt_data(data['paypal_secret'])
    
    db.session.commit()
    
    log_audit(request.current_user.id, 'payment_config_updated', 'Configurações de pagamento atualizadas')
    log_security_event('payment_config_updated', 'high', 
                      f'Configurações de pagamento atualizadas por admin {request.current_user.id}')
    
    return jsonify({'message': 'Configuração de pagamento atualizada com sucesso'}), 200

@app.route('/api/admin/stats', methods=['GET'])
@require_auth
@require_admin
def get_stats():
    """Retorna estatísticas do sistema"""
    total_users = User.query.count()
    active_subscriptions = User.query.filter_by(subscription_status='active').count()
    total_guilds = DiscordGuild.query.filter_by(is_active=True).count()
    recent_security_events = SecurityEvent.query.filter(
        SecurityEvent.severity.in_(['high', 'critical'])
    ).order_by(SecurityEvent.timestamp.desc()).limit(10).all()
    
    return jsonify({
        'total_users': total_users,
        'active_subscriptions': active_subscriptions,
        'total_guilds': total_guilds,
        'recent_security_events': [{
            'type': event.event_type,
            'severity': event.severity,
            'description': event.description,
            'timestamp': event.timestamp.isoformat()
        } for event in recent_security_events]
    }), 200

@app.route('/api/admin/audit-logs', methods=['GET'])
@require_auth
@require_admin
def get_audit_logs():
    """Retorna logs de auditoria"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'logs': [{
            'id': log.id,
            'user_id': log.user_id,
            'username': log.user.username if log.user else None,
            'action': log.action,
            'details': log.details,
            'ip_address': log.ip_address,
            'timestamp': log.timestamp.isoformat()
        } for log in logs.items],
        'total': logs.total,
        'pages': logs.pages,
        'current_page': logs.page
    }), 200

@app.route('/api/admin/security-events', methods=['GET'])
@require_auth
@require_admin
def get_security_events():
    """Retorna eventos de segurança"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    severity = request.args.get('severity', None)
    
    query = SecurityEvent.query
    
    if severity:
        query = query.filter_by(severity=severity)
    
    events = query.order_by(SecurityEvent.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'events': [{
            'id': event.id,
            'event_type': event.event_type,
            'severity': event.severity,
            'description': event.description,
            'ip_address': event.ip_address,
            'user_id': event.user_id,
            'timestamp': event.timestamp.isoformat()
        } for event in events.items],
        'total': events.total,
        'pages': events.pages,
        'current_page': events.page
    }), 200

# Tratamento de Erros
@app.errorhandler(429)
def ratelimit_handler(e):
    """Tratamento de erro de rate limit"""
    log_security_event('rate_limit_exceeded', 'medium', f'Rate limit excedido: {request.remote_addr}')
    return jsonify({'error': 'Muitas requisições. Por favor, tente novamente mais tarde.'}), 429

@app.errorhandler(500)
def internal_error(e):
    """Tratamento de erro interno"""
    log_security_event('internal_error', 'critical', f'Erro interno: {str(e)}')
    return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)



