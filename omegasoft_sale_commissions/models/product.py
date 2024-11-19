from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_commission = fields.Boolean(string="Commission per product")
    percentage = fields.Float(string="Percentage")
    fixed_amount = fields.Float(string="Fixed amount")
    commission_type = fields.Selection(
        [("percentage", "Percentage"), ("fixed_amount", "Fixed amount")], string="Type"
    )

    @api.onchange("percentage")
    def _onchange_percentage(self):
        if self.percentage < 0 or self.percentage > 100:
            raise ValidationError(
                _("You must enter percentages greater than 0 or less than 100.")
            )

    @api.onchange("commission_type")
    def _onchange_commission_type(self):
        if self.commission_type == "percentage":
            self.fixed_amount = 0
        elif self.commission_type == "fixed_amount":
            self.percentage = 0

    @api.onchange("product_commission")
    def _onchange_commission_product(self):
        if not self.product_commission:
            self.percentage = 0
            self.fixed_amount = 0
