from odoo import fields, models


class PersonType(models.Model):
    _name = "person.type"
    _description = "Type of person"

    name = fields.Char(string="Type", required=True)
    code = fields.Char(string="Code", required=True)
    is_company = fields.Boolean(string="It's company", default=False)
