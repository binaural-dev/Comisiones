from odoo.models import Model
from odoo.fields import Float
from odoo.api import depends, model


class AccountMoveLine(Model):
  
    _inherit = 'account.move.line'
    
    commission = Float(
        store=True,
        compute="_compute_commission"
    )
    
    @depends("move_id.collection_days")
    def _compute_commission(self):
        for line in self:
            product = line.product_id
            move = line.move_id
            partner = move.partner_id

            policies = self.env["commission.policy"].search([])
            
            commission_policy_client = policies.filtered(
                lambda c: c.policy_type == "client" 
                and partner.id in c.clients_id.ids
            )
            
            commission_policy_all = policies.filtered(
                lambda c: c.policy_type == "all"
            )
            
            commission_policy_product_product = policies.filtered(
                lambda c: c.policy_type == "product"
                and c.product_commission_type == "product"
                and product.id in c.products_id.ids
            )
            
            commission_policy_product_brand = policies.filtered(
                lambda c: c.policy_type == "product"
                and c.product_commission_type == "brand"
                and product.id in c.product_ids.ids
            )
            
            commission_policy_product_category = policies.filtered(
                lambda c: c.policy_type == "product"
                and c.product_commission_type == "category"
                and product.id in c.product_ids.ids
            )
            
            commissions = {
                "client": commission_policy_client[0] if len(commission_policy_client) > 0 else commission_policy_client,
                "product": {
                    "product": commission_policy_product_product[0] if len(commission_policy_product_product) > 0 else commission_policy_product_product,
                    "category": commission_policy_product_category[0] if len(commission_policy_product_category) > 0 else commission_policy_product_category,
                    "brand": commission_policy_product_brand[0] if len(commission_policy_product_brand) > 0 else commission_policy_product_brand
                },
                "all": commission_policy_all[0] if len(commission_policy_all) > 0 else commission_policy_all
            }

            if (
                move.move_type == "out_invoice"
                and move.last_payment_date
                and product.type in ["consu","service","product"]
            ):
                if product.id in commissions["product"]["product"].products_id.ids:
                    commission = commissions["product"]["product"].filtered(
                        lambda c: product.id in c.products_id.ids
                    )
                    
                    line.commission = commission.commission_line_ids.filtered(
                        lambda cl: cl.date_from <= move.collection_days <= cl.date_until
                        or (cl.date_from <= move.collection_days and cl.date_until == 0)
                    ).commission
                    continue
                elif product.categ_id.id in commissions["product"]["category"].categories_id.ids:
                    commission = commissions["product"]["category"].filtered(
                        lambda c: product.categ_id.id in c.categories_id.ids
                    )
                    
                    line.commission = commission.commission_line_ids.filtered(
                        lambda cl: cl.date_from <= move.collection_days <= cl.date_until
                        or (cl.date_from <= move.collection_days and cl.date_until == 0)
                    ).commission
                    continue
                elif product.brand_id.id in commissions["product"]["brand"].brands_id.ids:
                    commission = commissions["product"]["brand"].filtered(
                        lambda c: product.brand_id.id in c.brands_id.ids
                    )
                    
                    line.commission = commission.commission_line_ids.filtered(
                        lambda cl: cl.date_from <= move.collection_days <= cl.date_until
                        or (cl.date_from <= move.collection_days and cl.date_until == 0)
                    ).commission
                    continue
                elif partner.id in commissions["client"].clients_id.ids:
                    commission = commissions["client"].filtered(
                        lambda c: partner.id in c.clients_id.ids
                    )
                    
                    line.commission = commission.commission_line_ids.filtered(
                        lambda cl: cl.date_from <= move.collection_days <= cl.date_until
                        or (cl.date_from <= move.collection_days and cl.date_until == 0)
                    ).commission
                    continue
                else:
                    
                    line.commission = (
                        commissions["all"]
                        .commission_line_ids.filtered(
                            lambda cl: cl.date_from <= move.collection_days <= cl.date_until
                            or (cl.date_from <= move.collection_days and cl.date_until == 0)
                        )
                        .commission
                    )
                    continue
            else:
                line.commission = 0.0
