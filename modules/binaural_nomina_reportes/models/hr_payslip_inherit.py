from odoo import api, models, _
from odoo.tools.float_utils import float_repr
from odoo.exceptions import UserError


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    @api.model
    def get_employees_data_of_slips_with_faov_in_date_range(self, date_from, date_to):
        """
        Returns the data of the payslips with faov deduction in the given date range.

        The data needed for the FAOV txt file needs to meet certain parameters:
        - Second name: If it is empty, it must be replaced with a space.
        - Second lastname: If it is empty, it must be replaced with a space.
        - FAOV deduction: It must be a number of no more than 16 characters wihtout points or
                          commas. The last two characters are the decimal part.
        - Entry date: It must be a date in the format DDMMYYYY.
        - Departure date: It must be a date in the format DDMMYYYY.
                          If it is empty, it must be replaced with a space.

        Parameters
        ----------
        date_from : date
            The start date of the date range.
        date_to : date
            The end date of the date range.

        Returns
        -------
        list
            A list of dictionaries with the data of the employees that have payslips with faov
            in the given date range.
        """
        # Structs that have rules with FAOV
        faov_struct_ids = [
            self.env.ref("binaural_nomina.structure_payroll_basic").id,
            self.env.ref("binaural_nomina.structure_payroll_vacation").id,
            self.env.ref("binaural_nomina.structure_payroll_liquidaciones").id,
        ]
        payslips = self.env["hr.payslip"].search(
            [
                ("date_from", ">=", date_from),
                ("date_to", "<=", date_to),
                ("struct_id", "in", faov_struct_ids),
            ]
        )

        # Code of the rules of FAOV
        faov_rules_codes = [
            "PMFAOV",
            "PMFAOVVACBASIC",
            "PMFAOVVAC",
            "PMFAOVLIQ",
        ]
        employees_data_with_faov = []

        for payslip in payslips:
            entry_date = payslip.employee_id.entry_date.strftime("%d%m%Y")
            departure_date = (
                payslip.employee_id.departure_date.strftime("%d%m%Y")
                if payslip.employee_id.departure_date
                else " "
            )
            employee_data = {
                "prefix_vat": payslip.employee_id.prefix_vat,
                "vat": payslip.employee_id.vat,
                "name": payslip.employee_id.name,
                "second_name": payslip.employee_id.second_name or " ",
                "lastname": payslip.employee_id.lastname,
                "second_lastname": payslip.employee_id.second_lastname or " ",
                "entry_date": entry_date,
                "departure_date": departure_date,
            }
            faov = sum(
                abs(line.total) for line in payslip.line_ids if line.code in faov_rules_codes
            )
            faov_rep = float_repr(faov, 2).split(".")
            employee_data["faov"] = f"{faov_rep[0]}{faov_rep[1]}"
            employees_data_with_faov.append(employee_data)
        return employees_data_with_faov
