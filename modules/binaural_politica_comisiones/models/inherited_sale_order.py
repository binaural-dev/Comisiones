from odoo.api import (
    model
)
from odoo.fields import (
    Many2many,
    Datetime
)
from datetime import timedelta
from odoo.models import Model

class SaleOrder(Model):
    _inherit = "sale.order"
    
    commission_images_id = Many2many(
        "commission.policy.image",
        "budget_ids",
        string="Imagenes de comisiones",
    )
    
    @model
    def trigger_create_or_assign_commission_images_for_transfers(self):
        now = Datetime.now()
        start_date = now - timedelta(hours=24)
        end_date = now

        transfers = self.env["sale.order"].search([
            ("create_date", ">=", start_date),
            ("create_date", "<=", end_date),
            ("state", "not in", ["cancel", "draft"]),
            ("commission_images_id", "=", False),
            ("invoice_ids", "=", False)
        ])

        for sale_order in transfers:
            sale_order.generate_commission_image_for_sale_order()
    
    @model
    def generate_commission_image_for_sale_order(self):
        CommissionPolicy = self.env["commission.policy"]
        
        commission_client = CommissionPolicy.get_commission("client")
        commission_product_product = CommissionPolicy.get_commission("product", "product")
        commission_product_category = CommissionPolicy.get_commission("product", "category")
        commission_product_brand = CommissionPolicy.get_commission("product", "brand")
        commission_all = CommissionPolicy.get_commission("all")
        
        client = len(commission_client) - 1 if len(commission_client) > 0 else 0
        product_product = len(commission_product_product) - 1 if len(commission_product_product) > 0 else 0
        product_category = len(commission_product_category) - 1 if len(commission_product_category) > 0 else 0
        product_brand = len(commission_product_brand) - 1 if len(commission_product_brand) > 0 else 0
        all = len(commission_all) - 1 if len(commission_all) > 0 else 0
        
        commissions = {
            "client": commission_client[client],
            "product": {
                "product": commission_product_product[product_product],
                "category": commission_product_category[product_category],
                "brand": commission_product_brand[product_brand],
            },
            "all":commission_all[all],
        }   
        
        for sale_order in self:
            outs = sale_order if sale_order.state == 'sale' else False

            for line in sale_order.order_line:
                    
                if line.product_id.id in commissions["product"]["product"].products_id.ids:
                    commission = commissions["product"]["product"].filtered(
                        lambda c: line.product_id.id in c.products_id.ids
                    )
                    
                    commition = commission.get_or_create_commission_image(outs, "product", "category", commission)
                    sale_order.commission_images_id = commition

                    continue
                
                if line.product_id.categ_id.id in commissions["product"]["category"].categories_id.ids:
                    
                    commission = []
                    
                    for commit in commissions["product"]["category"].categories_id.ids:
                        index = 0
                        if line.product_id.categ_id.id == commit:
                            commission = commissions['product']['category'][index]
                            break
                        index += 1
                    
                    commition = commission.get_or_create_commission_image(outs, "product", "category", commission)
                    sale_order.commission_images_id = commition

                    continue
                
                if line.product_id.brand_id.id in commissions["product"]["brand"].brands_id.ids:
                    commission = commissions["product"]["brand"].filtered(
                        lambda c: line.product_id.brand_id.id in c.brands_id.ids
                    )
                    
                    commition = commission.get_or_create_commission_image(outs, "product", "category", commission)
                    sale_order.commission_images_id = commition

                    continue
                
                if sale_order.partner_id.id in commissions["client"].clients_id.ids:
                    commission = commissions["client"].filtered(
                        lambda c: sale_order.partner_id.id in c.clients_id.ids
                    )                    
                    
                    commition = commission.get_or_create_commission_image(outs, "product", "category", commission)
                    sale_order.commission_images_id = commition

                    continue
                
                commission = commissions['all']
                
                if len(commission) == 0 or not outs:
                    continue
                
                commition = commission.get_or_create_commission_image(outs, "product", "category", commission)
                sale_order.commission_images_id = commition
    
    
