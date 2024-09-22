from odoo import fields, models


class ResTownHall(models.Model):
    _name = "res.town.hall"
    _description = "Alcaldías"

    name = fields.Char(string="Alcaldía", required=True)
    percentage = fields.Float(string="% de retención", digits=(5, 2))
    expence_account_id = fields.Many2one(
        "account.account",
        string="Cuenta de gastos",
        required=True,
        company_dependent=True,
    )
    payable_account_id = fields.Many2one(
        "account.account",
        string="Cuenta por pagar",
        required=True,
        company_dependent=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Contacto",
        required=True,
        help="""Contacto relacionado el cual será utilizado al momento de
        registrar el pago del impuesto municipal por ingresos brutos.""",
    )

    _sql_constraints = [
        (
            "check_percentage",
            "CHECK(percentage > 0 AND percentage <= 100)",
            "El porcentaje de retención debe estar en "
            "un rango mayor a 0 y menor o igual a 100.",
        ),
    ]
