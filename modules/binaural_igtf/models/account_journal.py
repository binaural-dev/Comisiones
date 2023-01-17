from odoo import fields, models, api, _

class AccountJournalIgtf(models.Model):
    _inherit = 'account.journal'

    default_is_igtf_config = fields.Boolean(compute="_compute_default_is_igtf")
    is_igtf = fields.Boolean(string="IGTF en divisas", default=False, tracking=True)

    def _compute_default_is_igtf(self):
        self.default_is_igtf_config = self.env['ir.config_parameter'].sudo().get_param('is_igtf_on_foreign_exchange')