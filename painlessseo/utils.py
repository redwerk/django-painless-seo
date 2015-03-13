from painlessseo import settings
from painlessseo.models import SeoMetadata
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import activate, get_language
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.forms.models import model_to_dict
import re


def get_seomodel_titles(cls):
    return cls.SEO_DEFAULT_TITLES if hasattr(cls, "SEO_DEFAULT_TITLES") else settings.FALLBACK_TITLE


def get_seomodel_descriptions(cls):
    return cls.SEO_DEFAULT_DESCRIPTIONS if hasattr(cls, "SEO_DEFAULT_DESCRIPTIONS") else settings.FALLBACK_DESCRIPTION


def get_seomodel_metadatas(cls, metadata):
    if metadata == 'title':
        return get_seomodel_titles(cls=cls)
    if metadata == 'description':
        return get_seomodel_descriptions(cls=cls)


def get_for_lang(item, lang_code):
    if isinstance(item, str):
        return item
    elif isinstance(item, dict):
        return get_key_or_default(item, lang_code, settings.DEFAULT_LANG_CODE)


def get_key_or_default(item, key, default_key):
    if (key in item):
        return item[key]
    else:
        return item[default_key]


def get_formatted_metadata(path, lang_code):
    # Find correct metadata
    result = {}

    try:
        seometadata = SeoMetadata.objects.get(
            path=path, lang_code=lang_code)
        metadata_dict = model_to_dict(seometadata)

        for item in ['title', 'description']:
            # Get the correct fallback title or description if None or empty
            seo_item = metadata_dict[item]
            if seo_item is None or seo_item == '':
                seo_item = get_for_lang(get_seomodel_metadatas(
                    cls=instance.__class__, metadata=item), lang_code)

            # Now substitute parameters {XX} by instance.XX (only for instance based)
            if seometadata.content_object:
                # Path is from SEO Model instance
                instance = seometadata.content_object

                matches = re.findall(r"\{\s*([^\}\s]+)\s*\}", seo_item)
                if matches:
                    for match in matches:
                        # For each field, check if exists the one for the language
                        field_lang = "%s_%s" % (match, lang_code)
                        if hasattr(instance, field_lang):
                            seo_item = re.sub(
                                r"\{\s*%s\s*\}" % match,
                                unicode(getattr(instance, field_lang)),
                                seo_item)
                        elif hasattr(instance, match):
                            seo_item = re.sub(
                                r"\{\s*%s\s*\}" % match,
                                unicode(getattr(instance, match)),
                                seo_item)
                        else:
                            raise ValueError(
                                "Model %s does not have attribute %s" % (
                                    instance.__class__, match.strip()))

            # Final value
            result[item] = seo_item

    except SeoMetadata.DoesNotExist:
        # SeoMetadata not found, fallback to general default
        result = {
            'title': get_for_lang(settings.FALLBACK_TITLE, lang_code),
            'description': get_for_lang(settings.FALLBACK_DESCRIPTION, lang_code),
        }

    return result


def update_seo(sender, instance, **kwargs):
    active_lang = get_language()

    default_titles = get_seomodel_titles(cls=sender)
    default_descriptions = get_seomodel_descriptions(cls=sender)

    for lang_code, lang_name in settings.SEO_LANGUAGES:
        activate(lang_code)
        absolute_url = instance.get_absolute_url()
        try:
            sm = SeoMetadata.objects.get(
                content_type=ContentType.objects.get_for_model(instance),
                object_id=instance.id, lang_code=lang_code)
            if absolute_url != sm.path:
                sm.path = absolute_url
        except SeoMetadata.DoesNotExist:
            default_title = get_for_lang(
                default_titles, lang_code)
            default_description = get_for_lang(
                default_descriptions, lang_code)
            sm = SeoMetadata(
                lang_code=lang_code, content_object=instance,
                path=absolute_url,
                title=default_title, description=default_description)
        sm.save()
    activate(active_lang)


def delete_seo(sender, instance, **kwargs):
    ctype = ContentType.objects.get_for_model(instance)
    for sm in SeoMetadata.objects.filter(content_type=ctype, object_id=instance.id):
        sm.delete()


def reset_seo_info(sender, instance, **kwargs):
    '''
        reset_seo :: resets the SEO information of all SeoMetadata instances
        associated in order to update a change on the default values.
        Resets instances which seo values has not been modified by the user i.e.
        they keep the previous default value.
    '''
    ctype = ContentType.objects.get_for_model(instance)
    for sm in SeoMetadata.objects.filter(
            content_type=ctype, object_id=instance.id, is_default=True):
        sm.title = get_for_lang(get_seomodel_titles(ctype.model_class()), sm.lang_code)
        sm.description = get_for_lang(get_seomodel_descriptions(ctype.model_class()), sm.lang_code)
        sm.save(update_default=False)


def register_seo_signals():
    for app, model in settings.SEO_MODELS:
        ctype = ContentType.objects.get(app_label=app, model=model)
        if not hasattr(ctype.model_class(), 'get_absolute_url'):
            raise ImproperlyConfigured("Needed get_absolute_url method not defined on %s.%s model." % (app, model))
        models.signals.post_save.connect(update_seo, sender=ctype.model_class(), weak=False)
        models.signals.pre_delete.connect(delete_seo, sender=ctype.model_class(), weak=False)
