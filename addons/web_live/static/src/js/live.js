(function() {
    openerp.web.WebClient.include({
        declare_bus_channel: function() {
            this._super();
            var channel = 'web_live_' + this.session.uid;
            this.bus_on(channel, function(message) {
                var e = 'web_live-' + message.model + '-';
                if (message.kanban) {
                    openerp.bus.bus.trigger(e + 'kanban', message);
                }
            });
            this.add_bus_channel(channel);
        },
    });
})();
