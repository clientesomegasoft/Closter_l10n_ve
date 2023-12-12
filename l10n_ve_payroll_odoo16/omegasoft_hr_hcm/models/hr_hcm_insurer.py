# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrHCMInsurer(models.Model):
    _name        = 'hr.hcm.insurer'
    _description = 'Insurer'

    name = fields.Char(
        'Name',
        required = True)
