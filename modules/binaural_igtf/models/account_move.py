from odoo import fields, models, api, _


class AccountMoveIgtf(models.Model):
    _inherit = "account.move"

    parent_id = fields.Many2one(
        "account.payment",
        string="Parent Payment",
        domain=[("is_igtf_on_foreign_exchange", "=", True)],
        help="Parent Payment for this IGTF invoice",
    )
    is_igtf = fields.Boolean(
        string="¿Es IGTF?",
        default=False,
        compute="_compute_is_igtf",
        help="The move is IGTF?",
    )
    bi_igtf = fields.Monetary(
        string="BI IGTF", default=0.00, readonly=True, help="subtotal with igtf"
    )
    igtf = fields.Float(
        string="IGTF",
        default=0.00,
        digits=(12, 4),
        readonly=True,
        help="IGTF Percentage",
    )
    igtf_amount_total = fields.Monetary(
        string="Total a pagar con IGTF",
        compute="_def_igtf_amount",
        store=True,
        help="Amount to pay with IGTF",
    )
    igtf_debt_total = fields.Monetary(
        string="Total adeudado con IGTF",
        compute="_def_total_debt_igtf",
        store=True,
        help="Total debt with IGTF",
    )
    usd_payment = fields.Boolean(
        string="¿Pago en USD?", default=False, help="Payment in USD?"
    )

    def _compute_is_igtf(self):
        is_igtf = self.env["ir.config_parameter"].sudo().get_param('is_igtf_on_foreign_exchange')
        if is_igtf:
            for record in self:
                record.is_igtf = True

    
    @api.depends("amount_total", "igtf")
    def _def_igtf_amount(self):
        for record in self:
            record.igtf_amount_total = record.igtf + record.amount_total


    @api.depends("amount_residual", "igtf")
    def _def_total_debt_igtf(self):
        is_igtf = self.env["ir.config_parameter"].sudo().get_param('is_igtf_on_foreign_exchange')
        is_igtf_expense = self.env["ir.config_parameter"].sudo().get_param('is_igtf_expense_account')
        for record in self:
            if is_igtf and is_igtf_expense:
                record.igtf_debt_total = 0.00
            else:
                record.igtf_debt_total = record.amount_residual + record.igtf


    def _create_igtf_move_client(self, partials):
        """
		Create IGTF move to client

		This method create the IGTF move to client when the payment is in foreign exchange.

		params:
			partials: The partials of the payment.
		
		return:
			move: The move created.

		"""
        for account in self:
            if account.move_type == 'out_invoice' and partials.credit_move_id.payment_id.is_igtf_on_foreign_exchange and partials.credit_move_id.move_id.journal_id.type == 'cash' or partials.credit_move_id.move_id.journal_id.type == 'bank':
                cta_conf = int(self.env['ir.config_parameter'].sudo().get_param('igtf_received_payable_id'))
                journal = int(self.env['ir.config_parameter'].sudo().get_param('journal_id_igtf'))
                journal_id = self.env['account.journal'].search([('id', '=', journal)])
                cta_conf_id = self.env['account.account'].search([('id', '=', cta_conf)])
                
                move = self.env['account.move'].create({
                    "ref": (f"IGTF Divisas/{account.name}/{partials.credit_move_id.payment_id.ref}%"),
                    "usd_payment": True,
                    "date": account.invoice_date,
                    "journal_id": journal_id.id,
                    "parent_id": partials.credit_move_id.payment_id.id,
                    "partner_id": partials.credit_move_id.payment_id.partner_id.id,
                    "foreign_currency_rate": partials.credit_move_id.payment_id.foreign_currency_rate,
                    "state": "draft",
                    'line_ids': [
                        (
                            0,
                            0,
                            {
                                "account_id": partials.credit_move_id.payment_id.partner_id.property_account_receivable_id.id,
                                "partner_id": partials.credit_move_id.payment_id.partner_id.id,
                                "name": (f"IGTF Divisas/{account.name}/{partials.credit_move_id.payment_id.ref}"),
                                "debit": account.igtf_debt_total,
                                "invoice_parent_id": account.id,
                            }
                        ),
                        (
                            0,
                            0,
                            {
                                "account_id": cta_conf_id.id,
                                "partner_id": partials.credit_move_id.payment_id.partner_id.id,
                                "name": (f"IGTF Divisas/{account.name}/{partials.credit_move_id.payment_id.ref}"),
                                "credit": account.igtf_debt_total,
                            }
                        )
                    ]
                })
                move.line_ids[0].reconciled = True
                move.state = 'posted'
                return move

    def _create_igtf_move_expense(self, partials):
        """
		Create IGTF move to client expense

		This method create the IGTF move to client when the payment is in foreign exchange.

		params:
			partials: The partials of the payment.
		
		return:
			move: The move created.

		"""
        for account in self:
            if account.move_type == 'out_invoice' and partials.credit_move_id.payment_id.is_igtf_on_foreign_exchange and partials.credit_move_id.move_id.journal_id.type == 'cash' or partials.credit_move_id.move_id.journal_id.type == 'bank':
                cta_conf = int(self.env['ir.config_parameter'].sudo().get_param('igtf_expense_account_id'))
                cta_conf_received = int(self.env['ir.config_parameter'].sudo().get_param('igtf_received_payable_id'))
                journal = int(self.env['ir.config_parameter'].sudo().get_param('journal_id_igtf'))
                
                journal_id = self.env['account.journal'].search([('id', '=', journal)])
                cta_conf_id = self.env['account.account'].search([('id', '=', cta_conf)])
                cta_conf_received_id = self.env['account.account'].search([('id', '=', cta_conf_received)])
                
                move = self.env['account.move'].create({
                    "ref": (f"IGTF Divisas/{account.name}/{partials.credit_move_id.payment_id.ref}"),
                    "usd_payment": True,
                    "date": partials.credit_move_id.payment_id.date,
                    "journal_id": journal_id.id,
                    "parent_id": partials.credit_move_id.payment_id.id,
                    "partner_id": partials.credit_move_id.payment_id.partner_id.id,
                    "foreign_currency_rate": partials.credit_move_id.payment_id.foreign_currency_rate,
                    "state": "draft",
                    'line_ids': [
                        (
                            0,
                            0,
                            {
                                "account_id": cta_conf_id.id,
                                "partner_id": partials.credit_move_id.payment_id.partner_id.id,
                                "name": (f"IGTF Divisas/{account.name}/{partials.credit_move_id.payment_id.ref}"),
                                "debit": account.igtf_received_total,
                                "invoice_parent_id": account.id,
                            }
                        ),
                        (
                            0,
                            0,
                            {
                                "account_id": cta_conf_received_id.id,
                                "partner_id": partials.credit_move_id.payment_id.partner_id.id,
                                "name": (f"IGTF Divisas/{account.name}/{partials.credit_move_id.payment_id.ref}"),
                                "credit": account.igtf_debt_total,
                            }
                        )
                    ]
                })
                move.state = 'posted'
                move.line_ids[0].reconciled = True
                return move

    def _create_igtf_move_provider(self, partials):
        """
		Create IGTF move to provider

		This method create the IGTF move to provider when the payment is in foreign exchange.

		params:
			partials: The partials of the payment.
		
		return:
			move: The move created.

		"""
        for account in self:
            if account.move_type == 'in_invoice' and partials.debit_move_id.payment_id.is_igtf_on_foreign_exchange:
                journal = int(self.env['ir.config_parameter'].sudo().get_param('journal_id_igtf'))
                journal_id = self.env['account.journal'].search([('id', '=', journal)])
                cta_conf = int(self.env['ir.config_parameter'].sudo().get_param('igtf_provider_account_id'))
                cta_conf_id = self.env['account.account'].search([('id', '=', cta_conf)])
                
                move = self.env['account.move'].create({
                    "ref": (f"IGTF Divisas/{account.name}/{partials.debit_move_id.payment_id.ref}"),
                    "usd_payment": True,
                    "date": partials.debit_move_id.payment_id.date,
                    "journal_id": journal_id.id,
                    "parent_id": partials.debit_move_id.payment_id.id,
                    "partner_id": partials.debit_move_id.payment_id.partner_id.id,
                    "foreign_currency_rate": partials.debit_move_id.payment_id.foreign_currency_rate,
                    "state": "draft",
                    'line_ids': [
                        (
                            0,
                            0,
                            {
                                "account_id": cta_conf_id.id,
                                "partner_id": partials.debit_move_id.payment_id.partner_id.id,
                                "name": (f"IGTF Divisas/{account.name}/{partials.debit_move_id.payment_id.ref}"),
                                "debit": account.igtf_debt_total,
                            }
                        ),
                        (
                            0,
                            0,
                            {
                                "account_id": partials.debit_move_id.payment_id.partner_id.property_account_payable_id.id,
                                "partner_id": partials.debit_move_id.payment_id.partner_id.id,
                                "name": (f"IGTF Divisas/{account.name}/{partials.debit_move_id.payment_id.ref}"),
                                "credit": account.igtf_debt_total,
                                "invoice_parent_id": account.id,
                            }
                        )
                    ]
                })
                move.state = 'posted'
                move.line_ids[1].reconciled = True
                return move

    def _create_igtf_move_client_rectified(self, partials):
        """
		Create IGTF move to client rectification

		This method create the IGTF move to client when the payment is in foreign exchange and the invoice is a rectification.

		params:
			partials: The partials of the payment.
		
		return:
			move: The move created.

		"""
        for account in self:
            if account.move_type == 'out_refund' and partials.credit_move_id.move_id.journal_id.type == 'sale':
                cta_conf = int(self.env['ir.config_parameter'].sudo().get_param('igtf_received_payable_id'))
                journal = int(self.env['ir.config_parameter'].sudo().get_param('journal_id_igtf'))
                journal_id = self.env['account.journal'].search([('id', '=', journal)])
                cta_conf_id = self.env['account.account'].search([('id', '=', cta_conf)])
                
                move = self.env['account.move'].create({
                    "ref": (f"IGTF Divisas/{account.name}/{partials.debit_move_id.payment_id.ref}"),
                    "usd_payment": True,
                    "date": partials.debit_move_id.payment_id.date,
                    "journal_id": journal_id.id,
                    "parent_id": partials.debit_move_id.payment_id.id,
                    "partner_id": partials.debit_move_id.payment_id.partner_id.id,
                    "foreign_currency_rate": partials.debit_move_id.payment_id.foreign_currency_rate,
                    "state": "draft",
                    'line_ids': [
                        (
                            0,
                            0,
                            {
                                "account_id": partials.debit_move_id.payment_id.partner_id.property_account_receivable_id.id,
                                "partner_id": partials.debit_move_id.payment_id.partner_id.id,
                                "name": (f"IGTF Divisas/{account.name}/{partials.debit_move_id.payment_id.ref}"),
                                "credit": account.igtf_debt_total,
                                "invoice_parent_id": account.id,
                            }
                        ),
                        (
                            0,
                            0,
                            {
                                "account_id": cta_conf_id.id,
                                "partner_id": partials.debit_move_id.payment_id.partner_id.id,
                                "name": (f"IGTF Divisas/{account.name}/{partials.debit_move_id.payment_id.ref}"),
                                "debit": account.igtf_debt_total,
                            }
                        )
                    ]
                })
                move.line_ids[0].reconciled = True
                move.state = 'posted'
                return move

    def _create_igtf_move_expense_rectified(self, partials):
        """
		Create IGTF move to expense rectification

		This method create the IGTF move to client when the payment is in foreign exchange and the invoice is a rectification.

		params:
			partials: The partials of the payment.
		
		return:
			move: The move created.

		"""
        for account in self:
            if account.move_type == 'out_refund'  and partials.credit_move_id.move_id.journal_id.type == 'sale':
                cta_conf = int(self.env['ir.config_parameter'].sudo().get_param('igtf_expense_account_id'))
                cta_conf_received = int(self.env['ir.config_parameter'].sudo().get_param('igtf_received_payable_id'))
                journal = int(self.env['ir.config_parameter'].sudo().get_param('journal_id_igtf'))
                
                journal_id = self.env['account.journal'].search([('id', '=', journal)])
                cta_conf_id = self.env['account.account'].search([('id', '=', cta_conf)])
                cta_conf_received_id = self.env['account.account'].search([('id', '=', cta_conf_received)])
                
                move = self.env['account.move'].create({
                    "ref": (f"IGTF Divisas/{account.name}/{partials.debit_move_id.payment_id.ref}"),
                    "usd_payment": True,
                    "date": partials.debit_move_id.payment_id.date,
                    "journal_id": journal_id.id,
                    "parent_id": partials.debit_move_id.payment_id.id,
                    "partner_id": partials.debit_move_id.payment_id.partner_id.id,
                    "foreign_currency_rate": partials.debit_move_id.payment_id.foreign_currency_rate,
                    "state": "draft",
                    'line_ids': [
                        (
                            0,
                            0,
                            {
                                "account_id": cta_conf_id.id,
                                "partner_id": partials.debit_move_id.payment_id.partner_id.id,
                                "name": (f"IGTF Divisas/{account.name}/{partials.debit_move_id.payment_id.ref}"),
                                "credit": account.igtf_debt_total,
                                "invoice_parent_id": account.id,
                            }
                        ),
                        (
                            0,
                            0,
                            {
                                "account_id": cta_conf_received_id.id,
                                "partner_id": partials.debit_move_id.payment_id.partner_id.id,
                                "name": (f"IGTF Divisas/{account.name}/{partials.debit_move_id.payment_id.ref}"),
                                "debit": account.igtf_debt_total,
                            }
                        )
                    ]
                })
                move.state = 'posted'
                move.line_ids[0].reconciled = True
                return move

    def _create_igtf_move_provider_rectified(self, partials):
        """
		Create IGTF move to provider rectification

		This method create the IGTF move to provider when the payment is in foreign exchange and the invoice is a rectification.

		params:
			partials: The partials of the payment.
		
		return:
			move: The move created.

		"""
        for account in self:
            if account.move_type == 'in_refund' and partials.credit_move_id.payment_id.is_igtf_on_foreign_exchange:
                journal = int(self.env['ir.config_parameter'].sudo().get_param('journal_id_igtf'))
                journal_id = self.env['account.journal'].search([('id', '=', journal)])
                cta_conf = int(self.env['ir.config_parameter'].sudo().get_param('igtf_account_especials_id'))
                cta_conf_id = self.env['account.account'].search([('id', '=', cta_conf)])
                
                move = self.env['account.move'].create({
                    "ref": (f"IGTF Divisas/{account.name}/{partials.credit_move_id.payment_id.ref}"),
                    "usd_payment": True,
                    "date": partials.credit_move_id.payment_id.date,
                    "journal_id": journal_id.id,
                    "parent_id": partials.credit_move_id.payment_id.id,
                    "partner_id": partials.credit_move_id.payment_id.partner_id.id,
                    "foreign_currency_rate": partials.credit_move_id.payment_id.foreign_currency_rate,
                    "state": "draft",
                    'line_ids': [
                        (
                            0,
                            0,
                            {
                                "account_id": cta_conf_id.id,
                                "partner_id": partials.credit_move_id.payment_id.partner_id.id,
                                "name": (f"IGTF Divisas/{account.name}/{partials.credit_move_id.payment_id.ref}"),
                                "credit": account.igtf_debt_total,
                            }
                        ),
                        (
                            0,
                            0,
                            {
                                "account_id": partials.credit_move_id.payment_id.partner_id.property_account_payable_id.id,
                                "partner_id": partials.credit_move_id.payment_id.partner_id.id,
                                "name": (f"IGTF Divisas/{account.name}/{partials.credit_move_id.payment_id.ref}"),
                                "debit": account.igtf_debt_total,
                                "invoice_parent_id": account.id,
                            }
                        )
                    ]
                })
                move.state = 'posted'
                move.line_ids[1].reconciled = True
                return move

    def _remove_outstanding_partial_igtf(self, partial_id, debit_move, credit_move):
        """
        This method remove the outstanding partials of the payment, discount the igtf amount and cancel the igtf move

        Params:
            partial_id: Contains the partials of the payment.
            debit_move: Contains the debit move of the payment.
            credit_move: Contains the credit move of the payment.
        """
        partial = self.env['account.partial.reconcile'].browse(partial_id)
        if partial.credit_move_id.payment_id.is_igtf_on_foreign_exchange == True:
            for record in debit_move:
                if record.bi_igtf >= 0 and record.igtf >= 0:
                    if record.bi_igtf <= record.amount_total:
                        record.bi_igtf = record.bi_igtf - partial.amount
                        record.igtf = record.igtf - partial.amount * (partial.credit_move_id.payment_id.igtf_percentage_on_foreign_exchange / 100)
                    else:
                        record.bi_igtf = 0
                        record.igtf = 0
                        
                    igtf_move = self.env['account.move'].search([('parent_id', '=', partial.credit_move_id.payment_id.id)])
                    igtf_move.write({
						'state': 'cancel'
					})
        elif partial.debit_move_id.payment_id.is_igtf_on_foreign_exchange == True:
            for record in credit_move:
                if record.bi_igtf >= 0 and record.igtf >= 0:
                    if record.bi_igtf <= record.amount_total:
                        record.bi_igtf = record.bi_igtf - partial.amount
                        record.igtf = record.igtf - partial.amount * (partial.debit_move_id.payment_id.igtf_percentage_on_foreign_exchange / 100)
                    else:
                        record.bi_igtf = 0
                        record.igtf = 0
                    igtf_move = self.env['account.move'].search([('parent_id', '=', partial.debit_move_id.payment_id.id)])
                    igtf_move.write({
						'state': 'cancel'
					})

    def js_remove_outstanding_partial(self, partial_id):
        partial = self.env['account.partial.reconcile'].browse(partial_id)
        self._remove_outstanding_partial_igtf(partial_id, partial.debit_move_id.move_id, partial.credit_move_id.move_id)
        res = super().js_remove_outstanding_partial(partial_id)
        return res

    
    def js_assign_outstanding_line(self, line_id):
        """
            Add the payment to the invoice's reconciliation widget.

            This function is called by the 'payment' widget when the user reconciles a suggested
            journal item with the current invoice. It will add the payment to the invoice's

            when the user pays an invoice from the invoice form view, create a igtf move and reconcile it with the payment

            params:
                -partial_ids: list of dicts containing: 'account_id', 'debit', 'credit', 'name' and 'amount_currency'
            
            example:
                [{'account_id': 1, 'debit': 0.0, 'credit': 100.0, 'name': 'payment', 'amount_currency': 0.0}]

        """
        is_igtf_config = self.env['ir.config_parameter'].sudo().get_param('is_igtf_on_foreign_exchange')
        is_igtf_expense_config = self.env['ir.config_parameter'].sudo().get_param('is_igtf_expense_account')
        is_igtf_provider_config = self.env['ir.config_parameter'].sudo().get_param('igtf_provider')
        
        res = super().js_assign_outstanding_line(line_id)
        if res['partials'].credit_move_id.payment_id.is_igtf_on_foreign_exchange == True:
            for record in self:
                record.bi_igtf += res['partials'].amount
                record.igtf += res['partials'].amount * (res['partials'].credit_move_id.payment_id.igtf_percentage_on_foreign_exchange / 100)
				#Asigando el igtf y el pago del igtf a los pagos parciales.
                res['partials'].igtf = record.igtf
                res['partials'].bi_igtf = record.bi_igtf
                
        if res['partials'].debit_move_id.payment_id.is_igtf_on_foreign_exchange == True:
            for record in self:
                record.bi_igtf += res['partials'].amount
                record.igtf += res['partials'].amount * (res['partials'].debit_move_id.payment_id.igtf_percentage_on_foreign_exchange / 100)
				#Asigando el igtf y el pago del igtf a los pagos parciales.
                res['partials'].igtf = record.igtf
                res['partials'].bi_igtf = record.bi_igtf

        #Creando los asientos de igtf dependiendo de las configuraciones
        
        if is_igtf_config and is_igtf_expense_config == False and is_igtf_provider_config == False:
            if self.move_type == 'out_invoice':
                self._create_igtf_move_client(res['partials'])
            elif self.move_type == 'out_refund':
                self._create_igtf_move_client_rectified(res['partials'])
                
        elif is_igtf_config and is_igtf_expense_config and is_igtf_expense_config == False:
            if self.move_type == 'out_invoice':
                self._create_igtf_move_expense(res['partials'])
            elif self.move_type == 'out_refund':
                self._create_igtf_move_expense_rectified(res['partials'])
                
        elif is_igtf_config and is_igtf_provider_config and is_igtf_expense_config == False:
            if self.move_type == 'in_invoice':
                self._create_igtf_move_provider(res['partials'])
            elif self.move_type == 'in_refund':
                self._create_igtf_move_provider_rectified(res['partials'])
            elif self.move_type == 'out_invoice':
                self._create_igtf_move_client(res['partials'])
            elif self.move_type == 'out_refund':
                self._create_igtf_move_client_rectified(res['partials'])

        elif is_igtf_config and is_igtf_expense_config and is_igtf_provider_config:
            if self.move_type == 'out_invoice':
                self._create_igtf_move_expense(res['partials'])
            elif self.move_type == 'out_refund':
                self._create_igtf_move_expense_rectified(res['partials'])
            elif self.move_type == 'in_invoice':
                self._create_igtf_move_provider(res['partials'])
            elif self.move_type == 'in_refund':
                self._create_igtf_move_provider_rectified(res['partials'])
        
        return res


    def action_pay_igtf(self):
        view = self.env.ref("binaural_igtf.wizard_pay_igtf_form")
        invoice = [
		]
        for record in self:
            invoice.append(record.id)
            
        return {
			"name": _("Pago de IGTF"),
			"type": "ir.actions.act_window",
			"view_mode": "form",
			"res_model": "wizard.pay.igtf",
			"views": [(view.id, 'form')],
			"view_id": view.id,
			"target": "new",
			"context": dict(
				default_move_id = self.id,
				default_amount=self.igtf,
				default_memo=self.name,
				default_tax=self.foreign_currency_rate,
			),
		}
