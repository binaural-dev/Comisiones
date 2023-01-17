from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ResConfigSettingsIgtf(models.TransientModel):
    _inherit = 'res.config.settings'

    is_igtf_on_foreign_exchange = fields.Boolean(string='IGTF on Foreign Exchange')
    igtf_percentage = fields.Float(string='IGTF Percentage', default=3.0, digits=(12, 2))
    igtf_received_payable_id = fields.Many2one('account.account', string="IGTF percibido por pagar")
    is_igtf_expense_account = fields.Boolean(string='Cubre el IGTF')
    igtf_expense_account_id = fields.Many2one('account.account', string="Cuenta de gasto IGTF")
    journal_id_igtf = fields.Many2one('account.journal', string="Diario IGTF")
    igtf_provider = fields.Boolean(string='Proveedor IGTF')
    igtf_provider_account_id = fields.Many2one('account.account', string="Cuenta proveedor IGTF")

    @api.onchange('is_igtf_on_foreign_exchange')
    def _onchange_is_igtf_on_foreign_exchange(self):
        for record in self:
            if not record.is_igtf_on_foreign_exchange:
                record.igtf_percentage = False
                record.igtf_received_payable_id = False
                record.igtf_expense_account_id = False
                record.is_igtf_expense_account = False 
                
    @api.onchange('is_igtf_expense_account')
    def _onchange_is_igtf_expense_account(self):
        for record in self:
            if not record.is_igtf_expense_account:
                record.igtf_expense_account_id = False
    def set_values(self):
        if self.igtf_percentage < 0:
            raise UserError(_('The IGTF percentage must be greater than 0.')
            )
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param('is_igtf_on_foreign_exchange', self.is_igtf_on_foreign_exchange)
        self.env['ir.config_parameter'].sudo().set_param('igtf_percentage', self.igtf_percentage)
        self.env['ir.config_parameter'].sudo().set_param('is_igtf_expense_account', self.is_igtf_expense_account)
        self.env['ir.config_parameter'].sudo().set_param('igtf_expense_account_id', self.igtf_expense_account_id.id)
        self.env['ir.config_parameter'].sudo().set_param('igtf_received_payable_id', self.igtf_received_payable_id.id)
        self.env['ir.config_parameter'].sudo().set_param('journal_id_igtf', self.journal_id_igtf.id)
        self.env['ir.config_parameter'].sudo().set_param('igtf_provider', self.igtf_provider)
        self.env['ir.config_parameter'].sudo().set_param('igtf_provider_account_id', self.igtf_provider_account_id.id)


    @api.model
    def get_values(self):
        res = super().get_values()
        res['is_igtf_on_foreign_exchange'] = self.env['ir.config_parameter'].sudo().get_param('is_igtf_on_foreign_exchange')
        res['igtf_percentage'] = self.env['ir.config_parameter'].sudo().get_param('igtf_percentage')
        res['is_igtf_expense_account'] = self.env['ir.config_parameter'].sudo().get_param('is_igtf_expense_account')
        res['igtf_expense_account_id'] = int(self.env['ir.config_parameter'].sudo().get_param('igtf_expense_account_id'))
        res['igtf_received_payable_id'] = int(self.env['ir.config_parameter'].sudo().get_param('igtf_received_payable_id'))
        res['journal_id_igtf'] = int(self.env['ir.config_parameter'].sudo().get_param('journal_id_igtf'))
        res['igtf_provider'] = self.env['ir.config_parameter'].sudo().get_param('igtf_provider')
        res['igtf_provider_account_id'] = int(self.env['ir.config_parameter'].sudo().get_param('igtf_provider_account_id'))
        return res





