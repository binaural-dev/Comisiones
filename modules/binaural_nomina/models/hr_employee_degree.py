from odoo import fields, models, _


class HrEmployeeDegree(models.Model):
    _name = "hr.employee.degree"
    _description = "Datos de estudios realizados por un empleado"

    name = fields.Char(string="Título Obtenido", required=True)
    employee_id = fields.Many2one("hr.employee", string="Empleado", required=True)
    school = fields.Char(string="Institución Académica")
    date_end = fields.Date(string="Año de Egreso")
    degree = fields.Selection(
        selection=[("high_school", "Bachiller"), ("technician", "Técnico"),
                   ("college", "Universitario"), ("master", "Maestría"), ("doctorate", "Doctorado")],
        string="Grado de instrucción", required=True)
