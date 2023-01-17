from odoo import fields, models, api, _

class AccountMoveLineIgtf(models.Model):
    _inherit = "account.move.line"

    invoice_parent_id = fields.Many2one(string='Factura Padre')
