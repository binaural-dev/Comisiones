from odoo.models import Model
from odoo.fields import Many2many

class ProductCategory(Model):
    _inherit = 'product.category'
    
    commission_policy_category_rel = Many2many(
        'commission.policy'
    )
    
    commission_policy_image_category_rel = Many2many(
        "commission.policy.image"
    )