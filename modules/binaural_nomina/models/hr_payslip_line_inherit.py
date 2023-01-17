from odoo import models, fields


class HrPayslipLine(models.Model):
    _inherit = "hr.payslip.line"

    is_a_days_line = fields.Boolean(string="Es una línea de días", default=False)
    is_a_hours_line = fields.Boolean(string="Es una línea de horas", default=False)
    employee_vat = fields.Char(string="Documento", related="employee_id.vat")
    category_code = fields.Char(string="Categoría", related="category_id.code")
    slip_state = fields.Selection(string="Estado", related="slip_id.state")
