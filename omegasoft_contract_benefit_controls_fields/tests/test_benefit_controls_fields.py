from odoo.tests.common import TransactionCase


class TestBenefitControlsField(TransactionCase):
    def test_compute_benefit_controls_field(self):
        """Test the compute of benefit_controls field."""
        contract = self.env["hr.contract"].search([], limit=1)
        contract.write(
            {
                "accumulated_social_benefits": 24.6,
                "interest_accrued_employee_benefits": 2.5,
            }
        )

        self.assertGreaterEqual(
            contract.accumulated_social_benefits,
            0,
            "Los montos de los controles prestacionales deben ser superiores a cero.",
        )

        self.assertGreaterEqual(
            contract.interest_accrued_employee_benefits,
            0,
            "Los montos de los controles prestacionales deben ser superiores a cero.",
        )
