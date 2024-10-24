from odoo import fields, models
from odoo.tools import get_timedelta


class PlanningRecurrency(models.Model):
    _inherit = "planning.recurrency"

    def _repeat_slot(self, stop_datetime=False):
        PlanningSlot = self.env["planning.slot"]
        for recurrency in self:
            slot = PlanningSlot.search(
                [("recurrency_id", "=", recurrency.id)],
                limit=1,
                order="start_datetime DESC",
            )

            if slot and slot.filtered(
                lambda employee: employee.employee_id.contract_id.state in ["open"]
            ):
                # find the end of the recurrence
                recurrence_end_dt = False
                if recurrency.repeat_type == "until":
                    recurrence_end_dt = recurrency.repeat_until

                # find end of generation period (either the end of recurrence
                # (if this one ends before the cron period), or the given
                # `stop_datetime` (usually the cron period))
                if not stop_datetime:
                    stop_datetime = fields.Datetime.now() + get_timedelta(
                        recurrency.company_id.planning_generation_interval, "month"
                    )
                range_limit = min(
                    [dt for dt in [recurrence_end_dt, stop_datetime] if dt]
                )

                # generate recurring slots
                recurrency_delta = get_timedelta(recurrency.repeat_interval, "week")
                next_start = PlanningSlot._add_delta_with_dst(
                    slot.start_datetime, recurrency_delta
                )

                slot_values_list = []
                while next_start < range_limit:
                    slot_values = slot.copy_data(
                        {
                            "start_datetime": next_start,
                            "end_datetime": next_start
                            + (slot.end_datetime - slot.start_datetime),
                            "recurrency_id": recurrency.id,
                            "company_id": recurrency.company_id.id,
                            "repeat": True,
                            "state": "draft",
                        }
                    )[0]
                    slot_values_list.append(slot_values)
                    next_start = PlanningSlot._add_delta_with_dst(
                        next_start, recurrency_delta
                    )

                if slot_values_list:
                    PlanningSlot.create(slot_values_list)
                    recurrency.write(
                        {
                            "last_generated_end_datetime": slot_values_list[-1][
                                "start_datetime"
                            ]
                        }
                    )

            else:
                recurrency.unlink()
