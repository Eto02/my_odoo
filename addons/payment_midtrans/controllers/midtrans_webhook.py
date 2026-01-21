import logging
import pprint
import requests
import base64
import hashlib

from werkzeug import urls
from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class MidtransController(http.Controller):


    @http.route('/payment/midtrans/get_snap_token', type='json', auth='public')
    def midtrans_get_snap_token(self, transaction_id, **kwargs):
        try:
            tx = request.env['payment.transaction'].sudo().browse(transaction_id)
            
            if not tx or not tx.exists():
                _logger.error("Transaction not found: %s", transaction_id)
                return {'error': 'Transaction not found'}
            
            if tx.provider_code != 'midtrans':
                _logger.error("Invalid provider for transaction %s: %s", transaction_id, tx.provider_code)
                return {'error': 'Invalid payment provider'}
            
            _logger.info("Getting snap token for transaction %s", tx.reference)
            snap_data = tx._create_midtrans_transaction()
            
            return {
                'snap_token': snap_data.get('snap_token'),
                'snap_url': tx.provider_id._get_midtrans_snap_url(),
                'order_id': tx.midtrans_order_id
            }
            
        except Exception as e:
            _logger.exception("Error getting Midtrans snap token for transaction %s", transaction_id)
            return {'error': str(e)}

    @http.route('/payment/midtrans/success', type='json', auth='public', csrf=False)
    def midtrans_success(self, **post):
        """
        Handle payment success callback from JS
        """
        try:
            transaction_id = post.get('transaction_id')
            snap_result = post.get('snap_result', {})
            
            if not transaction_id:
                return {'success': False, 'message': 'Transaction ID not found'}
            
            tx = request.env['payment.transaction'].sudo().browse(int(transaction_id))
            
            if not tx.exists():
                return {'success': False, 'message': 'Transaction not found'}
            
            _logger.info("Payment success callback for transaction %s", tx.reference)
            
            # Verify transaction status dengan Midtrans
            order_id = tx.midtrans_order_id
            provider = tx.provider_id
            server_key = provider.midtrans_server_key
            api_url = provider._get_midtrans_api_url()
            
            auth_string = base64.b64encode(f"{server_key}:".encode()).decode()
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Basic {auth_string}'
            }
            
            response = requests.get(
                f"{api_url}/{order_id}/status",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            status_data = response.json()
            
            _logger.info("Verified transaction status: %s", status_data.get('transaction_status'))
            
            # Update transaction status
            tx._handle_notification_data('midtrans', status_data)
            
            return {
                'success': True,
                'message': 'Payment processed',
                'redirect_url': f'/payment/status?tx_id={tx.id}'
            }
            
        except Exception as e:
            _logger.exception("Error in payment success callback")
            return {'success': False, 'message': str(e)}

    @http.route('/payment/midtrans/notification', type='json', auth='public', csrf=False)
    def midtrans_notification(self, **post):
        _logger.info("="*80)
        _logger.info("Midtrans notification received")
        _logger.info("="*80)
        _logger.info("Notification data:\n%s", pprint.pformat(post))
        
        try:
            order_id = post.get('order_id')
            status_code = post.get('status_code')
            gross_amount = post.get('gross_amount')
            signature_key = post.get('signature_key')
            
            if not all([order_id, status_code, gross_amount, signature_key]):
                _logger.error("Midtrans notification missing required fields")
                return {'status': 'error', 'message': 'Missing required fields'}
            
            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                'midtrans', post
            )
            
            provider = tx_sudo.provider_id
            server_key = provider.midtrans_server_key
            
            signature_string = f"{order_id}{status_code}{gross_amount}{server_key}"
            calculated_signature = hashlib.sha512(signature_string.encode()).hexdigest()
            
            if calculated_signature != signature_key:
                _logger.warning(
                    "Midtrans: Invalid signature for order %s. Expected: %s, Got: %s",
                    order_id, calculated_signature, signature_key
                )
                return {'status': 'error', 'message': 'Invalid signature'}
            
            _logger.info("Signature verified successfully for order %s", order_id)
            
            tx_sudo._handle_notification_data('midtrans', post)
            
            _logger.info("Notification processed successfully for order %s", order_id)
            return {'status': 'ok'}
            
        except ValidationError as e:
            _logger.exception("Midtrans notification validation error")
            return {'status': 'error', 'message': str(e)}
        except Exception as e:
            _logger.exception("Unexpected error processing Midtrans notification")
            return {'status': 'error', 'message': 'Internal server error'}

    @http.route('/payment/midtrans/return', type='http', auth='public', csrf=False, save_session=False)
    def midtrans_return(self, **post):

        _logger.info("="*80)
        _logger.info("Midtrans return from payment page")
        _logger.info("="*80)
        _logger.info("Return data:\n%s", pprint.pformat(post))
        
        order_id = post.get('order_id')
        
        if order_id:
            try:
                tx_sudo = request.env['payment.transaction'].sudo().search([
                    ('midtrans_order_id', '=', order_id)
                ], limit=1)
                
                if tx_sudo:
                    provider = tx_sudo.provider_id
                    server_key = provider.midtrans_server_key
                    api_url = provider._get_midtrans_api_url()
                    
                    auth_string = base64.b64encode(f"{server_key}:".encode()).decode()
                    headers = {
                        'Accept': 'application/json',
                        'Authorization': f'Basic {auth_string}'
                    }
                    
                    _logger.info("Verifying transaction status for order %s", order_id)
                    response = requests.get(
                        f"{api_url}/{order_id}/status",
                        headers=headers,
                        timeout=10
                    )
                    response.raise_for_status()
                    status_data = response.json()
                    
                    _logger.info("Status verification response:\n%s", pprint.pformat(status_data))
                    
                    tx_sudo._handle_notification_data('midtrans', status_data)
                    
                    _logger.info("Transaction status updated successfully for order %s", order_id)
                    
            except Exception as e:
                _logger.exception("Error verifying Midtrans transaction status for order %s", order_id)
        
        return request.redirect('/payment/status')
    
    @http.route('/payment/midtrans/webhook', type='json', auth='public', csrf=False)
    def midtrans_webhook(self, **post):
        return self.midtrans_notification(**post)