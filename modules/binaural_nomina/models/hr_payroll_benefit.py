import logging

from datetime import date, datetime
from dateutil import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class HrPayrollBenefit(models.Model):
    _name = "hr.payroll.benefits.accumulated"
    _rec_name = "employee_name"
    _description = "Acumulado de Prestaciones"

    employee_id = fields.Many2one("hr.employee", string="Empleado", required=True)
    employee_name = fields.Char(related="employee_id.name")
    accumulated_benefits = fields.Float(string="Acumulado de prestaciones", required=True)
    accumulated_benefits_advance = fields.Float(
        string="Saldo acumulado de anticipos de prestaciones"
    )
    available_benefits = fields.Float(
        string="Saldo disponible de prestaciones total", compute="_compute_available_benefits"
    )
    available_benefits_to_pay = fields.Float(
        string="Saldo disponible de prestaciones", compute="_compute_available_benefits_to_pay"
    )
    accumulated_interest = fields.Float(string="Acumulado de intereses", required=True)
    date = fields.Date(string="Fecha del último cálculo", required=True)

    _sql_constraints = [
        (
            "unique_employee_id",
            "UNIQUE(employee_id)",
            "Este empleado ya tiene acumulado de prestaciones",
        ),
    ]

    @api.depends("accumulated_benefits", "accumulated_benefits_advance")
    def _compute_available_benefits(self):
        for benefit in self:
            benefit.available_benefits = (
                benefit.accumulated_benefits - benefit.accumulated_benefits_advance
            )

    @api.depends("available_benefits")
    def _compute_available_benefits_to_pay(self):
        for benefit in self:
            benefit.available_benefits_to_pay = (
                benefit.accumulated_benefits * 0.75
            ) - benefit.accumulated_benefits_advance

    def _compute_employee_mixed_monthly_wage(self):
        self.ensure_one()
        employee = self.employee_id
        seniority = employee.get_seniority_months_since_last_seniority_year()

        if seniority == 0:
            employee.mixed_monthly_wage = 0
            return

        months = seniority if seniority < 3 else 3
        moves = self.env["hr.payroll.move"].search(
            [
                ("employee_id", "=", employee.id),
                ("move_type", "=", "salary"),
            ]
        )
        date_from = date.today() + relativedelta.relativedelta(months=-(months))
        moves_in_between_three_months_and_now = moves.filtered(lambda m: m.date > date_from)
        moves_accrued_sum = sum(
            move.total_accrued for move in moves_in_between_three_months_and_now
        )
        employee.mixed_monthly_wage = moves_accrued_sum / months

    @api.model
    def get_monthly_benefits(self):
        calculo_prestaciones = (
            self.env["ir.config_parameter"].sudo().get_param("calculo_prestaciones")
        )
        if calculo_prestaciones != "mensual":
            return True

        benefits_days = int(
            self.env["ir.config_parameter"].sudo().get_param("dias_prestaciones_mes")
        )
        if not bool(benefits_days):
            raise UserError(
                _(
                    "No se ha definido la cantidad de días de prestaciones por mes en"
                    + "la configuración de nómina."
                )
            )

        employees = self.env["hr.employee"].search([])
        for employee in employees:
            if not employee.entry_date:
                continue

            seniority = employee._get_seniority()
            if seniority.months < 1 and seniority.years < 1:
                continue

            if employee.last_monthly_calculated_benefits:
                months_diff = relativedelta.relativedelta(
                    fields.Date.today(), employee.last_monthly_calculated_benefits
                ).months
                _logger.warning("Months diff: %s", (months_diff))
                if months_diff < 1:
                    continue

            employee._get_benefits(benefits_days, True)

    @api.model
    def get_quarterly_benefits(self):
        calculo_prestaciones = (
            self.env["ir.config_parameter"].sudo().get_param("calculo_prestaciones")
        )
        if calculo_prestaciones != "trimestral":
            return True

        benefits_days = (
            int(self.env["ir.config_parameter"].sudo().get_param("dias_prestaciones_mes")) * 3
        )

        if not bool(benefits_days):
            raise UserError(
                _(
                    "No se ha definido la cantidad de días de prestaciones por mes en"
                    + "la configuración de nómina."
                )
            )

        employees = self.env["hr.employee"].search([])
        for employee in employees:
            if not employee.entry_date:
                continue

            seniority = employee._get_seniority()
            if seniority.months < 3 and seniority.years < 1:
                continue

            if employee.last_quarterly_calculated_benefits:
                months_diff = relativedelta.relativedelta(
                    fields.Date.today(), employee.last_quarterly_calculated_benefits
                ).months
                if months_diff < 3:
                    continue

            employee._get_benefits(benefits_days, False)

    @api.model
    def get_annual_benefits(self):
        today = datetime.today().date()

        employees = self.env["hr.employee"].search([])
        for employee in employees:
            _logger.warning("Entry date: %s" % (employee.entry_date))
            entry_date = employee.entry_date
            if not entry_date or today.day != entry_date.day or today.month != entry_date.month:
                continue

            days_per_year = int(
                self.env["ir.config_parameter"].sudo().get_param("dias_prestaciones_anno")
            )
            if not bool(days_per_year):
                raise UserError(
                    _(
                        "No se ha definido la cantidad de días de prestaciones por año en"
                        + "la configuración de nómina."
                    )
                )

            maximum_of_days = int(
                self.env["ir.config_parameter"].sudo().get_param("maximo_dias_prestaciones_anno")
            )
            if not bool(maximum_of_days):
                raise UserError(
                    _(
                        "No se ha definido la cantidad máxima de días de prestaciones por año en"
                        + "la configuración de nómina."
                    )
                )

            seniority = employee._get_seniority_in_years()
            # Annual benefits calculation should start on the second year of the employee.
            if seniority < 2:
                continue

            days_per_employee_years = days_per_year * seniority

            benefits_days = (
                days_per_employee_years
                if days_per_employee_years < maximum_of_days
                else maximum_of_days
            )

            employee._get_benefits(benefits_days, is_annual=True)

    @api.model
    def get_benefits_interest(self):
        interest_rate = float(
            self.env["ir.config_parameter"].sudo().get_param("tasa_intereses_prestaciones")
        )
        if not bool(interest_rate):
            raise UserError(
                _(
                    "No se ha definido la tasa mensual de intereses de prestaciones"
                    + "en la configuración de nómina."
                )
            )
        daily_interest_rate = interest_rate / 30
        _logger.warning("Daily interest rate: %s", daily_interest_rate)

        employees = self.env["hr.employee"].search([])
        _logger.warning("Employees: %s", employees)
        for employee in employees:
            _logger.warning("Employee: %s", employee)
            benefits_accumulated = self.env["hr.payroll.benefits.accumulated"].search(
                [
                    ("employee_id", "=", employee.id),
                ]
            )
            _logger.warning("Benefits accumulated: %s", benefits_accumulated)
            if not any(benefits_accumulated):
                continue

            available_benefits = benefits_accumulated[-1]["available_benefits"]
            daily_interest = available_benefits * (daily_interest_rate / 100)
            employee._register_payroll_benefits(interests=daily_interest)

    @api.model
    def get_available_benefits(self, employee_id):
        benefit = self.env["hr.payroll.benefits.accumulated"].search(
            [
                ("employee_id", "=", employee_id),
            ],
            limit=1,
        )
        return benefit.available_benefits

    @api.model
    def get_accumulated_interest(self, employee_id):
        benefit = self.env["hr.payroll.benefits.accumulated"].search(
            [
                ("employee_id", "=", employee_id),
            ],
            limit=1,
        )
        return benefit.accumulated_interest
