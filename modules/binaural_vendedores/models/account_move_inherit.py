import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    seller_id = fields.Many2one(
        "hr.employee",
        string="Seller",
        track=True,
        help="Partner's seller reference."
    )
