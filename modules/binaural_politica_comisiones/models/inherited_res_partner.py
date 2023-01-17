from odoo.models import Model
from odoo.fields import Many2many

class ResPartner(Model):
    _inherit = 'res.partner'
    
    commission_policy_client_rel = Many2many(
        'commission.policy'
    )
    
    commission_policy_image_client_rel = Many2many(
        "commission.policy.image"
    )