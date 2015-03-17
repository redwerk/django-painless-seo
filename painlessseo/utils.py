from painlessseo import settings
from painlessseo.models import SeoMetadata
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import activate, get_language
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.forms.models import model_to_dict
from django.core.urlresolvers import resolve
from painlessseo.models import SeoRegisteredModel

import re


def get_fallback_metadata(lang_code):
    title = settings.FALLBACK_TITLE
    description = settings.FALLBACK_DESCRIPTION
    lang = lang_code
    if isinstance(settings.FALLBACK_TITLE, dict):
        if lang_code not in settings.FALLBACK_TITLE:
            lang = settings.DEFAULT_LANG_CODE
        title = settings.FALLBACK_TITLE[lang]
    if isinstance(settings.FALLBACK_DESCRIPTION, dict):
        if lang_code not in settings.FALLBACK_DESCRIPTION:
            lang = settings.DEFAULT_LANG_CODE
        description = settings.FALLBACK_DESCRIPTION[lang]

    return {
        'title': title,
        'description': description,
        }


def get_instance_metadata(instance, lang_code):
    if instance:
        ctype = ContentType.objects.get_for_model(instance)
        available_metadata = SeoRegisteredModel.objects.filter(
            content_type=ctype, lang_code=lang_code).order_by('id')

        if available_metadata.exists():
            total = available_metadata.count()
            index = 0
            if hasattr(instance, 'id'):
                index = instance.id % total
            elif hasattr(instance, 'pk'):
                index = instance.pk % total

            return {
                'title': available_metadata[index].title,
                'description': available_metadata[index].description,
            }

    return get_fallback_metadata(lang_code)


def format_metadata(result, instance=None, lang_code=None, path_args=None):
    formatted_metadata = {}
    for meta_key, meta_value in result.iteritems():
        formatted_metadata[meta_key] = format_from_instance(
            string=format_from_params(string=meta_value, path_args=path_args),
            instance=instance,
            lang_code=lang_code)

    return formatted_metadata


def format_from_params(string, path_args=None):
    # Format using parameters
    result = string
    if path_args:
        index = 0
        for arg in path_args:
            arg = re.sub('-', ' ', arg).title()
            result = re.sub(
                r'\{\s*%d\s*\}' % (index), arg, result)
            index += 1

    return result


def format_from_instance(string, instance=None, lang_code=None):
    # Now substitute parameters {XX} by instance.XX (only for instance based
    result = string
    if instance and lang_code:
        matches = re.findall(r"\{\s*([^\}\s]+)\s*\}", string)
        if matches:
            for match in matches:
                # For each field, check if exists the one for the language
                field_lang = "%s_%s" % (match, lang_code)
                if hasattr(instance, field_lang):
                    result = re.sub(
                        r"\{\s*%s\s*\}" % match,
                        unicode(getattr(instance, field_lang)),
                        result)
                elif hasattr(instance, match):
                    result = re.sub(
                        r"\{\s*%s\s*\}" % match,
                        unicode(getattr(instance, match)),
                        result)
                else:
                    raise ValueError(
                        "Model %s does not have attribute %s" % (
                            instance.__class__, match.strip()))
    return result


def get_path_metadata(path, lang_code, instance=None):
    # By default, fallback to general default
    result = get_fallback_metadata(lang_code)

    # Find correct metadata
    seometadata = None
    path_args = None

    try:
        # Try to find exact match
        seometadata = SeoMetadata.objects.get(
            path=path, lang_code=lang_code)

    except SeoMetadata.DoesNotExist:
        # SeoMetadata not found, try to find an alternative path
        abstract_seometadatas = SeoMetadata.objects.filter(
            lang_code=lang_code
            ).filter(
            Q(path__icontains="{") | Q(path__icontains="}")).order_by('-path')

        for abs_seometadata in list(abstract_seometadatas):
            regex_path = re.sub(r'\{\d+\}', r'([\w\d\-]+)', abs_seometadata.path)
            regex_path = '^' + regex_path + '$'
            match = re.search(regex_path, path)
            if match:
                seometadata = abs_seometadata
                path_args = match.groups()
                break

    if seometadata:
        # If seometadata found
        result = seometadata.get_metadata()
        instance = seometadata.content_object or instance

    else:
        # No exact nor abstract seo metadata found, prepare default
        if instance:
            # Look for registered model default
            result = get_instance_metadata(instance, lang_code)

    # At this point, result contains the resolved value before formatting.
    formatted_result = format_metadata(result, instance, lang_code, path_args)

    return formatted_result


def update_seo(sender, instance, auto_languages=[], **kwargs):
    active_lang = get_language()

    for lang_code, lang_name in settings.SEO_LANGUAGES:
        activate(lang_code)
        ctype = ContentType.objects.get_for_model(instance)

        try:
            sm = SeoMetadata.objects.get(
                content_type=ctype,
                object_id=instance.id,
                lang_code=lang_code)

            # If it exists, update path
            absolute_url = instance.get_absolute_url()
            if absolute_url and absolute_url != sm.path:
                sm.path = absolute_url
                sm.save()

        except SeoMetadata.DoesNotExist:
            # If it does not exists, only create if it is from sync command
            if lang_code in auto_languages:
                absolute_url = instance.get_absolute_url()
                metadata = get_instance_metadata(instance, lang_code)
                if absolute_url:
                    sm = SeoMetadata(
                        content_type=ctype,
                        object_id=instance.id,
                        lang_code=lang_code,
                        path=absolute_url,
                        title=metadata["title"],
                        description=metadata["description"])
                    sm.save()

    activate(active_lang)


def delete_seo(sender, instance, **kwargs):
    ctype = ContentType.objects.get_for_model(instance)
    for sm in SeoMetadata.objects.filter(content_type=ctype, object_id=instance.id):
        sm.delete()


def register_seo_signals():
    for app, model in settings.SEO_MODELS:
        ctype = ContentType.objects.get(app_label=app.lower(), model=model.lower())
        if not hasattr(ctype.model_class(), 'get_absolute_url'):
            raise ImproperlyConfigured("Needed get_absolute_url method not defined on %s.%s model." % (app, model))
        models.signals.post_save.connect(update_seo, sender=ctype.model_class(), weak=False)
        models.signals.pre_delete.connect(delete_seo, sender=ctype.model_class(), weak=False)
