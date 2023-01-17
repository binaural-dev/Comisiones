from odoo.models import Model
from odoo.fields import Many2one

class ProductTemplate(Model):
    _inherit = 'product.template'

    commission_policy_id = Many2one(
        'commission.policy',
        string="Commission"
    )
    
    commission_policy_image_id = Many2one(
        'commission.policy.image',
        string="Commission image"
    )