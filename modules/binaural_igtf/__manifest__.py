{
    'name': 'Binaural IGTF',
    'summary': 'Modulo para el impuesto IGTF (Impuesto a las grandes transacciones financieras)',
    'license': 'AGPL-3',
    'description': 'Modulo para el impuesto IGTF (Impuesto a las grandes transacciones financieras)',
    'author': 'Binauraldev',
    'website': "https://binauraldev.com/",
    'category': 'Accounting/Accounting',
    'version': '1.0',

    'depends': ['base', 'account'],

    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings.xml',
        'views/account_journal.xml',
        'views/account_payment.xml',
        'views/account_move.xml',
        'wizard/account_payment_register.xml',
        'wizard/pay_igtf.xml',
    ],
    'images': ['static/description/icon.png'],

    'application': True,


}