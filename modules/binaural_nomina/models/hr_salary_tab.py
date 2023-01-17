from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tests.common import Form


class HrSalaryTab(models.Model):
    _name = "hr.salary.tab"
    _inherit = ["mail.thread"]
    _description = "Tabulador Salarial"

    name = fields.Char(string="Nombre", related="job_id.name")
    active = fields.Boolean(default=True)
    state = fields.Selection(
        [
            ("active", "Vigente"),
            ("inactive", "Inactivo"),
        ],
        string="Estatus",
        compute="_compute_state",
    )
    date_from = fields.Date(string="Vigente desde", required=True, tracking=True)
    job_id = fields.Many2one(
        "hr.job", string="Puesto de trabajo", required=True, tracking=True
    )
    wage_type = fields.Selection(
        selection=[("monthly", "Salario Fijo Mensual"), ("hourly", "Salario por Hora")],
        string="Tipo de salario",
        required=True,
        tracking=True,
    )
    wage = fields.Float(string="Salario Mensual", required=True, tracking=True)
    hourly_wage = fields.Float(string="Salario por Hora", tracking=True)

    def action_update(self):
        for tab in self:
            if not tab.active:
                raise UserError(
                    _("No se pueden actualizar los salarios desde un tabulador inactivo.")
                )
            contracts = self.env["hr.contract"].search(
                [
                    ("job_id", "=", tab.job_id.id),
                    ("state", "=", "open"),
                ]
            )
            structure_types = contracts.mapped("structure_type_id")
            for structure_type in structure_types:
                with Form(structure_type) as structure_type_form:
                    structure_type_form.wage_type = tab.wage_type
            for contract in contracts:
                with Form(contract) as contract_form:
                    if tab.wage_type == "monthly":
                        contract_form.wage = tab.wage
                    if tab.wage_type == "hourly":
                        contract_form.hourly_wage = tab.hourly_wage
            tab.message_post(body=_("Salarios Actualizados."))

    @api.depends("active")
    def _compute_state(self):
        for tab in self:
            tab.state = "active" if tab.active else "inactive"
