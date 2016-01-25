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

import json

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

        client = Client(settings.url, unwrap(settings.hawk))  # unwrap() DUE TO BUG https://github.com/kumar303/mohawk/issues/21
        link, id = client.send(data)
        Log.note("Success!  Located at {{link}} id={{id}}", link=link, id=id)

        # FILL THE REST OF THE FILE
        Log.note("Add ing {{num}} more...", num=99-id)
        for i in range(id + 1, storage.BATCH_SIZE):
            l, k = client.send(data)
            if l != link:
                Log.error("Expecting rest of data to have same link")

        # TEST LINK HAS DATA
        content = convert.zip2bytes(requests.get(link).content)
        for line in convert.utf82unicode(content).split("\n"):
            data = convert.json2value(line)
            if data.etl.id == id:
                Log.note("Data {{id}} found", id=id)
                break
        else:
            Log.error("Expecting to find data at link")


    def test_public_request(self):
        # MAKE SOME DATA
        data = {
            "a": {  # MATCHES SERVER PATTERN
                "b": "good",
                "c": [
                    {"k": "good", "m": 1},
                    {"k": 2, "m": 2}
                ]
            },
            "constant": "this is a test",
            "random-data": convert.bytes2base64(Random.bytes(100))
        }

        content = json.dumps(data)

        response = requests.post(
            url=settings.url,
            data=content,
            headers={
                'Content-Type': CONTENT_TYPE
            }
        )

        self.assertEqual(response.status_code, 200, "Expecting 200")

        about = json.loads(response.content)
        return about['link'], about['etl']['id']

        Log.note("Data located at {{link}} id={{id}}", link=link, id=id)


    def test_public_request_too_big(self):
        # MAKE SOME DATA
        data = {
            "a": {  # MATCHES SERVER PATTERN
                "b": "good",
                "c": [
                    {"k": "good", "m": 1},
                    {"k": 2, "m": 2}
                ]
            },
            "constant": "this is a test",
            "random-data": convert.bytes2base64(Random.bytes(500))
        }

        content = json.dumps(data)

        def poster():
            response = requests.post(
                url=settings.url,
                data=content,
                headers={
                    'Content-Type': CONTENT_TYPE
                }
            )

            self.assertEqual(response.status_code, 200, "Expecting 200")

        self.assertRaises(Exception, poster)

    def test_missing_auth(self):
        # MAKE SOME DATA
        data = {
            "constant": "this is a test",
            "random-data": convert.bytes2base64(Random.bytes(100))
        }

        response = requests.post(settings.bad_url, data=convert.unicode2utf8(convert.value2json(data)))
        self.assertEqual(response.status_code, 400)
