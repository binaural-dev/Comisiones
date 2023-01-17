from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_confirm(self):
        """
        After the normal flow of the confirm button, updates the latest_price and the
        last_latest_standard_price of the product (and its template if the products variants are not
        active) of each line having the field update_latest_standard_price as True.

        We need the last_latest_standard_price to be able to return the latest price to its previous
        value if the purchase order is cancelled.
        """
        res = super().button_confirm()

        for line in self._get_lines_with_updatable_latest_standard_price():
            product = line.product_id

            product.last_latest_standard_price = line.latest_standard_price
            product.latest_standard_price = line.price_unit

            variants_are_active = product.get_variants_are_active()
            if not variants_are_active:
                product.product_tmpl_id.last_latest_standard_price = line.latest_standard_price
                product.product_tmpl_id.latest_standard_price = line.price_unit

        return res

    def button_cancel(self):
        """
        After the normal flow of the cancel button, updates the latest_price of the product
        (and its template if the product variants are not active) of each line having the field
        update_latest_standard_price as True.

        We need to return the latest price to its previous value when the purchase order is
        cancelled.
        """
        super().button_cancel()

        for line in self._get_lines_with_updatable_latest_standard_price():
            product = line.product_id
            product.latest_standard_price = product.last_latest_standard_price

            variants_are_active = product.get_variants_are_active()
            if not variants_are_active:
                product.product_tmpl_id.latest_standard_price = (
                    product.product_tmpl_id.last_latest_standard_price
                )
        return True

    def _get_lines_with_updatable_latest_standard_price(self):
        return self.mapped("order_line").filtered(lambda l: l.update_latest_standard_price)


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.onchange("price_unit")
    def onchange_update_latest_standard_price(self):
        """
        If the price unit is changed, the update_latest_standard_price field is set to True by
        default.
        """
        self.update_latest_standard_price = self.price_unit > self.latest_standard_price

    latest_standard_price = fields.Monetary(compute="_compute_latest_standard_price", store=True)
    update_latest_standard_price = fields.Boolean(default=False)

    @api.depends("product_id")
    def _compute_latest_standard_price(self):
        for line in self:
            line.latest_standard_price = line.product_id.latest_standard_price
