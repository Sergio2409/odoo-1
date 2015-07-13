from openerp.osv import fields, osv
from openerp import pooler
import threading,time, base64
from EchoClient import WhatsappEchoClient
from Contacts.contacts import WAContactsSyncRequest
import sys

def resultToString(result):
    unistr = str if sys.version_info >= (3, 0) else unicode
    out = []
    for k, v in result.items():
        if v is None:
            continue
        out.append("%s: %s" %(k, v.encode("utf-8") if type(v) is unistr else v))
        
    return "\n\n".join(out)

class yowsup_partner_send(osv.osv):
    _name = 'yowsup.partner.send'
    def _default_get_mobile(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        partner_pool = self.pool.get('res.partner')
        active_ids = fields.get('active_ids')
        res = {}
        i = 0
        for partner in partner_pool.browse(cr, uid, active_ids, context=context): 
            i += 1           
            res = partner.mobile
        if i > 1:
            raise orm.except_orm(_('Error'), _('You can only select one partner'))
        return res
    def _default_get_gateway(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        obj = self.pool.get('yowsup.gateway')
        gateway_ids = obj.search(cr, uid, [], limit=1, context=context)
        return gateway_ids and gateway_ids[0] or False
    
    _columns = {
        'mobile_to': fields.char('To', size=50, required=True),
        'message': fields.char('message', size=512, required=False),  
        'gateway': fields.many2one('yowsup.gateway', 'Whatsapp Gateway', required=True),
        }
    _defaults = {
        'mobile_to': _default_get_mobile,
        'gateway': _default_get_gateway,        
    }
    def whatsapp_send(self, cr, uid, ids, context=None):
        for move in self.browse(cr, uid, ids, context=context): 
            phone = move.mobile_to.encode('utf-8')
            message = move.message.encode('utf-8') 
            wa = WhatsappEchoClient(phone, message)
            login = move.gateway.phone
            
            password = move.gateway.password
            password = base64.b64decode(bytes(password.encode('utf-8')))
            wa.login(login, password)
        return self.pool.get('warning_box').info(cr, uid, title='Test send message', message="Ok")
    
    def whatsapp_sync(self, cr, uid, ids, context=None):
        for move in self.browse(cr, uid, ids, context=context):
            contacts = move.mobile_to.encode('utf-8').split(',')
            for index in range(len(contacts)):
                if contacts[index][0] !='+':
                    contacts[index] = '+' + contacts[index]
                
            login = move.gateway.phone
            password = move.gateway.password
            password = base64.b64decode(bytes(password.encode('utf-8')))
            wsync = WAContactsSyncRequest(login, password, contacts)
            result = wsync.send()
            result = resultToString(result)
            return self.pool.get('warning_box').info(cr, uid, title='Test sync contacts', message=result)

yowsup_partner_send()