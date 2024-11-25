from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date


class StudentReservation(models.Model):
    _name = "student.reservation"
    _description = "Student reservation"

    name = fields.Char('Name', compute="_compute_name", store=True, readonly=True)
    ref = fields.Char(string='Reference', related='admission_id.name')
    student_id = fields.Many2one('res.partner', string='Student', required=True,
                                 domain=[('is_student', '=', True)])
    sport_id = fields.Many2one(
        'product.product', string="Sport Name", domain=[('is_sportname', '=', True)])
    level_id = fields.Many2one('res.partner', string="Sport Center", domain=[
        ('is_sport', '=', True)])
    trainer_id = fields.Many2one(comodel_name='res.partner', domain=[('is_coach', '=', True)], string='Coach')
    duration = fields.Float("Duration(Days)", compute="_compute_spend_time")
    state = fields.Selection([
        ('yet', 'Yet to come'),
        ('today', 'Today'),
        ('finished', 'Finished'), ],
        string='State',
        copy=False, default="yet", store=True)
    is_finished = fields.Boolean()

    check_register = fields.Boolean('Check Register')
    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
    color = fields.Integer()
    admission_id = fields.Many2one('student.admission')
    is_vip = fields.Boolean(string='VIP')

    @api.model
    def update_reservation_states(self):
        """Cron job to update the state of reservations."""
        current_date = datetime.now().date()  # Get the current date only (without time)
        reservations = self.search([])

        for reservation in reservations:
            if reservation.start_date and reservation.end_date:
                start_date = reservation.start_date.date()  # Extract the date part of start_date
                end_date = reservation.end_date.date()  # Extract the date part of end_date

                if current_date < start_date:
                    reservation.state = 'yet'
                elif start_date == current_date:  # Compare only the day
                    reservation.state = 'today'
                elif current_date > end_date:
                    reservation.state = 'finished'

    @api.depends('trainer_id', 'student_id')
    def _compute_name(self):
        for record in self:
            coach_name = record.trainer_id.name if record.trainer_id else "No Coach"
            student_name = record.student_id.name if record.student_id else "No Student"
            record.name = f"{student_name} with {coach_name}"

    @api.depends('start_date', 'end_date')
    def _compute_spend_time(self):
        for record in self:
            if record.start_date and record.end_date:
                # Calculate the number of days (including fractions of days)
                delta = record.end_date - record.start_date
                record.duration = delta.total_seconds() / 3600  # Convert seconds to days
            else:
                record.duration = 0.0

    @api.constrains('trainer_id', 'start_date', 'end_date')
    def _check_trainer_availability(self):
        for record in self:
            if record.trainer_id and record.start_date and record.end_date:
                # Search for overlapping reservations for the same trainer
                overlapping_reservations = self.search([
                    ('trainer_id', '=', record.trainer_id.id),
                    ('id', '!=', record.id),  # Exclude the current record
                    ('start_date', '<=', record.end_date),  # Overlap condition
                    ('end_date', '>=', record.start_date)  # Overlap condition
                ])
                for over_res in overlapping_reservations:
                    if over_res.is_vip:
                        raise ValidationError(
                            f"There is a vip reservation done in this appointment."
                        )

                if overlapping_reservations and record.is_vip:
                    raise ValidationError(
                        f"There is some reservations in this time for this couch, choose another empty appointment."
                    )
                if len(overlapping_reservations) >= 5:
                    raise ValidationError(
                        f"Trainer {record.trainer_id.name} already has 5 reservations in this time frame."
                    )

    def unlink(self):
        for record in self:
            if record.state == 'finished':
                raise ValidationError(_("You cannot delete a reservation that is in the 'Finished' state."))
        return super(StudentReservation, self).unlink()

    #
    # @api.onchange('trainer_id')
    # def _onchange_trainer_id(self):
    #     if self.trainer_id and self.student_id:
    #         self.student_id.trainer_id = self.trainer_id.id

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         if vals.get('name', _('New')) == _('New'):
    #             vals['name'] = self.env['ir.sequence'].next_by_code(
    #                 'student.reservation') or _('New')
    #     res = super(Studentreservation, self).create(vals_list)
    #     portal_wizard_obj = self.env['portal.wizard']
    #     created_portal_wizard = portal_wizard_obj.create({})
    #     if created_portal_wizard and res.email:
    #         portal_wizard_user_obj = self.env['portal.wizard.user']
    #         wiz_user_vals = {
    #             'wizard_id': created_portal_wizard.id,
    #             'partner_id': res.student_id.id,
    #             'email': res.student_id.email,
    #         }
    #         created_portal_wizard_user = portal_wizard_user_obj.create(wiz_user_vals)
    #         if created_portal_wizard_user:
    #             created_portal_wizard_user.action_grant_access()
    #     return res
