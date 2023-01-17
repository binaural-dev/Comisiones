from odoo import api, fields, models, _


class ResConfigSettingsBinauralNomina(models.TransientModel):
    _inherit = 'res.config.settings'

    _sql_constraints = [
        ('dia_adicional_posterior','CHECK(dia_adicional_posterior > 0)',
            'Dia adicional tiene que ser positivo'),
        ('dia_vacaciones_anno','CHECK(dia_vacaciones_anno > 0)',
            'Cantidad de dias de disfrute tiene que ser positivo'),
        ('dia_adic_cc','CHECK(dia_adic_cc >= 0)',
            'Dias adicionales por contratacion colectiva tiene que ser positivo'),
        ('dia_adic_bono_cc','CHECK(dia_adic_bono_cc >= 0)',
            'Dias adicionales de bono por contratacion colectiva tiene que ser positivo'),
        ('dias_utilidades','CHECK(dias_utilidades >= 0)',
            'Cantidad de días de utilidades tiene que ser positivo'),
        ('dias_prestaciones_mes','CHECK(dias_prestaciones_mes >= 0)',
            'Cantidad de días acumulados de prestaciones al mes tiene que ser positivo'),
        ('dias_prestaciones_anno','CHECK(dias_prestaciones_anno >= 0)',
            'Cantidad de días de prestaciones por año cumplido tiene que ser positivo'),
        ('maximo_dias_prestaciones_anno','CHECK(maximo_dias_prestaciones_anno >= 0)',
            'Cantidad máxima de días por años cumplidos tiene que ser positivo'),
        ('dia_cron_provisiones','CHECK(dia_cron_provisiones >= 1 AND dia_cron_provisiones <= 30)',
            'Dia del mes para ejecutar el cron de provisiones debe estar entre 1 y 30'),
    ]

    dia_cron_provisiones = fields.Integer(string="Día del mes para ejecutar el cron de provisiones")
    sueldo_base_ley = fields.Float(
        string="Sueldo base de ley", help="Sueldo base de ley", digits=(9,2))
    porcentaje_deduccion_faov = fields.Float(
        string="Porcentaje de deduccion FAOV", digits=(5,2),
        help="Porcentaje que se usara para la deduccion")
    porcentaje_deduccion_ince = fields.Float(
        string="Porcentaje de deduccion INCE", digits=(5,2),
        help="Porcentaje que se usara para la deduccion")

    porcentaje_deduccion_ivss = fields.Float(
        string="Porcentaje de deduccion IVSS", digits=(5,2),
        help="Porcentaje que se usara para la deduccion")
    tope_salario_ivss = fields.Integer(
        string="Tope salario IVSS",
        help="Cantidad de salarios maximos usados para el calculo de la deduccion")
    monto_maximo_ivss = fields.Float(string="Monto maximo deduccion", store=True, readonly=True)

    porcentaje_deduccion_pf = fields.Float(
        string="Porcentaje de deduccion Paro Forzoso", digits=(5,2),
        help="Porcentaje que se usara para la deduccion")
    tope_salario_pf = fields.Integer(
        string="Tope salario Paro Forzoso",
        help="Cantidad de salarios maximos usados para el calculo de la deduccion")
    monto_maximo_pf = fields.Float(string="Monto maximo deduccion Paro Forzoso", store=True, readonly=True)
    cuenta_analitica_departamentos = fields.Boolean(string="Cuenta analitica de los departamentos")

    #bono nocturno
    porcentaje_recargo_nocturno = fields.Float(
        string="Porcentaje de recargo para horas nocturas", digits=(5,2),
        help="Porcentaje de recargo para calcular el pago de hora nocturna")

    #vacaciones
    dia_adicional_posterior = fields.Integer(string="Dias adicionales posterior al primer año", help="Día adicional posterior al primer año de trabajo para el bono")
    dia_vacaciones_anno = fields.Integer(string="Cantidad de días de disfrute año 1", help="Cantidad de días de disfrute año 1")
    dia_adic_cc = fields.Integer(
        string="Dias adicionales por contratación colectiva",
        help="Dias adicionales por contratación colectiva")
    dia_adic_bono_cc = fields.Integer(
        string="Dias adicionales de bono por contratación colectiva",
        help="Dias adicionales de bono por contratación colectiva")

    #utilidades
    tipo_utilidades = fields.Selection(
        [('last_wage','Ultimo sueldo devengado'),
         ('annual_avg','Promedio de Salario Anual')],
        "Base para utilidades")
    dias_utilidades = fields.Integer(
        string="Cantidad de días de utilidades", help="Cantidad de días de utilidades")

    #prestaciones
    dias_prestaciones_mes = fields.Integer(
        string="Cantidad de días al mes", help="Cantidad de días acumulados de prestaciones al mes")
    dias_prestaciones_anno = fields.Integer(
        string="Cantidad de días por año cumplido", help="Cantidad de días acumulados de prestaciones por año cumplido")
    maximo_dias_prestaciones_anno = fields.Integer(
        string="Cantidad máxima de días por años cumplidos", help="Cantidad máxima de días por años cumplidos")
    tipo_calculo_intereses_prestaciones = fields.Selection(
        [("fideicomiso", "Fideicomiso"),
         ("interno", "Interno")],
        "Tipo de calculo de intereses de prestaciones",
        help="Si los intereses de prestaciones se calculan internamente o por fideicomiso")
    tasa_intereses_prestaciones = fields.Float(
        string="Tasa mensual de intereses de prestaciones",
        help="% de Tasa Mensual de Intereses de Prestaciones.")
    calculo_prestaciones = fields.Selection(
        [("mensual", "Mensual"),
        ("trimestral", "Trimestral")], 
        string="Calculo")

    def set_values(self):
        super(ResConfigSettingsBinauralNomina, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('sueldo_base_ley',self.sueldo_base_ley)

        self.env['ir.config_parameter'].sudo().set_param('porcentaje_deduccion_faov',self.porcentaje_deduccion_faov)
        self.env['ir.config_parameter'].sudo().set_param('porcentaje_deduccion_ince',self.porcentaje_deduccion_ince)

        self.env['ir.config_parameter'].sudo().set_param('porcentaje_deduccion_ivss',self.porcentaje_deduccion_ivss)
        self.env['ir.config_parameter'].sudo().set_param('tope_salario_ivss',self.tope_salario_ivss)
        self.env['ir.config_parameter'].sudo().set_param('monto_maximo_ivss',self.monto_maximo_ivss)

        self.env['ir.config_parameter'].sudo().set_param('porcentaje_deduccion_pf',self.porcentaje_deduccion_pf)
        self.env['ir.config_parameter'].sudo().set_param('tope_salario_pf',self.tope_salario_pf)
        self.env['ir.config_parameter'].sudo().set_param('monto_maximo_pf',self.monto_maximo_pf)
        self.env['ir.config_parameter'].sudo().set_param('cuenta_analitica_departamentos',self.cuenta_analitica_departamentos)

        #cron provisiones
        self.env['ir.config_parameter'].sudo().set_param('dia_cron_provisiones',self.dia_cron_provisiones)

        #bono nocturno
        self.env['ir.config_parameter'].sudo().set_param('porcentaje_recargo_nocturno',self.porcentaje_recargo_nocturno)

        #vacaciones
        self.env['ir.config_parameter'].sudo().set_param('dia_adicional_posterior',self.dia_adicional_posterior)
        self.env['ir.config_parameter'].sudo().set_param('dia_vacaciones_anno',self.dia_vacaciones_anno)
        self.env['ir.config_parameter'].sudo().set_param('dia_adic_cc',self.dia_adic_cc)
        self.env['ir.config_parameter'].sudo().set_param('dia_adic_bono_cc',self.dia_adic_bono_cc)
        
        #utilidades
        self.env['ir.config_parameter'].sudo().set_param('tipo_utilidades',self.tipo_utilidades)
        self.env['ir.config_parameter'].sudo().set_param('dias_utilidades',self.dias_utilidades)

        #prestaciones
        self.env['ir.config_parameter'].sudo().set_param('dias_prestaciones_mes',self.dias_prestaciones_mes)
        self.env['ir.config_parameter'].sudo().set_param('dias_prestaciones_anno',self.dias_prestaciones_anno)
        self.env['ir.config_parameter'].sudo().set_param('maximo_dias_prestaciones_anno',self.maximo_dias_prestaciones_anno)
        self.env['ir.config_parameter'].sudo().set_param('tipo_calculo_intereses_prestaciones',self.tipo_calculo_intereses_prestaciones)
        self.env['ir.config_parameter'].sudo().set_param('tasa_intereses_prestaciones',self.tasa_intereses_prestaciones)
        self.env['ir.config_parameter'].sudo().set_param('calculo_prestaciones',self.calculo_prestaciones)

    @api.model
    def get_values(self):
        res = super(ResConfigSettingsBinauralNomina, self).get_values()
        res['sueldo_base_ley'] = self.env['ir.config_parameter'].sudo().get_param('sueldo_base_ley')

        res['porcentaje_deduccion_faov'] = self.env['ir.config_parameter'].sudo().get_param('porcentaje_deduccion_faov')
        res['porcentaje_deduccion_ince'] = self.env['ir.config_parameter'].sudo().get_param('porcentaje_deduccion_ince')
        
        res['porcentaje_deduccion_ivss'] = self.env['ir.config_parameter'].sudo().get_param('porcentaje_deduccion_ivss')
        res['tope_salario_ivss'] = self.env['ir.config_parameter'].sudo().get_param('tope_salario_ivss')
        res['monto_maximo_ivss'] = self.env['ir.config_parameter'].sudo().get_param('monto_maximo_ivss')

        res['porcentaje_deduccion_pf'] = self.env['ir.config_parameter'].sudo().get_param('porcentaje_deduccion_pf')
        res['tope_salario_pf'] = self.env['ir.config_parameter'].sudo().get_param('tope_salario_pf')
        res['monto_maximo_pf'] = self.env['ir.config_parameter'].sudo().get_param('monto_maximo_pf')
        res['cuenta_analitica_departamentos'] = self.env['ir.config_parameter'].sudo().get_param('cuenta_analitica_departamentos')

        #cron provisiones
        res['dia_cron_provisiones'] = self.env['ir.config_parameter'].sudo().get_param('dia_cron_provisiones')

        #bono nocturno
        res['porcentaje_recargo_nocturno'] = self.env['ir.config_parameter'].sudo().get_param('porcentaje_recargo_nocturno')

        #vacaciones
        res['dia_adicional_posterior'] = self.env['ir.config_parameter'].sudo().get_param('dia_adicional_posterior')
        res['dia_vacaciones_anno'] = self.env['ir.config_parameter'].sudo().get_param('dia_vacaciones_anno')
        res['dia_adic_cc'] = self.env['ir.config_parameter'].sudo().get_param('dia_adic_cc')
        res['dia_adic_bono_cc'] = self.env['ir.config_parameter'].sudo().get_param('dia_adic_bono_cc')

        #utilidades
        res['tipo_utilidades'] = self.env['ir.config_parameter'].sudo().get_param('tipo_utilidades')
        res['dias_utilidades'] = self.env['ir.config_parameter'].sudo().get_param('dias_utilidades')
        
        #prestaciones
        res['dias_prestaciones_mes'] = self.env['ir.config_parameter'].sudo().get_param('dias_prestaciones_mes')
        res['dias_prestaciones_anno'] = self.env['ir.config_parameter'].sudo().get_param('dias_prestaciones_anno')
        res['maximo_dias_prestaciones_anno'] = self.env['ir.config_parameter'].sudo().get_param('maximo_dias_prestaciones_anno')
        res['tipo_calculo_intereses_prestaciones'] = self.env['ir.config_parameter'].sudo().get_param('tipo_calculo_intereses_prestaciones')
        res['tasa_intereses_prestaciones'] = self.env['ir.config_parameter'].sudo().get_param('tasa_intereses_prestaciones')
        res['calculo_prestaciones'] = self.env['ir.config_parameter'].sudo().get_param('calculo_prestaciones')

        return res

    @api.onchange('sueldo_base_ley','tope_salario_ivss','tope_salario_pf')
    def _onchange_topes_maximos(self):
        self.monto_maximo_ivss = self.sueldo_base_ley * self.tope_salario_ivss
        self.monto_maximo_pf = self.sueldo_base_ley * self.tope_salario_pf
