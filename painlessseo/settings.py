# Copyright (C) 2014 Glamping Hub (https://glampinghub.com)
# License: BSD 3-Clause

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

DEFAULT_LANG_CODE = getattr(settings, 'LANGUAGE_CODE', 'en')[:2]

FALLBACK_TITLE = getattr(settings, 'SEO_DEFAULT_TITLES', None)
if isinstance(FALLBACK_TITLE, str):
    FALLBACK_TITLE = {
        DEFAULT_LANG_CODE: FALLBACK_TITLE,
    }

FALLBACK_DESCRIPTION = getattr(settings, 'SEO_DEFAULT_DESCRIPTIONS', None)
if isinstance(FALLBACK_DESCRIPTION, str):
    FALLBACK_DESCRIPTION = {
        DEFAULT_LANG_CODE: FALLBACK_DESCRIPTION,
    }

if FALLBACK_TITLE is None:
    raise ImproperlyConfigured('SEO_DEFAULT_TITLES is not defined in settings.')

if FALLBACK_DESCRIPTION is None:
    raise ImproperlyConfigured('SEO_DEFAULT_DESCRIPTIONS is not defined in settings.')

I18N = getattr(settings, 'USE_I18N')

if I18N:
    SEO_LANGUAGES = getattr(settings, 'LANGUAGES', None)
    if not SEO_LANGUAGES:
        raise ImproperlyConfigured('If USE_I18N is set to True, you need to define LANGUAGES in settings.')
else:
    SEO_LANGUAGES = ((DEFAULT_LANG_CODE, DEFAULT_LANG_CODE), )

SEO_MODELS = getattr(settings, 'SEO_MODELS', [])
