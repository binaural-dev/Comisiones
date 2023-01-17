from odoo import api, fields, models, _


class HrPayslispsEmployeeIhn(models.TransientModel):
    _inherit = "hr.payslip.employees"

    structure_type_id = fields.Many2one(
        "hr.payroll.structure.type", string="Structure Type", required=True, default=False
    )

    structure_id = fields.Many2one(
        "hr.payroll.structure",
        string="Structure",
        required=True,
        domain="[('type_id','=', structure_type_id)]",
    )

    @api.onchange("structure_type_id")
    def _onchange_structure_type_id(self):
        if self.structure_type_id:
            for record in self:
                record.employee_ids = self._get_employees().filtered(
                    lambda employee: employee.contract_id.structure_type_id
                    == self.structure_type_id
                )
