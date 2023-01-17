from odoo import api, fields, models
from lxml import etree
import json
import logging

_logger = logging.getLogger(__name__)


def _get_out_debit_to_move_type_alternative(record):
    if record.move_type in ["out_invoice", "in_invoice"] and any(record.debit_origin_id):
        return "out_debit"

    return None


class AccountMove(models.Model):
    _inherit = "account.move"

    move_type_alternative = fields.Char(compute="_compute_move_type_alternative")

    @api.depends("move_type")
    def _compute_move_type_alternative(self):
        for record in self:
            record.move_type_alternative = False

            if any(record.move_type):
                out_debit = _get_out_debit_to_move_type_alternative(record)

                if out_debit:
                    record.move_type_alternative = out_debit

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super().fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        foreign_currency_id = self.env["ir.config_parameter"].sudo().get_param("curreny_foreign_id")
        foreign_currency_symbol = ""
        if foreign_currency_id:
            foreign_currency_record = self.env["res.currency"].search(
                [("id", "=", int(foreign_currency_id))]
            )
            foreign_currency_symbol = foreign_currency_record.symbol
        municipality_retention = (
            self.env["ir.config_parameter"].sudo().get_param("use_municipal_retention")
        )
        if foreign_currency_id and foreign_currency_id == "2":
            if view_type == "tree":
                doc = etree.XML(res["arch"])
                foreign_amount_total = doc.xpath("//field[@name='foreign_amount_total']")
                if foreign_amount_total:
                    foreign_amount_total[0].set("string", f"Total Moneda {foreign_currency_symbol}")
                    res["arch"] = etree.tostring(doc, encoding="unicode")
            elif view_type == "form":
                doc_p = etree.XML(res["arch"])
                page_usd = doc_p.xpath("//page[@name='alternate_coin_usd']")[0]
                page_usd.set("string", f"Moneda {foreign_currency_symbol}")
                res["arch"] = etree.tostring(doc_p, encoding="unicode")
                doc = etree.XML(res["fields"]["invoice_line_ids"]["views"]["tree"]["arch"])
                foreign_price_unit = doc.xpath("//field[@name='foreign_price_unit']")[0]
                foreign_price_unit.set("string", f"Precio {foreign_currency_symbol}")
                foreign_subtotal = doc.xpath("//field[@name='foreign_subtotal']")[0]
                foreign_subtotal.set("string", f"Subtotal {foreign_currency_symbol}")
                res["fields"]["invoice_line_ids"]["views"]["tree"]["arch"] = etree.tostring(
                    doc, encoding="unicode"
                )
                doc = etree.XML(res["fields"]["retention_iva_line_ids"]["views"]["tree"]["arch"])
                foreign_facture_amount = doc.xpath("//field[@name='foreign_facture_amount']")[0]
                foreign_facture_amount.set("string", f"Base Imponible {foreign_currency_symbol}")
                foreign_facture_total = doc.xpath("//field[@name='foreign_facture_total']")[0]
                foreign_facture_total.set("string", f"Total Factura {foreign_currency_symbol}")
                foreign_iva_amount = doc.xpath("//field[@name='foreign_iva_amount']")[0]
                foreign_iva_amount.set("string", f"Iva Factura {foreign_currency_symbol}")
                foreign_retention_amount = doc.xpath("//field[@name='foreign_retention_amount']")[0]
                foreign_retention_amount.set("string", f"Monto Retenido {foreign_currency_symbol}")
                res["fields"]["retention_iva_line_ids"]["views"]["tree"]["arch"] = etree.tostring(
                    doc, encoding="unicode"
                )

                doc = etree.XML(res["fields"]["retention_islr_line_ids"]["views"]["tree"]["arch"])
                foreign_facture_amount = doc.xpath("//field[@name='foreign_facture_amount']")[0]
                foreign_facture_amount.set("string", f"Base Imponible {foreign_currency_symbol}")
                foreign_facture_total = doc.xpath("//field[@name='foreign_facture_total']")[0]
                foreign_facture_total.set("string", f"Total Factura {foreign_currency_symbol}")
                foreign_iva_amount = doc.xpath("//field[@name='foreign_iva_amount']")[0]
                foreign_iva_amount.set("string", f"Iva Factura {foreign_currency_symbol}")
                foreign_retention_amount = doc.xpath("//field[@name='foreign_retention_amount']")[0]
                foreign_retention_amount.set("string", f"Monto Retenido {foreign_currency_symbol}")
                res["fields"]["retention_islr_line_ids"]["views"]["tree"]["arch"] = etree.tostring(
                    doc, encoding="unicode"
                )
        elif foreign_currency_id and foreign_currency_id == "3":
            if view_type == "tree":
                doc = etree.XML(res["arch"])
                foreign_amount_total = doc.xpath("//field[@name='foreign_amount_total']")
                if foreign_amount_total:
                    foreign_amount_total[0].set("string", f"Total Moneda {foreign_currency_symbol}")
                    res["arch"] = etree.tostring(doc, encoding="unicode")
            elif view_type == "form":
                doc_p = etree.XML(res["arch"])
                doc = etree.XML(res["fields"]["invoice_line_ids"]["views"]["tree"]["arch"])
                foreign_price_unit = doc.xpath("//field[@name='foreign_price_unit']")[0]
                foreign_price_unit.set("string", f"Precio {foreign_currency_symbol}")
                foreign_subtotal = doc.xpath("//field[@name='foreign_subtotal']")[0]
                foreign_subtotal.set("string", f"Subtotal {foreign_currency_symbol}")
                res["fields"]["invoice_line_ids"]["views"]["tree"]["arch"] = etree.tostring(
                    doc, encoding="unicode"
                )
                page_bsf = doc_p.xpath("//page[@name='alternate_coin_bsf']")[0]
                page_bsf.set("string", f"Moneda {foreign_currency_symbol}")
                doc = etree.XML(res["fields"]["retention_iva_line_ids"]["views"]["tree"]["arch"])
                foreign_facture_amount = doc.xpath("//field[@name='foreign_facture_amount']")[0]
                foreign_facture_amount.set("string", f"Base Imponible {foreign_currency_symbol}")
                foreign_facture_total = doc.xpath("//field[@name='foreign_facture_total']")[0]
                foreign_facture_total.set("string", f"Total Factura {foreign_currency_symbol}")
                foreign_iva_amount = doc.xpath("//field[@name='foreign_iva_amount']")[0]
                foreign_iva_amount.set("string", f"Iva Factura {foreign_currency_symbol}")
                foreign_retention_amount = doc.xpath("//field[@name='foreign_retention_amount']")[0]
                foreign_retention_amount.set("string", f"Monto Retenido {foreign_currency_symbol}")
                res["fields"]["retention_iva_line_ids"]["views"]["tree"]["arch"] = etree.tostring(
                    doc, encoding="unicode"
                )

                doc = etree.XML(res["fields"]["retention_islr_line_ids"]["views"]["tree"]["arch"])
                foreign_facture_amount = doc.xpath("//field[@name='foreign_facture_amount']")[0]
                foreign_facture_amount.set("string", f"Base Imponible {foreign_currency_symbol}")
                foreign_facture_total = doc.xpath("//field[@name='foreign_facture_total']")[0]
                foreign_facture_total.set("string", f"Total Factura {foreign_currency_symbol}")
                foreign_iva_amount = doc.xpath("//field[@name='foreign_iva_amount']")[0]
                foreign_iva_amount.set("string", f"Iva Factura {foreign_currency_symbol}")
                foreign_retention_amount = doc.xpath("//field[@name='foreign_retention_amount']")[0]
                foreign_retention_amount.set("string", f"Monto Retenido {foreign_currency_symbol}")
                res["fields"]["retention_islr_line_ids"]["views"]["tree"]["arch"] = etree.tostring(
                    doc, encoding="unicode"
                )
                res["arch"] = etree.tostring(doc_p, encoding="unicode")
        if not municipality_retention and view_type == "form":
            doc = etree.XML(res["arch"])
            municipality_field = doc.xpath("//field[@name='municipality_tax']")[0]
            modifiers_field = json.loads(municipality_field.get("modifiers") or "{}")
            modifiers_field["invisible"] = True
            municipality_field.set("modifiers", json.dumps(modifiers_field))

            municipality_voucher = doc.xpath("//field[@name='municipality_tax_voucher_id']")[0]
            modifiers_voucher = json.loads(municipality_voucher.get("modifiers") or "{}")
            modifiers_voucher["invisible"] = True
            municipality_voucher.set("modifiers", json.dumps(modifiers_voucher))

            municipality_page = doc.xpath("//page[@name='imp_municipales']")[0]
            modifiers_page = json.loads(municipality_page.get("modifiers") or "{}")
            modifiers_page["invisible"] = True
            municipality_page.set("modifiers", json.dumps(modifiers_page))

            res["arch"] = etree.tostring(doc, encoding="unicode")

        elif municipality_retention and view_type == "form":
            context = dict(self._context or {})

            if "default_move_type" in context and context["default_move_type"] in [
                "in_invoice",
                "in_refund",
                "out_invoice",
                "out_refund",
            ]:
                doc = etree.XML(res["arch"])
                municipality_field = doc.xpath("//field[@name='municipality_tax']")[0]
                modifiers_field = json.loads(municipality_field.get("modifiers") or "{}")
                if context["default_move_type"] in ["out_invoice", "out_refund"]:
                    modifiers_field["invisible"] = True
                else:
                    modifiers_field["invisible"] = False
                municipality_field.set("modifiers", json.dumps(modifiers_field))

                municipality_voucher = doc.xpath("//field[@name='municipality_tax_voucher_id']")[0]
                modifiers_voucher = json.loads(municipality_voucher.get("modifiers") or "{}")
                modifiers_voucher["invisible"] = False
                municipality_voucher.set("modifiers", json.dumps(modifiers_voucher))

                municipality_page = doc.xpath("//page[@name='imp_municipales']")[0]
                modifiers_page = json.loads(municipality_page.get("modifiers") or "{}")
                modifiers_page["invisible"] = False
                municipality_page.set("modifiers", json.dumps(modifiers_page))

                res["arch"] = etree.tostring(doc, encoding="unicode")
            else:
                doc = etree.XML(res["arch"])
                municipality_field = doc.xpath("//field[@name='municipality_tax']")[0]
                modifiers_field = json.loads(municipality_field.get("modifiers") or "{}")
                modifiers_field["invisible"] = True
                municipality_field.set("modifiers", json.dumps(modifiers_field))

                municipality_voucher = doc.xpath("//field[@name='municipality_tax_voucher_id']")[0]
                modifiers_voucher = json.loads(municipality_voucher.get("modifiers") or "{}")
                modifiers_voucher["invisible"] = True
                municipality_voucher.set("modifiers", json.dumps(modifiers_voucher))

                municipality_page = doc.xpath("//page[@name='imp_municipales']")[0]
                modifiers_page = json.loads(municipality_page.get("modifiers") or "{}")
                modifiers_page["invisible"] = True
                municipality_page.set("modifiers", json.dumps(modifiers_page))

                res["arch"] = etree.tostring(doc, encoding="unicode")

        return res


