from odoo import fields, models, api, _

class ProductInherit(models.Model):
    _inherit="product.template"


    product_warranty = fields.Boolean(string="Warranty Period")