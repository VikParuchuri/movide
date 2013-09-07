from django.shortcuts import render, render_to_response, redirect
from django.conf import settings
import logging
from datetime import timedelta
from django.utils.timezone import now
from django.template import RequestContext

from django.contrib.auth import authenticate, login, logout as django_logout
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.conf import settings
from django.core.urlresolvers import reverse
from twython import Twython
from api.models import UserProfile
from api.tasks import create_user_profile

log=logging.getLogger(__name__)


def logout(request, redirect_url=settings.LOGOUT_REDIRECT_URL):
    django_logout(request)
    return HttpResponseRedirect(request.build_absolute_uri(redirect_url))


def begin_auth(request):
    # Instantiate Twython with the first leg of our trip.
    twitter = Twython(settings.TWITTER_AUTH_APP_KEY, settings.TWITTER_AUTH_SECRET_APP_KEY)

    # Request an authorization url to send the user to...
    callback_url = request.build_absolute_uri(reverse('frontend.views.thanks'))
    auth_props = twitter.get_authentication_tokens(callback_url)

    # Then send them over there, durh.
    request.session['request_token'] = auth_props
    return HttpResponseRedirect(auth_props['auth_url'])


def thanks(request, redirect_url=settings.LOGIN_REDIRECT_URL):
    """A user gets redirected here after hitting Twitter and authorizing your app to use their data.

    This is the view that stores the tokens you want
    for querying data. Pay attention to this.

    """
    # Now that we've got the magic tokens back from Twitter, we need to exchange
    # for permanent ones and store them...
    oauth_token = request.session['request_token']['oauth_token']
    oauth_token_secret = request.session['request_token']['oauth_token_secret']
    twitter = Twython(settings.TWITTER_AUTH_APP_KEY, settings.TWITTER_AUTH_SECRET_APP_KEY,
                      oauth_token, oauth_token_secret)

    # Retrieve the tokens we want...
    authorized_tokens = twitter.get_authorized_tokens(request.GET['oauth_verifier'])

    # If they already exist, grab them, login and redirect to a page displaying stuff.
    try:
        user = User.objects.get(username=authorized_tokens['screen_name'])
        try:
            profile = UserProfile.objects.get(user=user)
            profile.oauth_secret = authorized_tokens['oauth_token_secret']
            profile.oauth_token = profile.oauth_token = authorized_tokens['oauth_token']
            profile.save()
        except UserProfile.DoesNotExist:
            create_profile(authorized_tokens, user)

    except User.DoesNotExist:
        user = User.objects.create_user(authorized_tokens['screen_name'], "fjdsfn@jfndjfn.com", authorized_tokens['oauth_token_secret'])
        create_profile(authorized_tokens, user)

    user = authenticate(
        username=authorized_tokens['screen_name'],
        password=authorized_tokens['oauth_token_secret']
    )
    login(request, user)
    return HttpResponseRedirect(redirect_url)

def create_profile(authorized_tokens, user):
    profile = create_user_profile(authorized_tokens['screen_name'], user)
    profile.oauth_token = authorized_tokens['oauth_token']
    profile.oauth_secret = authorized_tokens['oauth_token_secret']
    profile.save()

def dashboard(request):
    return render_to_response("dashboard/main.html", context_instance=RequestContext(request))

def index(request):
    return render_to_response("index.html", context_instance=RequestContext(request))
