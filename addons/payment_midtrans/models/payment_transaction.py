import logging
import requests
import json
import base64
import hashlib
from werkzeug import urls

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.addons.payment import utils as payment_utils

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    midtrans_order_id = fields.Char(
        string='Midtrans Order ID',
        readonly=True,
        help='Unique order ID yang digenerate untuk Midtrans'
    )
    
    midtrans_transaction_id = fields.Char(
        string='Midtrans Transaction ID',
        readonly=True,
        help='Transaction ID dari Midtrans setelah pembayaran diproses'
    )

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        
        if self.provider_code != 'midtrans':
            return res

        base_url = self.provider_id.get_base_url()
        
        midtrans_order_id = f"{self.reference}-{self.id}"
        
        rendering_values = {
            'api_url': self.provider_id._get_midtrans_api_url(),
            'snap_url': self.provider_id._get_midtrans_snap_url(),
            'client_key': self.provider_id.midtrans_client_key,
            'order_id': midtrans_order_id,
            'amount': int(self.amount),  # Midtrans butuh integer (dalam cent/smallest unit)
            'currency': self.currency_id.name,
            'return_url': urls.url_join(base_url, '/payment/midtrans/return'),
        }
        
        self.midtrans_order_id = midtrans_order_id
        
        return rendering_values

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        
        if provider_code != 'midtrans' or len(tx) == 1:
            return tx

        order_id = notification_data.get('order_id')
        if not order_id:
            raise ValidationError(
                "Midtrans: " + _("Received notification with missing order_id")
            )

        tx = self.search([
            ('midtrans_order_id', '=', order_id),
            ('provider_code', '=', 'midtrans')
        ])
        
        if not tx:
            raise ValidationError(
                "Midtrans: " + _("No transaction found matching order_id: %s", order_id)
            )
        
        return tx

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        
        if self.provider_code != 'midtrans':
            return

        self.midtrans_transaction_id = notification_data.get('transaction_id')
        
        transaction_status = notification_data.get('transaction_status')
        fraud_status = notification_data.get('fraud_status', 'accept')

        _logger.info(
            "Processing Midtrans notification for transaction %s: status=%s, fraud=%s",
            self.reference, transaction_status, fraud_status
        )

        # Update transaction status berdasarkan Midtrans status
        # Reference: https://docs.midtrans.com/en/after-payment/http-notification
        
        if transaction_status == 'capture':
            # Pembayaran berhasil di-capture (untuk credit card)
            if fraud_status == 'accept':
                self._set_done()  # Set status ke 'done'
            elif fraud_status == 'challenge':
                self._set_pending()  # Perlu review fraud
                
        elif transaction_status == 'settlement':
            # Pembayaran sukses (untuk non-credit card)
            self._set_done()
            
        elif transaction_status in ['cancel', 'deny', 'expire']:
            # Pembayaran dibatalkan/ditolak/expired
            self._set_canceled()
            
        elif transaction_status == 'pending':
            # Pembayaran masih pending (menunggu customer bayar)
            self._set_pending()
            
        else:
            # Status tidak dikenali
            _logger.warning(
                "Received unrecognized transaction status for transaction %s: %s",
                self.reference, transaction_status
            )
            self._set_error(
                "Midtrans: " + _("Unknown transaction status: %s", transaction_status)
            )

    def _create_midtrans_transaction(self):
        
        self.ensure_one()
        
        server_key = self.provider_id.midtrans_server_key
        api_url = self.provider_id._get_midtrans_api_url()
        

        auth_string = base64.b64encode(f"{server_key}:".encode()).decode()
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Basic {auth_string}'
        }
        
        base_url = self.provider_id.get_base_url()
        
        # Prepare transaction data untuk Midtrans Snap API
        # Reference: https://docs.midtrans.com/en/snap/integration-guide
        payload = {
            'transaction_details': {
                'order_id': self.midtrans_order_id,
                'gross_amount': int(self.amount)  # Harus integer
            },
            'customer_details': {
                'first_name': self.partner_id.name or 'Guest',
                'email': self.partner_id.email or 'noreply@example.com',
                'phone': self.partner_id.phone or self.partner_id.mobile or '08123456789'
            },
            'callbacks': {
                'finish': urls.url_join(base_url, '/payment/midtrans/return')
            }
        }
        
        if hasattr(self, 'sale_order_ids') and self.sale_order_ids:
            sale_order = self.sale_order_ids[0]
            item_details = []
            for line in sale_order.order_line:
                item_details.append({
                    'id': line.product_id.id,
                    'name': line.product_id.name,
                    'price': int(line.price_unit),
                    'quantity': int(line.product_uom_qty)
                })
            payload['item_details'] = item_details
        
        try:
            _logger.info("Creating Midtrans transaction for order %s", self.midtrans_order_id)
            
            response = requests.post(
                f"{api_url}/snap/transactions",
                headers=headers,
                data=json.dumps(payload),
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            _logger.info("Midtrans transaction created successfully: %s", result.get('token'))
            
            return {
                'snap_token': result.get('token'),
                'redirect_url': result.get('redirect_url')
            }
            
        except requests.exceptions.RequestException as e:
            _logger.exception("Midtrans API Error: %s", str(e))
            raise ValidationError(
                _("Unable to create Midtrans transaction: %s") % str(e)
            )

    def _send_payment_request(self):
        if self.provider_code != 'midtrans':
            return super()._send_payment_request()
        return None

    def _get_processing_values(self):
        res = super()._get_processing_values()
        if self.provider_code == 'midtrans':
            res.update({
                'midtrans_order_id': self.midtrans_order_id,
            })
        return res