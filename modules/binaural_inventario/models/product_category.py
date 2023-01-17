from odoo import models, fields

class ProductCategory(models.Model):
    _inherit = 'product.category'
    _check_company_auto = True

    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company
    )