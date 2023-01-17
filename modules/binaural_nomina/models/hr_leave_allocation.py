from odoo import api, fields, models, _


class HrLeaveAllocation(models.Model):
    _inherit = "hr.leave.allocation"

    @api.model
    def create_vacation_allocation_per_employee(self):
        """
        Creates a leave allocation of type vacation for each employee that has one year or more and
        its entry day and month correspond with the current ones with the corresponding number of
        days based on their seniority.
        """
        vacation_leave_type_id = self.env["ir.model.data"].xmlid_to_res_id(
            "binaural_nomina.hr_leave_vacaciones"
        )
        employees = self.env["hr.employee"].search([])
        employees_with_one_year_of_seniority_or_more = employees.filtered(
            employee_has_one_year_or_more_today
        )
        vacation_days_year_1 = int(self.env["ir.config_parameter"].get_param("dia_vacaciones_anno"))
        vacation_days_post_year_1 = int(
            self.env["ir.config_parameter"].get_param("dia_adicional_posterior")
        )
        for employee in employees_with_one_year_of_seniority_or_more:
            vacation_days = vacation_days_year_1 + (
                vacation_days_post_year_1 * (employee._get_seniority_in_years() - 1)
            )
            self.create(
                {
                    "name": _("Vacation Allocation"),
                    "holiday_type": "employee",
                    "employee_id": employee.id,
                    "holiday_status_id": vacation_leave_type_id,
                    "number_of_days": vacation_days,
                }
            )


def employee_has_one_year_or_more_today(employee):
    """
    Check if the employee has one year or more of seniority and the entry day and month are the
    same as the current ones.

    Parameters
    ----------
    employee : hr.employee
        The employee to check.

    Returns
    -------
    bool
        Whether the employee has one year or more of seniority and the entry day and month are the
        same as the current ones.
    """
    today = fields.Date.today()
    this_month = today.month
    this_day = today.day
    return (
        employee._get_seniority_in_years() >= 1
        and employee.entry_date.month == this_month
        and employee.entry_date.day == this_day
    )
