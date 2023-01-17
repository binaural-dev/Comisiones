from odoo import api, fields, models

class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    holiday_work_entry_type_id = fields.Many2one(
        "hr.work.entry.type", string="Tipo de entrada de trabajo para feriados")
    break_day_work_entry_type_id = fields.Many2one(
        "hr.work.entry.type", string="Tipo de entrada de trabajo para días de descanso")
