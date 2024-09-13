# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
import logging
import pytz

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import format_date

_logger = logging.getLogger(__name__)

class HrAppraisal(models.Model):
    _inherit = "hr.appraisal"

    organizational_units_id = fields.Many2one(
        'hr.organizational.units', string='organizational units', related='employee_id.organizational_units_id')