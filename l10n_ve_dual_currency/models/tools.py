# -*- coding: utf-8 -*-

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from datetime import date, datetime, time
import pytz

def to_datetime(value, tz=None):
	if isinstance(value, date):
		value = datetime.combine(value, time.max).replace(microsecond=0)
	elif isinstance(value, str):
		value = datetime.strptime(value, DATETIME_FORMAT[:len(value)-2]).replace(hour=23, minute=59, second=59)
	elif not (value and isinstance(value, datetime)):
		return None

	if value.tzinfo:
		raise ValueError("Datetime field expects a naive datetime: %s" % value)

	return (tz and pytz.timezone(tz).localize(value).astimezone(pytz.UTC) or value).replace(tzinfo=None)