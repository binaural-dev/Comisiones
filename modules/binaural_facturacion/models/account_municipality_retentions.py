# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class MunicipalityRetentions(models.Model):
    _name = 'account.municipality.retentions'
    _description = 'Retenciones Municipales'

    name = fields.Char(string="Número de Comprobante", copy=False)
    date = fields.Date(string="Fecha de Comprobante",
                       required=True, copy=False)
    type = fields.Selection(selection=[
        ('out_invoice', 'Factura de Cliente'),
        ('in_invoice', 'Factura de Proveedor'),
    ], string="Tipo de Comprobante", readonly=True)
    date_accounting = fields.Date(
        string="Fecha Contable", required=True, copy=False)
    partner_id = fields.Many2one(
        'res.partner', string="Razón Social", required=True, copy=False)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('emitted', 'Emitida'),
        ('cancel', 'Cancelada')], string="Estado", default='draft', copy=False)
    retention_line_ids = fields.One2many(
        'account.municipality.retentions.line', 'retention_id', string="Retenciones", copy=False)

    #Comprobante/numero de secuencia que se guardara en asientos contables
    number = fields.Char('Comprobante')
    #  active = fields.Boolean("Active", default=True)

    @api.constrains('name')
    def constraint_name(self):
        for record in self:
            if record.name:
                if self.search([('name', '=', self.name), ('id', '!=', self.id)]):
                    raise ValidationError(
                        'Ya existe un comprobante con el número %s' % self.name)
            if record.type == 'out_invoice':
                if not self.name:
                    raise ValidationError(
                        'El número de comprobante no puede estar vacío')

    def get_sequence_municipality_retention(self):
        sequence = self.env['ir.sequence'].search(
            [('code', '=', 'retention.municipality.retention.control.number')])
        if not sequence:
            sequence = self.env['ir.sequence'].create({
                'name': 'Numero de control',
                'code': 'retention.municipality.retention.control.number',
                'padding': 5
            })
        return sequence.next_by_code('retention.municipality.retention.control.number')

    def action_validate(self):
        context = dict(self._context or {})
        for retention_line in self.retention_line_ids:
            if self.type != 'out_invoice':
                retention_line._calculate_retention()
            if not 'from_invoice' in context:
                retention_line.invoice_id.write({
                    "municipality_tax_voucher_id": self.id,
                    "municipality_tax": True
                })
            else:
                retention_line.invoice_id.write({
                    "municipality_tax_voucher_id": self.id,
                })
        move = None
        

        journal_id = None
        account_id = None
        if self.type == 'out_invoice':
            journal_id = int(self.env['ir.config_parameter'].get_param(
                'journal_municipal_retention_clients'))
            account_id = int(self.env['ir.config_parameter'].get_param(
                'account_municipal_retention_clients'))
        elif self.type == 'in_invoice':
            journal_id = int(self.env['ir.config_parameter'].get_param(
                'journal_municipal_retention'))
            account_id = int(self.env['ir.config_parameter'].get_param(
                'account_municipal_retention'))
            sequence = self.get_sequence_municipality_retention()
            self.name = str(sequence)

        entries_to_post = []

        self.state = 'emitted'


        for line in self.retention_line_ids:
            account_invoice = None
            if self.type == 'out_invoice':
                for line_invoice in line.invoice_id.line_ids:
                    if line.invoice_id.amount_total == line_invoice.debit:
                        account_invoice = line_invoice.account_id.id
            else:
                for line_invoice in line.invoice_id.line_ids:
                    if line.invoice_id.amount_total == line_invoice.credit:
                        account_invoice = line_invoice.account_id.id

            to_post = addEntryToJournal(self, journal_id, account_id, self.date_accounting, self.name, line.invoice_id.foreign_currency_rate,
                                        account_invoice, line.invoice_id.partner_id.id, line.foreign_rate, self.type, line.total_retained,  line.currency_id.id)
            entries_to_post.append(to_post)

        for index, retention_line in enumerate(self.retention_line_ids):
            entries_to_post[index].action_post()
            retention_line.invoice_id.js_assign_outstanding_line(
                entries_to_post[index].line_ids[0].id)

        #Numero de secuencia de impuestos municipales
        number = 'RM-' + self.name + "-" + self.retention_line_ids.invoice_id.name

        move = self.env['account.move'].search([('ref', '=', self.name)])  
        move.write({
            'name':number
        })

    def action_open_wizard(self):
        return {
            'name': 'Reporte de Retenciones Municipales',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'wizard.municipality.retentions',
            'context': {'default_retention_id': self.id},
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    #Cancelar impuestos municipales de proveedor, si las lineas de retencion son del proveedor se eliminan, el estado pasa 
    # a cancelado y se hace unlink, despues de esto retorna el estado cancel.
    def action_cancel(self):
        move = None
        self.retention_line_ids.invoice_id.municipality_retentions_line_ids.unlink()
        move = self.env['account.move'].search([('ref', '=', self.name)])  
        move.write({
            'state':'cancel'
        })
        self.state = 'cancel'
        #move = self.env['account.move'].search([('ref', '=' 'retention')])
        #self.unlink()
        
    

def addEntryToJournal(obj, journal_id, account_id, date_accounting, ref,
                      foreign_currency_rate, account_invoice, partner_id, foreign_rate, type, total_retained,  currency_id):
    move = None
    if type == 'out_invoice':
        move = obj.env['account.move'].create({
            'move_type': 'entry',
            'date': date_accounting,
            'journal_id': journal_id,
            'ref': ref,
            'foreign_currency_rate': foreign_currency_rate,
            'line_ids': [
                (0, 0, {
                    "account_id": account_invoice,
                    "partner_id": partner_id,
                    "foreign_currency_rate": foreign_rate,
                    "credit": total_retained,
                    'currency_id': currency_id,
                }),
                (0, 0, {
                    "account_id": account_id,
                    "partner_id": partner_id,
                    "foreign_currency_rate": foreign_rate,
                    "debit": total_retained,
                    'currency_id': currency_id,
                })
            ],
        })
    else:

        move = obj.env['account.move'].create({
            'move_type': 'entry',
            'date': date_accounting,
            'journal_id': journal_id,
            'ref': ref,
            'foreign_currency_rate': foreign_currency_rate,
            'line_ids': [
                (0, 0, {
                    "account_id": account_invoice,
                    "partner_id": partner_id,
                    "foreign_currency_rate": foreign_rate,
                    "debit": total_retained,
                    'currency_id': currency_id,
                }),
                (0, 0, {
                    "account_id": account_id,
                    "partner_id": partner_id,
                    "foreign_currency_rate": foreign_rate,
                    "credit": total_retained,
                    'currency_id': currency_id,
                })
            ],
        })
    return move


