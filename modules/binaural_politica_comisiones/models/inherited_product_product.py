from odoo.models import Model
from odoo.fields import Many2many, Many2one

class ProductProduct(Model):
    _inherit = 'product.product'
    
    commission_policy_product_rel = Many2many(
        'commission.policy'
    )
    
    commission_policy_id = Many2one(
        'commission.policy'
    )
    
    commission_policy_image_category_rel = Many2many(
        "commission.policy.image"
    )
    
    commission_policy_image_id = Many2one(
        "commission.policy.image"
    )

