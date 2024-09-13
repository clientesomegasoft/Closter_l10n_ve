odoo.define('omegasoft_employee_arc.yearpicker', function (require) {
	'use strict';

	var field_registry = require('web.field_registry');
	var datepicker = require('web.datepicker');
	var basic_fields = require('web.basic_fields')

	var YearPickerWidget = datepicker.DateWidget.extend({
		init: function (parent, options) {
			this._super.apply(this, arguments);
			this.name = parent.name;
			this.options = _.extend({
				locale: moment.locale(),
				viewMode:    'years',
				minViewMode: 'years',
				viewSelect:  'years',
				autoclose: true,
				format: 'YYYY',
				minDate: moment({ y: 1000 }),
				maxDate: moment({ y: 9999 }),
				useCurrent: false,
				widgetParent: 'body',
				keyBinds: null,
			}, options || {});
		},

		_formatClient: function (v) {
			return v.format(this.options.format);
		},

		_parseClient: function (v) {
			return moment(v, this.options.format)
		},

	});

	var YearPicker = basic_fields.FieldDate.extend({
		supportedFieldTypes: ['integer'],

		init: function () {
			this._super.apply(this, arguments);
			this.formatOptions.timezone = true;
		},

		start: function () {
			var self = this;
			var promise;
			if(self.mode === 'edit'){
				self.datewidget = self._makeDatePicker();
				self.datewidget.on('datetime_changed', self, function () {
					var value = self._getValue();
					if ((!value && self.value) || (value && !self._isSameValue(value))) {
						self._setValue(value);
					}
				});
				promise = self.datewidget.appendTo('<div>').then(function () {
					self.datewidget.$el.addClass(self.$el.attr('class'));
					self._prepareInput(self.datewidget.$input);
					self._replaceElement(self.datewidget.$el);
				});
			}
			return Promise.resolve(promise).then(self._super.bind(self));
		},

		_makeDatePicker: function () {
			return new YearPickerWidget(this, this.datepickerOptions);
		},

		_formatValue: function(value) {
			if(!this.shouldFormat || (this.mode === 'edit' && this.nodeOptions.type === 'number')){
				return value;
			}
			return String(value);
		},

		_parseValue: function (value) {
			if(this.mode === 'edit' && this.nodeOptions.type === 'string'){
				return String(value);
			}
			if( this.mode === 'edit' && moment.isMoment(value) ){
				return parseInt(value.format('Y'), 10);
			}
			return Number(value);
		},

		_renderEdit: function () {
			var liftedValue = moment(String(this.value), 'Y');
			this.datewidget.setValue( liftedValue );
			this.$input = this.datewidget.$input;
		},

		_isSameValue: function (value) {
			if (this.value === false || value === false) {
				return this.value === value;
			}
			return this.value == value;
		},
	});

	field_registry.add('fieldyear_int', YearPicker);
	return YearPicker;
});