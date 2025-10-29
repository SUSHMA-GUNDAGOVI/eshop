from django import template
import json
from django import template
register = template.Library()

@register.filter
def split(value, arg):
    """
    Splits a string by the given argument and returns a list.
    Usage: {{ product.size|split:"," }}
    """
    return value.split(arg)


register = template.Library()

@register.filter
def to_json(value):
    return json.dumps(value)

@register.filter
def lower(value):
    """
    Converts a string to lowercase. Used for generating unique IDs.
    """
    return value.lower()


@register.filter
def split(value, delimiter):
    """
    Split a string by delimiter and return list
    """
    if value and delimiter:
        return [item.strip() for item in value.split(delimiter)]
    return []