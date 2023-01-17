from odoo.models import Model
from odoo.fields import (
    Integer,
    Float,
    Boolean,
    Many2one
)

class CommissionPolicyImageLine(Model):
    _name = "commission.policy.image.line"
    _description = "Image of the exact moment when a date range is requested or modified."

    date_from = Integer(
        "Since",
        required=True,
        default=1,
        help="From days"
    )
    
    date_until = Integer(
        "Until",
        required=True,
        help="until days"
    )
    
    commission = Float(
        "Commission",
        required=True,
        help="Commission percentage"
    )
    
    percentage_report = Float(
        "Percentage for Reports",
        help="Commission percentage of reports"
    )
    
    not_applied = Boolean(
        "Do Not Apply for Report",
        help="Do not apply this restriction to the report"
    )
    
    policy_image_id = Many2one(
        "commission.policy.image",
        string="Commission History",
        required=True,
        ondelete="cascade",
    )
