import logging
from odoo.tools.float_utils import float_repr
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class HrEmployeeSalaryChange(models.Model):
    _inherit = "hr.employee.salary.change"

    previous_wage = fields.Float(compute="_compute_previous_wage")

    def _compute_previous_wage(self):
        self.previous_wage = 0.0
        for salary_change in self:
            salary_changes_of_the_same_employee = self.env["hr.employee.salary.change"].search(
                [
                    ("employee_id", "=", salary_change.employee_id.id),
                    ("id", "!=", salary_change.id),
                    ("date", "<=", salary_change.date),
                ],
                order="date DESC, id DESC",
                limit=1,
            )
            if salary_changes_of_the_same_employee:
                salary_change.previous_wage = salary_changes_of_the_same_employee.wage

    @api.model
    def get_employee_data_of_salary_changes_on_the_given_range(self, date_from, date_to):
        """
        Returns the data of the employees with salary changes on the given date range.

        Parameters
        ----------
        date_from : date
            The start date of the date range.
        date_to : date
            The end date of the date range.

        Returns
        -------
        list
            A list of dictionaries with the data of the employees that have salary changes on the
            given date range.
        """
        salary_changes_data = self.env["hr.employee.salary.change"].search(
            [
                ("date", ">=", date_from),
                ("date", "<=", date_to),
            ]
        )
        decimal_separator = (
            self.env["ir.config_parameter"].sudo().get_param("separador_decimales_ivss")
        )
        employees_data = []
        for salary_change in salary_changes_data:
            employee = salary_change.employee_id
            if decimal_separator == ".":
                weekly_wage = float_repr((salary_change.previous_wage / 4), 2)
                new_weekly_wage = float_repr((salary_change.wage / 4), 2)
            else:
                weekly_wage = float_repr((salary_change.previous_wage / 4), 2).replace(
                    ".", decimal_separator
                )
                new_weekly_wage = float_repr((salary_change.wage / 4), 2).replace(
                    ".", decimal_separator
                )

            employee_data = {
                "prefix_vat": employee.prefix_vat,
                "vat": employee.vat,
                "name": f"{employee.lastname} {employee.name}",
                "weekly_wage": weekly_wage,
                "new_weekly_wage": new_weekly_wage,
                "date": salary_change.date.strftime("%d/%m/%Y"),
            }
            employees_data.append(employee_data)
        return employees_data
