# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, SUPERUSER_ID

class ResPartnerIn(models.Model):
    _inherit = 'res.partner'

    is_consignments = fields.Boolean(string="Consignments", help="Consignments", copy=False)
    commission = fields.Float(string="Commission (%)")


class Product(models.Model):
    _inherit = "product.template"

    is_consignments = fields.Boolean(string="Consignments", help="Consignments",copy=False)

