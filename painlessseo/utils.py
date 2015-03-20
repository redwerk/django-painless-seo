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
import hashlib


def get_fallback_metadata(lang_code, index=0):
    titles = settings.FALLBACK_TITLE
    descriptions = settings.FALLBACK_DESCRIPTION
    lang = lang_code
    if isinstance(titles, dict):
        if lang_code not in titles:
            lang = settings.DEFAULT_LANG_CODE
        title = titles[lang]
        if isinstance(title, list):
            title = title[index % len(title)]

    if isinstance(descriptions, dict):
        if lang_code not in descriptions:
            lang = settings.DEFAULT_LANG_CODE
        description = descriptions[lang]
        if isinstance(description, list):
            description = description[index % len(description)]

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


def format_metadata(result, instance=None, lang_code=None, path_args=[], seo_context={}):
    formatted_metadata = {}
    path_context = {}
    for index in range(0, len(path_args)):
        path_context[str(index)] = path_args[index]
    seo_context.update(path_context)
    for meta_key, meta_value in result.iteritems():
        # First format using the instance
        instance_string = format_from_instance(
            string=meta_value,
            instance=instance,
            lang_code=lang_code)
        # Then format using the context
        formatted_metadata[meta_key] = format_from_params(
            string=instance_string,
            **seo_context)

    return formatted_metadata


def format_from_params(string, **kwargs):
    # Format using parameters
    result = string
    if kwargs:
        for name, value in kwargs.iteritems():
            value = re.sub('-', ' ', str(value)).title()
            result = re.sub(
                r'\{\s*%s\s*\}' % (name), value, result)

    return result


def format_from_instance(string, instance=None, lang_code=None):
    # Now substitute parameters {XX} by instance.XX (only for instance based
    result = string
    if instance and lang_code:
        matches = re.findall(r"\{\s*([^\}\s]+)\s*\}", string)
        if matches:
            for match in matches:
                # For each field, check if exists the one for the language
                attrs = match.split('.')
                base = instance
                found = True
                for attr in attrs:
                    field_lang = "%s_%s" % (attr, lang_code)
                    if hasattr(base, field_lang):
                        attr_name = field_lang
                    elif hasattr(base, attr):
                        attr_name = attr
                    elif base is None:
                        # In case is a foreign key with 'None' value
                        # We can't go deeper, but we found the attr
                        attr_value = None
                        break
                    else:
                        # Attr not found, so let it like it is
                        found = False
                        break

                    attr_value = getattr(base, attr_name)
                    if hasattr(attr_value, 'get'):
                        base = attr_value.get()
                    else:
                        base = attr_value

                if found:
                    result = re.sub(
                        r"\{\s*%s\s*\}" % match,
                        unicode(attr_value or ''),
                        result)
    return result


def get_path_metadata(path, lang_code, instance=None, seo_context={}):
    # By default, fallback to general default
    index = int(hashlib.md5(path).hexdigest(), 16)
    result = get_fallback_metadata(lang_code, index=index)

    # Find correct metadata
    seometadata = None
    path_args = []

    try:
        # Try to find exact match
        seometadata = SeoMetadata.objects.get(
            path=path, lang_code=lang_code)

    except SeoMetadata.DoesNotExist:
        # SeoMetadata not found, try to find an alternative path
        abstract_seometadatas = SeoMetadata.objects.filter(
            lang_code=lang_code, has_parameters=True,
            ).order_by('id')
        matches = []

        # Collect all metadatas that matches the path
        for abs_seometadata in list(abstract_seometadatas):
            regex_path = re.sub(r'\{\d+\}', r'([\w\d\-]+)', abs_seometadata.path)
            regex_path = '^' + regex_path + '/?$'
            match = re.search(regex_path, path)
            if match:
                matches.append({
                    'seometadata': abs_seometadata,
                    'groups': match.groups(),
                    })

        if len(matches) > 0:
            random_match = matches[index % len(matches)]
            seometadata = random_match['seometadata']
            path_args = random_match['groups']

    if seometadata:
        # If seometadata found
        result = seometadata.get_metadata()
        instance = seometadata.content_object or instance

    else:
        # No exact nor abstract seo metadata found, prepare default
        if instance:
            # Look for registered model default
            result = get_instance_metadata(instance, lang_code) or result

    # At this point, result contains the resolved value before formatting.
    formatted_result = format_metadata(result, instance, lang_code, path_args, seo_context)

    return formatted_result


def update_seo(sender, instance, auto_languages=[], **kwargs):
    active_lang = get_language()

    for lang_code, lang_name in settings.SEO_LANGUAGES:
        activate(lang_code)
        ctype = ContentType.objects.get_for_model(instance)

        sms = SeoMetadata.objects.filter(
            content_type=ctype,
            object_id=instance.id,
            lang_code=lang_code)

        if sms.exists():
            # If it exists, update path
            absolute_url = instance.get_absolute_url()
            for sm in sms.all():
                if absolute_url and absolute_url != sm.path:
                    sm.path = absolute_url
                    sm.save()
        else:
            # If it does not exists, only create if it is from sync command
            if lang_code in auto_languages:
                absolute_url = instance.get_absolute_url()
                metadata = get_fallback_metadata(lang_code)
                metadata = get_instance_metadata(instance, lang_code) or metadata
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
