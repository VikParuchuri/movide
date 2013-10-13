from __future__ import unicode_literals
from django.template.loader import render_to_string
from inspect import isdatadescriptor
from django import forms
from django.templatetags.static import static
from django.template import RequestContext
import json
import logging
from models import UserResourceState
from django.utils.html import mark_safe
from permissions import ClassGroupPermissions
from fs.s3fs import S3FS
from django.conf import settings
from boto.s3.connection import S3Connection
from boto.s3.bucket import Bucket
from django.core.files.uploadedfile import UploadedFile
from redactor.widgets import RedactorEditor
import time
from datetime import datetime
from django.core.urlresolvers import reverse
from urlparse import urlparse
import re
from copy import deepcopy
from uploads import upload_to_s3, get_temporary_s3_url

log = logging.getLogger(__name__)

class RichEditor(RedactorEditor):
    init_js = """<script type="text/javascript">
      jQuery(document).ready(function(){{
        var resource_modal =  $(".view-a-resource-modal");
        if(resource_modal.length > 0){{
            resource_modal = resource_modal[0];
            try{{
                is_open = $(resource_modal).data()['bs.modal'].isShown;
            }} catch(err){{
                is_open = false;
            }}
            $("#{id}").data('redactor-options', {options});
            $("#{id}").addClass('redactor-enabled');
            if(is_open == true){{
                $("#{id}").redactor({options});
            }} else {{
                $(".view-a-resource-modal").one('shown.bs.modal', function () {{
                    $("#{id}").redactor({options});
                }});
            }}
        }}
      }});
    </script>
    """

    class Media(RedactorEditor.Media):
        extend = False
        js = (
            'redactor/jquery-migrate.min.js',
            'redactor/redactor.min.js',
        )
        css = {
            'all': (
                'redactor/css/redactor.css',
            )
        }

    def __init__(self, *args, **kwargs):
        self.upload_to = kwargs.pop('upload_to', '')
        self.custom_options = kwargs.pop('redactor_options', {})
        self.allow_file_upload = kwargs.pop('allow_file_upload', True)
        self.allow_image_upload = kwargs.pop('allow_image_upload', True)
        self.class_name = kwargs.pop('class_name')
        super(RedactorEditor, self).__init__(*args, **kwargs)

    def get_options(self):
        options = getattr(settings, 'REDACTOR_OPTIONS', {})
        options.update(self.custom_options)
        if self.allow_file_upload:
            options['fileUpload'] = reverse(
                'redactor_upload_file',
                kwargs={
                    'classgroup': self.class_name,
                    'upload_to': self.upload_to
                }
            )
        if self.allow_image_upload:
            options['imageUpload'] = reverse(
                'redactor_upload_image',
                kwargs={
                    'classgroup': self.class_name,
                    'upload_to': self.upload_to
                }
            )
        return json.dumps(options)

    def render(self, name, value, attrs=None):
        html = super(RedactorEditor, self).render(name, value, attrs)
        final_attrs = self.build_attrs(attrs)
        id_ = final_attrs.get('id')
        html += self.init_js.format(id=id_, options=self.get_options())
        return mark_safe(html)

def get_resource_score(resource, user, grading_policy):
    scores = []
    if grading_policy == "COM":
        for child in resource.children.all():
            scores.append(UserResourceState.objects.filter(user=user, resource=child).exists())
    else:
        for child in resource.children.all():
            try:
                user_resource_state = UserResourceState.objects.get(user=user, resource=child)
            except UserResourceState.DoesNotExist:
                user_resource_state = None
            renderer = ResourceRenderer(child, user_resource_state=user_resource_state, user=user)
            if hasattr(renderer.module, "get_score"):
                scores.append(renderer.module.get_score())
    return scores

class ModuleException(Exception):
    pass

class ResourceScope(object):
    user = "user"
    author = "author"

