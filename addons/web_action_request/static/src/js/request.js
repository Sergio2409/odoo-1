(function() {
    openerp.web.WebClient.include({
        declare_bus_channel: function() {
            this._super();
            var channel = 'action.request_' + this.session.uid;
            this.bus_on(channel, function(action) {
                openerp.client.action_manager.do_action(action);
            });
            this.add_bus_channel(channel);
        },
    });
})();
