from django.template.loader import render_to_string
from inspect import isdatadescriptor
from django import forms
from django.templatetags.static import static
from django.template import RequestContext
import json

class ResourceScope(object):
    user = "user"
    author = "author"

class ResourceForm(forms.Form):
    name = forms.CharField(label="Resource Name", help_text="The name for this resource.")

    def __init__(self, *args, **kwargs):
        extra = kwargs.pop('extra')
        super(ResourceForm, self).__init__(*args, **kwargs)

        for i, values in enumerate(extra):
            label = values['label']
            name = values['name']
            help_text = values['help_text']
            value = values['value']
            self.fields[name] = forms.CharField(label=label, help_text=help_text, initial=value)

    def extra_fields(self, fields):
        for name, value in self.cleaned_data.items():
            if name in fields:
                yield (name, value)

class Field(object):
    def __init__(self, default=None, label=None, help_text=None, scope=None):
        if getattr(self, 'value', None) is None:
            self.value = default
        self.label = label
        self.help_text = help_text
        self.scope = scope
        self.default = default

    def __get__(self, obj, obj_type):
        if obj is None:
            return self
        return self.from_json(self.value)

    def __set__(self, obj, value):
        self.value = self.to_json(value)

    @classmethod
    def from_json(cls, value):
        return value

    @classmethod
    def to_json(cls, value):
        return value

class ResourceHTML(object):
    css_template = "<link rel='stylesheet' href='{0}'>"
    js_template = "<script src='{0}'></script>"

    def __init__(self):
        self.html = ""
        self.js = []
        self.css = []

    def add_html(self, html):
        self.html = self.html + html

    def add_js(self, js):
        if js.startswith('http'):
            self.js.append(js)
        else:
            self.js.append(static(js))

    def add_css(self, css):
        if css.startswith('http'):
            self.css.append(css.replace('http:', '').replace('https:', ''))
        else:
            self.css.append(static(css))

    def get_html(self):
        js_text = "".join([self.js_template.format(js) for js in self.js])
        css_text = "".join([self.css_template.format(css) for css in self.css])

        return js_text + css_text + self.html

class ResourceRenderer(object):
    def __init__(self, resource, user_resource_state=None, static_data=None):
        self.resource = resource
        self.user_resource_state = user_resource_state

        try:
            resource_data = json.loads(self.resource.data)
        except (ValueError, TypeError):
            resource_data = {}

        if user_resource_state is not None:
            try:
                user_data = json.loads(self.user_resource_state.data)
            except (ValueError, TypeError):
                user_data = {}
        else:
            user_data = {}

        if static_data is None:
            static_data = {}

        self.module = RESOURCE_MODULES[self.resource.resource_type](
            resource_data,
            user_data,
            static_data,
        )

    def user_view(self):
        response = self.module.user_view()
        self.save_module_data()
        return response

    def author_view(self):
        response = self.module.author_view()
        return response

    def handle_ajax(self, action, post_data):
        response = self.module.handle_ajax(action, post_data)
        self.save_module_data()
        return response

    def save_module_data(self):
        data = self.module.get_data()

        self.resource.data = json.dumps(data[ResourceScope.author])
        self.resource.save()

        if self.user_resource_state is not None:
            if ResourceScope.user in data:
                self.user_resource_state.data = json.dumps(data[ResourceScope.user])
            else:
                self.user_resource_state.data = json.dumps({})
            self.user_resource_state.save()

class ResourceModule(object):
    resource_template = "resources/resource.html"
    js = []
    css = []

    author_template = "resources/author.html"
    author_js = []
    author_css = []

    def __init__(self, resource_data, user_data, static_data):

        # Set data from various scopes.
        self.static_data = static_data
        self.data = {
            ResourceScope.author: resource_data,
            ResourceScope.user: user_data,
        }

        self.fields = [attr for attr in dir(self.__class__) if not attr.startswith("__") and isinstance(getattr(self.__class__, attr), Field)]
        self.read_data()
        self.form_field_dictionaries = []
        for field in self.fields:
            class_field = getattr(self.__class__, field)
            self.form_field_dictionaries.append({
                'label': class_field.label,
                'help_text': class_field.help_text,
                'name': field,
                'value': getattr(self, field)
            })

    def user_view(self):
        resource_html = ResourceHTML()
        resource_html.add_html(render_to_string(self.resource_template, {'content': self.render_module()}))
        for js in self.js:
            resource_html.add_js(js)
        for css in self.css:
            resource_html.add_css(css)
        return resource_html.get_html()

    def render_module(self):
        raise NotImplementedError

    def get_scope(self, field):
        class_field = getattr(self.__class__, field)
        scope = class_field.scope
        return class_field, scope

    def store_data(self):
        self.data = {}
        for field in self.fields:
            class_field, scope = self.get_scope(field)
            if scope not in self.data:
                self.data[scope] = {}
            self.data[scope].update({field: class_field.to_json(getattr(self, field))})

    def read_data(self):
        for field in self.fields:
            class_field, scope = self.get_scope(field)
            if scope in self.data:
                value = self.data[scope].get(field)
                if value is None:
                    value = class_field.default
                setattr(self, field, value)

    def render_module_author(self):
        raise NotImplementedError

    def author_view(self):
        resource_html = ResourceHTML()
        resource_html.add_html(render_to_string(self.author_template, {'content': self.render_module_author()}))
        for js in self.author_js:
            resource_html.add_js(js)
        for css in self.author_css:
            resource_html.add_css(css)
        return resource_html.get_html()

    def handle_ajax(self, request):
        raise NotImplementedError

    def get_data(self):
        self.store_data()
        return self.data

class SimpleAuthoringMixin(object):

    def render_module_author(self):
        form = ResourceForm(extra=self.form_field_dictionaries)
        return render_to_string("resources/form.html", {
            'form': form,
            'action_link': self.static_data.get('author_post_link'),
            'form_id': "resource-creation-form",
        }, context_instance=RequestContext(self.static_data.get('request')))

    def save_form_values(self, request):
        form = ResourceForm(request.POST, extra=self.form_field_dictionaries)
        if form.is_valid():
            for (name, value) in form.extra_fields(self.fields):
                setattr(self, name, value)

    def handle_ajax(self, request):
        action = request.POST.get('action')

        actions = {
            'save_form_values': self.save_form_values
        }

        return actions[action](request)

class HTMLModule(SimpleAuthoringMixin, ResourceModule):
    html = Field(
        default="",
        label="Post text",
        help_text="The text of your post.  You can use HTML.",
        scope=ResourceScope.author
    )
    template = "resources/html_module.html"

    def render_module(self):
        return render_to_string(self.template, {
            'html': self.html
        })


class LinkModule(SimpleAuthoringMixin, ResourceModule):
    link = Field(
        default="",
        label="URL",
        help_text="The link to your resource.",
        scope=ResourceScope.author
    )
    template = "resources/link_module.html"

    def render_module(self):
        return render_to_string(self.template, {
            'link': self.link
        })

class ProblemModule(ResourceModule):
    pass

RESOURCE_MODULES = {
    'html': HTMLModule,
    'link': LinkModule
}