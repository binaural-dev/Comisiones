from odoo import api, fields, models, _


class ResConfigSettingsBinauralFacturacion(models.TransientModel):
	_inherit = 'res.config.settings'

	not_cost_higher_price_invoice = fields.Boolean(string='No permitir costo mayor o igual al precio de venta en facturas')
	account_longitude_report = fields.Integer(string='Longitud de auxiliar de cuenta contable')
	tax_today = fields.Boolean(string='Activar Tasas para los Activos')
	series_invoicing = fields.Boolean()

	def set_values(self):
		super(ResConfigSettingsBinauralFacturacion, self).set_values()
		self.env['ir.config_parameter'].sudo().set_param('not_cost_higher_price_invoice', self.not_cost_higher_price_invoice)
		self.env['ir.config_parameter'].sudo().set_param('account_longitude_report', self.account_longitude_report)
		self.env['ir.config_parameter'].sudo().set_param('tax_today', self.tax_today)
		self.env['ir.config_parameter'].sudo().set_param('series_invoicing', self.series_invoicing)

	@api.model
	def get_values(self):
		res = super(ResConfigSettingsBinauralFacturacion, self).get_values()
		res['not_cost_higher_price_invoice'] = self.env['ir.config_parameter'].sudo().get_param('not_cost_higher_price_invoice')
		res['account_longitude_report'] = self.env['ir.config_parameter'].sudo().get_param('account_longitude_report')
		res['tax_today'] = self.env['ir.config_parameter'].sudo().get_param('tax_today')
		res['series_invoicing'] = self.env['ir.config_parameter'].sudo().get_param('series_invoicing')

		return res
