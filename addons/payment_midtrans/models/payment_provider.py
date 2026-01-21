import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

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
        groups='base.group_system',       
        help='Server Key dari Midtrans Dashboard. Digunakan untuk API authentication.'
    )
    midtrans_client_key = fields.Char(
        string='Client Key',
        required_if_provider='midtrans',
        help='Client Key dari Midtrans Dashboard. Digunakan di frontend untuk Snap.'
    )
    midtrans_merchant_id = fields.Char(
        string='Merchant ID',
        required_if_provider='midtrans',
        help='Merchant ID yang didapat dari Midtrans'
    )
    
    midtrans_environment = fields.Selection(
        [
            ('sandbox', 'Sandbox (Testing)'),
            ('production', 'Production (Live)')
        ],
        string='Environment',
        required_if_provider='midtrans',
        default='sandbox',
        help='Gunakan Sandbox untuk testing, Production untuk live transactions'
    )
    
    midtrans_method = fields.Selection(
        [
            ('snap', 'Snap (Recommended)'),
            ('coreapi', 'Core API'),
        ],
        string='Integration Method',
        required_if_provider='midtrans',
        default='snap',
        help='Snap untuk popup payment, Core API untuk custom integration'
    )

    def _get_midtrans_api_url(self):
        """Get Midtrans API endpoint URL"""
        self.ensure_one()
        if self.midtrans_environment == 'production':
            return 'https://api.midtrans.com/v2'
        return 'https://api.sandbox.midtrans.com/v2'
    
    def _get_midtrans_snap_url(self):
        """Get Midtrans Snap JS URL"""
        self.ensure_one()
        if self.midtrans_environment == 'production':
            return 'https://app.midtrans.com/snap/snap.js'
        return 'https://app.sandbox.midtrans.com/snap/snap.js'
    
    def _get_midtrans_snap_redirect_url(self):
        """Get Midtrans Snap redirect URL"""
        self.ensure_one()
        if self.midtrans_environment == 'production':
            return 'https://app.midtrans.com/snap/v2/vtweb/'
        return 'https://app.sandbox.midtrans.com/snap/v2/vtweb/'

    @api.model
    def _get_compatible_providers(self, *args, currency_id=None, **kwargs):
        """Get compatible payment providers"""
        providers = super()._get_compatible_providers(*args, currency_id=currency_id, **kwargs)
        return providers

    def _midtrans_get_api_url(self):
        """Get API URL (alias for compatibility)"""
        return self._get_midtrans_api_url()
    
    @api.constrains('midtrans_server_key', 'midtrans_client_key', 'midtrans_merchant_id', 'state')
    def _check_midtrans_credentials(self):
        """Validate Midtrans credentials"""
        for provider in self:
            if provider.code == 'midtrans' and provider.state != 'disabled':
                if not provider.midtrans_server_key:
                    raise ValidationError(_('Server Key harus diisi untuk Midtrans'))
                if not provider.midtrans_client_key:
                    raise ValidationError(_('Client Key harus diisi untuk Midtrans'))
                if not provider.midtrans_merchant_id:
                    raise ValidationError(_('Merchant ID harus diisi untuk Midtrans'))

    def _get_tx_form_redirect_url(self, **kwargs):
        """Get transaction redirect URL for Odoo 17"""
        if self.code != 'midtrans':
            return super()._get_tx_form_redirect_url(**kwargs)
        
        # For Midtrans, we handle the redirect in JS
        return None
    
    def _get_default_payment_method_codes(self):
        """Get default payment method codes for Midtrans"""
        if self.code != 'midtrans':
            return super()._get_default_payment_method_codes()
        
        return ['card', 'bank_transfer', 'ewallet']