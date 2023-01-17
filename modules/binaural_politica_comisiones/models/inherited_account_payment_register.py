import logging

from odoo import models

_logger = logging.getLogger(__name__)

class AccountPaymentRegisterBinauralComisiones(models.TransientModel):
    _inherit = 'account.payment.register'
    
    def action_create_payments(self):
        super().action_create_payments()

        if self.payment_difference == 0.0:         
            self.line_ids[0].move_id.commission_invoice.paid_seller = 'paid'