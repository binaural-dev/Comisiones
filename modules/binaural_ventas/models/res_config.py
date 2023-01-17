from odoo import api, fields, models


class ResConfigSettingsBinauralVentas(models.TransientModel):
    _inherit = "res.config.settings"

    not_cost_higher_price_sale = fields.Boolean()
    # "No Permitir Costo Mayor o igual al Precio de venta"
    not_qty_on_hand_less_than_zero_sale = fields.Boolean(default=True)

    def set_values(self):
        super().set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "not_cost_higher_price_sale", self.not_cost_higher_price_sale
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "not_qty_on_hand_less_than_zero_sale", self.not_qty_on_hand_less_than_zero_sale
        )

    @api.model
    def get_values(self):
        res = super().get_values()
        res["not_cost_higher_price_sale"] = (
            self.env["ir.config_parameter"].sudo().get_param("not_cost_higher_price_sale")
        )
        res["not_qty_on_hand_less_than_zero_sale"] = (
            self.env["ir.config_parameter"].sudo().get_param("not_qty_on_hand_less_than_zero_sale")
        )
        return res
