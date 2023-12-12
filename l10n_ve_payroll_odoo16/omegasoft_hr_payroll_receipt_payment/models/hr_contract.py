# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class Contract(models.Model):
    _inherit = 'hr.contract'

    def _get_contract_wage_field(self):
        res = super(Contract, self)._get_contract_wage_field()
        res = 'hourly_wage' if self.wage_type == 'hourly' else 'wage'
        return res
