from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CommissionConfLine(models.Model):
    _name = "commission.conf.line"
    _description = "set up commissions"

    contract_id = fields.Many2one("hr.contract", string="Contract")
    department_id = fields.Many2one(
        "hr.department",
        string="Department",
        required=True,
        domain=[("generate_commissions", "=", True)],
    )
    bill_calculation = fields.Selection(
        [("posted_bill", "Invoice generated"), ("paid_bill", "Invoice paid")],
        string="Bill Calculation",
        required=True,
    )
    fixed_amount = fields.Float(string="Fixed amount")
    direct_percentage = fields.Float(string="Direct percentage")
    allocation_percentage = fields.Float(string="Allocation percentage")
    global_percentage = fields.Float(string="Global percentage")
    scale_ids = fields.Many2many("commission.scale", string="Scale")

    @api.onchange("direct_percentage")
    def _onchange_direct_percentage(self):
        if self.direct_percentage < 0 or self.direct_percentage > 100:
            raise ValidationError(
                _("You must enter percentages greater than 0 or less than 100.")
            )

    @api.onchange("allocation_percentage")
    def _onchange_allocation_percentage(self):
        if self.allocation_percentage < 0 or self.allocation_percentage > 100:
            raise ValidationError(
                _("You must enter percentages greater than 0 or less than 100.")
            )

    @api.onchange("global_percentage")
    def _onchange_global_percentage(self):
        if self.global_percentage < 0 or self.global_percentage > 100:
            raise ValidationError(
                _("You must enter percentages greater than 0 or less than 100.")
            )

    @api.onchange("department_id")
    def _onchange_department_id(self):
        department_ids = self.contract_id.commission_conf_line_ids.mapped(
            "department_id"
        )
        return {
            "domain": {
                "department_id": [
                    ("generate_commissions", "=", True),
                    ("id", "not in", department_ids.ids),
                ]
            }
        }
