from io import BytesIO
import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class FaovTxtWizard(models.TransientModel):
    _name = "faov.txt.wizard"
    _description = "Wizard to generate FAOV txt file"

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)

    def download_faov_txt(self):
        self.ensure_one()
        url = f"/web/binary/download_faov_txt?&date_from={self.date_from}&date_to={self.date_to}"
        _logger.warning("URL: %s", url)
        return {"type": "ir.actions.act_url", "url": url, "target": "self"}

    @api.model
    def generate_faov_txt(self, date_from, date_to):
        employees_data = self.env["hr.payslip"].get_employees_data_of_slips_with_faov_in_date_range(
            date_from, date_to
        )
        payroll_affiliate_number = (
            self.env["ir.config_parameter"].sudo().get_param("numero_afiliacion_nomina")
        )
        txt = {}
        with BytesIO() as f:
            for employee in employees_data:
                f.write(b"%s," % (employee["prefix_vat"].encode("utf-8")))
                f.write(b"%s," % (employee["vat"].encode("utf-8")))
                f.write(b"%s," % (employee["name"].encode("utf-8")))
                f.write(b"%s," % (employee["second_name"].encode("utf-8")))
                f.write(b"%s," % (employee["lastname"].encode("utf-8")))
                f.write(b"%s," % (employee["second_lastname"].encode("utf-8")))
                f.write(b"%s," % (employee["faov"].encode("utf-8")))
                f.write(b"%s," % (employee["entry_date"].encode("utf-8")))
                f.write(b"%s\n" % (employee["departure_date"].encode("utf-8")))
            txt["file"] = f.getvalue()
            txt["filename"] = f"N{payroll_affiliate_number}{date_from.strftime('%m%Y')}.txt"
        return txt
