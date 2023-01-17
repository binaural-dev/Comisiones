import re
import logging
from odoo.tools.float_utils import float_repr
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    entry_occupation_id = fields.Many2one("hr.employee.entry.occupation")
    type = fields.Many2one("hr.employee.type")
    condition = fields.Selection(
        [("N", "Normal"), ("P", "Pensioner"), ("J", "Retired")], default="N"
    )
    motor_skill = fields.Selection([("S", "Left Handed"), ("N", "Right Handed")], default="N")

    @api.constrains("private_mobile_phone")
    def _check_private_mobile_phone(self):
        valid_phone = "^(414|424|412|416|426)[0-9]{7}$"
        for employee in self:
            _logger.warning(re.match(valid_phone, employee.private_mobile_phone))
            if not bool(re.match(valid_phone, employee.private_mobile_phone)):
                raise ValidationError(
                    _("The private mobile phone must be in the format 4141234567.")
                )

    @api.constrains("work_email")
    def _check_work_email(self):
        valid_email = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        for employee in self:
            if not bool(re.match(valid_email, employee.work_email)):
                raise ValidationError(
                    _("The work email must be in the format example@example.com.")
                )

    @api.model
    def get_ingresses_data_on_the_given_range(self, date_from, date_to):
        """
        Returns the data of the employees that ingressed on the given date range.

        Parameters
        ----------
        date_from : date
            The start date of the date range.
        date_to : date
            The end date of the date range.

        Returns
        -------
        list
            A list of dictionaries with the data of the employees that ingressed on the
            given date range.

        """
        employees = self.env["hr.employee"].search(
            [
                ("contract_id", "!=", False),
                ("entry_date", "!=", False),
                ("entry_date", ">=", date_from),
                ("entry_date", "<=", date_to),
            ]
        )
        decimal_separator = (
            self.env["ir.config_parameter"].sudo().get_param("separador_decimales_ivss")
        )
        employees_data = []
        for employee in employees:
            if decimal_separator == ".":
                weekly_wage = float_repr((employee.contract_id.wage / 4), 2)
            else:
                weekly_wage = float_repr((employee.contract_id.wage / 4), 2).replace(
                    ".", decimal_separator
                )
            employee_data = {
                "prefix_vat": employee.prefix_vat,
                "vat": employee.vat,
                "name": f"{employee.lastname} {employee.name}",
                "entry_date": employee.entry_date.strftime("%d/%m/%Y"),
                "weekly_wage": weekly_wage,
                "type": employee.type.code,
                "occupation": employee.entry_occupation_id.code,
                "condition": employee.condition,
                "motor_skill": employee.motor_skill,
                "state": employee.state_id.code,
                "municipality": employee.municipality_id.code,
                "parish": employee.parish_id.code,
                "address": f"{employee.street or ''} {employee.street2 or ''}",
                "phone": employee.phone or " ",
                "mobile": employee.private_mobile_phone,
                "email": employee.work_email,
            }
            employees_data.append(employee_data)
        return employees_data
