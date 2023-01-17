from odoo import fields, models


class HrEmployeeType(models.Model):
    _name = "hr.employee.type"
    _description = "Employee Type"

    name = fields.Char(string="Description", required=True)
    code = fields.Char(required=True)

    def name_get(self):
        """Change the display name of the employee type to show the code as long as the name."""
        result = []
        for employee_type in self:
            result.append((employee_type.id, f"{employee_type.code} {employee_type.name}"))
        return result
