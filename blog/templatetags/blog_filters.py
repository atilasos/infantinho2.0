from django import template

register = template.Library()

@register.filter
def replace(value, arg):
    """
    Replaces all occurrences of arg[0] with arg[1] in value.
    Usage: {{ value|replace:"old,new" }}
    """
    try:
        old, new = arg.split(',')
        return value.replace(old, new)
    except:
        return value

@register.filter
def replace_hyphen(value):
    """
    Replaces underscores with hyphens in the value.
    Usage: {{ value|replace_hyphen }}
    """
    return value.replace('_', '-') 