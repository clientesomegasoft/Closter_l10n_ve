odoo.define("l10n_ve_arc_report.report_filter", function (require) {
    "use strict";

    var {
        WarningDialog,
    } = require("@web/legacy/js/_deprecated/crash_manager_warning_dialog");
    var StandaloneFieldManagerMixin = require("web.StandaloneFieldManagerMixin");
    var account_report = require("account_reports.account_report");
    var accountReportsWidget = account_report.accountReportsWidget;
    var RelationalFields = require("web.relational_fields");
    var datepicker = require("web.datepicker");
    var Widget = require("web.Widget");
    var core = require("web.core");
    var QWeb = core.qweb;
    var _t = core._t;

    var M2OFilters = Widget.extend(StandaloneFieldManagerMixin, {
        init: function (parent, fields) {
            this._super.apply(this, arguments);
            StandaloneFieldManagerMixin.init.call(this);
            this.fields = fields;
            this.widgets = {};
        },

        willStart: function () {
            var self = this;
            var defs = [this._super.apply(this, arguments)];
            _.each(this.fields, function (field, fieldName) {
                defs.push(self._makeM2OWidget(field, fieldName));
            });
            return Promise.all(defs);
        },

        start: function () {
            var self = this;
            var $content = $(QWeb.render("m2oWidgetTable", {fields: this.fields}));
            self.$el.append($content);
            _.each(this.fields, function (field, fieldName) {
                self.widgets[fieldName].appendTo(
                    $content.find("#" + fieldName + "_field")
                );
            });
            return this._super.apply(this, arguments);
        },

        _confirmChange: function () {
            var self = this;
            var result = StandaloneFieldManagerMixin._confirmChange.apply(
                this,
                arguments
            );
            var data = {};
            _.each(this.fields, function (filter, fieldName) {
                data[fieldName] = {};
                if (self.widgets[fieldName].value) {
                    data[fieldName] = {
                        id: self.widgets[fieldName].value.data.id,
                        name: self.widgets[fieldName].value.data.display_name,
                    };
                }
            });
            this.trigger_up("m2o_changed", data);
            return result;
        },

        _makeM2OWidget: function (fieldInfo, fieldName) {
            var self = this;
            var options = {};
            options[fieldName] = {options: {no_create: true, no_open: true}};
            return this.model
                .makeRecord(
                    fieldInfo.modelName,
                    [
                        {
                            fields: [
                                {
                                    name: "id",
                                    type: "integer",
                                },
                                {
                                    name: "display_name",
                                    type: "char",
                                },
                            ],
                            name: fieldName,
                            relation: fieldInfo.modelName,
                            type: "many2one",
                            value: fieldInfo.value.id,
                            domain: fieldInfo.domain,
                        },
                    ],
                    options
                )
                .then(function (recordID) {
                    self.widgets[fieldName] = new RelationalFields.FieldMany2One(
                        self,
                        fieldName,
                        self.model.get(recordID),
                        {mode: "edit"}
                    );
                    self._registerWidget(recordID, fieldName, self.widgets[fieldName]);
                });
        },
    });

    var yearpicker = datepicker.DateWidget.extend({
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.name = parent.name;
            this.options = _.extend(
                {
                    locale: moment.locale(),
                    viewMode: "years",
                    format: "YYYY",
                    minDate: moment({y: 1000}),
                    maxDate: moment({y: 9999}),
                    widgetParent: "body",
                },
                options || {}
            );
            this.__libInput = 2;
            this.__isOpen = false;
        },
    });

    accountReportsWidget.include({
        custom_events: _.extend({}, accountReportsWidget.prototype.custom_events, {
            m2o_changed: function (ev) {
                this.report_options.partner_id = ev.data.partner_id;
                return this.reload();
            },
        }),

        render_searchview_buttons: function () {
            var self = this;
            this._super.apply(this, arguments);

            // YEAR FILTER
            var $yearpickers = this.$searchview_buttons.find(
                ".js_account_reports_yearpicker"
            );
            $yearpickers.each(function () {
                var name = $(this).find("input").attr("name");
                var defaultValue = $(this).data("default-value");
                var dt = new yearpicker({});
                dt.replace($(this)).then(function () {
                    dt.$el.find("input").attr("name", name);
                    if (defaultValue) {
                        dt.setValue(moment({y: defaultValue}));
                    }
                });
            });

            this.$searchview_buttons
                .find(".js_account_report_year_filter")
                .click(function () {
                    var year = self.$searchview_buttons.find(
                        '.o_datepicker_input[name="year"]'
                    );
                    var error = year.val() === "";
                    self.report_options.year = parseInt(year.val(), 10);
                    if (error) {
                        new WarningDialog(
                            self,
                            {title: _t("Odoo Warning")},
                            {message: _t("Date cannot be empty")}
                        ).open();
                    } else {
                        self.reload();
                    }
                });

            // M2OFILTER
            if ("partner_id" in this.report_options) {
                if (this.partner_m2o_filter === undefined) {
                    this.partner_m2o_filter = new M2OFilters(this, {
                        partner_id: {
                            label: _t("Proveedor"),
                            modelName: "res.partner",
                            value: this.report_options.partner_id,
                            domain: [
                                [
                                    "partner_type",
                                    "in",
                                    ["supplier", "customer_supplier"],
                                ],
                            ],
                        },
                    });
                    this.partner_m2o_filter.appendTo(
                        this.$searchview_buttons.find(".js_m2o_filters")
                    );
                } else {
                    this.$searchview_buttons
                        .find(".js_m2o_filters")
                        .append(this.partner_m2o_filter.$el);
                }
            }
        },
    });
});
