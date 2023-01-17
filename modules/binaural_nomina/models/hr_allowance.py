from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrAllowance(models.Model):
    _name = "hr.allowance"
    _description = "Complementos salariales"

    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string="Código", required=True)
    state = fields.Selection(
        [("active", "Activo"), ("inactive", "Inactivo")], string="Estado", default="active"
    )
    value = fields.Float(string="Valor", required=True)
    description = fields.Char(string="Descripción", required=True)
    line_ids = fields.One2many("hr.allowance.line", "allowance_id", string="Líneas de complemento")

    _sql_constraints = [
        ("name_unique", "UNIQUE(name)", _("Ya existe un complemento con ese nombre.")),
        ("code_unique", "UNIQUE(code)", _("Ya existe un complemento con ese código.")),
    ]

    def action_deactivate(self):
        for allowance in self:
            lines = self.env["hr.allowance.line"].search(
                [("allowance_id", "=", allowance.id), ("employee_id", "!=", False)]
            )
            if any(lines):
                raise UserError(
                    _("No se puede desactivar este complemento porque está asociado a un empleado")
                )
            allowance.state = "inactive"
            return True

    def action_activate(self):
        for allowance in self:
            allowance.state = "active"
            return True

    def action_update_lines(self):
        for line in self.mapped("line_ids"):
            line.action_update_value()


class HrAllowanceLine(models.Model):
    _name = "hr.allowance.line"
    _description = "Líneas de Complementos salariales"

    employee_id = fields.Many2one("hr.employee", string="Empleado")
    allowance_id = fields.Many2one("hr.allowance", string="Complemento")
    code = fields.Char(string="Código", related="allowance_id.code", store=True)
    value = fields.Float(string="Valor", compute="_compute_value", readonly=False, store=True)
    description = fields.Char(string="Descripción", related="allowance_id.description")

    @api.depends("allowance_id")
    def _compute_value(self):
        for line in self:
            line.action_update_value()

    def action_update_value(self):
        for line in self:
            line.value = line.allowance_id.value
