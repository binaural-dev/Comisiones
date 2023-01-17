# -*- coding: utf-8 -*-
{
    'name': "Binaural Politica de Ventas para Ecommerce",

    'summary': """
        Modulo para manejar las politicas de ventas en el apartado de ecommerce. """,

    'description': """
        Modulo para el manejo de multimonedas
    """,

    'author': "Binauraldev",
    'website': "https://binauraldev.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Inventory/Website',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['binaural_inventario', 'web', 'website', 'website_sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/template_assets.xml',
        'views/ecommerce_template.xml',
    ],
    'application':True,
}

