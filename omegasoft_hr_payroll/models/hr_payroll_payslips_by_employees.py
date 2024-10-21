from collections import defaultdict
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import format_date


class HrPayslipEmployees(models.TransientModel):
    _inherit = "hr.payslip.employees"

    department_ids = fields.Many2many(related="structure_id.department_ids")

    fortnight = fields.Selection(
        [
            ("first_fortnight", "First fortnight"),
            ("second_fortnight", "Second fortnight"),
        ],
        string="Fortnights",
        help="""Indicates whether the structure associated with
        the payroll is first or second fortnight""",
    )

    struct_fortnight = fields.Selection(related="structure_id.schedule_pay")

    @api.depends("structure_id", "department_id")
    def _compute_employee_ids(self):
        for wizard in self:
            domain = wizard._get_available_contracts_domain()

            if wizard.structure_id and not wizard.department_id:
                department = wizard.structure_id.department_ids.ids
            else:
                department = self.department_id.id

            domain = expression.AND(
                [domain, [("department_id", "child_of", department)]]
            )
            wizard.employee_ids = self.env["hr.employee"].search(domain)

    def compute_sheet(self):
        self.ensure_one()
        if not self.env.context.get("active_id"):
            from_date = fields.Date.to_date(self.env.context.get("default_date_start"))
            end_date = fields.Date.to_date(self.env.context.get("default_date_end"))
            today = fields.date.today()
            first_day = today + relativedelta(day=1)
            last_day = today + relativedelta(day=31)
            if from_date == first_day and end_date == last_day:
                batch_name = from_date.strftime("%B %Y")
            else:
                batch_name = _(
                    "From %(from_date)s to %(from_to)s",
                    from_date=format_date(self.env, from_date),
                    from_to=format_date(self.env, end_date),
                )
            payslip_run = self.env["hr.payslip.run"].create(
                {
                    "name": batch_name,
                    "date_start": from_date,
                    "date_end": end_date,
                }
            )
        else:
            payslip_run = self.env["hr.payslip.run"].browse(
                self.env.context.get("active_id")
            )

        employees = self.with_context(active_test=False).employee_ids
        if not employees:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))

        # Prevent a payslip_run from having multiple payslips for the same employee
        employees -= payslip_run.slip_ids.employee_id
        success_result = {
            "type": "ir.actions.act_window",
            "res_model": "hr.payslip.run",
            "views": [[False, "form"]],
            "res_id": payslip_run.id,
        }
        if not employees:
            return success_result

        payslips = self.env["hr.payslip"]
        Payslip = self.env["hr.payslip"]

        contracts = employees._get_contracts(
            payslip_run.date_start, payslip_run.date_end, states=["open", "close"]
        ).filtered(lambda c: c.active)
        date_start = datetime.combine(
            fields.Datetime.to_datetime(payslip_run.date_start), datetime.min.time()
        )
        date_stop = datetime.combine(
            fields.Datetime.to_datetime(payslip_run.date_end), datetime.max.time()
        )
        contracts._generate_work_entries(date_start, date_stop)
        work_entries = self.env["hr.work.entry"].search(
            [
                ("date_start", "<=", payslip_run.date_end),
                ("date_stop", ">=", payslip_run.date_start),
                ("employee_id", "in", employees.ids),
            ]
        )
        self._check_undefined_slots(work_entries, payslip_run)

        ##########################################################
        self.structure_id = payslip_run.struct_id.id
        ##########################################################

        if self.structure_id.type_id.default_struct_id == self.structure_id:
            work_entries = work_entries.filtered(
                lambda work_entry: work_entry.state != "validated"
            )
            if work_entries._check_if_error():
                work_entries_by_contract = defaultdict(
                    lambda: self.env["hr.work.entry"]
                )

                for work_entry in work_entries.filtered(
                    lambda w: w.state == "conflict"
                ):
                    work_entries_by_contract[work_entry.contract_id] |= work_entry

                for contract, work_entries in work_entries_by_contract.items():
                    conflicts = work_entries._to_intervals()
                    time_intervals_str = "\n - ".join(
                        ["", *[f"{s[0]} -> {s[1]}" for s in conflicts._items]]
                    )
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": _("Some work entries could not be validated."),
                        "message": _(
                            "Time intervals to look for:%s", time_intervals_str
                        ),
                        "sticky": False,
                    },
                }

        ##############################################################
        # payslip_run.write({
        #     'struct_id': self.structure_id.id,
        #     'fortnight': self.fortnight,
        #     'struct_fortnight': self.struct_fortnight
        # })
        # payslip_run._onchange_fortnight()

        # days = payslip_run._get_number_of_mondays_saturdays_sundays(
        #     payslip_run.date_start,payslip_run.date_end
        # )
        # payslip_run.number_of_mondays = days.get('number_of_mondays')
        # payslip_run.number_of_saturdays_sundays = days.get(
        #     'number_of_saturdays_sundays'
        # )
        ##############################################################

        default_values = Payslip.default_get(Payslip.fields_get())
        payslips_vals = []
        for contract in self._filter_contracts(contracts):
            values = dict(
                default_values,
                **{
                    "name": _("New Payslip"),
                    "employee_id": contract.employee_id.id,
                    # 'credit_note': payslip_run.credit_note,
                    "payslip_run_id": payslip_run.id,
                    "date_from": payslip_run.date_start,
                    "date_to": payslip_run.date_end,
                    "contract_id": contract.id,
                    "struct_id": self.structure_id.id
                    or contract.structure_type_id.default_struct_id.id,
                    ##############################################################
                    "rate_id": payslip_run.rate_id.id,
                    "rate_amount": payslip_run.rate_amount,
                    "number_of_mondays": payslip_run.number_of_mondays,
                    "number_of_saturdays_sundays": payslip_run.number_of_saturdays_sundays,
                    "fortnight": payslip_run.fortnight or False,
                    "struct_fortnight": payslip_run.struct_fortnight or False,
                    ##############################################################
                },
            )
            payslips_vals.append(values)
        payslips = Payslip.with_context(tracking_disable=True).create(payslips_vals)
        payslips._compute_name()
        payslips.compute_sheet()
        payslip_run.state = "verify"

        return success_result
