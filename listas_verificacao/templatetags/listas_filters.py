from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Retorna um item de um dicionário usando a chave fornecida."""
    if not isinstance(dictionary, dict):
        return None
    return dictionary.get(key)

@register.filter
def filter_validados(status_map, dominio):
    """Count the number of validated objectives for a given domain"""
    return sum(1 for status in status_map.values() 
              if status.objetivo.dominio == dominio and status.status == 'validado')

@register.filter
def div(value, arg):
    """Divide the value by the argument"""
    try:
        # Se value for uma lista, calcular a soma dos valores
        if isinstance(value, list):
            value = sum(float(x) for x in value if x is not None)
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter
def mul(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, ZeroDivisionError):
        return 0 