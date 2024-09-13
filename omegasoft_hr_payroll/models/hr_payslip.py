# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
from odoo.tools import float_compare, float_is_zero, plaintext2html
from dateutil.relativedelta import relativedelta, MO
from datetime import datetime, date, timedelta
import calendar
import time
from collections import defaultdict
from markupsafe import Markup
from calendar import monthrange

class HrPayslip(models.Model):
    _name = 'hr.payslip'
    _inherit = ['hr.payslip', 'mail.thread', 'mail.activity.mixin']

    rate_id = fields.Many2one('res.currency.rate', string='Rate', tracking=True, default=lambda self: self.env.company.currency_ref_id.rate_ids.filtered(lambda aml: aml.is_payroll_rate).sorted('name')[-1], domain="[('currency_id', '=', currency_ref_id), ('is_payroll_rate', '=', True)]")
    
    payroll_structure_for_rate = fields.Many2many(related='company_id.payroll_structure_for_rate')
    structure_for_rate = fields.Boolean(default=False)
    rate_amount = fields.Float(string="Rate amount", tracking=True)
    company_currency = fields.Many2one(comodel_name='res.currency', default=lambda self: self.env.company.currency_id, tracking=True)
    currency_id = fields.Many2one(related='struct_id.currency_id')

    fortnight = fields.Selection([('first_fortnight', 'First fortnight'), ('second_fortnight', 'Second fortnight')], 
        string="Fortnights", help="Indicates whether the structure associated with the payroll is first or second fortnight", tracking=True)

    struct_fortnight = fields.Selection(related='struct_id.schedule_pay')
    schedule_pay_contract = fields.Selection(related='contract_id.structure_type_id.default_schedule_pay')
    
    number_of_mondays = fields.Float(string='Number of Mondays', help="Number of Mondays in the selected period.", default=0, tracking=True)

    number_of_saturdays_sundays = fields.Float(string='Number of Saturdays and Sundays', help="Number of Saturdays and Sundays in the period selected ", default=0, tracking=True)

    email_state = fields.Selection([
        ('outgoing', 'Outgoing'),
        ('sent', 'Sent'),
        ('received', 'Received'),
        ('exception', 'Delivery Failed'),
        ('cancel', 'Cancelled'),
    ], 'Email Status', default='outgoing')
    
    structures_for_utility_resets = fields.Many2many(related='company_id.structures_for_utility_resets')
    structure_for_resets_labor_liabilities = fields.Many2many(related='company_id.structure_for_resets_labor_liabilities')
    payroll_structure_for_profits = fields.Many2many(related='company_id.payroll_structure_for_profits')
    wage_type_contract = fields.Selection(related="employee_id.wage_type")
    average_wage = fields.Monetary(related="employee_id.average_wage", string="Average wage")
    use_average_wage = fields.Boolean(related="struct_id.use_average_wage")
    week_number = fields.Integer('number of week', default=False)
    complementary_payroll = fields.Boolean(related="struct_id.complementary_payroll")
    
    @api.constrains('name','struct_id')
    def _constrains_average_wage(self):
        for record in self:     
            if record.average_wage <= 0 and record.struct_id.use_average_wage:
                raise UserError('El calculo del promedio debe ser mayor a cero')
    
    @api.onchange('struct_id')
    def _check_fields_structure_for_rate(self):     
        self.structure_for_rate = True if self.struct_id.id in self.payroll_structure_for_rate.ids else False

    @api.onchange('rate_id')
    def _rate_onchange(self):
        if self.rate_id:
            self.rate_amount = self.rate_id.inverse_company_rate
        else:
            self.rate_amount = 0

    @api.onchange('name','date_from','date_to')
    def _onchange_number_of_mondays_saturdays_sundays(self):
        if self.name:
            days = self._get_number_of_mondays_saturdays_sundays(self.date_from, self.date_to)
            self.number_of_mondays = days.get('number_of_mondays')
            self.number_of_saturdays_sundays = days.get('number_of_saturdays_sundays')
            
    @api.onchange('name','struct_id','date_from','date_to')
    def _onchange_number_of_week(self):
        if self.name and self.struct_id and self.contract_id.structure_type_id.default_schedule_pay == 'weekly':
            self.week_number = self.date_to.isocalendar()[1] if self.date_to.isocalendar()[1] == self.date_from.isocalendar()[1]\
                and self.date_to > self.date_from else False
    
    @api.onchange('week_number')
    def _onchange_date_week(self):
        if self.date_to > self.date_from and self.name and self.struct_id and self.contract_id.structure_type_id.default_schedule_pay == 'weekly':
            self.date_from = datetime(1997,1,1)+relativedelta(weekday=MO(-1), weeks= int(self.week_number), year=self.date_from.year)
            self.date_to = self.date_from+relativedelta(days=6)
    
    def _get_number_of_mondays_saturdays_sundays(self, start_of_period, end_of_period):
        """
            Receives a date range (start_of_period and end_of_period) 
            and calculates the number of Mondays, Saturdays and Sundays within the range.
        """

        number_of_mondays = 0
        number_of_saturdays_sundays = 0

        if start_of_period.month == end_of_period.month:
            """
                The start and end of the payroll period are in the same month.
            """
            num_days = monthrange(start_of_period.year, start_of_period.month)
            for dia in range(start_of_period.day, end_of_period.day + 1):
                if(datetime(start_of_period.year, start_of_period.month, dia).weekday() == 0):
                    number_of_mondays += 1
                if(datetime(start_of_period.year, start_of_period.month, dia).weekday() in [5, 6]):
                    number_of_saturdays_sundays += 1
                
                if(dia == 30 and num_days[1] > 30 and end_of_period.day == 30 ):
                    if(datetime(start_of_period.year, start_of_period.month, 31).weekday() == 0):
                        number_of_mondays += 1
                
        elif end_of_period.month > start_of_period.month:
            """
                The payroll start and end periods have different months.
            """

            day_month = calendar.monthrange(
                start_of_period.year, start_of_period.month)[1]

            for dia in range(start_of_period.day, day_month + 1):
                if(datetime(start_of_period.year, start_of_period.month, dia).weekday() == 0):
                    number_of_mondays += 1
                if(datetime(start_of_period.year, start_of_period.month, dia).weekday() in [5, 6]):
                    number_of_saturdays_sundays += 1

            for dia in range(1, end_of_period.day + 1):
                if(datetime(end_of_period.year, end_of_period.month, dia).weekday() == 0):
                    number_of_mondays += 1
                if(datetime(end_of_period.year, end_of_period.month, dia).weekday() in [5, 6]):
                    number_of_saturdays_sundays += 1

        return {'number_of_mondays': number_of_mondays, 'number_of_saturdays_sundays': number_of_saturdays_sundays}

    @api.onchange('struct_id','fortnight')
    def _onchange_fortnight(self):
        today = fields.Date.today()
        
        for record in self:
            if record.struct_id and record.struct_id.schedule_pay != 'bi-weekly':
                record.date_from = date(today.year, today.month, 1)
                record.date_to = fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date())
                if record.fortnight:
                    record.fortnight = False
            elif record.fortnight:
                if record.fortnight == 'first_fortnight':
                    record.date_from = date(today.year, today.month, 1)
                    record.date_to = date(today.year, today.month, 15)
                elif record.fortnight == 'second_fortnight':
                    record.date_from = date(today.year, today.month, 16)
                    record.date_to = fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date())
                    if record.date_to.day == 31:
                        record.date_to = record.date_to + relativedelta(days=-1)

    def get_today(self):
        return fields.Date.today()

    def action_send_payslip_by_email(self):
        mapped_reports = self._get_pdf_reports()
        generic_name = _("Payslip")
        template = self.env.ref('omegasoft_hr_payroll.mail_template_new_payslip_custom_omegasoft', raise_if_not_found=False)

        for report, payslips in mapped_reports.items():
            for payslip in payslips:
                attachments_vals_list = []
                pdf_content, dummy = report.sudo()._render_qweb_pdf(report.id, payslip.id)
                if report.print_report_name:
                    pdf_name = safe_eval(report.print_report_name, {'object': payslip})
                else:
                    pdf_name = generic_name
                attachments_vals_list.append({
                    'name': pdf_name,
                    'type': 'binary',
                    'raw': pdf_content,
                    'res_model': payslip._name,
                    'res_id': payslip.id
                })
                # Send email to employees
                if template:
                    data_id = self.env['ir.attachment'].sudo().create(attachments_vals_list)
                    template.attachment_ids = [(6, 0, [data_id.id])]
                    #################################################
                    template.send_mail_template(payslip.id, payslip, force_send=True)
                    #################################################
                    template.attachment_ids = [(3, data_id.id)]

    def _compute_basic_net(self):
        for payslip in self:
            #
            #rules BAS7
            codes_basic = self.env.company.salary_rules_for_basic.filtered(lambda struct: struct.struct_id.id == payslip.struct_id.id).mapped('code') if self.env.company.salary_rules_for_basic else []

            #rules NET
            codes_net = self.env.company.salary_rules_for_net.filtered(lambda struct: struct.struct_id.id == payslip.struct_id.id).mapped('code') if self.env.company.salary_rules_for_net else []
            codes = []
            
            if codes_basic and codes_net:
                codes = codes_basic + codes_net
            elif codes_basic:
                codes = codes_basic
            elif codes_net:
                codes = codes_net

            if 'BASIC' not in codes:
                codes.append('BASIC')
            if 'NET' not in codes:
                codes.append('NET')

            line_values = (payslip._origin)._get_line_values(codes)
            #
            
            if codes_basic:
                payslip.basic_wage = 0
                for code in codes_basic:
                    payslip.basic_wage += line_values[code][payslip._origin.id]['total']
            else:
                payslip.basic_wage = line_values['BASIC'][payslip._origin.id]['total']
            
            if codes_net:
                payslip.net_wage = 0
                for code in codes_net:
                    payslip.net_wage += line_values[code][payslip._origin.id]['total']
            else:
                payslip.net_wage = line_values['NET'][payslip._origin.id]['total']


    def _compute_earnings_generated(self, is_payslip_cancel=False):
        structures_for_profits = self.env.company.payroll_structure_for_profits.ids if self.env.company.payroll_structure_for_profits else []
        categories_for_profits = self.env.company.salary_rules_categories_for_profits.mapped('code') if self.env.company.salary_rules_categories_for_profits else []
        for record in self:
            if record.struct_id.id in structures_for_profits:
                profits = sum(item.total for item in record.line_ids.filtered(lambda x: x.category_id.code in categories_for_profits))
                total_profits = profits * ((record.env.company.days_of_profit or 0) / 360)
                if not is_payslip_cancel:
                    record.contract_id.earnings_generated += total_profits
                else:
                    record.contract_id.earnings_generated -= total_profits if record.contract_id.earnings_generated > 0 else 0 
                record.contract_id.earnings_generated_total_available = record.contract_id.earnings_generated - record.contract_id.advances_granted
            else:
                pass

    def _compute_profits_resets(self, is_payslip_cancel=False):
        structures_for_profits_resets = self.env.company.structures_for_utility_resets.ids if self.env.company.structures_for_utility_resets else []
        for record in self:
            if not is_payslip_cancel and record.struct_id.id in structures_for_profits_resets:
                record.contract_id.earnings_generated_previous_amount = record.contract_id.earnings_generated
                record.contract_id.advances_granted_previous_amount = record.contract_id.advances_granted
                
                record.contract_id.earnings_generated = 0
                record.contract_id.advances_granted = 0
                record.contract_id.earnings_generated_total_available = 0
                record.contract_id.recent_resets = record.date_from
            elif is_payslip_cancel and record.struct_id.id in structures_for_profits_resets:
                record.contract_id.earnings_generated = record.contract_id.earnings_generated_previous_amount
                record.contract_id.advances_granted = record.contract_id.advances_granted_previous_amount
                record.contract_id.earnings_generated_total_available = record.contract_id.earnings_generated - record.contract_id.advances_granted
                
                payslip_obj = self.env['hr.payslip'].search(
                [('employee_id', '=', record.employee_id.id), ('state', 'in', ['done', 'paid']),('struct_id', 'in', structures_for_profits_resets)], order="create_date desc")
                previous_resets = False
                for payslib in payslip_obj:
                    if not previous_resets and payslib.struct_id.id in structures_for_profits_resets and record.id != payslib.id:
                        record.contract_id.recent_resets = payslib.date_from
                        previous_resets = True
                if not previous_resets:
                    record.contract_id.recent_resets = None
                    
                
    def _compute_vacations_resets(self, is_payslip_cancel=False):
        structures_for_vacations_resets = self.env.company.structures_for_utility_resets.ids if self.env.company.structures_for_utility_resets else []
        for record in self:
            if not is_payslip_cancel and record.struct_id.id in structures_for_vacations_resets:
                record.contract_id.vacations_advances_granted_previous_amount = record.contract_id.vacations_advances_granted

                record.contract_id.vacations_advances_granted = 0
            elif is_payslip_cancel and record.struct_id.id in structures_for_vacations_resets:
                record.contract_id.vacations_advances_granted = record.contract_id.vacations_advances_granted_previous_amount

    def _compute_social_benefits_resets(self, is_payslip_cancel=False):
        structure_for_resets_labor_liabilities = self.env.company.structure_for_resets_labor_liabilities.ids if self.env.company.structure_for_resets_labor_liabilities else []
        for record in self:
            if not is_payslip_cancel and record.struct_id.id in structure_for_resets_labor_liabilities:
                record.contract_id.social_benefits_generated_previous_amount = record.contract_id.social_benefits_generated
                record.contract_id.accrued_social_benefits_previous_amount = record.contract_id.accrued_social_benefits
                record.contract_id.advances_of_social_benefits_previous_amount = record.contract_id.advances_of_social_benefits
                
                record.contract_id.benefit_interest_previous_amount = record.contract_id.benefit_interest
                record.contract_id.days_per_year_accumulated_previous_amount = record.contract_id.days_per_year_accumulated
                
                record.contract_id.social_benefits_generated = 0
                record.contract_id.accrued_social_benefits = 0
                record.contract_id.advances_of_social_benefits = 0
                record.contract_id.total_available_social_benefits_generated = 0

                record.contract_id.benefit_interest = 0
                record.contract_id.days_per_year_accumulated = 0
            elif is_payslip_cancel and record.struct_id.id in structure_for_resets_labor_liabilities:
                record.contract_id.benefit_interest = record.contract_id.benefit_interest_previous_amount
                record.contract_id.days_per_year_accumulated = record.contract_id.days_per_year_accumulated_previous_amount

                record.contract_id.social_benefits_generated = record.contract_id.social_benefits_generated_previous_amount
                record.contract_id.accrued_social_benefits = record.contract_id.accrued_social_benefits_previous_amount
                record.contract_id.advances_of_social_benefits = record.contract_id.advances_of_social_benefits_previous_amount
                record.contract_id.total_available_social_benefits_generated = (record.contract_id.social_benefits_generated + record.contract_id.accrued_social_benefits) - record.contract_id.advances_of_social_benefits

    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()
        self._compute_earnings_generated()
        self._compute_profits_resets()
        self._compute_vacations_resets()
        self._compute_social_benefits_resets()
        return res

    def action_payslip_cancel(self):
        for record in self:
            if(record.move_id.state in ['posted']):
                name = record.name
                raise UserError(_("No se puede llevar a borrardor una nomina con asientos publicados: \n"
                                "%(name)s",
                                name = name))
            else:
                record._check_payroll()
                record._compute_earnings_generated(True)
                record._compute_profits_resets(True)
                record._compute_vacations_resets(True)
                record._compute_social_benefits_resets(True)
        return super(HrPayslip, self).action_payslip_cancel()
        
    def _check_payroll(self):
        if(self.struct_id and self.payroll_structure_for_profits and self.struct_id.id in self.payroll_structure_for_profits.ids):
            if(self.contract_id.recent_resets and self.contract_id.recent_resets >= self.date_from):
                raise ValidationError(
                        _("Tiene un pago de utilidades en estado pagado o realizado"))
            
    def action_payslip_paid(self):
        if any(move.state != 'posted' for move in self.move_id):
            raise UserError('No se puede marcar la nómina como pagada si el asiento contable no esta publicado.')
        return super(HrPayslip, self).action_payslip_paid()
    
    def _action_create_account_move(self):
        precision = self.env['decimal.precision'].precision_get('Payroll')

        # Add payslip without run
        payslips_to_post = self.filtered(lambda slip: not slip.payslip_run_id)

        # Adding pay slips from a batch and deleting pay slips with a batch that is not ready for validation.
        payslip_runs = (self - payslips_to_post).mapped('payslip_run_id')
        for run in payslip_runs:
            if run._are_payslips_ready():
                payslips_to_post |= run.slip_ids

        # A payslip need to have a done state and not an accounting move.
        payslips_to_post = payslips_to_post.filtered(lambda slip: slip.state == 'done' and not slip.move_id)

        # Check that a journal exists on all the structures
        if any(not payslip.struct_id for payslip in payslips_to_post):
            raise ValidationError(_('One of the contract for these payslips has no structure type.'))
        if any(not structure.journal_id for structure in payslips_to_post.mapped('struct_id')):
            raise ValidationError(_('One of the payroll structures has no account journal defined on it.'))

        # Map all payslips by structure journal and pay slips month.
        # {'journal_id': {'month': [slip_ids]}}
        slip_mapped_data = defaultdict(lambda: defaultdict(lambda: self.env['hr.payslip']))
        for slip in payslips_to_post:
            slip_mapped_data[slip.struct_id.journal_id.id][fields.Date().end_of(slip.date_to, 'month')] |= slip
        for journal_id in slip_mapped_data: # For each journal_id.
            for slip_date in slip_mapped_data[journal_id]: # For each month.
                line_ids = []
                debit_sum = 0.0
                credit_sum = 0.0
                date = slip_date
                move_dict = {
                    'narration': '',
                    'ref': date.strftime('%B %Y'),
                    'journal_id': journal_id,
                    'date': date,
                }

                for slip in slip_mapped_data[journal_id][slip_date]:
                    move_dict['narration'] += plaintext2html(slip.number or '' + ' - ' + slip.employee_id.name or '')
                    move_dict['narration'] += Markup('<br/>')
                    move_dict['currency_id'] = slip.currency_id.id
                    move_dict['currency_rate_ref'] = slip.rate_id.id if slip.rate_id else self.env['res.currency.rate'].sudo().search([('is_payroll_rate', '=', True)],limit=1).id 
                    
                    slip_lines = slip._prepare_slip_lines(date, line_ids)
                    line_ids.extend(slip_lines)

                for line_id in line_ids: # Get the debit and credit sum.
                    debit_sum += line_id['debit']
                    credit_sum += line_id['credit']

                # The code below is called if there is an error in the balance between credit and debit sum.
                if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                    slip._prepare_adjust_line(line_ids, 'credit', debit_sum, credit_sum, date)
                elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                    slip._prepare_adjust_line(line_ids, 'debit', debit_sum, credit_sum, date)

                # Add accounting lines in the move
                move_dict['line_ids'] = [(0, 0, line_vals) for line_vals in line_ids]
                move = self._create_account_move(move_dict)
                for slip in slip_mapped_data[journal_id][slip_date]:
                    slip.write({'move_id': move.id, 'date': date})
        return True
    
    def _prepare_line_values(self, line, account_id, date, debit, credit):
        debit_ref = debit
        credit_ref = credit
        date_ref = date
        if self.currency_id != self.company_id.currency_id:
            date_ref = self.rate_id.name if self.rate_id else self.env['res.currency.rate'].sudo().search([('is_payroll_rate', '=', True)],limit=1).name
            debit_ref = self.currency_id._convert(debit, self.company_id.currency_id, self.company_id, date_ref)
            credit_ref = self.currency_id._convert(credit, self.company_id.currency_id, self.company_id, date_ref)
        res = super(HrPayslip, self)._prepare_line_values(line, account_id, date_ref, debit_ref, credit_ref)
        
        res.update({
            'currency_id': self.currency_id.id,
            'amount_currency': debit - credit,
        })
        
        return res