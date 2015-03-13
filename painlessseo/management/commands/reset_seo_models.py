"""
sync_seo_models.py

    Goes through all the registered models syncing the seo information.

"""
from optparse import make_option

from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError
from django.core.urlresolvers import resolve, Resolver404
from django.contrib.contenttypes.models import ContentType

from painlessseo.utils import reset_seo_info


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list
    help = '''DEBUG only: Reset the SEO info in the database for registered models. '''
    requires_model_validation = True

    def handle_noargs(self, **options):
        seo_models = settings.SEO_MODELS
        for app, model in seo_models:
            print("Reseting %s models in app %s") % (model, app)
            ctype = ContentType.objects.get(app_label=app, model=model)
            if not hasattr(ctype.model_class(), 'get_absolute_url'):
                raise ImproperlyConfigured("Needed get_absolute_url method not defined on %s.%s model." % (app, model))
            model_class = ctype.model_class()
            for obj in model_class.objects.all():
                reset_seo_info(model_class, obj, weak=True)
            count = model_class.objects.count()
            print("%d %s reseted on app %s") % (count, model, app)