class ResourceForm(forms.Form):

    def __init__(self, *args, **kwargs):
        extra = kwargs.pop('extra')
        super(ResourceForm, self).__init__(*args, **kwargs)

        for k in extra:
            values = extra[k]
            label = values['label']
            name = values['name']
            help_text = values['help_text']
            value = values['value']
            widget = values['widget']
            widget_options = values['widget_options']
            options_dict = {
                'label': label,
                'help_text': help_text,
                'initial': value,
            }
            if widget is not None:
                if widget_options is None:
                    options_dict['widget'] = widget
                else:
                    options_dict['widget'] = widget(**widget_options)
            self.fields[name] = forms.CharField(**options_dict)

    def extra_fields(self, fields):
        for name, value in self.cleaned_data.items():
            if name in fields:
                yield (name, value)

class Field(object):
    def __init__(self, default=None, label=None, help_text=None, scope=None, editable=False, widget=None, widget_options=None):
        if getattr(self, 'value', None) is None:
            self.value = default
        self.label = label
        self.help_text = help_text
        self.scope = scope
        self.default = default
        self.editable = editable
        self.widget = widget
        self.widget_options = widget_options

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
        self.child_html = ""

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

        if len(self.child_html) > 0:
            html = self.html.replace("#{child_views}", self.child_html)
        else:
            html = self.html.replace("#{child_views}", '')

        return js_text + css_text + html

    def add_child(self, resource_html):
        self.child_html += resource_html.html
        self.js = list(set(self.js + resource_html.js))
        self.css = list(set(self.css + resource_html.css))

class ResourceRenderer(object):

    def __init__(self, resource, user_resource_state=None, static_data=None, user=None):
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

        self.static_data = static_data
        self.user = user

        self.module = RESOURCE_MODULES[self.resource.resource_type](
            resource_data,
            user_data,
            self.resource,
            static_data,
        )

    def get_children(self):
        return self.resource.children.all()

    def child_author_views(self):
        child_views = []
        children = self.get_children()
        for child in children:
            renderer = ResourceRenderer(child, static_data=self.static_data, user=self.user)
            child_views.append(renderer.author_view())
        return child_views

    def child_user_views(self):
        child_views = []
        children = self.get_children()

        # Store data to prevent descriptor overwrite by children.
        self.module.store_data()
        for child in children:
            child_access_level = ClassGroupPermissions.get_permission_level(child.classgroup, child, "change_resource")
            user_access_level = ClassGroupPermissions.access_level(child.classgroup, self.user)
            if ClassGroupPermissions.PERMISSION_LEVELS[user_access_level] >= ClassGroupPermissions.PERMISSION_LEVELS[child_access_level]:
                user_state, created = UserResourceState.objects.get_or_create(
                    user=self.user,
                    resource=child
                )
                renderer = ResourceRenderer(child, user_resource_state=user_state, static_data=self.static_data, user=self.user)
                child_views.append(renderer.user_view())

        # Read data back in.
        self.module.read_data()
        return child_views

    def user_view(self):
        resource_html = self.module.user_view()
        child_views = self.child_user_views()
        for child in child_views:
            resource_html.add_child(child)

        self.save_module_data()
        return resource_html

    def author_view(self):
        resource_html = self.module.author_view()
        child_views = self.child_author_views()
        for child in child_views:
            resource_html.add_child(child)
        return resource_html

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
    name = Field(
        default=None,
        label="Resource Name",
        help_text="The name for this module.  Must be unique (You cannot have two modules in the class with the same name).",
        scope=ResourceScope.author,
        editable=True
    )

    resource_template = "resources/user_view.html"
    resource_author_template = "resources/author_view.html"
    js = []
    css = []
    js_class_name = None

    author_js = []
    author_css = []
    author_js_class_name = None

    def __init__(self, resource_data, user_data, resource, static_data):

        # Set data from various scopes.
        self.static_data = static_data
        self.resource_id = resource.id
        self.resource_type = resource.resource_type
        self.class_name = resource.classgroup.name
        self.resource = resource
        self.resource_name = resource.display_name
        self.widget_options = {}

        self.data = {
            ResourceScope.author: resource_data,
            ResourceScope.user: user_data,
        }

        self.fields = [attr for attr in dir(self.__class__) if not attr.startswith("__") and isinstance(getattr(self.__class__, attr), Field)]
        self.read_data()

    @property
    def form_field_dictionaries(self):
        form_field_dictionaries = {}
        for field in self.fields:
            class_field = getattr(self.__class__, field)
            if class_field.scope == ResourceScope.author and class_field.editable is True:
                form_field_dictionaries[field] = {
                    'label': class_field.label,
                    'help_text': class_field.help_text,
                    'name': field,
                    'value': getattr(self, field),
                    'widget': class_field.widget,
                    'widget_options': self.widget_options.get(field),
                }
        return form_field_dictionaries

    def user_view(self):
        resource_html = ResourceHTML()
        resource_html.add_html(render_to_string(self.resource_template, {
            'content': self.render_module(),
            'resource_id': self.resource_id,
            'js_class_name': self.js_class_name,
            'resource_type': self.resource_type,
            'class_name': self.class_name
        }))
        for js in self.js:
            resource_html.add_js(js)
        for css in self.css:
            resource_html.add_css(css)
        return resource_html

    def render_module(self):
        raise NotImplementedError

    def get_scope(self, field):
        class_field = getattr(self.__class__, field)
        scope = class_field.scope
        return class_field, scope

    def change_visibility(self, post_data):
        ClassGroupPermissions.assign_perms(self.resource.classgroup, self.resource, "change_resource", post_data.get("new_role"))
        return {'success': True}

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
        current_role = ClassGroupPermissions.get_permission_level(self.resource.classgroup, self.resource, "change_resource")
        resource_html.add_html(render_to_string(self.resource_author_template, {
            'content': self.render_module_author(),
            'resource_id': self.resource_id,
            'js_class_name': self.author_js_class_name,
            'resource_type': self.resource_type,
            'class_name': self.class_name,
            'roles': [ClassGroupPermissions.student, ClassGroupPermissions.teacher],
            'current_role': current_role,
        }))
        for js in self.author_js:
            resource_html.add_js(js)
        for css in self.author_css:
            resource_html.add_css(css)
        return resource_html

    def handle_ajax_module(self, action, post_data, **kwargs):
        raise NotImplementedError

    def handle_ajax(self, action, post_data, **kwargs):
        actions = {
            'change_visibility': self.change_visibility,
            }

        if action in actions:
            return actions[action](post_data)
        else:
            return self.handle_ajax_module(action, post_data, **kwargs)

    def get_data(self):
        self.store_data()
        return self.data

