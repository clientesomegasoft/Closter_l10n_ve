from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountISLRConcept(models.Model):
    _name = "account.islr.concept"
    _description = "ISLR Concept"
    _order = "name"

    name = fields.Char(string="Concept name", required=True)
    rate_ids = fields.One2many(
        "account.islr.concept.rate", "islr_concept_id", string="Rates"
    )

    def get_concept_rate(self, person_type_id, base_ut):
        self.ensure_one()

        rate_id = self.rate_ids.filtered(
            lambda line: line.person_type_id.id == person_type_id.id
        )
        if not rate_id:
            raise ValidationError(
                f"""No se encontró tasa de retención de ISLR.\n\nTipo:
                {person_type_id.name}\nConcepto: {self.name}"""
            )

        if not rate_id.rate_type:
            rate = rate_id.rate / 100
            subtraction = rate_id.subtraction
        else:
            if base_ut <= 2000:
                rate = 0.15
                subtraction = 0.0
            elif base_ut <= 3000:
                rate = 0.2
                subtraction = 140
            else:
                rate = 0.34
                subtraction = 500
            if rate_id.rate_type == "payment":
                subtraction = 0.0

        return {
            "id": rate_id.id,
            "base": rate_id.base / 100,
            "rate": rate,
            "subtraction": subtraction,
        }


class AccountISLRConceptRate(models.Model):
    _name = "account.islr.concept.rate"
    _description = "ISLR concept rate"
    _order = "name"

    name = fields.Char(string="Code", size=3, required=True)
    person_type_id = fields.Many2one(
        "person.type", string="Type of person", required=True
    )
    base = fields.Float(string="% Base", digits=(5, 2), default=100)
    factor = fields.Float(string="Factor", digits=(16, 4))
    rate = fields.Float(string="% Retention", digits=(5, 2))
    subtraction = fields.Float(
        string="Subtraction (UT)", compute="_compute_subtraction", store=True
    )
    rate_type = fields.Selection(
        [("payment", "Accumulated payments"), ("rate", "Rate 2")], string="Rate type"
    )
    islr_concept_id = fields.Many2one(
        "account.islr.concept", string="ISLR Concept", ondelete="cascade"
    )

    _sql_constraints = [
        ("unique_name", "UNIQUE(name)", "The code must be unique!"),
        ("isdigit_name", "CHECK(name ~ '^\\d+$')", "The code must be numeric!"),
        (
            "unique_person_type_id",
            "UNIQUE(islr_concept_id, person_type_id)",
            'The "Person Type" field must be unique per concept!',
        ),
    ]

    @api.depends("factor", "rate")
    def _compute_subtraction(self):
        for rec in self:
            rec.subtraction = rec.factor * rec.rate / 100
