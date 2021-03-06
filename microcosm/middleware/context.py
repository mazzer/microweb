import logging

from django.conf import settings
from django.http import HttpResponseRedirect

import requests
import grequests
import pylibmc as memcache

from microcosm.api.resources import Site
from microcosm.api.resources import WhoAmI
from microcosm.api.exceptions import APIException

logger = logging.getLogger('microcosm.middleware')

class ContextMiddleware():
    """
    Provides request context such as the current site and authentication status.
    """

    def __init__(self):
        self.mc = memcache.Client(['%s:%d' % (settings.MEMCACHE_HOST, settings.MEMCACHE_PORT)])

    def process_request(self, request):
        """
        Checks for access_token cookie and appends it to the request object if present.

        All request objects have a view_requests attribute which is a list of requests
        that will be executed by grequests to fetch data for the view.
        """

        request.access_token = None
        request.whoami_url = ''
        request.view_requests = []
        request.site = None

        if request.COOKIES.has_key('access_token'):
            request.access_token = request.COOKIES['access_token']
            url, params, headers = WhoAmI.build_request(request.get_host(), request.access_token)
            request.view_requests.append(grequests.get(url, params=params, headers=headers))
            request.whoami_url = url

        try:
            request.site = Site.retrieve(request.get_host())
        except APIException as e:
            if e.status_code == 400:
                return HttpResponseRedirect('https://microco.sm')
        return None
