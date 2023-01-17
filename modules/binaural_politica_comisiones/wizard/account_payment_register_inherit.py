from odoo import models

class AccountPaymentRegisterBinauralComisiones(models.TransientModel):
    _inherit = 'account.payment.register'
    
    def action_create_payments(self):
        if self.payment_difference == 0.0:         
            self.line_ids.move_id.commission_invoice.paid_seller = 'paid'
            
        return super().action_create_payments()