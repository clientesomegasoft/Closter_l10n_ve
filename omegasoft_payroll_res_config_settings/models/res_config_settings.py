from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    average_wage_ids = fields.One2many(
        related="company_id.average_wage_ids", readonly=False
    )
    average_wage_count = fields.Integer(
        string="average_wage_count", compute="_compute_average_wage_count"
    )

    salary_rules_category = fields.Many2many(
        "hr.salary.rule.category",
        related="company_id.salary_rules_category",
        string="Categories of wage rules",
        readonly=False,
    )

    codes_line_receipt = fields.Char(
        related="company_id.codes_line_receipt",
        string="Receipt line codes",
        readonly=False,
    )
    sequences_lines_receipt = fields.Char(
        related="company_id.sequences_lines_receipt",
        string="Sequences of lines on the receipt",
        readonly=False,
    )

    minimum_wage = fields.Monetary(
        related="company_id.minimum_wage", string="Minimum wage", readonly=False
    )
    minimum_wage_currency = fields.Many2one(
        "res.currency", related="company_id.minimum_wage_currency", readonly=False
    )

    vacations = fields.Integer(
        related="company_id.vacations", string="Vacations", readonly=False
    )

    days_of_profit = fields.Integer(
        related="company_id.days_of_profit", string="Days of profit", readonly=False
    )

    salary_basket_ticket = fields.Monetary(
        related="company_id.salary_basket_ticket",
        string="Salary Basket Ticket",
        readonly=False,
    )
    salary_basket_ticket_currency = fields.Many2one(
        "res.currency",
        related="company_id.salary_basket_ticket_currency",
        readonly=False,
    )

    central_bank_social_benefits_rate = fields.Float(
        related="company_id.central_bank_social_benefits_rate",
        string="Social benefits rate Central Bank",
        readonly=False,
    )

    salary_rules_categories_assignments = fields.Many2many(
        "hr.salary.rule.category",
        relation="category_assignments",
        related="company_id.salary_rules_categories_assignments",
        string="Categories for assignments",
        readonly=False,
    )
    salary_rules_categories_deductions = fields.Many2many(
        "hr.salary.rule.category",
        relation="category_deductions",
        related="company_id.salary_rules_categories_deductions",
        string="Categories for deductions",
        readonly=False,
    )

    lines_other_entries_type = fields.Many2many(
        "hr.payslip.input.type",
        relation="lines_other_entries_type",
        related="company_id.lines_other_entries_type",
        string="Lines other entries",
        readonly=False,
    )

    salary_rules_categories_basic = fields.Many2one(
        "hr.salary.rule.category",
        related="company_id.salary_rules_categories_basic",
        string="Categories for basic",
        readonly=False,
    )
    salary_rules_categories_net = fields.Many2one(
        "hr.salary.rule.category",
        related="company_id.salary_rules_categories_net",
        string="Categories for net",
        readonly=False,
    )

    payroll_structure_for_basic = fields.Many2many(
        "hr.payroll.structure",
        relation="rule_structure_basic",
        related="company_id.payroll_structure_for_basic",
        string="Payroll structure for basic",
        readonly=False,
    )
    payroll_structure_for_net = fields.Many2many(
        "hr.payroll.structure",
        relation="rule_structure_net",
        related="company_id.payroll_structure_for_net",
        string="Payroll structure for net",
        readonly=False,
    )

    payroll_structure_for_rate = fields.Many2many(
        "hr.payroll.structure",
        relation="rule_structure_rate",
        related="company_id.payroll_structure_for_rate",
        string="fee required for the following structures",
        readonly=False,
    )

    salary_rules_for_basic = fields.Many2many(
        "hr.salary.rule",
        relation="rule_assignments",
        related="company_id.salary_rules_for_basic",
        string="Rule for basic",
        readonly=False,
    )
    salary_rules_for_net = fields.Many2many(
        "hr.salary.rule",
        relation="rule_deductions",
        related="company_id.salary_rules_for_net",
        string="Rule for net",
        readonly=False,
    )

    quarterly_payment_benefits = fields.Boolean(
        string="Quarterly payment of benefits",
        related="company_id.quarterly_payment_benefits",
        readonly=False,
    )
    profits_generated = fields.Boolean(
        string="Profits generated",
        related="company_id.profits_generated",
        readonly=False,
    )
    advance_profit_sharing = fields.Boolean(
        string="Advance profit sharing",
        related="company_id.advance_profit_sharing",
        readonly=False,
    )
    net_income = fields.Boolean(
        string="Net income", related="company_id.net_income", readonly=False
    )
    social_benefits = fields.Boolean(
        string="Social benefits", related="company_id.social_benefits", readonly=False
    )

    payroll_structure_for_average_vacation_salary = fields.Many2many(
        "hr.payroll.structure",
        relation="structure_for_average_vacation_salary",
        related="company_id.payroll_structure_for_average_vacation_salary",
        string="Payroll structure for Average vacation salary",
        readonly=False,
    )
    show_average_vacation_salary = fields.Boolean(
        string="Show Average vacation salary",
        related="company_id.show_average_vacation_salary",
        readonly=False,
    )

    payroll_structure_for_salary_settlement = fields.Many2many(
        "hr.payroll.structure",
        relation="structure_for_salary_settlement",
        related="company_id.payroll_structure_for_salary_settlement",
        string="Payroll structure for Salary Settlement",
        readonly=False,
    )
    show_salary_settlement = fields.Boolean(
        string="Show Salary Settlement",
        related="company_id.show_salary_settlement",
        readonly=False,
    )

    salary_rules_categories_for_profits = fields.Many2many(
        "hr.salary.rule.category",
        relation="category_for_profits",
        related="company_id.salary_rules_categories_for_profits",
        string="Categories for profits",
        readonly=False,
    )
    payroll_structure_for_profits = fields.Many2many(
        "hr.payroll.structure",
        relation="payroll_structure_for_profits",
        string="Payroll structure for profits",
        related="company_id.payroll_structure_for_profits",
        readonly=False,
    )

    structures_for_utility_resets = fields.Many2many(
        "hr.payroll.structure",
        relation="payroll_structures_for_utility_resets",
        related="company_id.structures_for_utility_resets",
        string="Structures for utility resets",
        help="Structures for the reinitialization of profits",
        readonly=False,
    )
    structure_for_resets_labor_liabilities = fields.Many2many(
        "hr.payroll.structure",
        relation="payroll_structure_for_resets_labor_liabilities",
        related="company_id.structure_for_resets_labor_liabilities",
        string="Structures for labor liabilities resets",
        help="Structures for the reinitialization of labor liabilities (at year-end)",
        readonly=False,
    )

    # hr_working_hours = fields.Boolean(
    #     string='Working hours',
    #     related='company_id.hr_working_hours',
    #     readonly=False
    # )
    # hr_planning = fields.Boolean(
    #     string='Planning',
    #     related='company_id.hr_planning',
    #     readonly=False
    # )

    @api.constrains(
        "minimum_wage",
        "vacations",
        "days_of_profit",
        "salary_basket_ticket",
        "central_bank_social_benefits_rate",
    )
    def _check_fields(self):
        flag = (
            True
            if (
                self.minimum_wage < 0
                or self.vacations < 0
                or self.days_of_profit < 0
                or self.salary_basket_ticket < 0
                or self.central_bank_social_benefits_rate < 0
            )
            else False
        )
        if flag:
            raise ValidationError(
                _("Global amounts. The amount entered must not be less than zero.")
            )

    @api.depends("average_wage_ids")
    def _compute_average_wage_count(self):
        average_wage_count = self.env["average_wage_lines"].sudo().search_count([])
        for record in self:
            record.average_wage_count = average_wage_count

    def _search_element(self, salary_rules_list, payroll_structure_list):
        if len(salary_rules_list) >= len(payroll_structure_list):
            list1 = salary_rules_list
            list2 = payroll_structure_list
        else:
            list1 = payroll_structure_list
            list2 = salary_rules_list
        return any(item in list2 for item in list1)

    @api.onchange("salary_rules_categories_basic", "payroll_structure_for_basic")
    def _onchange_categories_basic(self):
        exist_element = self._search_element(
            self.salary_rules_for_basic.struct_id.ids or [],
            self.payroll_structure_for_basic.ids or [],
        )
        for record in self:
            if record.salary_rules_for_basic and (
                record.salary_rules_for_basic.category_id.id
                != record.salary_rules_categories_basic.id
                or not exist_element
            ):
                record.salary_rules_for_basic = False

    @api.onchange("salary_rules_categories_net", "payroll_structure_for_net")
    def _onchange_categories_net(self):
        exist_element = self._search_element(
            self.salary_rules_for_net.struct_id.ids or [],
            self.payroll_structure_for_net.ids or [],
        )
        for record in self:
            if record.salary_rules_for_net and (
                record.salary_rules_for_net.category_id.id
                != record.salary_rules_categories_net.id
                or not exist_element
            ):
                record.salary_rules_for_net = False


