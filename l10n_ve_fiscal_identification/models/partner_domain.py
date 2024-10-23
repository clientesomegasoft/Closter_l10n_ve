from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_id = fields.Many2one(
        domain="[('type', '!=', 'private'), ('company_id', 'in', (False, company_id)), ('partner_type', 'in', ('customer', 'customer_supplier'))]"  # noqa: B950
    )


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    partner_id = fields.Many2one(
        domain="[('type', '!=', 'private'), ('company_id', 'in', (False, company_id)), ('partner_type', 'in', ('supplier', 'customer_supplier'))]"  # noqa: B950
    )


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_partner_domain(self):
        move_type = self._context.get("default_move_type", "entry")
        if move_type in self.get_sale_types(include_receipts=True):
            partner_type = ", ('partner_type', 'in', ('customer', 'customer_supplier'))"
        elif move_type in self.get_purchase_types(include_receipts=True):
            partner_type = ", ('partner_type', 'in', ('supplier', 'customer_supplier'))"
        else:
            partner_type = ""
        return (
            "[('type', '!=', 'private'), ('company_id', 'in', (False, company_id)) %s]"
            % partner_type
        )

    partner_id = fields.Many2one(domain=_get_partner_domain)


class AccountPaymentInnerit(models.Model):
    _inherit = "account.payment"

    def _get_partner_domain(self):
        default_partner_type = self._context.get("default_partner_type")
        if default_partner_type == "customer":
            partner_type = ", ('partner_type', 'in', ('customer', 'customer_supplier'))"
        elif default_partner_type == "supplier":
            partner_type = ", ('partner_type', 'in', ('supplier', 'customer_supplier'))"
        else:
            partner_type = ""
        return (
            "['|', ('parent_id', '=', False), ('is_company', '=', True) %s]"
            % partner_type
        )

    partner_id = fields.Many2one(domain=_get_partner_domain)
