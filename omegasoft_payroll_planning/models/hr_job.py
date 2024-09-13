# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
import calendar
from odoo.tools.safe_eval import safe_eval

class HrJob(models.Model):
    _inherit = 'hr.job'

    rotating_job = fields.Boolean(string='Rotating job')