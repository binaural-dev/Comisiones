from odoo import fields, models


class HrEmployeeEntryOccupation(models.Model):
    _name = "hr.employee.entry.occupation"
    _description = "Employee Entry Occupation"

    name = fields.Char(string="Description", required=True)
    code = fields.Char(required=True)

    def name_get(self):
        """Change the display name of the occupation to show the code as long as the name."""
        result = []
        for occupation in self:
            result.append((occupation.id, f"{occupation.code} {occupation.name}"))
        return result
