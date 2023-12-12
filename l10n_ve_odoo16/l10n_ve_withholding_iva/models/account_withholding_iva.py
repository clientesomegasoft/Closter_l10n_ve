# -*- coding: utf-8 -*-

from odoo import models, fields, api, Command
from odoo.exceptions import UserError

class AccountWithholdingIVA(models.Model):
	_name = "account.withholding.iva"
	_description = "Retención de IVA"
	_order = "date desc, name desc, id desc"

	name = fields.Char(string='Numero de comprobante', default='NUMERO DE COMPROBANTE')
	type = fields.Selection([('customer', 'Retención IVA clientes'), ('supplier', 'Retención IVA proveedores')], required=True, readonly=True)
	state = fields.Selection([('draft', 'Borrador'), ('posted', 'Publicado'), ('cancel', 'Cancelado')], string='Estado', default='draft')
	invoice_id = fields.Many2one('account.move', string='Factura', required=True, readonly=True)
	agent_id = fields.Many2one('res.partner', string='Agente de retención', required=True, readonly=True)
	subject_id = fields.Many2one('res.partner', string='Sujeto retenido', required=True, readonly=True)
	iva_rate_id = fields.Many2one('withholding.iva.rate', string='Porcentaje de retención', required=True)
	date = fields.Date(string='Fecha de comprobante', required=True, readonly=True, states={'draft': [('readonly', False)]})
	invoice_date = fields.Date(related='invoice_id.invoice_date', string='Fecha factura')
	line_ids = fields.One2many('account.withholding.iva.line', 'withholding_iva_id', string='Lineas', readonly=True)
	exempt_amount = fields.Monetary(string='Monto exento')
	tax_base_amount = fields.Monetary(string='Base imponible', compute='_compute_amount', store=True)
	tax_amount = fields.Monetary(string='Impuesto', compute='_compute_amount', store=True)
	amount = fields.Monetary(string='Monto retenido', compute='_compute_amount', store=True)
	move_id = fields.Many2one('account.move', string='Asiento contable')
	journal_id = fields.Many2one('account.journal', string='Diario', required=True, readonly=True)
	withholding_account_id = fields.Many2one('account.account', string='Cuenta de retención', required=True)
	destination_account_id = fields.Many2one('account.account', string='Cuenta destino', required=True)
	txt_id = fields.Many2one('account.withholding.iva.txt', string='TXT IVA')
	txt_state = fields.Selection(related='txt_id.state', store=True)
	currency_id = fields.Many2one('res.currency', related='company_id.fiscal_currency_id', store=True)
	company_id = fields.Many2one('res.company', related='invoice_id.company_id', store=True)

	@api.depends('line_ids.tax_base_amount', 'line_ids.tax_amount', 'line_ids.amount')
	def _compute_amount(self):
		for withholding_iva_id in self:
			tax_base_amount = tax_amount = amount = 0.0
			for line in withholding_iva_id.line_ids:
				tax_base_amount += line.tax_base_amount
				tax_amount += line.tax_amount
				amount += line.amount
			withholding_iva_id.tax_base_amount = tax_base_amount
			withholding_iva_id.tax_amount = tax_amount
			withholding_iva_id.amount = amount

	def button_post(self):
		if not self.date:
			self.date = fields.Date.today()
		if self.type == 'supplier' and self.name == 'NUMERO DE COMPROBANTE':
			self.name = self.date.strftime('%Y%m') + self.env['ir.sequence'].with_company(self.company_id).next_by_code('account_withholding_iva')
		elif self.type == 'customer' and (not self.name or self.name == 'NUMERO DE COMPROBANTE'):
			raise UserError('El numero de comprobante es requerido.')

		values = self._prepare_move_values()
		if self.move_id:
			self.move_id.with_context(
				skip_invoice_sync=True, skip_account_move_synchronization=True, skip_compute_balance_ref=True
			).write(values)
		else:
			self.move_id = self.env['account.move'].with_context(
				skip_invoice_sync=True, skip_account_move_synchronization=True, skip_compute_balance_ref=True
			).create(values)

		self.move_id.with_context(skip_compute_balance_ref=True).action_post()

		# Reconcile.
		(self.move_id.line_ids + self.invoice_id.line_ids)\
		.filtered(lambda l: l.account_id.id == self.destination_account_id.id and not l.reconciled)\
		.with_context(no_exchange_difference=True)\
		.reconcile()

		self.write({'state': 'posted'})

	def button_send_mail(self):
		self.ensure_one()
		template_id = self.env.ref('l10n_ve_withholding_iva.mail_template_withholding_iva_receipt').id
		return {
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'mail.compose.message',
			'target': 'new',
			'context': {
				'default_model': 'account.withholding.iva',
				'default_res_id': self.id,
				'default_use_template': bool(template_id),
				'default_template_id': template_id,
				'default_composition_mode': 'comment',
				'default_email_layout_xmlid': 'mail.mail_notification_light',
			},
		}

	def button_draft(self):
		if self.txt_state == 'posted':
			raise UserError('No se puede restablecer a borrador una retención ya declarada.')
		if self.move_id:
			self.move_id.button_draft()
		self.write({'state': 'draft'})

	def button_cancel(self):
		if self.txt_state == 'posted':
			raise UserError('No se puede cancelar una retención ya declarada.')
		if self.move_id:
			if self.move_id.state == 'posted':
				self.move_id._reverse_moves([{
					'date': fields.Date.context_today(self),
					'ref': 'Reverso de: ' + self.move_id.name}],
					cancel=True
				)
			elif self.move_id.state == 'draft':
				self.move_id.button_cancel()
		self.invoice_id.withholding_iva_id = False
		self.write({'state': 'cancel'})

	def button_open_journal_entry(self):
		self.ensure_one()
		return {
			'name': 'Asiento',
			'type': 'ir.actions.act_window',
			'res_model': 'account.move',
			'context': {'create': False},
			'view_mode': 'form',
			'res_id': self.move_id.id,
		}

	def unlink(self):
		for withholding_iva_id in self:
			if withholding_iva_id.state != 'cancel':
				raise UserError('Solo retenciones en estado Cancelado pueden ser suprimidas.')
		return super().unlink()

	def _prepare_move_values(self):
		partner_id = self.agent_id if self.type == 'customer' else self.subject_id
		withholding_line, counterpart_line, writeoff_lines = self._seek_for_lines()
		sign = 1 if self.invoice_id.is_inbound() else -1
		iva_rate = self.iva_rate_id.name / 100

		amount_currency = balance = balance_ref = 0.0
		for line in self.line_ids:
			amount_currency += self.invoice_id.currency_id.round(line.base_amount_currency * iva_rate * sign)
			balance += self.company_id.currency_id.round(line.base_amount_company_currency * iva_rate * sign)
			balance_ref += self.company_id.currency_ref_id.round(line.base_amount_currency_ref * iva_rate * sign)

		move_line_values = [{
			'name': 'COMP. RET. IVA %s' % self.name,
			'partner_id': partner_id.id,
			'account_id': self.withholding_account_id.id,
			'amount_currency': amount_currency,
			'currency_id': self.invoice_id.currency_id.id,
			'balance': balance,
			'balance_ref': balance_ref,
		},{
			'name': 'COMP. RET. IVA %s' % self.name,
			'partner_id': partner_id.id,
			'account_id': self.destination_account_id.id,
			'amount_currency': -amount_currency,
			'currency_id': self.invoice_id.currency_id.id,
			'balance': -balance,
			'balance_ref': -balance_ref,
		}]
	
		line_ids_commands = [
			Command.update(withholding_line.id, move_line_values[0]) if withholding_line else Command.create(move_line_values[0]),
			Command.update(counterpart_line.id, move_line_values[1]) if counterpart_line else Command.create(move_line_values[1])
		]
		for line in writeoff_lines:
			line_ids_commands.append(Command.delete(line.id))

		return {
			'move_type': 'entry',
			'ref': self.invoice_id.name,
			'date': self.date,
			'journal_id': self.journal_id.id,
			'partner_id': partner_id.id,
			'currency_rate_ref': self.invoice_id.currency_rate_ref.id,
			'currency_id': self.invoice_id.currency_id.id,
			'company_id': self.company_id.id,
			'line_ids': line_ids_commands,
		}

	def _seek_for_lines(self):
		withholding_line = self.env['account.move.line']
		counterpart_line = self.env['account.move.line']
		writeoff_lines = self.env['account.move.line']
		for line in self.move_id.line_ids:
			if line.account_id == self.withholding_account_id:
				withholding_line |= line
			elif line.account_id == self.destination_account_id:
				counterpart_line |= line
			else:
				writeoff_lines |= line
		return withholding_line, counterpart_line, writeoff_lines


class AccountWithholdingIVALine(models.Model):
	_name = "account.withholding.iva.line"
	_description = "Lineas de retencion de IVA"
	
	withholding_iva_id = fields.Many2one('account.withholding.iva', ondelete='cascade', required=True)
	tax_line_id = fields.Many2one('account.tax', string='Impuesto', required=True)
	tax_base_amount = fields.Monetary(string='Base imponible')
	tax_amount = fields.Monetary(string='Monto impuesto')
	amount = fields.Monetary(string='Monto retenido', compute='_compute_amount', store=True)
	base_amount_currency = fields.Float()
	base_amount_company_currency = fields.Float()
	base_amount_currency_ref = fields.Float()
	currency_id = fields.Many2one('res.currency', related='company_id.fiscal_currency_id', store=True)
	company_id = fields.Many2one('res.company', related='withholding_iva_id.company_id', store=True)

	@api.depends('tax_amount', 'withholding_iva_id.iva_rate_id')
	def _compute_amount(self):
		for line in self:
			line.amount = line.currency_id.round(line.tax_amount * line.withholding_iva_id.iva_rate_id.name / 100)