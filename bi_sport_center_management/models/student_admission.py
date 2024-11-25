# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta, date


class StudentAdmission(models.Model):
    _name = "student.admission"
    _description = "Student Admission"

    name = fields.Char('Name', required=True,
                       readonly=True, default=lambda self: _('New'))
    student_id = fields.Many2one('res.partner', string='Student Name', required=True,
                                 domain=[('is_student', '=', False), ('is_coach', '=', False)])
    mobile = fields.Char('Mobile', related='student_id.mobile', store=True, readonly=False)
    p_name = fields.Char('Parent Name', related='student_id.p_name', readonly=False)
    parent_mobile = fields.Char('Parent Mobile', related='student_id.phone', readonly=False)
    p1_name = fields.Char('Parent Name ', related='inquiry_id.p_name', readonly=False)
    parent1_mobile = fields.Char('Parent Mobile ', related='inquiry_id.parent_mobile', readonly=False)
    email = fields.Char('Email', related='student_id.email', store=True, readonly=False)
    is_disability = fields.Boolean('Description', related='student_id.is_disability', store=True, readonly=False)
    disability_description = fields.Text('Disability Description', related='student_id.disability_description',
                                         store=True, readonly=False)
    sport_id = fields.Many2one(
        'product.product', string="Sport Name", domain=[('is_sportname', '=', True)])
    level_id = fields.Many2one('res.partner', string="Sport Center", domain=[
        ('is_sport', '=', True)])
    trainer_id = fields.Many2one(comodel_name='res.partner', domain=[('is_coach', '=', True)], string='Coach')
    duration = fields.Float("Duration(Days)", compute="_compute_spend_time")
    state = fields.Selection([
        ('new', 'New'),
        ('enrolled', 'Enrolled'),
        ('student', 'Student'),
        ('cancel', 'Cancelled')], string='State',
        copy=False, default="new", store=True)
    is_invoiced = fields.Boolean()
    inquiry_id = fields.Many2one('student.inquiry', string='Inquiry')
    check_parent = fields.Boolean('Check Parent', related='inquiry_id.check_parent')
    check_register = fields.Boolean('Check Register')
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    is_warning = fields.Boolean(string="Warning", compute="_compute_is_warning", store=True)
    n_of_reservations = fields.Integer(string='Number of reservations', )
    n_of_reservations_done = fields.Integer(string='Number of reservations done',
                                            compute='_compute_n_of_reservations_done')
    reservation_ids = fields.One2many('student.reservation', 'admission_id')
    is_reservation_done = fields.Boolean(defualt=False, compute='_compute_is_reservation_done')

    @api.depends('reservation_ids')
    def _compute_is_reservation_done(self):
        for rec in self:
            if rec.reservation_ids and len(rec.reservation_ids) == rec.n_of_reservations:
                rec.is_reservation_done = True
            else:
                rec.is_reservation_done = False

    @api.depends('reservation_ids')
    def _compute_n_of_reservations_done(self):
        for rec in self:
            rec.n_of_reservations_done = len(rec.reservation_ids)

    @api.constrains('n_of_reservations')
    def _check_n_of_reservations(self):
        for record in self:
            if record.n_of_reservations <= 0:
                raise ValidationError("The number of reservations cannot be 0 or negative.")

    @api.depends('end_date')
    def _compute_is_warning(self):
        for record in self:
            if record.end_date:
                # Calculate the warning date as a `datetime.date`
                warning_date = date.today() + timedelta(days=5)
                # Compare `end_date` (date) with `warning_date` (also date)
                record.is_warning = record.end_date <= warning_date
            else:
                record.is_warning = False

    @api.model
    def _update_is_warning(self):
        """Update the warning field for all records."""
        admissions = self.search([])
        for admission in admissions:
            admission._compute_is_warning()

    @api.depends('start_date', 'end_date')
    def _compute_spend_time(self):
        for record in self:
            if record.start_date and record.end_date:
                # Calculate the number of days directly
                delta = (record.end_date - record.start_date).days
                record.duration = float(delta) + 1  # Convert to float if needed
            else:
                record.duration = 0.0

    @api.onchange('trainer_id')
    def _onchange_trainer_id(self):
        if self.trainer_id and self.student_id:
            self.student_id.trainer_id = self.trainer_id.id

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'student.admission') or _('New')

        res = super(StudentAdmission, self).create(vals_list)

        portal_wizard_obj = self.env['portal.wizard']
        for record in res:
            if record.email:  # Ensure email exists
                try:
                    # Attempt to create portal access
                    created_portal_wizard = portal_wizard_obj.create({})
                    portal_wizard_user_obj = self.env['portal.wizard.user']
                    wiz_user_vals = {
                        'wizard_id': created_portal_wizard.id,
                        'partner_id': record.student_id.id,
                        'email': record.student_id.email,
                    }
                    created_portal_wizard_user = portal_wizard_user_obj.create(wiz_user_vals)
                    if created_portal_wizard_user:
                        created_portal_wizard_user.action_grant_access()
                except UserError as e:
                    # Skip granting access if the user already has portal access
                    if 'portal access' in str(e):
                        continue
                    else:
                        raise e  # Re-raise any other errors

        return res

    def action_enroll(self):
        self.state = 'enrolled'
        # self.student_id.update({'is_student': False})
        template = self.env.ref(
            'bi_sport_center_management.student_admission_enroll_email_template')
        if template:
            template.send_mail(self.id, force_send=True)

        # print(self._context)
        # return {
        #     'name': 'Create Invoice',
        #     'view_mode': 'form',
        #     'res_model': 'create.invoice',
        #     'type': 'ir.actions.act_window',
        #     'context': self._context,
        #     'target': 'new',
        # }

    def action_make_student(self):
        if not self.is_invoiced:
            return {
                'name': 'Create Invoice',
                'view_mode': 'form',
                'res_model': 'create.invoice',
                'type': 'ir.actions.act_window',
                'context': self._context,
                'target': 'new',
            }
        if self.is_invoiced:
            self.state = 'student'
            self.student_id.update({'is_student': True})

    def action_cancel(self):
        self.ensure_one()
        invoice_ids = self.env['account.move'].search([('invoice_origin', '=', self.name)])
        if len(invoice_ids.ids) == 1:
            invoice = invoice_ids
            invoice.button_cancel()
        self.state = 'cancel'
        self.student_id.update({'is_student': False})
        for reserv in self.reservation_ids:
            if reserv.state != 'finished':
                reserv.unlink()

    def action_new(self):
        self.ensure_one()
        self.state = 'new'

    def action_view_invoice(self):
        self.ensure_one()
        invoice_ids = self.env['account.move'].search([('invoice_origin', '=', self.name)])
        if invoice_ids:
            action = {
                'name': _("Admission Invoices"),
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'target': 'current',
            }
            if len(invoice_ids.ids) == 1:
                invoice = invoice_ids.ids[0]
                action['res_id'] = invoice
                action['view_mode'] = 'form'
                action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            else:
                action['view_mode'] = 'list,form'
                action['domain'] = [('id', 'in', invoice_ids.ids)]
            return action

    def action_create_reservation(self):
        """Open a new form view for creating a reservation."""
        self.ensure_one()  # Ensure the action is executed on a single record
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Reservation',
            'res_model': 'student.reservation',
            'view_mode': 'form',
            'view_id': self.env.ref('bi_sport_center_management.student_reservation_view_form').id,
            'target': 'new',  # Open in dialog (new form)
            'context': {
                'default_student_id': self.student_id.id,  # Pre-fill student
                'default_admission_id': self.id,  # Link to current admission
                'default_trainer_id': self.trainer_id.id,  # Link to current admission
                'default_sport_id': self.sport_id.id,  # Link to current admission
                'default_level_id': self.level_id.id,  # Link to current admission
            }
        }

    def action_view_reservations(self):
        self.ensure_one()
        reservation_ids = self.env['student.reservation'].search([('ref', '=', self.name)])
        if reservation_ids:
            action = {'name': _("Student Reservations"), 'type': 'ir.actions.act_window',
                      'res_model': 'student.reservation', 'target': 'current', 'view_mode': 'list,form',
                      'domain': [('id', 'in', reservation_ids.ids)]}
            # if len(reservation_ids.ids) == 1:
            #     reservation = reservation_ids.ids[0]
            #     action['res_id'] = reservation
            #     action['view_mode'] = 'form'
            #     action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]

            return action

    def unlink(self):
        for record in self:
            if record.state == 'student':
                raise ValidationError(_("You cannot delete an admission that is in the 'student' state, cancel it first."))
        return super(StudentAdmission, self).unlink()