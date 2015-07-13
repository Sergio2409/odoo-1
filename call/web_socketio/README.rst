WEB_SOCKETIO
============

`Socket.IO <http://socket.io>`_ is a virtual socket create for 
`Nodejs <http://nodejs.org>`_. It 's an asynchronious socket base on the events.
You can define your events without do a rpc request 

What have you to use Socket.IO?
-------------------------------

Supported transports
~~~~~~~~~~~~~~~~~~~~

In order to provide realtime connectivity on every browser, Socket.IO selects 
the most capable transport at runtime, without it affecting the API.

* WebSocket
* Adobe® Flash® Socket
* AJAX long polling
* AJAX multipart streaming
* Forever Iframe
* JSONP Polling

upported browsers
~~~~~~~~~~~~~~~~~

* Desktop:
    * Internet Explorer 5.5+
    * Safari 3+
    * Google Chrome 4+
    * Firefox 3+
    * Opera 10.61+
* Mobile:
    * iPhone / iPad Safari
    * Android WebKit
    * WebOs WebKit

What is the requirement
-----------------------

We need to get 3 python eggs:

* `gevent <http://www.gevent.org>`_: provides a wsgi server based on greenlets, and patches the python 
  eggs to replace blocking instructions.
* `gevent_psycopg2 <https://github.com/zacharyvoase/gevent-psycopg2>`_: Patches psycopg2 egg for gevent
* `gevent_socketio <https://github.com/abourget/gevent-socketio>`_: wsgi server based on gevent wsgi server for SocketIO

Install the python eggs needed for gevent_socketio::

    pip install gevent
    pip install gevent_psycopg2
    pip install gevent_socketio

Apache or Nginx to make a url dispatcher.

How to use SocketIO with OpenERP
--------------------------------

Make your Nginx/Apache conf
~~~~~~~~~~~~~~~~~~~~~~~~~~~

example conf for nginx::

    worker_processes  1;

    events {
        worker_connections  1024;
    }

    http {
        server {
            listen  80;
            server_name www.myopenerp.fr;
            location /socket.io {
                proxy_pass   http://127.0.0.1:8068;
                proxy_http_version 1.1;

                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection "upgrade";
                proxy_set_header Host $host;

                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto https;

                proxy_redirect off;
            }
            location / {
                proxy_pass   http://127.0.0.1:8069;
            }
        }
    }


Example conf for Apache, neep proxy and proxy_http modules::

    <VirtualHost *:80>
    	ServerAdmin jssuzanne@anybox.fr
    	ServerName www.myopenerp.fr
    
    	<location /socket.io/1/websocket/>
    		ProxyPass wss://localhost:8068/socket.io/1/websocket/
    	</location>
    	<location /socket.io/>
    		ProxyPass http://localhost:8068/socket.io/
    	</location>
    	<location />
    		ProxyPass http://localhost:8069/
    	</location>
    
    </VirtualHost>

.. warning:: No websocket with Apache 2.2

/etc/hosts::

    127.0.0.1       www.myopenerp.fr


the port::

    8069: the OpenERP server
    8068: the long polling server


/socketio is the default path to dispatch the poll

Start the OpenERP server
~~~~~~~~~~~~~~~~~~~~~~~~

Install the web_socketio module or module which depends on web_socketio::

    oe -d mydb -i web_socketio


Start the long polling server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

start the server::

    python web_socketio/web_socketio/server.py -d mydb

the server has 4 options:

* -d: Database names (Default: the conf file db_name)
* -i: Interface(Default: 127.0.0.1)
* -p: Port(Default: 8068)
* --max-cursor: The max number of the simultaneous open cursor  by databases


How to use long polling in OpenERP module
-----------------------------------------

Notions
~~~~~~~

SocketIO use 3 notions:

* NameSpace: A group of event, all the event in the same NameSpace and the 
  same socket share them information.
* Event: Javascript event, exist also in the server
* Signal: key to link a emition to an event.

Module
~~~~~~

You have to add web_socketio in the dependencies of your module. The module 
add Javascript function to call SocketIO and Python 
class to declare the namespace

Python
~~~~~~

the module ``web_socketio`` give a class to make a NameSpace ``OpenERPNameSpace``.

This class inherit of basenamespace of gevent_socketio add some event:

* ``recv_connect``: Receive a connect signal.
* ``recv_disconnect``: Receive a disconnect signal.
* ``on_session_id``: Receive a session_id signal, this signal must be received to 
  get the OpenERP session and validate if the user is connected.

The NameSpace have got some method to communicate with OpenERP:

* ``model``: Return an OpenERP model wrapper
* ``listen``: web_socket use postgresql notification, The gevent server listen 
  only one channel postgres, and stock in sub channel, For use this method you
  must define AdapterClass for postresql notification in NameSpace
