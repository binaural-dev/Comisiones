from datetime import date, datetime
from math import ceil, floor
from dateutil import relativedelta
import pandas

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class BinauralHrEmployeeInherit(models.Model):
    _inherit = "hr.employee"

    second_name = fields.Char()
    lastname = fields.Char(required=True)
    second_lastname = fields.Char()

    porc_ari = fields.Float(
        string="Porcentaje ARI",
        help="Porcentaje retencion ISLR",
        digits=(5, 2),
        default=0.0,
    )
    no_ivss = fields.Boolean(string="No cotiza a IVSS")
    no_faov = fields.Boolean(string="No cotiza a FAOV")
    no_pmpf = fields.Boolean(string="No cotiza a Paro Forzoso")

    entry_date = fields.Date(string="Fecha de ingreso", required=True, tracking=True)
    seniority = fields.Char(string="Antigüedad", compute="_compute_seniority")

    dependant_ids = fields.One2many(
        "hr.employee.dependant", "employee_id", string="Dependientes", store=True
    )
    degree_ids = fields.One2many(
        "hr.employee.degree", "employee_id", string="Estudios Realizados", store=True
    )
    bank_ids = fields.One2many("hr.employee.bank", "employee_id", string="Información Bancaria")
    default_account_bank_id = fields.Many2one(
        "hr.employee.bank",
        string="Cuenta bancaria principal",
        compute="_compute_default_account_bank_id",
        store=True,
        default=False,
        domain="[('employee_id.id', '=', id)]",
        readonly=False,
    )

    @api.depends("bank_ids")
    def _compute_default_account_bank_id(self):
        for employee in self:
            self_banks = self.env["hr.employee.bank"].search(
                [("employee_id", "=", employee.id)], limit=1
            )
            employee.default_account_bank_id = False
            if len(self_banks) != 0:
                employee.default_account_bank_id = self_banks

    type_holidays = fields.Selection(
        [
            ("last_wage", "Ultimo sueldo devengado"),
            ("avg_last_month", "Promedio de sueldo devengado de los últimos dos meses"),
        ],
        "Base para vacaciones",
        default="last_wage",
    )
    holidays_accrued = fields.Float(
        string="Devengado para vacaciones", compute="_compute_holidays_accrued"
    )

    prefix_vat = fields.Selection(
        [
            ("V", "V"),
            ("E", "E"),
        ],
        "Prefijo Rif",
        default="V",
    )
    vat = fields.Char(string="RIF")
    street = fields.Char(string="Calle")
    street2 = fields.Char(string="Calle 2")
    address_country_id = fields.Many2one("res.country", string="País")
    city_id = fields.Many2one(
        "res.country.city",
        "Ciudad",
        tracking=True,
        domain="[('state_id','=',state_id)]",
    )
    state_id = fields.Many2one(
        "res.country.state",
        "Estado",
        tracking=True,
        domain="[('country_id','=',address_country_id)]",
    )
    zip = fields.Char(string="Código Postal", change_default=True)
    municipality_id = fields.Many2one(
        "res.country.municipality",
        "Municipio",
        tracking=True,
        domain="[('state_id','=',state_id)]",
    )
    parish_id = fields.Many2one(
        "res.country.parish",
        "Parroquia",
        tracking=True,
        domain="[('municipality_id','=',municipality_id)]",
    )
    house_type = fields.Selection(
        [("owned", "Propia"), ("rented", "Alquilada"), ("family", "Familiar")],
        "Vivienda",
        default="owned",
        tracking=True,
    )
    private_mobile_phone = fields.Char(string="Teléfono celular personal", tracking=True)

    has_open_contract = fields.Boolean(
        string="Tiene Contrato", compute="_compute_has_open_contract"
    )

    mixed_monthly_wage = fields.Float(string="Salario mixto mensual")
    average_annual_wage = fields.Float(string="Salario promedio anual")

    last_monthly_calculated_benefits = fields.Date(
        string="Fecha del ultimo calculo mensual de acumulado de prestaciones"
    )
    last_quarterly_calculated_benefits = fields.Date(
        string="Fecha del ultimo calculo trimestral de acumulado de prestaciones"
    )
    days_per_years = fields.Integer(string="Días por año", compute="_compute_days_per_years")

    allowance_line_ids = fields.One2many(
        "hr.allowance.line", "employee_id", string="Complementos Salariales", tracking=True
    )

    def default_country_id(self):
        return self.env.ref("base.ve")

    country_id = fields.Many2one(default=default_country_id)

    @api.model
    def _name_search(self, name, args=None, operator="ilike", limit=100, name_get_uid=None):
        args = args or []
        args = [] if args is None else args.copy()
        if name:
            args += ["|", "|", ("vat", operator, name), ("name", operator, name)]
        return super()._name_search(
            name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid
        )

    @api.depends("entry_date", "departure_date")
    def _compute_seniority(self):
        for employee in self:
            seniority = ""
            diff = self._get_seniority()
            if diff:
                years = diff.years
                months = diff.months
                days = diff.days

                years_string = "Años" if years > 1 else "Año"
                months_string = "Meses" if months > 1 else "Mes"
                days_string = "Días" if days > 1 else "Día"

                if days > 0:
                    seniority += f"{days} {days_string}"
                if months > 0 and days > 0:
                    seniority = f"{months} {months_string} / " + seniority
                elif months > 0:
                    seniority = f"{months} {months_string} " + seniority
                if years > 0 and (days > 0 or months > 0):
                    seniority = f"{years} {years_string} / " + seniority
                elif years > 0:
                    seniority = f"{years} {years_string} " + seniority
            employee.seniority = seniority

    @api.depends("contract_id.salary_type")
    def _compute_holidays_accrued(self):
        for employee in self:
            salary_type = employee.contract_id.salary_type
            employee.holidays_accrued = 0
            if type(employee.id) == int:
                employee_salary_payments = employee.get_all_payroll_moves()
                if salary_type and employee_salary_payments:
                    if salary_type == "fixed":
                        employee.holidays_accrued = employee_salary_payments[-1]["total_accrued"]
                    else:
                        last_month_accrued = employee_salary_payments[-1]["total_accrued"]
                        second_to_last_month_accrued = (
                            employee_salary_payments[-2]["total_accrued"]
                            if len(employee_salary_payments) > 1
                            else 0
                        )
                        third_to_last_month_accrued = (
                            employee_salary_payments[-3]["total_accrued"]
                            if len(employee_salary_payments) > 2
                            else 0
                        )

                        employee.holidays_accrued = (
                            last_month_accrued
                            + second_to_last_month_accrued
                            + third_to_last_month_accrued
                        ) / 3

    @api.depends("contract_ids")
    def _compute_has_open_contract(self):
        for employee in self:
            employee.has_open_contract = False
            if any(
                self.env["hr.contract"].search(
                    [("state", "=", "open"), ("employee_id", "=", employee.id)]
                )
            ):
                employee.has_open_contract = True

    def _compute_employee_average_wage(self, id):
        employee = self.env["hr.employee"].search([("id", "=", id)])

        moves = employee._get_payroll_moves_grouped_by_months_of_a_specific_year()
        if not moves:
            return 0

        last_month = int(moves[-1]["month"])
        last_month_wage = moves[-1]["total_accrued"]
        for month in range(last_month + 1, 13):
            moves.append(
                {
                    "month": month,
                    "total_accrued": last_month_wage,
                }
            )
        annual_average = sum(move["total_accrued"] for move in moves) / len(moves)

        employee.average_annual_wage = annual_average
        return annual_average

    def _get_seniority_in_years(self):
        self.ensure_one()
        seniority = 0
        if self.entry_date:
            from_date = self.entry_date
            to_date = self.departure_date if self.departure_date else fields.Date.today()

            diff = relativedelta.relativedelta(to_date, from_date)
            seniority = diff.years
        return seniority

    def _get_seniority(self):
        self.ensure_one()

        if not self.entry_date:
            return None

        from_date = self.entry_date
        to_date = self.departure_date if self.departure_date else fields.Date.today()

        return relativedelta.relativedelta(to_date, from_date)

    def _compute_days_per_years(self):
        maximo_dias_prestaciones_anno = int(
            self.env["ir.config_parameter"].sudo().get_param("maximo_dias_prestaciones_anno")
        )
        for employee in self:
            seniority = employee._get_seniority()
            years = int(seniority.years)
            if seniority.months >= 6:
                years += 1
            employee.days_per_years = years * maximo_dias_prestaciones_anno

    def _get_benefits_per_years_amount(self):
        payroll_moves = self._get_payroll_moves_grouped_by_months_of_a_specific_year()
        salary_type = self.contract_id.salary_type
        total_accrued = 0
        if salary_type == "variable":
            return 0
        total_accrued = payroll_moves[-1]["total_accrued"]
        amount_per_days = total_accrued / 30
        return amount_per_days * self.days_per_years

    def _get_payroll_moves_grouped_by_months_of_a_specific_year(self, year=datetime.today().year):
        for employee in self:
            self._cr.execute(
                """
                    SELECT
                        EXTRACT(MONTH FROM date) AS month,
                        SUM(total_basic) as total_basic,
                        SUM(total_accrued) as total_accrued
                    FROM hr_payroll_move as move
                    WHERE
                        employee_id = %s AND
                        move_type = 'salary' AND
                        EXTRACT(YEAR FROM date) = %s
                    GROUP BY month
                    ORDER BY month asc;
                """,
                (employee.id, year),
            )
            return self._cr.dictfetchall()

    def _get_benefits(self, benefits_days, is_monthly=False, is_annual=False):
        self.ensure_one()

        if not self.contract_id:
            return

        integral_daily_wage = self.contract_id.get_integral_daily_wage()
        benefits_payment = integral_daily_wage * benefits_days

        today = datetime.today().date()

        self._register_payroll_benefits(benefits=benefits_payment)
        benefits_accumulated = self.env["hr.payroll.benefits.accumulated"].search(
            [("employee_id", "=", self.id)],
            limit=1,
        )

        # Creating the register of the detail
        detail_params = {
            "date": today,
            "employee_id": self.id,
            "amount": benefits_payment,
            "accumulated_amount": benefits_accumulated.accumulated_benefits,
        }
        if is_monthly:
            detail_params["type"] = "monthly"
            self.last_monthly_calculated_benefits = today
        elif not is_annual:
            detail_params["type"] = "quarterly"
            self.last_quarterly_calculated_benefits = today
        else:
            detail_params["type"] = "annual"
        self.env["hr.payroll.benefits.accumulated.detail"].create(detail_params)

    def _register_payroll_benefits(self, benefits=0, interests=0, benefits_advance=0):
        for employee in self:
            payroll_benefits_accumulated = self.env["hr.payroll.benefits.accumulated"]
            benefits_accumulated_params = {
                "employee_id": employee.id,
                "accumulated_benefits": benefits,
                "accumulated_interest": interests,
                "accumulated_benefits_advance": benefits_advance,
                "date": fields.Date.today(),
            }
            benefits_accumulated = payroll_benefits_accumulated.search(
                [("employee_id", "=", employee.id)]
            )

            if any(benefits_accumulated):
                benefits_to_update = benefits_accumulated[-1]

                benefits_accumulated_params[
                    "accumulated_benefits"
                ] += benefits_to_update.accumulated_benefits
                benefits_accumulated_params[
                    "accumulated_interest"
                ] += benefits_to_update.accumulated_interest
                benefits_accumulated_params[
                    "accumulated_benefits_advance"
                ] += benefits_to_update.accumulated_benefits_advance

                benefits_to_update.sudo().write(benefits_accumulated_params)
            else:
                payroll_benefits_accumulated.sudo().create(benefits_accumulated_params)

    def _get_date_range_since_last_salary_move(self):
        self.ensure_one()
        last_move = self.env["hr.payroll.move"].search(
            [
                ("employee_id", "=", self.id),
                ("move_type", "=", "salary"),
            ],
            limit=1,
            order="date desc",
        )
        if not last_move:
            raise UserError(_("%s No tiene aún ningún pago de nómina." % (self.name)))
        return (
            pandas.date_range(
                last_move.date + relativedelta.relativedelta(days=1),
                datetime.today().replace(hour=23),
                freq="1h",
            )
            .to_pydatetime()
            .tolist()
        )

    def _get_vacation_bonus_days_of_previous_moves(self):
        self.ensure_one()
        vacation_moves = self.env["hr.payroll.move"].search(
            [
                ("employee_id", "=", self.id),
                ("move_type", "=", "vacation"),
            ]
        )
        result = sum(move.vacation_bonus_days for move in vacation_moves)
        return result

    def _has_paid_vacation(self, year=datetime.today().year):
        first_day_of_year = date(year, 1, 1)
        last_day_of_year = date(year, 12, 31)
        year_date_range = (
            pandas.date_range(first_day_of_year, last_day_of_year, freq="D")
            .to_pydatetime()
            .tolist()
        )

        vacation_moves = self.env["hr.payroll.move"].search(
            [
                ("employee_id", "=", self.id),
                ("move_type", "=", "vacation"),
                ("date", "in", year_date_range),
            ]
        )

        return any(vacation_moves)

    def get_not_taken_vacation_days(self):
        self.ensure_one()
        days = 0
        work_entry_vacation_id = self.env["ir.model.data"].xmlid_to_res_id(
            "binaural_nomina.hr_work_entry_binaural_vacation", raise_if_not_found=False
        )
        vacation_allocations = self.env["hr.leave.allocation"].search(
            [
                ("employee_id", "=", self.id),
                ("holiday_status_id.work_entry_type_id", "=", work_entry_vacation_id),
            ]
        )
        for allocation in vacation_allocations:
            days += allocation.max_leaves - allocation.leaves_taken
        return days

    @api.constrains("entry_date", "departure_date")
    def _check_dates(self):
        for employee in self:
            if employee.departure_date and employee.departure_date <= employee.entry_date:
                raise ValidationError(_("La fecha de egreso debe ser mayor a la fecha de ingreso."))

    @api.constrains("vat", "prefix_vat")
    def _check_vat(self):
        for employee in self:
            if employee.vat:
                employee_with_the_same_vat = (
                    self.env["hr.employee"]
                    .sudo()
                    .search(
                        [
                            ("vat", "=", employee.vat),
                            ("prefix_vat", "=", employee.prefix_vat),
                            ("id", "!=", employee.id),
                        ]
                    )
                )
                if any(employee_with_the_same_vat):
                    raise ValidationError(_("Ya existe un empleado con ese RIF."))

    @api.constrains("type_holidays")
    def _check_employee_has_moves_from_at_least_two_months(self):
        for employee in self:
            if employee.type_holidays == "avg_last_month":
                if not type(employee.id) != "int":
                    raise ValidationError(
                        _(
                            "No se puede usar como base para vaciones el promedio del devengado de"
                            + "los últimos dos meses porque el empleado acaba de ser registrado."
                        )
                    )
                salary_payments = employee._get_payroll_moves_grouped_by_months_of_a_specific_year()
                if len(salary_payments) < 2:
                    raise ValidationError(
                        _(
                            "No se puede usar como base para vaciones el promedio del devengado de"
                            + "los últimos dos meses porque el empleado tiene registrados menos de"
                            + "dos pagos de nómina mensual."
                        )
                    )

    def name_get(self):
        """Change the display name of the employee to show all the names."""
        result = []
        for employee in self:
            if employee.lastname:
                result.append(
                    (
                        employee.id,
                        f"{employee.name} {employee.second_name or ''} "
                        f"{employee.lastname} {employee.second_lastname or ''}",
                    )
                )
            else:
                result.append((employee.id, f"{employee.name}"))
        return result

    def has_salary_moves(self):
        """Returns True if the employee has payroll moves with salary type, else returns False."""
        self.ensure_one()
        salary_moves = self.env["hr.payroll.move"].search(
            [
                ("employee_id", "=", self.id),
                ("move_type", "=", "salary"),
            ],
            limit=1,
        )
        if any(salary_moves):
            return True
        return False

    def get_all_payroll_moves(self):
        self._cr.execute(
            """
                SELECT
                    EXTRACT(MONTH FROM date) AS month,
                    SUM(total_basic) as total_basic,
                    SUM(total_accrued) as total_accrued
                FROM hr_payroll_move as move
                WHERE
                    employee_id = %s AND
                    move_type = 'salary'
                GROUP BY month
                ORDER BY month asc;
            """,
            (self.id,),
        )
        moves = self._cr.dictfetchall()
        return moves

    def get_vacation_bonus_days_alicuot(self):
        self.ensure_one()
        vacation_bonus_days = self.get_vacation_bonus_days()
        moves = self.get_all_payroll_moves()
        return (vacation_bonus_days / 360) * (moves[-1]["total_accrued"] / 30)

    def get_vacation_bonus_days(self):
        self.ensure_one()
        seniority_in_months = self.get_seniority_in_months()
        additional_days = int(
            self.env["ir.config_parameter"].sudo().get_param("dia_adicional_posterior")
        )
        annual_vacation_days = int(
            self.env["ir.config_parameter"].sudo().get_param("dia_vacaciones_anno")
        )
        vacation_bonus_days = (
            floor(seniority_in_months / 12.0) * additional_days
        ) + annual_vacation_days
        return vacation_bonus_days

    def get_not_paid_vacation_bonus_days(self):
        """
        Compute the number of bonus days of the previous years that had not been paid (without
        taking into account the fraction of the current year).

        Those are, the number of bonus days that correspond to the employee on all history minus
        the bonus days on the payroll moves of type vacation that the they have.

        Returns
        -------
        int
            The number of bonus days not paid.
        """
        self.ensure_one()
        seniority_years = self._get_seniority_in_years()
        if seniority_years == 0:
            return 0

        additional_days = int(
            self.env["ir.config_parameter"].sudo().get_param("dia_adicional_posterior")
        )
        annual_vacation_days = int(
            self.env["ir.config_parameter"].sudo().get_param("dia_vacaciones_anno")
        )
        bonus_days_of_the_current_year = annual_vacation_days + (seniority_years * additional_days)

        vacation_slips = self.env["hr.payroll.move"].search(
            [
                ("employee_id", "=", self.id),
                ("move_type", "=", "vacation"),
            ]
        )
        bonus_days_taken = sum(slip.vacation_bonus_days for slip in vacation_slips)

        total_employee_bonus_days = sum(range(annual_vacation_days, bonus_days_of_the_current_year))
        return total_employee_bonus_days - bonus_days_taken

    def get_fractional_vacation_days(self, is_bonus=False):
        """
        Compute the fractional days or bonus days of vacation for the current year.

        If the vacations of the employee had already been paid this year and they departure month
        (or the current one) is less than they entry month, the result will be 0.

        If the days that are gonna be computed are bonus, the total of days to use as a fraction
        are calculated taking into account the first years for the additional days, else we use the
        additional days starting on year 2.

        Parameters
        ----------
        is_bonus : bool
            If the days that are gonna be computed are bonus vacation days.

        Returns
        -------
        float
            The fraction of days or bonus days of the current year.
        """
        self.ensure_one()
        first_day_of_year = date.today().replace(month=1, day=1)
        last_day_of_year = date.today().replace(month=12, day=1)
        vacation_slips_of_current_year = self.env["hr.payroll.move"].search(
            [
                ("employee_id", "=", self.id),
                ("date_to_vacation", ">=", first_day_of_year),
                ("date_to_vacation", "<=", last_day_of_year),
            ],
            order="date desc",
            limit=1,
        )

        if bool(vacation_slips_of_current_year) and self.entry_date.month >= (
            self.departure_date.month if self.departure_date else date.today.month
        ):
            return 0

        seniority_years = self._get_seniority_in_years()
        vacation_days = int(self.env["ir.config_parameter"].sudo().get_param("dia_vacaciones_anno"))
        additional_vacation_days_per_year = int(
            self.env["ir.config_parameter"].sudo().get_param("dia_adicional_posterior")
        )
        additional_vacation_days_total = seniority_years * additional_vacation_days_per_year

        # If the days are not the bonus one, the additional days must be added starting year 2 of
        # the employee.
        if not is_bonus:
            additional_vacation_days_total -= additional_vacation_days_per_year
        months_worked_this_year = (
            self.departure_date.month if self.departure_date else date.today().month
        ) - self.entry_date.month

        days_per_month = (additional_vacation_days_total + vacation_days) / 12
        return days_per_month * months_worked_this_year

    def get_benefits_days_total(self):
        """
        Compute the total days of benefits on the current date.

        These are the benefits days per year from the config multiplied by the number of seniority
        years the employee has starting on year 2.

        Returns
        -------
        int
            The number of benefits days of the employee for the current date.
        """
        self.ensure_one()
        benefits_days_per_year_from_year_two = int(
            self.env["ir.config_parameter"].get_param("dias_prestaciones_anno")
        )
        seniority = self._get_seniority_in_years()
        if seniority <= 1:
            return 0
        return (benefits_days_per_year_from_year_two - 1) * seniority

    def get_profit_sharing_days_alicuot(self):
        self.ensure_one()
        profit_sharing_days = int(
            self.env["ir.config_parameter"].sudo().get_param("dias_utilidades")
        )
        moves = self.get_all_payroll_moves()
        return (profit_sharing_days / 360) * (moves[-1]["total_accrued"] / 30)

    def get_profit_sharing_days(self, liquidation=False):
        self.ensure_one()
        profit_sharing_days_conf = int(self.env["ir.config_parameter"].get_param("dias_utilidades"))
        seniority_in_years = self._get_seniority_in_years()

        if seniority_in_years >= 1 and not liquidation:
            return profit_sharing_days_conf

        seniority_in_months = self.get_seniority_months_since_first_day_of_year()
        return ceil(profit_sharing_days_conf / 12 * seniority_in_months)

    def get_seniority_months_since_first_day_of_year(self):
        self.ensure_one()
        seniority = self._get_seniority()
        if not seniority:
            return 0
        first_day_of_year = date.today().replace(month=1, day=1)
        if self.entry_date >= first_day_of_year:
            return self.get_seniority_in_months()
        seniority_in_months = relativedelta.relativedelta(
            datetime.today(), first_day_of_year
        ).months
        return seniority_in_months

    def get_seniority_in_months(self):
        self.ensure_one()
        seniority = self._get_seniority()
        if not seniority:
            return 0
        return seniority.years * 12 + seniority.months

    def get_profit_sharing_wage(self):
        profit_sharing_type = self.env["ir.config_parameter"].get_param("tipo_utilidades")

        if profit_sharing_type == "annual_avg":
            return self._compute_employee_average_wage(self.id) / 30

        moves = self.get_all_payroll_moves()
        if not moves:
            raise UserError(_(f"No se encontraron pagos de nómina para el empleado {self.name}"))
        return moves[-1]["total_accrued"] / 30

    def get_seniority_months_since_last_seniority_year(self):
        self.ensure_one()
        seniority = 0
        diff = self._get_seniority()
        if diff:
            from_date = self.entry_date
            to_date = self.departure_date if self.departure_date else fields.Date.today()

            diff = relativedelta.relativedelta(to_date, from_date)
            seniority = diff.months
        return seniority

    def toggle_active(self):
        res = super().toggle_active()
        if len(self) == 1 and not self.active:
            departure_date = self.departure_date or fields.Date.today()
            res["context"]["default_departure_date"] = departure_date
        return res
