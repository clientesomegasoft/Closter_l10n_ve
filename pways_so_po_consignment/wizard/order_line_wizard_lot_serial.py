from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError

class OrderLineWizardLotSerial(models.TransientModel):
    _name = 'order.line.wizard.lot.serial'
    _description = "Sale Order Create Wizard"

    line_id = fields.Many2one('order.line.wizard', string="Line Id")
    product_id = fields.Many2one('product.product', related="line_id.product_id")
    lot_producing_id = fields.Many2one('stock.lot', string='Lot/Serial Number')
    qty = fields.Float(string="QTY")
