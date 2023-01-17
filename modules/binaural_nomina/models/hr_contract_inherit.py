from odoo import api, fields, models


class BinauralHrContractInherit(models.Model):
    _inherit = "hr.contract"
    _description = "Herencia contrato para Venezuela"

    daily_wage = fields.Float(
        string="Salario diario", compute="_compute_daily_wage", store=True
    )
    hourly_daily_wage = fields.Float(
        string="Salario diario por hora",
        compute="_compute_hourly_daily_wage",
        store=True,
    )
    schedule_payment_type = fields.Selection(
        [
            ("weekly", "Semanal"),
            ("half-monthly", "Quincenal"),
            ("monthly", "Mensual"),
        ],
        "Pago programado",
        default="monthly",
    )
    salary_type = fields.Selection(
        [("fixed", "Fijo"), ("variable", "Variable")],
        "Tipo de salario",
        default="fixed",
    )
    analytic_account_id = fields.Many2one(
        string="Cuenta analítica", related="department_id.accounting_analytical_id"
    )

    @api.model
    def create(self, vals):
        res = super().create(vals)
        register_salary_change(self, res, vals)
        return res

    def write(self, vals):
        res = super().write(vals)
        contract = self.env["hr.contract"].search([("id", "=", self.id)])
        register_salary_change(self, contract, vals)
        return res

    @api.depends("wage")
    def _compute_daily_wage(self):
        for contract in self:
            contract.daily_wage = contract.wage / 30

    @api.depends("daily_wage", "resource_calendar_id.hours_per_day")
    def _compute_hourly_daily_wage(self):
        for contract in self:
            hours = contract.resource_calendar_id.hours_per_day
            if contract.hourly_daily_wage != 0:
                contract.hourly_daily_wage = contract.hourly_daily_wage / hours

    def get_integral_daily_wage(self):
        self.ensure_one()
        employee_id = self.employee_id
        employee_salary_payments = employee_id.get_all_payroll_moves()

        if not employee_salary_payments:
            return 0

        last_accrued = employee_salary_payments[-1]["total_accrued"]
        bonus_days_alicuot = employee_id.get_vacation_bonus_days_alicuot()
        profit_sharing_days_alicuot = (
            employee_id.get_profit_sharing_days_alicuot()
        )
        return (last_accrued / 30) + bonus_days_alicuot + profit_sharing_days_alicuot


def register_salary_change(self, contract, vals):
    """
    Makes a register of a salary change for the given contract.

    If a salary change has already been made for the same employee on the current day, then instead
    of creating a new register the one that exists is updated.

    Parameters
    ----------
    contract : Recordset(hr.contract)
        The contract of the employee in which the salary change is made.
    vals : dict
        The values that are being updated.
    """
    salary_changed = False
    keys = ("wage", "wage_type", "hourly_wage")
    for key in keys:
        if key in vals:
            salary_changed = True
            break
    if not salary_changed:
        return

    salary_change_model = self.env["hr.employee.salary.change"]
    today_salary_change = salary_change_model.search(
        [
            ("employee_id", "=", contract.employee_id.id),
            ("date", "=", fields.Date.today()),
        ],
        limit=1
    )
    if today_salary_change:
        today_salary_change.sudo().write(
            {
                "wage_type": contract.wage_type,
                "wage": contract.wage,
                "hourly_wage": contract.hourly_wage,
            }
        )
        return

    self.env["hr.employee.salary.change"].sudo().create(
        {
            "contract_id": contract.id,
            "wage_type": contract.wage_type,
            "wage": contract.wage,
            "hourly_wage": contract.hourly_wage,
        }
    )
