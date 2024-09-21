from odoo import api, fields, models


class PlanningSlot(models.Model):
    _inherit = "planning.slot"

    work_shifts_id = fields.Many2one(
        comodel_name="work.shifts",
        string="Shift name",
        ondelete="restrict",
        readonly=True,
    )

    @api.onchange("resource_id")
    def get_domain_resource_id(self):
        roles = self.env["planning.role"].search([]).ids
        domain = {"domain": {"role_id": [("id", "in", roles)]}}
        if self.resource_id:
            domain = {
                "domain": {
                    "role_id": [
                        ("id", "in", self.resource_id.employee_id.planning_role_ids.ids)
                    ]
                }
            }
        return domain

    @api.onchange("role_id")
    def get_domain_role_id(self):
        resources = self.env["resource.resource"].search([]).ids
        domain = {"domain": {"resource_id": [("id", "in", resources)]}}
        if self.role_id:
            domain = {
                "domain": {
                    "resource_id": [
                        ("employee_id", "in", self.role_id.resource_ids.ids)
                    ]
                }
            }
        return domain

    @api.model_create_multi
    def create(self, vals_list):
        res = super(__class__, self).create(vals_list)
        if vals_list:
            for record in res:
                hr_work_entry = []
                employee_id = self.env["hr.employee"].search(
                    [("id", "=", record.resource_id.employee_id.id)]
                )

                if employee_id.filtered(
                    lambda employee: employee.contract_id.state in ["open"]
                ):
                    work_entry_type_id = self.env["hr.work.entry.type"].search(
                        [
                            ("id", "=", record.template_id.work_entry_type_id.id),
                            (
                                "planning_slot_template_ids",
                                "in",
                                record.template_id.ids,
                            ),
                        ]
                    )
                    work_entry_type_attendance = self.env.ref(
                        "hr_work_entry.work_entry_type_attendance",
                        raise_if_not_found=False,
                    )

                    date_start = (
                        fields.Datetime.context_timestamp(
                            record, fields.Datetime.from_string(record.start_datetime)
                        )
                        if record.start_datetime
                        else False
                    )
                    date_stop = (
                        fields.Datetime.context_timestamp(
                            record, fields.Datetime.from_string(record.end_datetime)
                        )
                        if record.end_datetime
                        else False
                    )

                    hr_work_entry.append(
                        {
                            "name": work_entry_type_id.name
                            + ":"
                            + " "
                            + record.resource_id.name
                            if work_entry_type_id
                            else work_entry_type_attendance.name
                            + ":"
                            + " "
                            + record.resource_id.name,
                            "employee_id": employee_id.id,
                            "work_entry_type_id": work_entry_type_id.id
                            if work_entry_type_id
                            else work_entry_type_attendance.id,
                            "duration": record.allocated_hours,
                            "date_start": record.start_datetime,
                            "date_stop": record.end_datetime,
                            "planning_slot_id": record.id,
                        }
                    )

                    work_entrys = self.env["hr.work.entry"].search(
                        [
                            ("employee_id", "=", hr_work_entry[0].get("employee_id")),
                            ("date_start", ">=", date_start.date()),
                            ("date_stop", "<=", date_stop.date()),
                        ]
                    )
                    for record in work_entrys:
                        record.unlink()

                    self.env["hr.work.entry"].create(hr_work_entry)
        return res

    def unlink(self):
        for record in self:
            hr_work_entry = []
            work_entry_type_attendance = self.env.ref(
                "hr_work_entry.work_entry_type_attendance", raise_if_not_found=False
            )
            if record.id:
                work_entrys = self.env["hr.work.entry"].search(
                    [("planning_slot_id", "=", record.ids)]
                )

                for entrys in work_entrys:
                    entrys.unlink()
        return super(__class__, self).unlink()
