# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions

import logging
_logger = logging.getLogger(__name__)

class BinauralAccountJournalInherit(models.Model):
    _inherit = 'account.journal'

    @api.model
    def load_master_data_journal(self):
        values = {
            'name': 'Sueldos y Salarios',
            'type': 'general'
        }
        result_search = self.search([('code','=','SS')])        
        values['code'] = 'SSAL' if result_search else 'SS'            
        self.create(values)
