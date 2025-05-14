from odoo import fields, models, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


# class ProductTemp(models.Model):
#     _inherit = "product.template"

#     warranty_id = fields.Many2one("product.warranty.track")


class ProductWarrantyLine(models.Model):
    _name = "product.warranty.track.line"

    warranty_id = fields.Many2one("product.warranty.track")
    product_id = fields.Many2one("product.template", string="Product")
    lot_no_product = fields.Many2many("stock.lot", string="Product Serial No.")


class WarrantyProductDetails(models.Model):
    _name = "product.warranty.track"

    line_ids = fields.One2many("product.warranty.track.line", "warranty_id")
    customer_id = fields.Many2one("res.partner", string="Customer")
    sale_id = fields.Many2one("sale.order", string="Sale Order")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date", required=True)
    state = fields.Selection([('draft','Under Approval'),('approved','Approved'),('expired','Expired'), ('cancel','Canceled')], default='draft',copy=False,track_visibility='onchange' ,string='State',readonly=True)


    @api.model
    def create(self, values):
        # results = self.env['product.warranty.track'].browse()
        print("results-----------------------", values)
        line_ids = values.pop("line_ids", [])
        print("---------------line_ids", line_ids)
        for line in line_ids:
            print("-------------------line", line)
            if line[0] == 0:
                line_data = line[2]
                product_id = line_data.get("product_id")
                lot_ids = [lot[1] for lot in line_data.get("lot_no_product", [])]
                customer_id = values.get("customer_id")
                sale_id = values.get("sale_id")

                # check if exist
                existing = self.search(
                    [
                        ("customer_id", "=", customer_id),
                        ("sale_id", "=", sale_id),
                        ("line_ids.product_id", "=", product_id),
                        ("line_ids.lot_no_product", "in", lot_ids),
                    ]
                )
                if not existing:
                    single_values = values.copy()
                    print("-------------------single_values", single_values)
                    single_values["line_ids"] = [line]
                    print("-------------------single_values 2", single_values)
                    res = super(WarrantyProductDetails, self).create(single_values)
                else:
                    raise UserError("Warranty Already Created.")
        return res

    def action_confirm(self):
        self.state = 'approved' 
    
    def action_cancel(self):
        self.state = 'cancel'

    def action_set_to_draft(self):
        self.state = 'draft'

    def check_if_expired(self):
        today = fields.Date.today()
        for record in self:
            if record.state == 'cancel':
                continue
            if record.state == 'approved' and record.end_date and record.end_date < today:
                record.state = 'expired'


class SaleOrderWarranty(models.Model):
    _inherit = "sale.order.line"

    def action_line_button(self):
        cusomer_name = self.order_id.partner_id.id
        sold_product = self.product_id.id
        sales_order = self.order_id.id
        waranty_start_date = self.order_id.invoice_ids.invoice_date
        waranty_end_date = waranty_start_date + relativedelta(years=1)

        # fetching lots of the product in sale.order.line from stock.move
        product_lot_of_sale = self.env["stock.move"].search(
            [("product_id", "=", sold_product), ("sale_line_id", "=", self.id)]
        )
        lot_tracks = product_lot_of_sale.lot_ids

        # fetch product warranty if present
        product_warranty = self.product_id.product_warranty

        for lot_one in lot_tracks:
            existing_warranty = self.env["product.warranty.track"].search(
                [("lot_no_product", "=", lot_one.id)]
            )
            if product_warranty:
                if not existing_warranty:
                    self.env["product.warranty.track"].create(
                        {
                            "customer_id": cusomer_name,
                            "product_id": sold_product,
                            "sale_id": sales_order,
                            "start_date": waranty_start_date,
                            "lot_no_product": lot_one.id,
                            "end_date": waranty_end_date,
                        }
                    )
                else:
                    raise UserError("Warranty Already Created.")
            else:
                raise UserError("Product Have No Warranty.")


class AccountInherit(models.Model):
    _inherit = "account.move"

    def action_custom_warranty(self):
        self.ensure_one()

        invoice_name = self.payment_reference
        invoice_origin_account = self.invoice_origin
        # fetch product detail of sale.order in sale.order.line
        sale_order_find = self.env["sale.order"].search(
            [("name", "=", invoice_origin_account)]
        )

        customer_of_sale = sale_order_find.partner_id.id
        product_in_sales_order_line = sale_order_find.order_line

        self.env["account.move.warranty.wizard"].search(
            [("user_id", "=", self.env.user.id)]
        ).unlink()

        for product_data in product_in_sales_order_line:
            self.env["account.move.warranty.wizard"].create(
                {
                    "invoice_name": invoice_name,
                    "user_id": self.env.user.id,
                    "product_id_sold": product_data.product_id.id,
                    "sales_name": invoice_origin_account,
                    "order_line_id_picking": product_data.id,
                    "cust_id": customer_of_sale,
                    "starting_date": self.invoice_date,
                }
            )

        return {
            "type": "ir.actions.act_window",
            "name": "Warranty",
            "res_model": "account.move.warranty.wizard",
            "target": "new",
            "view_mode": "list",
            "view_type": "list",
            "context": {
                "default_user_id": self.env.user.id,
                "search_default_current_user": True,
            },
        }

    def action_form_opening(self):
        # send data to form using context (From account.move to product.warranty.track)
        sale_data = self.env["sale.order"].search([("name", "=", self.invoice_origin)])
        product_lines = []
        # product_idd = []
        for line in sale_data.order_line:
            product = line.product_id.product_tmpl_id

            # check if product have warranty checked in template
            if not product.product_warranty:
                continue

            lot_ids = (
                self.env["stock.move"]
                .search(
                    [
                        ("product_id", "=", line.product_id.id),
                        ("origin", "=", sale_data.name),
                    ]
                )
                .mapped("lot_ids")
            )
            # for product.warranty.track.line data
            product_lines.append(
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "lot_no_product": [(6, 0, lot_ids.ids)] if lot_ids else False,
                    },
                )
            )

        return {
            "name": "Warranty Form",
            "type": "ir.actions.act_window",
            "res_model": "product.warranty.track",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_customer_id": self.partner_id.id,
                "default_start_date": self.invoice_date,
                "default_sale_id": sale_data.id,
                "default_line_ids": product_lines,
            },
        }
