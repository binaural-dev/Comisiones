from odoo.models import TransientModel
from odoo.fields import (
    Many2one
)
from odoo.api import model


class ResConfigPolicyCommission(TransientModel):
    
    _inherit = 'res.config.settings'
    
    seller_department = Many2one(
        'hr.department',
        'Departamento'
    )
    
    commission_product_id = Many2one(
        'product.product',
        'Producto',
        domain="[('type','=','service')]"
    )
    
    commission_journal_id = Many2one(
        'account.journal',
        'Diario',
        domain="[('type','=','purchase')]"
    )
        
    @model
    def get_values(self):
        res = super().get_values()
        params = self.env['ir.config_parameter'].sudo()
        
        res.update(
            seller_department=int(params.get_param('seller_department')),
            commission_product_id=int(params.get_param('commission_product_id')),
            commission_journal_id=int(params.get_param('commission_journal_id'))
        )
    
        return res
    
    def set_values(self):
        super().set_values()
        params = self.env["ir.config_parameter"].sudo()    
        
        params.set_param('seller_department', self.seller_department.id)
        params.set_param('commission_product_id', self.commission_product_id.id)
        params.set_param('commission_journal_id', self.commission_journal_id.id)