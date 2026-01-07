from odoo import http
from odoo.http import request
import requests
import base64

class MidtransController(http.Controller):

    @http.route("/payment/midtrans/snap", type="json", auth="public")
    def midtrans_snap(self, reference, amount, partner):
        provider = request.env["payment.provider"].sudo().search([("code", "=", "midtrans")], limit=1)

        auth = base64.b64encode(
            (provider.midtrans_server_key + ":").encode()
        ).decode()

        payload = {
            "transaction_details": {
                "order_id": reference,
                "gross_amount": int(amount),
            },
            "customer_details": {
                "first_name": partner.get("name"),
                "email": partner.get("email"),
            },
        }

        url = (
            "https://app.sandbox.midtrans.com/snap/v1/transactions"
            if provider.midtrans_environment == "sandbox"
            else "https://app.midtrans.com/snap/v1/transactions"
        )

        res = requests.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/json",
            },
            timeout=20,
        )

        return res.json()
