# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestParafiscalContributionsField(TransactionCase):

    def test_compute_parafiscal_contributions_field(self):
        """Test the compute of parafiscal contributions field."""
        contract = self.env['hr.contract'].search([], limit=1)
        contract.write({
            'percentage_income_tax_islr': -5,
        })
        expect_values = [x for x in range(0,100)]

        self.assertIn(contract.percentage_income_tax_islr in expect_values, 'Los montos permitidos para el porcentaje de ISLR estan en el rango [0,99].')