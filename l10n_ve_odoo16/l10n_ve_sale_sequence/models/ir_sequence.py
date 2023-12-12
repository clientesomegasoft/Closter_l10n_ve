# -*- coding: utf-8 -*-

from odoo import fields, models

class IrSequence(models.Model):
	_inherit = "ir.sequence"

	serie = fields.Char(string='Serie')
	nro_ctrl_journal_ids = fields.One2many('account.journal', 'nro_ctrl_sequence_id', string='Diarios de número de control')
	invoice_name_journal_ids = fields.One2many('account.journal', 'invoice_name_sequence_id', string='Diarios de factura')