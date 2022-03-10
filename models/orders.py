# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, float_repr
from datetime import date
import time
# import fcntl
# import socket
# import struct
# import macpath
from uuid import getnode as get_mac
from odoo.exceptions import UserError, ValidationError


class SaleOrderNegative(models.Model):
    _name = "sale.order.negative"

    name = fields.Char('TripId')
    amount = fields.Char('COST')


class SaleOrder(models.Model):
    _inherit = "sale.order"

    rehla_id = fields.Char('Rehla Id')
    trip_id = fields.Char('Trip Id')
    passenger_id = fields.Char('Passenger Id')
    reh_driver_id = fields.Char('Driver Id')
    rehla_uniq_id = fields.Char(string='Rehla Unique Id')
    vat_Value = fields.Float(string="VATValue")
    driver_revenue = fields.Float(string="DriverRevenue")
    tax_value_system = fields.Float(string="TaxValueAndSystemRevenue")
    add_tax_amount = fields.Float(string="add Tax Amount")
    vat_percentage = fields.Float(string="VATPercentage")
    percentage = fields.Float(string="Percentage")
    our_caliculate = fields.Float(string='Our Caliculation')
    updated_sale = fields.Boolean(string="Update Sale")
    car_categ = fields.Selection([
        ('0', 'None'),
        ('1', 'Go'),
        ('2', 'Taxi'),
        ('3', 'VIP'),
        ('4', 'Family'),
        ('5', 'Ladies'),
        ('6', 'Go Plus'),
        ('7', 'Family Plus'),
    ], string='Car Category', readonly=True, copy=False, index=True, track_visibility='onchange',
        track_sequence=3,
    )

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            print(order.add_tax_amount,'order.add_tax_amount')
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                # 'amount_total': amount_untaxed + amount_tax+order.add_tax_amount,
                'amount_total': amount_untaxed + amount_tax,
            })

