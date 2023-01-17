from odoo import api, fields, models, _

class AccountPartialBinauralFacturacion(models.Model):
    _inherit = 'account.partial.reconcile'

    bi_igtf = fields.Monetary(string="bigtf", default= 0.00, store=True, currency_field='company_currency_id',)
    igtf = fields.Monetary(string="igtf", default= 0.00, store=True, currency_field='company_currency_id',)