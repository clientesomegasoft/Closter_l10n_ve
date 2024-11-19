from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrEmployeeFamilyInformation(models.Model):
    _name = "hr_employee_family_information"
    _description = "Employees family information"

    name = fields.Char(string="Name", help="Name of relative")
    active = fields.Boolean(
        default=True,
        help="""Set active to false to hide the fam,ily
        information tag without removing it.""",
    )
    relationship = fields.Selection(
        string="Relationship",
        help="Relationship",
        selection=[
            ("father", "Father"),
            ("mother", "Mother"),
            ("son", "Son"),
            ("daughter", "Daughter"),
            ("spouse", "Spouse"),
        ],
    )
    nationality = fields.Selection(
        selection=[("venezuelan", "V"), ("foreigner", "E")], string="Nationality"
    )
    id_number = fields.Char(string="ID Number")
    date_of_birth = fields.Date(string="Date of birth")
    age = fields.Integer(string="Age")
    guardianship = fields.Boolean(
        string="Guardianship",
        help="indicates whether you have guardianship of the child",
    )
    gender = fields.Selection(
        string="Gender", selection=[("male", "Male"), ("female", "Female")]
    )

    type_age = fields.Selection(
        string="Type age",
        selection=[("days", "Days"), ("months", "Months"), ("years", "Years")],
    )

    study_level = fields.Selection(
        string="Study level",
        selection=[
            ("maternal", "Maternal"),
            ("elementary_school", "Elementary school"),
            ("high_school", "High School"),
            ("university", "University"),
        ],
    )
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee")
    is_family_burden = fields.Boolean(string="Carga Familiar", default=False)

    @api.onchange("date_of_birth")
    def _onchange_date_of_birth(self):
        years = relativedelta(datetime.now(), self.date_of_birth).years
        months = relativedelta(datetime.now(), self.date_of_birth).months
        days = relativedelta(datetime.now(), self.date_of_birth).days
        if years > 0:
            self.age = years
            self.type_age = "years"
        elif months > 0:
            self.age = months
            self.type_age = "months"
        else:
            self.age = days
            self.type_age = "days"

    @api.onchange("id_number")
    def _onchange_id_number(self):
        if self.id_number and not self.id_number.isdigit():
            raise ValidationError(
                _(
                    "Advertencia! Para el número de C.I "
                    "solo se admiten caracteres numéricos"
                )
            )
        if self.id_number and len(self.id_number) > 8:
            raise ValidationError(
                _(
                    "Advertencia! La longitud para el número de C.I "
                    "no debe ser mayor a 8 caracteres"
                )
            )
