from django.template.loader import render_to_string
from inspect import isdatadescriptor
from django import forms

class ResourceForm(forms.Form):
    def __init__(self, *args, **kwargs):
        extra = kwargs.pop('extra')
        super(ResourceForm, self).__init__(*args, **kwargs)

        for i, values in enumerate(extra):
            label = values['label']
            name = values['name']
            help_text = values['help_text']
            self.fields[name] = forms.CharField(label=label, help_text=help_text)

    def extra_fields(self, fields):
        for name, value in self.cleaned_data.items():
            if name in fields:
                yield (name, value)

class Field(object):
    def __init__(self, default=None, label=None, help_text = None):
        self.value = default
        self.label = label
        self.help_text = help_text

    def __get__(self, obj, obj_type):
        if obj is None:
            return self
        return self.value

    def __set__(self, obj, value):
        self.value = value


class ResourceRenderer(object):
    def __init__(self, resource):
        self.resource = resource
        self.module = RESOURCE_MODULES[self.resource.resource_type](self.resource)

    def render(self):
        return self.module.render()

    def create_form(self):
        return self.module.create_form()

    def save_form_values(self, request):
        self.module.save_form_values(request)

    def get_module_data(self):
        return self.module.get_data()

class ResourceModule(object):
    resource_template = "resources/resource.html"

    def __init__(self, resource):
        self.resource = resource
        self.data = resource.data
        self.fields = [attr for attr in dir(self.__class__) if not attr.startswith("__") and isdatadescriptor(getattr(self.__class__, attr))]
        self.read_data()
        self.form_field_dictionaries = []
        for field in self.fields:
            class_field = getattr(self.__class__, field)
            self.form_field_dictionaries.append({
                'label': class_field.label,
                'help_text': class_field.help_text,
                'name': field
            })


    def render(self):
        return render_to_string(self.resource_template, {
            'content': self.render_module()
        })

    def render_module(self):
        raise NotImplementedError

    def store_data(self):
        self.data = {}
        for field in self.fields:
            self.data.update({field: getattr(self, field)})

    def read_data(self):
        for field in self.fields:
            setattr(self, field, self.data.get(field))

    def create_form(self):
        form = ResourceForm(extra=self.form_field_dictionaries)
        return render_to_string("resources/form.html", {
            'form': form,
            'action_link': self.resource.link,
            'form_id': "resource-{0}".format(self.resource.id)
        })

    def save_form_values(self, request):
        form = ResourceForm(request.POST, extra=self.form_field_dictionaries)
        if form.is_valid():
            for (name, value) in form.extra_fields(self.fields):
                setattr(self, name, value)

    def get_data(self):
        self.store_data()
        return self.data


class HTMLModule(ResourceModule):
    html = Field(
        default="",
        label="Post text",
        help_text="The text of your post.  You can use HTML."
    )
    template = "resources/html_module.html"

    def render_module(self):
        self.module_html = render_to_string(self.template, {
            'html': self.html
        })


class LinkModule(ResourceModule):
    link = Field(
        default="",
        label="URL",
        help_text="The link to your resource."
    )
    template = "resources/link_module.html"

    def render_module(self):
        self.module_html = render_to_string(self.template, {
            'link': self.link
        })

RESOURCE_MODULES = {
    'html': HTMLModule,
    'link': LinkModule
}