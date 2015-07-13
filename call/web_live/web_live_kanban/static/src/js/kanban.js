openerp.web_live_kanban = function (instance) {
    /* WARNING use the old v7 api to include javascript
        because web_kanban hasn't been migrate yet on the new api */

    instance.web_kanban.KanbanView.include({
        start: function() {
            this._super.apply(this, arguments);
            this.card_in_modification = {}
            var model = this.dataset._model.name;
            openerp.bus.bus.on(
                'web_live-' + model + '-kanban', this, this.on_get_live_changed);
        },
        destroy: function() {
            var model = this.dataset._model.name;
            openerp.bus.bus.off(
                'web_live-' + model + '-kanban', this, this.on_get_live_changed);
            this._super();
        },
        on_get_live_changed: function (event) {
            var self = this;
            _(event.ids).each(function (id) {
                if (self.card_in_modification[id] == true) return

                self.card_in_modification[id] = true;
                var card = self.live_get_card(id);
                self.live_card_is_in_domain_search(id)
                .then( function () {
                    if (card) {
                        var group_id = event[self.group_by] || card.group.value;
                        var sequence = self.live_get_sequence(event, card);
                        self.live_card_moved(card, group_id, sequence);
                        card.do_reload();
                        self.card_in_modification[id] = false;
                    } else {
                        if (event[self.group_by]) self.live_create_card(event, id);
                        else {
                            self.dataset._model.call(
                                'read', [id, [self.group_by]], {load: '_classic_write'})
                            .then( function (record) {
                                event[self.group_by] = record[self.group_by];
                                self.live_create_card(event, id);
                            });
                        }
                    }
                })
                .fail( function () {
                    if (card) self.live_remove_card(card);
                });
            });
        },
        live_create_card: function(liveevent, card_id) {
            var self = this;
            group = self.live_get_group(liveevent[this.group_by]);
            if (group) {
                group.dataset.read_ids([card_id], group.view.fields_keys)
                .done(function (records) {
                    group.view.dataset.ids.push(card_id);
                    group.do_add_records(records);
                    var card = self.live_get_card(card_id);
                    var sequence = self.live_get_sequence(liveevent, card);
                    var group_by = liveevent[self.group_by];
                    self.live_card_moved(card, group_by, sequence);
                    self.card_in_modification[card_id] = false;
                });
            };
        },
        live_remove_card: function(card) {
            card.group.remove_record(card.id);
            card.destroy();
            this.card_in_modification[card.id] = false;
        },
        live_card_moved: function(card, group_id, sequence) {
            // reorder card in group at the new sequence
            var old_group = card.group;
            var new_group = null;
            var old_sequence = _.indexOf(old_group.records, card);
            if (card.group.value == group_id) new_group = old_group;
            else {
                new_group = this.live_get_group(group_id);
                card.group = new_group;
            }
            if (old_sequence != sequence || old_group != new_group) {
                old_group.records.splice(old_sequence, 1);
                new_group.records.splice(sequence, 0, card);
                var $old_group = old_group.$records.find('.oe_kanban_column_cards');
                $old_group.children()[old_sequence].remove();
                var $new_group = new_group.$records.find('.oe_kanban_column_cards');
                if ($new_group.children().length <= sequence || $new_group.children().length == 0) {
                    card.$el.appendTo($new_group).css({'opacity':0}).animate({'opacity':1}, 'slow');
                } else card.$el.insertBefore($new_group.children()[sequence]);
            }
        },
        live_get_group: function(id) {
            var g = null;
            _(this.groups).each(function (group) {
                if (group.value == id) g = group;
            });
            return g;
        },
        live_get_card: function(id) {
            var card = null;
            _(this.groups).each(function (group) {
                _(group.records).each(function (record) {
                    if (record.id == id) card = record;
                });
            });
            return card;
        },
        live_get_sequence: function(liveevent, card) {
            var sequence = card.group.records.length;
            if (liveevent.sequence != undefined) sequence = liveevent.sequence;
            else if (card.record.sequence) sequence = card.record.sequence.raw_value;
            return sequence;
        },
        live_card_is_in_domain_search: function(id) {
            var def = $.Deferred();
            var domain = [].concat(this.search_domain, [['id', '=', id]]);
            this.dataset._model.call('search', [domain]).then( function(ids) {
                if (ids.length) def.resolve();
                else def.reject();
            });
            return def;
        },
    });
};
