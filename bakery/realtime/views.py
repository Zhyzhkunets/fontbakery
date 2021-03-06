# coding: utf-8
# Copyright 2013 The Font Bakery Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# See AUTHORS.txt for the list of Authors and LICENSE.txt for the License.
from __future__ import print_function

import os
import gevent
import itsdangerous
from flask import Response, current_app
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import BroadcastMixin
from flask.ext.rq import get_connection
from rq import Worker

from flask import (Blueprint, request)

realtime = Blueprint('realtime', __name__)

class StatusNamespace(BaseNamespace, BroadcastMixin):

    def __init__(self, *args, **kwargs):
        r = kwargs.get('request', None)
        self.status = ''
        if hasattr(r, '_conn'):
            self._conn = r._conn
        super(StatusNamespace, self).__init__(*args, **kwargs)

    def initialize(self):
        self.status = False
        self.spawn(self.check_queue)

    def check_queue(self):
        prev = self.status
        while True:
            gevent.sleep(0.5)
            workers = [w.state != 'idle' for w in Worker.all(self._conn)]

            if len(workers) == 0:
                self.status = 'gone'
            elif any(workers):
                self.status = 'start'
            else:
                self.status = 'stop'

            if prev != self.status:
                self.emit(self.status, {})

            prev = self.status

    def on_status(self, msg):
        if self.status:
            self.emit('start', {})
        else:
            self.emit('stop', {})


class BuildNamespace(BaseNamespace, BroadcastMixin):

    def __init__(self, *args, **kwargs):
        r = kwargs.get('request', None)
        if hasattr(r, '_conn'):
            self._conn = r._conn
            self._data_root = r._data_root
            self._signer = r._signer
        super(BuildNamespace, self).__init__(*args, **kwargs)

    def on_subscribe(self, data):
        login, pid = self._signer.unsign(data).split('/')

        gevent.spawn(self.emit_file, login, pid)

    def emit_file(self, login, pid):
        filename = os.path.join(self._data_root, login, "%s.process.log" % pid)
        if os.path.exists(filename) and os.path.isfile(filename):
            logfile = open(filename, 'r')
# TODO: make this work so that the whole file is sent in one go if the process has ended.
#            for line in logfile:
#                self.emit('message', 'looking at line for end\n')
#                if "End:" in line:
#                    self.emit('message', 'found end\n')
#                    logfile2 = open(filename, 'r')
#                    self.emit('message', logfile2.read())
#                    logfile2.close()
#                    logfile.close()
#                    return
            while True:
                line = logfile.readline()
#                self.emit('message', 'read a line: ')
                if line:
                    self.emit('message', line)
                    if line.startswith('End:'):
                        break
                    gevent.sleep(0.1) # A small delay to reduce browser hammering. It slows down the 'real time' log feel, comment this out for that.
                else:
#                    self.emit('message', 'blank \n')
                    gevent.sleep(0.1)
            logfile.close()
        else:
            self.emit('message', 'Fatal: Log file not found')

@realtime.route('/socket.io/<path:remaining>')
def socketio(remaining):
    real_request = request._get_current_object()
    # add redis connection
    real_request._conn = get_connection()
    real_request._data_root = current_app.config.get('DATA_ROOT')
    real_request._signer = itsdangerous.Signer(current_app.secret_key)
    socketio_manage(request.environ, {
        '/status': StatusNamespace,
        '/build': BuildNamespace,
        }, request=real_request)
    return Response()
