# Copyright (C) 2014 Glamping Hub (https://glampinghub.com)
# License: BSD 3-Clause

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import pre_save


from painlessseo import settings


class SeoRegisteredModel(models.Model):
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    lang_code = models.CharField(verbose_name=_('Language'), max_length=2,
                                 choices=settings.SEO_LANGUAGES,
                                 default=settings.DEFAULT_LANG_CODE)

    # SEO Info
    title = models.CharField(verbose_name=_('Title'), max_length=100, blank=True, null=True)
    description = models.CharField(verbose_name=_('Description'), max_length=200, blank=True, null=True)

    class Meta:
        verbose_name = _('SEO Model')
        verbose_name_plural = _('SEO Models')


class SeoMetadata(models.Model):
    content_type = models.ForeignKey(ContentType, null=True, blank=True, verbose_name=_('Model'))
    object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Id'))
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    lang_code = models.CharField(verbose_name=_('Language'), max_length=2,
                                 choices=settings.SEO_LANGUAGES,
                                 default=settings.DEFAULT_LANG_CODE)
    has_parameters = models.BooleanField(
        default=False,
        help_text=_(u"This indicates if the SEOMetadata path contains parameters."))
    path = models.CharField(verbose_name=_('Path'), max_length=200, db_index=True,
                            null=True, blank=False,
                            help_text=_("This should be an absolute path, excluding the domain name. Example: '/foo/bar/'. You can also capture parameters using '{X}' notation, where X is a positive number."))

    # SEO Info
    title = models.CharField(
        verbose_name=_('Title'), max_length=100, blank=False, null=True,
        help_text=_("Here you can make use of the parameters captured in the URL using the same '{X}' notation."))
    description = models.CharField(
        verbose_name=_('Description'), max_length=200, blank=False, null=True,
        help_text=_("Here you can make use of the parameters captured in the URL using the same '{X}' notation."))

    class Meta:
        verbose_name = _('SEO Path Metadata')
        verbose_name_plural = _('SEO Path Metadata')
        ordering = ('path', 'lang_code')

    def __unicode__(self):
        return "Language: %s | URL: %s" % (self.lang_code, self.path)

    def get_metadata(self):
        result = {}
        for item in settings.SEO_FIELDS:
            result[item] = getattr(self, item)
        return result
