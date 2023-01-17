# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResCompany(models.Model):
  _inherit = 'res.company'
  
  use_retention = fields.Boolean(string="Uses retentions", default=False)
  account_retention_iva = fields.Many2one(
    'account.account', 'IVA Retention Account')
  account_retention_islr = fields.Many2one(
    'account.account', 'ISLR Retention account')
  journal_retention_client = fields.Many2one(
    'account.journal', 'Customer Retentions Journal')
  journal_retention_supplier = fields.Many2one(
    'account.journal', 'Provider Retentions Journal')
  
  
  

    
