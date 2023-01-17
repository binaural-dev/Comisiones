from odoo import api, fields, models, _


class ResConfigSettingsBinauralNominaReportes(models.TransientModel):
    _inherit = "res.config.settings"

    numero_afiliacion_nomina = fields.Char(
        string="Número de afiliación de nomina", help="Número de afiliación de nomina."
    )
    separador_campos_ivss = fields.Selection(
        [(";", ";"), (":", ":")],
        string="Separador de campos de IVSS",
        default=";",
        help="Separador de campos de txt de carga masiva del IVSS.",
    )
    separador_decimales_ivss = fields.Selection(
        [(".", "."), (",", ",")],
        string="Separador de decimales de IVSS",
        default=",",
        help="Separador de decimales de txt de carga masiva del IVSS.",
    )

    def set_values(self):
        super().set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "numero_afiliacion_nomina", self.numero_afiliacion_nomina
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "separador_campos_ivss", self.separador_campos_ivss
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "separador_decimales_ivss", self.separador_decimales_ivss
        )

    def get_values(self):
        res = super().get_values()
        res["numero_afiliacion_nomina"] = (
            self.env["ir.config_parameter"].sudo().get_param("numero_afiliacion_nomina")
        )
        res["separador_campos_ivss"] = (
            self.env["ir.config_parameter"].sudo().get_param("separador_campos_ivss")
        )
        res["separador_decimales_ivss"] = (
            self.env["ir.config_parameter"].sudo().get_param("separador_decimales_ivss")
        )
        return res
