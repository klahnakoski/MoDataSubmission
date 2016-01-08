# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import requests
from mohawk import Sender

from pyLibrary import convert, jsons
from pyLibrary.debugs.logs import Log
from pyLibrary.dot import wrap, unwrap
from pyLibrary.maths.randoms import Random
from pyLibrary.testing.fuzzytestcase import FuzzyTestCase
from pyLibrary.thread.multiprocess import Process

CONTENT_TYPE = b"application/json"

server = None
settings = None


class TestService(FuzzyTestCase):
    def __init__(self, *args, **kwargs):
        global server
        global settings

        FuzzyTestCase.__init__(self, *args, **kwargs)
        if not server:
            server = Process(
                "Storage Server",
                [
                    "python",
                    "modatasubmission/app.py"
                    "--setting=tests/resources/config/server.json"
                ],
                env={b"PYTHONPATH": b"."}
            )
            settings = jsons.ref.get("file://tests/resources/config/client.json")

    @classmethod
    def tearDownClass(cls):
        if server:
            server.stop()

    def test_request(self):
        content = convert.unicode2utf8(convert.value2json({
            "constant": "this is a test",
            "random-data": convert.bytes2base64(Random.bytes(100))
        }))
        sender = Sender(
            unwrap(settings.hawk),
            settings.url,
            b"POST",
            content=content,
            content_type=CONTENT_TYPE
        )

        response = requests.post(
            url=settings.url,
            data=content,
            headers={
                'Authorization': sender.request_header,
                'Content-Type': CONTENT_TYPE
            }
        )

        sender.accept_response(
            response.headers['Server-Authorization'],
            content=response.content,
            content_type=response.headers['Content-Type']
        )

        link = wrap(response.json).link

        Log.note("Success!  Located at {{link}}", link=link)
