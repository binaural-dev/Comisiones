from odoo import models, fields, api
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PayIgtf(models.TransientModel):
    _name = "wizard.pay.igtf"
    amount = fields.Float(string="IGTF to pay")
    move_id = fields.Many2one("account.move", string="Move entry")
    date = fields.Date(string="Date payment", default=fields.Date.today(), required=True)
    journal_id = fields.Many2one("account.journal", string="Journal", domain="[('type', '=', ['bank','cash'])]", required=True)
    currency_id = fields.Many2one("res.currency", string="Currency", related="journal_id.currency_id", readonly=False)
    foreign_currency_rate = fields.Float(string="Foreign currency rate", digits=(12, 2), compute="_compute_foreign_currency_rate", readonly=False)
    memo = fields.Text()

    @api.depends('date')
    def _compute_foreign_currency_rate(self):
        for record in self:
            record.foreign_currency_rate = record.move_id.foreign_currency_rate
    
    def _compute_amount_to_pay(self):
        _logger.warning("foreign_currency_rate: %s", self.foreign_currency_rate)
        self.amount = self.foreign_currency_rate * self.igtf

    def action_pay_igtf(self):
        self.validate_payment()
        self.create_payment_igtf()
        for record in self.move_id:
            record.igtf_debt_total= 0

    def validate_payment(self):
        for record in self:
            if record.journal_id.sequence_id:
                if record.journal_id.sequence_id.active == False:
                    raise UserError(
                        "El diario seleccionado no tiene secuencia activa"
                    )
           
    def create_payment_igtf(self):
        partner_type = ""
        payment_type = ""
        
        reconciled_vals = []
        invoice_vals = []
        partial_reconcile_vals = []
        for record in self:
            if record.move_id.move_type == "out_invoice":
                partner_type = "customer"
                payment_type = "inbound"
            elif record.move_id.move_type == "out_refund":
                partner_type = "customer"
                payment_type = "outbound"
            elif record.move_id.move_type == "in_invoice":
                partner_type = "supplier"
                payment_type = "outbound"
            elif record.move_id.move_type == "in_refund":
                partner_type = "supplier"
                payment_type = "inbound"
                
            pay = self.env["account.payment"].create(
                {
                    "name": record.journal_id.sequence_id.next_by_id(),
                    "payment_type": payment_type,
                    "partner_type": partner_type,
                    "amount": record.amount * record.foreign_currency_rate if record.currency_id.name != 'USD' else record.amount,
                    "currency_id": record.currency_id.id,
                    "foreign_currency_rate": record.foreign_currency_rate,
                    "is_igtf_payment": True,
                    "partner_id": record.move_id.partner_id.id,
                    "extract_state": "no_extract_requested",
                    "destination_account_id": record.move_id.partner_id.property_account_receivable_id.id,
                    "move_id": record.move_id.id
                    if record.move_id.move_type == "entry"
                    else False,
                    "journal_id": record.journal_id.id,
                    "date": record.date,
                    "ref": "Pago de IGTF",
                    "state": "draft",
                }
            )
            if partner_type == "supplier":
                pay.partner_type = "supplier"
        
            pay.state = "posted"
            
            reconcile = self.env["account.move.line"].search(
                [("move_id", "=", pay.move_id.id)]
            )
            reconcile_igtf = self.env["account.move.line"].search(
                [("invoice_parent_id", "=", record.move_id.id)]
            )
            for payment in reconcile:
                if partner_type == "supplier" and payment.account_id.user_type_id.type == "payable":
                    reconciled_vals.append(payment.id)

                if partner_type == "customer" and payment.account_id.user_type_id.type == "receivable":
                    reconciled_vals.append(payment.id)

            for invoice in reconcile_igtf:
                if invoice.move_id.state == "posted":
                    invoice_vals.append(invoice.id)


                reconciled_igtf = self.env["account.partial.reconcile"].create(
                    {
                        "debit_move_id": invoice.id,
                        "credit_move_id": reconciled_vals[0],
                    }
                )
                partial_reconcile_vals.append(reconciled_igtf.id)

            self.env["account.full.reconcile"].create(
                {
                    "partial_reconcile_ids": [
                        (6, 0,
                        reconciled_vals[0],
                        [reconcile for reconcile in partial_reconcile_vals])
                    ],
                    "reconciled_line_ids": [
                        (
                            6,
                            0,
                            [reconcile for reconcile in reconciled_vals]
                            + [invoice for invoice in invoice_vals],
                        )
                    ],
                    "exchange_move_id": False,
                }
            )
            self.env["account.move.line"].search( [("id", "=", reconciled_vals[0])]).reconciled = True
            reconcile.write({"reconciled": True})

            
            pay.is_reconciled = True

            return pay