from openerp import models, api


class AbstractLive(models.AbstractModel):
    _name = 'abstract.live'
    _description = 'Abstract Live'

    @api.model
    def notify(self, kwargs):
        kwargs.update({
            'model': self._name,
        })
        mods = self.env['web.live.model.config'].search(
            [('model.model', '=', self._name)])
        kwargs.update({r.view_type: r.isselected for r in mods})
        notifies = []
        for user in self.env.user.search([('id', '!=', self.env.uid)]):
            notifies.append(('web_live_%d' % user.id, kwargs))

        self.env['bus.bus'].sendmany(notifies)

    @api.model
    def create(self, values):
        res = super(AbstractLive, self).create(values)
        kwargs = dict(ids=[res.id])
        kwargs.update(res.read(load='_classic_write')[0])
        self.notify(kwargs)
        return res

    @api.multi
    def write(self, values):
        res = super(AbstractLive, self).write(values)
        if len(values) == 1 and values.get('message_last_post'):
            pass
        else:
            kwargs = dict(ids=[x.id for x in self])
            kwargs.update(values)
            self.notify(kwargs)

        return res

    @api.multi
    def unlink(self):
        res = super(AbstractLive, self).unlink()
        self.notify(ids=[x.id for x in self])
        return res
