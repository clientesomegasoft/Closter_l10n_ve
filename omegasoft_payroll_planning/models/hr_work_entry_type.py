# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from odoo.tools.safe_eval import safe_eval

class HrWorkEntryType(models.Model):
    _inherit = 'hr.work.entry.type'

    planning_slot_template_ids = fields.Many2many(comodel_name='planning.slot.template', relation='hr_work_entry_type_planning_slot_template', string='Slot template')

class HrWorkEntry(models.Model):
    _inherit = 'hr.work.entry'

    planning_slot_id = fields.Many2one(comodel_name='planning.slot', string='Planning Slot')