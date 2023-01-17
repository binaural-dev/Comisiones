import logging
from psycopg2 import IntegrityError
from odoo.tests.common import Form, SavepointCase
from odoo.tests import tagged
_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class HrEmployeeSalaryChangeTestCase(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(HrEmployeeSalaryChangeTestCase, cls).setUpClass()

        employee = Form(cls.env["hr.employee"])
        employee.name = "Empleado Prueba 1"
        employee.save()

        structure_type = Form(cls.env["hr.payroll.structure.type"])
        structure_type.name = "Estructure Prueba 1"
        structure_type.wage_type = "hourly"
        structure_type.save()

        contract = Form(cls.env["hr.contract"])
        contract.name = "Contrato Prueba 1"
        contract.structure_type_id = cls.env["hr.payroll.structure.type"].search([("id", '=', structure_type.id)])
        contract.hourly_wage = 55
        contract.save()

        cls.employee = cls.env["hr.employee"].search([("id", '=', employee.id)])
        cls.stucture_type = cls.env["hr.payroll.structure.type"].search([("id", '=', structure_type.id)])
        cls.contract = cls.env["hr.contract"].search([("id", '=', contract.id)])

    def test_salary_change_registered_successfully(self):
        """
        Validar que la última fecha de  variación del empleado coincidan con 
        la información registrada en la ficha del contrato vigente del empleado.
        """
        with Form(self.contract) as contract:
            contract.hourly_wage = 10
        last_salary_change = self.env["hr.employee.salary.change"].search([])[-1]
        self.assertEqual(last_salary_change.wage_type, "hourly")
        self.assertEqual(last_salary_change.hourly_wage, 10)