class SimpleAuthoringMixin(object):

    def render_module_author(self):
        form = ResourceForm(extra=self.form_field_dictionaries, auto_id='%s-in-{0}'.format(self.resource.id))
        return render_to_string("resources/form.html", {
            'form': form,
            'action_link': self.static_data.get('author_post_link'),
            'form_id': "resource-creation-form",
        }, context_instance=RequestContext(self.static_data.get('request')))

    def save_form_values(self, post_data):
        for name in post_data:
            if hasattr(self, name) and isinstance(getattr(self.__class__, name), Field):
                setattr(self, name, post_data[name])

        return {'success': True}

    def handle_ajax_module(self, action, post_data, **kwargs):
        actions = {
            'save_form_values': self.save_form_values
        }

        return actions[action](post_data)

class HTMLModule(SimpleAuthoringMixin, ResourceModule):
    html = Field(
        default="",
        label="Post text",
        help_text="The text of your post.",
        scope=ResourceScope.author,
        editable=True,
        widget=RichEditor,
    )
    template = "resources/html_module.html"

    def replace_html_links(self):
        match_pattern = r'(\#\[\[.+\]\])'
        regex = re.compile(match_pattern)

        resource_pattern = r'\#\[\[(.+)\]\]'
        resource_regex = re.compile(resource_pattern)

        html = deepcopy(self.html)
        matches = regex.findall(html)

        for m in matches:
            resource_name = resource_regex.findall(m)[0]
            file_url = get_temporary_s3_url(resource_name)
            html = html.replace(m, file_url)
        return html

    def save_form_values(self, post_data):
        if 'html' in post_data:
            url_search_pattern = r'(https:\/\/{0}.s3.amazonaws.com\/{1}\/.+)">'.format(settings.S3_BUCKETNAME.lower(), self.resource.classgroup.name)
            regex = re.compile(url_search_pattern)
            resource_pattern = r'https:\/\/{0}.s3.amazonaws.com\/({1}\/.+)\?Signature'.format(settings.S3_BUCKETNAME.lower(), self.resource.classgroup.name)
            resource_regex = re.compile(resource_pattern)
            matches = regex.findall(post_data['html'])
            for m in matches:
                resource_name = resource_regex.findall(m)[0]
                resource_name = "#[[{0}]]".format(resource_name)
                post_data['html'] = post_data['html'].replace(m, resource_name)

        for name in post_data:
            if hasattr(self, name) and isinstance(getattr(self.__class__, name), Field):
                setattr(self, name, post_data[name])

        return {'success': True}

    def render_module_author(self):
        self.widget_options['html'] = {
            'class_name': self.class_name
        }
        form_field_dict = self.form_field_dictionaries
        form_field_dict['html']['value'] = self.replace_html_links()
        form = ResourceForm(extra=form_field_dict, auto_id='%s-in-{0}'.format(self.resource.id))
        return render_to_string("resources/form.html", {
            'form': form,
            'action_link': self.static_data.get('author_post_link'),
            'form_id': "resource-creation-form",
            }, context_instance=RequestContext(self.static_data.get('request')))


    def render_module(self):

        return render_to_string(self.template, {
            'html': self.replace_html_links(),
            'name': self.name,
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
            'link': self.link,
            'name': self.name,
        })

