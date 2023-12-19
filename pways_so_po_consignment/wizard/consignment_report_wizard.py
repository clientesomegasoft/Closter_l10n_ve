from odoo import models, fields, api, _
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

class ConsignmentReportWizard(models.TransientModel):
    _name = 'consignment.report.wizard'
    _description =" Consignment Purchase Report"

    report_type = fields.Selection([('consignment_details_report', 'Consignment Sale Report'), ('purchase_sale_report', 'Consignment Detail Report')], string="Report", default="consignment_details_report")
    consignment_account_id = fields.Many2one('account.analytic.account', string="Consignment Account")
    date_from = fields.Date(string='Date From', required=True, default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    date_to = fields.Date(string='Date To', required=True, default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))
    customer_ids = fields.Many2many('res.partner', string="Customers")
    product_ids = fields.Many2many('product.product', string="Product")

    def action_print_report(self):
        data = {
            'report_type': self.report_type,
            'consignment_account_id': self.consignment_account_id.id,
            'date_from' : self.date_from,
            'date_to' : self.date_to,
            'customer_ids': self.customer_ids.ids,
            'product_ids': self.product_ids.ids,
            }
        return self.env.ref('pways_so_po_consignment.consignment_report').report_action(self, data=data)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        if any(muster.date_from > muster.date_to for muster in self):
            raise ValidationError(_("Attendance Muster 'Date From' must be earlier 'Date To'."))

class ConsignmentTemplateReport(models.AbstractModel):
    _name = 'report.pways_so_po_consignment.consignments_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        consignment_account_id = self.env['account.analytic.account'].browse(data.get('consignment_account_id'))
        print(consignment_account_id, "consignment_account_id")
        report_type = data.get('report_type')
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        consignment_detailes_report = [] 
        consignment_header_report = []
        expenses_details = []
        if report_type == "consignment_details_report":
            sale_domain_consignment = [('is_consignments', '=', True), ('date_order', '>=', date_from),('date_order', '<=', date_to), ('state', '=', 'sale'), ('analytic_id', '=', consignment_account_id.id)]
            purchase_order_id = consignment_account_id.purchase_order_id
            sale_order_ids = self.env['sale.order'].search(sale_domain_consignment)
            sale_order_lines = sale_order_ids.mapped('order_line')
            purchase_order_lines = purchase_order_id.mapped('order_line')
            vendor_name = purchase_order_id.partner_id.name
            purchase_date = purchase_order_id.date_order
            consignment_name = consignment_account_id.name
            total_sale_amount = sum(sale_order_ids.mapped('amount_total'))
            commission_amount = (total_sale_amount * consignment_account_id.commission)/100
            consignment_lines = consignment_account_id.mapped('consignment_ids').filtered(lambda x:x.consignment_type == 'expense')
            expense_product_amount = sum(consignment_lines.mapped('unit_price'))
            total_expense = commission_amount + expense_product_amount
            paid_amount = total_sale_amount - total_expense
            expense_amount = sum(consignment_lines.mapped('unit_price'))
            for expense in consignment_lines:
                expenses_details.append({
                    'name': expense.product_id.name,
                    'unit_price': round(expense.unit_price, 2),
                    })
            for line in purchase_order_lines:
                sale_qty = sum(sale_order_lines.filtered(lambda x:x.product_id.id == line.product_id.id).mapped('product_uom_qty'))
                sale_total_price = sum(sale_order_lines.filtered(lambda x:x.product_id.id == line.product_id.id).mapped('price_subtotal'))
                consignment_detailes_report.append({
                'product_name': line.product_id.name,
                'purchase_qty': line.product_qty,
                'sale_qty': sale_qty,
                'purchase_price': round(line.price_subtotal,2),
                'sale_price': round(sale_total_price,2),
                'uom': line.product_uom.name,
                })
            consignment_header_report.append({
                'vendor_name': vendor_name,
                'sale_order_ids': ', '.join(sale.name for sale in sale_order_ids),
                'purchase_date': purchase_date,
                'consignment_name': consignment_name,
                'total_sale_amount': total_sale_amount,
                'commission_percentage': consignment_account_id.commission,
                'commission': round(commission_amount, 2),
                'total_expense': round(total_expense, 2),
                'paid_amount': round(paid_amount,2),
                'expenses_details': expenses_details,
                'expense_amount': round(expense_amount,2)
                })
        customer_ids = data.get('customer_ids')
        product_ids = data.get('product_ids')
        lines = []
        print("helllo", report_type)
        if report_type == "purchase_sale_report":
            print("nam__________")
            sale_domain = [('is_consignments', '=', True), ('date_order', '>=', date_from),('date_order', '<=', date_to), ('state', '=', 'sale')]
            if customer_ids:
                sale_domain.append(('partner_id', 'in', customer_ids))
            sale_ids = self.env['sale.order'].search(sale_domain)
            print(sale_ids, "sale_ids")
            for sale in sale_ids:
                order_line = self.env['sale.order.line']
                if product_ids:
                    order_line = sale.order_line.filtered(lambda x: x.product_id.id in product_ids)
                else:
                    order_line = sale.mapped('order_line')
                lines.append({
                    'sale': sale,
                    'name': sale.name,
                    'sale_ids': sale_ids,
                    'customer': sale.partner_id.name,
                    'analytic_id': sale.analytic_id.name,
                    'order_line': order_line,
                    'purchase_id': sale.analytic_id.purchase_order_id.name,
                })
                print(lines, "lines")
        return {
            'docs': docs,
            'company': self.env.company,
            'lines':lines,
            'consignment_detailes_report': consignment_detailes_report,
            'report_type': report_type,
            'date_from': date_from,
            'date_to': date_to,
            'consignment_header_report': consignment_header_report,
        }
