# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    ThinkOpen Solutions Brasil
#    Copyright (C) Thinkopen Solutions <http://www.tkobr.com>.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import json
from openerp import models, fields, api, _
import datetime
from odoo.exceptions import Warning as UserError


class AccountExpenseType(models.Model):
    _name = 'account.expense.type'

    name = fields.Char('Name')
    expense_type = fields.Selection([('c', 'Customer Inovice'), ('s', 'Supplier Invoice'), ('b', 'Both')],
                                    required=True, default='b', string='InvoiceType')


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def post(self):
        res = super(AccountPayment, self).post()
        for res in self:
            for invoice in res.invoice_ids:
                if invoice.type == 'out_invoice':
                    invoice.move_id.date = datetime.datetime.now()
                    invoice.move_id.state = 'posted'
                    for move_line in invoice.move_id.line_ids:
                        if move_line.credit > 0:
                            move_line.date_maturity = invoice.move_id.date
        return res

    @api.model
    def create(self, vals):
        res = super(AccountPayment, self).create(vals)
        if vals.get('communication'):
            invoice = self.env['account.invoice'].search([('number','=', vals.get('communication'))])
            if invoice:
                invoice_payment_vals = {
                    'payment_date':vals.get('payment_date'),
                    'amount':vals.get('amount'),
                    'name':res,
                    'invoice_id':invoice.id
                }
                self.env['invoice.payment.info'].create(invoice_payment_vals)
        return res


class InvoicePaymentInfo(models.Model):
    _name = 'invoice.payment.info'
    _description = 'Invoice Payment Details'

    payment_date = fields.Date(string='Payment Date', copy=False)
    name = fields.Char('Name', copy=False)
    invoice_id = fields.Many2one('account.invoice', string='Invoice ID', copy=False)
    currency_id = fields.Many2one('res.currency', related='invoice_id.currency_id', readonly=True,
        help='Utility field to express amount currency')
    amount = fields.Monetary(string='Amount', copy=False, required=True, currency_field='currency_id')


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    expense_type_id = fields.Many2one('account.expense.type', string=u'Expense Type')
    payment_line = fields.One2many('invoice.payment.info', 'invoice_id', string="Invoice Payment Lines")
    payment_date = fields.Date(related='payment_line.payment_date', string='Payment Date')

    # set move date
    @api.multi
    def action_invoice_paid(self):
        # lots of duplicate calls to action_invoice_paid, so we remove those already paid
        to_pay_invoices = self.filtered(lambda inv: inv.state != 'paid')
        result = super(AccountInvoice, self).action_invoice_paid()
        for invoice in to_pay_invoices:
            if invoice.move_id:
                if invoice.type == 'out_invoice':
                    invoice.move_id.date = datetime.datetime.now()
                    invoice.move_id.state = 'posted'
                    for move_line in invoice.move_id.line_ids:
                        if move_line.credit > 0:
                            move_line.date_maturity = invoice.move_id.date
        return result

    # set account Account Move to unposted
    def action_invoice_re_open(self):
        result = super(AccountInvoice, self).action_invoice_re_open()
        if self.type in ('out_invoice', 'out_refund'):
            self.move_id.write({'state': 'draft'})
        return result

    @api.multi
    def update_history(self):
        payment_obj = self.env['account.payment']
        inv_obj = self.env['account.invoice']
        invoices = inv_obj.search([])
        invoices = set(invoices)
        for invoice in invoices:
            if invoice.payments_widget != u'false':
                info = json.loads(invoice.payments_widget)
                for content in info.get('content'):
                    for data in content:
                        if data == 'payment_id':
                            payment_id = content[data]
                            payment_id = payment_obj.search([('id','=',int(payment_id))])
                        if data == 'date':
                            payment_date = content[data]
                        if data == 'amount':
                            amount = content[data]
                        if data == 'name':
                            name = content[data]
                    invoice_payment_vals = {
                        'payment_date':payment_date,
                        'amount':amount,
                        'name':name,
                        'invoice_id':invoice.id,
                        'currency_id':payment_id.currency_id.id
                    }
                    self.env['invoice.payment.info'].create(invoice_payment_vals)
        return True


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    service_type_id = fields.Many2one(
        'br_account.service.type', related='product_id.service_type_id', string=u'Tipo de Serviço')
