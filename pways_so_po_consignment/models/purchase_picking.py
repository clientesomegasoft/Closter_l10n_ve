from odoo import SUPERUSER_ID, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"  # pylint: disable=consider-merging-classes-inherited

    location_id = fields.Many2one("stock.location", "Location", copy=False)

    def _prepare_stock_moves(self, picking):
        res = super(__class__, self)._prepare_stock_moves(picking)
        if self.location_id:
            for val in res:
                val["location_dest_id"] = self.location_id and self.location_id.id
        return res


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"  # pylint: disable=consider-merging-classes-inherited

    def _get_location_picking(self, location_id):
        moves = self.picking_ids.mapped("move_lines").filtered(
            lambda x: x.location_id == location_id
        )
        return moves.mapped("picking_id").filtered(
            lambda x: x.state not in ("done", "cancel")
        )

    def _create_picking(self):
        StockPicking = self.env["stock.picking"]
        for order in self:
            if any(
                [
                    ptype in ["product", "consu"]
                    for ptype in order.order_line.mapped("product_id.type")
                ]
            ):
                pickings = order.picking_ids.filtered(
                    lambda x: x.state not in ("done", "cancel")
                )
                location_ids = order.order_line.mapped("location_id")
                if location_ids:
                    # continue
                    for location in location_ids:
                        pickings = order._get_location_picking(location)
                        if not pickings:
                            res = order._prepare_picking()
                            res["location_dest_id"] = location.id
                            picking = StockPicking.create(res)

                        else:
                            picking = pickings[0]
                        moves = order.order_line.filtered(
                            lambda x: x.location_id == location
                        )._create_stock_moves(picking)
                        moves = moves.filtered(
                            lambda x: x.state not in ("done", "cancel")
                        )._action_confirm()
                        seq = 0
                        for move in sorted(moves, key=lambda move: move.date):
                            seq += 5
                            move.sequence = seq
                        moves._action_assign()
                        picking.message_post_with_view(
                            "mail.message_origin_link",
                            values={"self": picking, "origin": order},
                            subtype_id=self.env.ref("mail.mt_note").id,
                        )
                else:
                    pickings = order.picking_ids.filtered(
                        lambda x: x.state not in ("done", "cancel")
                    )
                    if not pickings:
                        res = order._prepare_picking()
                        picking = StockPicking.with_user(SUPERUSER_ID).create(res)
                    else:
                        picking = pickings[0]
                    moves = order.order_line._create_stock_moves(picking)
                    moves = moves.filtered(
                        lambda x: x.state not in ("done", "cancel")
                    )._action_confirm()
                    seq = 0
                    for move in sorted(moves, key=lambda move: move.date):
                        seq += 5
                        move.sequence = seq
                    moves._action_assign()
                    picking.message_post_with_view(
                        "mail.message_origin_link",
                        values={"self": picking, "origin": order},
                        subtype_id=self.env.ref("mail.mt_note").id,
                    )
        return True
