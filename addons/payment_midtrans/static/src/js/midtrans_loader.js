odoo.define("payment_midtrans.snap", function (require) {
    "use strict";

    const rpc = require("web.rpc");

    document.addEventListener("click", async (ev) => {
        if (ev.target.id !== "midtrans-pay") return;

        const data = await rpc.query({
            route: "/payment/midtrans/snap",
            params: window.paymentContext,
        });

        window.snap.pay(data.token);
    });
});
