from django.shortcuts import render, render_to_response, redirect
from django.conf import settings
import logging
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from api.tasks import UserTwitterData
from django.http import Http404, HttpResponse
from api.models import Classgroup
from rest_framework.response import Response
from rest_framework import status

log=logging.getLogger(__name__)

def create_profile(authorized_tokens, user):
    user_data = UserTwitterData(authorized_tokens['screen_name'])
    profile = user_data.create_profile(user)
    profile.oauth_token = authorized_tokens['oauth_token']
    profile.oauth_secret = authorized_tokens['oauth_token_secret']
    profile.save()

@login_required()
def dashboard(request):
    return render_to_response("dashboard/main.html", context_instance=RequestContext(request))

def index(request):
    return render_to_response("index.html", context_instance=RequestContext(request))

@login_required()
def verify_code(request):
    code = request.POST.get('code')
    class_name = request.POST.get("class_name")
    user = request.user
    if isinstance(code, list):
        code = code[0]
    if isinstance(class_name, list):
        class_name = class_name[0]

    if code is None:
        return HttpResponse(status=400)
    if class_name is None:
        return HttpResponse(status=400)

    try:
        cg = Classgroup.objects.get(name=class_name)
    except Classgroup.DoesNotExist:
        return Http404

    if cg.class_settings.access_key == code:
        user.classgroups.add(cg)
        user.save()
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=400)


VALID_ACTIVE_PAGES = ['messages', 'stats', 'users', 'notifications']
@login_required()
def classview(request, classgroup, **kwargs):
    active_page = kwargs.get('active_page', 'messages')
    if active_page not in VALID_ACTIVE_PAGES:
        return Http404

    try:
        cg = Classgroup.objects.get(name=classgroup)
    except Classgroup.DoesNotExist:
        return Http404

    is_owner = str(cg.owner == request.user).lower()
    template_vars = {
        'name': cg.name,
        'display_name': cg.display_name,
        'link': cg.link(),
        'is_owner': is_owner,
        'access_key': cg.class_settings.access_key,
        'active_page': active_page,
        }

    if request.user.classgroups.filter(name=classgroup).count() == 0:
        return render_to_response("enter_class_code.html", template_vars, context_instance=RequestContext(request))

    return render_to_response("dashboard/classview.html", template_vars,
           context_instance=RequestContext(request)
    )

