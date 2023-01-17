from odoo import api, fields, models


class HrEmployeeSalaryChange(models.Model):
    _name = "hr.employee.salary.change"
    _description = "Variaciones Salariales"

    date = fields.Date(string="Fecha", default=fields.Date.today())
    contract_id = fields.Many2one(
        "hr.contract", string="Contrato", readonly=True)
    employee_id = fields.Many2one(
        "hr.employee", string="Empleado", related="contract_id.employee_id", store=True)
    wage_type = fields.Selection(
        selection=[("monthly", "Salario Fijo Mensual"), ("hourly", "Salario por Hora")],
        string="Tipo de salario", readonly=True)
    wage = fields.Float(string="Salario Mensual", readonly=True)
    hourly_wage = fields.Float(string="Salario por Hora", readonly=True)
