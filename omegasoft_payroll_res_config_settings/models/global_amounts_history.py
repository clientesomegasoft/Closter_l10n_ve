from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MinimumWageHistory(models.Model):
    _name = "minimum.wage.history"
    _description = "Minimum wage history"

    active = fields.Boolean("Active", default=True)
    amount = fields.Float("Amount", digits=(16, 2))
    currency_id = fields.Many2one("res.currency", string="Currency", required=True)
    date = fields.Date("Date", default=date.today(), required=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda s: s.env.company
    )
    in_use = fields.Boolean("In Use", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        line = self.search([("date", "<=", date.today())], order="date desc", limit=1)
        if line:
            line.company_id.write(
                {
                    "minimum_wage": line.amount,
                    "minimum_wage_currency": line.currency_id.id,
                }
            )
            self.search([("in_use", "=", True)], limit=1).in_use = False
            line.in_use = True
        return res

    def write(self, vals):
        res = super().write(vals)
        line = self.search([("date", "<=", date.today())], order="date desc", limit=1)
        if line:
            line.company_id.write(
                {
                    "minimum_wage": line.amount,
                    "minimum_wage_currency": line.currency_id.id,
                }
            )
            self.search(
                [("in_use", "=", True), ("id", "!=", self.id)], limit=1
            ).in_use = False
            if not line.in_use:
                line.in_use = True

        if "active" in vals and self.in_use:
            raise ValidationError(_("Cannot archive the record in use."))

        return res

    def unlink(self):
        if self.in_use:
            raise ValidationError(_("Cannot delete the record in use."))
        return super().unlink()

    def set_minimum_wage(self):
        self = self.sudo()
        for company in self.env["res.company"].search([]):
            line = self.search(
                [("date", "<=", date.today()), ("company_id", "=", company.id)],
                order="date desc",
                limit=1,
            )
            if line:
                line.company_id.write(
                    {
                        "minimum_wage": line.amount,
                        "minimum_wage_currency": line.currency_id.id,
                    }
                )
                self.search(
                    [("in_use", "=", True), ("id", "!=", line.id)], limit=1
                ).in_use = False
                if not line.in_use:
                    line.in_use = True

    @api.onchange("date")
    def _onchange_date(self):
        if self.date < date.today():
            raise ValidationError(
                _(
                    "It is not possible to create backdated records through the interface. Historical data must be entered by import upload."
                )
            )

    @api.constrains("date")
    def _constrains_date(self):
        if self.search(
            [("date", "=", self.date), ("id", "!=", self.id)],
            order="date desc",
            limit=1,
        ):
            raise ValidationError(_("There can be no more than one record per day."))

    @api.constrains("amount")
    def _constrains_amount(self):
        if self.amount <= 0:
            raise ValidationError(_("The amount must be greater than zero."))


class SalaryBasketTicketHistory(models.Model):
    _name = "salary.basket.ticket.history"
    _description = "Salary Basket Ticket History"

    active = fields.Boolean("Active", default=True)
    amount = fields.Float("Amount", digits=(16, 2))
    currency_id = fields.Many2one("res.currency", string="Currency", required=True)
    date = fields.Date("Date", default=date.today(), required=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda s: s.env.company
    )
    in_use = fields.Boolean("In Use", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        line = self.search([("date", "<=", date.today())], order="date desc", limit=1)
        if line:
            line.company_id.write(
                {
                    "salary_basket_ticket": line.amount,
                    "salary_basket_ticket_currency": line.currency_id.id,
                }
            )
            self.search([("in_use", "=", True)], limit=1).in_use = False
            line.in_use = True
        return res

    def write(self, vals):
        res = super().write(vals)
        line = self.search([("date", "<=", date.today())], order="date desc", limit=1)
        if line:
            line.company_id.write(
                {
                    "salary_basket_ticket": line.amount,
                    "salary_basket_ticket_currency": line.currency_id.id,
                }
            )
            self.search(
                [("in_use", "=", True), ("id", "!=", self.id)], limit=1
            ).in_use = False
            if not line.in_use:
                line.in_use = True

        if "active" in vals and self.in_use:
            raise ValidationError(_("Cannot archive the record in use."))
        return res

    def unlink(self):
        if self.in_use:
            raise ValidationError(_("Cannot delete the record in use."))
        return super().unlink()

    def set_salary_basket_ticket(self):
        self = self.sudo()
        for company in self.env["res.company"].search([]):
            line = self.search(
                [("date", "<=", date.today()), ("company_id", "=", company.id)],
                order="date desc",
                limit=1,
            )
            if line:
                line.company_id.write(
                    {
                        "salary_basket_ticket": line.amount,
                        "salary_basket_ticket_currency": line.currency_id.id,
                    }
                )
                self.search(
                    [("in_use", "=", True), ("id", "!=", line.id)], limit=1
                ).in_use = False
                if not line.in_use:
                    line.in_use = True

    @api.onchange("date")
    def _onchange_date(self):
        if self.date < date.today():
            raise ValidationError(
                _(
                    "It is not possible to create backdated records through the interface. Historical data must be entered by import upload."
                )
            )

    @api.constrains("date")
    def _constrains_date(self):
        if self.search(
            [("date", "=", self.date), ("id", "!=", self.id)],
            order="date desc",
            limit=1,
        ):
            raise ValidationError(_("There can be no more than one record per day."))

    @api.constrains("amount")
    def _constrains_amount(self):
        if self.amount <= 0:
            raise ValidationError(_("The amount must be greater than zero."))


class VacationsHistory(models.Model):
    _name = "vacations.history"
    _description = "Vacations History"

    active = fields.Boolean("Active", default=True)
    days = fields.Integer("Days")
    date = fields.Date("Date", default=date.today(), required=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda s: s.env.company
    )
    in_use = fields.Boolean("In Use", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        line = self.search([("date", "<=", date.today())], order="date desc", limit=1)
        if line:
            line.company_id.write(
                {
                    "vacations": line.days,
                }
            )
            self.search([("in_use", "=", True)], limit=1).in_use = False
            line.in_use = True
        return res

    def write(self, vals):
        res = super().write(vals)
        line = self.search([("date", "<=", date.today())], order="date desc", limit=1)
        if line:
            line.company_id.write(
                {
                    "vacations": line.days,
                }
            )
            self.search(
                [("in_use", "=", True), ("id", "!=", self.id)], limit=1
            ).in_use = False
            if not line.in_use:
                line.in_use = True

        if "active" in vals and self.in_use:
            raise ValidationError(_("Cannot archive the record in use."))
        return res

    def unlink(self):
        if self.in_use:
            raise ValidationError(_("Cannot delete the record in use."))
        return super().unlink()

    def set_vacations(self):
        self = self.sudo()
        for company in self.env["res.company"].search([]):
            line = self.search(
                [("date", "<=", date.today()), ("company_id", "=", company.id)],
                order="date desc",
                limit=1,
            )
            if line:
                line.company_id.write(
                    {
                        "vacations": line.days,
                    }
                )
                self.search(
                    [("in_use", "=", True), ("id", "!=", line.id)], limit=1
                ).in_use = False
                if not line.in_use:
                    line.in_use = True

    @api.onchange("date")
    def _onchange_date(self):
        if self.date < date.today():
            raise ValidationError(
                _(
                    "It is not possible to create backdated records through the interface. Historical data must be entered by import upload."
                )
            )

    @api.constrains("date")
    def _constrains_date(self):
        if self.search(
            [("date", "=", self.date), ("id", "!=", self.id)],
            order="date desc",
            limit=1,
        ):
            raise ValidationError(_("There can be no more than one record per day."))

    @api.constrains("days")
    def _constrains_days(self):
        if self.days < 0:
            raise ValidationError(_("The days must be greater or equal than zero."))


class DaysOfProfitHistory(models.Model):
    _name = "days.of.profit.history"
    _description = "Days Of Profit History"

    active = fields.Boolean("Active", default=True)
    days = fields.Integer("Days")
    date = fields.Date("Date", default=date.today(), required=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda s: s.env.company
    )
    in_use = fields.Boolean("In Use", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        line = self.search([("date", "<=", date.today())], order="date desc", limit=1)
        if line:
            line.company_id.write(
                {
                    "days_of_profit": line.days,
                }
            )
            self.search([("in_use", "=", True)], limit=1).in_use = False
            line.in_use = True
        return res

    def write(self, vals):
        res = super().write(vals)
        line = self.search([("date", "<=", date.today())], order="date desc", limit=1)
        if line:
            line.company_id.write(
                {
                    "days_of_profit": line.days,
                }
            )
            self.search(
                [("in_use", "=", True), ("id", "!=", self.id)], limit=1
            ).in_use = False
            if not line.in_use:
                line.in_use = True

        if "active" in vals and self.in_use:
            raise ValidationError(_("Cannot archive the record in use."))
        return res

    def unlink(self):
        if self.in_use:
            raise ValidationError(_("Cannot delete the record in use."))
        return super().unlink()

    def set_days_of_profit(self):
        self = self.sudo()
        for company in self.env["res.company"].search([]):
            line = self.search(
                [("date", "<=", date.today()), ("company_id", "=", company.id)],
                order="date desc",
                limit=1,
            )
            if line:
                line.company_id.write(
                    {
                        "days_of_profit": line.days,
                    }
                )
                self.search(
                    [("in_use", "=", True), ("id", "!=", line.id)], limit=1
                ).in_use = False
                if not line.in_use:
                    line.in_use = True

    @api.onchange("date")
    def _onchange_date(self):
        if self.date < date.today():
            raise ValidationError(
                _(
                    "It is not possible to create backdated records through the interface. Historical data must be entered by import upload."
                )
            )

    @api.constrains("date")
    def _constrains_date(self):
        if self.search(
            [("date", "=", self.date), ("id", "!=", self.id)],
            order="date desc",
            limit=1,
        ):
            raise ValidationError(_("There can be no more than one record per day."))

    @api.constrains("days")
    def _constrains_days(self):
        if self.days < 0:
            raise ValidationError(_("The days must be greater or equal than zero."))


class CentralBankSocialBenefitsRateHistory(models.Model):
    _name = "central.bank.social.benefits.rate.history"
    _description = "Central Bank Social Benefits Rate History"

    active = fields.Boolean("Active", default=True)
    amount = fields.Float("Amount", digits=(16, 2))
    date = fields.Date("Date", default=date.today(), required=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda s: s.env.company
    )
    in_use = fields.Boolean("In Use", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        line = self.search([("date", "<=", date.today())], order="date desc", limit=1)
        if line:
            line.company_id.write(
                {
                    "central_bank_social_benefits_rate": line.amount,
                }
            )
            self.search([("in_use", "=", True)], limit=1).in_use = False
            line.in_use = True
        return res

    def write(self, vals):
        res = super().write(vals)
        line = self.search([("date", "<=", date.today())], order="date desc", limit=1)
        if line:
            line.company_id.write(
                {
                    "central_bank_social_benefits_rate": line.amount,
                }
            )
            self.search(
                [("in_use", "=", True), ("id", "!=", self.id)], limit=1
            ).in_use = False
            if not line.in_use:
                line.in_use = True

        if "active" in vals and self.in_use:
            raise ValidationError(_("Cannot archive the record in use."))
        return res

    def unlink(self):
        if self.in_use:
            raise ValidationError(_("Cannot delete the record in use."))
        return super().unlink()

    def set_central_bank_social_benefits_rate(self):
        self = self.sudo()
        for company in self.env["res.company"].search([]):
            line = self.search(
                [("date", "<=", date.today()), ("company_id", "=", company.id)],
                order="date desc",
                limit=1,
            )
            if line:
                line.company_id.write(
                    {
                        "central_bank_social_benefits_rate": line.amount,
                    }
                )
                self.search(
                    [("in_use", "=", True), ("id", "!=", line.id)], limit=1
                ).in_use = False
                if not line.in_use:
                    line.in_use = True

    @api.onchange("date")
    def _onchange_date(self):
        if self.date < date.today():
            raise ValidationError(
                _(
                    "It is not possible to create backdated records through the interface. Historical data must be entered by import upload."
                )
            )

    @api.constrains("date")
    def _constrains_date(self):
        if self.search(
            [("date", "=", self.date), ("id", "!=", self.id)],
            order="date desc",
            limit=1,
        ):
            raise ValidationError(_("There can be no more than one record per day."))

    @api.constrains("amount")
    def _constrains_amount(self):
        if self.amount <= 0:
            raise ValidationError(_("The amount must be greater than zero."))
