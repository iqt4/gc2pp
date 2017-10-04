#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  pc.py
#
#  Copyright 2016 Dirk Silkenbäumer <dirk@silkenbaeumer.eu>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
from __future__ import print_function

import datetime as dt
import sys
# import locale
import csv
import re
import json
import difflib
import piecash
from piecash._common import CallableList


def load_ini():
    if len(sys.argv) > 1:
        ini = sys.argv[1]
    else:
        ini = 'pc.json'

    with open(ini, 'r') as f:
        return json.load(f)
  
        
def set_para(ini, book):
        #find all stocks, except currencies and template
        stocklist = CallableList([c for c in book.commodities
                            if c.namespace not in ['CURRENCY', 'template']])
        
        due_date = dt.datetime.strptime(ini['due_date'], '%Y-%m-%d')
        
        para = {'gnc_file': ini['gnc_file'],
                'due_date': due_date,
                'gnc_stocklist': stocklist}
        
        for k, v in ini['accounts'].items():
            if isinstance(v, list):
                para[k]=[book.accounts(fullname=i) for i in v]
            else:
                para[k]=book.accounts(fullname=v)
        
        return(para)


def save_ini(para):
    def to_json(python_object):
        if isinstance(python_object, dt.datetime):
#            return {'__class__': 'datetime',
#                '__value__': python_object.date().isoformat()}
            return python_object.date().isoformat()
        elif isinstance(python_object, piecash.core.account.Account):
            return python_object.fullname.encode('utf-8')
        raise TypeError(repr(python_object) + ' is not JSON serializable')

    para_exp = {k:v for k,v in para.items()
        if k in ['gnc_file', 'due_date']}
    
    accounts = {p:para[p] for p in para
        if p in ['gnc_portfolio', 'gnc_dividend', 'gnc_account',
                 'gnc_charge', 'gnc_tax', 'gnc_dividend', 'gnc_day2day']}

    para_exp['accounts'] = accounts
    
    with open('pc.json', 'w') as f:
        json.dump(para_exp, f, ensure_ascii=False, indent=4, default=to_json)


def getDate(due_date):
    while True:
        info = 'Datum [{0}]: '.format(due_date.strftime('%d.%m.%Y'))
        user_input = input(info)
        try:
            if user_input == '':
                d = due_date
            else:
                d = dt.datetime.strptime(user_input, '%d.%m.%Y')
            return d
        except ValueError:
            print('Falsches Datum')


def get_transactions(splits, due_date):
    transactions = [sp.transaction for sp in splits
        if sp.transaction.post_date.replace(tzinfo=None) >= due_date]

    return(sorted(list(set(transactions)), key=lambda tr: tr.post_date))


def write_stocklist(stocklist):
    header = ['ISIN', 'WKN', 'Ticker-Symbol', 'Wertpapiername', 'Währung', 'Notiz']

    with open('stock.csv', 'wb') as f:
        f_csv = csv.DictWriter(f, header, delimiter=';', quoting=csv.QUOTE_NONE)
        f_csv.writeheader()

        for stock in stocklist:
            row = {'ISIN':stock.cusip,
                   'Ticker-Symbol':stock.mnemonic,
                   'Wertpapiername':stock.fullname,
                   'Währung':'EUR',
                   'Notiz':stock.namespace}

            f_csv.writerow(row)


