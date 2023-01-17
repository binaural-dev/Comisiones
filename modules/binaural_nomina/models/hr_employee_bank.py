from odoo import fields, models, api,_


class HrEmployeeBank(models.Model):
    _name = "hr.employee.bank"
    _description = "Información bancaria de un empleado"

    name = fields.Char(string="Número de Cuenta", required=True)
    employee_id = fields.Many2one("hr.employee", string="Empleado")
    bank_name = fields.Many2one('res.bank', string="Banco")
    account_type = fields.Selection(
        selection=[("checking", "Corriente"), ("saving", "Ahorro")],
        string="Tipo de cuenta")
    details = fields.Text(string="Observaciones")

    account_holder_name = fields.Char(string="Titular de la cuenta", required=True , compute="_compute_account_holder_name", store=True, readonly=False)
    type_doc = fields.Selection(
        selection=[("V", "V"), ("E", "E"), ("J", "J"), ("G", "G"), ("C", "C")],
        string="Tipo de documento", compute="_compute_type_doc",required=True,readonly=False, store=True)
    number_doc = fields.Char(string="Número de documento", compute="_compute_number_doc",required=True, readonly=False , store=True)

    @api.depends("employee_id")
    def _compute_number_doc(self):
        for record in self:
            record.number_doc = record.employee_id.vat

    @api.depends("employee_id")
    def _compute_account_holder_name(self):
        for record in self:
            record.account_holder_name = record.employee_id.name

    @api.depends("employee_id")
    def _compute_type_doc(self):
        for record in self:
            record.type_doc = record.employee_id.prefix_vat