class ResCompany(models.Model):
    _inherit = "res.company"

    average_wage_ids = fields.One2many(
        "average_wage_lines", "company_id", string="average wage"
    )

    salary_rules_category = fields.Many2many(
        "hr.salary.rule.category", string="Categories of wage rules"
    )

    codes_line_receipt = fields.Char(string="Receipt line codes")
    sequences_lines_receipt = fields.Char(string="Sequences of lines on the receipt")

    minimum_wage = fields.Monetary(string="Minimum wage", default=0)
    minimum_wage_currency = fields.Many2one("res.currency")

    vacations = fields.Integer(string="Vacations", default=0)

    days_of_profit = fields.Integer(string="Days of profit", default=0)

    salary_basket_ticket = fields.Monetary(string="Salary Basket Ticket", default=0)
    salary_basket_ticket_currency = fields.Many2one("res.currency")

    central_bank_social_benefits_rate = fields.Float(
        string="Social benefits rate Central Bank", default=0
    )

    salary_rules_categories_assignments = fields.Many2many(
        "hr.salary.rule.category",
        relation="category_assignments",
        string="Categories for assignments",
    )
    salary_rules_categories_deductions = fields.Many2many(
        "hr.salary.rule.category",
        relation="category_deductions",
        string="Categories for deductions",
    )

    lines_other_entries_type = fields.Many2many(
        "hr.payslip.input.type",
        relation="lines_other_entries_type",
        string="Lines other entries",
    )

    salary_rules_categories_basic = fields.Many2one(
        "hr.salary.rule.category", string="Categories for basic"
    )
    salary_rules_categories_net = fields.Many2one(
        "hr.salary.rule.category", string="Categories for net"
    )

    payroll_structure_for_basic = fields.Many2many(
        "hr.payroll.structure",
        relation="rule_structure_basic",
        string="Payroll structure for basic",
    )
    payroll_structure_for_net = fields.Many2many(
        "hr.payroll.structure",
        relation="rule_structure_net",
        string="Payroll structure for net",
    )

    payroll_structure_for_rate = fields.Many2many(
        "hr.payroll.structure",
        relation="rule_structure_rate",
        string="fee required for the following structures",
    )

    salary_rules_for_basic = fields.Many2many(
        "hr.salary.rule", relation="rule_assignments", string="Rule for basic"
    )
    salary_rules_for_net = fields.Many2many(
        "hr.salary.rule", relation="rule_deductions", string="Rule for net"
    )

    quarterly_payment_benefits = fields.Boolean(string="Quarterly payment of benefits")
    profits_generated = fields.Boolean(string="Profits generated")
    advance_profit_sharing = fields.Boolean(string="Advance profit sharing")
    net_income = fields.Boolean(string="Net income")
    social_benefits = fields.Boolean(string="Social benefits")

    payroll_structure_for_average_vacation_salary = fields.Many2many(
        "hr.payroll.structure",
        relation="structure_for_average_vacation_salary",
        string="Payroll structure for Average vacation salary",
    )
    show_average_vacation_salary = fields.Boolean(string="Average vacation salary")

    payroll_structure_for_salary_settlement = fields.Many2many(
        "hr.payroll.structure",
        relation="structure_for_salary_settlement",
        string="Payroll structure for Salary Settlement",
    )
    show_salary_settlement = fields.Boolean(string="Salary Settlement")

    salary_rules_categories_for_profits = fields.Many2many(
        "hr.salary.rule.category",
        relation="category_for_profits",
        string="Categories for profits",
    )
    payroll_structure_for_profits = fields.Many2many(
        "hr.payroll.structure",
        relation="payroll_structure_for_profits",
        string="Payroll structure for profits",
    )

    structures_for_utility_resets = fields.Many2many(
        "hr.payroll.structure",
        relation="payroll_structures_for_utility_resets",
        string="Structures for utility resets",
        help="Structures for the reinitialization of profits (at year-end)",
    )
    structure_for_resets_labor_liabilities = fields.Many2many(
        "hr.payroll.structure",
        relation="payroll_structure_for_resets_labor_liabilities",
        string="Structures for labor liabilities resets",
        help="Structures for the reinitialization of labor liabilities (at year-end)",
    )
    # hr_working_hours = fields.Boolean(string='Working hours')
    # hr_planning = fields.Boolean(string='Planning')
