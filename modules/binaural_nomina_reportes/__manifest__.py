{
    "name": "Binaural Nomina Reportes",
    "summary": """
        Reportes para la nómina de Integra.
    """,
    "author": "Binaural",
    "website": "http://www.yourcompany.com",
    "category": "Human Resources",
    "version": "0.1",
    # any module necessary for this one to work correctly
    "depends": ["binaural_nomina"],
    # always loaded
    "data": [
        "data/hr_employee_entry_occupation.xml",
        "data/hr_employee_type.xml",
        "data/report_paperformat.xml",
        "security/ir.model.access.csv",
        "views/res_config.xml",
        "wizard/faov_txt_wizard.xml",
        "wizard/ivss_salary_change_txt_wizard.xml",
        "wizard/ivss_employee_ingress_txt_wizard.xml",
        "views/hr_employee_binaural.xml",
        "views/hr_menu_binaural.xml",
        "views/hr_payslip_payment_methods_inh.xml",
        "report/hr_payslip_run_report.xml",
    ],
    # only loaded in demonstration mode
    "demo": [],
}
