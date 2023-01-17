{
    "name": "binaural nomina",
    "summary": """
        Personalizaciones para la nomina de Venezuela
        """,
    "description": """
        Modulo que agrega las personalizaciones de ley para Venezuela, incluye FAOV, INCE, IVSS, Paro Forzoso
    """,
    "author": "Binaural C.A.",
    "website": "https://binauraldev.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Human Resources",
    "version": "14.0.0.0.1",
    # any module necessary for this one to work correctly
    "depends": [
        "base",
        "account",
        "hr_work_entry_holidays",
        "hr_payroll",
        "hr_payroll_account",
        "binaural_contactos_configuraciones",
    ],
    "external_dependencies": {"python" : ["pandas"]},
    # always loaded
    "data": [
        "data/account_journal.xml",
        "data/master_data.xml",
        "data/rules_data.xml",
        "data/config_data.xml",
        "data/ir_cron.xml",
        "data/provisions_rules_data.xml",
        "security/ir.model.access.csv",
        "views/hr_department_view_inh.xml",
        "views/hr_allowance_lines.xml",
        "views/hr_allowance.xml",
        "views/hr_contract_binaural.xml",
        "views/hr_employee_binaural.xml",
        "views/hr_employee_salary_change.xml",
        "views/hr_leave_binaural.xml",
        "views/hr_leave_type_binaural.xml",
        "views/hr_payroll_benefit.xml",
        "views/hr_payroll_benefits_accumulated_detail.xml",
        "views/hr_payroll_move.xml",
        "views/hr_payroll_structure.xml",
        "views/hr_payslip_binaural.xml",
        "views/hr_payslip_payment_methods.xml",
        "views/hr_salary_rule_binaural.xml",
        "views/hr_salary_tab.xml",
        "views/report_payslip_templates_inherit.xml",
        "views/res_bank_view.xml",
        "views/res_config.xml",
        "views/hr_menu_binaural.xml",
        "wizard/hr_departure_wizard.xml",
        "wizard/hr_payroll_payslip_by_employees_view_inh.xml",
    ],
    # only loaded in demonstration mode
    "demo": [],
}
