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

from modatasubmission import storage, Client
from pyLibrary import convert, jsons
from pyLibrary.debugs.logs import Log
from pyLibrary.dot import unwrap
from pyLibrary.maths.randoms import Random
from pyLibrary.testing.fuzzytestcase import FuzzyTestCase

CONTENT_TYPE = b"application/json"
NUM_TESTS = storage.BATCH_SIZE

server = None
settings = None


class TestService(FuzzyTestCase):
    """
    PLEASE RUN THE SERVICE LOCALLY, USING --settings==tests/resources/config/server.json
    BEFORE STARTING TESTS
    """

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
        # MAKE SOME DATA
        data = {
            "constant": "this is a test",
            "random-data": convert.bytes2base64(Random.bytes(100))
        }

        client = Client(settings.url, unwrap(settings.hawk)) # unwrap() DUE TO BUG https://github.com/kumar303/mohawk/issues/21
        link = client.send(data)
        Log.note("Success!  Located at {{link}}", link=link)

    def test_many_request(self):
        client = Client(settings.url, unwrap(settings.hawk))  # unwrap() DUE TO BUG https://github.com/kumar303/mohawk/issues/21
        link = None
        for i in range(NUM_TESTS):
            link = client.send({
                            "constant": "this is a test",
                            "random-data": convert.bytes2base64(Random.bytes(100))
                        })

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

