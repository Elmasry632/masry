from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date


class StudentReservation(models.Model):
    _name = "student.reservation"
    _description = "Trainee reservation"

    name = fields.Char('Name', compute="_compute_name", store=True, readonly=True)
    ref = fields.Char(string='Reference', related='admission_id.name')
    student_id = fields.Many2one('res.partner', string='Trainee', required=True,
                                 domain=[('is_student', '=', True)])
    sport_id = fields.Many2one(
        'product.product', string="Sport Name", domain=[('is_sportname', '=', True)])
    level_id = fields.Many2one('res.partner', string="Sport Center", domain=[
        ('is_sport', '=', True)])
    trainer_id = fields.Many2one(comodel_name='res.partner', domain=[('is_coach', '=', True)], string='Coach')

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
    day_name = fields.Char(string='Day', compute='_compute_day_name', store=True)
    color = fields.Integer()
    admission_id = fields.Many2one('student.admission')
    is_vip = fields.Boolean(string='VIP')
    c_level_id = fields.Many2one('level.level', string='Level', related='admission_id.c_level_id')
    student_age = fields.Integer(related='admission_id.age')

    @api.depends('start_date')
    def _compute_day_name(self):
        for record in self:
            if record.start_date:
                # Use strftime to format the date as day name
                record.day_name = record.start_date.strftime('%A')  # e.g., Monday
            else:
                record.day_name = ''

    def action_finish(self):
        for rec in self:
            rec.state = 'finished'

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

    def action_change_details(self):
        """Opens the reservation change wizard."""
        self.ensure_one()  # Ensure only one record is selected
        view_id = self.env.ref('bi_sport_center_management.reservation_change_wizard_form').id
        context = self.env.context.copy()
        context['active_id'] = self.id
        return {
            'name': _('Change Reservation Details'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'reservation.change.wizard',  # Replace with your wizard model name
            'view_id': view_id,
            'context': context,
            'target': 'new',
        }

    # @api.constrains('trainer_id', 'start_date', 'end_date')
    # def _check_trainer_availability(self):
    #     for record in self:
    #         if record.trainer_id and record.start_date and record.end_date:
    #             overlapping_reservations = self.search([
    #                 ('trainer_id', '=', record.trainer_id.id),
    #                 ('id', '!=', record.id),
    #                 ('start_date', '<=', record.end_date),
    #                 ('end_date', '>=', record.start_date)
    #             ])
    #             vip_reservations = overlapping_reservations.filtered(lambda r: r.is_vip)
    #
    #             if vip_reservations:
    #                 # Trigger the confirmation wizard
    #                 self.env['reservation.conflict.wizard'].create({
    #                     'trainer_id': record.trainer_id.id,
    #                     'conflict_message': "There is a VIP reservation in this time. Do you want to proceed?"
    #                 }).with_context(active_id=record.id).action_open_dialog()
    #                 return
    #
    #             if len(overlapping_reservations) >= 5:
    #                 # Trigger the confirmation wizard for capacity
    #                 self.env['reservation.conflict.wizard'].create({
    #                     'trainer_id': record.trainer_id.id,
    #                     'conflict_message': f"Trainer {record.trainer_id.name} already has 5 reservations in this time frame. Do you want to proceed?"
    #                 }).with_context(active_id=record.id).action_open_dialog()
    #                 return

    def unlink(self):
        for record in self:
            if record.state == 'finished':
                raise ValidationError(_("You cannot delete a reservation that is in the 'Finished' state."))
            if record.admission_id.state == 'student':
                raise ValidationError(
                    _("You cannot delete a reservation after creating invoice, but you can still edit your reservation.."))

        return super(StudentReservation, self).unlink()

    #
    # @api.onchange('trainer_id')
    # def _onchange_trainer_id(self):
    #     if self.trainer_id and self.student_id:
    #         self.student_id.trainer_id = self.trainer_id.id

    @api.model_create_multi
    def create(self, vals_list):
        res = super(StudentReservation, self).create(vals_list)

        return res
