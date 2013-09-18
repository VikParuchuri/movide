from django.shortcuts import render, render_to_response, redirect
from django.conf import settings
import logging
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from api.tasks import UserTwitterData
from django.http import Http404
from api.models import Classgroup

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
def classview(request, classgroup):
    if request.user.classgroups.filter(name=classgroup).count() == 0:
        return Http404

    try:
        cg = Classgroup.objects.get(name=classgroup)
    except Classgroup.DoesNotExist:
        return Http404

    return render_to_response("dashboard/classview.html", {
                'name' : cg.name,
                'display_name': cg.display_name,
                'link': cg.link(),
            },
           context_instance=RequestContext(request)
    )

