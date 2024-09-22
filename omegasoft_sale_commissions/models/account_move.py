from datetime import datetime

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    department_id = fields.Many2one(
        "hr.department",
        string="Department",
        domain=[("generate_commissions", "=", True)],
    )
    seller_employee_id = fields.Many2one("hr.employee", string="seller")
    assigned_employee_id = fields.Many2one("hr.employee", string="Assigned")
    required_department_id = fields.Boolean(
        string="required_department_id", default=False
    )

    @api.onchange("seller_employee_id")
    def _onchange_seller_employee(self):
        if self.seller_employee_id and not self.assigned_employee_id:
            self.assigned_employee_id = self.seller_employee_id
            self.required_department_id = True

    @api.onchange("assigned_employee_id", "seller_employee_id")
    def _onchange_required_department_id(self):
        if self.seller_employee_id and self.assigned_employee_id:
            self.required_department_id = True
        else:
            self.required_department_id = False

    def action_post(self):
        res = super(__class__, self).action_post()
        for rec in self:
            # Total de la factura en la moneda de la compañia
            total_invoice = rec.currency_id._convert(
                rec.amount_untaxed,
                rec.company_currency_id,
                rec.company_id,
                rec.currency_rate_ref,
            )
            # Se obtienen las líneas de configuración que
            # cumplan con las condiciones establecidas
            query_resul = rec._query_commission_conf_line(
                rec.department_id.id,
                rec.seller_employee_id.id,
                rec.assigned_employee_id.id,
                "'posted_bill'",
                total_invoice,
            )
            # Se calcula el monto adicional de comisiones por producto
            commission_products = rec._calculate_commission_products()
            if query_resul and commission_products:
                rec._create_paid_commission_line(
                    query_resul, commission_products, total_invoice
                )
        return res

    @api.constrains("payment_state")
    def _constrains_payment_state(self):
        for rec in self.filtered(
            lambda x: x.move_type
            in ("out_invoice", "out_refund", "in_invoice", "in_refund")
            and x.payment_state == "paid"
        ):
            # Total de la factura en la moneda de la compañia
            total_invoice = rec.currency_id._convert(
                rec.amount_untaxed,
                rec.company_currency_id,
                rec.company_id,
                rec.currency_rate_ref,
            )
            # Se obtienen las líneas de configuración
            # que cumplan con las condiciones establecidas
            query_resul = rec._query_commission_conf_line(
                rec.department_id.id,
                rec.seller_employee_id.id,
                rec.assigned_employee_id.id,
                "'paid_bill'",
                total_invoice,
            )
            # Se calcula el monto adicional de comisiones por producto
            commission_products = rec._calculate_commission_products()
            if query_resul and commission_products:
                rec._create_paid_commission_line(
                    query_resul, commission_products, total_invoice
                )

    def _calculate_commission_products(self):
        products = self.invoice_line_ids.filtered(
            lambda line: line.product_id.product_commission
        )
        return sum(
            [
                x.price_subtotal * (x.product_id.percentage) / 100
                if x.product_id.commission_type == "percentage"
                else x.product_id.fixed_amount
                for x in products
            ]
        )

    def _create_paid_commission_line(
        self, query_resul, commission_products, total_invoice
    ):
        self.ensure_one()
        if query_resul:
            for cl in query_resul:
                total_commission = 0
                if cl.get("cs_id", False):
                    total_commission = (
                        commission_products
                        + cl.get("cs_fixed_amount")
                        + (total_invoice * cl.get("cs_percentage") / 100)
                    )
                else:
                    total_commission = (
                        commission_products
                        + cl.get("ccl_amount")
                        + (total_invoice * cl.get("global_percentage") / 100)
                    )
                    if cl.get("contract_employee") == self.seller_employee_id.id:
                        total_commission += (
                            total_invoice * cl.get("direct_percentage") / 100
                        )
                    elif cl.get("contract_employee") == self.assigned_employee_id.id:
                        total_commission += (
                            total_invoice * cl.get("allocation_percentage") / 100
                        )

                psa_vals = {
                    "contract_id": cl.get("hc_id"),
                    "employee_id": cl.get("contract_employee"),
                    "invoice_id": self.id,
                    "department_id": cl.get("department"),
                    "date": datetime.now(),
                    "state": "pending",
                    "assignment": total_commission,
                    "currency_id": self.company_currency_id.id,
                }
                self.env["paid.sales.allocation"].create(psa_vals)

    def _query_commission_conf_line(
        self, department, seller, assigned, calculation, total_invoice
    ):
        self.ensure_one()
        if self.department_id and self.seller_employee_id and self.assigned_employee_id:
            query = """
                    SELECT ccl.id AS ccl_id,
                                ccl.department_id AS department,
                                ccl.bill_calculation AS bill_calculation,
                                ccl.fixed_amount AS ccl_amount,
                                ccl.direct_percentage AS direct_percentage,
                                ccl.allocation_percentage AS allocation_percentage,
                                ccl.global_percentage AS global_percentage,
                                hc.id AS hc_id,
                                hc.employee_id AS contract_employee,
                                scale.scale AS cs_id,
                                cs.fixed_amount AS cs_fixed_amount,
                                cs.percentage AS cs_percentage
                            FROM commission_conf_line AS ccl
                            JOIN hr_contract AS hc ON hc.id = ccl.contract_id
                            LEFT JOIN (SELECT ccl.id AS commission,
                                                max(cs.id) AS scale
                                        FROM commission_conf_line AS ccl
                                        JOIN commission_conf_line_commission_scale_rel AS comun ON comun.commission_conf_line_id = ccl.id
                                        LEFT JOIN commission_scale AS cs ON cs.id = comun.commission_scale_id
                                        WHERE (%(total_invoice)s >= cs.sale_scale_from AND %(total_invoice)s <= cs.sale_scale_to)
                                        group by ccl.id) AS scale ON scale.commission = ccl.id
                            LEFT JOIN commission_scale AS cs ON cs.id = scale.scale
                    WHERE (
                        ccl.department_id = %(department)s AND
                        ccl.bill_calculation = %(calculation)s AND
                        (hc.employee_id in (%(seller)s, %(assigned)s) OR ccl.global_percentage > 0)
                    );
                """ % {
                "department": department,
                "seller": seller,
                "assigned": assigned,
                "calculation": calculation,
                "total_invoice": total_invoice,
            }
            self._cr.execute(query)
            return self._cr.dictfetchall()
