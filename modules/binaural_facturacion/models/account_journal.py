from odoo import api, fields, models, _


class AccountJournalBinauralFacturacion(models.Model):
    _inherit = "account.journal"

    fiscal = fields.Boolean(default=False, tracking=100)
    series_correlative_sequence_id = fields.Many2one(
        "ir.sequence", string="Nro de control de serie", tracking=True
    )

    show_series_correlative = fields.Boolean(compute="_compute_show_series_correlative")

    def _compute_show_series_correlative(self):
        series_invoicing = self.env['ir.config_parameter'].sudo().get_param('series_invoicing')
        self.update({"show_series_correlative": False})
        if not series_invoicing:
            return
        self.filtered(lambda j: j.type == "sale" and j.fiscal).update(
            {"show_series_correlative": True}
        )
