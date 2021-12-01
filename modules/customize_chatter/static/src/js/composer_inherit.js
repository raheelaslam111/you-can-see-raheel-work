odoo.define('customize_chatter.InheritComposterJS', function (require) {
"use strict";
var core = require('web.core');
var _t = core._t;
var Dialog = require('web.Dialog');
var Class = require('web.Class');

var composer = require('mail.mail/static/src/components/composer/composer.js');

var ComposerVariable = composer.include({
    _onClickSend() {
//        _onClickSend() {
            alert("hello i am");
            console.log('abcd');
            if (this.composer.isLog)
            {
            this._postMessage()
            }
            else
            {
                Dialog.confirm(this, _t("Are you sure you want to post message?"), {
                confirm_callback: async () =>{ this._postMessage();
            }});
            }
//    }
    }
});

return { ComposerVariable: ComposerVariable};

});