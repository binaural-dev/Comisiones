import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class StockPickingInherit(models.Model):
    _inherit = "stock.picking"

    seller_id = fields.Many2one("hr.employee", related="partner_id.seller_id", string="Seller", track=True, help="Partner's seller reference.")