# Copyright (C) 2014 Glamping Hub (https://glampinghub.com)
# License: BSD 3-Clause

from django.template import Library
from django.utils.translation import get_language

from painlessseo import settings
from painlessseo.models import SeoMetadata
from painlessseo.utils import get_path_metadata
from django import template

register = Library()


@register.filter
def single_quotes(description):
    return description.replace('\"', '\'')


@register.tag(name='capture_as')
def do_capture_as(parser, token):
    try:
        tag_name, args = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError("'capture_as' node requires a variable name.")
    nodelist = parser.parse(('endcapture_as',))
    parser.delete_first_token()
    return CaptureAsNode(nodelist, args)


class CaptureAsNode(template.Node):
    def __init__(self, nodelist, varname):
        self.nodelist = nodelist
        self.varname = varname

    def render(self, context):
        output = self.nodelist.render(context)
        # Trim and remove duplicated spaces
        output = output.strip()
        output = " ".join(output.split())
        context[self.varname] = output
        return ''


@register.inclusion_tag('painlessseo/metadata.html', takes_context=True)
def get_seo(context, **kwargs):
    path = context['request'].path
    lang_code = get_language()[:2]
    view = context.get('view', None)
    seo_context = {}
    seo_obj = None

    if view:
        # Try to get the instance if exists
        try:
            if hasattr(view, 'get_object'):
                seo_obj = view.get_object()
        except AttributeError:
            pass

        # Try to get seo_context
        seo_context = view.get_context_data()
        if hasattr(view, 'get_seo_context'):
            seo_context = view.get_seo_context()

    metadata = get_path_metadata(
        path=path, lang_code=lang_code,
        instance=seo_obj,
        seo_context=seo_context)

    result = {}
    for item in ['title', 'description']:
        result[item] = (
            metadata.get(item) or
            kwargs.get(item))
    return result


@register.simple_tag(takes_context=True)
def get_seo_title(context, default=''):
    return get_seo(context, title=default).get('title')


@register.simple_tag(takes_context=True)
def get_seo_description(context, default=''):
    return get_seo(context, description=default).get('description')
