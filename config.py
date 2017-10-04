# json style - may be used in config file later
_gnc_accounts = {
    "bank": [
        "Aktiva:Barvermögen:MLP:Abwicklungskonto",
        "Aktiva:Barvermögen:Deutsche Bank:Depotkonto"
    ],
    "money-market": [
        "Aktiva:Barvermögen:MLP:Tagesgeldkonto"
    ],
    "interest": [
        "Erträge:Zinsen:MLP Konten",
        "Erträge:Zinsen:Tagesgeld MLP"
    ],
    "commission": [
        "Aufwendungen:Bankgebühren:MLP:Wertpapierdepot",
        "Aufwendungen:Bankgebühren:MLP:Konten",
        "Aufwendungen:Bankgebühren:Deutsche Bank:Depot DB"
    ],
    "tax": [
        "Aufwendungen:Steuern:Kapitalertragssteuer",
        "Aufwendungen:Steuern:Solidaritätszuschlag",
        "Aufwendungen:Steuern:Quellensteuer"
    ],
    "investment": "Aktiva:Investments:Wertpapierdepot",
    "dividend": "Erträge:Dividende:Wertpapierdepot"
}

ini = {
    "gnc_file": "Haushalt_sq3.gnucash",
    "due_date": "2012-01-01"
}


# piecash accounts
import piecash


def get_accounts(book):
    accounts = dict()

    # find all stock accounts, except currencies and template
    accounts['stocks'] = piecash._common.CallableList([c for c in book.commodities
                        if c.namespace not in ['CURRENCY', 'template']])

    for k, v in _gnc_accounts.items():
        if isinstance(v, list):
            accounts[k] = [book.accounts(fullname=i) for i in v]
        else:
            accounts[k] = book.accounts(fullname=v)

    return (accounts)


# ab hier überarbeiten
#due_date = dt.datetime.strptime(ini['due_date'], '%Y-%m-%d')

# para = {'gnc_file': ini['gnc_file'],
#        'due_date': due_date,
#        'gnc_stocklist': stocks}

import sys

def load_ini():
    if len(sys.argv) > 1:
        ini = sys.argv[1]
    else:
        ini = 'pc.json'

    with open(ini, 'r') as f:
        return json.load(f)


def save_ini(para):
    def to_json(python_object):
        if isinstance(python_object, dt.datetime):
            #            return {'__class__': 'datetime',
            #                '__value__': python_object.date().isoformat()}
            return python_object.date().isoformat()
        elif isinstance(python_object, piecash.core.account.Account):
            return python_object.fullname.encode('utf-8')
        raise TypeError(repr(python_object) + ' is not JSON serializable')

    para_exp = {k: v for k, v in para.items()
                if k in ['gnc_file', 'due_date']}

    accounts = {p: para[p] for p in para
                if p in ['gnc_portfolio', 'gnc_dividend', 'gnc_account',
                         'gnc_charge', 'gnc_tax', 'gnc_dividend', 'gnc_day2day']}

    para_exp['accounts'] = accounts

    with open('pc.json', 'w') as f:
        json.dump(para_exp, f, ensure_ascii=False, indent=4, default=to_json)
