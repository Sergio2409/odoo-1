from openerp import models


class CrmLead(models.Model):

    _name = 'crm.lead'

    _inherit = [
        'crm.lead',
        'abstract.live',
    ]
