from odoo import api, fields, models, _
import logging
import base64

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('midtrans', 'Midtrans')],
        ondelete={'midtrans': 'set default'}
    )
    
    midtrans_server_key = fields.Char(
        string='Server Key',
        required_if_provider='midtrans',
        groups='base.group_system'
    )
    midtrans_client_key = fields.Char(
        string='Client Key',
        required_if_provider='midtrans',
        groups='base.group_system'
    )
    midtrans_merchant_id = fields.Char(
        string='Merchant ID',
        required_if_provider='midtrans',
        groups='base.group_system'
    )
    midtrans_use_sandbox = fields.Boolean(
        string='Use Sandbox',
        default=True,
        help='Enable untuk testing dengan Sandbox Midtrans'
    )
    midtrans_payment_methods = fields.Many2many(
        'payment.midtrans.method',
        string='Payment Methods',
        help='Pilih metode pembayaran yang akan diaktifkan'
    )
    
    def _get_midtrans_api_url(self):
        self.ensure_one()
        if self.midtrans_use_sandbox:
            return 'https://app.sandbox.midtrans.com/snap/v1'
        return 'https://app.midtrans.com/snap/v1'
    
    def _get_midtrans_headers(self):
        self.ensure_one()
        auth_string = f"{self.midtrans_server_key}:"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Basic {auth_b64}'
        }
    
    @api.model
    def _get_compatible_providers(self, *args, company_id=None, **kwargs):
        providers = super()._get_compatible_providers(*args, company_id=company_id, **kwargs)
        return providers
    
    def _midtrans_make_request(self, endpoint, data=None):
        self.ensure_one()
        url = f"{self._get_midtrans_api_url()}/{endpoint}"
        headers = self._get_midtrans_headers()
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            _logger.error(f"Midtrans API request failed: {e}")
            raise ValidationError(_("Gagal terhubung ke Midtrans: %s") % str(e))
    

    class PaymentMidtransMethod(models.Model):
        _name = 'payment.midtrans.method'
        _description = 'Midtrans Payment Method'
        
        name = fields.Char(string='Method Name', required=True)
        code = fields.Char(string='Method Code', required=True)
        active = fields.Boolean(string='Active', default=True)
        sequence = fields.Integer(string='Sequence', default=10)
        
        _sql_constraints = [
            ('code_unique', 'UNIQUE(code)', 'Method code must be unique!')
        ]