from odoo import fields, models, _, api
from datetime import date

class RepairWarranty(models.Model):
    _inherit = "repair.order"

    @api.onchange('lot_id')
    def _onchange_lot_warranty(self):
        fetch_warranty_line = self.env['product.warranty.track.line'].search([('lot_no_product','=',self.lot_id.id)])
        fetch_warranty = fetch_warranty_line.warranty_id
        warranty_start = fetch_warranty.start_date
        warranty_end = fetch_warranty.end_date
        today_date = date.today()
        if warranty_end:
            if warranty_end >= today_date:
                self.under_warranty = True
