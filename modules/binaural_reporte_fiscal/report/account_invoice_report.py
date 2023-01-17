from lxml import etree
from odoo import api, fields, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"


    foreign_amount_untaxed = fields.Float(string="Base imponible alterna")
    foreign_amount_tax = fields.Float(string="Impuesto Alterno")
    foreign_amount_total = fields.Float(string="Total facturado alterno")

    _depends = {
        "account.move": [
            "foreign_amount_untaxed", "foreign_amount_tax", "foreign_amount_total",
        ],
    }

    @api.model
    def _select(self):
        return super()._select() + ", move.foreign_amount_untaxed, move.foreign_amount_tax, move.foreign_amount_total"

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id, view_type=view_type,
                                      toolbar=toolbar, submenu=submenu)
        foreign_currency_id = self.env["ir.config_parameter"].sudo(
        ).get_param("curreny_foreign_id")
        if foreign_currency_id and foreign_currency_id == '2':
            doc = etree.XML(res["arch"])
            foreign_amount_untaxed = doc.xpath(
                "//field[@name='foreign_amount_untaxed']")
            if foreign_amount_untaxed:
                    foreign_amount_untaxed[0].set("string", "Base Imponible $")
                    res["arch"] = etree.tostring(doc, encoding="unicode")
            foreign_amount_tax = doc.xpath(
                "//field[@name='foreign_amount_tax']")
            if foreign_amount_tax:
                    foreign_amount_tax[0].set("string", "Impuesto $")
                    res["arch"] = etree.tostring(doc, encoding="unicode")
            foreign_amount_total = doc.xpath(
                "//field[@name='foreign_amount_total']")
            if foreign_amount_total:
                    foreign_amount_total[0].set("string", "Total Moneda $")
                    res["arch"] = etree.tostring(doc, encoding="unicode")
        else:
            doc = etree.XML(res["arch"])
            foreign_amount_untaxed = doc.xpath(
                "//field[@name='foreign_amount_untaxed']")
            if foreign_amount_untaxed:
                    foreign_amount_untaxed[0].set("string", "Base Imponible Bs.F")
                    res["arch"] = etree.tostring(doc, encoding="unicode")
            foreign_amount_tax = doc.xpath(
                "//field[@name='foreign_amount_tax']")
            if foreign_amount_tax:
                    foreign_amount_tax[0].set("string", "Impuesto Bs.F")
                    res["arch"] = etree.tostring(doc, encoding="unicode")
            foreign_amount_total = doc.xpath(
                "//field[@name='foreign_amount_total']")
            if foreign_amount_total:
                    foreign_amount_total[0].set("string", "Total Moneda Bs.F")
                    res["arch"] = etree.tostring(doc, encoding="unicode")
        return res
