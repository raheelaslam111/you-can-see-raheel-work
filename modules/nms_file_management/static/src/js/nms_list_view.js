odoo.define('nms_file_management.nms_list_view', function (require) {

"use strict";

var core = require('web.core');

var ListController = require('web.ListController');
    /*ListController.include({
        renderButtons: function($node) {
        this._super.apply(this, arguments);
            if (this.$buttons) {
                let nms_import_button = this.$buttons.find('.o_list_nms_import_button');
                nms_import_button && nms_import_button.click(this.proxy('nms_import_button')) ;
            }
        },

        nms_import_button: function () {
            var action = this.do_action({
                name: _('Import NMS File'),
                type: 'ir.actions.act_window',
                view_mode: 'form',
                res_model: 'nms.file.import',
                res_id: false,
                views: [[false, 'form']],
                target: 'new',
                flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}
            });
        }
    });*/

    ListController.include({
        renderButtons: function($node) {
        this._super.apply(this, arguments);
            if (this.$buttons) {
                let nms_import_button = this.$buttons.find('.o_list_lot_nms_import_button');
                nms_import_button && nms_import_button.click(this.proxy('nms_import_button')) ;
            }
        },

        nms_import_button: function () {
            var action = this.do_action({
                name: _('Import NMS File'),
                type: 'ir.actions.act_window',
                view_mode: 'form',
                res_model: 'nms.file.import',
                res_id: false,
                views: [[false, 'form']],
                target: 'new',
                flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}
            });
        }
    });

})
