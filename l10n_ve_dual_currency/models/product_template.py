from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    list_price_ref = fields.Float(
        string="Precio de venta op.",
        digits="Product Price",
        compute="_compute_list_price_ref",
        inverse="_inverse_list_price_ref",
        store=True,
    )
    standard_price_ref = fields.Float(
        "Coste op.",
        compute="_compute_standard_price_ref",
        inverse="_set_standard_price_ref",
        digits="Product Price",
    )
    currency_ref_id = fields.Many2one("res.currency", compute="_compute_currency_id")
    cost_currency_ref_id = fields.Many2one(
        "res.currency", compute="_compute_cost_currency_id"
    )

    @api.depends("list_price")
    def _compute_list_price_ref(self):
        for template in self:
            template.list_price_ref = (
                template.list_price * template.currency_ref_id.rate
            )

    @api.onchange("list_price_ref")
    def _inverse_list_price_ref(self):
        for template in self:
            template.list_price = (
                template.list_price_ref / template.currency_ref_id.rate
            )

    @api.depends_context("company")
    @api.depends("product_variant_ids", "product_variant_ids.standard_price_ref")
    def _compute_standard_price_ref(self):
        unique_variants = self.filtered(
            lambda template: len(template.product_variant_ids) == 1
        )
        for template in unique_variants:
            template.standard_price_ref = (
                template.product_variant_ids.standard_price_ref
            )
        for template in self - unique_variants:
            template.standard_price_ref = 0.0

    def _set_standard_price_ref(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.standard_price_ref = (
                    template.standard_price_ref
                )

    @api.depends("company_id")
    def _compute_currency_id(self):
        main_company = self.env["res.company"]._get_main_company()
        for template in self:
            template.currency_id = (
                template.company_id.sudo().currency_id.id or main_company.currency_id.id
            )
            template.currency_ref_id = (
                template.company_id.sudo().currency_ref_id.id
                or main_company.currency_ref_id.id
            )

    @api.depends_context("company")
    def _compute_cost_currency_id(self):
        self.cost_currency_id = self.env.company.currency_id.id
        self.cost_currency_ref_id = self.env.company.currency_ref_id.id
