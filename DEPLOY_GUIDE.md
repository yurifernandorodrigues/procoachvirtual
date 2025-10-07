# Guia de Deploy - Pro Coach Virtual

Este guia fornece instruções passo a passo para fazer o deploy do **Pro Coach Virtual** em plataformas de hospedagem gratuitas.

## Arquitetura

- **Frontend:** React + Vite → Vercel (gratuito)
- **Backend:** Flask + SQLAlchemy → Render (gratuito)
- **Banco de Dados:** PostgreSQL → Render (gratuito)

## Pré-requisitos

1. Conta no [GitHub](https://github.com)
2. Conta no [Vercel](https://vercel.com)
3. Conta no [Render](https://render.com)

## Passo 1: Preparar o Repositório no GitHub

### 1.1 Criar Repositório

```bash
cd /home/ubuntu/lol-coach-production-site
git init
git add .
git commit -m "Initial commit - Pro Coach Virtual"
```

### 1.2 Criar Repositório no GitHub

1. Acesse [GitHub](https://github.com/new)
2. Crie um novo repositório chamado `procoachvirtual`
3. **Não** inicialize com README, .gitignore ou licença

### 1.3 Fazer Push do Código

```bash
git remote add origin https://github.com/SEU_USUARIO/procoachvirtual.git
git branch -M main
git push -u origin main
```

## Passo 2: Deploy do Backend no Render

### 2.1 Criar Web Service

1. Acesse [Render Dashboard](https://dashboard.render.com)
2. Clique em **"New +"** → **"Web Service"**
3. Conecte seu repositório GitHub `procoachvirtual`
4. Configure:
   - **Name:** `procoachvirtual-api`
   - **Region:** Oregon (US West) ou mais próximo
   - **Branch:** `main`
   - **Root Directory:** `lol-coach-backend`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** `Free`

### 2.2 Configurar Variáveis de Ambiente

No painel do Render, vá em **Environment** e adicione:

```
SECRET_KEY=<gerar_chave_aleatoria_segura>
FLASK_ENV=production
DATABASE_URL=<será_preenchido_automaticamente_pelo_render>
ALLOWED_ORIGINS=https://procoachvirtual.vercel.app
```

### 2.3 Criar Banco de Dados PostgreSQL

1. No Render Dashboard, clique em **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name:** `procoachvirtual-db`
   - **Database:** `procoachvirtual`
   - **User:** `procoachvirtual`
   - **Region:** Mesmo do Web Service
   - **Instance Type:** `Free`

3. Após criar, copie a **Internal Database URL**
4. Cole no campo `DATABASE_URL` das variáveis de ambiente do Web Service

### 2.4 Deploy

O Render fará o deploy automaticamente. Aguarde até o status ficar **"Live"**.

Sua API estará disponível em: `https://procoachvirtual-api.onrender.com`

## Passo 3: Deploy do Frontend no Vercel

### 3.1 Importar Projeto

1. Acesse [Vercel Dashboard](https://vercel.com/dashboard)
2. Clique em **"Add New..."** → **"Project"**
3. Importe seu repositório GitHub `procoachvirtual`

### 3.2 Configurar Projeto

- **Framework Preset:** Vite
- **Root Directory:** `lol-coach-frontend`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Install Command:** `npm install`

### 3.3 Configurar Variáveis de Ambiente

Adicione a variável:

```
VITE_API_URL=https://procoachvirtual-api.onrender.com
```

### 3.4 Deploy

Clique em **"Deploy"**. O Vercel fará o build e deploy automaticamente.

Seu site estará disponível em: `https://procoachvirtual.vercel.app`

## Passo 4: Configurar Domínio Personalizado (Opcional)

### 4.1 Comprar Domínio

Registre um domínio (ex: `procoachvirtual.com`) em:
- [GoDaddy](https://godaddy.com)
- [Hostinger](https://hostinger.com.br)
- [Registro.br](https://registro.br) (para .com.br)

### 4.2 Configurar DNS no Vercel

1. No Vercel, vá em **Settings** → **Domains**
2. Adicione seu domínio personalizado
3. Siga as instruções para configurar os registros DNS:
   - **Tipo A:** Aponte para o IP do Vercel
   - **Tipo CNAME:** `cname.vercel-dns.com`

### 4.3 Atualizar CORS no Backend

No Render, atualize a variável `ALLOWED_ORIGINS`:

```
ALLOWED_ORIGINS=https://procoachvirtual.com,https://www.procoachvirtual.com
```

## Passo 5: Inicializar Banco de Dados

### 5.1 Criar Tabelas

Acesse o shell do Render:

1. No Render Dashboard, vá no seu Web Service
2. Clique em **"Shell"**
3. Execute:

```bash
python
>>> from app import db, app
>>> with app.app_context():
...     db.create_all()
...     print("Banco de dados inicializado!")
>>> exit()
```

### 5.2 Verificar Conta Admin

A conta de administrador será criada automaticamente no primeiro acesso ao backend.

**Credenciais:**
- **Login:** yurifrdf
- **Senha:** Isacnoahjade@131312

## Passo 6: Testar o Site

1. Acesse `https://procoachvirtual.vercel.app`
2. Faça login com a conta de administrador
3. Teste as funcionalidades:
   - Registro de novos usuários
   - Login/Logout
   - Visualização de planos
   - Vinculação de Discord ID

## Monitoramento e Logs

### Vercel (Frontend)
- Acesse **Dashboard** → **Deployments** → **View Function Logs**

### Render (Backend)
- Acesse **Dashboard** → **Logs**

## Custos

### Plano Gratuito (Atual)

| Serviço | Plano | Custo | Limitações |
|---------|-------|-------|------------|
| Vercel | Hobby | R$ 0/mês | 100 GB bandwidth, builds ilimitados |
| Render | Free | R$ 0/mês | 750h/mês, sleep após 15min inatividade |
| PostgreSQL | Free | R$ 0/mês | 1 GB storage, expira após 90 dias |

### Plano Pago (Recomendado para Produção)

| Serviço | Plano | Custo | Benefícios |
|---------|-------|-------|------------|
| Vercel | Pro | $20/mês (~R$ 100) | Domínio personalizado, analytics |
| Render | Starter | $7/mês (~R$ 35) | Sem sleep, 512 MB RAM |
| PostgreSQL | Starter | $7/mês (~R$ 35) | 10 GB storage, backups |

**Total:** ~R$ 170/mês

## Próximos Passos

1. ✅ Deploy do frontend e backend
2. ⏳ Integrar sistema de pagamentos (Mercado Pago/Stripe)
3. ⏳ Implementar dashboard do usuário
4. ⏳ Implementar painel administrativo
5. ⏳ Conectar com o bot Discord
6. ⏳ Testes de integração completos

## Suporte

Para dúvidas ou problemas, consulte a documentação oficial:
- [Vercel Docs](https://vercel.com/docs)
- [Render Docs](https://render.com/docs)
- [Flask Docs](https://flask.palletsprojects.com)

---

**Pro Coach Virtual** - Seu coach virtual para subir de elo
