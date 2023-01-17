from odoo.models import Model
from odoo.fields import Many2many

class ProductBrand(Model):
    _inherit = 'product.brand'
    
    commission_policy_brand_rel = Many2many(
        'commission.policy'
    )
    
    commission_policy_image_brand_rel = Many2many(
        'commission.policy.image'
    )