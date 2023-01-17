# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettingBinauralContactos(models.TransientModel):
    _inherit = 'res.config.settings'

    use_retention = fields.Boolean(string="Uses retentions",
    related='company_id.use_retention', readonly=False)

    account_retention_iva = fields.Many2one(
        'account.account', 'IVA Retention Account',
        related='company_id.account_retention_iva', readonly=False
    )
    account_retention_islr = fields.Many2one(
        'account.account', 'ISLR Retention account',
        related='company_id.account_retention_islr', readonly=False
    )

    account_retention_receivable_client = fields.Many2one(
        'account.account', 'Cuenta P/cobrar clientes')
    account_retention_to_pay_supplier = fields.Many2one(
        'account.account', 'Cuenta P/pagar proveedor')

    journal_retention_client = fields.Many2one(
        'account.journal', 'Customer Retentions Journal',
        related='company_id.journal_retention_client', readonly=False
    )
    journal_retention_supplier = fields.Many2one(
        'account.journal', 'Provider Retentions Journal',
        related='company_id.journal_retention_supplier', readonly=False
    )

    qty_max = fields.Integer(string='Cantidad Máxima',
                             required=True, default=25)

    journal_contingence_ids = fields.Many2one(
        'account.journal', 'Diario de Factura de Contingencia')
    curreny_foreign_id = fields.Many2one('res.currency', 'Moneda Alterna')

    use_municipal_retention = fields.Boolean(
        "Uso de Retenciones Municipales", implied_group='binaural_contactos_configuraciones.use_municipal_retention', default=False)

    account_municipal_retention = fields.Many2one(
        'account.account', 'Cuenta de Retenciones Municipales Proveedores')
    journal_municipal_retention = fields.Many2one(
        'account.journal', 'Diario de Retenciones Municipales Proveedores')
    account_municipal_retention_clients = fields.Many2one(
        'account.account', 'Cuenta de Retenciones Municipales Clientes')
    journal_municipal_retention_clients = fields.Many2one(
        'account.journal', 'Diario de Retenciones Municipales Clientes')

    @api.model
    def get_values(self):
        res = super(ResConfigSettingBinauralContactos, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            use_municipal_retention=params.get_param(
                'use_municipal_retention'),
            account_retention_receivable_client=int(
                params.get_param('account_retention_receivable_client')),
            account_retention_to_pay_supplier=int(
                params.get_param('account_retention_to_pay_supplier')),
            account_municipal_retention=int(
                params.get_param('account_municipal_retention')),
            qty_max=int(params.get_param('qty_max')),
            curreny_foreign_id=int(params.get_param('curreny_foreign_id')),
            journal_municipal_retention=int(
                params.get_param('journal_municipal_retention')),
            account_municipal_retention_clients=int(
                params.get_param('account_municipal_retention_clients')),
            journal_municipal_retention_clients=int(
                params.get_param('journal_municipal_retention_clients')),
        )
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'use_municipal_retention', self.use_municipal_retention)
        self.env['ir.config_parameter'].sudo().set_param(
            'account_retention_receivable_client', self.account_retention_receivable_client.id)
        self.env['ir.config_parameter'].sudo().set_param(
            'account_retention_to_pay_supplier', self.account_retention_to_pay_supplier.id)
        self.env['ir.config_parameter'].sudo().set_param(
            'account_municipal_retention', self.account_municipal_retention.id)
        self.env['ir.config_parameter'].sudo(
        ).set_param('qty_max', self.qty_max)
        self.env['ir.config_parameter'].sudo().set_param(
            'curreny_foreign_id', self.curreny_foreign_id.id)
        self.env['ir.config_parameter'].sudo().set_param(
            'journal_municipal_retention', self.journal_municipal_retention.id)
        self.env['ir.config_parameter'].sudo().set_param(
            'journal_municipal_retention_clients', self.journal_municipal_retention_clients.id)
        self.env['ir.config_parameter'].sudo().set_param(
            'account_municipal_retention_clients', self.account_municipal_retention_clients.id)
        super(ResConfigSettingBinauralContactos, self).set_values()
