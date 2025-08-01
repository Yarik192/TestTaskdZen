from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    return int(value) * int(arg)

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
