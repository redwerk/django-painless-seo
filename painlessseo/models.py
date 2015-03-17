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
    title = models.CharField(verbose_name=_('Title'), max_length=65, blank=True, null=True)
    description = models.CharField(verbose_name=_('Description'), max_length=155, blank=True, null=True)

    class Meta:
        verbose_name = _('SEO Model')
        verbose_name_plural = _('SEO Models')


class SeoMetadata(models.Model):
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    lang_code = models.CharField(verbose_name=_('Language'), max_length=2,
                                 choices=settings.SEO_LANGUAGES,
                                 default=settings.DEFAULT_LANG_CODE)
    path = models.CharField(verbose_name=_('Path'), max_length=200, db_index=True,
                            null=True, blank=False,
                            help_text=_("This should be an absolute path, excluding the domain name. Example: '/foo/bar/'."))

    # SEO Info
    title = models.CharField(
        verbose_name=_('Title'), max_length=65, blank=False, null=True)
    description = models.CharField(
        verbose_name=_('Description'), max_length=155, blank=False, null=True)

    class Meta:
        verbose_name = _('SEO Path Metadata')
        verbose_name_plural = _('SEO Path Metadata')
        unique_together = (('path', 'lang_code'), )
        ordering = ('path', 'lang_code')

    def __unicode__(self):
        return "Language: %s | URL: %s" % (self.lang_code, self.path)

    def get_metadata(self):
        result = {}
        for item in settings.SEO_FIELDS:
            result[item] = getattr(self, item)
        return result
