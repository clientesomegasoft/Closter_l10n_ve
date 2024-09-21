from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleConsignmentReportWizard(models.TransientModel):
    _name = "sale.consignment.report.wizard"

    report_type = fields.Selection(
        [
            ("consignment_details_report", "Consignment Detailes Report"),
            ("sale_details_report", "Sale Detailes Report"),
        ],
        default="consignment_details_report",
        string="Report",
    )
    date_from = fields.Date(
        string="Date From",
        required=True,
        default=lambda self: fields.Date.to_string(date.today().replace(day=1)),
    )
    date_to = fields.Date(
        string="Date To",
        required=True,
        default=lambda self: fields.Date.to_string(
            (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()
        ),
    )
    customer_ids = fields.Many2many("res.partner", string="Customers")
    product_ids = fields.Many2many("product.product", string="Product")
    consignment_ids = fields.Many2many(
        "sale.consignment.order", string="Consignment Order"
    )

    def action_print_report(self):
        data = {
            "date_from": self.date_from,
            "date_to": self.date_to,
            "customer_ids": self.customer_ids.ids,
            "product_ids": self.product_ids.ids,
            "consignment_ids": self.consignment_ids.ids,
            "report_type": self.report_type,
        }
        return self.env.ref(
            "pways_so_po_consignment.sale_consignment_report"
        ).report_action(self, data=data)

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        if any(muster.date_from > muster.date_to for muster in self):
            raise ValidationError(
                _("Attendance Muster 'Date From' must be earlier 'Date To'.")
            )


class SaleConsignmentTemplate(models.AbstractModel):
    _name = "report.pways_so_po_consignment.sale_consignments_template"

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get("active_model")
        docs = self.env[model].browse(self.env.context.get("active_id"))
        date_from = data.get("date_from")
        date_to = data.get("date_to")
        customer_ids = data.get("customer_ids")
        product_ids = data.get("product_ids")
        report_type = data.get("report_type")
        consignment_order_ids = data.get("consignment_ids")
        lines = []
        consignment_order_details = []
        if report_type == "sale_details_report":
            consignment_domain = [
                ("date_order", ">=", date_from),
                ("date_order", "<=", date_to),
            ]
            if customer_ids:
                consignment_domain.append(("partner_id", "in", customer_ids))
            consignment_ids = self.env["sale.consignment.order"].search(
                consignment_domain
            )
            for consignment in consignment_ids:
                order_line = self.env["sale.consignment.line"]
                sale_order_lines = self.env["sale.order.line"]
                if product_ids:
                    sale_order_lines = consignment.sale_ids.mapped(
                        "order_line"
                    ).filtered(lambda x: x.product_id.id in product_ids)
                    order_line = consignment.order_line.filtered(
                        lambda x: x.product_id.id in product_ids
                    )
                else:
                    order_line = consignment.mapped("order_line")
                    sale_order_lines = consignment.sale_ids.mapped("order_line")
                lines.append(
                    {
                        "consignment_id": consignment,
                        "name": consignment.name,
                        "customer": consignment.partner_id.name,
                        "order_line": order_line,
                        "sale_order_ids": consignment.sale_ids,
                        "sale_order_lines_ids": sale_order_lines,
                        "data_from": date_from,
                        "date_to": date_to,
                    }
                )

        if report_type == "consignment_details_report":
            domain = [("date_order", ">=", date_from), ("date_order", "<=", date_to)]
            if consignment_order_ids:
                domain.append(("id", "in", consignment_order_ids))
            consignment_order_ids = self.env["sale.consignment.order"].search(domain)
            for consignment in consignment_order_ids:
                total = sum(consignment.order_line.mapped("price_subtotal"))
                cost_total = sum(consignment.order_line.mapped("cost_total"))
                profit_total = sum(consignment.order_line.mapped("profit_total"))
                sale_total = sum(consignment.order_line.mapped("sale_total"))
                consignment_order_details.append(
                    {
                        "consignment_id": consignment,
                        "name": consignment.name,
                        "customer": consignment.partner_id.name,
                        "date": consignment.date_order,
                        "order_line": consignment.order_line,
                        "total": round(total, 2),
                        "cost_total": round(cost_total, 2),
                        "profit_total": round(profit_total, 2),
                        "sale_total": round(sale_total, 2),
                    }
                )
        return {
            "docs": docs,
            "company": self.env.company,
            "lines": lines,
            "data_from": date_from,
            "date_to": date_to,
            "report_type": report_type,
            "consignment_order_details": consignment_order_details,
        }