class SalesUpload(models.Model):
    _inherit = 'sales.upload'

    def send_payment_transactions(self):
        print('fdgdfg')
        import json
        import requests
        from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
        if self.env['json.payment.configuration'].search([]):
            link = self.env['json.payment.configuration'].search([])[-1].name
            # responce = requests.get(link)
            if link:
                responce = requests.get(link)
                line_data = json.loads(responce.text)
                for each in line_data['model']:
                    print('Hello', each)
                    if each['Name']:
                        if not self.env['transaction.report'].sudo().search([('trip_id', '=', each['TripId'])]):
                            if each['CreationDate']:
                                # if each['TransactionDate']:
                                invoice_date = each['CreationDate'].split('T')[0].split('-')
                                month = invoice_date[1]
                                day = invoice_date[2]
                                year = invoice_date[0]
                            else:
                                day = datetime.today().day
                                month = datetime.today().month
                                year = datetime.today().year
                            # invoice_date = each['CreationDate'].split('T')[0].split('-')
                            month = invoice_date[1]
                            day = invoice_date[2]
                            year = invoice_date[0]
                            vendor = self.env['res.partner'].sudo().search([('name', '=', each['Name']),('reh_driver_id', '=', each['IdentityNumber'])])
                            if not vendor and each['Name']:
                                vendor = self.env['res.partner'].sudo().create({
                                    'name': each['Name'],
                                    'reh_driver_id': each['IdentityNumber'],
                                    'mobile': each['PhoneNumber'],
                                    # 'user_id': each['UserId'],
                                    'type_of_customer': 'b_c',
                                    'email': each['Email'],
                                    'schema_id': 'IQA',
                                    'schema_id_no': 'xxxx'
                                })

                            if vendor:
                                self.env['transaction.report'].sudo().create({
                                    "rehla_id": str(each['Id']),
                                    "trip_id": str(each['TripId']),
                                    "reservation_id": each['ReservationId'],
                                    "vat_amount": each['VATAmount'],
                                    "reh_driver_id": str(each['IdentityNumber']),
                                    "email": each['Email'],
                                    "mobile": each['PhoneNumber'],
                                    "amount": each['Amount'],
                                    "driver_name": vendor[0].id,
                                    "create_date": str(year) + '-' + str(month) + '-' + str(day), })
                                for each_inv in self.env['account.move'].sudo().search(
                                        [('partner_id', '=', vendor[0].id), ('state', '!=', 'cancel')]):
                                    pmt_wizard = self.env['account.payment.register'].with_context(
                                        active_model='account.move',
                                        active_ids=each_inv.ids).create({
                                        'payment_date': year + '-' + month + '-' + day,
                                        'journal_id': self.env['account.journal'].search(
                                            [('name', '=', 'Cash'), ('company_id', '=', 1)]).id,
                                        'payment_method_id': self.env.ref(
                                            'account.account_payment_method_manual_in').id,
                                        'amount': each['Amount'],
                                    })
                                    pmt_wizard._create_payments()
                                    print(pmt_wizard, vendor.name)

    def send_to_approval(self):

        import json
        import requests
        import base64
        from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
        if self.env['json.configuration'].search([]):
            link = self.env['json.configuration'].search([])[-1].name
            responce = requests.get(link)
            print('dfdddgdfgdf111')
            if responce:

                if self.env['sale.order'].sudo().search([('trip_id', '!=', False)]):
                    last_trip = self.env['sale.order'].sudo().search([])[0].trip_id
                    print(last_trip, 'last_trip')
                    # "https: // apiv2.rehlacar.com / api / GetTripsReportForERP?LastTripId =%s" % last_trip
                    # responce = requests.get("https://apiv2.rehlacar.com/api/GetTripsReportForERP?LastTripId=%s" % last_trip)

                    # responce = requests.get("https://apiv2.rehlacar.com/api/GetTripsReportForERP?LastTripId=%s" % last_trip)
                    responce = requests.get(link.rsplit('=')[0] + "=%s" % last_trip)
                else:
                    # responce = requests.get("https://apiv2.rehlacar.com/api/GetTripsReportForERP?LastTripId=78940")
                    responce = requests.get(link)

                # responce = selfs.get("http://rehlaapi.native-tech.co/api/GetTripsReportForERP")
                #####################################3
                # responce = selfs.get("http://5.189.161.117:8069/Estimate/Orders?id=1")
                # line_data = json.loads(rec['data'])
                # current_u = http.self.env['ir.config_parameter'].get_param('web.base.url') + http.self.httpself.full_path
                # responce = selfs.get(self.httpself.__dict__['url'])
                if responce:
                    print('dfdddgdfgdf2222')
                    line_data = json.loads(responce.text)
                    # line_data = line_data['model']
                    order = self.env['sale.order']
                    line_data['model'].reverse()
                    # print(line_data)
                    i = 0
                    for each in line_data['model']:
                        # inb = self.env['account.move']
                        # inb1 = self.env['account.move']
                        # move_id = self.env['account.move']
                        if each['TripCost'] < 0:
                            print(each['TripCost'])
                            mm = self.env['sale.order.negative'].create(
                                {'amount': str(each['TripCost']), 'name': str(each['TripId'])})
                            print(mm, 'lllllllllllll')
                            continue
                        print(each['TripCost'], 'Trip')
                        # if each['TripCost'] != '78941':

                        if i <= 100:
                            inb = self.env['account.move']
                            inb1 = self.env['account.move']
                            move_id = self.env['account.move']
                            if each['DriverId']:
                                if not self.env['res.partner'].sudo().search(
                                        [('reh_driver_id', '=', each['DriverId'])]):
                                    driver_id = self.env['res.partner'].sudo().create({
                                        'name': each['DriverName'],
                                        # Ù…Ø§Ù‡Ø±
                                        # str(self.lineEdit_2.text()).decode("utf-8")
                                        # 'passenger_name': each['DriverName'].encode('utf8'),
                                        'reh_driver_id': str(each['DriverId']),
                                        'mobile': each['DriverPhoneNumber'],
                                        'email': each['DriverEmail'],
                                        'type_of_customer': 'b_c',
                                        'schema_id': 'IQA',
                                        'schema_id_no': 'xxxx'
                                        # 'supplier':True

                                    })
                                else:
                                    driver_id = self.env['res.partner'].sudo().search(
                                        [('reh_driver_id', '=', each['DriverId'])])

                            if driver_id:
                                if not self.env['purchase.order'].sudo().search([('trip_id', '=', each['TripId'])]):
                                    product_p_line = []

                                    # tax_ids = self.env['account.tax'].search([('name', '=', 'VAT 15%'),('type_tax_use','=','purchase')])
                                    # tax_ids += self.env['account.tax'].search([('name', '=', 'Percentage 7%'),('type_tax_use','=','purchase')])

                                    excluded_value = 0
                                    basic_value = 0
                                    price_unit = 0

                                    transportation_aut = each['TransportAuthorityFee']
                                    airport_additional = each['AirportAdditionalFees']
                                    distance_amount = each['Distance'] * each['KMPrice']
                                    print(each['TripId'])
                                    actual = distance_amount + each['CaptainPounce'] + each['TransportAuthorityFee'] + \
                                             each[
                                                 'AirportAdditionalFees'] + each['MinimumPay']
                                    # 52.5###
                                    # tax_value_system = actual * 7 / 100
                                    tax_value_system = actual * each['Percentage'] / 100
                                    # 3.67####
                                    application_fee = tax_value_system
                                    coupon_value = each['CouponValue']
                                    actual_cali = actual + tax_value_system - each['CouponValue']
                                    # value_added = actual_cali * 15 / 100
                                    value_added = actual_cali * each['VATPercentage'] / 100

                                    trip_cost = each['TripCost'] - each['CouponValue']
                                    captain_cost = trip_cost - transportation_aut - airport_additional - tax_value_system + coupon_value - value_added
                                    price_unit = captain_cost

                                    # if tax_ids:
                                    #     tax = 0
                                    #     for eachs in tax_ids:
                                    #         if eachs.children_tax_ids:
                                    #             for ch in eachs.children_tax_ids:
                                    #                 tax += ch.amount
                                    #         else:
                                    #             tax += eachs.amount
                                    #     value = tax
                                    #     # basic_value = each['DriverRevenue'] * value / 100
                                    #     # basic_value1 = each['DriverRevenue'] - basic_value
                                    #     #
                                    #     # # line.basic_value = basic_value
                                    #     # # line.basic_value = basic_value
                                    #     #
                                    #     # # line.total_amount = line.quantity * line.amount
                                    #     # excluded_value = 1 * basic_value1
                                    #
                                    #     value = 100 + tax
                                    #     value = value
                                    #     basic_value = each['TripCost'] * 100 / value
                                    #     price_unit = basic_value / 1
                                    print(self.env['product.product'].sudo().search(
                                        [('name', '=', 'Driver Expense')]).id, 'product')

                                    print(self.env['uom.uom'].sudo().search([('name', '=', 'Units')]), 'UOMs')

                                    # line = (0, 0, {
                                    #     'product_id': self.env['product.product'].sudo().search(
                                    #         [('name', '=', 'Driver Expense')]).id,
                                    #     'product_qty': 1,
                                    #     'product_uom_qty': 1,
                                    #     'date_planned': datetime.now().date().strftime(DEFAULT_SERVER_DATE_FORMAT),
                                    #     # 'price_unit':each['DriverRevenue'],
                                    #     # 'price_unit':excluded_value,
                                    #     'price_unit':price_unit,
                                    #     'basic_value': basic_value,
                                    #     'trip_cost': each['DriverRevenue'],
                                    #     'display_type' :'line_section',
                                    #     # 'taxes_id':[(6, 0, tax_ids.ids)],
                                    #     'name': self.env['product.product'].sudo().search([('name', '=', 'Driver Expense')]).name,
                                    #     'product_uom': (self.env['uom.uom'].sudo().search([('name', '=', 'Units')])).id,
                                    #
                                    # })
                                    #
                                    #
                                    # product_p_line.append(line)

                                    # po = self.env['purchase.order'].sudo().create({
                                    #     'partner_id': driver_id.id,
                                    #     'trip_id': str(each['TripId']),
                                    #     'transportation_aut': -transportation_aut,
                                    #     'airport_additional': -airport_additional,
                                    #     'taxvalue_system': -tax_value_system,
                                    #     'value_added': -value_added,
                                    #     'application_fee': -application_fee,
                                    #     'coupon_value': +coupon_value,
                                    #     # 'reh_driver_id':driver_id.reh_driver_id,
                                    #     'mobile': each['DriverPhoneNumber'],
                                    #
                                    #     # 'rehla_id': each['Reservations'][0]['Id'],
                                    #     # 'order_line':product_p_line,
                                    #     'order_line': [(0, 0, {
                                    #         # 'name': self.env['product.product'].sudo().search([('name', '=', 'Dr0iver Expense')]).name,
                                    #         'name': self.env['product.product'].sudo().search(
                                    #             [('name', '=', 'Driver Expense')]).name,
                                    #         'product_id': self.env['product.product'].sudo().search(
                                    #             [('name', '=', 'Driver Expense')]).id,
                                    #         'product_qty': 1,
                                    #         'product_uom': self.env['uom.uom'].sudo().search(
                                    #             [('name', '=', 'Units')]).id,
                                    #         'price_unit': price_unit,
                                    #         'basic_value': basic_value,
                                    #         'trip_cost': each['DriverRevenue'],
                                    #         # 'date_planned': time.strftime('%Y-%m-%d'),
                                    #         'date_planned': datetime.now().date().strftime(DEFAULT_SERVER_DATE_FORMAT),
                                    #     })],
                                    # })
                                    # po.sudo().button_confirm()
                                    #
                                    # j = self.env['account.payment.method'].sudo().search([('name', '=', 'Manual')])[0]
                                    # journal = self.env['account.journal'].sudo().search(
                                    #     [('name', '=', 'Cash'), ('company_id', '=', 1)])

                                    # if po.amount_total > 0:
                                    #     inb = po.sudo().automatic_bill_creation()
                                    #     # inb = po.invoice_ids
                                    #     if not po.invoice_ids:
                                    #         inb = self.env['account.move'].search([('purchase_id', '=', po.id)])
                                    #     else:
                                    #         inb = po.invoice_ids
                                    #     # inb.sudo().action_invoice_open()
                                    #     # inb.sudo().action_invoice_open()
                                    #     # for line in po.invoice_ids.invoice_line_ids:
                                    #     #     line.basic_value = basic_value
                                    #     # line.trip_cost = each['DriverRevenue']
                                    #     if each['Reservations'][0]['PaymentType'] == True :
                                    #       if inb:
                                    #           if inb.state == 'draft':
                                    #               if inb.amount_total >=0:
                                    #                    inb.action_post()
                                    #             # pmt_wizard = self.env['account.payment.register'].with_context(active_model='account.move',
                                    #             #                                                                active_ids=inb.ids).create({
                                    #             #     'payment_date': inb.date,
                                    #             #     'journal_id': self.env['account.journal'].search(
                                    #             #         [('name', '=', 'Cash'), ('company_id', '=', 1)]).id,
                                    #             #     'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
                                    #             #     'amount': inb.amount_total,
                                    #             #
                                    #             # })
                                    #             # pmt_wizard._create_payments()
                                    #
                                    #
                                    #
                                    #
                                    #
                                    #     # payment = self.env['account.payment'].sudo().create(
                                    #     #     {'partner_id': driver_id.id,
                                    #     #      'amount': po.amount_total,
                                    #     #      'payment_type': 'outbound',
                                    #     #      'payment_method_id': self.env.ref(
                                    #     #          'account.account_payment_method_manual_in').id,
                                    #     #      'journal_id': journal.id,
                                    #     #      'partner_type': 'supplier',
                                    #     #      # 'currency_id': self.currency_usd_id,
                                    #     #      'ref': po.name+'=>'+driver_id.name,
                                    #     #      # 'move_id': inb.id
                                    #     #
                                    #     #      })
                                    #     #
                                    #     # m = payment.sudo().action_post()
                                    #     # inb.action_post()

                            order = self.env['sale.order']
                            if each['Reservations']:
                                if not self.env['sale.order'].sudo().search(
                                        [('trip_id', '=', each['Reservations'][0]['TripId'])]):
                                    i = i + 1
                                    partner_id = self.env['res.partner'].sudo().search(
                                        [('passenger_id', '=', each['Reservations'][0]['PassengerId'])])
                                    if not partner_id:
                                        partner_id = self.env['res.partner'].sudo().create({
                                            'name': each['Reservations'][0]['PassengerName'].encode('utf8'),
                                            'passenger_id': each['Reservations'][0]['PassengerId'],
                                            'mobile': each['Reservations'][0]['PassengerPhoneNumber'],
                                            'email': each['Reservations'][0]['PassengerEmail'],
                                            'type_of_customer': 'b_c',
                                            # 'passenger_name': each['Reservations'][0]['PassengerName'],
                                            'schema_id': 'IQA',
                                            'schema_id_no': 'xxxx'

                                        })
                                    tax_ids = self.env['account.tax'].search(
                                        [('name', '=', 'VAT 15%'), ('type_tax_use', '=', 'sale')])
                                    # tax_ids += self.env['account.tax'].search(
                                    #     [('name', '=', 'Percentage 7%'), ('type_tax_use', '=', 'sale')])
                                    excluded_value = 0
                                    actual = 0
                                    # each['Distance']
                                    # each['KMPrice']
                                    # each['CaptainPounce']
                                    # each['TransportAuthorityFee']
                                    # each['AirportAdditionalFees']
                                    # each['MinimumPay']
                                    # each['CouponValue']
                                    distance_amount = each['Distance'] * each['KMPrice']
                                    # actual = distance_amount + each['CaptainPounce'] + each['TransportAuthorityFee'] + \
                                    #          each[
                                    #              'AirportAdditionalFees'] + each['MinimumPay']

                                    actual = distance_amount + each['CaptainPounce'] + each['MinimumPay']
                                    # 39.5
                                    # 2.765

                                    # tax_value_system = actual * 7 / 100
                                    # applicable_for = tax_value_system + actual - each['CouponValue']

                                    basic_value = 0
                                    # price_unit = 0
                                    # price_unit = applicable_for
                                    price_unit = actual
                                    print(price_unit, 'price unit')
                                    if tax_ids:
                                        tax = 0
                                        for eachs in tax_ids:
                                            if eachs.children_tax_ids:
                                                for ch in eachs.children_tax_ids:
                                                    tax += ch.amount
                                            else:
                                                tax += eachs.amount
                                        value = tax
                                        # basic_value = each['TripCost'] * value / 100
                                        # basic_value = each['TripCost'] * 100 / value
                                        # basic_value1 = each['TripCost'] - basic_value
                                        # line.basic_value = basic_value
                                        # line.basic_value = basic_value

                                        # line.total_amount = line.quantity * line.amount

                                        # value = tax
                                        # basic_value = applicable_for * value / 100

                                        # excluded_value = 1 * basic_value1

                                    product_line = []
                                    line = (0, 0, {
                                        'product_id': self.env['product.product'].sudo().search(
                                            [('name', '=', 'Rehla Car')]).id,
                                        'product_uom_qty': each['Reservations'][0]['SeatCount'],
                                        # 'price_unit': each['Reservations'][0]['SeatsCost'],
                                        # 'price_unit': each['TripCost'],
                                        'basic_value': basic_value,
                                        'trip_cost': each['TripCost'],
                                        # 'price_unit': excluded_value,
                                        'price_unit': price_unit,
                                        'name': self.env['product.product'].sudo().search(
                                            [('name', '=', 'Rehla Car')]).name,
                                        # 'tax_id': [(6, 0, tax_ids.ids)],
                                        'product_uom': (self.env['uom.uom'].sudo().search([('name', '=', 'Units')])).id,

                                    })
                                    product_line.append(line)
                                    # import datetime
                                    # date = each['CreationDate'].split('T')[0]
                                    # aDateTime = datetime.datetime.fromisoformat('2020-10-04 22:47:00')
                                    if each['CreationDate']:
                                        invoice_date = each['CreationDate'].split('T')[0].split('-')
                                        month = invoice_date[1]
                                        day = invoice_date[2]
                                        year = invoice_date[0]
                                    else:
                                        day = datetime.today().day
                                        month = datetime.today().month
                                        year = datetime.today().year
                                    vals = {
                                        'partner_id': partner_id.id,
                                        'car_categ': str(each['CarCategoryId']),
                                        'trip_id': str(each['Reservations'][0]['TripId']),
                                        'rehla_id': str(each['Reservations'][0]['Id']),
                                        'payment_type': str(each['Reservations'][0]['PaymentType']),
                                        'govt_char': each['TransportAuthorityFee'],
                                        'additional_airport': each['AirportAdditionalFees'],
                                        'status_of_trip': str(each['Reservations'][0]['StatusId']),
                                        'order_line': product_line,
                                        'mobile': each['Reservations'][0]['PassengerPhoneNumber'],
                                        'distance': each['Distance'],
                                        'per_km': each['KMPrice'],
                                        'vat_percentage': each['VATPercentage'],
                                        'percentage': each['Percentage'],
                                        'driver_revenue':each['DriverRevenue'],
                                        'reh_driver_id':each['DriverId'],
                                        'vat_Value':each['VATValue'],
                                        'tax_value_system': each['TaxValueAndSystemRevenue'],
                                        'bonus': each['CaptainPounce'],
                                        'transportation_aut': each['TransportAuthorityFee'],
                                        'airport_additional': each['AirportAdditionalFees'],
                                        'taxvalue_system': tax_value_system,
                                        'coupon_value': each['CouponValue'],
                                        'creation_date': str(year) + '-' + str(month) + '-' + str(day),
                                        'basic_fire': each['MinimumPay'],
                                    }
                                    order = self.env['sale.order'].sudo().create(vals)
                                    print(order, 'orderorder')

                                    custom_tax_ids = self.env['account.tax']

                                    # if order.transportation_aut:
                                    #     print('fcgfcg')
                                    #     Transportation_Tax = self.env['account.tax'].search(
                                    #         [('name', '=', 'Transportation Authority'), ('type_tax_use', '=', 'sale')])
                                    #     Transportation_Tax.amount = order.transportation_aut
                                    #     custom_tax_ids += Transportation_Tax
                                    #     for sale_line in order.order_line:
                                    #         sale_line.tax_id += Transportation_Tax
                                    # if order.airport_additional:
                                    #     print('fcgfcg')
                                    #     Airport_Tax = self.env['account.tax'].search(
                                    #         [('name', '=', 'Airport Additional'), ('type_tax_use', '=', 'sale')])
                                    #     Airport_Tax.amount = order.airport_additional
                                    #     custom_tax_ids += Airport_Tax
                                    #     for sale_line in order.order_line:
                                    #         sale_line.tax_id += Airport_Tax
                                    # if order:
                                    #     for sale_line in order.order_line:
                                    #         print('fcgfcg')
                                    #         # Vat_Custom = self.env['account.tax'].search([('name', '=', 'Vat Value')])
                                    #         Vat_Custom = self.env['account.tax'].search(
                                    #             [('name', '=', 'VAT 15%'), ('type_tax_use', '=', 'sale')])
                                    #         cal_amount = sale_line.price_unit + order.airport_additional + order.transportation_aut
                                    #         if each['Percentage']:
                                    #
                                    #             caliculate = cal_amount * each['Percentage'] / 100
                                    #             revenue_tax = self.env['account.tax'].search(
                                    #                 [('name', '=', 'Tax&System Revenue'), ('type_tax_use', '=', 'sale')])
                                    #             revenue_tax.amount = caliculate
                                    #             custom_tax_ids += revenue_tax
                                    #             for sale_line in order.order_line:
                                    #                 sale_line.tax_id += revenue_tax
                                    #         else:
                                    #             caliculate = 0
                                    #         cal_total = cal_amount + caliculate
                                    #         Coupon_Tax = self.env['account.tax'].search(
                                    #             [('name', '=', 'Coupon'), ('type_tax_use', '=', 'sale')])
                                    #         if order.coupon_value:
                                    #             Coupon_Tax.amount = -order.coupon_value
                                    #             custom_tax_ids += Coupon_Tax
                                    #             cal_total = cal_total + Coupon_Tax.amount
                                    #             for sale_line in order.order_line:
                                    #                 sale_line.tax_id += Coupon_Tax
                                    #         else:
                                    #             Coupon_Tax.amount = 0
                                    #             cal_total = cal_total - Coupon_Tax.amount
                                    #         if each['VATPercentage']:
                                    #             caliculates = cal_total * each['VATPercentage'] / 100
                                    #             Vat_Custom.amount = caliculates
                                    #             custom_tax_ids += Vat_Custom
                                    #             order.add_tax_amount = caliculates
                                    #             for sale_line in order.order_line:
                                    #                 sale_line.tax_id += Vat_Custom
                                    #     # for sale_line in order.order_line:
                                    #     #     sale_line.tax_id += custom_tax_ids
                                    #     #     if round(sale_line.trip_cost)< round(order.amount_total):
                                    #     #         if round(sale_line.trip_cost)+1 < round(order.amount_total):
                                    #     #             sale_line.tax_id = False
                                    #     #             order.our_caliculate = sale_line.price_unit
                                    #     #             sale_line.price_unit = order.driver_revenue
                                    #     #             print(order,'orderwwwwwwwwwwwwwwwwwwwww')
                                    #     #             custom_tax_ids = self.env['account.tax']
                                    #     #             order.updated_sale =True
                                    #     #             if order.transportation_aut:
                                    #     #                 print('fcgfcg')
                                    #     #                 Transportation_Tax = self.env['account.tax'].search(
                                    #     #                     [('name', '=', 'Transportation Authority'),
                                    #     #                      ('type_tax_use', '=', 'sale')])
                                    #     #                 Transportation_Tax.amount = order.transportation_aut
                                    #     #                 custom_tax_ids += Transportation_Tax
                                    #     #             if order.airport_additional:
                                    #     #                 print('fcgfcg')
                                    #     #                 Airport_Tax = self.env['account.tax'].search(
                                    #     #                     [('name', '=', 'Airport Additional'),
                                    #     #                      ('type_tax_use', '=', 'sale')])
                                    #     #                 Airport_Tax.amount = order.airport_additional
                                    #     #                 custom_tax_ids += Airport_Tax
                                    #     #             Vat_Custom = self.env['account.tax'].search(
                                    #     #                 [('name', '=', 'VAT 15%'), ('type_tax_use', '=', 'sale')])
                                    #     #             # cal_amount = sale_line.price_unit + order.airport_additional + order.transportation_aut
                                    #     #             cal_amount = order.driver_revenue + order.airport_additional + order.transportation_aut
                                    #     #             if each['Percentage']:
                                    #     #                 caliculate = cal_amount * each['Percentage'] / 100
                                    #     #                 revenue_tax = self.env['account.tax'].search(
                                    #     #                     [('name', '=', 'Tax&System Revenue'),
                                    #     #                      ('type_tax_use', '=', 'sale')])
                                    #     #                 revenue_tax.amount = caliculate
                                    #     #                 custom_tax_ids += revenue_tax
                                    #     #             else:
                                    #     #                 caliculate = 0
                                    #     #             cal_total = cal_amount + caliculate
                                    #     #             Coupon_Tax = self.env['account.tax'].search(
                                    #     #                 [('name', '=', 'Coupon'), ('type_tax_use', '=', 'sale')])
                                    #     #             if order.coupon_value:
                                    #     #                 Coupon_Tax.amount = -order.coupon_value
                                    #     #                 custom_tax_ids += Coupon_Tax
                                    #     #                 cal_total = cal_total + Coupon_Tax.amount
                                    #     #             else:
                                    #     #                 Coupon_Tax.amount = 0
                                    #     #                 cal_total = cal_total - Coupon_Tax.amount
                                    #     #             if each['VATPercentage']:
                                    #     #                 caliculates = cal_total * each['VATPercentage'] / 100
                                    #     #                 Vat_Custom.amount = caliculates
                                    #     #                 custom_tax_ids += Vat_Custom
                                    #     #                 order.add_tax_amount = caliculates
                                    #     #                 print('order','ordervvvvvvvvvvvvvv')
                                    #     #             sale_line.tax_id += custom_tax_ids
                                    #     #     if round(sale_line.trip_cost) > round(order.amount_total):
                                    #     #         if round(sale_line.trip_cost) > round(order.amount_total)+1:
                                    #     #             sale_line.tax_id = False
                                    #     #             order.our_caliculate =  sale_line.price_unit
                                    #     #             sale_line.price_unit =  order.driver_revenue
                                    #     #             print(order,'orderwwwwwwwwwwwwwwwwwwwww')
                                    #     #             custom_tax_ids = self.env['account.tax']
                                    #     #             order.updated_sale =True
                                    #     #             if order.transportation_aut:
                                    #     #                 print('fcgfcg')
                                    #     #                 Transportation_Tax = self.env['account.tax'].search(
                                    #     #                     [('name', '=', 'Transportation Authority'),
                                    #     #                      ('type_tax_use', '=', 'sale')])
                                    #     #                 Transportation_Tax.amount = order.transportation_aut
                                    #     #                 custom_tax_ids += Transportation_Tax
                                    #     #             if order.airport_additional:
                                    #     #                 print('fcgfcg')
                                    #     #                 Airport_Tax = self.env['account.tax'].search(
                                    #     #                     [('name', '=', 'Airport Additional'),
                                    #     #                      ('type_tax_use', '=', 'sale')])
                                    #     #                 Airport_Tax.amount = order.airport_additional
                                    #     #                 custom_tax_ids += Airport_Tax
                                    #     #             Vat_Custom = self.env['account.tax'].search(
                                    #     #                 [('name', '=', 'VAT 15%'), ('type_tax_use', '=', 'sale')])
                                    #     #             # cal_amount = sale_line.price_unit + order.airport_additional + order.transportation_aut
                                    #     #             cal_amount = order.driver_revenue + order.airport_additional + order.transportation_aut
                                    #     #             if each['Percentage']:
                                    #     #                 caliculate = cal_amount * each['Percentage'] / 100
                                    #     #                 revenue_tax = self.env['account.tax'].search(
                                    #     #                     [('name', '=', 'Tax&System Revenue'),
                                    #     #                      ('type_tax_use', '=', 'sale')])
                                    #     #                 revenue_tax.amount = caliculate
                                    #     #                 custom_tax_ids += revenue_tax
                                    #     #             else:
                                    #     #                 caliculate = 0
                                    #     #             cal_total = cal_amount + caliculate
                                    #     #             Coupon_Tax = self.env['account.tax'].search(
                                    #     #                 [('name', '=', 'Coupon'), ('type_tax_use', '=', 'sale')])
                                    #     #             if order.coupon_value:
                                    #     #                 Coupon_Tax.amount = -order.coupon_value
                                    #     #                 custom_tax_ids += Coupon_Tax
                                    #     #                 cal_total = cal_total + Coupon_Tax.amount
                                    #     #             else:
                                    #     #                 Coupon_Tax.amount = 0
                                    #     #                 cal_total = cal_total - Coupon_Tax.amount
                                    #     #             if each['VATPercentage']:
                                    #     #                 caliculates = cal_total * each['VATPercentage'] / 100
                                    #     #                 Vat_Custom.amount = caliculates
                                    #     #                 custom_tax_ids += Vat_Custom
                                    #     #                 order.add_tax_amount = caliculates
                                    #     #                 print('order','ordervvvvvvvvvvvvvv')
                                    #     #             sale_line.tax_id += custom_tax_ids
                                    #     print(order,'order')
                                    # # order.sudo().action_confirm()
                                    # # if order.status_of_trip != '4':
                                    # #     # invoice = order.action_invoice_create()
                                    # #     invoice = order._create_invoices()
                                    # #     # inb = self.env['account.move'].sudo().browse(invoice[0])
                                    # #     inb1 = invoice
                                    # #     # inb.sudo().action_invoice_open()
                                    # #     # inb.sudo().action_invoice_open()
                                    # #     for line in inb1.invoice_line_ids:
                                    # #         line.basic_value = basic_value
                                    # #         line.trip_cost = each['TripCost']
                                    # #     # inb.sudo().action_post()
                                    # #     # journal = self.env['account.journal'].sudo().search(
                                    # #     #     [('name', '=', 'Cash'), ('company_id', '=', 1)])
                                    # #     #
                                    # #     # payment = self.env['account.payment'].sudo().create(
                                    # #     #     {'partner_id': order.partner_id.id,
                                    # #     #      'amount': order.amount_total,
                                    # #     #      'payment_type': 'inbound',
                                    # #     #      'payment_method_id': self.env.ref(
                                    # #     #          'account.account_payment_method_manual_in').id,
                                    # #     #      'journal_id': journal.id,
                                    # #     #      'partner_type': 'customer',
                                    # #     #      # 'currency_id': self.currency_usd_id,
                                    # #     #      'ref': order.name + '=>' + order.partner_id.name,
                                    # #     #      # 'move_id': inb.id
                                    # #     #
                                    # #     #      })
                                    # #     # payment.sudo().action_post()
                                    # #
                                    # #     if inb1:
                                    # #         if inb1.state == 'draft':
                                    # #             if inb1.amount_total >= 0:
                                    # #                 inb1.action_post()
                                    # # inb1.action_post()
                                    # # pmt_wizard = self.env['account.payment.register'].with_context(
                                    # #     active_model='account.move',
                                    # #     active_ids=inb1.ids).create({
                                    # #     'payment_date': inb1.date,
                                    # #     'journal_id': self.env['account.journal'].search(
                                    # #         [('name', '=', 'Cash'), ('company_id', '=', 1)]).id,
                                    # #     'payment_method_id': self.env.ref(
                                    # #         'account.account_payment_method_manual_in').id,
                                    # #     'amount': inb1.amount_total,
                                    #
                                    # #
                                    # # })
                                    # # pmt_wizard._create_payments()

                                    if order:
                                        driv = each['DriverRevenue'] + each['VATValue']
                                        # self.env['profit.car.orders'].sudo().create({
                                        #     'date': datetime.today().date(),
                                        #     'passenger_id': order.partner_id.passenger_id,
                                        #     'trip_id': str(each['Reservations'][0]['TripId']),
                                        #     'rehla_id': str(each['Reservations'][0]['Id']),
                                        #     'reh_driver_id': str(driver_id.reh_driver_id),
                                        #     'driver_cost': each['DriverRevenue'],
                                        #     'trip_cost': each['TripCost'],
                                        #     'tax_amount': each['VATValue'],
                                        #     'profit': each['TripCost'] - driv,
                                        #     'passenger': order.partner_id.id,
                                        #     'driver': driver_id.id,
                                        #     'revenue_profit': each['TaxValueAndSystemRevenue']
                                        # })
                                        # percentage = 0
                                        # wallet_amount = 0
                                        # if each['Reservations'][0]['PaymentType'] == True:
                                        #     percentage = each['TripCost'] * 22 / 100
                                        #     wallet_amount = each['TripCost'] - percentage
                                        # if each['Reservations'][0]['PaymentType'] == False:
                                        #     # percentage = each['TripCost'] * 22 / 100
                                        #     wallet_amount = each['TripCost']
                                        #
                                        # self.env['wallet.amount'].sudo().create({
                                        #     'date': datetime.today().date(),
                                        #     'passenger_id': str(order.partner_id.id),
                                        #     'trip_id': str(each['Reservations'][0]['TripId']),
                                        #     'rehla_id': str(each['Reservations'][0]['Id']),
                                        #     'reh_driver_id': str(driver_id.reh_driver_id),
                                        #     'driver_cost': each['DriverRevenue'],
                                        #     'trip_cost': each['TripCost'],
                                        #     'driver_id': driver_id.id,
                                        #     'passenger': order.partner_id.id,
                                        #     'payment_type': str(each['Reservations'][0]['PaymentType']),
                                        #     'wallet_amount': wallet_amount
                                        # })
                                        # vals = {
                                        #     'journal_id': self.env['account.journal'].search(
                                        #         [('name', '=', 'Miscellaneous Operations'),
                                        #          ('company_id', '=', 1)]).id,
                                        #     'state': 'draft',
                                        #     'ref': driver_id.name
                                        # }
                                        # pay_id_list = []
                                        # move_id = self.env['account.move'].create(vals)
                                        # partner_id = driver_id.id
                                        # label = driver_id.name
                                        #
                                        # # if self.type_of_credit == False:
                                        # temp = (0, 0, {
                                        #     'account_id': self.env['account.account'].sudo().search(
                                        #         [('name', '=', 'Product Sales'),
                                        #          ('company_id', '=', 1)]).id,
                                        #     'name': label,
                                        #     'move_id': move_id.id,
                                        #     'date': datetime.today().date(),
                                        #     'partner_id': driver_id.id,
                                        #     'debit': wallet_amount,
                                        #     'credit': 0,
                                        # })
                                        # pay_id_list.append(temp)

                                        # acc = self.env['account.account'].sudo().search(
                                        #     [('name', '=', 'Account Receivable'),
                                        #      ('company_id', '=', 1)])
                                        # temp = (0, 0, {
                                        #     'account_id': acc.id,
                                        #     'name': label,
                                        #     'move_id': move_id.id,
                                        #     'date': datetime.today().date(),
                                        #     'partner_id': driver_id.id,
                                        #     'debit': 0,
                                        #     'credit': wallet_amount,
                                        # })
                                        # pay_id_list.append(temp)
                                        # move_id.line_ids = pay_id_list
                                        # if move_id.state == 'draft':
                                        #    move_id.sudo().action_post()


                                    else:
                                        order.sudo().action_cancel()


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # user_id = fields.Char(string='User Id')
    rehla_id = fields.Char('Rehla Id')
    trip_id = fields.Char('Trip Id')
    passenger_id = fields.Char('Passenger Id')
    reh_driver_id = fields.Char('Driver Id')
    rehla_uniq_id = fields.Char(string='Rehla Unique Id')


