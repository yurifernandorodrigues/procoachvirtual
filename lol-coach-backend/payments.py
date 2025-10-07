"""
Módulo de Pagamentos
Suporta Pix, Cartão de Crédito e Débito via Mercado Pago e Stripe
"""

import os
import requests
import hmac
import hashlib
from datetime import datetime, timedelta
from flask import current_app

class PaymentProcessor:
    """Classe base para processadores de pagamento"""
    
    def __init__(self):
        self.provider = None
    
    def create_payment(self, amount, description, payment_method, customer_data):
        raise NotImplementedError
    
    def create_subscription(self, plan_id, customer_data):
        raise NotImplementedError
    
    def cancel_subscription(self, subscription_id):
        raise NotImplementedError
    
    def verify_webhook(self, payload, signature):
        raise NotImplementedError


class MercadoPagoProcessor(PaymentProcessor):
    """Processador de pagamentos via Mercado Pago"""
    
    def __init__(self, access_token):
        super().__init__()
        self.provider = 'mercadopago'
        self.access_token = access_token
        self.base_url = 'https://api.mercadopago.com'
    
    def _make_request(self, method, endpoint, data=None):
        """Faz requisição à API do Mercado Pago"""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f'{self.base_url}{endpoint}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição ao Mercado Pago: {e}")
            return None
    
    def create_pix_payment(self, amount, description, customer_data):
        """Cria um pagamento via Pix"""
        data = {
            'transaction_amount': float(amount),
            'description': description,
            'payment_method_id': 'pix',
            'payer': {
                'email': customer_data.get('email'),
                'first_name': customer_data.get('first_name', ''),
                'last_name': customer_data.get('last_name', ''),
                'identification': {
                    'type': customer_data.get('doc_type', 'CPF'),
                    'number': customer_data.get('doc_number', '')
                }
            }
        }
        
        result = self._make_request('POST', '/v1/payments', data)
        
        if result:
            return {
                'payment_id': result.get('id'),
                'status': result.get('status'),
                'qr_code': result.get('point_of_interaction', {}).get('transaction_data', {}).get('qr_code'),
                'qr_code_base64': result.get('point_of_interaction', {}).get('transaction_data', {}).get('qr_code_base64'),
                'ticket_url': result.get('point_of_interaction', {}).get('transaction_data', {}).get('ticket_url')
            }
        
        return None
    
    def create_card_payment(self, amount, description, card_token, installments, customer_data):
        """Cria um pagamento via cartão de crédito/débito"""
        data = {
            'transaction_amount': float(amount),
            'token': card_token,
            'description': description,
            'installments': int(installments),
            'payment_method_id': 'visa',  # Será determinado pelo token
            'payer': {
                'email': customer_data.get('email'),
                'identification': {
                    'type': customer_data.get('doc_type', 'CPF'),
                    'number': customer_data.get('doc_number', '')
                }
            }
        }
        
        result = self._make_request('POST', '/v1/payments', data)
        
        if result:
            return {
                'payment_id': result.get('id'),
                'status': result.get('status'),
                'status_detail': result.get('status_detail'),
                'payment_method': result.get('payment_method_id'),
                'installments': result.get('installments')
            }
        
        return None
    
    def create_subscription(self, plan_id, customer_data, card_token=None):
        """Cria uma assinatura recorrente"""
        # Primeiro, criar um cliente
        customer_result = self._make_request('POST', '/v1/customers', {
            'email': customer_data.get('email'),
            'first_name': customer_data.get('first_name', ''),
            'last_name': customer_data.get('last_name', ''),
            'identification': {
                'type': customer_data.get('doc_type', 'CPF'),
                'number': customer_data.get('doc_number', '')
            }
        })
        
        if not customer_result:
            return None
        
        customer_id = customer_result.get('id')
        
        # Se houver token de cartão, adicionar como método de pagamento
        if card_token:
            self._make_request('POST', f'/v1/customers/{customer_id}/cards', {
                'token': card_token
            })
        
        # Criar assinatura
        subscription_data = {
            'preapproval_plan_id': plan_id,
            'payer_email': customer_data.get('email'),
            'card_token_id': card_token,
            'auto_recurring': {
                'frequency': 1,
                'frequency_type': 'months',
                'transaction_amount': customer_data.get('amount', 0),
                'currency_id': 'BRL'
            },
            'back_url': customer_data.get('back_url', ''),
            'status': 'authorized'
        }
        
        result = self._make_request('POST', '/preapproval', subscription_data)
        
        if result:
            return {
                'subscription_id': result.get('id'),
                'status': result.get('status'),
                'init_point': result.get('init_point')
            }
        
        return None
    
    def cancel_subscription(self, subscription_id):
        """Cancela uma assinatura"""
        result = self._make_request('PUT', f'/preapproval/{subscription_id}', {
            'status': 'cancelled'
        })
        
        return result is not None
    
    def get_payment_status(self, payment_id):
        """Consulta o status de um pagamento"""
        result = self._make_request('GET', f'/v1/payments/{payment_id}')
        
        if result:
            return {
                'payment_id': result.get('id'),
                'status': result.get('status'),
                'status_detail': result.get('status_detail'),
                'transaction_amount': result.get('transaction_amount')
            }
        
        return None
    
    def verify_webhook(self, payload, signature):
        """Verifica a autenticidade de um webhook do Mercado Pago"""
        # Mercado Pago usa x-signature header
        # Implementar verificação conforme documentação oficial
        return True  # Placeholder


