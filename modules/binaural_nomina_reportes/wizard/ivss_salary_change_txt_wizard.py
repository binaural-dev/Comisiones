from io import BytesIO
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class IvssSalaryChangeTxtWizard(models.TransientModel):
    _name = "ivss.salary.change.txt.wizard"
    _description = "Wizard to generate IVSS salary change txt file"

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)

    def download_ivss_salary_change_txt(self):
        self.ensure_one()
        salary_change_count = self.env["hr.employee.salary.change"].search_count(
            [
                ("date", ">=", self.date_from),
                ("date", "<=", self.date_to),
            ]
        )
        if salary_change_count == 0:
            raise UserError(_("No salary variations found for the selected date range."))
        if salary_change_count > 10000:
            raise UserError(
                _(
                    "The number of salary variations is over 10,000, "
                    "please select a smaller date range."
                )
            )
        url = (
            "/web/binary/download_ivss_salary_change_txt?"
            f"&date_from={self.date_from}&date_to={self.date_to}"
        )
        return {"type": "ir.actions.act_url", "url": url, "target": "self"}

    @api.model
    def generate_ivss_salary_change_txt(self, date_from, date_to):
        salary_changes_data = self.env[
            "hr.employee.salary.change"
        ].get_employee_data_of_salary_changes_on_the_given_range(date_from, date_to)
        fields_separator = self.env["ir.config_parameter"].sudo().get_param("separador_campos_ivss")
        txt = {}
        with BytesIO() as f:
            for salary_change in salary_changes_data:
                f.write(
                    b"%s%s"
                    % (
                        salary_change["prefix_vat"].encode("utf-8"),
                        fields_separator.encode("utf-8"),
                    )
                )
                f.write(
                    b"%s%s"
                    % (salary_change["vat"].encode("utf-8"), fields_separator.encode("utf-8"))
                )
                f.write(
                    b"%s%s"
                    % (salary_change["name"].encode("utf-8"), fields_separator.encode("utf-8"))
                )
                f.write(
                    b"%s%s"
                    % (
                        salary_change["weekly_wage"].encode("utf-8"),
                        fields_separator.encode("utf-8"),
                    )
                )
                f.write(
                    b"%s%s"
                    % (
                        salary_change["new_weekly_wage"].encode("utf-8"),
                        fields_separator.encode("utf-8"),
                    )
                )
                f.write(
                    b"%s%s"
                    % (salary_change["date"].encode("utf-8"), fields_separator.encode("utf-8"))
                )
                if salary_changes_data[-1] != salary_change:
                    f.write(b"\n")
            txt["file"] = f.getvalue()
            txt["filename"] = (
                _("salary_changes-%s", date_from.strftime("%d%m%Y"))
                + f"-{date_to.strftime('%d%m%Y')}.txt"
            )
        return txt
