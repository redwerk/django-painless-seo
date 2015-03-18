# Copyright (C) 2014 Glamping Hub (https://glampinghub.com)
# License: BSD 3-Clause

from django.contrib import admin
from django.core import exceptions
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from painlessseo.models import SeoMetadata, SeoRegisteredModel
from painlessseo.utils import register_seo_signals
from django.utils.translation import activate, get_language
from django.contrib.contenttypes.models import ContentType
from django import forms


class RegisteredSeoModelsFilter(admin.SimpleListFilter):
    title = 'Model'
    parameter_name = 'model'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """

        res = []
        models = SeoRegisteredModel.objects.values(
            'content_type__id', 'content_type__name').distinct()
        for seomodel in list(models):
            res.append((seomodel['content_type__id'], seomodel['content_type__name']))
        return res

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(content_type_id=self.value())
        else:
            return queryset.all()


class SeoMetadataInlineFormSet(generic.BaseGenericInlineFormSet):
    def clean(self):
        for form in self.forms:
            if form.cleaned_data:
                data = form.cleaned_data
                instance = self.instance
                if not data["id"]:
                    # It is a creation, so check for existance
                    ctype = ContentType.objects.get_for_model(instance)
                    equal_lang = SeoMetadata.objects.filter(
                        content_type=ctype,
                        object_id=instance.id,
                        lang_code=data["lang_code"],)

                    if equal_lang.exists():
                        raise exceptions.ValidationError(
                            'Already exists a SEO Metadata for this object and language %s.' % lang_code)

                # Compute path and update if neccessary
                active_language = get_language()
                activate(data["lang_code"])
                path = instance.get_absolute_url()
                form.cleaned_data['path'] = path
                activate(active_language)

        return super(SeoMetadataInlineFormSet, self).clean()


class SeoMetadataInline(generic.GenericTabularInline):
    extra = 1
    model = SeoMetadata
    readonly_fields = ('path',)
    formset = SeoMetadataInlineFormSet


class SeoRegisteredModelAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'lang_code', 'title', 'description')
    list_filter = ('lang_code', RegisteredSeoModelsFilter)
    search_fields = ['title', 'description', ]


class AddSeoMetadataForm(forms.ModelForm):

    class Meta:
        model = SeoMetadata
        exclude = ('content_type', 'object_id', )


class SeoMetadataAdmin(admin.ModelAdmin):
    add_form = AddSeoMetadataForm
    list_display = ('path', 'lang_code', 'has_parameters')
    search_fields = ['path', ]
    list_filter = ('lang_code', 'has_parameters', )

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during user creation
        """
        defaults = {}
        if obj is None:
            defaults.update({
                'form': self.add_form,
            })
        defaults.update(kwargs)
        return super(SeoMetadataAdmin, self).get_form(request, obj, **defaults)


admin.site.register(SeoRegisteredModel, SeoRegisteredModelAdmin)
admin.site.register(SeoMetadata, SeoMetadataAdmin)

register_seo_signals()