class AccountRetention(models.Model):
    _inherit = "account.retention"

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super().fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        foreign_currency_id = self.env["ir.config_parameter"].sudo().get_param("curreny_foreign_id")
        foreign_currency_symbol = ""
        if foreign_currency_id:
            foreign_currency_record = self.env["res.currency"].search(
                [("id", "=", int(foreign_currency_id))]
            )
            foreign_currency_symbol = foreign_currency_record.symbol
        if foreign_currency_id and foreign_currency_id == "2":
            if view_type == "form":
                doc = etree.XML(res["fields"]["retention_line"]["views"]["tree"]["arch"])
                foreign_facture_amount = doc.xpath("//field[@name='foreign_facture_amount']")[0]
                foreign_facture_amount.set("string", f"Base Imponible {foreign_currency_symbol}")
                foreign_facture_total = doc.xpath("//field[@name='foreign_facture_total']")[0]
                foreign_facture_total.set("string", f"Total Factura {foreign_currency_symbol}")
                foreign_iva_amount = doc.xpath("//field[@name='foreign_iva_amount']")[0]
                foreign_iva_amount.set("string", f"Iva Factura {foreign_currency_symbol}")
                foreign_retention_amount = doc.xpath("//field[@name='foreign_retention_amount']")[0]
                foreign_retention_amount.set("string", f"Monto Retenido {foreign_currency_symbol}")
                res["fields"]["retention_line"]["views"]["tree"]["arch"] = etree.tostring(
                    doc, encoding="unicode"
                )
        elif foreign_currency_id and foreign_currency_id == "3":
            if view_type == "form":
                doc = etree.XML(res["fields"]["retention_line"]["views"]["tree"]["arch"])
                foreign_facture_amount = doc.xpath("//field[@name='foreign_facture_amount']")[0]
                foreign_facture_amount.set("string", f"Base Imponible {foreign_currency_symbol}")
                foreign_facture_total = doc.xpath("//field[@name='foreign_facture_total']")[0]
                foreign_facture_total.set("string", f"Total Factura {foreign_currency_symbol}")
                foreign_iva_amount = doc.xpath("//field[@name='foreign_iva_amount']")[0]
                foreign_iva_amount.set("string", f"Iva Factura {foreign_currency_symbol}")
                foreign_retention_amount = doc.xpath("//field[@name='foreign_retention_amount']")[0]
                foreign_retention_amount.set("string", f"Monto Retenido {foreign_currency_symbol}")
                res["fields"]["retention_line"]["views"]["tree"]["arch"] = etree.tostring(
                    doc, encoding="unicode"
                )
        foreign_currency_id = int(
            self.env["ir.config_parameter"].sudo().get_param("curreny_foreign_id")
        )
        if view_type == "form":
            doc = etree.XML(res["fields"]["retention_line"]["views"]["tree"]["arch"])
            facture_amount = doc.xpath("//field[@name='facture_amount']")[0]
            facture_amount.set("string", f"Base Imponible {self.company_id.currency_id.symbol}")
            facture_total = doc.xpath("//field[@name='facture_total']")[0]
            facture_total.set("string", f"Total Factura {foreign_currency_symbol}")
            iva_amount = doc.xpath("//field[@name='iva_amount']")[0]
            iva_amount.set("string", f"Iva Factura {foreign_currency_symbol}")

            foreign_facture_amount = doc.xpath("//field[@name='foreign_facture_amount']")[0]
            foreign_facture_amount.set("string", f"Base Imponible {foreign_currency_symbol}")
            foreign_facture_total = doc.xpath("//field[@name='foreign_facture_total']")[0]
            foreign_facture_total.set("string", f"Total Factura {foreign_currency_symbol}")
            foreign_iva_amount = doc.xpath("//field[@name='foreign_iva_amount']")[0]
            foreign_iva_amount.set("string", f"Iva Factura {foreign_currency_symbol}")

            retention_amount = doc.xpath("//field[@name='retention_amount']")[0]
            foreign_retention_amount = doc.xpath("//field[@name='foreign_retention_amount']")[0]
            if foreign_currency_id == 3:
                retention_amount.set("string", f"Monto Retenido $")
                foreign_retention_amount.set("string", f"Monto Retenido {foreign_currency_symbol}")
                retention_amount.set("optional", "hide")
                retention_amount.set("options", "{}")
            elif foreign_currency_id == 2:
                retention_amount.set("string", f"Monto Retenido {foreign_currency_symbol}")
                foreign_retention_amount.set("string", f"Monto Retenido {foreign_currency_symbol}]")
                foreign_retention_amount.set("optional", "hide")
                foreign_retention_amount.set("options", "{}")

            res["fields"]["retention_line"]["views"]["tree"]["arch"] = etree.tostring(
                doc, encoding="unicode"
            )
        return res
