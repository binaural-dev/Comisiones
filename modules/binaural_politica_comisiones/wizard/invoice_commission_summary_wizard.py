import logging
from lxml import etree

from odoo.models import TransientModel
from odoo.fields import (
    Char,
    Many2many
)
from odoo import api

_logger = logging.getLogger(__name__)


class InvoiceCommissionSummaryWizard(TransientModel):
    _name = 'invoice.commission.summary.wizard'
    _description = 'Invoice Commission Summary Wizard'

    name = Char(
        "Name",
        required=True
    )
    
    invoice_line_ids = Many2many(
        'account.move.line',
        'commission_sumary_rel',
        string="Invoice Lines"
    )
    
    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)    
        company = api.Environment(self.env.cr, self.env.uid, {})['res.company'].browse(1)
        currency_id = company.currency_id.id
        currency_symbol = self.env['res.currency'].search([('id','=',currency_id)]).symbol
        
        if view_type == 'form':
            doc = etree.XML(res["arch"])
            price_subtotal = self.env['account.move.line'].fields_get(['price_subtotal'])
            invoice_line_ids_field = doc.xpath("//field[@name='invoice_line_ids']")
            if not price_subtotal is None:
                price_subtotal['price_subtotal']["string"] = f"Subtotal ({currency_symbol})"                
                invoice_line_ids_field.append(price_subtotal)
                res["arch"] = etree.tostring(doc, encoding="unicode")
                
        return res
