
def strftime_rfc3339(d):
    """d is a date that is assumed to be UTC."""
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")
