from odoo import models, fields, api
from io import BytesIO
import logging

_logger = logging.getLogger(__name__)


class HrPayslipPaymentMethodsInh(models.Model):
    _inherit = "hr.payslip.payment.methods"

    def download_bnc_txt(self):
        self.ensure_one()
        url = f"/web/binary/download_bnc_txt?payment_method_id={self.id}"
        _logger.warning("URL: %s", url)
        return {"type": "ir.actions.act_url", "url": url, "target": "self"}

    def generate_bnc_txt(self):
        self.ensure_one()
        txt = {}
        with BytesIO() as f:
            for payslip in self.payslip_ids:
                p = self.env["hr.payslip"].search([("id", "=", payslip.id)])
                amount_without_decimals = str(payslip.net_wage).split(".")
                if len(amount_without_decimals[1]) < 2:
                    amount_without_decimals[1] = amount_without_decimals[1] + "0"
                amount_without_decimals = amount_without_decimals[0] + amount_without_decimals[1]

                f.write(b"NC ")
                f.write(b"%s" % (payslip.employee_id.default_account_bank_id.name.encode("utf-8")))
                f.write(b"%s" % (amount_without_decimals.encode("utf-8")))
                f.write(b"%s" % (payslip.employee_id.prefix_vat.encode("utf-8")))
                f.write(b"%s\n" % (payslip.employee_id.vat.encode("utf-8")))
            txt["file"] = f.getvalue()
            txt[
                "filename"
            ] = f"BNC_TXT_{self.date_from.strftime('%d%m%Y')}_TO_{self.date_to.strftime('%d%m%Y')}.txt"
        return txt
