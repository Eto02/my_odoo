from odoo import models, fields

class PaymentProviderMidtrans(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("midtrans", "Midtrans")],
        ondelete={"midtrans": "set default"},
    )

    midtrans_server_key = fields.Char(string="Midtrans Server Key", groups="base.group_system")
    midtrans_client_key = fields.Char(string="Midtrans Client Key")
    midtrans_environment = fields.Selection(
        [("sandbox", "Sandbox"), ("production", "Production")],
        default="sandbox",
    )