class VideoModule(SimpleAuthoringMixin, ResourceModule):
    video_id = Field(
        default="",
        label="Youtube video ID",
        help_text="The Youtube video ID.",
        scope=ResourceScope.author,
        editable=True
    )
    template = "resources/video_module.html"

    def render_module(self):
        return render_to_string(self.template, {
            'video_id': self.video_id,
            'resource_id': self.resource_id,
            'name': self.name,
        })

class VerticalModule(ResourceModule):
    description = Field(
        default=None,
        label="Description",
        help_text="The description for this module.",
        scope=ResourceScope.author,
        editable=True
    )

    template = "resources/vertical_module.html"
    author_template = "resources/vertical_author.html"
    author_css = ["css/resource/vertical.css"]
    author_js = ["js/resource/vertical_author.js"]
    author_js_class_name = "VerticalAuthor"
    js = ["js/resource/vertical_module.js"]
    css = ["css/resource/vertical.css"]
    js_class_name = "VerticalUser"

    def handle_ajax_module(self, action, post_data, **kwargs):
        ajax_handlers = {
            'reorder_modules': self.reorder_modules,
            'save_form_values': self.save_form_values
        }

        return json.dumps(ajax_handlers[action](post_data))

    def save_form_values(self, post_data):
        for name in post_data:
            if hasattr(self, name) and isinstance(getattr(self.__class__, name), Field):
                setattr(self, name, post_data[name])
        return {'success': True}

    def reorder_modules(self, post_data):
        child_ids = post_data['child_ids']
        self.resource.set_resource_order(child_ids)

        return {'success': True}

    def render_module(self):
        return render_to_string(self.template, {
            'description': self.description,
        })

    def render_module_author(self):
        form = ResourceForm(extra=self.form_field_dictionaries)
        return render_to_string(self.author_template, {
            'form': form,
            'action_link': self.static_data.get('author_post_link'),
            'form_id': "resource-creation-form",
            }, context_instance=RequestContext(self.static_data.get('request')))

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
        label="Student answers",
        help_text="List of which answer the student selected on each attempt.",
        scope=ResourceScope.user
    )

    template = "resources/multiple_choice_module.html"
    author_template = "resources/multiple_choice_author.html"
    author_css = ["css/resource/multiple_choice.css"]
    author_js = ["js/resource/multiple_choice_author.js"]
    author_js_class_name = "MultipleChoiceAuthor"
    css = ["css/resource/multiple_choice.css"]
    js = ["js/resource/multiple_choice_module.js"]
    js_class_name = "MultipleChoiceUser"

    def save_form_values(self, post_data):
        self.maximum_attempts = int(post_data['maximum_attempts'])
        options = {int(k.replace('option', '')): post_data[k] for k in post_data if k.startswith('option')}

        self.name = post_data['name']

        self.question = post_data['question']
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

    def get_score(self):
        if len(self.answers) > 0:
            previous_answer = int(self.answers[-1])
            return int(self.correct_answer() == previous_answer)
        else:
            return 0

    def handle_ajax_module(self, action, post_data, **kwargs):
        ajax_handlers = {
            'save_answer': self.save_answer,
            'try_again': self.try_again,
            'save_form_values': self.save_form_values
        }

        return json.dumps(ajax_handlers[action](post_data))

    def save_answer(self, post_data):
        self.answers.append(post_data['answer'])
        if self.attempts < self.maximum_attempts:
            self.attempts += 1
            return {'correct': self.find_correct(post_data['answer']), 'html': self.render_module()}
        else:
            error_msg = "Cannot attempt this problem again."
            raise ModuleException(error_msg)

    def allow_retry(self):
        allow_retry = False
        if self.attempts < self.maximum_attempts:
            allow_retry = True
        return allow_retry

    def try_again(self):
        return {'allow_retry': self.allow_retry()}

    def render_module(self):
        previous_answer = -1
        if len(self.answers) > 0:
            previous_answer = int(self.answers[-1])
        return render_to_string(self.template, {
            'options': [o[0] for o in self.options],
            'question': self.question,
            'previous_answer': previous_answer,
            'allow_retry': self.allow_retry(),
            'correct_answer': self.correct_answer(),
            'resource_id': self.resource_id,
            'name': self.name,
        })

    def render_module_author(self):
        form = ResourceForm(extra=self.form_field_dictionaries)
        return render_to_string(self.author_template, {
            'form': form,
            'action_link': self.static_data.get('author_post_link'),
            'form_id': "resource-creation-form",
            'options': self.options,
            }, context_instance=RequestContext(self.static_data.get('request')))

