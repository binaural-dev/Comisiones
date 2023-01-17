
from odoo.api import constrains
from odoo.exceptions import ValidationError
from odoo.fields import (
    Float,
    Integer,
    Many2one,
)
from odoo.models import Model
from odoo.tools.float_utils import float_compare
from odoo import _

class CommissionPolicyLine(Model):
    _name = "commission.policy.line"
    _description = "Commission percentage based in a certain range date"

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
    
    policy_id = Many2one(
        "commission.policy",
        string="Commission politicy",
        required=True,
        ondelete="cascade"
    )

    @constrains("commission")
    def _check_commission_non_negative(self):
        for commission_line in self:
            if float_compare(commission_line.commission, 0.0, precision_digits=2) < 0:
                raise ValidationError(_("The commission cannot be less than zero!"))