# -*- coding: utf-8 -*-
import logging

from odoo import _
from odoo.exceptions import UserError,MissingError
from odoo.models import TransientModel
from odoo.fields import (
    Many2many,
    Selection
)
from odoo.api import model

_logger = logging.getLogger(__name__)

class AccountExpenseWizard(TransientModel):
    _name = 'account.expense.wizard'
    _description = 'create one or more expense records from invoices with the associated vendor.'

    move_ids = Many2many(
        'account.move',
        string='Seller invoices'
    )
    
    type_expense = Selection(
        [
            ('per_commission', 'generate an invoice for commision'),
            ('all_commissions', 'generate an invoice with all commissions')
        ],
        required=True,
        default='per_commission'
    )

    @model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        active_move_ids = self.env['account.move']
        if self.env.context['active_model'] == 'account.move' and 'active_ids' in self.env.context:
            active_move_ids = self.env['account.move'].browse(self.env.context['active_ids'])
        if len(active_move_ids.seller_id) > 1:
            raise UserError(_('You can only create expenses for the same seller'))
        if len(active_move_ids.currency_id) > 1:
            raise UserError(_('You can only create expenses with the same currency'))
        if len(active_move_ids.seller_id) > 1:
            raise UserError(_('All customers must have a vendor'))
        values['move_ids'] = [(6, 0, active_move_ids.ids)]
        return values

    def generate_invoice(self):
        self.ensure_one()
        if self.type_expense == 'per_commission':
            self.per_commission()
            return
        
        self.all_commissions()

    def per_commission(self):        
        invoices_json = []
        config_values = self.env['res.config.settings'].get_values()
        commission_journal = self.env['account.journal'].search([('id','=',config_values['commission_journal_id'])])
        for move in self.move_ids:
            invoice_line = self.format_move(move)        
            commission_journal.sequence_id.number_next_actual += 1
            invoices_json.append(invoice_line)            
        
        ordered_json = sorted(invoices_json, key=lambda commission: commission['name'],reverse=True)
        self.invoice(ordered_json,per_commission=True)
            
            

    def all_commissions(self):
        config_values = self.env['res.config.settings'].get_values()

        commission_journal = self.env['account.journal'].search([('id','=',config_values['commission_journal_id'])])
        commission_product_id = config_values['commission_product_id']   

        copy_move = [{
            'name': '',
            'address': '',
            'currency_id':  0,
            'correlative': '  ',
            'extract_state': '',
            'seller_id': 0,
            'amount_total_signed': 0.0,
            'commission_discount': 0.0 ,
            'invoice_partner_display_name': '',
            'paid_seller': '',
            'foreign_currency_rate': 0.0,
            'foreign_amount_total': 0.0,
            'invoice_line_ids': [],
            'journal_id': commission_journal.id, 
            'move_type': 'in_invoice',
            'state': 'draft',
            'payment_state': 'in_payment',
            'product_id': commission_product_id,
            'partner_id': 0,
            'invoice_line_ids': [],
            'is_commission_payment': True,
            'commission_invoice': ''
        }]
        
        total_commission = 0
        commission_discount = 0
        foreign_amount_total = 0
        lines = []
        
        for move in self.move_ids:
            total_commission += move.total_commission
            commission_discount += move.commission_discount
            foreign_amount_total += move.foreign_amount_total

            name = self._format_name_all_invoices(commission_journal.sequence_id.number_next_actual)
            rname = move.discount_invoice.name if len(move.discount_invoice) == 1 else '' 
            
            copy_move[0]['name'] = name
            copy_move[0]['paid_seller'] = move.paid_seller
            copy_move[0]['currency_id'] = move.currency_id.id
            copy_move[0]['invoice_partner_display_name'] = move.invoice_partner_display_name
            copy_move[0]['seller_id'] = move.seller_id.id
            copy_move[0]['foreign_currency_rate'] = move.foreign_currency_rate
            copy_move[0]['extract_state'] = move.extract_state
            copy_move[0]['address'] = move.address
            copy_move[0]['partner_id'] = move.seller_id.address_home_id.id        
            lines.append((0, 0, {
                'currency_id': move.currency_id.id,
                'product_id': commission_product_id,
                'quantity': 1,
                'price_unit': move.total_commission,
                'name': f'{move.name} / NC: {rname}' if rname != '' else move.name
            })) 
        
        copy_move[0]['invoice_line_ids'] = lines
        copy_move[0]['foreign_amount_total'] = foreign_amount_total    
        copy_move[0]['amount_total_signed'] = total_commission
        copy_move[0]['commission_discount'] = commission_discount
        copy_move[0]['commission_invoice'] = self
        if len(self.move_ids) > 0:
            self.invoice(copy_move)
    
    def format_move(self,move):
        config_values = self.env['res.config.settings'].get_values()
        commission_journal = self.env['account.journal'].search([('id','=',config_values['commission_journal_id'])])
        commission_product_id = config_values['commission_product_id']
        
        name = self._format_name_all_invoices(commission_journal.sequence_id.number_next_actual)
        rname = move.discount_invoice.name if len(move.discount_invoice) == 1 else '' 
        
        return {
                'name': name,
                'address': move.address,
                'currency_id': move.currency_id.id,
                'extract_state': move.extract_state,
                'seller_id': move.seller_id.id,
                'amount_total_signed': move.total_commission,
                'commission_discount': move.commission_discount,
                'invoice_partner_display_name': move.invoice_partner_display_name,
                'paid_seller': 'process',
                'foreign_currency_rate': move.foreign_currency_rate,
                'foreign_amount_total': move.foreign_amount_total,
                'journal_id': commission_journal.id, 
                'move_type': 'in_invoice',
                'state': 'draft',
                'payment_state': 'in_payment',
                'product_id': commission_product_id,
                'partner_id': move.seller_id.address_home_id.id,
                'invoice_line_ids': [(0, 0, {
                    'currency_id': move.currency_id.id,
                    'product_id': commission_product_id,
                    'quantity': 1,
                    'price_unit': move.total_commission,
                    'name': f'{move.name} / NC: {rname}' if rname != '' else move.name 
                })],
                'commission_invoice': move,
                'is_commission_payment': True,   
            }
    
    
    def invoice(self, invoice_json,per_commission=None):
        config_values = self.env['res.config.settings'].get_values()
        commission_journal = self.env['account.journal'].search([('id','=',config_values['commission_journal_id'])])
        AccountMove = self.env['account.move']          
        try:
            index = 0
            for json in invoice_json:                
                if per_commission:
                    move = AccountMove.create([json])
                    move.line_ids[-1].name = move.name
                    json.commission_invoice = move
                    index += 1
                    
                    
            if per_commission:
                self.move_ids.write({
                    'paid_seller': 'process'
                }) 
                return
                     
            move = AccountMove.create(invoice_json)    
            move.line_ids[-1].name = move.name       
            
            self.move_ids.write({
                'paid_seller': 'process'
            })            
            
            self.move_ids.commission_invoice = move

            commission_journal.sequence_id.number_next_actual += 1
            
        except Exception as e:
            raise MissingError(e)
    
    def _format_name_all_invoices(self,name):
        return f'{name}'.rjust(4).replace(' ','0')        