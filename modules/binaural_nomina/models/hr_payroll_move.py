from odoo import api, fields, models, _


class HrPayrollMove(models.Model):
    _name = "hr.payroll.move"
    _description = "Pagos de nómina"
    _rec_name = "employee_name"
    _inherit = ["mail.thread"]

    move_type = fields.Selection(
        [
            ("salary", "Salario"),
            ("vacation", "Vacaciones"),
            ("benefits", "Prestaciones"),
            ("profit_sharing", "Utilidades"),
            ("liquidation", "Liquidación"),
        ],
        string="Tipo",
        default="salary",
    )
    employee_id = fields.Many2one("hr.employee", string="Empleado", required=True)
    employee_name = fields.Char(string="Nombre", related="employee_id.name", store=True)
    employee_prefix_vat = fields.Selection(related="employee_id.prefix_vat", store=True)
    employee_vat = fields.Char(string="RIF", related="employee_id.vat", store=True)
    employee_private_mobile_phone = fields.Char(
        string="Teléfono personal", related="employee_id.private_mobile_phone", store=True
    )
    date = fields.Date(string="Fecha del recibo de pago", default=fields.Date.today())
    department_id = fields.Many2one(
        "hr.department", string="Departamento", related="employee_id.department_id", store=True
    )

    total_basic = fields.Float(string="Salario base")
    total_deduction = fields.Float(string="Total deducción")
    total_accrued = fields.Float(string="Total devengado")
    total_net = fields.Float(string="Total neto")

    total_assig = fields.Float(string="Total asignaciones")
    advance_of_benefits = fields.Float(string="Anticipo de prestaciones")
    benefits_payment = fields.Float(string="Prestaciones")
    profit_sharing_payment = fields.Float(string="Utilidades")

    date_from_vacation = fields.Date()
    date_to_vacation = fields.Date()

    vacational_period = fields.Char(
        string="Periodo vacacional", compute="_compute_vacational_period"
    )
    vacation_days = fields.Integer(string="Días correspondientes de vacaciones")
    vacation_bonus_days = fields.Integer(string="Días correspondientes de bono vacacional")
    consumed_vacation_days = fields.Integer(string="Días consumidos de vacaciones")
    total_vacation_bonus = fields.Float(string="Total bono vacacional")
    total_vacation = fields.Float(string="Total pago por disfrute de vacaciones")

    @api.depends("date_from_vacation", "date_to_vacation")
    def _compute_vacational_period(self):
        for move in self:
            if not (bool(move.date_from_vacation) and bool(move.date_to_vacation)):
                move.vacational_period = ""
                continue
            move.vacational_period = (
                f"{move.date_from_vacation.strftime('%d/%m/%Y')}"
                f"- {move.date_to_vacation.strftime('%d/%m/%Y')}"
            )