class ProfitCarOrders(models.Model):
    _inherit = 'profit.car.orders'

    rehla_id = fields.Char('Rehla Id')
    trip_id = fields.Char('Trip Id')
    passenger_id = fields.Char('Passenger Id')
    reh_driver_id = fields.Char('Driver Id')
    rehla_uniq_id = fields.Char(string='Rehla Unique Id')


class WalletAmount(models.Model):
    _inherit = 'wallet.amount'
    _order = 'id desc'

    rehla_id = fields.Char('Rehla Id')
    trip_id = fields.Char('Trip Id')
    passenger_id = fields.Char('Passenger Id')
    reh_driver_id = fields.Char('Driver Id')
    rehla_uniq_id = fields.Char(string='Rehla Unique Id')


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    rehla_id = fields.Char('Rehla Id')
    trip_id = fields.Char('Trip Id')
    passenger_id = fields.Char('Passenger Id')
    reh_driver_id = fields.Char('Driver Id')
    rehla_uniq_id = fields.Char(string='Rehla Unique Id')


class TransactionReport(models.Model):
    _inherit = 'transaction.report'
    _order = 'id desc'

    rehla_id = fields.Char('Rehla Id')
    trip_id = fields.Char('Trip Id')
    passenger_id = fields.Char('Passenger Id')
    reh_driver_id = fields.Char('Driver Id')
    rehla_uniq_id = fields.Char(string='Rehla Unique Id')


