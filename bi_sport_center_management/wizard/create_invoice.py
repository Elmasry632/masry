# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import ValidationError

<<<<<<< HEAD

=======
>>>>>>> 82abafd9f08b9e97473ef0f8668618f5fcdd8639
class CreateInvoice(models.Model):
    _name = "create.invoice"
    _description = "Student Invoice"

    def action_create_invoice(self):
        admission_id = self.env['student.admission'].browse(self._context.get('active_id'))
        if admission_id:
<<<<<<< HEAD
            sale_journals = self.env['account.journal'].sudo().search([('type', '=', 'sale')])
=======
            sale_journals = self.env['account.journal'].sudo().search([('type','=','sale')])
>>>>>>> 82abafd9f08b9e97473ef0f8668618f5fcdd8639
            invoice = self.env['account.move'].create({
                'invoice_origin': admission_id.name or '',
                'move_type': 'out_invoice',
                'ref': admission_id.name or '',
<<<<<<< HEAD
                'journal_id': sale_journals and sale_journals[0].id or False,
                'partner_id': admission_id.student_id.id,
                'invoice_date': fields.date.today(),
                'currency_id': admission_id.student_id.currency_id.id or self.env.user.currency_id.id,
                'company_id': self.env.user.company_id.id or False,
            })

            # Calculate quantity in months based on duration and a predefined number of days per month
            days_per_month = 31  # Adjust this value as needed
            invoice_line_quantity = (admission_id.duration + days_per_month - 1) // days_per_month

            if admission_id.sport_id and admission_id.sport_id:
                invoice.write({'invoice_line_ids': [
                    (0, 0, {
                        'product_id': admission_id.sport_id.id,
                        'name': admission_id.sport_id.display_name or '',
                        'product_uom_id': admission_id.sport_id.uom_id.id,
                        'price_unit': admission_id.sport_id.lst_price,
                        'quantity': invoice_line_quantity,  # Use calculated quantity in months
                        'move_name': admission_id.name or '',
                    })]})
            if invoice:
                admission_id.is_invoiced = True
=======
                'journal_id':sale_journals and sale_journals[0].id or False ,
                'partner_id': admission_id.student_id.id,
                'invoice_date': fields.date.today(),
                'currency_id': admission_id.student_id.currency_id.id or self.env.user.currency_id.id,
                'company_id': self.env.user.company_id.id or False ,
            })
            if admission_id.sport_id and admission_id.sport_id:
                invoice.write({'invoice_line_ids': [
                    (0,0, {
                        'product_id':admission_id.sport_id.id,
                        'name': admission_id.sport_id.display_name or '',
                        'product_uom_id': admission_id.sport_id.uom_id.id,
                        'price_unit': admission_id.sport_id.lst_price,
                        'quantity': admission_id.duration,
                        'move_name': admission_id.name or '',
                })]})
            if invoice:
                admission_id.is_invoiced = True                
>>>>>>> 82abafd9f08b9e97473ef0f8668618f5fcdd8639
        else:
            raise ValidationError('Admission Registration not found!')
