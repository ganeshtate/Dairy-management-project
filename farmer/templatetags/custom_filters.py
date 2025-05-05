from django import template

register = template.Library()

# Custom filter to convert text to uppercase
@register.filter(name='my_upper')
def my_upper(value):
    """Converts a string to uppercase."""
    if isinstance(value, str):
        return value.upper()
    return value

# Custom filter to get nested dictionary item safely
@register.filter(name='get_item')
def get_item(dictionary, key):
    """Safely get item from dictionary by key."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def split(value, delimiter=' '):
    return value.split(delimiter)
