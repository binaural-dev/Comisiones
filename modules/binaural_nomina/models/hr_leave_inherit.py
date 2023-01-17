from collections import defaultdict
from typing import List
import pandas

from odoo import api, models, _
from odoo.addons.hr_payroll.models.browsable_object import BrowsableObject
from odoo.exceptions import UserError


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _get_number_of_days(self, date_from, date_to, employee_id):
        """
        Ensure that if the leave type is a vacation leave type and the holiday type is per employee
        and if the employee has free days on the date range, those days are not taked
        into account when calculating the number of days of the leave.
        """
        work_entry_vacation_id = self.env.ref("binaural_nomina.hr_work_entry_binaural_vacation").id
        is_not_vacation_or_holiday_type_is_not_employee = (
            self.holiday_status_id.work_entry_type_id.id != work_entry_vacation_id
            or self.holiday_type != "employee"
        )
        if is_not_vacation_or_holiday_type_is_not_employee:
            return super()._get_number_of_days(date_from, date_to, employee_id)
        days_count = 0
        date_range = pandas.date_range(date_from, date_to, freq="D").to_pydatetime().tolist()
        for date in date_range:
            if date.weekday() > 4:
                continue

            entries = self._get_employee_work_entry_ids(
                date.replace(hour=0), date.replace(hour=23), employee_id, "in"
            )
            if any(entries):
                continue

            days_count += 1

        return {"days": days_count, "hours": 0}

    def action_confirm(self):
        for holiday in self:
            holiday._vacation_entry_type_validation()
        return super().action_confirm()

    def action_validate(self):
        """
        Ensure that when the leave has a holiday_type of category, company or department the dates
        that are used to calculate the leaves created by that are full days.
        """
        leaves = self.filtered(
            lambda request: request.holiday_type != "employee"
        )
        for leave in leaves:
            leave.date_from = leave.date_from.replace(hour=0, minute=0, second=0)
            leave.date_to = leave.date_to.replace(hour=23, minute=59, second=59)
        return super().action_validate()

    def _cancel_work_entry_conflict(self):
        """
        First of all making sure that the entries are created taking into account the holiday_type,
        which does not happen on the original method (it taked into account just the case of the
        'employee' holiday_type).
        Also ensuring that the work entries of holidays and break days are generated for the
        approved leave, instead of just creating entries of the basic work entry type that the leave
        type has.

        Normally when the leave is approved, it overrides all the entry types that are in the date
        range of the leave, creating entries of just one type. Here, we let the normal flow of this
        action happen for the basic entries that the employee has, and then we create the work
        entries of the leave type's holiday and break day (This fields were created in this module
        """
        if not self:
            return
        # We need the recordset of employees so even if the holiday_type is not employee the work
        # entries are created.
        employees = self.env["hr.employee"]
        entries_to_replace = []

        # 1. Create a work entry for each leave
        work_entries_vals_list = []
        for leave in self:
            # Checking which holiday type the leave is for adding the employees to the list.
            if leave.holiday_type == "category":
                leave_employees = leave.category_id.employee_ids
            elif leave.holiday_type == "company":
                leave_employees = self.env["hr.employee"].search(
                    [("company_id", "=", leave.mode_company_id.id)]
                )
            elif leave.holiday_type == "employee":
                leave_employees = leave.employee_id
            else:
                leave_employees = leave.department_id.member_ids

            for employee in leave_employees:
                contracts = employee.sudo()._get_contracts(
                    leave.date_from, leave.date_to, states=["open", "close"]
                )
                for contract in contracts:
                    # Generate only if it has aleady been generated
                    if (
                        leave.date_to >= contract.date_generated_from
                        and leave.date_from <= contract.date_generated_to
                    ):
                        work_entries_vals_list += contracts._get_work_entries_values(
                            leave.date_from.replace(hour=0, minute=0, second=0),
                            leave.date_to.replace(hour=23, minute=59, second=59),
                        )

                # Getting the work entries of holidays and break days that are in the date range of
                # the leave.
                entries_to_replace.append(self._get_entries_to_replace(leave, employee))

            # Adding the employees of the current leave to the list so we can use it later.
            employees |= leave_employees

        new_leave_work_entries = self.env["hr.work.entry"].create(work_entries_vals_list)

        if new_leave_work_entries:
            # 2. Fetch overlapping work entries, grouped bodoo when leaves are groupals it does not
            # change the wkir entry of the employeey employees
            start = min(self.mapped("date_from"), default=False)
            stop = max(self.mapped("date_to"), default=False)
            work_entry_groups = self.env["hr.work.entry"].read_group(
                [
                    ("date_start", "<", stop),
                    ("date_stop", ">", start),
                    ("employee_id", "in", employees.ids),
                ],
                ["work_entry_ids:array_agg(id)", "employee_id"],
                ["employee_id", "date_start", "date_stop"],
                lazy=False,
            )
            work_entries_by_employee = defaultdict(lambda: self.env["hr.work.entry"])
            for group in work_entry_groups:
                employee_id = group.get("employee_id")[0]
                work_entries_by_employee[employee_id] |= self.env["hr.work.entry"].browse(
                    group.get("work_entry_ids")
                )

            # 3. Archive work entries included in leaves
            included = self.env["hr.work.entry"]
            overlappping = self.env["hr.work.entry"]
            for work_entries in work_entries_by_employee.values():
                # Work entries for this employee
                new_employee_work_entries = work_entries & new_leave_work_entries
                previous_employee_work_entries = work_entries - new_leave_work_entries

                # Build intervals from work entries
                leave_intervals = new_employee_work_entries._to_intervals()
                conflicts_intervals = previous_employee_work_entries._to_intervals()

                # Compute intervals completely outside any leave
                # Intervals are outside, but associated records are overlapping.
                outside_intervals = conflicts_intervals - leave_intervals

                overlappping |= self.env["hr.work.entry"]._from_intervals(outside_intervals)
                included |= previous_employee_work_entries - overlappping
            overlappping.write({"leave_id": False})
            included.write({"active": False})

        # Replacing the work entries of the holidays and break days with the ones that are on the
        # leave type
        self._replace_break_days_and_holidays_entries(entries_to_replace)

    @api.model
    def _get_entries_to_replace(self, leave, employee) -> BrowsableObject:
        """
        Creates a list of work entries to replace for the employees of each leave that is gonna be
        generated from the current one.

        This allows us to get the work entries of the holidays and break days before the creation of
        the entries of the leaves, so we can later replace them with the entries specified to be in
        that place, instead of the basic work entry of the leave type.

        Returns
        -------
        BrowsableObject
            The data with the employee and the work entries that are gonna be replaced.
        """
        entry_type_holiday = self.env.ref("binaural_nomina.hr_work_entry_binaural_holiday").id
        entry_type_holiday_not_worked = self.env.ref(
            "binaural_nomina.hr_work_entry_binaural_holiday_not_worked"
        ).id
        entry_type_break_day = self.env.ref("binaural_nomina.hr_work_entry_binaural_break_day").id
        entry_type_break_day_not_worked = self.env.ref(
            "binaural_nomina.hr_work_entry_binaural_weekend"
        ).id

        leave_type = leave.holiday_status_id
        entry_types_to_replace = {
            entry_type_holiday: leave_type.holiday_work_entry_type_id.id,
            entry_type_holiday_not_worked: leave_type.holiday_work_entry_type_id.id,
            entry_type_break_day: leave_type.break_day_work_entry_type_id.id,
            entry_type_break_day_not_worked: leave_type.break_day_work_entry_type_id.id,
        }
        work_entry_ids = leave._get_employee_work_entry_ids(
            leave.date_from, leave.date_to, employee.id, "in"
        )
        holiday_data = {
            "leave_id": leave.id,
            "leave_type": leave_type,
            "entry_types_to_replace": entry_types_to_replace,
            "work_entry_ids": work_entry_ids,
        }
        return BrowsableObject(employee.id, holiday_data, None)

    @api.model
    def _replace_break_days_and_holidays_entries(self, entries_data: List[BrowsableObject]):
        """
        Replaces the work entries of the holidays and break days with the work entries specified in
        the leave type of the leave.

        Parameters
        ----------
        entries_data : List[BrowsableObject]
            The data with the employee and the work entries that are gonna be replaced.
        """
        for holiday in entries_data:
            if not bool(holiday.work_entry_ids):
                continue
            for entry in holiday.work_entry_ids:
                work_entry_type_id = entry.work_entry_type_id
                entry_to_deactivate = self.env["hr.work.entry"].search(
                    [
                        ("employee_id", "=", entry.employee_id.id),
                        ("date_start", "=", entry.date_start),
                        ("date_stop", "=", entry.date_stop),
                        ("id", "!=", entry.id),
                    ]
                )
                new_entry_type_id = self.env["hr.work.entry.type"].search(
                    [
                        ("id", "=", holiday.entry_types_to_replace[work_entry_type_id.id]),
                    ]
                )
                entry_to_deactivate.active = False
                entry.write(
                    {
                        "name": f"{new_entry_type_id.name}: {entry.employee_id.name}",
                        "active": True,
                        "work_entry_type_id": new_entry_type_id.id,
                        "leave_id": holiday.leave_id,
                    }
                )

    def _vacation_entry_type_validation(self):
        self.ensure_one()
        work_entry_vacation_id = self.env.ref("binaural_nomina.hr_work_entry_binaural_vacation").id
        leave_type = self.holiday_status_id
        leave_type_has_holiday_and_break_day_entry_type = (
            leave_type.holiday_work_entry_type_id and leave_type.break_day_work_entry_type_id
        )
        if (
            leave_type.work_entry_type_id.id == work_entry_vacation_id
            and not leave_type_has_holiday_and_break_day_entry_type
        ):
            raise UserError(
                _("Vacation leave type must have a holiday and a break day work entry type.")
            )

    def action_refuse(self):
        """
        Deleting the work entries that the leave type generated an then regenerating the ones that
        should be there based on the contract of the employee.

        The work entries of the leave type are generated when the leave is approved, so when we
        cancel the leave, we need to delete those entries and then regenerate the ones that should
        be there based on the contract of the employee.
        """
        res = super().action_refuse()
        for holiday in self:
            leave_type_work_entries = [
                holiday.holiday_status_id.work_entry_type_id.id,
            ]
            if holiday.holiday_status_id.holiday_work_entry_type_id:
                leave_type_work_entries.append(
                    holiday.holiday_status_id.holiday_work_entry_type_id.id
                )
            if holiday.holiday_status_id.break_day_work_entry_type_id:
                leave_type_work_entries.append(
                    holiday.holiday_status_id.break_day_work_entry_type_id.id
                )

            work_entry_ids = holiday._get_employee_work_entry_ids(
                holiday.date_from,
                holiday.date_to,
                holiday.employee_id.id,
                "in",
                leave_type_work_entries,
            )
            work_entry_ids.unlink()

            holiday.employee_id.with_context(
                force_work_entry_generation=True
            ).generate_work_entries(holiday.date_from, holiday.date_to)
        return res

    @api.model
    @api.returns("hr.work.entry")
    def _get_employee_work_entry_ids(
        self,
        date_from,
        date_to,
        employee_id,
        entry_type_operator="not in",
        entry_type_ids=[],
    ):
        """
        Searchs for the work entries that meets the requirements that are passed as parameters.

        Parameters
        ----------
        date_from : datetime
            The start date of the range in which ther work entries will be searched for.
        date_to : datetime
            The end date of the range in which ther work entries will be searched for.
        employee_id : int
            The id of the employee for whom the work entries will be searched for.
        entry_type_operator : str, optional
            The operator that will be used to search for the work entries, by default "not in".
        entry_type_ids : list, optional
            The list of work entry types that will be used to search for the work entries, by
            default []. If it is not provided, the types that are gonna be searched will be the
            default for holidays, break days and weekends.

        Returns
        -------
        Recordset of hr.work.entry
            The work entries that meets the requirements that are passed as parameters.
        """
        if not any(entry_type_ids):
            entry_type_ids = self._get_entry_type_not_to_count_ids()

        date_range = (
            pandas.date_range(date_from, date_to.replace(hour=23), freq="1h")
            .to_pydatetime()
            .tolist()
        )
        employee_work_entry_ids = self.env["hr.work.entry"].search(
            [
                ("employee_id", "=", employee_id),
                ("date_start", "in", date_range),
                ("date_stop", "in", date_range),
                ("work_entry_type_id", entry_type_operator, entry_type_ids),
            ]
        )
        return employee_work_entry_ids

    @api.model
    def _get_entry_type_not_to_count_ids(self) -> list:
        """
        Returns a list with the ids of the holiday, weekend and break day work entry types.
        """
        entry_type_not_to_count_ids = [
            self.env.ref("binaural_nomina.hr_work_entry_binaural_holiday").id,
            self.env.ref("binaural_nomina.hr_work_entry_binaural_holiday_not_worked").id,
            self.env.ref("binaural_nomina.hr_work_entry_binaural_weekend").id,
            self.env.ref("binaural_nomina.hr_work_entry_binaural_break_day").id,
        ]
        return entry_type_not_to_count_ids
