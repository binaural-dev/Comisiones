from odoo.fields import (
    Char,
    Datetime,
    Selection,
    Many2many,
    One2many
)
from odoo.api import (
    model,
    depends
)
from odoo.models import Model

class CommissionPolicyImage(Model):
    _name = "commission.policy.image"
    _description = "A backup image of the moment when a commission is requested or modified."
    _order = "create_date desc"

    name = Char(
        "Name",
        required=True
    )
    
    budget_ids = Many2many(
        'sale.order',
        'commission_images_id',
        string = "budgets"
    )
    
    date_created = Datetime(
        "Creation date",
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
        string="Commission Type",
        required=True,
    )
    
    product_commission_type = Selection(
        selection=[
            ("product", "Product"),
            ("category", "Category"),
            ("brand", "Brand")
        ],
        string="Aplicar A",
    )
    
    clients_id = Many2many(
        "res.partner",
        "commission_policy_image_client_rel",
        string="Clients VIP"
    )
    
    products_id = Many2many(
        "product.product",
        "commission_policy_image_product_rel",
        string="Products"
    )
    
    brands_id = Many2many(
        "product.brand",
        "commission_policy_image_brand_rel",
        string="Brands"
    )
    
    categories_id = Many2many(
        "product.category",
        "commission_policy_image_category_rel",
        string="Categories"
    )
    
    commission_line_ids = One2many(
        "commission.policy.image.line",
        "policy_image_id",
        string="Commission Range"
    )
    
    product_ids = One2many(
        "product.product",
        "commission_policy_image_id",
        readonly=False,
        compute="_compute_products_based_on_brand_or_category"
    )
     

    @depends("policy_type", "name")
    def _compute_display_name(self):
        policy_type_dict = {
            "client": "Client",
            "product": "Product",
            "all": "General"
        }
        
        for commission_i in self:
            commission_i.display_name = (
                f"{policy_type_dict.get(commission_i.policy_type)} ({commission_i.name})"
            )

    @model
    def get_image_commission(self, policy_type: str, product_policy_type=None):
        """
        Method to get the last image of a commission policy.
        :param policy_type: The type of commission policy.
        :param product_policy_type: The type of product policy.
        :return: recordset of the last image of a commission policy found in given types.
        """
        commission_policy = None
        if product_policy_type:
            commission_policy = self.env["commission.policy.image"].search(
                [
                    ("policy_type", "=", policy_type),
                    ("product_commission_type", "=", product_policy_type),
                ],
            )
        else:
            commission_policy = self.env["commission.policy.image"].search(
                [("policy_type", "=", policy_type)]
            )

        return commission_policy

        
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
        

    @model
    def get_commission_product_ids(self, policy_type: str, product_policy_types=None):
        if not product_policy_types:
            product_policy_types = []

        commission_product_ids = set()
        for product_policy_type in product_policy_types:
            commissions = self.env['commission.policy'].get_commission(policy_type, product_policy_type)
            for commission in commissions:
                if product_policy_type == "product":
                    commission_product_ids.update(commission.products_id.ids)
                else:
                    commission_product_ids.update(commission.product_ids.ids)

        return list(commission_product_ids)
    
    @model
    def is_commission_in_type(self, o_commission):
        for commission_i in self:
            if commission_i.compare_commission_image(o_commission):
                return commission_i

        return False

    @model
    def compare_commission_image(self, o_commission) -> bool:
        """
        Compare the current commission image with its original commission.

        :param o_commission: commission to compare with current image
        :return True if the commissions are the same, False otherwise.
        """

        attr_equally_list = []

        if self.products_id:
            attr_equally_list.append(self.products_id.ids == o_commission.products_id.ids)
            
        if self.brands_id:
            attr_equally_list.append(self.brands_id.ids == o_commission.brands_id.ids)
            
        if self.categories_id:
            attr_equally_list.append(self.categories_id.ids == o_commission.categories_id.ids)
            
        if self.clients_id:
            attr_equally_list.append(self.clients_id.ids == o_commission.clients_id.ids)
            
        if self.product_ids:
            attr_equally_list.append(self.product_ids.ids == o_commission.product_ids.ids)

        for policy_line, i_policy_line in zip(
            self.commission_line_ids, o_commission.commission_line_ids
        ):
            attr_equally_list.append(
                policy_line.date_from == i_policy_line.date_from
                and policy_line.date_until == i_policy_line.date_until
                and policy_line.commission == i_policy_line.commission
            )

        return all(attr_equally_list)
