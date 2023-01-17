# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from lxml import etree
import json

_logger = logging.getLogger(__name__)


class MunicipalityRetentionsLine(models.Model):
    _name = "account.municipality.retentions.line"
    _description = 'Retenciones Municipales Linea'

    name = fields.Char(string="Descripción", default="RET-Municipal")
    retention_id = fields.Many2one(
        'account.municipality.retentions', string="Retencion", ondelete='cascade')
    invoice_id = fields.Many2one(
        'account.move', string='Factura', required=True, ondelete='cascade')
    currency_id = fields.Many2one(
        'res.currency', string='Moneda', default=lambda self: self.env.user.company_id.currency_id)
    total_invoice = fields.Monetary(
        string="Total Facturado", related="invoice_id.amount_total")
    invoice_amount_untaxed = fields.Monetary(
        string="Base Imponible", related="invoice_id.amount_untaxed")
    economic_activity_id = fields.Many2one(
        'economic.activity', string="Actividad Economica")
    activity_aliquot = fields.Float(
        string="Aliquota", related="economic_activity_id.aliquot")
    total_retained = fields.Float(string="Retenido")
    foreign_rate = fields.Float(
        string="tasa foranea", related="invoice_id.foreign_currency_rate")
    foreign_total_invoice = fields.Monetary(
        string="Total Factura Alterno", related="invoice_id.foreign_amount_total")
    foreign_invoice_amount_untaxed = fields.Monetary(
        string="Base Imponible Alterno", related="invoice_id.foreign_amount_untaxed")
    foreign_total_retained = fields.Float(string="Retenido Alterno")
    municipality_id = fields.Many2one(
        'res.country.municipality', string="Municipio", related="economic_activity_id.municipality_id")

    @api.constrains('total_retained', 'total_invoice', 'foreign_total_retained')
    def _constraint_municipality_tax(self):
        for record in self:
            if record.total_retained == 0 or record.total_invoice == 0 or record.foreign_total_retained == 0:
                raise ValidationError(
                    "No se puede crear una retención con valores en cero")
                
            if record.total_retained > record.invoice_id.amount_residual:
                raise ValidationError(
                    "El monto retenido no puede ser mayor al importe adeudado de factura")

    @api.onchange('invoice_id')
    def default_economic_activity(self):
        if self.invoice_id:
            if not self.invoice_id.partner_id.economic_activity_id:
                raise UserError(
                    "Debe registrar actividad economica del cliente/proveedor")

            self.economic_activity_id = self.invoice_id.partner_id.economic_activity_id

    @api.onchange('total_retained')
    def onchange_total_retained_in_out_invoice(self):
        if self.retention_id and self.retention_id.type == 'out_invoice' and not self.env.context.get("noonchange"):
            rate_currency = self.get_rate_currency(
                "VEF", self.foreign_rate)
            self.foreign_total_retained = self.total_retained * rate_currency

        self.env.context = self.with_context(noonchange=True).env.context

    @api.onchange('foreign_total_retained')
    def onchange_total_foreign_retained_in_out_invoice(self):
        if self.retention_id and self.retention_id.type == 'out_invoice' and not self.env.context.get("noonchange"):
            rate_currency = self.get_rate_currency(
                "VEF", self.foreign_rate)
            self.total_retained = self.foreign_total_retained * rate_currency

        self.env.context = self.with_context(noonchange=True).env.context

    def get_rate_currency(self, currency_name, rate):
        decimal_function = self.env['decimal.precision'].search(
            [('name', '=', 'decimal_quantity')])
        
        foreign_currency_name = 'USD' if currency_name == 'VEF' else 'VEF'

        return decimal_function.getCurrencyValue(
            rate, currency_name, foreign_currency_name, 'CALC')

    def _calculate_retention(self):
        self.total_retained = self.invoice_amount_untaxed * \
            (self.activity_aliquot/100)
        self.get_rate_currency(
            self.currency_id.name, self.foreign_rate)
        self.foreign_total_retained = self.get_rate_currency(
            self.currency_id.name, self.foreign_rate) * self.total_retained

    @api.onchange('economic_activity_id', "invoice_amount_untaxed")
    def onchange_economic_activity_id(self):
        if self.retention_id.type != 'out_invoice':
            self._calculate_retention()

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id,
                                      view_type=view_type, toolbar=toolbar, submenu=submenu)
        foreign_currency_id = self.env["ir.config_parameter"].sudo(
        ).get_param("curreny_foreign_id")
        currency = self.env['res.currency'].browse(int(foreign_currency_id))
        company_currency = self.env.user.company_id.currency_id
        if view_type == 'tree':
            doc = etree.XML(res["arch"])
            total_retained_field = doc.xpath(
                    "//field[@name='total_retained']")[0]
            foreign_total_retained_field = doc.xpath(
                    "//field[@name='foreign_total_retained']")[0]
            total_retained_field.set(
                "string", f"Retenido {company_currency.symbol}")
            foreign_total_retained_field.set(
                "string", f"Retenido {currency.symbol}")

            res["arch"] = etree.tostring(doc, encoding="unicode")

        return res
