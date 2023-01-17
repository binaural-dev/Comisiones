from odoo import models, fields, api

class BinauralPaymentMethods(models.Model):
    _name = "hr.payslip.payment.methods"
    _description = "Payment Methods"

    name = fields.Char(related="bank_id.name", string="bank name")
    bank_id = fields.Many2one("res.bank", string="Banco")
    date_from = fields.Date(string="Fecha de Inicio")
    date_to = fields.Date(string="Fecha de Fin")
    total = fields.Float(string="Total", compute="_compute_total")

    payslip_ids = fields.Many2many(
        "hr.payslip", string="recibos de nomina", compute="_compute_payslip_ids", store=True
    )

    @api.depends("date_from", "date_to", "bank_id")
    def _compute_payslip_ids(self):
        self.payslip_ids = []
        for record in self:
            payslip_ids = self.env["hr.payslip"].search(
                [
                    ("date_from", ">=", record.date_from),
                    ("date_to", "<=", record.date_to),
                    ("struct_category", "!=", "provision"),
                    ("bank_employee_id", "=", record.bank_id.id),
                    ("state", "=", "done"),
                ]
            )

            record.payslip_ids = payslip_ids

    @api.depends("payslip_ids", "date_from", "date_to")
    def _compute_total(self):
        for record in self:
            total = 0
            for payslip in record.payslip_ids:
                total += payslip.net_wage
            record.total = total
