from odoo import api, fields, models


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"

    should_approve_automatically = fields.Boolean(
        "Should Approve Automatically",
        compute="_compute_should_approve_automatically",
        help="Technical field used to avoid the validation "
        "errors that apperars if the user confirms a "
        "leave request that is approved automatically",
    )

    @api.depends("state", "active", "validation_type")
    def _compute_should_approve_automatically(self):
        """
        Calculate whether we should enable the confirm button
        or not in UI.

        NOTE:   It seems that if the user confirms a leave request without
                saving the record, a validation error could appear if the
                record is validated/approved on creation time.

                This error happens on odoo enterprise and leads to confusion
                and finally a poor user experience.
        """
        for record in self:
            record.should_approve_automatically = (
                record.validation_type
                and record.validation_type == "no_validation"
                and not record._origin.exists()
            )

    def action_noop(self):
        """Do nothing. Made to avoid problems with action_confirm on UI.
        SEE ALSO: _compute_should_approve_automatically()"""
        pass
