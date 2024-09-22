from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class HrContractAllocationLine(models.Model):
    _name = "contract_allocation_lines"
    _description = "Endowment lines"
    _order = "date_delivered desc, state desc"

    employee_id = fields.Many2one(
        comodel_name="hr.employee", string="Employee", ondelete="restrict"
    )

    employee_ids = fields.Many2many(related="allocation_id.employee_ids")

    product_id = fields.Many2one(
        string="Product",
        comodel_name="product.product",
        ondelete="restrict",
    )

    allocation_id = fields.Many2one(
        string="Allocation",
        comodel_name="contract_allocation",
        ondelete="restrict",
    )

    size_id = fields.Many2one(
        string="Size",
        comodel_name="contract_allocation_size",
        ondelete="restrict",
    )

    allocated_quantity = fields.Float(string="Allocated quantity", default=0)

    frequency = fields.Integer(string="Frequency", default=0)

    delivery_frequency = fields.Selection(
        string="Delivery frequency",
        selection=[("days", "Days"), ("monthly", "Monthly"), ("annual", "Annual")],
        default="monthly",
    )

    # Delivery

    delivered_each = fields.Char(string="Each", default="cada")

    quantity_delivered = fields.Float(string="Quantity delivered", default=0)

    quantity_to_deliver = fields.Float(
        string="Quantity to deliver", compute="_compute_allocated_quantity", store=True
    )

    date_delivered = fields.Date(string="Date delivered")

    is_delivered = fields.Boolean(compute="_compute_is_delivered", store=True)

    state = fields.Selection(
        selection=[
            ("draft", "To be delivered"),
            ("partial_delivery", "Partial delivery"),
            ("delivered", "Delivered"),
        ],
        string="Status",
        required=True,
        readonly=True,
        copy=False,
        default="draft",
    )

    @api.onchange("date_delivered")
    def _onchange_date_delivered(self):
        if self.quantity_delivered <= 0 and self.date_delivered:
            raise ValidationError("La Cantidad entregada debe ser mayor a cero")

    def write(self, vals):
        return super(__class__, self).write(vals)

    @api.onchange("allocated_quantity")
    def _onchange_allocated_quantity(self):
        for record in self:
            if record.allocated_quantity < record.quantity_delivered:
                raise UserError(
                    "La cantidad asignada no puede ser "
                    "menor que de la cantidad entregada."
                )

    @api.onchange("quantity_delivered")
    def _onchange_quantity_delivered(self):
        for record in self:
            if record.quantity_delivered > record.allocated_quantity:
                raise UserError("No puede entregar más de la cantidad asignada.")
            elif record.allocated_quantity and record.quantity_delivered:
                record.quantity_to_deliver = (
                    record.allocated_quantity - record.quantity_delivered
                )
            else:
                record.quantity_to_deliver = record.allocated_quantity

    @api.depends("allocated_quantity", "quantity_delivered", "date_delivered")
    def _compute_allocated_quantity(self):
        for record in self:
            if (
                record.allocated_quantity
                and record.quantity_delivered
                and record.date_delivered
            ):
                record.quantity_to_deliver = (
                    record.allocated_quantity - record.quantity_delivered
                )
            else:
                record.quantity_to_deliver = record.allocated_quantity

    @api.depends("quantity_to_deliver", "date_delivered")
    def _compute_is_delivered(self):
        for record in self:
            record.is_delivered = (
                True
                if record.quantity_to_deliver == 0 and record.date_delivered
                else False
            )
            if record.quantity_delivered == 0:
                record.state = "draft"
            elif record.is_delivered:
                record.state = "delivered"
            else:
                record.state = "partial_delivery"

    # employee file code

    employee_file = fields.Boolean(
        "Employee file", related="allocation_id.company_id.employee_file"
    )
    employee_file_code_id = fields.Many2one(
        "employee.file.code", string="Employee File", ondelete="set null"
    )

    @api.onchange("employee_file_code_id")
    def _onchange_employee_file_code_id(self):
        if self.employee_file:
            if (
                self.employee_file_code_id
                and self.employee_file_code_id != self.employee_id.employee_file_code_id
            ):
                self.employee_id = self.employee_file_code_id.employee_id
            elif not self.employee_file_code_id and self.employee_id:
                self.employee_id = False

    @api.onchange("employee_id")
    def _onchange_employee(self):
        if self.employee_file:
            if (
                self.employee_id
                and self.employee_file_code_id != self.employee_id.employee_file_code_id
            ):
                self.employee_file_code_id = self.employee_id.employee_file_code_id
            elif not self.employee_id and self.employee_file_code_id:
                self.employee_file_code_id = False

    @api.constrains("employee_file_code_id")
    def _constrains_employee_file_code_id(self):
        if self.employee_file:
            if not self._context.get("bypass", False):
                if (
                    self.employee_file_code_id
                    and self.employee_file_code_id
                    != self.employee_id.employee_file_code_id
                ):
                    self.employee_id = self.employee_file_code_id.employee_id
                elif not self.employee_file_code_id and self.employee_id:
                    self.employee_id = False

    @api.constrains("employee_id")
    def _constrains_employee(self):
        if self.employee_file:
            if (
                self.employee_id
                and self.employee_file_code_id != self.employee_id.employee_file_code_id
            ):
                self.employee_file_code_id = self.employee_id.employee_file_code_id
            elif not self.employee_id and self.employee_file_code_id:
                self.employee_file_code_id = False

    # employee file code
