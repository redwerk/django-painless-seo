# Django PainlessSEO

[![PyPI version](https://pypip.in/version/django-painless-seo/badge.svg?style=flat)](https://pypi.python.org/pypi/django-painless-seo)
[![PyPI downloads](https://pypip.in/download/django-painless-seo/badge.svg?style=flat)](https://pypi.python.org/pypi/django-painless-seo)

This django app provides multiple **easy ways of adding SEO metadata** to your django site:

- **Absolute URLs**
- **Parameterized URLs**
- **Model instances**
- **Per Model fallback**
- **General fallback**

Moreover, it is fully designed to work on **multilingual sites**, allowing you 
to define diferent metadata depending on the active language.

Furthermore, it's fully integrated with the admin site including inline forms for models.

## Index

0. [Index](#index)
1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Defining the SEO metadata](#defining-the-seo-metadata)
  1. [Absolute URLs](#absolute-urls)
  2. [Parameterized URLs](#parameterized-urls)
  3. [Model Instances](#model-instances)
  4. [Per Model Default](#per-model-default)
  5. [General Fallbacks](#general-fallbacks)
4. [SEO Output](#seo-output)
5. [Notes](#notes)
6. [Legal Stuff](#legal-stuff)

## Requirements

    Django >= 1.5.0

## Installation

1. Clone the git repository.
    $> git clone https://github.com/Glamping-Hub/django-painless-seo.git

2. Place the *painlessseo* package included in the distribution on the *PYTHONPATH*. 

3. Add 'painlessseo' to the INSTALLED_APPS in your settings.py.

4. Add configuration variables on your *settings.py* as defined in sections [3.4](#per-model-default) and [3.5](#general-fallbacks)

5. Run *syncdb* command to syncronize your database.
    $> python ./manage.py syncdb

6. Run *sync_seo_models* command to initialize the registered models.
    $> python ./manage.py sync_seo_models

Congratulaions ! You have successfully installed 'painlessseo' on your django project !

## Defining the SEO metadata

Once you have your application installed, you need to define your SEO content. In order to make this task as easy as possible, painlessseo allows you to define your SEO metadata in 5 different ways

### Absolute URLs

The easiest way to define the SEO info to be included in your app is by creating a new instance of SeoMetadata model and define the absolute URL that will trigger such information, together with the associated language. This can be easily done through the django admin site, just by including 'painlessseo.seometadata' model in your admin.

### Parameterized URLs 

However, as soon as your project start growing, you will problably find this way a little bit tiring. In many cases, you will find yourself creating many similar SeoMetadata instances when you need to define SEO content that fits for different URLs. 

For that reason, painlessseo allows you to define SEOMetadata instances with parameterized paths, just by setting its has_parameters attribute to True:
    
    /blog/articles/{0}

This SEO metadata will trigger for URLs like '/blog/articles/how-awesome-is-painlessseo' or '/blog/articles/yet-another-article', given that there is no absolute URL match for these URLs. 

The parameter wildcard takes the form of '{Y}' where 'Y' is a positive number that must appear in order, and matches alphanumerical characters together with the dash symbol '-'.
Furthermore, you can use the information captured and include it in the SEO content of your SeoMetadata instance, again by including the {Y} wildcard.

### Model Instances

Well, that's pretty amazing isn't it? And just by writting a few lines, but ... what would happen if you need to change your URL structure but still want to have SeoMetadata associated  with your articles? 

For that reason, painlessseo also allows you to associate a SEOMetadata instance with any model instance of your app. This way, you can have the url of the metadata instance synced with the URL obtained through the 'get_absolute_url' method of your model instance, and this is done for all the declared languages. 

Moreover, as with the parameters explained in section [3.3](#parameterized-urls), you can include wildcards on your SEO metadata, but now accessing the attributes of the instance. This way, you could have something like:

    title = "{name} by {author.username}"

Which will output 
    
    "How Awesome Is Painlessseo by Painlessseo"

Given that the article model has a field named "name" and a foreign key named "author" with an attribute "username". Furthermore, painlessseo will first try to obtain the language dependant field, for example 'name_en' or 'name_es', before fallbacking to the generic 'name' field.

In order to activate the synchronization for model instances you have to define first the
`SEO_MODELS` variable in your *settings.py* like this:

    SEO_MODELS = (
        ('myapp', 'mymodel'),
        ('anotherapp', 'anothermodel'),
    )

And then call the command:
    
    sync_seo_models :: initializes the seo metadata info for registered models
        and initializes its with the default value for each of the languages 
        declared in settings.

    $> python ./manage.py sync_seo_models

In order to allow your admin users to modify such information, you can add the inline form to the admin instance for the model:

    from painlessseo.admin import SeoMetadataInline

    class MyModelAdmin(admin.ModelAdmin):
        inlines = [SeoMetadataInline, ]

Now every time you save a model instance, the SEO metadata will be updated automatically.

### Per Model Default

Furthermore, in case you don't want to define a different SEO Content for each of the istances of a registered model, you can also declare DEFAULT_SEO_TITLES and DEFAULT_SEO_DESCRIPTIONS variables at model level, which will override the generic fallbacks for URLs related to instances of this particular model. This 'relationship' is stablished by calling the *"get_object"* method of the django view; If your are using a DetailView, that method will be already declared, if not, you need to declare it yourself.
    
    class MyModel(models.Model):
        DEFAULT_SEO_TITLES = { 
            'en': 'Lorem ipsum model title english',
            'es': 'Lorem ipsum model title español',
        }
        DEFAULT_SEO_DESCRIPTIONS = { 
            'en': 'Lorem ipsum model description english',
            'es': 'Lorem ipsum model description español',
        }

However, this value its only registered when calling the 'sync_seo_models' command for the first time on a particular model; After that, you can change this content through the admin site on SEORegisteredModel panel.

As with the instance-related SEO metadata, the content declared as fallbacks for DetailViews can also content references to attributes of the instance by surounding the name of the property by '{}'.

In order to avoid having duplicated titles on different pages related with instances of same model, painlessseo allows you to create a bunch of Metadescriptions that will be assigned for each instance depending on its 'id' or 'pk' attributes. Doing that is as simple as creating multiple SeoRegisteredModel instanes through the admin for the same model and language. When an instance requires this information, its 'id' or 'pk' attributes will be used to select the correct one (selected = id % total).

### General Fallbacks

Well ... everything is pretty amazing, and really easy to implement ... but what happens if I forget to include a SEOMetadata instance for a particular URL? Will I get a page without any SEO information? Not at all. 
PainlessSEO uses two configuration variables on your *settings.py* so that you can define the default information that will be displayed if an URL has no matching SEO Metadata instance:

    DEFAULT_SEO_TITLES = { 
        'en': 'Lorem ipsum title english',
        'es': 'Lorem ipsum title español',
        ...
    }
    DEFAULT_SEO_DESCRIPTIONS = { 
        'en': 'Lorem ipsum description english',
        'es': 'Lorem ipsum description español',
        ...
    }

As with the Model based default titles and descriptions, these variables can be defined either as a character string (default for all languages) or as a dict (with a different value depending on the language)

## SEO Output

Outputting the SEO info is as simple as loading the `seo` template library and using the `get_seo`
template tag like this:

    {% load seo %}

    <head>
        {% get_seo %}
    </head>

In order to ensure compilance with google SEO best practices, both title and description content will be truncated at 65 and 165 characters respectively, even if your content is longer.

## Notes

[Why PainlessSEO does not include keywords meta tag](http://googlewebmastercentral.blogspot.in/2009/09/google-does-not-use-keywords-meta-tag.html).

## Legal Stuff

This software is licensed under the terms of the BSD 3-clause license. You can
find the whole text of the license in the LICENSE file.