class WalletAmountReportLines(models.Model):
    _inherit = 'wallet.amount.report.lines'

    rehla_id = fields.Char('Rehla Id')
    trip_id = fields.Char('Trip Id')
    passenger_id = fields.Char('Passenger Id')
    reh_driver_id = fields.Char('Driver Id')
    rehla_uniq_id = fields.Char(string='Rehla Unique Id')


class AutomaticRehlaRecord(models.Model):
    _name = 'automatic.rehla.record'
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    start_date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    op_lines = fields.One2many('automatic.rehla.reclines', 'rec_lines')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('close', 'Closed'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'automatic.rehla.record') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('automatic.rehla.record') or _('New')
        return super(AutomaticRehlaRecord, self).create(vals)
        # if self:
        #     self.auto_confirm_all()
        # if rec:
        #     rec.auto_confirm_all()

    @api.onchange('start_date')
    def onchange_start_date(self):
        so_list = []
        for each_inv in self.env['sale.order'].search([('state', '=', 'draft')]):
            amount_final = 0
            if each_inv:
                for sale_line in each_inv.order_line:
                    Vat_Custom = self.env['account.tax'].search(
                        [('name', '=', 'VAT 15%'), ('type_tax_use', '=', 'sale')])
                    cal_amount = sale_line.price_unit + each_inv.airport_additional + each_inv.transportation_aut
                    cal_total = 0
                    amount_final = cal_amount
                    if each_inv.percentage:
                        caliculate = cal_amount * each_inv.percentage / 100
                        revenue_tax = self.env['account.tax'].search(
                            [('name', '=', 'Tax&System Revenue'), ('type_tax_use', '=', 'sale')])
                        cal_total = cal_amount + caliculate
                        amount_final+=caliculate
                    Coupon_Tax = self.env['account.tax'].search(
                        [('name', '=', 'Coupon'), ('type_tax_use', '=', 'sale')])
                    if each_inv.coupon_value:
                        Coupon_Tax.amount = each_inv.coupon_value
                        cal_total = cal_total + Coupon_Tax.amount
                        amount_final = amount_final+Coupon_Tax.amount
                    else:
                        Coupon_Tax.amount = 0
                        cal_total = cal_total + Coupon_Tax.amount
                        amount_final = amount_final- Coupon_Tax.amount
                    if each_inv.vat_percentage:
                        caliculates = cal_total * each_inv.vat_percentage / 100
                        amount_final +=caliculates
            so_dict = (0, 0, {
                'partner_id': each_inv.partner_id.id,
                'sale_id': each_inv.id,
                'trip_id': each_inv.trip_id,
                'rehla_id': each_inv.rehla_id,
                'state': each_inv.state,
                'amount': each_inv.amount_total,
                'final_amount':amount_final
            })
            so_list.append(so_dict)

        self.op_lines = so_list

    def auto_confirm_all(self):
        i = 0
        for each_inv in self.op_lines:

            # if i <= 1:
                if each_inv.sale_id.state == "draft":
                    # i += 1
                    custom_tax_ids = self.env['account.tax']

                    if each_inv.sale_id.transportation_aut:
                        print('fcgfcg')
                        Transportation_Tax = self.env['account.tax'].search([('name', '=', 'Transportation Authority'),('type_tax_use','=','sale')])
                        Transportation_Tax.amount =0
                        Transportation_Tax.amount = each_inv.sale_id.transportation_aut
                        custom_tax_ids += Transportation_Tax
                        for sale_line in each_inv.sale_id.order_line:
                            sale_line.tax_id +=Transportation_Tax
                    if each_inv.sale_id.airport_additional:
                        print('fcgfcg')
                        Airport_Tax = self.env['account.tax'].search([('name', '=', 'Airport Additional'),('type_tax_use','=','sale')])
                        Airport_Tax.amount = 0
                        Airport_Tax.amount = each_inv.sale_id.airport_additional
                        custom_tax_ids += Airport_Tax
                        for sale_line in each_inv.sale_id.order_line:
                            sale_line.tax_id += Airport_Tax
                    if each_inv.sale_id:
                        for sale_line in each_inv.sale_id.order_line:
                            print('fcgfcg')
                            # Vat_Custom = self.env['account.tax'].search([('name', '=', 'Vat Value')])
                            Vat_Custom = self.env['account.tax'].search([('name', '=', 'VAT 15%'),('type_tax_use','=','sale')])
                            cal_amount = sale_line.price_unit+each_inv.sale_id.airport_additional+each_inv.sale_id.transportation_aut
                            cal_total =0
                            if each_inv.sale_id.percentage:
                                caliculate = cal_amount * each_inv.sale_id.percentage / 100
                                revenue_tax = self.env['account.tax'].search([('name', '=', 'Tax&System Revenue'),('type_tax_use','=','sale')])
                                revenue_tax.amount = 0
                                revenue_tax.amount = caliculate
                                custom_tax_ids += revenue_tax
                                cal_total = cal_amount + caliculate
                                for sale_line in each_inv.sale_id.order_line:
                                    sale_line.tax_id += revenue_tax
                            Coupon_Tax = self.env['account.tax'].search([('name', '=', 'Coupon'),('type_tax_use','=','sale')])
                            if each_inv.sale_id.coupon_value:
                                Coupon_Tax.amount = 0
                                # Coupon_Tax.amount = -each_inv.sale_id.coupon_value
                                Coupon_Tax.amount = each_inv.sale_id.coupon_value
                                custom_tax_ids += Coupon_Tax
                                cal_total = cal_total+Coupon_Tax.amount
                                for sale_line in each_inv.sale_id.order_line:
                                    sale_line.tax_id += Coupon_Tax
                            else:
                                Coupon_Tax.amount =0
                                cal_total = cal_total + Coupon_Tax.amount
                            if each_inv.sale_id.vat_percentage:
                                caliculates = cal_total * each_inv.sale_id.vat_percentage / 100
                                Vat_Custom.amount = 0
                                Vat_Custom.amount = caliculates
                                custom_tax_ids += Vat_Custom
                                each_inv.sale_id.add_tax_amount = caliculates
                                for sale_line in each_inv.sale_id.order_line:
                                    sale_line.tax_id += Vat_Custom

                                # tax_ids = self.env['account.tax'].search(
                                #     [('name', '=', 'VAT 15%'), ('type_tax_use', '=', 'sale')])
                                custom_tax_ids += Vat_Custom

                    # if each_inv.sale_id.state == 'sale':
                    if each_inv.sale_id.state == 'draft':
                        # for sale_line in each_inv.sale_id.order_line:
                        #     sale_line.tax_id +=custom_tax_ids
                        if each_inv.modified_amount:
                            sale = each_inv.sale_id
                            self.driver_modification(sale,each_inv.modified_amount)
                        each_inv.sale_id.action_confirm()
                        driv = each_inv.sale_id.driver_revenue + each_inv.sale_id.vat_Value

                        # invoice = each_inv.sale_id._create_invoices()
                        # invoice.add_tax_amount = each_inv.sale_id.add_tax_amount
                        list_m = []
                        fl = False
                        for l in each_inv.sale_id.order_line:
                            print(each_inv.sale_id,'each_inv.sale_id')
                            account_id = self.env['account.account'].search([('name', '=', 'Product Sales')])
                            awb_cargo = (0, 0, {
                                'name': l.product_id.name,
                                'account_id': account_id.id,
                                'price_unit': l.price_unit,
                                'quantity': 1,
                                'discount': 0,
                                'tax_ids': [(6, 0, l.tax_id.ids)],
                                'sale_line_ids': l,
                                'product_id': l.product_id.id,
                            })
                            list_m.append(awb_cargo)
                        invoice = self.env['account.move'].create({
                            'move_type': 'out_invoice',
                            'partner_id': each_inv.sale_id.partner_id[0].id,
                            'state': 'draft',
                            'add_tax_amount': each_inv.sale_id.add_tax_amount,
                            'add_coupan_amount': each_inv.sale_id.coupon_value,
                            'journal_id': self.env['account.journal'].search([('name', '=', 'Customer Invoices')]).id,
                            'currency_id': each_inv.sale_id.company_id.currency_id.id,
                            'company_id': each_inv.sale_id.company_id.id,
                            'invoice_line_ids': list_m,
                            'invoice_date': datetime.today().date(),
                            # 'l10n_in_gst_treatment': each_inv.sale_id.partner_id.l10n_in_gst_treatment

                        })
                        print(invoice,'invoiceinvoiceinvoice')
                        print(each_inv.sale_id,'each_inv.sale_ideach_inv.sale_id')
                        # new_inv.action_post()

                        # for inv_line in invoice.invoice_line_ids:
                        #     my_tax = self.env['account.tax']
                        #     if inv_line.tax_ids:
                        #         my_tax +=inv_line.tax_ids[0]
                        #         inv_line.tax_ids -=inv_line.tax_ids[0]
                        #     inv_line.tax_ids+=my_tax
                        if invoice.amount_total >0:
                           invoice.sudo().action_post()
                        purchase_taxes = self.env['account.tax']
                        driver_id = self.env['res.partner'].search([('reh_driver_id','=',each_inv.sale_id.reh_driver_id)])[0]

                        # Transportation_Tax_purchase = self.env['account.tax'].search([('name', '=', 'Transportation Authority'),('type_tax_use','=','purchase')])
                        # Transportation_Tax_purchase.amount = each_inv.sale_id.govt_char
                        # purchase_taxes+=Transportation_Tax_purchase
                        #
                        # Airport_Tax_purchase = self.env['account.tax'].search([('name', '=', 'Airport Additional'),('type_tax_use','=','purchase')])
                        # Airport_Tax_purchase.amount = each_inv.sale_id.additional_airport
                        # purchase_taxes +=Airport_Tax_purchase
                        #
                        # revenue_tax_purchase = self.env['account.tax'].search(
                        #     [('name', '=', 'Tax&System Revenue'), ('type_tax_use', '=', 'purchase')])
                        # revenue_tax_purchase.amount = each_inv.sale_id.tax_value_system
                        # purchase_taxes +=revenue_tax_purchase
                        if not driver_id:
                            driver_id = self.env['res.partner'].sudo().create({
                                'name': each_inv.sale_id.reh_driver_id,
                                'reh_driver_id': str(each_inv.sale_id.reh_driver_id),
                                'type_of_customer': 'b_c',
                                'schema_id': 'IQA',
                                'schema_id_no': 'xxxx'
                            })

                        Vat_Custom = self.env['account.tax'].search(
                            [('name', '=', 'VAT 15%'), ('type_tax_use', '=', 'purchase')])
                        # Vat_Custom.amount = each_inv.sale_id.vat_Value
                        purchase_taxes +=Vat_Custom


                        # Coupon_Tax = self.env['account.tax'].search(
                        #     [('name', '=', 'Coupon'), ('type_tax_use', '=', 'purchase')])
                        # Coupon_Tax.amount = each_inv.sale_id.coupon_value
                        # purchase_taxes +=Coupon_Tax


                        po = self.env['purchase.order'].sudo().create({
                            'partner_id': driver_id.id,
                            'trip_id': each_inv.sale_id.trip_id,
                            'transportation_aut': -each_inv.sale_id.govt_char,
                            'airport_additional': -each_inv.sale_id.additional_airport,
                            'taxvalue_system': -each_inv.sale_id.tax_value_system,
                            'value_added': -each_inv.sale_id.vat_Value,
                            'application_fee': -each_inv.sale_id.tax_value_system,
                            'coupon_value': each_inv.sale_id.coupon_value,
                            'mobile': driver_id.mobile,
                            'order_line': [(0, 0, {
                                'name': self.env['product.product'].sudo().search(
                                    [('name', '=', 'Driver Expense')]).name,
                                'product_id': self.env['product.product'].sudo().search(
                                    [('name', '=', 'Driver Expense')]).id,
                                'product_qty': 1,
                                'product_uom': self.env['uom.uom'].sudo().search(
                                    [('name', '=', 'Units')]).id,
                                'price_unit': each_inv.sale_id.driver_revenue,
                                'basic_value': 0,
                                'trip_cost': each_inv.sale_id.driver_revenue,
                                # 'date_planned': time.strftime('%Y-%m-%d'),
                                'taxes_id':purchase_taxes,
                                'date_planned': datetime.now().date().strftime(DEFAULT_SERVER_DATE_FORMAT),
                            })],
                        })
                        po.sudo().button_confirm()

                    po_ref = self.env['purchase.order'].search([('trip_id','=',each_inv.sale_id.trip_id)])
                    mm=self.env['profit.car.orders'].sudo().create({
                        'date': datetime.today().date(),
                        'passenger_id': each_inv.sale_id.partner_id[0].passenger_id,
                        'trip_id': each_inv.sale_id.trip_id,
                        'rehla_id': each_inv.sale_id.rehla_id,
                        'reh_driver_id': po_ref.partner_id[0].reh_driver_id,
                        'driver_cost': each_inv.sale_id.driver_revenue,
                        'trip_cost': each_inv.sale_id.amount_total,
                        'tax_amount': each_inv.sale_id.vat_Value,
                        'profit': each_inv.sale_id.amount_total - driv,
                        'passenger': each_inv.sale_id.partner_id[0].id,
                        'driver': po_ref.partner_id[0].id,
                        'revenue_profit':each_inv.sale_id.tax_value_system
                    })
                    print(mm,'mm')
                    percentage = 0
                    wallet_amount = 0
                    if each_inv.sale_id.payment_type == True:
                        percentage = each_inv.sale_id.amount_total * 22 / 100
                        wallet_amount = each_inv.sale_id.amount_total - percentage
                    if each_inv.sale_id.payment_type == False:
                        wallet_amount = each_inv.sale_id.amount_total

                    vv = self.env['wallet.amount'].sudo().create({
                        'date': datetime.today().date(),
                        'passenger_id': str(each_inv.sale_id.partner_id[0].id),
                        'trip_id': each_inv.sale_id.trip_id,
                        'rehla_id': each_inv.sale_id.rehla_id,
                        'reh_driver_id': po_ref.partner_id[0].reh_driver_id,
                        'driver_cost': each_inv.sale_id.driver_revenue,
                        'trip_cost': each_inv.sale_id.amount_total,
                        'driver_id': po_ref.partner_id[0].id,
                        'passenger': each_inv.sale_id.partner_id[0].id,
                        'payment_type': each_inv.sale_id.payment_type,
                        'wallet_amount': wallet_amount
                    })
                    print(vv,'vv')

        self.write({'state': 'close'})

    def driver_modification(self,sale,each_inv):
        if sale:
            print('driver_modification',sale)
            for line in sale.order_line:
                line.price_unit = each_inv
                line.tax_id = False
                custom_tax_ids = self.env['account.tax']
                if sale.transportation_aut:
                    Transportation_Tax = self.env['account.tax'].search(
                        [('name', '=', 'Transportation Authority'), ('type_tax_use', '=', 'sale')])
                    Transportation_Tax.amount = 0
                    Transportation_Tax.amount = sale.transportation_aut
                    custom_tax_ids += Transportation_Tax
                    for sale_line in sale.order_line:
                        sale_line.tax_id += Transportation_Tax
                if sale.airport_additional:
                    Airport_Tax = self.env['account.tax'].search(
                        [('name', '=', 'Airport Additional'), ('type_tax_use', '=', 'sale')])
                    Airport_Tax.amount = 0
                    Airport_Tax.amount = sale.airport_additional
                    custom_tax_ids += Airport_Tax
                    for sale_line in sale.order_line:
                        sale_line.tax_id += Airport_Tax
                if sale:
                    for sale_line in sale.order_line:
                        # Vat_Custom = self.env['account.tax'].search([('name', '=', 'Vat Value')])
                        Vat_Custom = self.env['account.tax'].search(
                            [('name', '=', 'VAT 15%'), ('type_tax_use', '=', 'sale')])
                        cal_amount = each_inv + sale.airport_additional + sale.transportation_aut
                        cal_total = 0
                        if sale.percentage:
                            caliculate = cal_amount * sale.percentage / 100
                            revenue_tax = self.env['account.tax'].search(
                                [('name', '=', 'Tax&System Revenue'), ('type_tax_use', '=', 'sale')])
                            revenue_tax.amount = 0
                            revenue_tax.amount = caliculate
                            custom_tax_ids += revenue_tax
                            cal_total = cal_amount + caliculate
                            for sale_line in sale.order_line:
                                sale_line.tax_id += revenue_tax
                        Coupon_Tax = self.env['account.tax'].search(
                            [('name', '=', 'Coupon'), ('type_tax_use', '=', 'sale')])
                        if sale.coupon_value:
                            Coupon_Tax.amount = 0
                            # Coupon_Tax.amount = -sale.coupon_value
                            Coupon_Tax.amount = sale.coupon_value
                            custom_tax_ids += Coupon_Tax
                            cal_total = cal_total + Coupon_Tax.amount
                            for sale_line in sale.order_line:
                                sale_line.tax_id += Coupon_Tax
                        else:
                            Coupon_Tax.amount = 0
                            cal_total = cal_total - Coupon_Tax.amount
                        if sale.vat_percentage:
                            caliculates = cal_total * sale.vat_percentage / 100
                            Vat_Custom.amount = 0
                            Vat_Custom.amount = caliculates
                            custom_tax_ids += Vat_Custom
                            sale.add_tax_amount = caliculates
                            for sale_line in sale.order_line:
                                sale_line.tax_id += Vat_Custom
