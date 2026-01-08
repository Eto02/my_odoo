/** @odoo-module **/

import paymentForm from '@payment/js/payment_form';

paymentForm.include({
    
    async _processPayment(provider, paymentOptionId, flow) {
        if (provider !== 'midtrans') {
            return this._super(...arguments);
        }
        
        const snapToken = this.el.querySelector('input[name="snap_token"]')?.value;
        const clientKey = this.el.querySelector('input[name="client_key"]')?.value;
        const useSandbox = this.el.querySelector('input[name="use_sandbox"]')?.value === 'True';
        
        if (!snapToken || !clientKey) {
            this._displayError(
                this.el.querySelector('.o_payment_form_midtrans'),
                'Missing Midtrans configuration'
            );
            return;
        }
        
        await this._loadMidtransSnap(useSandbox);
        
        return new Promise((resolve, reject) => {
            window.snap.pay(snapToken, {
                onSuccess: (result) => {
                    console.log('Midtrans payment success:', result);
                    resolve();
                },
                onPending: (result) => {
                    console.log('Midtrans payment pending:', result);
                    resolve();
                },
                onError: (result) => {
                    console.error('Midtrans payment error:', result);
                    this._displayError(
                        this.el.querySelector('.o_payment_form_midtrans'),
                        'Payment failed: ' + (result.status_message || 'Unknown error')
                    );
                    reject(result);
                },
                onClose: () => {
                    console.log('Midtrans popup closed');
                    this._displayError(
                        this.el.querySelector('.o_payment_form_midtrans'),
                        'Payment cancelled'
                    );
                    reject(new Error('Payment cancelled'));
                }
            });
        });
    },
    
    async _loadMidtransSnap(useSandbox) {
        if (window.snap) {
            return; // Already loaded
        }
        
        const snapUrl = useSandbox 
            ? 'https://app.sandbox.midtrans.com/snap/snap.js'
            : 'https://app.midtrans.com/snap/snap.js';
        
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = snapUrl;
            script.setAttribute('data-client-key', this.el.querySelector('input[name="client_key"]').value);
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
});