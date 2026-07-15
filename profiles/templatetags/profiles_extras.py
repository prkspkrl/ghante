from django import template


register = template.Library()


@register.filter
def color_index(value):
    return value % 8


@register.filter
def star_range(rating):
    full = int(rating)
    half = 1 if rating - full >= 0.3 else 0
    empty = 5 - full - half
    return {'full': range(full), 'half': range(half), 'empty': range(empty)}