class AutomaticRehlaRecLines(models.Model):
    _name = 'automatic.rehla.reclines'

    rec_lines = fields.Many2one('automatic.rehla.record')
    invoice_id = fields.Many2one('account.move', string="Invoice")
    sale_id = fields.Many2one('sale.order', string="Sales Order")
    trip_id = fields.Char(string="Trip Id")
    rehla_id = fields.Char(string="Rehla Id")
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('confirm', 'confirm'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, tracking=True,
        default='draft')
    partner_id = fields.Many2one('res.partner', string="Customer")
    amount = fields.Float(string="Sale Amount")
    final_amount = fields.Float(string="Final Amount")
    modified_amount = fields.Float(string="Modified Amount")


class AccountMove(models.Model):
    _inherit = 'account.move'

    rehla_id = fields.Char('Rehla Id')
    trip_id = fields.Char('Trip Id')
    passenger_id = fields.Char('Passenger Id')
    reh_driver_id = fields.Char('Driver Id')
    rehla_uniq_id = fields.Char(string='Rehla Unique Id')
    entry_rehla_type = fields.Selection([
        ('none', 'None'),
        ('transport_entry', 'Transportation Entry'),
        ('airport', 'Airport Fee'),
        ('coupons', 'Coupons'),
    ], string='Car Category', readonly=True, copy=False, index=True, track_visibility='onchange',
        track_sequence=3, default='none'
    )
    add_tax_amount = fields.Float(string="add Tax Amount")
    add_coupan_amount = fields.Float(string="add coupan Amount")

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id')
    def _compute_amount(self):
        for move in self:
            print('gdfgdf')

            if move.payment_state == 'invoicing_legacy':
                # invoicing_legacy state is set via SQL when setting setting field
                # invoicing_switch_threshold (defined in account_accountant).
                # The only way of going out of this state is through this setting,
                # so we don't recompute it here.
                move.payment_state = move.payment_state
                continue

            total_untaxed = 0.0
            total_untaxed_currency = 0.0
            total_tax = 0.0
            total_tax_currency = 0.0
            total_to_pay = 0.0
            total_residual = 0.0
            total_residual_currency = 0.0
            total = 0.0
            total_currency = 0.0
            currencies = move._get_lines_onchange_currency().currency_id

            for line in move.line_ids:
                if move.is_invoice(include_receipts=True):
                    # === Invoices ===

                    if not line.exclude_from_invoice_tab:
                        # Untaxed amount.
                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.tax_line_id:
                        # Tax amount.
                        total_tax += line.balance
                        total_tax_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.account_id.user_type_id.type in ('receivable', 'payable'):
                        # Residual amount.
                        total_to_pay += line.balance
                        total_residual += line.amount_residual
                        total_residual_currency += line.amount_residual_currency
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency

            if move.move_type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1
            move.amount_untaxed = sign * (total_untaxed_currency if len(currencies) == 1 else total_untaxed)
            move.amount_tax = sign * (total_tax_currency if len(currencies) == 1 else total_tax)
            move.amount_total = sign * (total_currency if len(currencies) == 1 else total)
            # move.amount_total = move.amount_total+move.add_coupan_amount
            # move.amount_total
            move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)
            # move.amount_residual = move.amount_residual+move.add_coupan_amount
            move.amount_residual = move.amount_residual
            move.amount_untaxed_signed = -total_untaxed
            move.amount_tax_signed = -total_tax
            move.amount_total_signed = abs(total) if move.move_type == 'entry' else -total
            move.amount_residual_signed = total_residual

            currency = len(currencies) == 1 and currencies or move.company_id.currency_id

            # Compute 'payment_state'.
            new_pmt_state = 'not_paid' if move.move_type != 'entry' else False

            if move.is_invoice(include_receipts=True) and move.state == 'posted':

                if currency.is_zero(move.amount_residual):
                    reconciled_payments = move._get_reconciled_payments()
                    if not reconciled_payments or all(payment.is_matched for payment in reconciled_payments):
                        new_pmt_state = 'paid'
                    else:
                        new_pmt_state = move._get_invoice_in_payment_state()
                elif currency.compare_amounts(total_to_pay, total_residual) != 0:
                    new_pmt_state = 'partial'

            if new_pmt_state == 'paid' and move.move_type in ('in_invoice', 'out_invoice', 'entry'):
                reverse_type = move.move_type == 'in_invoice' and 'in_refund' or move.move_type == 'out_invoice' and 'out_refund' or 'entry'
                reverse_moves = self.env['account.move'].search(
                    [('reversed_entry_id', '=', move.id), ('state', '=', 'posted'), ('move_type', '=', reverse_type)])

                # We only set 'reversed' state in cas of 1 to 1 full reconciliation with a reverse entry; otherwise, we use the regular 'paid' state
                reverse_moves_full_recs = reverse_moves.mapped('line_ids.full_reconcile_id')
                if reverse_moves_full_recs.mapped('reconciled_line_ids.move_id').filtered(lambda x: x not in (
                        reverse_moves + reverse_moves_full_recs.mapped('exchange_move_id'))) == move:
                    new_pmt_state = 'reversed'

            move.payment_state = new_pmt_state

