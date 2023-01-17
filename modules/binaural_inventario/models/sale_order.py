import logging

from odoo import _, api
from odoo.exceptions import ValidationError
from odoo.models import Model

_logger = logging.getLogger()


class SaleOrderInherited(Model):
    _inherit = "sale.order"

    @api.constrains("order_line")
    def _constrains_order_line_sales_policy(self):
        for sale_order in self:
            if len(sale_order.order_line):
                product = self._check_order_lines(sale_order.order_line)
                if product:
                    raise ValidationError(_(f"El producto {product.name} tiene una política de ventas, la cantidad a vender" 
                                            f"debe ser un múltiplo de sí mismo o {product.sales_policy}"))
    @api.constrains('order_line')
    def _check_qty_available(self):
        overdraw_inventory = self.env['ir.config_parameter'].sudo().get_param('overdraw_inventory')
        if overdraw_inventory:
            for record in self:
                record.ensure_one()
                for line in record.order_line:
                    if line.product_id.type == 'product':
                        if line.product_uom_qty > line.product_id.free_qty:
                            #"The quantity of the product %s exceeds what is available (%i)"
                            raise ValidationError(_("La cantidad de producto %s excede lo disponible (%i)") %
                                                  (line.product_id.name, line.product_id.free_qty))

    def _check_order_lines(self, sale_order_line):
        for line in sale_order_line:
            product = line.product_id
            if product.sales_policy > 1 and product.available_qty >= product.sales_policy and (line.product_uom_qty % product.sales_policy) != 0:
                return product
        
        return False