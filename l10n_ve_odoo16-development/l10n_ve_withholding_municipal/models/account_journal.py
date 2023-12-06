# -*- coding: utf-8 -*-

from odoo import fields, models

class AccountJournal(models.Model):
	_inherit = "account.journal"

	withholding_journal_type = fields.Selection(selection_add=[('municipal', 'Municipal')])