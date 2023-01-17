from odoo import api, fields, models, _

class HrWorkEntryType(models.Model):
    _inherit = "hr.payroll.structure"

    category = fields.Selection([
        ("salary", "Salario"),
        ("vacation", "Vacaciones"),
        ("benefits", "Prestaciones"),
        ("profit_sharing", "Utilidades"),
        ("liquidation", "Liquidación"),
        ("provision", "Provisiones"),
    ], string="Categoría", default="salary")

    schedule_pay = fields.Selection([
        ('monthly', 'Mensual'),
        ('quarterly', 'Quincenal'),
        ('annually', 'Anual'),
        ('weekly', 'Semanal'),
        ('days', 'Dias'),
    ], compute='_compute_schedule_pay', store=True, readonly=False,
    string='Rango de pago', index=True,
    help="Defines the frequency of the wage payment.")

    def copy(self, default=None):
        default = default or {}
        res = super().copy(default)
        res.rule_ids.unlink()
        for rule in self.rule_ids:
            rule.copy({'struct_id': res.id})
        return res

class HrPayrollStructureType(models.Model):
    _inherit = 'hr.payroll.structure.type'

    default_schedule_pay = fields.Selection([
        ('monthly', 'Mensual'),
        ('quarterly', 'Quincenal'),
        ('annually', 'Anual'),
        ('weekly', 'Semanal'),
        ('days', 'Dias'),
    ], string='Default Scheduled Pay', default='monthly',
    help="Defines the frequency of the wage payment.")

    def copy(self, default=None):
        default = default or {}
        res = super().copy(default)
        for struct in self.struct_ids:
            struct.copy({'type_id': res.id})
        return res
