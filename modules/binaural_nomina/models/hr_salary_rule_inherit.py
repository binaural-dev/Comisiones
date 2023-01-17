from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class BinauralHrSalaryRuleInherit(models.Model):
    _name = "hr.salary.rule"
    _inherit = ["hr.salary.rule", "mail.thread", "mail.activity.mixin"]

    is_a_days_rule = fields.Boolean(string="Es una regla de días", default=False, tracking=True)
    is_a_hours_rule = fields.Boolean(string="Es una regla de horas", default=False, tracking=True)
    appears_on_payslip = fields.Boolean(
        string="Appears on Payslip",
        default=True,
        tracking=True,
        help="Used to display the salary rule on payslip",
    )

    @api.constrains("is_a_days_rule", "is_a_hours_rule")
    def _onchange_is_a_days_rule(self):
        for record in self:
            if record.is_a_hours_rule and record.is_a_days_rule:
                raise ValidationError(_("No puede ser una regla de horas y de días a la vez."))

    condition_python = fields.Text(
        string="Python Condition",
        required=True,
        default="""
            # Available variables:
            #----------------------
            # payslip: object containing the payslips
            # employee: hr.employee object
            # contract: hr.contract object
            # rules: object containing the rules code (previously computed)
            # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
            # worked_days: object containing the computed worked days
            # inputs: object containing the computed inputs.
            # salario_minimo_actual: salario minimo actual asignado por configuracion general
            # porc_faov: float con porcentaje de deduccion FAOV asignado por configuracion general
            # porc_ince: float con porcentaje de deduccion INCE asignado por configuracion general
            # porc_ivss: float con porcentaje de deduccion IVSS asignado por configuracion general
            # tope_ivss: int con tope de salarios para deduccion IVSS asignado por configuracion
            # maximo_deduccion_ivss: float con monto maximo de deduccion IVSS (calculado automatico por configuracion)
            # porc_pf: float con porcentaje de deduccion paro forzoso asignado por configuracion general
            # tope_pf: int con tope de salarios para deduccion paro forzoso asignado por configuracion
            # maximo_deduccion_pf: float con monto maximo de deduccion paro forzoso (calculado automatico por configuracion)
            # porcentaje_recargo_nocturno: porcentaje de recargo para bono nocturno mensual
            # allowances: Objeto con el valor de cada asignación del empleado

            # Note: returned value have to be set in the variable 'result'

            result = rules.NET > categories.NET * 0.10""",
        help="Applied this rule for calculation if condition is true. You can specify condition like basic > 1000.",
    )

    amount_python_compute = fields.Text(
        string="Python Code",
        default="""
            # Available variables:
            #----------------------
            # payslip: object containing the payslips
            # employee: hr.employee object
            # contract: hr.contract object
            # rules: object containing the rules code (previously computed)
            # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
            # worked_days: object containing the computed worked days.
            # inputs: object containing the computed inputs.
            # salario_minimo_actual: salario minimo actual asignado por configuracion general
            # porc_faov: float con porcentaje de deduccion FAOV asignado por configuracion general
            # porc_ince: float con porcentaje de deduccion INCE asignado por configuracion general
            # porc_ivss: float con porcentaje de deduccion IVSS asignado por configuracion general
            # tope_ivss: int con tope de salarios para deduccion IVSS asignado por configuracion
            # maximo_deduccion_ivss: float con monto maximo de deduccion IVSS (calculado automatico por configuracion)
            # porc_pf: float con porcentaje de deduccion paro forzoso asignado por configuracion general
            # tope_pf: int con tope de salarios para deduccion paro forzoso asignado por configuracion
            # maximo_deduccion_pf: float con monto maximo de deduccion paro forzoso (calculado automatico por configuracion)
            # porcentaje_recargo_nocturno: porcentaje de recargo para bono nocturno mensual
            # allowances: Objeto con el valor de cada asignación del empleado

            # Note: returned value have to be set in the variable 'result'

            result = contract.wage * 0.10""",
    )
