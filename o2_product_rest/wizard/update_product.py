from openerp import models, fields, api
from openerp.exceptions import except_orm
import base64


MAGIC_TYPES = ('binary', )
MAGIC_COLUMNS = ('id', 'create_uid', 'create_date', 'write_uid', 'write_date', 'packaging_ids',
                 'attribute_line_ids', 'product_variant_ids', 'attribute_value_ids')


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1", "si")


class import_transient_product(models.TransientModel):
    _name = 'import.transient.product'

    @api.model
    def _get_model(self):
        return self.env['ir.model'].search([('model', '=', self._context['active'])]).id

    model = fields.Many2one('ir.model', 'Modelo', default=_get_model)
    is_update = fields.Boolean('es actualizacion?', default=True)
    data_file = fields.Binary('Archivo(.csv)')
    update_fields = fields.One2many('import.transient.product.fields', 'transient_import_id', 'Campos a actualizar', required=True)

    @api.one
    def button_update(self):
        toimport_fields = list()
        model_env = self.env[self.model.model]
        if not self.data_file:
            raise except_orm('Error!', 'El campo Archivo(.csv) esta vacio')
        buf = base64.decodestring(self.data_file).split('\n')
        buf = buf[:len(buf) - 1]
        line_fields = True
        for line in buf:
            item = line.split(',')
            # pro_template = self.env['product.template'].search([('o2s_id', '=', int(item[0]))]) # Este segmento solo para insertar los impuestos y se comenta el resto del metodo
            # tax = self.env['account.tax'].search([('name', '=', str(item[1]))])
            # query = 'INSERT INTO product_supplier_taxes_rel (prod_id, tax_id) VALUES (%s, %s)' % (pro_template.id, tax.id)
            # self._cr.execute(query)
            if line_fields:
                toimport_fields = item
                line_fields = False
                continue
            model_obj = model_env.browse(long(item[0])) # Descomentar aqui y comentar las 7 lineas de abajo
            # if long(item[1]) == 9: #1
            #     item[1] = '0' + item[1] #2
            # employee = self.env['hr.employee'].search([('identification_id', '=', str(item[0])), ('company_id', '=', int(item[1]))]) #3
            # if not employee:
            #     print 'Esta cedula no esta:', item[0]
            #     continue
            # model_obj = employee.contract_id #4
            for field in self.update_fields:
                value = dict()
                if not field.obj_field_name in toimport_fields:
                    raise except_orm('Error!', 'El campo %s a importar no se encuentra en el archivo' % field.obj_field_name)
                index = toimport_fields.index(field.obj_field_name)
                if field.obj_type not in ('one2many', 'many2many'):
                    value = self.set_dictvalue(field.obj_field_name, field.obj_type, item, index, value)
                elif field.obj_type == 'one2many':
                    obj_env = self.env[field.obj_field.relation]
                    tocreate = dict()
                    for name_field, field_obj in obj_env._fields.iteritems():
                        if field_obj.type not in ('one2many', 'many2many'):
                            if field_obj.required and name_field not in toimport_fields and name_field not in obj_env._defaults:
                                raise except_orm('Error!', 'El campo %s del modelo %s no se encuentra en el archivo' % (name_field, field.obj_field.relation))
                            if field_obj.required and name_field not in toimport_fields and name_field in obj_env._defaults:
                                continue
                            index = toimport_fields.index(name_field)
                            tocreate = self.set_dictvalue(name_field, field_obj.type, item, index, tocreate)
                    obj_env.create(tocreate)
                elif field.obj_type == 'many2many':
                    toupdate = list()
                    many_ids = item[index].split(';')
                    for my_id in many_ids:
                        try:
                            toupdate.append(long(my_id))
                        except ValueError:
                            raise except_orm('Error!', 'Formato no valido en el campo %s' % field.obj_field_name)
                    value[field.obj_field_name] = [[6, 0, toupdate]]

                model_obj.write(value)
        return True

    def set_dictvalue(self, param_field_name, param_field_type, item, index, value):

        if param_field_type in ('integer', 'float'):
            try:
                if param_field_type == 'float':
                    val = float(item[index])
                else:
                    val = int(item[index])
            except ValueError:
                raise except_orm('Error!', 'Formato numerico no valido para el campo %s' % param_field_name)
        elif param_field_type == 'many2one':
            try:
                val = long(item[index])
            except ValueError:
                raise except_orm('Error!', 'Formato no valido para campo %s de tipo many2one' % param_field_name)
        elif param_field_type == 'boolean':
            try:
                val = str2bool(item[index])
            except ValueError:
                raise except_orm('Error!', 'Formato no valido para campo %s de tipo boolean' % param_field_name)
        else:
            val = item[index]
        value[str(param_field_name)] = val

        return value

class import_transient_product_fields(models.TransientModel):
    _name = 'import.transient.product.fields'

    obj_field_name = fields.Char('Nombre', required=True)
    obj_type = fields.Char('Tipo', required=True)
    obj_field_required = fields.Boolean('Requerido?')
    transient_import_id = fields.Many2one('import.transient.product', 'Transient Update')
    obj_field = fields.Many2one('ir.model.fields', 'Campo', required=True)

    @api.onchange('obj_field')
    def onchange_obj_field(self):
        res = dict()
        self.obj_field_name = self.obj_field.name
        self.obj_type = self.obj_field.ttype
        self.obj_field_required = self.obj_field.required
        res['domain'] = {'obj_field': [('model', '=', self.transient_import_id.model.model), ('name', 'not in', MAGIC_COLUMNS),
                                       ('ttype', 'not in', MAGIC_TYPES)]}
        return res

