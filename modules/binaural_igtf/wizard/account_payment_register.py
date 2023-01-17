from odoo import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)

class AccountPaymentRegisterIgtf(models.TransientModel):
    _inherit = "account.payment.register"

    def default_is_igtf(self):
        if self.journal_id.is_igtf:
            return self.env['ir.config_parameter'].sudo().get_param('is_igtf_on_foreign_exchange')
        return False

    default_is_igtf_config = fields.Boolean(default=default_is_igtf)
    amount_with_igtf = fields.Float(string="IGTF", compute='_compute_amount_with_igtf', digits=(12, 4))
    igtf_percentage = fields.Float(string="Porcentaje IGTF", compute='_compute_igtf_percentage')
    is_igtf = fields.Boolean(string='Aplicar IGTF', default=default_is_igtf, compute='_compute_is_igtf')
    amount_igtf_rectified = fields.Float(string="IGTF Rectificado", compute='_compute_amount_igtf_rectified', digits=(12, 4))

    @api.depends('line_ids')
    def _compute_pay_igtf_amount(self):
        for account in self:
                account.pay_igtf_amount = account.line_ids.move_id.igtf

    @api.depends('journal_id')
    def _compute_is_igtf(self):
        for account in self:
            if account.journal_id.is_igtf == True:
                account.is_igtf = True
            elif account.journal_id.is_igtf and account.line_ids.move_id.move_type == 'in_refund' or account.line_ids.move_id.move_type == 'out_refund':
                account.is_igtf = True
            else:
                account.is_igtf = False

    @api.depends('is_igtf')
    def _compute_igtf_percentage(self):
        for rec in self:
            if self.is_igtf and rec.line_ids.move_id.move_type == 'out_invoice':
                rec.igtf_percentage = self.env['ir.config_parameter'].sudo().get_param('igtf_percentage')
            else:
                rec.igtf_percentage = 0


    @api.depends('amount')
    def _compute_amount_with_igtf(self):
        foreign_base = self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id')
        for rec in self:
            if self.is_igtf and foreign_base == '2':
                rec.amount_with_igtf = rec.amount * (self.igtf_percentage / 100) * rec.foreign_currency_rate
            elif self.is_igtf:
                rec.amount_with_igtf = rec.amount * (self.igtf_percentage / 100)
            else:
                rec.amount_with_igtf = rec.amount

    @api.depends('amount')
    def _compute_amount_igtf_rectified(self):
        igtf = self.env['ir.config_parameter'].sudo().get_param('igtf_percentage')
        for rec in self:
            if self.is_igtf:
                rec.amount_igtf_rectified = rec.amount * (float(igtf) / 100)
            else:
                rec.amount_igtf_rectified = rec.amount

    def action_create_payment_igtf(self):
        """
            Add the bi_igtf and igtf to the invoice's.

            This function is called by the 'payment' when the user pays an invoice and set the igtf and bi_igtf to the invoice's
            depending on the move_type and the igtf configuration

        """
        for account in self:
            if account.journal_id.is_igtf and account.currency_id.name == 'USD':
                if account.payment_difference < 0:
                    invoice_pay = account.payment_difference +  account.amount
                active_ids = self.env.context.get('active_ids')
                invoice = self.env['account.move'].browse(active_ids)
                if invoice.move_type == 'out_refund' and invoice.bi_igtf > 0 and invoice.igtf > 0 and invoice.igtf_debt_total > invoice.amount_total:
                    invoice.bi_igtf = invoice.bi_igtf
                    invoice.igtf = invoice.igtf
                elif invoice.move_type == 'out_refund' and invoice.amount_residual > 0:
                    invoice.bi_igtf += self.amount
                    invoice.igtf += self.amount_igtf_rectified


                elif invoice.move_type == 'in_refund' and invoice.bi_igtf > 0 and invoice.igtf > 0 and invoice.igtf_debt_total > invoice.amount_total:
                    invoice.bi_igtf = invoice.bi_igtf
                    invoice.igtf = invoice.igtf
                elif invoice.move_type == 'in_refund' and invoice.amount_residual > 0:
                    invoice.bi_igtf += self.amount
                    invoice.igtf += self.amount_igtf_rectified
                
                else:
                    _logger.warning('AQUI ENTRO 3')
                    invoice.bi_igtf += invoice_pay if account.payment_difference < 0 else self.amount
                    invoice.igtf += invoice_pay * (self.igtf_percentage / 100) if account.payment_difference < 0 else self.amount_with_igtf
                

    def create_igtf_move_client(self):
        """
		Create IGTF move to client

		This method create the IGTF move to client when the payment is in foreign exchange.
		
		return:
			move: The move created.

		"""
        cta_conf = int(self.env['ir.config_parameter'].sudo().get_param('igtf_received_payable_id'))
        journal = int(self.env['ir.config_parameter'].sudo().get_param('journal_id_igtf'))
        journal_id = self.env['account.journal'].search([('id', '=', journal)])
        cta_conf_id = self.env['account.account'].search([('id', '=', cta_conf)])

        for account in self:
             if account.journal_id.is_igtf and account.currency_id.name == 'USD':
                move = self.env['account.move'].create({
                    "ref": (f"IGTF Divisas/{account.line_ids.move_id.name}/{self.communication}"),
                    "usd_payment": True,
                    "date": self.payment_date,
                    "journal_id": journal_id.id,
                    "parent_id": account.line_ids.move_id.payment_id.id,
                    "partner_id": self.partner_id.id,
                    "foreign_currency_rate": self.foreign_currency_rate,
                    "state": "draft",
                    'line_ids': [
                        (
                            0,
                            0,
                            {
                                "account_id": self.partner_id.property_account_receivable_id.id,
                                "partner_id": self.partner_id.id,
                                "name": (f"IGTF Divisas/{account.line_ids.move_id.name}/{self.communication}"),
                                "debit": self.amount_with_igtf,
                                "invoice_parent_id": account.line_ids.move_id.id
                            }
                        ),
                        (
                            0,
                            0,
                            {
                                "account_id": cta_conf_id.id,
                                "partner_id": self.partner_id.id,
                                "name": (f"IGTF Divisas/{account.line_ids.move_id.name}/{self.communication}"),
                                "credit": self.amount_with_igtf
                            }
                        )
                    ]
                })
                _logger.warning('ME CREEEE')
                move.state = 'posted'
                move.line_ids[0].reconciled = True
                return move

    def create_igtf_move_expense(self):
        """
		Create IGTF move to expense

		This method create the IGTF move to expense when the payment is in foreign exchange.
		
		return:
			move: The move created.

		"""
        cta_conf = int(self.env['ir.config_parameter'].sudo().get_param('igtf_expense_account_id'))
        cta_conf_received = int(self.env['ir.config_parameter'].sudo().get_param('igtf_received_payable_id'))
        journal = int(self.env['ir.config_parameter'].sudo().get_param('journal_id_igtf'))

        journal_id = self.env['account.journal'].search([('id', '=', journal)])
        cta_conf_id = self.env['account.account'].search([('id', '=', cta_conf)])
        cta_conf_received_id = self.env['account.account'].search([('id', '=', cta_conf_received)])

        for account in self:
            if account.journal_id.is_igtf and account.currency_id.name == 'USD':
                move = self.env['account.move'].create({
                    "ref": (f"IGTF Divisas/{account.line_ids.move_id.name}/{self.communication}"),
                    "usd_payment": True,
                    "date": self.payment_date,
                    "journal_id": journal_id.id,
                    "parent_id": account.line_ids.move_id.payment_id.id,
                    "partner_id": self.partner_id.id,
                    "foreign_currency_rate": self.foreign_currency_rate,
                    "state": "draft",
                    'line_ids': [
                        (
                            0,
                            0,
                            {
                                "account_id": cta_conf_id.id,
                                "partner_id": self.partner_id.id,
                                "name": (f"IGTF Divisas/{account.line_ids.move_id.name}/{self.communication}"),
                                "debit": self.amount_with_igtf,
                                "invoice_parent_id": account.line_ids.move_id.id

                            }
                        ),
                        (
                            0,
                            0,
                            {
                                "account_id": cta_conf_received_id.id,
                                "partner_id": self.partner_id.id,
                                "name": (f"IGTF Divisas/{account.line_ids.move_id.name}/{self.communication}"),
                                "credit": self.amount_with_igtf
                            }
                        )
                    ]
                })
                move.state = 'posted'
                move.line_ids[0].reconciled = True
                return move

    def create_igtf_move_provider(self):
        """
		Create IGTF move to provider

		This method create the IGTF move to provider when the payment is in foreign exchange.
		
		return:
			move: The move created.

		"""
        journal = int(self.env['ir.config_parameter'].sudo().get_param('journal_id_igtf'))

        journal_id = self.env['account.journal'].search([('id', '=', journal)])

        for account in self:
            if account.journal_id.is_igtf and account.currency_id.name == 'USD':
                cta_conf = int(self.env['ir.config_parameter'].sudo().get_param('igtf_provider_account_id'))
                cta_conf_id = self.env['account.account'].search([('id', '=', cta_conf)])

                move = self.env['account.move'].create({
                    "ref": (f"IGTF Divisas/{account.line_ids.move_id.name}/{self.communication}"),
                    "usd_payment": True,
                    "date": self.payment_date,
                    "journal_id": journal_id.id,
                    "parent_id": account.line_ids.move_id.payment_id.id,
                    "partner_id": self.partner_id.id,
                    "foreign_currency_rate": self.foreign_currency_rate,
                    "state": "draft",
                    'line_ids': [
                        (
                            0,
                            0,
                            {
                                "account_id": cta_conf_id.id,
                                "partner_id": self.partner_id.id,
                                "name": (f"IGTF Divisas/{account.line_ids.move_id.name}/{self.communication}"),
                                "debit": self.amount_with_igtf
                            }
                        ),
                        (
                            0,
                            0,
                            {
                                "account_id": self.partner_id.property_account_payable_id.id,
                                "partner_id": self.partner_id.id,
                                "name": (f"IGTF Divisas/{account.line_ids.move_id.name}/{self.communication}"),
                                "credit": self.amount_with_igtf,
                                "invoice_parent_id": account.line_ids.move_id.id

                            }
                        )
                    ]
                })
                move.state = 'posted'
                move.line_ids[1].reconciled = True
                return move

    def create_igtf_move_client_rectified(self):
        """
		Create IGTF move to expense rectification

		This method create the IGTF move to expense when the payment is in foreign exchange and is a rectification.

		return:
			move: The move created.

		"""
        cta_conf = int(self.env['ir.config_parameter'].sudo().get_param('igtf_received_payable_id'))
        journal = int(self.env['ir.config_parameter'].sudo().get_param('journal_id_igtf'))
        journal_id = self.env['account.journal'].search([('id', '=', journal)])
        cta_conf_id = self.env['account.account'].search([('id', '=', cta_conf)])

        for account in self:
            if account.journal_id.is_igtf and account.currency_id.name == 'USD':
                move = self.env['account.move'].create({
                    "ref": (f"IGTF Divisas/{account.line_ids.move_id.name}/{self.communication}"),
                    "usd_payment": True,
                    "date": self.payment_date,
                    "journal_id": journal_id.id,
                    "parent_id": account.line_ids.move_id.payment_id.id,
                    "partner_id": self.partner_id.id,
                    "foreign_currency_rate": self.foreign_currency_rate,
                    "state": "draft",
                    'line_ids': [
                        (
                            0,
                            0,
                            {
                                "account_id": cta_conf_id.id,
                                "partner_id": self.partner_id.id,
                                "name": (f"IGTF Divisas/{account.line_ids.move_id.name}/{self.communication}"),
                                "credit": self.amount_with_igtf

                            }
                        ),
                        (
                            0,
                            0,
                            {
                                "account_id": self.partner_id.property_account_receivable_id.id,
                                "partner_id": self.partner_id.id,
                                "name": (f"IGTF Divisas/{account.line_ids.move_id.name}/{self.communication}"),
                                "debit": self.amount_with_igtf,
                                "invoice_parent_id": account.line_ids.move_id.id

                            }
                        )
                    ]
                })
                move.state = 'posted'
                move.line_ids[0].reconciled = True
                return move

    def create_igtf_move_expense_rectified(self):
        """
		Create IGTF move to expense rectification

		This method create the IGTF move to expense when the payment is in foreign exchange and is a rectification.

		return:
			move: The move created.

		"""
        cta_conf = int(self.env['ir.config_parameter'].sudo().get_param('igtf_expense_account_id'))
        cta_conf_received = int(self.env['ir.config_parameter'].sudo().get_param('igtf_received_payable_id'))
        journal = int(self.env['ir.config_parameter'].sudo().get_param('journal_id_igtf'))

        journal_id = self.env['account.journal'].search([('id', '=', journal)])
        cta_conf_id = self.env['account.account'].search([('id', '=', cta_conf)])
        cta_conf_received_id = self.env['account.account'].search([('id', '=', cta_conf_received)])

        for account in self:
            if account.journal_id.is_igtf and account.currency_id.name == 'USD':
                move = self.env['account.move'].create({
                    "ref": (f"IGTF Divisas/{account.line_ids.move_id.name}/{self.communication}"),
                    "usd_payment": True,
                    "date": self.payment_date,
                    "journal_id": journal_id.id,
                    "parent_id": account.line_ids.move_id.payment_id.id,
                    "partner_id": self.partner_id.id,
                    "foreign_currency_rate": self.foreign_currency_rate,
                    "state": "draft",
                    'line_ids': [
                        (
                            0,
                            0,
                            {
                                "account_id": cta_conf_id.id,
                                "partner_id": self.partner_id.id,
                                "name": (f"IGTF Divisas/{account.line_ids.move_id.name}/{self.communication}"),
                                "credit": self.amount_igtf_rectified,
                                "invoice_parent_id": account.line_ids.move_id.id

                            }
                        ),
                        (
                            0,
                            0,
                            {
                                "account_id": cta_conf_received_id.id,
                                "partner_id": self.partner_id.id,
                                "name": (f"IGTF Divisas/{account.line_ids.move_id.name}/{self.communication}"),
                                "debit": self.amount_igtf_rectified,

                            }
                        )
                    ]
                })
                move.state = 'posted'
                move.line_ids[0].reconciled = True
                return move

    def create_igtf_move_provider_rectified(self):
        """
		Create IGTF move to provider rectification

		This method create the IGTF move to provider when the payment is in foreign exchange and is a rectification.

		return:
			move: The move created.

		"""
        journal = int(self.env['ir.config_parameter'].sudo().get_param('journal_id_igtf'))

        journal_id = self.env['account.journal'].search([('id', '=', journal)])

        for account in self:
            if account.journal_id.is_igtf and account.currency_id.name == 'USD':
                cta_conf = int(self.env['ir.config_parameter'].sudo().get_param('igtf_provider_account_id'))
                cta_conf_id = self.env['account.account'].search([('id', '=', cta_conf)])

                move = self.env['account.move'].create({
                    "ref": (f"IGTF Divisas/{account.line_ids.move_id.name}/{self.communication}"),
                    "usd_payment": True,
                    "date": self.payment_date,
                    "journal_id": journal_id.id,
                    "parent_id": account.line_ids.move_id.payment_id.id,
                    "partner_id": self.partner_id.id,
                    "foreign_currency_rate": self.foreign_currency_rate,
                    "state": "draft",
                    'line_ids': [
                        (
                            0,
                            0,
                            {
                                "account_id": cta_conf_id.id,
                                "partner_id": self.partner_id.id,
                                "name": (f"IGTF Divisas/{account.line_ids.move_id.name}/{self.communication}"),
                                "credit": self.amount_igtf_rectified,

                            }
                        ),
                        (
                            0,
                            0,
                            {
                                "account_id": self.partner_id.property_account_payable_id.id,
                                "partner_id": self.partner_id.id,
                                "name": (f"IGTF Divisas/{account.line_ids.move_id.name}/{self.communication}"),
                                "debit": self.amount_igtf_rectified,
                                "invoice_parent_id": account.line_ids.move_id.id

                            }
                        )
                    ]
                })
                move.state = 'posted'
                move.line_ids[0].reconciled = True
                return move


    def _create_payments(self):
        """
            Add the payment to the invoice's.

            This function is called by the 'payment' widget when the user reconciles a suggested
            journal item with the current invoice. It will add the payment to the invoice's

            when the user pays an invoice from the invoice form view, create a igtf move and reconcile it with the payment

        """
        is_igtf_config = self.env['ir.config_parameter'].sudo().get_param('is_igtf_on_foreign_exchange')
        is_igtf_expense_config = self.env['ir.config_parameter'].sudo().get_param('is_igtf_expense_account')
        is_igtf_provider_config = self.env['ir.config_parameter'].sudo().get_param('igtf_provider')
        self.action_create_payment_igtf()
        for account in self:
            if account.journal_id.is_igtf and account.currency_id.name == 'USD':
                payments = super()._create_payments()
                if is_igtf_config and is_igtf_expense_config == False and is_igtf_provider_config == False:

                    if account.line_ids.move_id.move_type == 'out_invoice':
                        for payment in payments:
                            move = self.create_igtf_move_client()
                            move.parent_id = payment.id
                    elif account.line_ids.move_id.move_type == 'out_refund':
                        for payment in payments:
                            move = self.create_igtf_move_client_rectified()

                elif is_igtf_config and is_igtf_expense_config and is_igtf_provider_config == False:

                    if account.line_ids.move_id.move_type == 'out_invoice':
                        for payment in payments:
                            move = self.create_igtf_move_expense()
                            move.parent_id = payment.id
                    elif account.line_ids.move_id.move_type == 'out_refund':
                        for payment in payments:
                            move = self.create_igtf_move_expense_rectified()

                elif is_igtf_config and is_igtf_provider_config and is_igtf_expense_config == False:

                    if account.line_ids.move_id.move_type == 'in_invoice':
                        for payment in payments:
                            move = self.create_igtf_move_provider()
                            move.parent_id = payment.id
                    elif account.line_ids.move_id.move_type == 'in_refund':
                        for payment in payments:
                            move = self.create_igtf_move_provider_rectified()
                            move.parent_id = payment.id
                    elif account.line_ids.move_id.move_type == 'out_invoice':
                        for payment in payments:
                            move = self.create_igtf_move_client()
                            move.parent_id = payment.id
                    elif account.line_ids.move_id.move_type == 'out_refund':
                        for payment in payments:
                            move = self.create_igtf_move_client_rectified()

                elif is_igtf_config and is_igtf_expense_config and is_igtf_provider_config:

                    if account.line_ids.move_id.move_type == 'in_invoice':
                        for payment in payments:
                            move = self.create_igtf_move_provider()
                            move.parent_id = payment.id
                    elif account.line_ids.move_id.move_type == 'in_refund':
                        for payment in payments:
                            move = self.create_igtf_move_provider_rectified()
                            move.parent_id = payment.id
                    elif account.line_ids.move_id.move_type == 'out_invoice':
                        for payment in payments:
                            move = self.create_igtf_move_expense()
                            move.parent_id = payment.id
                    elif account.line_ids.move_id.move_type == 'out_refund':
                        for payment in payments:
                            move = self.create_igtf_move_expense_rectified()
                            move.parent_id = payment.id
                return payments
            else:
                return super()._create_payments()