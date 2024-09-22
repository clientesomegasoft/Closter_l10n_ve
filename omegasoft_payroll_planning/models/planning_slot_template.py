import math
from datetime import date, datetime, time, timedelta

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import format_time


class Workshifts(models.Model):
    _name = "work.shifts"
    _description = "Work shifts"

    name = fields.Char(string="Work shifts")


class PlanningSlotTemplate(models.Model):
    _inherit = "planning.slot.template"

    work_shifts_id = fields.Many2one(
        comodel_name="work.shifts", string="Shift name", ondelete="restrict"
    )
    work_entry_type_id = fields.Many2one(
        comodel_name="hr.work.entry.type", string="Work entry type", ondelete="restrict"
    )

    def name_get(self):
        result = []
        for shift_template in self:
            name = "%s - %s" % (
                shift_template.work_shifts_id.name
                if shift_template.work_shifts_id
                else shift_template.name,
                shift_template.role_id.name
                if shift_template.role_id.name is not False
                else "",
            )
            result.append([shift_template.id, name])
        return result

    @api.depends("start_time", "duration")
    def _compute_name(self):
        calendar = self.env.company.resource_calendar_id
        user_tz = pytz.timezone(self.env["planning.slot"]._get_tz())
        today = date.today()
        for shift_template in self:
            if not 0 <= shift_template.start_time < 24:
                raise ValidationError(
                    _("The start hour must be greater or equal to 0 and lower than 24.")
                )
            start_time = time(
                hour=int(shift_template.start_time),
                minute=round(math.modf(shift_template.start_time)[0] / (1 / 60.0)),
            )
            start_datetime = user_tz.localize(datetime.combine(today, start_time))
            (
                shift_template.duration_days,
                shift_template.end_time,
            ) = shift_template._get_company_work_duration_data(
                calendar, start_datetime, shift_template.duration
            )
            end_time = time(
                hour=int(shift_template.end_time),
                minute=round(math.modf(shift_template.end_time)[0] / (1 / 60.0)),
            )
            shift_template.name = "%s - %s %s" % (
                format_time(
                    shift_template.env, start_time, time_format="short"
                ).replace(":00 ", " "),
                format_time(shift_template.env, end_time, time_format="short").replace(
                    ":00 ", " "
                ),
                _("(%s days span)") % (shift_template.duration_days)
                if shift_template.duration_days > 1
                else "",
            )

    @api.model
    def _get_company_work_duration_data(self, calendar, start_datetime, duration):
        """ "
        Taking company's working calendar into account get the `hours` and
        `days` from start_time and duration expressed in time and hours.

        :param start_time: reference time
        :param duration: reference duration in hours

        Returns a tuple (duration, end_time) expressed as days and as hours.
        """
        duration = self._get_duration()
        end_datetime = start_datetime + duration
        # end_datetime = calendar.plan_hours(
        #     duration,
        #     start_datetime,
        #     compute_leaves=True
        # )

        if end_datetime is False:
            raise ValidationError(_("The duration is too long."))
        if duration == 0 and start_datetime.hour == 0:
            end_datetime = end_datetime.replace(hour=0)
        return (
            math.ceil(
                calendar.get_work_duration_data(start_datetime, end_datetime)["days"]
            ),
            timedelta(
                hours=end_datetime.hour, minutes=end_datetime.minute
            ).total_seconds()
            / 3600,
        )
