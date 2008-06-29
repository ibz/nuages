from datetime import datetime

import settings

def strftime_rfc3339(d):
    """d is a date that is assumed to be UTC."""
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")

def strftime_for_edit(d):
    """The timezone of d is simply ignored."""
    return d.strftime(settings.date_format_for_edit)

def strptime_for_edit(s):
    return datetime.strptime(s, settings.date_format_for_edit)
