
{
    'name': "Binaural Comisiones",
    'summary':
        """
            Personalizacion para las Politicas de Comisiones
        """,
    'description':
        """ 
            Modulo para generar las politicas de comisiones y calcularla para la factura de vendedor. 
        """,
    'author': "Binauraldev",
    'company': "Binauraldev",
    'license': 'AGPL-3',
    'maintainer': "Binauraldev",
    'website': "https://www.binauraldev.com",
    'category': "Expense/Payroll",
    'version': "0.0.0.0.0",
    'depends': [
        'account',
        'binaural_inventario',
        'binaural_vendedores',
        'binaural_facturacion'
    ],
    'data': [
        "security/ir.model.access.csv",
        "data/cron.xml",
        "data/hr_expense_data.xml",
        "data/default_settings.xml",
        "views/res_config.xml",
        "views/commission_policy_views.xml",
        "views/commission_policy_line_views.xml",
        "wizard/account_expense_wizard_view.xml",
        "data/actions.xml",
        "wizard/invoice_commission_summary_wizard_views.xml",
        "views/account_move_views.xml",
        "views/commission_policy_image_views.xml",
        "views/commission_policy_image_line_views.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}