class AccountOrderLine(models.Model):
    _inherit = 'account.move.line'
    # @api.model
    # def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes, move_type):
    #     ''' This method is used to compute 'price_total' & 'price_subtotal'.
    #
    #     :param price_unit:  The current price unit.
    #     :param quantity:    The current quantity.
    #     :param discount:    The current discount.
    #     :param currency:    The line's currency.
    #     :param product:     The line's product.
    #     :param partner:     The line's partner.
    #     :param taxes:       The applied taxes.
    #     :param move_type:   The type of the move.
    #     :return:            A dictionary containing 'price_subtotal' & 'price_total'.
    #     '''
    #     res = {}
    #
    #     # Compute 'price_subtotal'.
    #     line_discount_price_unit = price_unit * (1 - (discount / 100.0))
    #     subtotal = quantity * line_discount_price_unit
    #
    #     # Compute 'price_total'.
    #     if taxes:
    #         force_sign = -1 if move_type in ('out_invoice', 'in_refund', 'out_receipt') else 1
    #         taxes_res = taxes._origin.with_context(force_sign=force_sign).compute_all(line_discount_price_unit,
    #             quantity=quantity, currency=currency, product=product, partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
    #         if move_type == 'out_invoice':
    #             if self.sale_line_ids:
    #                 res['price_subtotal'] = taxes_res['total_excluded']-self.sale_line_ids.order_id.add_tax_amount
    #                 res['price_total'] = taxes_res['total_included']-self.sale_line_ids.order_id.add_tax_amount
    #             else:
    #                 res['price_subtotal'] = taxes_res['total_excluded'] - self.move_id.add_tax_amount
    #                 res['price_total'] = taxes_res['total_included'] - self.move_id.add_tax_amount
    #         elif move_type == 'in_invoice':
    #             if self.sale_line_ids:
    #                 res['price_subtotal'] = taxes_res['total_excluded'] + self.sale_line_ids.order_id.add_tax_amount
    #                 res['price_total'] = taxes_res['total_included'] + self.sale_line_ids.order_id.add_tax_amount
    #             else:
    #                 res['price_subtotal'] = taxes_res['total_excluded'] + self.move_id.add_tax_amount
    #                 res['price_total'] = taxes_res['total_included'] + self.move_id.add_tax_amount
    #
    #         else:
    #             res['price_subtotal'] = taxes_res['total_excluded']
    #             res['price_total'] = taxes_res['total_included']
    #
    #     else:
    #         res['price_total'] = res['price_subtotal'] = subtotal
    #     #In case of multi currency, round before it's use for computing debit credit
    #     if currency:
    #         res = {k: currency.round(v) for k, v in res.items()}
    #     return res
    #




