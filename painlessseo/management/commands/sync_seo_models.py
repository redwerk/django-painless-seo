"""
sync_seo_models.py

    Goes through all the registered models syncing the seo information.

"""
from optparse import make_option

from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError
from django.core.urlresolvers import resolve, Resolver404
from django.contrib.contenttypes.models import ContentType

from painlessseo.utils import delete_seo, update_seo


DEFAULT_REMOVE_404 = False


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--remove-404', dest='remove_404', default=DEFAULT_REMOVE_404,
                    help='Use this to indicate if old urls that return 404 must be removed'),

    )
    help = '''DEBUG only: Sync the SEO info in the database for registered models. '''
    requires_model_validation = True

    def handle_noargs(self, **options):
        seo_models = settings.SEO_MODELS
        for app, model in seo_models:
            print("Updating %s models in app %s") % (model, app)
            ctype = ContentType.objects.get(app_label=app, model=model)
            if not hasattr(ctype.model_class(), 'get_absolute_url'):
                raise ImproperlyConfigured("Needed get_absolute_url method not defined on %s.%s model." % (app, model))
            model_class = ctype.model_class()
            for obj in model_class.objects.all():
                update_seo(model_class, obj, weak=True)
            count = model_class.objects.count()
            print("%d %s updated on app %s") % (count, model, app)

        # try:
        #     resolve(obj.get_absolute_url())
        # except Resolver404:
        #     if options.get('remove_404', DEFAULT_REMOVE_404):
        #         delete_seo(model_class, obj, weak=True)
        #     else:
        #         update_seo(model_class, obj, weak=True)
