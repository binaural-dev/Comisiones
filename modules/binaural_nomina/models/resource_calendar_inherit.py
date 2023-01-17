from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class BinauralResourceCalendarInherit(models.Model):
    _inherit = 'resource.calendar.attendance'
    _description = 'Herencia para agregar opciones al calendario odoo'

    day_period = fields.Selection(selection_add=[('night','Noche'),('early_morning','Madrugada')], 
        ondelete={'night':'set default', 'early_morning':'set default'})