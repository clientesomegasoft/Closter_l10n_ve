from odoo.tests.common import TransactionCase


class TestAverageWageLines(TransactionCase):
    @classmethod
    def setUpClass(cls):
        """Set up initial data."""
        super(__class__, cls).setUpClass()

        cls.category = cls.env["hr.salary.rule.category"].create(
            {"name": "Test Category", "code": "TEST"}
        )

        default_schedule_pay = [
            "monthly",
            "quarterly",
            "semi-annually",
            "annually",
            "weekly",
            "bi-weekly",
            "bi-monthly",
        ]
        cls.structure = cls.env["hr.payroll.structure.type"].create(
            {
                "name": "Test Structure type",
                "default_schedule_pay": default_schedule_pay[0],
            }
        )

    def test_compute__check_average_days(self):
        """Test the compute average_days."""
        average_wage_line = self.env["average_wage_lines"].create(
            {
                "payroll_structure_type": self.structure.id,
                "salary_rule_category": self.category.id,
                "average_days": 0,
            }
        )

        self.assertGreaterEqual(
            average_wage_line.average_days,
            0,
            "Los montos para el promedio de días deben ser superiores a cero.",
        )

    # def test_recompute_salary_rule_code_when_change_category_code(self):
    #     """Test the recompute of salary rule code when change category code."""
    #     rule = self.env['hr.salary.rule'].create({
    #         'name': 'Test Salary Rule',
    #         'category_id': self.category.id,
    #         'struct_id': self.structure.id,
    #         'sequence': 1
    #     })

    #     self.category.write({'code': 'NEW'})

    #     expected_value = self.category.code + str(rule.sequence)

    #     self.assertEqual(
    #         rule.code,
    #         expected_value,
    #         'The code should be {}'.format(expected_value)
    #     )
