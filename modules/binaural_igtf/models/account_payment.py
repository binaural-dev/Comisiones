from odoo import fields, models, api, _


class AccountPaymentIgtf(models.Model):
    _inherit = "account.payment"

    def default_is_igtf(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("is_igtf_on_foreign_exchange")
        )

    default_is_igtf_on_foreign_exchange = fields.Boolean(
        string="IGTF en Divisas", default=default_is_igtf
    )
    is_igtf_on_foreign_exchange = fields.Boolean(
        string="IGTF en Divisas", compute="_compute_is_igtf"
    )
    amount_igtf_foreign_exchange = fields.Monetary(
        string="IGTF en Divisas", compute="_compute_amount_igtf_foreign_exchange"
    )
    igtf_percentage_on_foreign_exchange = fields.Float(
        string="IGTF en Divisas",
        default=0.0,
        compute="_compute_percentage_on_foreign_exchange",
    )
    is_igtf_payment = fields.Boolean(string="Es un pago de IGTF", default=False)

    @api.depends("journal_id", "is_igtf_payment")
    def _compute_is_igtf(self):
        for account in self:
            if account.journal_id.is_igtf == True and account.is_igtf_payment == False:
                account.is_igtf_on_foreign_exchange = True
            else:
                account.is_igtf_on_foreign_exchange = False

    @api.depends("amount", "is_igtf_on_foreign_exchange")
    def _compute_amount_igtf_foreign_exchange(self):
        for rec in self:
            if rec.is_igtf_on_foreign_exchange and rec.is_igtf_payment == False:
                rec.amount_igtf_foreign_exchange = (
                    rec.amount * (rec.igtf_percentage_on_foreign_exchange / 100) or 0.0
                )
            else:
                rec.amount_igtf_foreign_exchange = 0.0

    @api.depends("is_igtf_on_foreign_exchange")
    def _compute_percentage_on_foreign_exchange(self):
        for rec in self:
            rec.igtf_percentage_on_foreign_exchange = (
                self.env["ir.config_parameter"].sudo().get_param("igtf_percentage")
                or 0.0
            )