class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        if 'passenger_id' in vals and 'name' in vals:
            if not self.env['res.partner'].search([('passenger_id','=',vals['passenger_id'])]):
                res = super(ResPartner, self).create(vals)
                return res
            else:
                passenger = self.env['res.partner'].search(
                    [('passenger_id', '=', vals['passenger_id'])])
                for all in passenger:
                    all.name =str(vals['name'])
                return passenger
        elif 'reh_driver_id' in vals and 'name' in vals:
                    if not self.env['res.partner'].search([('reh_driver_id', '=', vals['reh_driver_id'])]):
                        res = super(ResPartner, self).create(vals)
                        return res
                    else:
                        passenger = self.env['res.partner'].search(
                            [('reh_driver_id', '=', vals['reh_driver_id'])])
                        for all in passenger:
                            print(all.name,'before')
                            all.name = str(vals['name'])
                            print(all.name,'after')
                        return passenger
        else:
            return super(ResPartner, self).create(vals)



class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    #
    # def create_invoices(self):
    #     sale_obj = self.env['sale.order']
    #     rec = super(SaleAdvancePaymentInv, self).create_invoices()
    #     order = sale_obj.browse(self._context.get('active_ids'))[0]
    #     print(order)
    #     for each_inv in order.invoice_ids:
    #         each_inv.add_tax_amount = order.add_tax_amount