* ``Validate``: indicate if the listen return is valide or must be put the 
  return of listen in the sub listen.
* ``secure_emit``: call emit, if emit is done with sucess validate the listen return
* ``notify``: make a postgres.notification

You must inherit of the ``OpenERPNameSpace`` and The class as a namespace in 
``web_socketio`` server.

To declare an event you must add the event in you class by a method begining 
by ``on_`` the event name.

Example::

    from openerp.addons.web_socketio.namespace import OpenERPNameSpace
    from openerp.addons.web_socketio.web_socketio import SocketIO


    class MyNameSpace(OpenERPNameSpace):

        def on_myEvent(self):
            pass


    SocketIO.add_namespace('/mynamespace', MyNameSpace)


The declared namespaces are on the log::

    2013-09-08 12:35:19,728 42106 INFO socketio openerp.addons.web_socketio.web_socketio: Add namespace: '/MyNameSpace'

The adapterClass is a class inherit of ``AbstractAdapter`` you can inherit 
the method:

* ``get`` which return the message to take. the argumments are ``self, messages, *args`` the args must be passed at the method listen
* ``format``: Modify the messages return by the listen

.. warning:: The messages return by get must be the same than message chosen, no modification

Example of Adapter::

    class MyAdapter(AbstractAdapter):
        channel = 'im_user'

        def get(self, messages, uid):
            res = []
            for m in messages:
                if m['values']['to_id'] == uid:
                    res.append(m)
            return res

Javascript
~~~~~~~~~~

Use the OpenERP function ``ìnstance.web.SocketIO`` to create a socket to the
SocketIO server::

    var socket = new instance.web.SocketIO('/MyNameSpace')

The socket created have got function:
* ``on``: Add an event
* ``emit``: Emit a signal
* ``disconnect``: Emit a disconnect signal


WEB_LONGPOLLING
===============

this module inherit the ``web_socketio`` module. This module add a new 
namespace ``/namespace`` and an instance of the ``instance.web.SocketIO`` 
when the javascriot is connected. The socket is disconnected when the 
javascript client is deconnected or reload when hte client is reload.

Module
------

You have to add web_longpolling in the dependencies of your module.

Javascript
----------

The module create one connection, we use the same connection for all the long
polling connection is needed::

    instance.web.longpolling_socket.on('other signal', function(messages) {
        console.log(messages);
    });
    instance.web.longpolling_socket.emit(signal, user_id)

Python
------

The ``LongPollingNameSpace`` inherit the ``OpenERPNameSpace`` and add the 
method ``on``. This method is a decorator to add event in the namespace. This
method have got three arguments:

* event name: the name of the event
* ``adpaterClass``: Adapter class tu use with this event
* ``eventtype``: they 3 type of event:
    * ``connect``: Call at the connection of the socket
    * ``on`` (default): A simple event
    * ``diconnect``: A event call after the close of the connection

The event add by the method ``on`` receive at the first argument an instance
of socketio session. You can use the methode of the namespace without give the
adapterClass::

    @on('signal', adapterClass=MyAdapter)
    def my_function(session, user_id):
        """ It is an example 
        messages = session.listen(sessuin.uid)
        user_obj = session.model('res.users')
        # the cr and uid are give in the wrapper and only by the wrapper
        # is to use the pool of connection 
        data = user_obj.format_message(user_id, messages)
        session.secure_emit('other signal', data)

Buildout
========

Example of buildout configuration::

    [buildout]
    parts = openerp
    versions = versions
    extensions = gp.vcsdevelop
    vcs-extend-develop = hg+http://bitbucket.org/anybox/oe_web_socketio#egg=oe.web.socketio
    vcs-update = true
    
    [openerp]
    recipe = anybox.recipe.openerp[bzr]:server
    version = bzr lp:openobject-server/7.0 openerp-server last:1
    addons = bzr lp:openobject-addons/7.0 openerp-addons last:1
             bzr lp:openerp-web/7.0 openerp-web last:1 subdir=addons
             hg http://bitbucket.org/anybox/web_socketio web_socketio default
    
    eggs = oe.web.socketio
    
    openerp_scripts = nosetests=nosetests command-line-options=-d
                      oe_web_socketio=oe_web_socketio 
    
    [versions]
    lxml = 2.3.3
    docutils = 0.9
    collective.recipe.sphinxbuilder = 0.7.3
    pyparsing = 1.5.6
    Werkzeug = 0.8.3

Build the buildout::

    bin/buildout -c buildout.cfg

Run the OpenERP server in the first shell::

    bin/start_openerp -d mydb

Run the Gevent SocketIO server in the second shell::

    ./bin/oe_web_socketio -d mydb

