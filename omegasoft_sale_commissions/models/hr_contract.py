from odoo import _, api, fields, models
from odoo.exceptions import UserError


class Contract(models.Model):
    _inherit = "hr.contract"

    receive_commission = fields.Boolean(string="Receives commission")

    # commission configuration page
    cutoff_type = fields.Selection(
        [("end_month", "End of the month"), ("personalized", "Personalized")],
        string="Cutoff date",
        default="end_month",
    )
    cutoff_date = fields.Integer(string="Cutoff date")
    commission_conf_line_ids = fields.One2many("commission.conf.line", "contract_id")

    # Assigned commissions page
    paid_sales_allocation_ids = fields.One2many("paid.sales.allocation", "contract_id")

    @api.constrains("cutoff_date")
    def _onchange_cutoff_date_kjfgkj(self):
        if self.receive_commission and self.cutoff_date < 1 or self.cutoff_date > 28:
            raise UserError(
                _(
                    "The allowed range of values on the commission cutoff date is 1-28."
                )
            )
