# -*- coding: utf-8 -*-
{
    'name': "Warranty",
    'summary': """Warranty tracking of sold product""",

    'author': "Smarten Technologies",
    'website': "https://www.smarten.com.np",
    'category': '',
    'sequence': '-105',
    'version': '18.1',
    'license': 'LGPL-3',

    'depends': [
        'base','stock','product','sale','account','repair',
    ],

    'data': [
        "security/ir.model.access.csv",
        "views/product_inherit.xml",
        # "views/sale_order_product_warranty_create.xml",
        "views/warranty_menuitem.xml",
        "views/account_warranty.xml",
        "wizards/account_move_wizard.xml",
    ],
    'application': True,
    'installable': True,
}