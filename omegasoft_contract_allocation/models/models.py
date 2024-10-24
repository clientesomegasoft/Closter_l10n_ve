from odoo import fields, models


class ProductTemplateCustomization(models.Model):
    _inherit = "product.template"

    is_an_endowment_product = fields.Boolean(string="It is an endowment product")


class HrContractCustomization(models.Model):
    _inherit = "hr.contract"

    allocation_ids = fields.Many2many(
        string="Allocations", comodel_name="contract_allocation", ondelete="restrict"
    )

    delivered_count = fields.Integer(compute="_compute_delivered_count")

    def get_endowments_delivered(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": ("Dotaciones entregadas"),
            "view_mode": "tree",
            "res_model": "contract_allocation_lines",
            "domain": [
                ("employee_id", "=", self.employee_id.id),
                ("quantity_delivered", ">", 0),
            ],
            "context": "{'create': False}",
        }

    def _compute_delivered_count(self):
        for record in self:
            record.delivered_count = self.env["contract_allocation_lines"].search_count(
                [
                    ("employee_id", "=", self.employee_id.id),
                    ("quantity_delivered", ">", 0),
                ]
            )
