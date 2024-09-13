# -*- coding: utf-8 -*-
from odoo import fields, models, api, exceptions, _
from odoo.exceptions import ValidationError
from markupsafe import Markup, escape


class Respartner(models.Model):
    _inherit = 'res.partner'
    
    def get_full_address(self):
        res = ''
        if self.street:
            res = res + self.street + ' '
        if self.street2:
            res = res + self.street2 + ' '
        if self.city:
            res = res + self.city + ' '
        if self.state_id:
            res = res + self.state_id.name + ' '
        if self.zip:
            res = res + self.zip + ' '
        if self.country_id:
            res = res + self.country_id.name + ' '
        return res
    
    def get_full_address_header(self):
        res = ''
        if self.street:
            res = res + self.street + ' '
        if self.street2:
            res = res + self.street2 + ' '
        if self.city:
            res = res + self.city + '\n'
        if self.state_id:
            res = res + self.state_id.name + ', '
        if self.zip:
            res = res + self.zip + '\n'
        if self.country_id:
            res = res + self.country_id.name + '\n'
        opsep = Markup('<br/>')
        address = opsep.join(res.split("\n")).strip()
        options = {
            'widget': 'contact',
            'fields': ['address'],
            'no_marker': True,
            'type': 'contact',
            'tagName': 'div',
            'inherit_branding': False
        }
        val = {
            'name': self.name,
            'address': address,
            'phone': self.phone,
            'mobile': self.mobile,
            'city': self.city,
            'country_id': self.country_id.display_name,
            'website': self.website,
            'email': self.email,
            'vat': self.vat,
            'vat_label': self.country_id.vat_label or _('VAT'),
            'fields': ['address'],
            'object': self,
            'options': options
        }
        return self.env['ir.qweb']._render('base.contact', val, minimal_qcontext=True)