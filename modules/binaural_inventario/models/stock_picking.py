# -*- coding: utf-8 -*-

from odoo import models, fields, api,exceptions
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

class StockPickingBinauralInventario(models.Model):
    _inherit = 'stock.picking'

    def _default_currency_id(self):
        return self.env.ref('base.VEF').id
    
    def default_alternate_currency(self):
        alternate_currency = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))

        if alternate_currency:
            return alternate_currency
        else:
            return False

    #foreign_currency_id = fields.Many2one('res.currency', compute='_compute_foreign_currency')
    #foreign_currency_rate = fields.Monetary(string="Tasa", tracking=True, currency_field='foreign_currency_id',
    #                                        compute='_compute_foreign_currency')
    foreign_currency_id = fields.Many2one('res.currency', default=default_alternate_currency,
                                          tracking=True)
    foreign_currency_rate = fields.Float(string="Tasa", tracking=True)
    foreign_currency_date = fields.Date(string="Fecha", default=fields.Date.today(), tracking=True)
    update_cost_inventory = fields.Boolean(string='Actualizar costo del producto',default=False)

    def _action_done(self):
        if self.picking_type_id.code in ['incoming'] and self.env['ir.config_parameter'].sudo().get_param('not_account_purchase'):
           res = super(StockPickingBinauralInventario, self)._action_done()
           for picking in self:
              for account in  picking.move_lines.account_move_ids:
                  account.write({'state': 'cancel'})
                  return res

        elif self.picking_type_id.code in ['outgoing'] and self.env['ir.config_parameter'].sudo().get_param('not_account_sell'):
            res = super(StockPickingBinauralInventario, self)._action_done()
            for picking in self:
                for account in picking.move_lines.account_move_ids:
                    account.write({'state': 'cancel'})
                    return res
        else:
            res = super(StockPickingBinauralInventario, self)._action_done()
            return res

    def action_confirm(self):
        #no aplicar para interna y compra
        #si esta activa la prohibicion
        for picking in self:
            if picking.picking_type_code in ['outgoing','internal'] and picking.env['ir.config_parameter'].sudo().get_param('not_move_qty_higher_store'):
                for sm in picking.move_ids_without_package:
                    quant = picking.env['stock.quant'].search(
                        [('location_id', '=', picking.location_id.id), ('product_id', '=', sm.product_id.id)], limit=1)
                    qty = sm.product_uom_qty
                    if quant and qty > (quant.quantity - quant.reserved_quantity):
                        raise exceptions.ValidationError(
                            "** No se puede realizar la transferencia. La cantidad a transferir es mayor a la cantidad disponible en el almacen**")
            picking._check_company()
            picking.mapped('package_level_ids').filtered(lambda pl: pl.state == 'draft' and not pl.move_ids)._generate_moves()
            # call `_action_confirm` on every draft move
            picking.mapped('move_lines')\
                .filtered(lambda move: move.state == 'draft')\
                ._action_confirm()

            # run scheduler for moves forecasted to not have enough in stock
            picking.mapped('move_lines').filtered(lambda move: move.state not in ('draft', 'cancel', 'done'))._trigger_scheduler()

        return True

    @api.depends('origin')
    def _compute_foreign_currency(self):
        for record in self:
            foreign_currency_rate = foreign_currency_id = 0
            if record.origin:
                sale_id = record.env['sale.order'].search([('name', '=', record.origin)], limit=1)
                if sale_id:
                    foreign_currency_id = sale_id.currency_id.id
                    foreign_currency_rate = sale_id.foreign_currency_rate
                else:
                    purchase_id = record.env['purchase.order'].search([('name', '=', record.origin)], limit=1)
                    if purchase_id:
                        foreign_currency_id = purchase_id.currency_id.id
                        foreign_currency_rate = purchase_id.foreign_currency_rate
            else:
                alternate_currency = int(record.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))
                foreign_currency_id = alternate_currency
                rate = self.env['res.currency.rate'].search([('currency_id', '=', foreign_currency_id),
                                                             ('name', '<=', fields.Date.today())], limit=1,
                                                            order='name desc')
                foreign_currency_rate = rate.rate
            record.foreign_currency_id = foreign_currency_id
            record.foreign_currency_rate = foreign_currency_rate

    @api.constrains('move_ids_without_package')
    def _validate_transfer_qty(self):
        """ Validar que no se pueda mover mas de la cantidad disponible en almacen
            Validar que la cantidad realizada en la transferencia no sea mayor a la Demanda inicial"""

        for record in self:
            if record.picking_type_id.code in ['outgoing','internal'] and self.env['ir.config_parameter'].sudo().get_param('not_move_qty_higher_store'):
                for sm in record.move_ids_without_package:
                    quant = record.env['stock.quant'].search([('location_id', '=', record.location_id.id), ('product_id', '=', sm.product_id.id)], limit=1)
                    qty = sm.product_uom_qty
                    qty_done = sm.quantity_done
                    if quant and qty > (quant.quantity - quant.reserved_quantity):
                        raise exceptions.ValidationError("** No se puede realizar la transferencia. La cantidad a transferir es mayor a la cantidad disponible en el almacen**")
                    
                    
class PurchaseOrderBinauralInventario(models.Model):
    _inherit = 'purchase.order'

    def _prepare_picking(self):
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id
            })
        if not self.partner_id.property_stock_supplier.id:
            raise UserError(_("You must set a Vendor Location for this partner %s", self.partner_id.name))
        return {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': self.partner_id.id,
            'user_id': False,
            'date': self.date_order,
            'origin': self.name,
            'location_dest_id': self._get_destination_location(),
            'location_id': self.partner_id.property_stock_supplier.id,
            'company_id': self.company_id.id,
            'foreign_currency_rate': self.foreign_currency_rate,
            'foreign_currency_id': self.foreign_currency_id.id,
        }
