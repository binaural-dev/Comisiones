from odoo import fields, models


class HrPayrollBenefitAccumulatedDetail(models.Model):
    """
    This model is used for keeping track of all the registered payrroll benefits accumulation.

    Its records are created inside the _get_benefits() methods on the inherit of the employee model
    on this same module.
    """
    _name = "hr.payroll.benefits.accumulated.detail"

    date = fields.Date()
    employee_id = fields.Many2one("hr.employee")
    amount = fields.Float()
    accumulated_amount = fields.Float()
    type = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("annual", "Annual"),
        ]
    )
