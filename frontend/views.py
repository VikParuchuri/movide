from django.shortcuts import render, render_to_response, redirect
from django.conf import settings
import logging
from datetime import timedelta
from django.utils.timezone import now
from django.template import RequestContext

log=logging.getLogger(__name__)

def index(request):
    return render_to_response("index.html", context_instance=RequestContext(request))