def alphanumeric_name(string):
    return re.sub(r'\W+', '', string.lower().encode("ascii", "ignore"))

class FileModule(ResourceModule):
    """
    The options data structure is a list of lists.
    So: [[text, correct], [text, correct]], like [["The sun is yellow", True], ["The sun is blue", False]].
    """
    filename = Field(
        default=None,
        label="Filename",
        help_text="Name of the uploaded file.",
        scope=ResourceScope.author
    )
    file_actual_name = Field(
        default=None,
        label="File S3 URL",
        help_text="URL of uploaded file.",
        scope=ResourceScope.author
    )

    template = "resources/file_module.html"
    author_template = "resources/file_author.html"

    def handle_ajax_module(self, action, post_data, **kwargs):
        ajax_handlers = {
            'save_form_values': self.save_form_values,
            }

        return json.dumps(ajax_handlers[action](post_data))

    def save_form_values(self, post_data):
        self.name = post_data['name']

        if 'file' in post_data and isinstance(post_data['file'], UploadedFile):
            file_obj = post_data['file']
            self.file_url, self.filename = upload_to_s3(file_obj, self.class_name)
            self.file_actual_name = file_obj.name
        return {'success': True}

    def render_module(self):
        file_url = None
        if self.filename is not None:
            file_url = get_temporary_s3_url(self.filename)
        if self.file_actual_name is None:
            self.file_actual_name = self.filename
        return render_to_string(self.template, {
            'file_actual_name': self.file_actual_name,
            'file_url': file_url,
            'resource_id': self.resource_id,
            'name': self.name,
            })

    def render_module_author(self):
        form = ResourceForm(extra=self.form_field_dictionaries)
        return render_to_string(self.author_template, {
            'form': form,
            'action_link': self.static_data.get('author_post_link'),
            'form_id': "resource-creation-form",
            'filename': self.filename,
            }, context_instance=RequestContext(self.static_data.get('request')))

RESOURCE_MODULES = {
    'html': HTMLModule,
    'link': LinkModule,
    'multiplechoice': MultipleChoiceProblemModule,
    'vertical': VerticalModule,
    'video': VideoModule,
    'file': FileModule,
}