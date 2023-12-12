
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import re

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    rif = fields.Char(string='R.I.F', groups="hr.group_hr_user", help="Fiscal information", tracking=True)
    job_id = fields.Many2one(related='contract_id.job_id', store=True)

    def _get_employee_l10n_ve_payroll_domain(self):
        return [('company_id', '=', self.env.company.id), ('active', '=', True), ('contract_id.state', 'in', ['open'] )]

    def write(self, vals):
        res = {}
        if vals.get('rif'):
            res = self.validate_rif(vals.get('rif', False))
            if not res:
                raise ValidationError(
                    'Advertencia El rif tiene un formato incorrecto. Ej: V-[0]1234567 or V-12345678[0], E-012345678, J-012345678 o G-012345678. Por favor, inténtelo de nuevo')
            if not self.validate_rif_duplicate(vals.get('rif', False)):
                raise ValidationError(
                    'Advertencia El empleado ya está registrado en el rif: %s y está activo' % (
                        vals.get('rif', False)))
        res = super(HrEmployee, self).write(vals)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        # validation for l10n_ve_odoo16:
        self = self.with_context(skip_check_partner_type=True)

        for vals in vals_list:
            res = {}
            if vals.get('rif'):
                res = self.validate_rif(vals.get('rif'))
                if not res:
                    raise ValidationError(
                        'Advertencia El rif tiene un formato incorrecto. Ej: V-[0]1234567 or V-12345678[0], E-012345678, J-012345678 o G-012345678. Por favor, inténtelo de nuevo')
                if not self.validate_rif_duplicate(vals.get('rif', False), True):
                    raise ValidationError(
                        'Advertencia El empleado ya está registrado en el rif: %s y está activo' % (
                            vals.get('rif', False)))
        return super(HrEmployee, self).create(vals_list)

    @api.model
    def validate_rif(self, field_value):
        rif_obj = re.compile(r"^[V|E|J|G]+[-][\d]{9}", re.X)
        rif_obj_2 = re.compile(r"^[V|E|J|G]+[-][\d]{8}", re.X)
        if rif_obj.search(field_value.upper()) or rif_obj_2.search(field_value.upper()):
            if rif_obj_2 and not rif_obj:
                if len(field_value) == 10 and field_value[2:][0] == '0':
                    return True
                else:
                    return False
            if len(field_value) == 11:
                return True
            else:
                return False
        return False

    def validate_rif_duplicate(self, valor, create=False):
        found = True
        rif = self.search([('rif', '=', valor)])
        if create:
            if rif:
                found = False
        elif rif:
            found = False
        return found
    