class StripeProcessor(PaymentProcessor):
    """Processador de pagamentos via Stripe"""
    
    def __init__(self, secret_key):
        super().__init__()
        self.provider = 'stripe'
        self.secret_key = secret_key
        self.base_url = 'https://api.stripe.com/v1'
    
    def _make_request(self, method, endpoint, data=None):
        """Faz requisição à API do Stripe"""
        headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        url = f'{self.base_url}{endpoint}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, data=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição ao Stripe: {e}")
            return None
    
    def create_card_payment(self, amount, description, payment_method_id, customer_email):
        """Cria um pagamento via cartão de crédito"""
        # Converter para centavos
        amount_cents = int(float(amount) * 100)
        
        data = {
            'amount': amount_cents,
            'currency': 'brl',
            'description': description,
            'payment_method': payment_method_id,
            'confirm': 'true',
            'receipt_email': customer_email
        }
        
        result = self._make_request('POST', '/payment_intents', data)
        
        if result:
            return {
                'payment_id': result.get('id'),
                'status': result.get('status'),
                'client_secret': result.get('client_secret')
            }
        
        return None
    
    def create_subscription(self, price_id, customer_email, payment_method_id=None):
        """Cria uma assinatura recorrente"""
        # Primeiro, criar ou buscar cliente
        customer_data = {
            'email': customer_email
        }
        
        if payment_method_id:
            customer_data['payment_method'] = payment_method_id
            customer_data['invoice_settings[default_payment_method]'] = payment_method_id
        
        customer_result = self._make_request('POST', '/customers', customer_data)
        
        if not customer_result:
            return None
        
        customer_id = customer_result.get('id')
        
        # Criar assinatura
        subscription_data = {
            'customer': customer_id,
            'items[0][price]': price_id,
            'expand[]': 'latest_invoice.payment_intent'
        }
        
        result = self._make_request('POST', '/subscriptions', subscription_data)
        
        if result:
            return {
                'subscription_id': result.get('id'),
                'status': result.get('status'),
                'client_secret': result.get('latest_invoice', {}).get('payment_intent', {}).get('client_secret')
            }
        
        return None
    
    def cancel_subscription(self, subscription_id):
        """Cancela uma assinatura"""
        result = self._make_request('DELETE', f'/subscriptions/{subscription_id}')
        return result is not None
    
    def verify_webhook(self, payload, signature, webhook_secret):
        """Verifica a autenticidade de um webhook do Stripe"""
        try:
            # Stripe usa HMAC SHA256
            expected_signature = hmac.new(
                webhook_secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            print(f"Erro ao verificar webhook: {e}")
            return False


class PaymentManager:
    """Gerenciador de pagamentos que abstrai os diferentes processadores"""
    
    def __init__(self, provider='mercadopago', **credentials):
        if provider == 'mercadopago':
            self.processor = MercadoPagoProcessor(credentials.get('access_token'))
        elif provider == 'stripe':
            self.processor = StripeProcessor(credentials.get('secret_key'))
        else:
            raise ValueError(f"Provedor de pagamento não suportado: {provider}")
    
    def create_pix_payment(self, amount, description, customer_data):
        """Cria pagamento via Pix (apenas Mercado Pago)"""
        if isinstance(self.processor, MercadoPagoProcessor):
            return self.processor.create_pix_payment(amount, description, customer_data)
        else:
            raise NotImplementedError("Pix não é suportado por este provedor")
    
    def create_card_payment(self, amount, description, payment_data, customer_data):
        """Cria pagamento via cartão"""
        if isinstance(self.processor, MercadoPagoProcessor):
            return self.processor.create_card_payment(
                amount, description,
                payment_data.get('card_token'),
                payment_data.get('installments', 1),
                customer_data
            )
        elif isinstance(self.processor, StripeProcessor):
            return self.processor.create_card_payment(
                amount, description,
                payment_data.get('payment_method_id'),
                customer_data.get('email')
            )
    
    def create_subscription(self, plan_data, customer_data, payment_data=None):
        """Cria assinatura recorrente"""
        if isinstance(self.processor, MercadoPagoProcessor):
            return self.processor.create_subscription(
                plan_data.get('plan_id'),
                customer_data,
                payment_data.get('card_token') if payment_data else None
            )
        elif isinstance(self.processor, StripeProcessor):
            return self.processor.create_subscription(
                plan_data.get('price_id'),
                customer_data.get('email'),
                payment_data.get('payment_method_id') if payment_data else None
            )
    
    def cancel_subscription(self, subscription_id):
        """Cancela assinatura"""
        return self.processor.cancel_subscription(subscription_id)
    
    def verify_webhook(self, payload, signature, secret=None):
        """Verifica webhook"""
        if isinstance(self.processor, StripeProcessor):
            return self.processor.verify_webhook(payload, signature, secret)
        else:
            return self.processor.verify_webhook(payload, signature)


# Planos de Assinatura
SUBSCRIPTION_PLANS = {
    'monthly': {
        'name': 'Plano Mensal',
        'description': 'Acesso completo ao bot por 1 mês',
        'price': 29.90,
        'currency': 'BRL',
        'interval': 'month',
        'interval_count': 1
    },
    'quarterly': {
        'name': 'Plano Trimestral',
        'description': 'Acesso completo ao bot por 3 meses (10% de desconto)',
        'price': 80.73,
        'currency': 'BRL',
        'interval': 'month',
        'interval_count': 3
    },
    'yearly': {
        'name': 'Plano Anual',
        'description': 'Acesso completo ao bot por 12 meses (20% de desconto)',
        'price': 287.04,
        'currency': 'BRL',
        'interval': 'year',
        'interval_count': 1
    }
}
