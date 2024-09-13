# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestSalaryRule(TransactionCase):

    @classmethod
    def setUpClass(cls):
        """Set up initial data."""
        super(TestSalaryRule, cls).setUpClass()

        cls.category = cls.env['hr.salary.rule.category'].create({
            'name': 'Test Category',
            'code': 'TEST'
        })

        cls.structure = cls.env['hr.payroll.structure'].search([], limit=1)

    def test_compute_salary_rule_code(self):
        """Test the compute of salary rule code."""
        rule = self.env['hr.salary.rule'].create({
            'name': 'Test Salary Rule',
            'category_id': self.category.id,
            'struct_id': self.structure.id,
            'sequence': 1
        })

        expected_value = self.category.code + str(rule.sequence)

        self.assertEqual(
            rule.code,
            expected_value,
            'The code should be {}'.format(expected_value)
        )

    def test_recompute_salary_rule_code_when_change_category_code(self):
        """Test the recompute of salary rule code when change category code."""
        rule = self.env['hr.salary.rule'].create({
            'name': 'Test Salary Rule',
            'category_id': self.category.id,
            'struct_id': self.structure.id,
            'sequence': 1
        })

        self.category.write({'code': 'NEW'})

        expected_value = self.category.code + str(rule.sequence)

        self.assertEqual(
            rule.code,
            expected_value,
            'The code should be {}'.format(expected_value)
        )
