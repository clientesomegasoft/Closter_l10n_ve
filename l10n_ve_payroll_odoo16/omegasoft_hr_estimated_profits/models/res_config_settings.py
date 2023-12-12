from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    estimated_profit_ids = fields.One2many(related='company_id.estimated_profit_ids', readonly=False)
    estimated_profit_count = fields.Integer(string='estimated profit count', compute='_compute_estimated_profit_count')
    
    
    @api.depends('estimated_profit_ids')
    def _compute_estimated_profit_count(self):
        estimated_profit_count = self.env['hr.estimated.profit'].sudo().search_count([])
        for record in self:
            record.estimated_profit_count = estimated_profit_count
    
class ResCompany(models.Model):
    _inherit = 'res.company'

    estimated_profit_ids = fields.One2many('hr.estimated.profit', 'company_id', string='estimated profit') 