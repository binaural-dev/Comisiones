{
    'name': "binaural ventas",

    'summary': """
       Modulo para el proceso de Ventas """,

    'author': "Binauraldev",
    'website': "https://binauraldev.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales/Sales',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base','sale','sale_management','binaural_contactos_configuraciones','binaural_inventario'],

    # always loaded
    'data': [
        'data/config_data.xml',
        'views/res_config.xml',
        'views/sale_form_inh.xml',
        'views/sale_search_inh.xml',
        'views/sale_trees_inh.xml',
    ],
    'application':True,
}
