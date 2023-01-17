from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from werkzeug.urls import url_encode
import logging
_logger = logging.getLogger(__name__)


class PurchaseOrderLineBinauralCompras(models.Model):
    _inherit = 'purchase.order.line'


    def default_alternate_currency(self):
        alternate_currency = int(
            self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))

        return alternate_currency or False

    @api.depends('order_id.foreign_currency_rate', 'price_unit', 'product_qty')
    def _amount_all_foreign(self):
        """
        Compute the foreign total amounts of the SO.
        """
        decimal_function = self.env['decimal.precision'].search(
            [('name', '=', 'decimal_quantity')]
        )
        for order_line in self:
            name_foreign_currency = order_line.order_id.foreign_currency_id.name
            name_base_currency = 'USD' if name_foreign_currency == 'VEF' else 'VEF'
            value_rate = 0

            value_rate = decimal_function.getCurrencyValue(
                rate=order_line.order_id.foreign_currency_rate,
                base_currency=name_base_currency,
                foreign_currency=name_foreign_currency
            )
                        
            order_line.foreign_price_unit = order_line.price_unit * value_rate
            order_line.foreign_subtotal = order_line.foreign_price_unit * order_line.product_qty


    company_currency_id = fields.Many2one(related='company_id.currency_id', string='Company Currency',
                                          readonly=True, store=True,
                                          help='Utility field to express amount currency')
    foreign_price_unit = fields.Monetary(
        string='Precio Alterno', store=True, readonly=True, compute='_amount_all_foreign', tracking=4)
    foreign_subtotal = fields.Monetary(
        string='Subtotal Alterno', store=True, readonly=True, compute='_amount_all_foreign', tracking=4)
    foreign_currency_id = fields.Many2one('res.currency', default=default_alternate_currency,
                                          tracking=True)