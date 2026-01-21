/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import publicWidget from '@web/legacy/js/public_widget';

/**
 * Midtrans Payment Integration untuk Odoo 17
 * Menangani payment flow dengan Snap popup
 */
publicWidget.registry.MidtransPaymentForm = publicWidget.Widget.extend({
    selector: 'button[name="o_payment_submit_button"][data-provider-code="midtrans"]',
    events: {
        'click': '_onClickPaymentButton',
    },

    /**
     * Click handler untuk payment button
     */
    _onClickPaymentButton(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        const button = ev.currentTarget;
        const txId = button.dataset.txId;
        const providerCode = button.dataset.providerCode;

        if (providerCode !== 'midtrans') {
            return;
        }

        this._processPayment(txId);
    },

    /**
     * Main payment processing
     */
    async _processPayment(txId) {
        try {
            this._showLoading(true);

            // Get snap token dari server
            const response = await rpc('/payment/midtrans/get_snap_token', {
                transaction_id: parseInt(txId),
            });

            if (response.error) {
                this._showError(_t('Payment Error'), response.error);
                return;
            }

            if (!response.snap_token) {
                this._showError(_t('Payment Error'), _t('Invalid response from payment gateway'));
                return;
            }

            // Load Snap JS jika belum loaded
            await this._ensureSnapLoaded(response.snap_url);

            this._showLoading(false);

            // Open Snap popup
            this._openSnapPopup(response.snap_token, txId);

        } catch (error) {
            console.error('Midtrans payment error:', error);
            this._showError(_t('Payment Error'), error.message);
        }
    },

    /**
     * Ensure Snap JS loaded
     */
    async _ensureSnapLoaded(snapUrl) {
        if (typeof window.snap !== 'undefined') {
            return Promise.resolve();
        }

        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = snapUrl;
            script.async = true;
            script.onload = () => resolve();
            script.onerror = () => reject(new Error('Failed to load Snap JS'));
            document.head.appendChild(script);
        });
    },

    /**
     * Open Snap payment popup
     */
    _openSnapPopup(snapToken, txId) {
        if (typeof window.snap === 'undefined') {
            this._showError(_t('Error'), _t('Payment gateway not loaded'));
            return;
        }

        window.snap.pay(snapToken, {
            onSuccess: (result) => {
                console.log('Payment success:', result);
                this._handlePaymentSuccess(result, txId);
            },
            onPending: (result) => {
                console.log('Payment pending:', result);
                this._handlePaymentPending(result, txId);
            },
            onError: (result) => {
                console.log('Payment error:', result);
                this._handlePaymentError(result, txId);
            },
            onClose: () => {
                console.log('Snap popup closed');
                this._showLoading(false);
            }
        });
    },

    /**
     * Handle successful payment
     */
    async _handlePaymentSuccess(result, txId) {
        try {
            const response = await rpc('/payment/midtrans/success', {
                transaction_id: parseInt(txId),
                snap_result: result,
            });

            if (response.success) {
                // Redirect ke success page
                window.location.href = response.redirect_url || '/payment/status';
            } else {
                this._showError(_t('Payment Error'), response.message);
            }
        } catch (error) {
            console.error('Error handling payment success:', error);
            this._showError(_t('Error'), error.message);
        }
    },

    /**
     * Handle pending payment
     */
    async _handlePaymentPending(result, txId) {
        console.log('Payment pending, waiting for callback...');
        // Redirect ke pending page
        window.location.href = '/payment/status';
    },

    /**
     * Handle payment error
     */
    async _handlePaymentError(result, txId) {
        this._showError(_t('Payment Error'), _t('Payment failed. Please try again.'));
    },

    /**
     * Show/hide loading indicator
     */
    _showLoading(show) {
        const loader = document.getElementById('midtrans_loading');
        if (loader) {
            if (show) {
                loader.classList.remove('d-none');
            } else {
                loader.classList.add('d-none');
            }
        }
    },

    /**
     * Show error notification
     */
    _showError(title, message) {
        this._showLoading(false);
        
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.role = 'alert';
        alertDiv.innerHTML = `
            <strong>${title}:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const paymentForm = document.querySelector('[data-provider-code="midtrans"]');
        if (paymentForm) {
            paymentForm.parentElement.insertBefore(alertDiv, paymentForm);
        }
    }
});

export default {
    MidtransPaymentForm,
};
