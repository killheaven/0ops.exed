# -*- coding: utf-8 -*-

import six
import cherrypy

try:
    from urllib.parse import unquote
except ImportError:
    from urllib import unquote

from exe.runner import ExecuteRunner

from .utils import *
from .consts import *
from .handler import EndpointHandler


@cherrypy.expose
class ExecuteHandler(EndpointHandler):
    """ Endpoint Handler: `/execute`. """

    __RUNNER__ = ExecuteRunner

    @cherrypy.tools.json_out()
    def GET(self, **params):
        """ Execute command on remote host. """

        target = parse_params_target(params)
        cmd = params.pop('cmd', None)
        if cmd == None:
            raise cherrypy.HTTPError(status.BAD_REQUEST, ERR_BAD_SERVPARAMS)
        cmd = unquote(cmd)

        result = next(self.handle(target, cmd), None)
        if not result:
            raise cherrypy.HTTPError(status.NOT_FOUND, ERR_NO_MATCH)
        else:
            return response(status.OK, result)

    @cherrypy.tools.json_in(force=False)
    @cherrypy.tools.json_out()
    def POST(self, **params):
        """ Execute command on remote host(s). """

        targets = cherrypy.request.json.pop('targets', None)
        if not targets or not isinstance(targets, list):
            raise cherrypy.HTTPError(status.BAD_REQUEST, ERR_NO_TARGET)

        cmd = cherrypy.request.json.pop('cmd', None)
        if not cmd or not isinstance(cmd, six.text_type):
            raise cherrypy.HTTPError(status.BAD_REQUEST, ERR_BAD_ROLE)

        jid = self.handle(targets, cmd, async=True)
        return response(status.CREATED, dict(jid=jid))
