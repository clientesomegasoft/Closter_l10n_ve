# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestBonusesField(TransactionCase):

    def test_compute_bonuses_field(self):
        """Test the compute of bonuses field."""
        contract = self.env['hr.contract'].search([], limit=1)
        contract.write({
            'complementary_bonus': 24.6,
            'night_bonus_amount': 2.5,
            'perfect_attendance_bonus': 45644.7,
        })

        self.assertGreaterEqual(
            contract.complementary_bonus,
            0,
            'Los montos de los bonos de salarios deben ser superiores a cero.'
        )

        self.assertGreaterEqual(
            contract.night_bonus_amount,
            0,
            'Los montos de los bonos de salarios deben ser superiores a cero.'
        )

        self.assertGreaterEqual(
            contract.perfect_attendance_bonus,
            0,
            'Los montos de los bonos de salarios deben ser superiores a cero.'
        )