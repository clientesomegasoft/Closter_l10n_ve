from odoo import fields, models


class HrWorkEntryType(models.Model):
    _inherit = "hr.work.entry.type"

    planning_slot_template_ids = fields.Many2many(
        comodel_name="planning.slot.template",
        relation="hr_work_entry_type_planning_slot_template",
        string="Slot template",
    )


class HrWorkEntry(models.Model):
    _inherit = "hr.work.entry"

    planning_slot_id = fields.Many2one(
        comodel_name="planning.slot", string="Planning Slot"
    )
