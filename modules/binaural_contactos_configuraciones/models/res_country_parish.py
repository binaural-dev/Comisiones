from odoo import api, fields, models, _

class ResCountryParish(models.Model):
    _name = 'res.country.parish'
    _description = 'Parroquias'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código', required=True)
    municipality_id = fields.Many2one('res.country.municipality', string='Municipio', required=True)
