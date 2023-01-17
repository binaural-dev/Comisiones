from odoo.models import Model
from datetime import datetime
from odoo.exceptions import UserError
from odoo.fields import (
    Date,
    Integer,
    Float,
    Many2many,
    Selection,
    Many2one,
    Boolean
)
from odoo.api import (
    depends,
    model
)
from odoo.tools import float_is_zero
from odoo import _
from json import loads

import logging

_logger = logging.getLogger(__name__)

class AccountMoveLine(Model):
    _inherit = "account.move"
    
    _order = 'name desc'
    
    paid_seller = Selection(
        [
            ("not_paid", "not paid"),
            ("process", "in process"),
            ("paid", "paid")
        ],
        default="not_paid",
    )
    
    seller_id = Many2one(
        "hr.employee",
        string="Seller"
    )
    
    collection_days = Integer(
        compute = "_compute_collection_days",
        store = True
    )
    
    total_commission = Float(
        compute="_compute_total_commission_of_invoice",
        store=True
    )
    
    discount_invoice = Many2many(
        "account.move",
        "reversal_id",
        "move_id",
        compute="_compute_discount_invoice"
    )
    
    commission_discount = Float(
        compute="_compute_discount_invoice",
        store=True,
        help="Discount of corrective payments",
    )
    
    product_id = Many2one(
        'product.product',
        string="product",
        store=True
    )
    
    commission_invoice = Many2many(
        'account.move',
        "revert_id",
        "move_id",
        string="Invoice Commission",
    )
    
    is_commission_payment = Boolean(
        default=False
    )
    
    def action_register_payment(self):        
        if not self.date_reception and self.move_type == 'out_invoice':
            raise UserError(_('receiption date is required'))
        
        return super().action_register_payment()
        
    @model    
    def create(self,vals):
        
        is_out_invoice = vals.get('move_type',False) == 'out_invoice'
        
        if not is_out_invoice:
            return super().create(vals)
        
        partner_id = vals['partner_id']
        seller_id = self.env['res.partner'].search([('id','=',partner_id)]).seller_id.id
        
        vals.update({"seller_id":seller_id})
            
        return super().create(vals)    
    
    @model
    def calculate_commission_product(self, amount_untaxed, commission, decimal_places):
        total_commission = 0
        if not float_is_zero(commission, precision_digits=2) and amount_untaxed:
            total = (commission / 100) * amount_untaxed
            total_commission = round(total, decimal_places)

        return total_commission
    
    @depends("amount_residual")
    def _compute_discount_invoice(self):
        for record in self:
            commission_discount = 0
            discount_invoice = False
            if (
                record.currency_id.is_zero(record.amount_residual)
                and record.move_type == "out_invoice"
            ):
                if record.invoice_payments_widget:
                    discount_invoice, commission_discount = self.get_discount_invoice(
                        record.invoice_payments_widget
                    )
                    discount_invoice = self.env["account.move"].search(
                        [("id", "in", discount_invoice)]
                    )
            record.commission_discount = commission_discount * -1
            record.discount_invoice = discount_invoice
            
    @depends("total_commission", "commission_discount", "last_payment_date")
    def _compute_total_commission_of_invoice(self):
        for move in self:
            total_commission = 0
            if move.last_payment_date and move.amount_untaxed:
                for line in move.invoice_line_ids:
                    total_commission += move.calculate_commission_product(
                        line.price_subtotal,
                        line.commission,
                        move.currency_id.decimal_places,
                    )

                if total_commission != 0:
                    total_commission -= abs(move.commission_discount)

            move.total_commission = total_commission
            
    @depends("date_reception", "last_payment_date")
    def _compute_collection_days(self):
        for record in self:
            collection_days = 0
            
            if record.date_reception and record.last_payment_date:
                expired = Date.from_string(record.last_payment_date) - Date.from_string(record.date_reception)
                collection_days = expired.days
                
            record.collection_days = collection_days

    def get_discount_invoice(self, payments):
        rec_ids = []
        total_commission = 0
        res = loads(payments)
        if res and len(res.get("content")) > 0:
            for payment in res.get("content"):
                account_payment_id = payment.get("account_payment_id", False)
                
                if not account_payment_id:
                    rec_id = payment.get("move_id", False)
                    
                    if rec_id:
                        rec_invoice = self.env["account.move"].browse(int(rec_id))
                        
                        if rec_invoice.exists():
                            if rec_invoice.reversed_entry_id.exists():
                                rec_total = 0
                                reversed_invoice = rec_invoice.reversed_entry_id
                                
                                for rec_line in rec_invoice.invoice_line_ids:

                                    reversed_line = reversed_invoice.invoice_line_ids.filtered(
                                        lambda rl: rl.product_id.id == rec_line.product_id.id
                                    )
                                    
                                    rec_total += self.calculate_commission_product(
                                        rec_line.price_subtotal,
                                        reversed_line.commission,
                                        rec_invoice.currency_id.decimal_places,
                                    )
                                    
                                total_commission += rec_total
                                
                            rec_ids.append(rec_invoice.id)
                            
        return rec_ids, total_commission

    def show_invoice_resume(self):
        view = self.env.ref(
            "binaural_politica_comisiones.invoice_commission_summary_wizard_form_view"
        )
        
        invoice_lines = self.invoice_line_ids.filtered(
            lambda x: x.product_id.type in ["consu","service","product"]
        )

        return {
            "name": _("Resumen de Factura"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "invoice.commission.summary.wizard",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "flags": {"mode": "readonly"},
            "context": dict(
                self.env.context,
                default_name=self.name,
                default_invoice_line_ids=invoice_lines.ids,
            ),
        }
        
    def calculate_total_commission(self, product_amount_untaxed, product_rec_commission):
        return product_amount_untaxed * (product_rec_commission / 100)
    
    def recalculate_total_commission(self):
        invoices = self.env["account.move"].search(
            [
                ("create_date", ">=", datetime(2022, 8, 4)),
                ("move_type", "=", "out_invoice"),
                ("picking_ids", "!=", False),
            ]
        )
        
        filtered_invoices = invoices.filtered(
            lambda x: "product" in x.picking_ids.commission_images_id.mapped("policy_type")
        )

        for invoice in filtered_invoices:
            invoice._compute_discount_invoice()
            invoice._compute_total_commission_of_invoice()
            
    
    