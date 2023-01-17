from odoo import models, fields, api
class Brand(models.Model):
    _name = 'product.brand'
    _description = 'Brands'

    active = fields.Boolean(
        'Active', 
        default=True
    )
    name = fields.Char(
        string='Name',
        required=True,
        help='Brand name'
    )