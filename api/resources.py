from django.template.loader import render_to_string
from inspect import isdatadescriptor
from django import forms
from django.templatetags.static import static
from django.template import RequestContext
import json
import logging

log = logging.getLogger(__name__)

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
    def __init__(self, default=None, label=None, help_text=None, scope=None, editable=False):
        if getattr(self, 'value', None) is None:
            self.value = default
        self.label = label
        self.help_text = help_text
        self.scope = scope
        self.default = default
        self.editable = editable

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

class ListField(Field):
    def __init__(self, **kwargs):
        super(ListField, self).__init__(**kwargs)
        if self.default is None:
            self.default = []
        if self.value is None:
            self.value = self.default

    def append(self, item):
        self.value.append(item)

    def __iter__(self):
        for val in self.value:
            yield val

    def __getitem__(self, k):
        return self.value[k]

    def __len__(self):
        return len(self.value)

class DictField(Field):
    def __init__(self, **kwargs):
        super(DictField, self).__init__(**kwargs)
        if self.default is None:
            self.default = {}
        if self.value is None:
            self.value = self.default

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
    user_template = "resources/user_view.html"
    author_template = "resources/author_view.html"

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
        return render_to_string(self.user_template, {
            'content': response,
            'resource_id': self.resource.id
            })

    def author_view(self):
        response = self.module.author_view()
        return render_to_string(self.author_template, {
            'content': response
        })

    def handle_ajax(self, action, post_data):
        post_data = json.loads(post_data)
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

    resource_author_template = "resources/author.html"
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
            if class_field.scope == ResourceScope.author and class_field.editable == True:
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
        resource_html.add_html(render_to_string(self.resource_author_template, {'content': self.render_module_author()}))
        for js in self.author_js:
            resource_html.add_js(js)
        for css in self.author_css:
            resource_html.add_css(css)
        return resource_html.get_html()

    def handle_ajax(self, action, post_data):
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

    def save_form_values(self, post_data):
        form = ResourceForm(post_data, extra=self.form_field_dictionaries)
        if form.is_valid():
            for (name, value) in form.extra_fields(self.fields):
                setattr(self, name, value)

    def handle_ajax(self, action, post_data):
        actions = {
            'save_form_values': self.save_form_values
        }

        return actions[action](post_data)

class HTMLModule(SimpleAuthoringMixin, ResourceModule):
    html = Field(
        default="",
        label="Post text",
        help_text="The text of your post.  You can use HTML.",
        scope=ResourceScope.author,
        editable=True
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
        scope=ResourceScope.author,
        editable=True
    )
    template = "resources/link_module.html"

    def render_module(self):
        return render_to_string(self.template, {
            'link': self.link
        })

class MultipleChoiceProblemModule(ResourceModule):
    """
    The options data structure is a list of lists.
    So: [[text, correct], [text, correct]], like [["The sun is yellow", True], ["The sun is blue", False]].
    """
    options = ListField(
        default=None,
        label="Multiple choice options",
        help_text="Options for this multiple choice problem.",
        scope=ResourceScope.author
    )
    question = Field(
        default=None,
        label="Question",
        help_text="The question for this problem.",
        scope=ResourceScope.author,
        editable=True
    )
    maximum_attempts = Field(
        default=1,
        label="Maximum attempts",
        help_text="Maximum number of attempts allowed.",
        scope=ResourceScope.author,
        editable=True
    )
    attempts = Field(
        default=0,
        label="Student attempts",
        help_text="Number of attempts the student has taken.",
        scope=ResourceScope.user
    )
    answers = ListField(
        default=None,
        label = "Student answers",
        help_text="List of which answer the student selected on each attempt.",
        scope=ResourceScope.user
    )

    template = "resources/multiple_choice_module.html"
    author_template = "resources/multiple_choice_author.html"
    author_css = ["css/resource/multiple_choice.css"]
    author_js = ["js/resource/multiple_choice_author.js"]
    css = ["css/resource/multiple_choice.css"]
    js = ["js/resource/multiple_choice_module.js"]

    def save_form_values(self, post_data):
        self.maximum_attempts = int(post_data['maximum_attempts'])
        options = {int(k.replace('option', '')): post_data[k] for k in post_data if k.startswith('option')}

        keys = options.keys()
        keys.sort()

        self.options = []
        for o in keys:
            self.options.append([options[o], o == int(post_data['correct'])])

        return {'success': True}

    def find_correct(self, response):
        return self.options[int(response)][1]

    def correct_answer(self):
        for (i,o) in enumerate(self.options):
            if o[1] == True:
                return i

    def handle_ajax(self, action, post_data):
        ajax_handlers = {
            'save_answer': self.save_answer,
            'try_again': self.try_again,
            'save_form_values': self.save_form_values
        }

        return json.dumps(ajax_handlers[action](post_data))

    def save_answer(self, post_data):
        self.answers.append(post_data['answer'])
        self.attempts += 1
        return {'correct': self.find_correct(post_data['answer'])}

    def allow_retry(self):
        allow_retry = False
        if self.attempts < self.maximum_attempts:
            allow_retry = True
        return allow_retry

    def try_again(self):
        return {'allow_retry': self.allow_retry()}

    def render_module(self):
        previous_answer = None
        if len(self.answers) > 0:
            previous_answer = int(self.answers[-1])

        return render_to_string(self.template, {
            'options': [o[0] for o in self.options],
            'question': self.question,
            'previous_answer': previous_answer,
            'allow_retry': self.allow_retry(),
            'correct_answer': self.correct_answer()
        })

    def render_module_author(self):
        form = ResourceForm(extra=self.form_field_dictionaries)
        return render_to_string(self.author_template, {
            'form': form,
            'action_link': self.static_data.get('author_post_link'),
            'form_id': "resource-creation-form",
            }, context_instance=RequestContext(self.static_data.get('request')))

RESOURCE_MODULES = {
    'html': HTMLModule,
    'link': LinkModule,
    'multiplechoice': MultipleChoiceProblemModule
}