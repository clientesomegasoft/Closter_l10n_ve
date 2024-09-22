import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError

rif_regex = re.compile("^[J,V,G]-[0-9]{8}-[0-9]$")
ci_regex = re.compile("^V[0-9]{7,8}$|^E[0-9]{3,10}$|^P[0-9]{10,20}$")


class Partner(models.Model):
    _inherit = "res.partner"

    @api.model
    def default_get(self, default_fields):
        res = super().default_get(default_fields)
        ctx = self._context
        if (
            ctx.get("res_partner_search_mode") == "customer"
            or ctx.get("default_customer_rank") == 1
            or ctx.get("search_default_customer") == 1
        ):
            res["partner_type"] = "customer"
        elif (
            ctx.get("res_partner_search_mode") == "supplier"
            or ctx.get("default_supplier_rank") == 1
            or ctx.get("search_default_supplier") == 1
        ):
            res["partner_type"] = "supplier"
        return res

    person_type_id = fields.Many2one(
        "person.type",
        string="Tipo de persona",
        domain="[('is_company', '=', is_company)]",
        tracking=True,
        copy=False,
    )
    person_type_code = fields.Char(related="person_type_id.code")
    identification = fields.Char("Documento de identidad", tracking=True, copy=False)
    partner_type = fields.Selection(
        [
            ("customer", "Cliente"),
            ("supplier", "Proveedor"),
            ("customer_supplier", "Cliente / Proveedor"),
        ],
        string="Clasificación comercial",
        tracking=True,
        copy=False,
    )
    vat = fields.Char(string="RIF", tracking=True, copy=False)

    _sql_constraints = [
        (
            "unique_identification",
            "UNIQUE(identification)",
            "\nYa existe un contacto con el mismo Documento de identidad !",
        ),
        (
            "unique_vat",
            "EXCLUDE (vat WITH =) WHERE (parent_id IS NULL)",
            "\nYa existe un contacto con el mismo RIF !",
        ),
    ]

    @api.constrains(
        "person_type_id", "identification", "vat", "country_id", "partner_type"
    )
    def check_partner_type(self):
        if self._context.get("skip_check_partner_type"):
            return
        for partner in self:
            if partner.type in ("contact", "invoice"):
                if partner.is_company:
                    if partner.person_type_id.code not in ("PJDO", "PJND"):
                        raise ValidationError(
                            _("El campo 'Tipo de persona' no puede ser nulo y "
                            "debe corresponder con el tipo de contacto Compañía "
                            "('PJDO' o 'PJND').")
                        )
                    if partner.person_type_id.code == "PJDO" and not partner.vat:
                        raise ValidationError(_("El campo 'RIF' no puede ser nulo !"))
                    if (
                        partner.person_type_id.code == "PJDO"
                        and partner.country_id.code == "VE"
                        and not (
                            rif_regex.match(partner.vat)
                            and self.simple_vat_check("ve", partner.vat)
                        )
                    ):
                        raise ValidationError(
                            _("El campo 'RIF' tiene un formato incorrecto.\n"
                            "Formatos admitidos: J-12345678-9, V-12345678-9 o "
                            "G-12345678-9.")
                        )
                else:
                    if partner.person_type_id.code not in ("PNRE", "PNNR"):
                        raise ValidationError(
                            _("El campo 'Tipo de persona' no puede ser nulo y debe "
                            "corresponder con el tipo de contacto Individual ('PNRE' "
                            "o 'PNNR').")
                        )
                    if not partner.identification:
                        raise ValidationError(
                            _("El campo 'Documento de identidad' no puede ser nulo !")
                        )
                    if (
                        partner.person_type_id.code == "PNRE"
                        and partner.country_id.code == "VE"
                        and not ci_regex.match(partner.identification)
                    ):
                        raise ValidationError(
                            _("El campo 'Documento de identidad' tiene un formato "
                            "incorrecto.\nFormatos admitidos: V12345678, E12345678, "
                            "P1234567890.")
                        )
                if not partner.partner_type:
                    raise ValidationError(
                        _("El campo 'Clasificación comercial' no puede ser nulo !")
                    )

    @api.constrains("vat", "country_id")
    def check_vat(self):
        return super(
            Partner, self.filtered(lambda p: p.country_id.code != "VE")
        ).check_vat()

    @api.onchange("type", "is_company")
    def _clean_fiscal_fields(self):
        self.person_type_id = False
        self.identification = False
        self.partner_type = False
        self.vat = False

    def _get_name(self):
        res = super(__class__, self)._get_name()
        if self._context.get("show_vat") and not self.vat and self.identification:
            res = "%s\n%s" % (res, self.identification)
        return res


class Users(models.Model):
    _inherit = "res.users"

    @api.model_create_multi
    def create(self, vals_list):
        self = self.with_context(skip_check_partner_type=True)
        return super(__class__, self).create(vals_list)


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.model_create_multi
    def create(self, vals_list):
        self = self.with_context(skip_check_partner_type=True)
        return super(__class__, self).create(vals_list)
