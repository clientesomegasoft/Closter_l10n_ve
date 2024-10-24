from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    consignment_location_id = fields.Many2one(
        "stock.location",
        domain="[('usage', '=', 'internal')]",
        string="Consignment Location",
    )
    consignment_rount_id = fields.Many2one("stock.route", string="Consignment Route")


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_confirm(self, merge=True, merge_into=False):
        stock_move = super(__class__, self)._action_confirm(
            merge=True, merge_into=False
        )
        for move in self.filtered(lambda x: x.sale_line_id.consignment_move_id):
            move_line_ids = []
            move.write(
                {"move_orig_ids": [(4, move.sale_line_id.consignment_move_id.id)]}
            )
            if move.move_line_ids:
                move.move_line_ids.unlink()
            for line in move.sale_line_id.line_lot_serial_ids:
                vals = (
                    0,
                    0,
                    {
                        "lot_id": line.lot_producing_id.id,
                        "qty_done": line.qty,
                        "product_id": line.product_id.id or False,
                        "product_uom_id": line.product_id.uom_id.id or False,
                        "location_id": (
                            line.line_id.order_id.warehouse_id.consignment_location_id.id
                        ),
                        "location_dest_id": self.location_dest_id.id,
                        "state": move.state,
                    },
                )
                move_line_ids.append(vals)
            move.move_line_ids = move_line_ids
        return stock_move
