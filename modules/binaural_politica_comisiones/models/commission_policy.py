from odoo import _
from odoo.models import Model
from odoo.exceptions import ValidationError
from odoo.fields import (
    Char,
    Date,
    Many2many,
    One2many,
    Selection,
)
from odoo.api import (
    model,
    depends,
    onchange,
    constrains
)

import logging

_logger = logging.getLogger(__name__)

class ComissionPolicy(Model):
    _name = "commission.policy"
    _description = "commission policy for sellers"
    
    @model
    def _get_products_domain(self):
        commission_product_ids = self.get_commission_product_ids("product", ["category","brand"])
        return [("id", "not in", commission_product_ids)]
    
    name = Char(
        "Name",
        required=True
    )
    
    display_name = Char(
        compute="_compute_display_name",
        store=True
    )
    
    policy_type = Selection(
        selection=[
            ("client", "Cliente"),
            ("product", "Producto"),
            ("all", "General")
        ],
        string="Commission type",
        required=True,
    )
    
    product_commission_type = Selection(
        selection=[
            ("product", "Product"),
            ("category", "Category"),
            ("brand", "Brand")
        ],
        string="Apply to",
    )
    
    clients_id = Many2many(
        "res.partner",
        "commission_policy_client_rel",
        string="Clients VIP"
    )
    
    products_id = Many2many(
        "product.product",
        "commission_policy_product_rel",
        string="Products",
        domain=_get_products_domain,
    )
    
    commission_line_ids = One2many(
        "commission.policy.line",
        "policy_id",
        string="Commissions range"
    )
    
    brands_id = Many2many(
        "product.brand",
        "commission_policy_brand_rel",
        string="Brands"
    )
    
    categories_id = Many2many(
        "product.category",
        "commission_policy_category_rel",
        string="Categories"
    )
    
    product_ids = One2many(
        "product.product",
        "commission_policy_id",
        compute="_compute_products_based_on_brand_or_category",
        readonly=False,
    )
    
    @depends("policy_type", "name")
    def _compute_display_name(self):
        policy_type_dict = {
            "client": "Cliente",
            "product": "Producto",
            "all": "General"
        }
      
        for commission in self:
            commission.display_name = (
                f"{policy_type_dict.get(commission.policy_type)} ({commission.name})"
            )

    @depends("product_commission_type","categories_id","brands_id")
    def _compute_products_based_on_brand_or_category(self):
        Product = self.env["product.product"]

        for commission in self:
            if commission.brands_id or commission.categories_id:
                
                products_commission_type = {
                    "category": Product.search(
                        [
                            ("categ_id", "in", commission.categories_id.ids),
                            (
                                "id",
                                "not in",
                                self.get_commission_product_ids("product", ["product", "brand"]),
                            ),
                        ]
                    ),
                    "brand": Product.search(
                        [
                            ("brand_id", "in", commission.brands_id.ids),
                            (
                                "id",
                                "not in",
                                self.get_commission_product_ids("product", ["product", "category"]),
                            ),
                        ]
                    ),
                }
                
                commission.product_ids = products_commission_type.get(
                    commission.product_commission_type
                ).ids
                
                

    @constrains("commission_line_ids")
    def _check_previous_range_date_until(self):
        for commission in self:
            if len(commission.commission_line_ids) > 1:
                commission_lines_list = sorted(
                    commission.commission_line_ids, key=lambda x: x.date_from
                )
                
                if commission_lines_list[-1].date_from <= commission_lines_list[-2].date_until:
                    raise ValidationError(
                        _(
                            "The start date for the commission must not be less than "
                            + "or equal to the end date of the previous commission."
                        )
                    )
                       

    @onchange("policy_type")
    def _onchange_product_policy_type(self):
        if self.policy_type != "product":
            self.product_commission_type = False

    @onchange("product_commission_type")
    def _onchange_product_commission_type(self):
        for commission in self:
            if commission.product_commission_type == "product":
                commission.brands_id = False
                commission.categories_id = False
          
            if commission.product_commission_type == "category":
                commission.products_id = False
                commission.brands_id = False
          
            if commission.product_commission_type == "brand":
                commission.products_id = False
                commission.categories_id = False

    @model
    def get_commission_product_ids(self, policy_type: str, product_policy_types=None):
        if not product_policy_types:
            product_policy_types = []

        commission_product_ids = set()
        for product_policy_type in product_policy_types:
            commissions = self.get_commission(policy_type, product_policy_type)
            for commission in commissions:
                if product_policy_type == "product":
                    commission_product_ids.update(commission.products_id.ids)
                else:
                    commission_product_ids.update(commission.product_ids.ids)
        return list(commission_product_ids)

    @model
    def get_commission(self, policy_type: str, product_policy_type=None):
        """
        Method to get the commission policy wich will be applied to a given product
        :param policy_type: The type of commission policy.
        :param product_policy_type: The type of product policy.
        :return: recordset of  a commission policy found in given types.
        """
        if not product_policy_type:            
            return self.env["commission.policy"].search(
                [("policy_type", "=", policy_type)]
            )   
        return self.env["commission.policy"].search(
                [
                    ("policy_type", "=", policy_type),
                    ("product_commission_type", "=", product_policy_type),
                ],
            )

        

    @model
    def get_or_create_commission_image(
        self,
        budget_ids,
        policy_type,
        product_commission_type=None,
        commission=None
    ):
        """
        Method to create a commission image if the current commission policy has
        been modified or to get the image with the picking reference to link which
        commission will be applied.
        :param picking_ids: The pickings which will be set in the commission image.
        :param policy_type: The type of commission policy.
        :param product_commission_type: The type of product policy.
        :return: a recordset with a new commission image or the current one.
        """
        commission_image = self.env["commission.policy.image"]

        commission_i = commission_image.get_image_commission(policy_type, product_commission_type)
        same_commission = False            

        if commission_i:
            same_commission = commission_i.is_commission_in_type(self)
        
        if not same_commission:
            
            new_commission_i = [
                {
                    "name": commission.name,
                    "policy_type": commission.policy_type,
                    "date_created": Date.context_today(self),
                    "product_commission_type": commission.product_commission_type,
                    "budget_ids": [(6, 0, budget_ids.ids)],
                    "clients_id": [(6, 0, commission.clients_id.ids)] if commission.clients_id else False,
                    "products_id": [(6, 0, commission.products_id.ids)] if commission.products_id else False,
                    "categories_id": [(6, 0, commission.categories_id.ids)] if commission.categories_id else False,
                    "brands_id": [(6, 0, commission.brands_id.ids)] if commission.brands_id else False,
                    "product_ids": [(6, 0, commission.product_ids.ids)] if commission.product_ids else False,
                    "commission_line_ids": [],
                }
            ]            
            
            for policy_line in self.commission_line_ids:
                new_commission_i[0]["commission_line_ids"].append(
                    (
                        0,
                        0,
                        {
                            "date_from": policy_line.date_from,
                            "date_until": policy_line.date_until,
                            "commission": policy_line.commission,
                        },
                    )
                )
            
            new_commission_image = commission_image.create(new_commission_i)
            return new_commission_image
        
        if len(budget_ids) + len(same_commission.budget_ids) > 0:
            
            budgets = budget_ids + same_commission.budget_ids
            same_commission.write({"budget_ids": [(6, 0, budgets.ids)]})
            return same_commission

