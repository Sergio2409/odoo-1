from openerp import models, fields, api
from lxml.etree import Element, SubElement, tostring


MODULES_TYPES = [
    ('kanban', 'module_web_live_kanban'),
]


VIEW_TYPE = [
    ('kanban', 'Kanban'),
    #('from', 'Form'),
    #('tree', 'Tree'),
]


class WebLiveModelConfig(models.Model):
    _name = 'web.live.model.config'
    _description = 'Configuration by model'

    model = fields.Many2one('ir.model', required=True)
    view_type = fields.Selection(selection=VIEW_TYPE, String='View type',
                                 required=True)
    isselected = fields.Boolean('Is selected')


class WebLiveConfig(models.TransientModel):
    _name = 'web.live.config'
    _description = 'Web live config'
    _inherit = 'res.config.settings'

    # View module
    module_web_live_kanban = fields.Boolean(string='Kanban')
    # module_web_live_form = fields.Boolean(string='from')
    # module_web_live_tree = fields.Boolean(string='tree')

    # Module linked and model linked
    module_live_crm = fields.Boolean(string='CRM')
    live_crm_lead_kanban = fields.Boolean(string='CRM lead / Kanban',
                                          required=True,
                                          module='live_crm',
                                          view_type='kanban')
    # ...

    @api.model
    def default_get(self, fields):
        res = super(WebLiveConfig, self).default_get(fields)
        mods = {}
        for mod in self.env['web.live.model.config'].search([]):
            if mod.model.model not in mods:
                mods[mod.model.model] = {}

            mods[mod.model.model][mod.view_type] = mod.isselected

        for name in fields:
            if name.startswith('live_'):
                column = self._columns[name]
                has_module = hasattr(column, 'module')
                has_view_type = hasattr(column, 'view_type')
                if has_module and has_view_type:
                    model = name[5:]
                    model = '.'.join(model.split('_')[:-1])
                    vtype = column.view_type

                    res[name] = mods.get(model, {}).get(vtype, False)

        return res

    @api.multi
    def execute(self):
        res = super(WebLiveConfig, self).execute()
        mod_obj = self.env['web.live.model.config']
        read = self.read()[0]
        for name in read.keys():
            if name.startswith('live_'):
                column = self._columns[name]
                has_module = hasattr(column, 'module')
                has_view_type = hasattr(column, 'view_type')
                if has_module and has_view_type:
                    model = name[5:]
                    model = '.'.join(model.split('_')[:-1])
                    vtype = column.view_type

                    mods = mod_obj.search([('model.model', '=', model),
                                           ('view_type', '=', vtype)])
                    if mods:
                        mods.write({'isselected': read[name]})
                    else:
                        models = self.env['ir.model'].search(
                            [('model', '=', model)])

                        if not models:
                            continue

                        mod_obj.create(dict(
                            model=models.id, view_type=vtype,
                            isselected=read[name]))

        return res

    @api.model
    def parse_live(self):
        modules = {}
        types = dict(kanban=[])

        columns = self._columns.items()
        columns.sort()

        for name, column in columns:
            has_module = hasattr(column, 'module')
            has_view_type = hasattr(column, 'view_type')
            if name.startswith('live_') and has_module and has_view_type:
                if column.module not in modules:
                    modules['module_%s' % column.module] = []

                modules['module_%s' % column.module].append(
                    (column.view_type, name))

                types[column.view_type].append(name)

        return modules, types

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        if view_type != 'form':
            return super(WebLiveConfig, self).fields_view_get(
                view_id=view_id, view_type=view_type, toolbar=toolbar,
                submenu=submenu)

        def sets(node, attributes):
            for key, value in attributes:
                node.set(key, value)

        models_by_modules, models_by_type = self.parse_live()

        form = Element('form')
        sets(form, (('string', 'Web live'), ('version', '7.0')))

        header = SubElement(form, 'header')

        bapply = SubElement(header, 'button')
        sets(bapply, (('string', 'Apply'), ('type', 'object'),
                      ('name', 'execute'), ('class', 'oe_highlight')))

        bcancel = SubElement(header, 'button')
        sets(bcancel, (('string', 'Cancel'), ('type', 'object'),
                       ('name', 'cancel'), ('class', 'oe_link')))

        group = SubElement(form, 'group')
        sets(group, (('string', 'Type of view'), ))
        for vtype, module in MODULES_TYPES:
            field = SubElement(group, 'field')
            sets(field, (('name', module),
                         ('on_change', "onchange_type(%s, '%s')" % (
                             module, "', '".join(models_by_type[vtype])))))

        modules = self._get_classified_fields()
        modules = [x for x in modules['module']
                   if x[0] not in [y[1] for y in MODULES_TYPES]]

        for module, record in modules:
            if record is None:
                continue

            models = models_by_modules.get(module, [])

            group = SubElement(form, 'group')
            sets(group, (('string', record.shortdesc), ('col', '4')))

            field = SubElement(group, 'field')
            sets(field, (('name', module),
                         ('string', 'Install(ed) / uninstall(ed)'),
                         ('on_change', "onchange_module(%s, '%s')" % (
                             module, "', '".join([x[1] for x in models])))))

            sub_group = SubElement(group, 'group')
            sets(sub_group, (
                ('col', '2'),
                ('colspan', '2'),
            ))
            for vtype, model in models:
                field = SubElement(sub_group, 'field')
                mod_vtype = dict(MODULES_TYPES)[vtype]
                sets(field, (
                    ('name', model),
                    ('on_change', "onchange_model(%s, '%s', '%s')" % (
                        model, module, mod_vtype))))

        arch = tostring(form)
        fields = self.fields_get()
        tb = {'print': [], 'action': [], 'relate': []}

        return {
            'arch': arch,
            'fields': fields,
            'toolbar': tb,
        }

    # keep old on change api because the same one has use for all field
    # and the field are dynamical

    def onchange_type(self, cr, uid, ids, active, *models):
        if active:
            return {}

        return {'value': dict((m, False) for m in models)}

    def onchange_module(self, cr, uid, ids, active, *models):
        if active:
            return {}

        return {'value': dict((m, False) for m in models)}

    def onchange_model(self, cr, uid, ids, active, *modules):
        if not active:
            return {}

        return {'value': dict((m, True) for m in modules)}