def write_portfolio(para):
    header = ['Datum', 'Typ', 'Wert', 'Buchungswährung',
              'Bruttobetrag','Währung Bruttobetrag', 'Wechselkurs',
              'Gebühren', 'Steuern', 'Stück',
              'ISIN', 'WKN', 'Ticker-Symbol', 'Wertpapiername',
              'Notiz']

    acc = ['gnc_charge', 'gnc_tax', 'gnc_account']

    with open('portfolio.csv', 'w') as f:
        f_csv = csv.DictWriter(f, header, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        f_csv.writeheader()
        
        for stockacc in para['gnc_portfolio'].children:
            transactions = get_transactions(stockacc.splits,
                                            para['due_date'])
            if not transactions:
                continue

            for tr in transactions:
                val = dict.fromkeys(acc, 0)
                stock_quantity = 0
                stock_value = 0
    
                for sp in tr.splits:
                    if sp.account == stockacc:
                        stock_quantity += sp.quantity
                        stock_value += sp.value
                    else:
                        for a in acc:
                            if sp.account in para[a]:
                                val[a] += sp.value

                if stock_quantity.is_zero():
                    continue
    
                if val['gnc_account'] != 0 or stock_value == 0: # Abrechnungskonto oder Incentiv
                    if stock_quantity.is_signed():
                        deal = 'Verkauf'
                    else:
                        deal = 'Kauf'
                    total = abs(val['gnc_account'])
                else:
                    if stock_quantity.is_signed():
                        deal = 'Auslieferung'
                    else:
                        deal = 'Einlieferung'
                    total = stock_value
    
                stock = stockacc.commodity
    
                row = {'Datum':tr.post_date.strftime('%Y-%m-%d'),
                       'Typ':deal,
                       'Wert':str(total),
                       'Buchungswährung':'EUR',
                       'Gebühren':str(val['gnc_charge']),
                       'Steuern':str(val['gnc_tax']),
                       'Stück':str(abs(stock_quantity)),
                       'ISIN':stock.cusip,
                       'Ticker-Symbol':stock.mnemonic,
                       'Wertpapiername':stock.fullname,
                       'Notiz':tr.description}
    
                f_csv.writerow(row)


def write_transfer(f_csv, transaction, para):
    v_day2day = 0
    for sp in transaction.splits:
        if sp.account in para['gnc_day2day']:
            v_day2day += sp.value

    row = {'Datum':transaction.post_date.strftime('%Y-%m-%d'),
       'Buchungswährung':'EUR',
       'Notiz':transaction.description}

    if v_day2day != 0:
        if v_day2day > 0:
            row['Typ'] = 'Umbuchung (Ausgang)'
        else:
            row['Typ'] = 'Umbuchung (Eingang)'
        row['Wert'] = str(-v_day2day)
        f_csv.writerow(row)


def write_split(f_csv, transaction, para):
    acc = ['gnc_charge', 'gnc_tax', 'gnc_interest',
           'gnc_account', 'gnc_day2day']
    val = dict.fromkeys(acc, 0)
    
    for sp in transaction.splits:
        for a in acc:
            if sp.account in para[a]:
                val[a] += sp.value

    delta = sum(val.values())

    row = {'Datum':transaction.post_date.strftime('%Y-%m-%d'),
       'Buchungswährung':'EUR',
       'Notiz':transaction.description}

    if val['gnc_charge'] != 0:
        if val['gnc_charge'] > 0:
            row['Typ'] = 'Gebühren'
        else:
            row['Typ'] = 'Gebührenerstattung'  # to be checked
        row['Wert'] = str(abs(val['gnc_charge']))
        f_csv.writerow(row)

    if val['gnc_tax'] != 0:
        if val['gnc_tax'] > 0:
            row['Typ'] = 'Steuern'
        else:
            row['Typ'] = 'Steuerrückerstattung'
        row['Wert'] = str(abs(val['gnc_tax']))
        f_csv.writerow(row)
        
    if val['gnc_interest'] < 0:
        row['Typ'] = 'Zinsen'
        row['Wert'] = str(-val['gnc_interest'])
        f_csv.writerow(row)

    #~ if val['gnc_day2day'] <> 0:
        #~ if val['gnc_day2day'] > 0:
            #~ row['Typ'] = u'Umbuchung (Ausgang)'
        #~ else:
            #~ row['Typ'] = u'Umbuchung (Eingang)'
        #~ row['Wert'] = locale.str(-val['gnc_day2day'])
        #~ f_csv.writerow(row)

    if delta != 0:
        if delta > 0:
            row['Typ'] = 'Einlage'
        else:
            row['Typ'] = 'Entnahme'
        row['Wert'] = str(abs(delta))
        f_csv.writerow(row)


def write_dividend(f_csv, transaction, para):
    junk = ['INHABER', 'NAMENS', 'VORZUGS', 'STAMM', 'AKTIEN',
            'SHARES', 'REGISTERED']

    stocknames = [s.fullname for s in para['gnc_stocklist']]
    stock = None

    #find stock by ISIN (MLP)
    r = re.search(r'WKN [A-Z0-9]{6} / '
                  r'(?P<isin>[A-Z]{2}[A-Z0-9]{9}[0-9])'
                  r'.*?MENGE '
                  r'(?P<quantity>[0-9]*)', transaction.description)

    if r:
        stock = para['gnc_stocklist'](cusip=r.group('isin'))
        quantity = r.group('quantity')
    else:
        #find stock by name (maxblue)
        r = re.search(r'STK/NOM: '
                      r'(?P<quantity>[0-9]*) '
                      r'(?P<name>.*)', transaction.description)
        if r:
            quantity, name = r.groups()
            for j in junk:
                name = name.replace(j, '')

            for s in difflib.get_close_matches(name, stocknames, 1):
                stock = para['gnc_stocklist'](fullname=s)

    if stock:
        tax = 0
        dividend = 0
        for sp in transaction.splits:
            if sp.account == para['gnc_dividend']:
                dividend = abs(sp.value)

            elif sp.account in para['gnc_tax']:
                tax += sp.value

        row = {
            'Datum':transaction.post_date.strftime('%Y-%m-%d'),
            'Typ':'Dividende',
            'Wert':str(dividend-tax),
            'Buchungswährung':'EUR',
            'Stück':quantity,
            'ISIN':stock.cusip,
            'Ticker-Symbol':stock.mnemonic,
            'Wertpapiername':stock.fullname,
            'Notiz':transaction.description
            }
        if tax:
            row['Steuern'] = str(tax)

        f_csv.writerow(row)


def write_day2day(para):
    t_day2day = []
    for acc in para['gnc_day2day']:
        t_day2day += get_transactions(acc.splits, para['due_date'])
    
    t_account = []
    for acc in para['gnc_account']:
        t_account += get_transactions(acc.splits, para['due_date'])

    
    header = ['Datum', 'Typ', 'Wert', 'Buchungswährung', 'Steuern',
              'Stück', 'ISIN', 'WKN', 'Ticker-Symbol', 'Wertpapiername',
              'Notiz']

    with open('day2day.csv', 'w') as f:
        f_csv = csv.DictWriter(f, header, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        f_csv.writeheader()
        
        if not t_day2day:
            return

        for tr in t_day2day:
            if tr not in t_account: #Umbuchung already done
                write_split(f_csv, tr, para)


def write_account(para):
    t_dividend = get_transactions(para['gnc_dividend'].splits,
                                  para['due_date'])
                               
    t_stock = []
    for acc in para['gnc_portfolio'].children:
        t_stock += get_transactions(acc.splits, para['due_date'])
 
    t_account = []
    for acc in para['gnc_account']:
        t_account += get_transactions(acc.splits, para['due_date'])
    
    header = ['Datum', 'Typ', 'Wert', 'Buchungswährung', 'Steuern',
              'Stück', 'ISIN', 'WKN', 'Ticker-Symbol', 'Wertpapiername',
              'Notiz']

    with open('account.csv', 'w') as f:
        f_csv = csv.DictWriter(f, header, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        f_csv.writeheader()
        
        if not t_account:
            return

        for tr in t_account:
            if tr in t_stock:
                continue
            elif tr in t_dividend:
                write_dividend(f_csv, tr, para)
            else:
                write_transfer(f_csv, tr, para)
                write_split(f_csv, tr, para)
                

#def write_dividend(para):
        #transactions = get_transactions(para['gnc_dividend'].splits,
                                        #para['due_date'])

        #stocknames = [s.fullname for s in para['gnc_stocklist']]

        #junk = ['INHABER', 'NAMENS', 'VORZUGS', 'STAMM', 'AKTIEN',
                #'SHARES', 'REGISTERED']

        #header = ['Datum', 'Typ', 'Wert', 'Buchungswährung', 'Steuern',
                  #'Stück', 'ISIN', 'WKN', 'Ticker-Symbol', 'Wertpapiername',
                  #'Notiz']

        #with open('dividend.csv', 'wb') as f:
            #f_csv = csv.DictWriter(f, header, delimiter=';', quoting=csv.QUOTE_MINIMAL)
            #f_csv.writeheader()

            #if not transactions:
                #return

            #for tr in transactions:

                ##find stock by ISIN (MLP)
                #r = re.search(r'WKN [A-Z0-9]{6} / '
                              #r'(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d{1})'
                              #r'.*?MENGE '
                              #r'(?P<quantity>\d*)', tr.description)

                #if r:
                    #stock = para['gnc_stocklist'](cusip=r.group('isin'))
                    #quantity = r.group('quantity')
                #else:
                    ##find stock by name (maxblue)
                    #r = re.search(r'STK/NOM: '
                                  #r'(?P<quantity>\d*)'
                                  #r' '
                                  #r'(?P<name>.*)', tr.description)
                    #if r:
                        #quantity, name = r.groups()
                        #for j in junk:
                            #name = name.replace(j, '')
                        #m=difflib.get_close_matches(name, stocknames, 1)[0]
                        #stock = para['gnc_stocklist'](fullname=m)
                    #else:
                        #stock = None

                #if stock:
                    #tax = 0
                    #dividend = 0
                    #for sp in tr.splits:
                        #if sp.account == para['gnc_dividend']:
                            #dividend = abs(sp.value)

                        #elif sp.account in para['gnc_tax']:
                            #tax += sp.value

                    #row = {
                        #'Datum':tr.post_date.strftime('%Y-%m-%d'),
                        #'Typ':'Dividende',
                        #'Wert':locale.str(dividend-tax),
                        #'Buchungswährung':'EUR',
                        #'Stück':quantity,
                        #'ISIN':stock.cusip,
                        #'Ticker-Symbol':stock.mnemonic,
                        #'Wertpapiername':stock.fullname.encode('utf-8'),
                        #'Notiz':tr.description.encode('utf-8')
                        #}
                    #if tax:
                        #row['Steuern'] = locale.str(tax)

                    #f_csv.writerow(row)


def main():
    ini = load_ini()

    with piecash.open_book(ini['gnc_file'], open_if_lock=True) as book:
        para = set_para(ini, book)

        para['due_date'] = getDate(para['due_date'])

#        locale.setlocale(locale.LC_NUMERIC, 'de_DE.UTF-8')

        write_account(para)
        write_day2day(para)
        write_portfolio(para)

#        write_dividend(para)
#        write_stocklist(stocklist)
        
        exit()
    
        para['due_date'] = dt.datetime.now()
    
        save_ini(para)
    return 0


if __name__ == '__main__':
    main()

