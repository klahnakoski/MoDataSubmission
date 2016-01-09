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

from modatasubmission import storage
from pyLibrary import convert, jsons
from pyLibrary.debugs import constants
from pyLibrary.debugs.logs import Log
from pyLibrary.dot import wrap, unwrap
from pyLibrary.maths.randoms import Random
from pyLibrary.testing.fuzzytestcase import FuzzyTestCase

CONTENT_TYPE = b"application/json"
NUM_TESTS = storage.BATCH_SIZE

server = None
settings = None


class TestService(FuzzyTestCase):
    def __init__(self, *args, **kwargs):
        global server
        global settings

        FuzzyTestCase.__init__(self, *args, **kwargs)
        if not settings:
            settings = jsons.ref.get("file://tests/resources/config/client.json")

        # if not server:
        #     server = Process(
        #         "Storage Server",
        #         [
        #             "python",
        #             "modatasubmission/app.py"
        #             "--setting=tests/resources/config/server.json"
        #         ],
        #         env={b"PYTHONPATH": b"."}
        #     )
        #     Thread.sleep(seconds=10)

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

        if response.status_code!=200:
            Log.error("Bad server response\n{{body}}", body=response.text)

        sender.accept_response(
            response.headers['Server-Authorization'],
            content=response.content,
            content_type=response.headers['Content-Type']
        )

        link = wrap(convert.json2value(convert.utf82unicode(response.content))).link
        Log.note("Success!  Located at {{link}}", link=link)
        return link

    def test_many_request(self):
        link = None
        for i in range(NUM_TESTS):
            link = self.test_request()

        # VERIFY WE HAVE DATA
        response = requests.get(link)
        bytes = convert.zip2bytes(response.content)

        lines = convert.utf82unicode(bytes).split("\n")
        Log.note("{{num}} lines", num=len(lines))
        for line in lines:
            if not line:
                continue
            d = convert.json2value(line)
            Log.note("{{data}}", data=d)
