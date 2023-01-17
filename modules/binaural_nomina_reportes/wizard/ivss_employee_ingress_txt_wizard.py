from io import BytesIO
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class IvssIngressTxtWizard(models.TransientModel):
    _name = "ivss.employee.ingress.txt.wizard"
    _description = "Wizard to generate IVSS employee ingress txt file"

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)

    def download_ivss_employee_ingress_txt(self):
        """
        Calls the controller that generates and downloads the txt file of the IVSS employee ingress.

        Returns
        -------
            dict
                The action calling the controller that downloads the file.
        """
        self.ensure_one()

        self._validate_employee_fields_for_txt()

        url = (
            "/web/binary/download_ivss_employee_ingress_txt?"
            f"&date_from={self.date_from}&date_to={self.date_to}"
        )
        return {"type": "ir.actions.act_url", "url": url, "target": "self"}

    def _validate_employee_fields_for_txt(self):
        """
        Raises an error if any of the employees that have ingressed on the given date range have
        invalid data.

        They must have data in the following fields:
            - type
            - entry_occupation_id
            - condition
            - motor_skill
            - state_id
            - municipality_id
            - parish_id
            - private_mobile_phone
            - work_email
        """
        self.ensure_one()
        employees = self.env["hr.employee"].search(
            [
                ("contract_id", "!=", False),
                ("entry_date", "!=", False),
                ("entry_date", ">=", self.date_from),
                ("entry_date", "<=", self.date_to),
            ]
        )
        if len(employees) == 0:
            raise UserError(_("No employees ingress are registered for the selected date range."))
        if len(employees) > 10000:
            raise UserError(
                _(
                    "The number of employee ingresses is over 10,000, "
                    "please select a smaller date range."
                )
            )

        invalid_employees_names = []
        for employee in employees:
            all_fields_for_the_report_are_valid = (
                employee.type
                and employee.entry_occupation_id
                and employee.condition
                and employee.motor_skill
                and employee.state_id
                and employee.municipality_id
                and employee.parish_id
                and employee.private_mobile_phone
                and employee.work_email
            )
            if not all_fields_for_the_report_are_valid:
                invalid_employees_names.append(f"{employee.name} {employee.lastname}")

        if any(invalid_employees_names):
            error_message = _("There is an error with the data of the following employees:\n")

            for name in invalid_employees_names:
                error_message += f"\t*{name}\n"
            error_message += _(
                "The following fields are required:\n"
                "\tType, Occupation, Condition, Motor Skill, State, Municipality, Parish, "
                "Phone, Private Mobile Phone and Work Email."
            )

            raise ValidationError(error_message)

    @api.model
    def generate_ivss_employee_ingress_txt(self, date_from, date_to):
        """
        Generates the txt file of the IVSS employee ingress.

        It gets the employees that have ingressed on the given date range and generates a txt file.

        Parameters
        ----------
        date_from : date
            The start date of the date range.
        date_to : date
            The end date of the date range.

        Returns
        -------
        dict
            A dictionary with the file name and the file content.
        """
        employees_data = self.env["hr.employee"].get_ingresses_data_on_the_given_range(
            date_from, date_to
        )
        fields_separator = self.env["ir.config_parameter"].sudo().get_param("separador_campos_ivss")
        txt = {}
        with BytesIO() as file:
            for employee in employees_data:
                file.write(
                    b"%s%s"
                    % (employee["prefix_vat"].encode("utf-8"), fields_separator.encode("utf-8"))
                )
                file.write(
                    b"%s%s" % (employee["vat"].encode("utf-8"), fields_separator.encode("utf-8"))
                )
                file.write(
                    b"%s%s" % (employee["name"].encode("utf-8"), fields_separator.encode("utf-8"))
                )
                file.write(
                    b"%s%s"
                    % (employee["entry_date"].encode("utf-8"), fields_separator.encode("utf-8"))
                )
                file.write(
                    b"%s%s"
                    % (employee["weekly_wage"].encode("utf-8"), fields_separator.encode("utf-8"))
                )
                file.write(
                    b"%s%s" % (employee["type"].encode("utf-8"), fields_separator.encode("utf-8"))
                )
                file.write(
                    b"%s%s"
                    % (employee["occupation"].encode("utf-8"), fields_separator.encode("utf-8"))
                )
                file.write(
                    b"%s%s"
                    % (employee["condition"].encode("utf-8"), fields_separator.encode("utf-8"))
                )
                file.write(
                    b"%s%s"
                    % (employee["motor_skill"].encode("utf-8"), fields_separator.encode("utf-8"))
                )
                file.write(
                    b"%s%s" % (employee["state"].encode("utf-8"), fields_separator.encode("utf-8"))
                )
                file.write(
                    b"%s%s"
                    % (employee["municipality"].encode("utf-8"), fields_separator.encode("utf-8"))
                )
                file.write(
                    b"%s%s" % (employee["parish"].encode("utf-8"), fields_separator.encode("utf-8"))
                )
                file.write(
                    b"%s%s"
                    % (employee["address"].encode("utf-8"), fields_separator.encode("utf-8"))
                )
                file.write(
                    b"%s%s" % (employee["phone"].encode("utf-8"), fields_separator.encode("utf-8"))
                )
                file.write(
                    b"%s%s" % (employee["mobile"].encode("utf-8"), fields_separator.encode("utf-8"))
                )
                file.write(
                    b"%s%s" % (employee["email"].encode("utf-8"), fields_separator.encode("utf-8"))
                )
                if employees_data[-1] != employee:
                    file.write(b"\n")
            txt["file"] = file.getvalue()
            txt["filename"] = (
                _("employee_ingresses-%s", date_from.strftime("%d%m%Y"))
                + f"-{date_to.strftime('%d%m%Y')}.txt"
            )
        return txt
