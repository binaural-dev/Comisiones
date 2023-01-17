import re
from pytz import timezone
from odoo import api, models, _
from odoo.exceptions import UserError


class BinauralHrWorkEntryInherit(models.Model):
    _inherit = "hr.work.entry"

    @api.onchange("work_entry_type_id")
    def _onchange_work_entry_type(self):
        if self.work_entry_type_id.name:
            regexp = re.compile(r"nocturn*")
            if regexp.search(self.work_entry_type_id.name):
                if self.date_start and self.date_stop:
                    date_start = self.date_start.astimezone(timezone(self.env.user.tz))

                    if date_start.hour < 19:
                        raise UserError(
                            _(
                                "Debe usar el tipo de entrada nocturna en un rango comprendido"
                                "entre las 7pm y las 5am"
                            )
                        )
