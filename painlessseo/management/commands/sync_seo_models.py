"""
sync_seo_models.py

    Goes through all the registered models syncing the seo information.

"""
from optparse import make_option

from django.core.management.base import NoArgsCommand, CommandError
from django.core.urlresolvers import resolve, Resolver404
from django.contrib.contenttypes.models import ContentType

from painlessseo import settings
from painlessseo.utils import (
    delete_seo, update_seo, get_fallback_metadata
    )
from painlessseo.models import SeoRegisteredModel
import hashlib

DEFAULT_CREATE_LANG = []
DEFAULT_SEO_MODELS = settings.SEO_MODELS


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--langs', dest='update_langs', default=DEFAULT_CREATE_LANG,
                    help='Use this to indicate which languages must be generated'),
        make_option('--models', dest='seo_models', default=DEFAULT_SEO_MODELS,
                    help='Use this to indicate which apps must be updated'),
        make_option('--sync-instances', dest='sync_instances', default=False,
                    help='Use this to indicate if instances must be synced'),

    )
    help = '''DEBUG only: Sync the SEO info in the database for registered models. '''
    requires_model_validation = True

    def handle_noargs(self, **options):
        seo_models = options.get('seo_models')
        if isinstance(seo_models, str):
            models = seo_models.split(' ')
            seo_models = []
            for model in models:
                seo_models.append(model.split('.'))

        update_langs = options.get('update_langs')
        if isinstance(update_langs, str):
            langs = update_langs.split(' ')
            update_langs = []
            for lang in langs:
                update_langs.append(lang)
        languages = settings.SEO_LANGUAGES

        for app, model in seo_models:
            ctype = ContentType.objects.get(app_label=app.lower(), model=model.lower())
            if not hasattr(ctype.model_class(), 'get_absolute_url'):
                raise ImproperlyConfigured("Needed get_absolute_url method not defined on %s.%s model." % (app, model))
            model_class = ctype.model_class()

            print("Registering %s model in app %s") % (model, app)
            for lang_code, language in languages:
                model_metadata = get_hardcoded_metadata(model_class, lang_code)
                titles = model_metadata['titles']
                descriptions = model_metadata['descriptions']
                max_len = max(len(titles), len(descriptions))
                for index in range(0, max_len):
                    title = titles[index % len(titles)]
                    desc = descriptions[index % len(descriptions)]
                    seorm, created = SeoRegisteredModel.objects.get_or_create(
                        content_type=ctype,
                        lang_code=lang_code,
                        title=title,
                        description=desc,
                        )
                    if created:
                        print("   - Lang '%s' updated.") % (lang_code)

            if options.get('sync_instances'):
                print("Updating %s instances in app %s") % (model, app)
                objs = list(model_class.objects.all())
                for obj in objs:
                    update_seo(model_class, obj, auto_languages=update_langs, weak=True)
                count = model_class.objects.count()
                print("%d %s updated on app %s") % (count, model, app)


def get_hardcoded_metadata(cls, lang_code):
    result = {}
    if hasattr(cls, 'DEFAULT_SEO_TITLES'):
        titles = getattr(cls, 'DEFAULT_SEO_TITLES')
        if isinstance(titles, dict):
            if lang_code in titles:
                titles = titles[lang_code]
            else:
                titles = titles[settings.DEFAULT_LANG_CODE]

            if not isinstance(titles, list):
                titles = [titles]

        result['titles'] = titles

    if hasattr(cls, 'DEFAULT_SEO_DESCRIPTIONS'):
        descs = getattr(cls, 'DEFAULT_SEO_DESCRIPTIONS')
        if isinstance(descs, dict):
            if lang_code in descs:
                descs = descs[lang_code]
            else:
                descs = descs[settings.DEFAULT_LANG_CODE]

            if not isinstance(descs, list):
                descs = [descs]

        result['descriptions'] = descs

    return result
