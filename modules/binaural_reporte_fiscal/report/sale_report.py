from lxml import etree
from odoo import api, fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    foreign_amount_untaxed = fields.Float(string="Base imponible alterna")
    foreign_amount_tax = fields.Float(string="Impuesto Alterno")
    foreign_amount_total = fields.Float(string="Total facturado alterno")

    def _query(self, with_clause="", fields={}, groupby="", from_clause=""):
        fields["foreign_amount_untaxed"] = ", s.foreign_amount_untaxed AS foreign_amount_untaxed"
        fields["foreign_amount_tax"] = ", s.foreign_amount_tax AS foreign_amount_tax"
        fields["foreign_amount_total"] = ", s.foreign_amount_total AS foreign_amount_total"
        groupby += ", s.foreign_amount_untaxed, s.foreign_amount_tax, s.foreign_amount_total"
        return super()._query(with_clause, fields, groupby, from_clause)

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

            if view_type == "dashboard":
                doc = etree.XML(res["arch"])

                foreign_amount_total_all = doc.xpath(
                    "//aggregate[@name='foreign_amount_total_all']")
                if foreign_amount_total_all:
                    foreign_amount_total_all[0].set("string", "Ventas totales $")
                    res["arch"] = etree.tostring(doc, encoding="unicode")
                foreign_amount_untaxed_all = doc.xpath(
                    "//aggregate[@name='foreign_amount_untaxed_all']")
                if foreign_amount_untaxed_all:
                    foreign_amount_untaxed_all[0].set("string", "Total libre de impuestos $")
                    res["arch"] = etree.tostring(doc, encoding="unicode")
                foreign_amount_tax_all = doc.xpath(
                    "//aggregate[@name='foreign_amount_tax_all']")
                if foreign_amount_tax_all:
                    foreign_amount_tax_all[0].set("string", "Total impuestos $")
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
