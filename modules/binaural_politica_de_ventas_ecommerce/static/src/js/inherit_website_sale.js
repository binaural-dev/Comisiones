odoo.define("binaural_politica_de_ventas_ecommerce.inherit_website_sale", function(require) {
    'use strict';

    var core = require("web.core");
    var publicWidget = require("web.public.widget");

    var WebsiteSaleInherited = publicWidget.registry.WebsiteSale;

    var _t = core._t;

    WebsiteSaleInherited.include({
        events: _.extend({}, WebsiteSaleInherited.prototype.events, {
            'change input.quantity': '_onChangeSalesPolicy',
        }),
        _onClickAddCartJSON: function (ev){
            return this.onBinClickAddCartJSON(ev);
        },
        onBinClickAddCartJSON: function (ev) {
            ev.preventDefault();
            let $link = $(ev.currentTarget);
            let $inputQuantity = $link.closest('.input-group').find("input.quantity");
            let $salesPolicyInput = $link.closest('.input-group').find('input.sales_policy');
            // var min = parseFloat($inputQuantity.data("min") || 0);
            const salesPolicy = parseFloat($salesPolicyInput.val());
            const max = parseFloat($inputQuantity.data("max") || Infinity);
            const previousQty = parseFloat($inputQuantity.val() || 0, 10);
            const quantity = ($link.has(".fa-minus").length ? ((salesPolicy)*-1) : salesPolicy) + previousQty;
            const newQty = quantity > salesPolicy ? (quantity < max ? quantity : max) : salesPolicy;
    
            if (newQty !== previousQty) {
                $inputQuantity.val(newQty).trigger('change');
            }
            return false;
        },
        _onChangeSalesPolicy: function (ev) {
            let $input = $(ev.currentTarget);
             
            const currentQty = $input.val();
            const salesPolicy = $input.closest('.input-group').find('input.sales_policy').val();

            if ((currentQty % salesPolicy) !== 0) {
                const newQty = Math.round(currentQty / salesPolicy) * salesPolicy;
                $input.val(newQty);
            }

        }
    });
});