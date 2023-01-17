from odoo import fields, models, _


class HrEmployeeDependant(models.Model):
    _name = "hr.employee.dependant"
    _description = "Dependientes de un empleado"

    name = fields.Char(string="Nombre", required=True)
    employee_id = fields.Many2one("hr.employee", string="Padre", required=True)
    birth_date = fields.Date("Fecha de Nacimiento", required=True)
    code = fields.Char(string="Nº de identificación", default="N/A")
    grade = fields.Char(string="Grado que Cursa")
    school_degree = fields.Selection(
        selection=[("maternal", "Maternal"), ("preschool", "Preescolar"),
                   ("elementary", "Primaria"), ("basic", "Básica"),
                   ("diversified", "Diversificada"), ("college", "Universitaria")],
        string="Nivel Escolar")
    school = fields.Char(string="Institución Escolar")
    school_address = fields.Char(string="Dirección Institución Escolar")
