from odoo import api, models


class PrePayslipRunReport(models.AbstractModel):
    _name = "report.binaural_nomina_reportes.report_pre_payslip_run"

    @api.model
    def _get_report_values(self, docids, data=None):
        runs = self.env["hr.payslip.run"].browse(docids)
        docs = runs.mapped("slip_ids")
        date_start = runs[0].date_start
        date_end = runs[0].date_end
        return {
              "doc_ids": docids,
              "doc_model": "hr.payslip.run",
              "docs": docs,
              "data": data,
              "user_lang": self.env.user.lang,
              "date_start": date_start,
              "date_end": date_end,
        }
