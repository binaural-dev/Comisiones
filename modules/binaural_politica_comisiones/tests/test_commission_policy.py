import logging

from odoo.addons.hr_expense.tests.common import TestExpenseCommon
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import Form

_logger = logging.getLogger(__name__)

@tagged('post_install','-at_install')
class TestCommissionPolicy(TestExpenseCommon):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        cls.ProductBrand = cls.env['product.brand']
        cls.CommissionPolicy = cls.env['commission.policy']
        cls.CommissionPolicyLine = cls.env['commission.policy.line']
        
        cls.brand_a = cls.ProductBrand.create({'name': 'Brand A', 'partner_id': cls.partner_a.id})
        cls.brand_b = cls.ProductBrand.create({'name': 'Brand B', 'partner_id': cls.partner_a.id})

        cls.product_a.write({'brand_id': cls.brand_a.id})
        cls.product_b.write({'brand_id': cls.brand_b.id})
        
        cls.vip_clients_commission_policy = cls.CommissionPolicy.create({
            "name": "Test Partner Policy",
            "policy_type": 'client',
            "clients_id": [
                (6, 0, [cls.partner_a.id, cls.partner_b.id])
            ],
            "commission_line_ids": [
                (
                    0,
                    0,
                    {
                        'date_from': -90,
                        'date_until': 10,
                        'commission': 5
                    }
                ),
                (
                    0,
                    0,
                    {
                        'date_from': 11,
                        'date_until': 20,
                        'commission': 4
                    }
                ),
                (
                    0,
                    0,
                    {
                        'date_from': 21,
                        'date_until': 0,
                        'commission': 1
                    }
                )
            ]
        })
        
        cls.product_commission_policies = cls.CommissionPolicy.create({
            "name": "Test Products Policy",
            "policy_type": 'product',
            "product_commission_type": "product",
            "products_id": (6, 0, [cls.product_a.id]),
            "commission_line_ids": [
                (
                    0,
                    0,
                    {
                        'date_from': -90,
                        'date_until': 8,
                        'commission': 8
                    }
                ),
                (
                    0,
                    0,
                    {
                        'date_from': 9,
                        'date_until': 14,
                        'commission': 7
                    }
                ),
                (
                    0,
                    0,
                    {
                        'date_from': 21,
                        'date_until': 0,
                        'commission': 3
                    }
                )
            ]
        })
        
        cls.product_brand_commission_policies = cls.CommissionPolicy.create({
            "name": "Test Product Brand Policy",
            "policy_type": 'product',
            "product_commission_type": "brand",
            "products_id": (6, 0, [cls.brand_b.id]),
            "commission_line_ids": [
                (
                    0,
                    0,
                    {
                        'date_from': -70,
                        'date_until': 21,
                        'commission': 12
                    }
                ),
                (
                    0,
                    0,
                    {
                        'date_from': 22,
                        'date_until': 30,
                        'commission': 10
                    }
                ),
                (
                    0,
                    0,
                    {
                        'date_from': 31,
                        'date_until': 0,
                        'commission': 9
                    }
                )
            ]
        })
        
        cls.product_categories_commission_policies = cls.CommissionPolicy.create({
            "name": "Test Product Categories Policy",
            "policy_type": 'product',
            "product_commission_type": "category",
            "products_id": (6, 0, [cls.env.ref('product.product_category_all').id]),
            "commission_line_ids": [
                (
                    0,
                    0,
                    {
                        'date_from': -80,
                        'date_until': 15,
                        'commission': 50
                    }
                ),
                (
                    0,
                    0,
                    {
                        'date_from': 16,
                        'date_until': 25,
                        'commission': 30
                    }
                ),
                (
                    0,
                    0,
                    {
                        'date_from': 26,
                        'date_until': 0,
                        'commission': 20
                    }
                )
            ]
        })

        cls.tax_group = cls.env["account.tax.group"].create({"name": "Tax"})

        cls.employee_bill = cls.env["hr.employee"].create({
            "name": "Bill Seller",
            "department_id": cls.env.ref("hr.dep_sales").id,
            "resource_calendar_id": cls.env.ref("resource.resource_calendar_std").id,
        })
        
        cls.delivery_method = cls.env["delivery.carrier"].create({
            "name": "Delivery Method",
            "delivery_type": "base_on_rule",
            "product_id": cls.company_data["product_service_delivery"].id,
            "margin": 0.0,
            "free_over": True,
            "amount": 0.0001,
            "fixed_price": 0.0,
        })
        
    def test_commission_for_partners(self):
        """ Test that the commission is correctly settled for partners """

        with Form(self.vip_clients_commission_policy) as commission_policy_form:
            self.assertIs(commission_policy_form.products_id, False,
                          "Products should not be set when partner is selected")
            self.assertIs(commission_policy_form.categories_id, False,
                          "Categories should not be set when partner is selected")
            self.assertIs(commission_policy_form.brands_id, False, "Brands should not be set when partner is selected")
            self.assertIs(commission_policy_form.product_commission_type, False,
                          "Product commission type should not be set when partner is selected")

            commission_policy_form.policy_type_id = self.policy_type_product.id
            commission_policy_form.product_commission_type = "product"
            self.assertIs(commission_policy_form.clients_id, False,
                          "Partners should not be set when product is selected")
            
    def test_commission_for_product_product(self):
        """ Test that the commission is correctly settled for products """

        with Form(self.product_commission_policies) as commission_policy_form:
            self.assertIs(commission_policy_form.clients_id, False,
                          "Clients should not be set when product is selected")
            self.assertEqual(commission_policy_form.product_commission_type, "product")
            self.assertIs(commission_policy_form.categories_id, False,
                          "Categories should not be set when product is selected")
            self.assertIs(commission_policy_form.brands_id, False, "Brands should not be set when product is selected")

    def test_commission_for_product_brand(self):
        """ Test that the commission is correctly settled for brands """

        with Form(self.product_brand_commission_policies) as commission_policy_form:
            self.assertIs(commission_policy_form.clients_id, False,
                          "Clients should not be set when product is selected")
            self.assertEqual(commission_policy_form.product_commission_type, "brand")
            self.assertIs(commission_policy_form.products_id, False,
                          "Products should not be set when brand is selected")
            self.assertIs(commission_policy_form.categories_id, False,
                          "Categories should not be set when product is selected")

    def test_commission_for_product_category(self):
        """ Test that the commission is correctly settled for categories """

        with Form(self.product_brand_commission_policies) as commission_policy_form:
            self.assertIs(commission_policy_form.clients_id, False,
                          "Clients should not be set when product is selected")
            self.assertEqual(commission_policy_form.product_commission_type, "category")
            self.assertIs(commission_policy_form.products_id, False,
                          "Products should not be set when brand is selected")
            self.assertIs(commission_policy_form.brands_id, False, "Brands should not be set when product is selected")
            
    def test_commission_date_overlap_below(self):
        """ Test where the commission date last range overlap below the date_until
            of the previous range """

        with self.assertRaises(ValidationError):
            test_commission_1 = self.CommissionPolicy.create({
                "name": "Test Commission 1",
                "policy_type": 'all',
                "commission_line_ids": [
                    (
                        0,
                        0,
                        {
                            'date_from': -80,
                            'date_until': 15,
                            'commission': 5
                        }
                    ),
                    (
                        0,
                        0,
                        {
                            'date_from': 14,
                            'date_until': 26,
                            'commission': 4
                        }
                    )
                ]
            })

    def test_commission_date_overlap_equal(self):
        """ Test where the commission date last range overlap equally with the date_until
            of the previous range """

        with self.assertRaises(ValidationError):
            test_commission_2 = self.CommissionPolicy.create({
                "name": "Test Commission 2",
                "policy_type": 'all',
                "commission_line_ids": [
                    (
                        0,
                        0,
                        {
                            'date_from': -80,
                            'date_until': 15,
                            'commission': 5
                        }
                    ),
                    (
                        0,
                        0,
                        {
                            'date_from': 15,
                            'date_until': 26,
                            'commission': 4
                        }
                    )
                ]
            })