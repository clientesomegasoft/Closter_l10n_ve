from odoo.tests.common import TransactionCase


class TestSalaryField(TransactionCase):
    def test_compute_salary_field(self):
        """Test the compute of salary field."""
        contract = self.env["hr.contract"].search([], limit=1)
        contract.write(
            {
                "cestaticket_salary": 0.577,
                "average_wage": 25,
                "salary_overtime_hours": 4.56447,
            }
        )

        self.assertGreaterEqual(
            contract.cestaticket_salary,
            0,
            "Los montos de los salarios deben ser superiores a cero.",
        )

        self.assertGreaterEqual(
            contract.average_wage,
            0,
            "Los montos de los salarios deben ser superiores a cero.",
        )

        self.assertGreaterEqual(
            contract.salary_overtime_hours,
            0,
            "Los montos de los salarios deben ser superiores a cero.",
        )
