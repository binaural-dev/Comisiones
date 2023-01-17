from datetime import date, datetime
from calendar import isleap
from dateutil.relativedelta import relativedelta

from odoo.addons.hr_payroll.models.browsable_object import BrowsableObject
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class BinauralHrPayslipInherit(models.Model):
    _inherit = "hr.payslip"

    benefits_advance = fields.Float(
        string="Anticipo",
        readonly=True,
        states={"draft": [("readonly", False)], "verify": [("readonly", False)]},
    )
    benefits_advance_percentage = fields.Float(
        string="% Anticipo",
        readonly=True,
        store=True,
        compute="_compute_benefits_advance_percentage",
        inverse="_inverse_benefits_advance_percentage",
        states={"draft": [("readonly", False)], "verify": [("readonly", False)]},
    )
    is_benefits = fields.Boolean(compute="_compute_is_benefits")
    schedule_payment = fields.Selection(
        [
            ("monthly", "Mensual"),
            ("quarterly", "Quincenal"),
            ("annually", "Anual"),
            ("weekly", "Semanal"),
            ("bi-weekly", "Bi-semanal"),
            ("days", "Dias"),
        ],
        compute="_compute_schedule_pay",
        store=True,
        readonly=False,
        string="Frecuencia de Pago",
    )
    struct_category = fields.Selection(related="struct_id.category", readonly=True)

    def default_accounting_analytical(self):
        return self.env["ir.config_parameter"].sudo().get_param("cuenta_analitica_departamentos")

    default_accounting_analytical = fields.Boolean(
        string="Cuenta analitica por departamento",
        default=default_accounting_analytical,
        store=False,
    )

    account_analytic_id = fields.Many2one(
        string="Cuenta Analítica", related="contract_id.analytic_account_id"
    )
    payment_method_ids = fields.Many2many("hr.payslip.payment.methods", string="Métodos de Pago")
    bank_employee_id = fields.Many2one(
        "res.bank", string="Banco", compute="_compute_employee_default_bank", store=True
    )
    account_number = fields.Many2one(
        "hr.employee.bank", string="Cuenta Bancaria", compute="_compute_account_number", store=True
    )
    employee_prefix_vat = fields.Char(
        string="Prefijo del RIF", compute="_compute_employee_prefix_vat", store=True
    )
    employee_vat = fields.Char(string="RIF", compute="_compute_employee_vat", store=True)

    date_from_vacation = fields.Date(
        readonly=True,
        default=lambda self: fields.Date.to_string(date.today().replace(day=1)),
        states={"draft": [("readonly", False)], "verify": [("readonly", False)]},
    )
    date_to_vacation = fields.Date(
        readonly=True,
        default=lambda self: fields.Date.to_string(
            (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()
        ),
        states={"draft": [("readonly", False)], "verify": [("readonly", False)]},
    )

    _sql_constraints = [
        (
            "_payslip_vacation_perid_entry_start_before_end",
            "check (date_to_vacation > date_from_vacation)",
            "Starting time of vacation period should be before end time.",
        )
    ]

    @api.depends("employee_id")
    def _compute_employee_default_bank(self):
        for payslip in self:
            payslip.bank_employee_id = payslip.employee_id.default_account_bank_id.bank_name

    @api.depends("employee_id")
    def _compute_employee_vat(self):
        for payslip in self:
            payslip.employee_vat = payslip.employee_id.vat

    @api.depends("employee_id")
    def _compute_account_number(self):
        for record in self:
            record.account_number = record.employee_id.default_account_bank_id

    @api.depends("employee_id")
    def _compute_employee_prefix_vat(self):
        for record in self:
            record.employee_prefix_vat = record.employee_id.prefix_vat

    def _prepare_line_values(self, line, account_id, date, debit, credit):
        res = super()._prepare_line_values(line, account_id, date, debit, credit)
        value = (
            line.salary_rule_id.analytic_account_id.id
            or line.slip_id.contract_id.analytic_account_id.id
        )
        if self.default_accounting_analytical:
            value = line.slip_id.contract_id.analytic_account_id.id
        res["analytic_account_id"] = value
        return res

    @api.onchange("schedule_payment", "date_from")
    def _schedule_payment_change(self):
        self.date_to = (
            self.date_from
            + relativedelta(days=self._get_schedule_limit(self.date_from.month))
            - relativedelta(days=1)
        )

    @api.depends("struct_id")
    def _compute_schedule_pay(self):
        for payslip in self:
            payslip.schedule_payment = payslip.struct_id.schedule_pay

    @api.depends("benefits_advance")
    def _compute_benefits_advance_percentage(self):
        for payslip in self:
            benefits_available_amount = payslip._get_employee_benefits_available_amount()
            if benefits_available_amount == 0:
                payslip.benefits_advance_percentage = 0
            else:
                payslip.benefits_advance_percentage = (
                    payslip.benefits_advance * 100 / benefits_available_amount
                )

    def _inverse_benefits_advance_percentage(self):
        for payslip in self:
            if not payslip.is_benefits:
                payslip.benefits_advance = 0
            else:
                benefits_available_amount = payslip._get_employee_benefits_available_amount()
                payslip.benefits_advance = benefits_available_amount * (
                    payslip.benefits_advance_percentage / 100
                )

    def _get_employee_benefits_available_amount(self):
        self.ensure_one()
        benefits_accumulated = self.env["hr.payroll.benefits.accumulated"].search(
            [
                ("employee_id", "=", self.employee_id.id),
            ]
        )
        return benefits_accumulated[-1].available_benefits if any(benefits_accumulated) else 0

    @api.depends("struct_id")
    def _compute_is_benefits(self):
        for payslip in self:
            payslip.is_benefits = payslip.struct_id.category == "benefits"

    def _get_base_local_dict(self):
        local_dict_return = super()._get_base_local_dict()

        allowances = self.employee_id.mapped("allowance_line_ids")
        allowances_dict = {allowance.code: allowance.value for allowance in allowances}

        local_dict_return.update(
            {
                "salario_minimo_actual": float(
                    self.env["ir.config_parameter"].sudo().get_param("sueldo_base_ley")
                ),
                "porc_faov": float(
                    self.env["ir.config_parameter"].sudo().get_param("porcentaje_deduccion_faov")
                ),
                "porc_ince": float(
                    self.env["ir.config_parameter"].sudo().get_param("porcentaje_deduccion_ince")
                ),
                "porc_ivss": float(
                    self.env["ir.config_parameter"].sudo().get_param("porcentaje_deduccion_ivss")
                ),
                "tope_ivss": float(
                    self.env["ir.config_parameter"].sudo().get_param("tope_salario_ivss")
                ),
                "maximo_deduccion_ivss": float(
                    self.env["ir.config_parameter"].sudo().get_param("monto_maximo_ivss")
                ),
                "porc_pf": float(
                    self.env["ir.config_parameter"].sudo().get_param("porcentaje_deduccion_pf")
                ),
                "tope_pf": float(
                    self.env["ir.config_parameter"].sudo().get_param("tope_salario_pf")
                ),
                "maximo_deduccion_pf": float(
                    self.env["ir.config_parameter"].sudo().get_param("monto_maximo_pf")
                ),
                "porcentaje_recargo_nocturno": float(
                    self.env["ir.config_parameter"].sudo().get_param("porcentaje_recargo_nocturno")
                ),
                "dias_utilidades_config": float(
                    self.env["ir.config_parameter"].sudo().get_param("dias_utilidades")
                ),
                "dias_vacaciones_config": float(
                    self.env["ir.config_parameter"].sudo().get_param("dia_vacaciones_anno")
                ),
                "dias_prestaciones_mes_config": float(
                    self.env["ir.config_parameter"].sudo().get_param("dias_prestaciones_mes")
                ),
                "tipo_calculo_intereses_prestaciones_config": (
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("tipo_calculo_intereses_prestaciones")
                ),
                "allowances": BrowsableObject(self.employee_id.id, allowances_dict, self.env),
            }
        )
        return local_dict_return

    def _get_schedule_limit(self, month=1):
        days = 30
        is_leap = isleap(self.date_to.year)
        if month in [1, 3, 5, 7, 8, 10, 12]:
            days = 31
        if month == 2:
            days = 28
            if is_leap:
                days = 29
        if self.schedule_payment == "quarterly":
            days = 15
        if self.schedule_payment == "weekly":
            days = 7
        if self.schedule_payment == "annually":
            days = 365
            if is_leap:
                days = 366
        return days

    @api.constrains("date_from", "date_to")
    def _check_date_from_and_to(self):
        for payslip in self:
            if payslip.schedule_payment != "days" and payslip.struct_id.category == "salary":
                if payslip.date_to >= (
                    payslip.date_from
                    + relativedelta(days=payslip._get_schedule_limit(payslip.date_from.month))
                ):
                    raise ValidationError(
                        _(
                            'La fecha debe tener un rango del "Periodo" de %s dias de diferencia'
                            '\nSi desea un periodo personalizado, actualice el "Pago planeado" a'
                            '"Dias"'
                        )
                        % payslip._get_schedule_limit(payslip.date_from.month)
                    )

    def _get_new_worked_days_lines(self):
        if not self.struct_id.use_worked_day_lines or self.struct_id.category == "profit_sharing":
            return [(5, False, False)]

        if self.struct_id.category == "liquidation":
            last_move_date_to_now = self.employee_id._get_date_range_since_last_salary_move()
            domain = [
                ("date_start", "in", last_move_date_to_now),
                ("date_stop", "in", last_move_date_to_now),
            ]
            worked_days_line_values = self._get_worked_day_lines(
                check_out_of_contract=False, domain=domain
            )
        else:
            worked_days_line_values = self._get_worked_day_lines(check_out_of_contract=False)

        worked_days_lines = self.worked_days_line_ids.browse([])
        work_entry_basic = self.env.ref("binaural_nomina.hr_work_entry_binaural_basic").id
        sum_worked_days = sum(x["number_of_days"] for x in worked_days_line_values)

        for r in worked_days_line_values:
            r["payslip_id"] = self.id
            if (
                r["work_entry_type_id"] == work_entry_basic
                and self.struct_id.category == "salary"
                and self.schedule_payment != "days"
            ):
                if sum_worked_days > (30 if self.date_from.month != 2 else 28):
                    r["number_of_days"] -= sum_worked_days - (
                        30 if self.date_from.month != 2 else 28
                    )
                if sum_worked_days >= 28 and self.date_from.month == 2:
                    r["number_of_days"] += 30 - sum_worked_days
            worked_days_lines |= worked_days_lines.new(r)

        return worked_days_lines

    def _get_paid_amount(self):
        self.ensure_one()
        daily_wage = self.contract_id.daily_wage

        if self.struct_id.category == "liquidation":
            worked_days = sum(self.worked_days_line_ids.mapped("number_of_days"))
            return daily_wage * worked_days

        SCHEDULE_PAYMENT_DAYS = {
            "weekly": 7,
            "half-monthly": 15,
            "monthly": 30,
        }
        schedule_payment_type = self.contract_id.schedule_payment_type
        return SCHEDULE_PAYMENT_DAYS[schedule_payment_type] * daily_wage

    def action_payslip_done(self):
        payslip_done_name = []
        message = ""
        for slip in self:
            if slip.is_benefits and slip.benefits_advance_percentage > 75:
                raise UserError(
                    _(
                        "No se puede realizar un adelanto de prestaciones por más del 75% del"
                        + "monto disponible del empleado."
                    )
                )
            payslips_done = self.env["hr.payslip"].search(
                [
                    ("date_from", "=", slip.date_from),
                    ("employee_id", "=", slip.employee_id.id),
                    ("contract_id", "=", slip.contract_id.id),
                    ("struct_id", "=", slip.struct_id.id),
                    ("state", "=", "done"),
                ]
            )

            if payslips_done:
                payslip_done_name.append(slip.number)

        if len(payslip_done_name) == 0:
            super().action_payslip_done()
            for slip in self:
                if slip.struct_id.category == "benefits":
                    slip.employee_id._register_payroll_benefits(
                        benefits_advance=slip.benefits_advance
                    )
                self._register_payroll_move(slip)
        elif len(payslip_done_name) == 1:
            message = (
                "El recibo %s tiene las mismas caracteristicas (contrato y estructura), verifique la informacion e intente nuevamente"
                % (payslip_done_name[0])
            )
            raise UserError(message)
        else:
            message = (
                "Los recibios %s tienen las mismas caracteristicas (contrato y estructura), verifique la informacion e intente nuevamente"
                % (", ".join(payslip_done_name))
            )
            raise UserError(message)

    def _register_payroll_move(self, slip):
        payroll_structure_category = slip.struct_id.category

        if payroll_structure_category == "provision":
            return

        move_params = {}
        move_params["move_type"] = payroll_structure_category
        move_params["employee_id"] = slip.employee_id.id
        move_params["date"] = slip.date_to

        if payroll_structure_category == "vacation":
            move_params["date_from_vacation"] = slip.date_from_vacation
            move_params["date_to_vacation"] = slip.date_to_vacation

        total_basic = 0
        total_deduction = 0
        total_accrued = 0
        total_net = 0
        total_assig = 0
        advance_of_benefits = 0
        benefits_payment = 0
        profit_sharing_payment = 0
        vacation_days = 0
        vacation_bonus_days = 0
        total_vacation_bonus = 0
        consumed_vacation_days = 0
        total_vacation = 0


        for line in slip.line_ids:
            if line.category_id.code == "DED":
                total_deduction += line.total
            if line.category_id.code == "ASIG":
                total_assig += line.total
            if line.category_id.code == "BASIC":
                total_basic += line.total
            if line.category_id.code == "DEV":
                total_accrued += line.total
            if line.category_id.code == "NET":
                total_net += line.total

            if line.code == "DDBVM":
                vacation_days += line.total
            if line.code == "DDVM":
                consumed_vacation_days += line.total
            if line.code == "PDDVM":
                total_vacation += line.total
            if line.code == "DDBVM":
                vacation_bonus_days += line.total
            if line.code == "PDDBVM":
                total_vacation_bonus += line.total
            if line.code == "UTIL":
                profit_sharing_payment += line.total
            if line.code == "ADPRESTA":
                advance_of_benefits += line.total

            if payroll_structure_category == "liquidation":
                if line.code == "DDVMLIQ":
                    vacation_days += line.total
                if line.code == "PDDVMLIQ":
                    total_vacation += line.total
                if line.code == "DDVBMLIQ":
                    vacation_bonus_days += line.total
                if line.code == "PDDVBMLIQ":
                    total_vacation_bonus += line.total
                if line.code == "UTILLIQ":
                    profit_sharing_payment += line.total
                if line.code == "PRESTA":
                    benefits_payment += line.total

        move_params["total_basic"] = total_basic
        move_params["total_deduction"] = total_deduction
        move_params["total_accrued"] = total_accrued
        move_params["total_net"] = total_net
        move_params["total_assig"] = total_assig
        move_params["advance_of_benefits"] = advance_of_benefits
        move_params["benefits_payment"] = benefits_payment
        move_params["profit_sharing_payment"] = profit_sharing_payment
        move_params["vacation_days"] = vacation_days
        move_params["vacation_bonus_days"] = vacation_bonus_days
        move_params["total_vacation_bonus"] = total_vacation_bonus
        move_params["consumed_vacation_days"] = consumed_vacation_days
        move_params["total_vacation"] = total_vacation

        self.env["hr.payroll.move"].create(move_params)

    def compute_sheet(self):
        for payslip in self:
            if not payslip.employee_id.contract_id:
                raise ValidationError(
                    _("El empleado %s no tiene un contrato activo")
                    % payslip.employee_id.name_get()[0][1]
                )

        result = super().compute_sheet()
        payslips = self.filtered(lambda slip: slip.state in ("draft", "verify"))

        for payslip in payslips:
            for rule in sorted(payslip.struct_id.rule_ids, key=lambda x: x.sequence):
                if not rule.is_a_days_rule and not rule.is_a_hours_rule:
                    continue

                is_a_x_rule = ""

                if rule.is_a_days_rule:
                    is_a_x_rule = "is_a_days_line"
                if rule.is_a_hours_rule:
                    is_a_x_rule = "is_a_hours_line"
                line_to_change = payslip.line_ids.search(
                    [
                        ("code", "=", rule.code),
                    ]
                )

                if not any(line_to_change):
                    continue

                line_to_change.write({is_a_x_rule: True})
        return result

    @api.model
    def create_and_confirm_provisions(self):
        """
        Calls the method for creating provisions of the current mont and applies the method
        action_payslip_done to the slips returned by it.
        """
        povisions_day = int(
            self.env["ir.config_parameter"].sudo().get_param("dia_cron_provisiones")
        )
        if date.today().day != povisions_day:
            return
        provisions = self._create_provisions_slips_for_current_month()
        provisions.action_payslip_done()

    @api.model
    def _create_provisions_slips_for_current_month(self):
        """
        Returns a recordset of hr.payslip created for the current month.

        The payslips are created for all the employees that have actives contract and at least
        one payroll move. They have the provision's structure.
        """
        provisions_structure_id = self.env.ref("binaural_nomina.structure_payroll_provisions").id
        first_day_of_month = datetime.today().replace(day=1)
        last_day_of_month = first_day_of_month + relativedelta(months=1, days=-1)

        slips = self.env["hr.payslip"]

        employees_with_moves = (
            self.env["hr.employee"]
            .search(
                [
                    ("active", "=", True),
                    ("contract_id", "!=", False),
                ]
            )
            .filtered(lambda employee: employee.has_salary_moves())
        )
        for employee in employees_with_moves:
            slip = self.env["hr.payslip"].create(
                {
                    "name": (
                        f"Provisiones - {employee.name} {employee.second_name or ''} "
                        f"{employee.lastname} {employee.second_lastname or ''} - "
                        f"{first_day_of_month.strftime('%m/%Y')}"
                    ),
                    "employee_id": employee.id,
                    "date_from": first_day_of_month,
                    "date_to": last_day_of_month,
                    "contract_id": employee.contract_id.id,
                    "struct_id": provisions_structure_id,
                }
            )
            slips += slip
        return slips

    ## FUNCIONES PARA REGLAS
    def _compute_monday_in_range(self, id):
        count = 0

        if id:
            payslip = self.env["hr.payslip"].browse(id)

            date_from = date(payslip.date_from.year, payslip.date_from.month, payslip.date_from.day)
            date_to = date(payslip.date_to.year, payslip.date_to.month, payslip.date_to.day)

            for d_ord in range(date_from.toordinal(), date_to.toordinal() + 1):
                d = date.fromordinal(d_ord)
                if d.weekday() == 0:
                    count += 1
        else:
            raise UserWarning("Debe agregar un id de hr.payslip para el calculo de lunes")

        return count
