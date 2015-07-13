from openerp.osv import fields, osv
from openerp import pooler
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import argparse, sys, os, csv
from Common.utilities import Utilities
from EchoClient import WhatsappEchoClient
from Registration.v2.existsrequest import WAExistsRequest as WAExistsRequestV2
from Contacts.contacts import WAContactsSyncRequest
from ListenerClient import WhatsappListenerClient
from Registration.v2.regrequest import WARegRequest as WARegRequestV2
from Registration.v2.coderequest import WACodeRequest as WACodeRequestV2
import threading,time, base64

COUNTRIES_CSV = "countries.csv"

def startDbusInterface():
    from dbus.mainloop.glib import DBusGMainLoop
    from Yowsup.Interfaces.DBus.DBusInterface import DBusInitInterface
    import gobject
    
    DBusGMainLoop(set_as_default=True)
    
    DBusInitInterface()
    
    mainloop = gobject.MainLoop()
    
    gobject.threads_init()
    print("starting")
    mainloop.run()


def resultToString(result):
    unistr = str if sys.version_info >= (3, 0) else unicode
    out = []
    for k, v in result.items():
        if v is None:
            continue
        out.append("%s: %s" %(k, v.encode("utf-8") if type(v) is unistr else v))
        
    return "\n\n".join(out)

def getCredentials(config):
    if os.path.isfile(config):
        f = open(config)
        
        phone = ""
        idx = ""
        pw = ""
        cc = ""
        
        try:
            for l in f:
                line = l.strip()
                if len(line) and line[0] not in ('#',';'):
                    
                    prep = line.split('#', 1)[0].split(';', 1)[0].split('=', 1)
                    
                    varname = prep[0].strip()
                    val = prep[1].strip()
                    
                    if varname == "phone":
                        phone = val
                    elif varname == "id":
                        idx = val
                    elif varname =="password":
                        pw =val
                    elif varname == "cc":
                        cc = val

            return (cc, phone, idx, pw);
        except:
            pass

    return 0

def dissectPhoneNumber(phoneNumber):
    try:
        with open(COUNTRIES_CSV, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                if len(row) == 3:
                    country, cc, mcc = row
                else:
                    country,cc = row
                    mcc = "000"
                try:
                    if phoneNumber.index(cc) == 0:
                        print("Detected cc: %s"%cc)
                        return (cc, phoneNumber[len(cc):])

                except ValueError:
                    continue
                
    except:
        pass
    return False


class yowsup_gateway(osv.osv):
    _name = 'yowsup.gateway'
    _columns = {'name':fields.char('name', size=30, required=True), 
                'cc':fields.char('code region', size=3, required=True), 
                'phone':fields.char('phone number', size=15, required=True),
                'idphone':fields.char('mac emei', size=30, required=False),
                'password':fields.char('password', size=30, required=False), 
                'test_to': fields.char('test to', size=50, required=False), 
                'test_message': fields.char('test message', size=512, required=False),  
                'autoack': fields.boolean('auto ack',required=False),   
                'keepalive': fields.boolean('keep alive',required=False), 
                'request_code': fields.selection([('sms','sms'), ('voice','voice')],'request code', required=False),
                'register_code': fields.char('register code',size=20,required=False),           
                }
    def test_sync(self, cr, uid, ids, context=None):
        for move in self.browse(cr, uid, ids, context=context):
            contacts = move.test_to.encode('utf-8').split(',')
            for index in range(len(contacts)):
                if contacts[index][0] !='+':
                    contacts[index] = '+' + contacts[index]
                
            login = move.phone
            password = move.password
            password = base64.b64decode(bytes(password.encode('utf-8')))
            wsync = WAContactsSyncRequest(login, password, contacts)
            result = wsync.send()
            result = resultToString(result)
            return self.pool.get('warning_box').info(cr, uid, title='Test sync contacts', message=result)
            
    def test_exists(self, cr, uid, ids, context=None):
        for move in self.browse(cr, uid, ids, context=context):
            identity = move.idphone
            identity = Utilities.processIdentity(identity)
            
            countryCode = move.cc
            login = move.phone
            phoneNumber = login[len(countryCode):]
            
            we = WAExistsRequestV2(countryCode, phoneNumber, identity)
            result = we.send()
            print(resultToString(result))
    
            if result["pw"] is not None:
                print("\n=========\nWARNING: %s%s's has changed by server to \"%s\", you must update your config file with the new password\n=========" %(countryCode, phoneNumber, result["pw"]))

    def test_gateway(self, cr, uid, ids, context=None):
        for move in self.browse(cr, uid, ids, context=context):               
            time_local = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT) 
            phone = move.test_to.encode('utf-8')
            message = move.test_message.encode('utf-8') + "\n\nTime: " + time_local
            wa = WhatsappEchoClient(phone, message)
            
            login = move.phone
            
            password = move.password
            password = base64.b64decode(bytes(password.encode('utf-8')))
            wa.login(login, password)
        return self.pool.get('warning_box').info(cr, uid, title='Test send message', message="Ok")
     
    def test_listen(self, cr, uid, ids, context=None):
        for move in self.browse(cr, uid, ids, context=context): 
            login = move.phone
            password = move.password
            password = base64.b64decode(bytes(password.encode('utf-8')))
            wa = WhatsappListenerClient( move.keepalive,move.autoack)
            wa.login(login, password)
            
    def request_code(self, cr, uid, ids, context=None):
        result = {}
        for move in self.browse(cr, uid, ids, context=context): 
            method = move.request_code
            if method not in ("sms","voice"):
                return self.pool.get('warning_box').info(cr, uid, title='Request Phone', message='error')   
            else:
                identity = move.idphone
                identity = Utilities.processIdentity(identity)
                countryCode = move.cc
                login = move.phone
                phoneNumber = login[len(countryCode):]
                wc = WACodeRequestV2(countryCode, phoneNumber, identity, method)
                result = wc.send()
                result = resultToString(result) + "\n" + "https://coderus.openrepos.net/whitesoft/whatsapp_sms"
                return self.pool.get('warning_box').info(cr, uid, title='REquest Phone', message=result)
        return self.pool.get('warning_box').info(cr, uid, title='Request Phone', message='error')   
            
                    
    def register(self, cr, uid, ids, context=None):
        result = {}
        for move in self.browse(cr, uid, ids, context=context): 
            code = move.register_code
            code = "".join(code.split('-'))
            identity = move.idphone
            identity = Utilities.processIdentity(identity)
            countryCode = move.cc
            login = move.phone
            phoneNumber = login[len(countryCode):]
            wr = WARegRequestV2(countryCode, phoneNumber, code, identity)
            result = wr.send()
            result = resultToString(result)
        return self.pool.get('warning_box').info(cr, uid, title='Register Phone', message=result)
            
               
yowsup_gateway()