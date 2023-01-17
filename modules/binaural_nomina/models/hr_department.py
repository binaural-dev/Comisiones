from odoo import models, fields

class HrDepartamenetInherit(models.Model):
    _inherit = 'hr.department'
    
    def default_accounting_analytical(self):
        return self.env['ir.config_parameter'].sudo().get_param('cuenta_analitica_departamentos')

    default_accounting_analytical = fields.Boolean(string='Default Accounting Analytical', default=default_accounting_analytical, store=False)
    accounting_analytical_id = fields.Many2one('account.analytic.account', string='Cuenta analítica')
