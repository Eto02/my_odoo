/** @odoo-module */
/* global Stripe */

import { _t } from '@web/core/l10n/translation';
const {ConnectionLostError, RPCError} = require('@web/core/network/rpc_service');
import paymentForm from '@payment/js/payment_form'; 
const {jsonrpc} = require('@web/core/network/rpc_service');
import { BlockUI, unblockUI } from "@web/core/ui/block_ui";
import { patch } from '@web/core/utils/patch';

console.log('Midtrans Payment Form Module loaded');

let snapScriptTag = document.createElement('script');

// Load Snap JS when document is ready
document.addEventListener('DOMContentLoaded', function() {
    BlockUI();
    if(window.location.pathname.indexOf('/shop/payment') > -1) {
        jsonrpc('/midtrans/get_snap_js').then(function(response) {
            console.log('Snap JS response:', response);
            
            if(response.production == "1") {
                snapScriptTag.src = "https://app.midtrans.com/snap/snap.js";
            } else {
                snapScriptTag.src = "https://app.sandbox.midtrans.com/snap/snap.js";
            }
            
            snapScriptTag.setAttribute('data-client-key', response.client_key);
            snapScriptTag.type = 'text/javascript';
            snapScriptTag.async = true;
            
            snapScriptTag.onload = function() {
                console.log('Snap JS loaded successfully');
                unblockUI();
            };
            
            snapScriptTag.onerror = function() {
                console.error('Failed to load Snap JS');
                unblockUI();
            };
            
            document.head.appendChild(snapScriptTag);
        }).catch(function(error) {
            console.error('Error loading Snap JS:', error);
            unblockUI();
        });
    }
});

/**
 * Patch PaymentForm to handle Midtrans payments
 */
patch(paymentForm.prototype, {
    /**
     * Set busy state for UI
     */
    _setStateBusy(isBusy) {
        if (isBusy) {
            BlockUI();
        } else {
            if (BlockUI) {
                unblockUI();
            }
        }
    },

    /**
     * Get form data as object
     */
    _getFormData($el) {
        const formArray = [];
        $el.find('input, select, textarea').each(function() {
            formArray.push({
                name: $(this).attr('name'),
                value: $(this).val()
            });
        });
        return formArray.reduce((m, e) => { m[e.name] = e.value; return m; }, {});
    },

    /**
     * Attach event listener to payment button
     */
    _attachEventListener(selector) {
        const self = this;
        const $btn = $(selector);
        const $form = $btn.parents('form');
        const $acquirer = $btn.closest('div.oe_sale_acquirer_button,div.oe_quote_acquirer_button,div.o_website_payment_new_payment');
        const acquirer_id = $("#acquirer_midtrans").val() || $acquirer.data('id') || $acquirer.data('acquirer_id');
        const access_token = $("input[name='access_token']").val() || $("input[name='token']").val();

        console.log('Event listener attached, acquirer_id:', acquirer_id);
        
        this._setStateBusy(true);

        const formData = this._getFormData($form);

        jsonrpc('/midtrans/get_token', {
            acquirer_id: acquirer_id,
            order_id: formData['order_id'],
            amount: formData['amount'],
            reference: formData['reference'],
            return_url: formData['return_url']
        }).then(function(response) {
            console.log('Token response:', response);
            
            if (response.snap_errors) {
                alert(response.snap_errors.join('\n'));
                self._setStateBusy(false);
                return;
            }

            snapScriptTag.setAttribute('data-client-key', response.client_key);
            self._setStateBusy(false);

            if (typeof window.snap !== 'undefined') {
                window.snap.pay(response.snap_token, {
                    onSuccess: function(result) {
                        console.log('Payment successful:', result);
                        jsonrpc('/midtrans/validate', {
                            reference: result.order_id,
                            transaction_status: 'done',
                            message: result.status_message
                        }).then(function() {
                            window.location = '/shop/confirmation';
                        });
                    },
                    onPending: function(result) {
                        console.log('Payment pending:', result);
                        jsonrpc('/midtrans/validate', {
                            reference: result.order_id,
                            transaction_status: 'pending',
                            message: result.status_message
                        }).then(function() {
                            window.location = '/shop/confirmation';
                        });
                    },
                    onError: function(result) {
                        console.log('Payment error:', result);
                        jsonrpc('/midtrans/validate', {
                            reference: result.order_id,
                            transaction_status: 'error',
                            message: result.status_message
                        }).then(function() {
                            window.location = '/shop/confirmation';
                        });
                    },
                    onClose: function() {
                        console.log('Payment popup closed');
                        self._setStateBusy(false);
                    }
                });
            } else {
                alert(_t('Payment gateway not available'));
                self._setStateBusy(false);
            }
        }).catch(function(error) {
            console.error('Token request error:', error);
            alert(_t('Error getting payment token'));
            self._setStateBusy(false);
        });
    },

    /**
     * Override _processRedirectFlow for Midtrans
     */
    async _processRedirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
         console.log("Processing Midtrans redirect flow");
        console.log("Processing values:", processingValues);
        if (providerCode.toLowerCase() !== 'midtrans') {
            console.log("Not Midtrans provider, using default flow");
            return await super.submit(...arguments);
        }

       

        const div = document.createElement('div');
        div.innerHTML = processingValues['redirect_form_html'];
        const redirectForm = div.querySelector('#midtrans-payment-button');
        
        console.log("Redirect form button:", redirectForm);

        if (redirectForm) {
          redirectForm.submit();
        } else {
            alert(_t('Payment button not found'));
        }
    },

    /**
     * Override _initiatePaymentFlow to add logging
     */
    async _initiatePaymentFlow(providerCode, paymentOptionId, paymentMethodCode, flow) {
        console.log("=== MIDTRANS PAYMENT FLOW ===");
        console.log("Provider Code:", providerCode);
        console.log("Payment Option ID:", paymentOptionId);
        console.log("Payment Method Code:", paymentMethodCode);
        console.log("Flow Type:", flow);
        console.log("Transaction Route:", this.paymentContext['transactionRoute']);
        
        try {
            console.log("Preparing to call RPC for transaction route"); 
            console.log("Transaction Route Params:", this._prepareTransactionRouteParams());
            console.log(this.paymentContext['transactionRoute']);
            const processingValues = await this.rpc(
                this.paymentContext['transactionRoute'], 
                this._prepareTransactionRouteParams()
            );

            
            console.log("Processing Values Received:", processingValues);
            
            if (flow === 'redirect') {
                console.log("Calling _processRedirectFlow");
                await this._processRedirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues);
            } else if (flow === 'direct') {
                console.log("Calling _processDirectFlow");
                await this._processDirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues);
            } else if (flow === 'token') {
                console.log("Calling _processTokenFlow");
                await this._processTokenFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues);
            } else {
                console.warn("Unknown flow type:", flow);
            }
            
        } catch (error) {
            console.error("Payment flow error:", error);
            if (error instanceof RPCError) {
                console.error("RPC Error message:", error.data?.message);
                this._displayErrorDialog(_t("Payment processing failed"), error.data.message);
                this._enableButton();
            } else {
                console.error("Non-RPC error:", error);
                throw error;
            }
        }
    }
});

