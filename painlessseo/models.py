# Copyright (C) 2014 Glamping Hub (https://glampinghub.com)
# License: BSD 3-Clause

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import pre_save


from painlessseo import settings


SEO_FIELDS = ['title', 'description']


class SeoMetadata(models.Model):
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    path = models.CharField(verbose_name=_('Path'), max_length=200, db_index=True,
                            help_text=_("This should be an absolute path, excluding the domain name. Example: '/foo/bar/'."))
    lang_code = models.CharField(verbose_name=_('Language'), max_length=2,
                                 choices=settings.SEO_LANGUAGES,
                                 default=settings.DEFAULT_LANG_CODE)
    is_default = models.BooleanField(
        default=True,
        help_text=_(u"This indicates if any seo info has been modified from the default one."),
        )

    # SEO Info
    title = models.CharField(verbose_name=_('Title'), max_length=65, blank=True)
    description = models.CharField(verbose_name=_('Description'), max_length=155, blank=True)

    # This way we can update the "is_default" field when any of the seo items
    # has been modified
    def __init__(self, *args, **kwargs):
        super(SeoMetadata, self).__init__(*args, **kwargs)
        for seo_item in SEO_FIELDS:
            setattr(self, '__' + seo_item, getattr(self, seo_item))

    def save(self, force_insert=False, force_update=False, update_default=True, *args, **kwargs):
        if update_default:
            for seo_item in SEO_FIELDS:
                if getattr(self, seo_item) != getattr(self, '__' + seo_item):
                    # SEO item has changed
                    self.is_default = False

        super(SeoMetadata, self).save(force_insert, force_update, *args, **kwargs)
        for seo_item in SEO_FIELDS:
            setattr(self, '__' + seo_item, getattr(self, seo_item))

    class Meta:
        verbose_name = _('SEO metadata')
        verbose_name_plural = _('SEO metadata')
        db_table = 'seo_metadata'
        unique_together = (('path', 'lang_code'), )
        ordering = ('path', 'lang_code')

    def __unicode__(self):
        return "Language: %s | URL: %s" % (self.lang_code, self.path)
