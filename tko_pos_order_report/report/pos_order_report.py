# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp import tools
from openerp.osv import fields, osv


class report_pos_order_tko(osv.osv):
    _name = "report.pos.order.tko"
    _description = "Point of Sale Orders Statistics"
    _auto = False

    _columns = {
        'date': fields.datetime('Date Order', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=True),
        'state': fields.selection(
            [('draft', 'New'), ('paid', 'Closed'), ('done', 'Synchronized'), ('invoiced', 'Invoiced'),
             ('cancel', 'Cancelled')],
            'Status'),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
        'user_id': fields.many2one('res.users', 'Salesperson', readonly=True),
        'location_id': fields.many2one('stock.location', 'Location', readonly=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
        'nbr': fields.integer('# of Lines', readonly=True),  # TDE FIXME master: rename into nbr_lines
        'journal_id': fields.many2one('account.journal', 'Journal'),
        'order_id': fields.many2one('pos.order', 'Order'),
        'total_discount': fields.float('Total Discount', readonly=True),
        'total_liquid': fields.float('Total Liquid', readonly=True),
        'average_price': fields.float('Average Price', readonly=True, group_operator="avg"),
        'order_id': fields.many2one('pos.order', 'Order', readonly=True),
        'order_type': fields.char(related='order_id.order_type', string=u'Internal Reference', readonly=True),

    }
    _order = 'date desc'

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_pos_order_tko')
        cr.execute("""
            create or replace view report_pos_order_tko as (
                select
                    min(l.id) as id,
                    count(*) as nbr,
                    s.date_order as date,
                    sum(l.qty * u.factor) as product_qty,
                    sum(l.qty * l.price_unit) as price_total,
                    sum((l.qty * l.price_unit) * (l.discount / 100) + coalesce((s.discount_on_order / s.no_lines ),0.0)) as total_discount,
                    sum(l.line_subototal) - coalesce(sum(s.discount_on_order / s.no_lines ),0.0) as total_liquid,
                    (sum(l.qty*l.price_unit)/sum(l.qty * u.factor))::decimal as average_price,
                    sum(cast(to_char(date_trunc('day',s.date_order) - date_trunc('day',s.create_date),'DD') as int)) as delay_validation,
                    s.partner_id as partner_id,
                    s.state as state,
                    s.user_id as user_id,
                    s.location_id as location_id,
                    s.company_id as company_id,
                    s.sale_journal as sale_journal,
                    l.product_id as product_id,
                    pt.categ_id as product_categ_id,
                    l.order_id as order_id,
                    s.order_type as order_type,
                    a.id as bank_statement_id,
                    al.id as bank_statement_line_id
                    s.session_id as session_id,
                    s.journal_id as journal_id,
                    s.account_move as account_move,
                    s.discount_card_name as discount_card,
                    s.discount_card_type as discount_type,
                    s.discount_card_value as discount_value,
                    s.discount_on_order as discount_on_order,
                    m.move_id as account_move_line_id,
                    
                from pos_order_line as l
                    left join pos_order s on (s.id=l.order_id)
                    left join product_product p on (p.id=l.product_id)
                    left join product_template pt on (pt.id=p.product_tmpl_id)
                    left join product_uom u on (u.id=pt.uom_id)
                    left join pos_discount_cards d on (d.id=s.discount_card_id)
                    left join account_bank_statement_line al on (al.pos_statement_id=s.id)
                    left join account_bank_statement a on (a.id=al.statement_id)
                    left join account_move_line m on (m.statement_id=al.statement_id)
                    
                group by
                    s.date_order, s.partner_id,s.state, pt.categ_id,
                    s.user_id,s.location_id,s.company_id,s.sale_journal,l.product_id,s.create_date,l.order_id,s.no_lines,s.discount_on_order,l.line_subototal,
                    s.order_type,s.statement_id,s.session_id,s.journal_id,s.account_move,s.discount_card_name,s.discount_card_type,s.discount_on_order,
                    m.move_id,a.id,al.id
                having
                    sum(l.qty * u.factor) != 0)""")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
