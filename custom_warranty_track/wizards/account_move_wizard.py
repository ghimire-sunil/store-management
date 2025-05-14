from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMoveWizard(models.TransientModel):
    _name = "account.move.warranty.wizard"


    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    invoice_name = fields.Char(string="Invoice Reference", readonly=False)
    end_dates = fields.Date(string="End Date", required=True)
    product_id_sold = fields.Many2one('product.template',string="Product")
    sales_name = fields.Char(string="Sale")
    order_line_id_picking = fields.Integer(string="Delivery Track")
    cust_id = fields.Many2one('res.partner',string="Customer")
    starting_date = fields.Date(string="Start Date")

    def action_create_warranty_for_account(self):
        # fetch sales id 
        sales_id_od_delivery = self.env['sale.order'].search([('name','=',self.sales_name)])

        # invoice date 
        # invoiced_date_of_order = sales_id_od_delivery.invoice_ids.invoice_date

        # fetch lot of delivered product 
        fetch_lot_from_delivery_sale = self.env['stock.move'].search([('product_id','=',self.product_id_sold.id),('sale_line_id','=',self.order_line_id_picking)])

        # fetch product warranty if present
        product_warranty = self.product_id_sold.product_warranty

        for lots_in_order in fetch_lot_from_delivery_sale.lot_ids:
            existing_warranty = self.env['product.warranty.track'].search([('lot_no_product', '=', lots_in_order.id)])
            if product_warranty == True:
                if not existing_warranty:
                    self.env['product.warranty.track'].create({
                                                            'customer_id':self.cust_id.id,
                                                            'product_id':self.product_id_sold.id,
                                                            'sale_id':sales_id_od_delivery.id,
                                                            'start_date':self.starting_date,
                                                            'lot_no_product':lots_in_order.id,
                                                            'end_date':self.end_dates,
                    })
                else:
                    raise UserError(f"Warranty Already Created.")
            else:
                raise UserError(f"Product Have No Warranty.")
            
