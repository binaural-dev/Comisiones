from datetime import datetime
from odoo import http, _


class BinauralNominaReportes(http.Controller):
    @http.route("/web/binary/download_faov_txt", type="http", auth="user")
    def download_faov_txt(self, date_from, date_to):
        faov_txt_wizard = http.request.env["faov.txt.wizard"].search([])
        txt = faov_txt_wizard.generate_faov_txt(
            datetime.strptime(date_from, "%Y-%m-%d"), datetime.strptime(date_to, "%Y-%m-%d")
        )
        return http.request.make_response(
            txt["file"],
            headers=[
                ("Content-Type", "text/plain"),
                ("Content-Disposition", f"attachment; filename={txt['filename']}"),
            ],
        )

    @http.route("/web/binary/download_bnc_txt", type="http", auth="user")
    def download_bnc_txt(self, payment_method_id):
        bnc_txt = http.request.env["hr.payslip.payment.methods"].search(
            [("id", "=", payment_method_id)]
        )
        txt = bnc_txt.generate_bnc_txt()

        return http.request.make_response(
            txt["file"],
            headers=[
                ("Content-Type", "text/plain"),
                ("Content-Disposition", f"attachment; filename={txt['filename']}"),
            ],
        )

    @http.route("/web/binary/download_ivss_salary_change_txt", type="http", auth="user")
    def download_ivss_salary_change_txt(self, date_from, date_to):
        ivss_salary_change_txt_wizard = http.request.env["ivss.salary.change.txt.wizard"].search([])
        txt = ivss_salary_change_txt_wizard.generate_ivss_salary_change_txt(
            datetime.strptime(date_from, "%Y-%m-%d"), datetime.strptime(date_to, "%Y-%m-%d")
        )
        return http.request.make_response(
            txt["file"],
            headers=[
                ("Content-Type", "text/plain"),
                ("Content-Disposition", f"attachment; filename={txt['filename']}"),
            ],
        )

    @http.route("/web/binary/download_ivss_employee_ingress_txt", type="http", auth="user")
    def download_ivss_employee_ingress_txt(self, date_from, date_to):
        ivss_employee_ingress_txt_wizard = http.request.env[
            "ivss.employee.ingress.txt.wizard"
        ].search([])
        txt = ivss_employee_ingress_txt_wizard.generate_ivss_employee_ingress_txt(
            datetime.strptime(date_from, "%Y-%m-%d"), datetime.strptime(date_to, "%Y-%m-%d")
        )
        return http.request.make_response(
            txt["file"],
            headers=[
                ("Content-Type", "text/plain"),
                ("Content-Disposition", f"attachment; filename={txt['filename']}"),
            ],
        )
