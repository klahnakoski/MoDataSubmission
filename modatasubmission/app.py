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

import sys

import flask
from flask import Flask
from mohawk import Receiver
from werkzeug.wrappers import Response

from modatasubmission.storage import Storage
from pyLibrary import convert, jsons, strings
from pyLibrary.debugs import constants
from pyLibrary.debugs import startup
from pyLibrary.debugs.exceptions import Except
from pyLibrary.debugs.logs import Log
from pyLibrary.maths.randoms import Random
from pyLibrary.times.dates import Date
from pyLibrary.times.durations import HOUR

RESPONSE_CONTENT_TYPE = b"application/json"


all_creds = []
containers = {}
config=None

app = Flask(__name__)


@app.route('/', defaults={'path': ''}, methods=['GET'])
@app.route('/<path:path>')
def service(path):
    try:
        request = flask.request
        auth = request.headers['Authorization']
        user = strings.between(auth, 'id="', '",')
        try:
            receiver = Receiver(
                lookup_credentials,
                auth,
                request.url,
                request.method,
                content=request.data,
                content_type=request.headers['Content-Type'],
                nonce=seen_nonce
            )
        except Exception, e:
            e = Except.wrap(e)
            raise Log.error("Authentication failed", cause=e)


        permissions = lookup_user(user)
        if path not in user.resources:
            Log.error("{{user}} not allowed access to {{resource}}", user=permissions.hawk.id, resource=path)

        link = submit_data(path, permissions, request.data)

        response_content = convert.unicode2utf8(convert.value2json({"link": link}))
        receiver.respond(
            content=response_content,
            content_type=RESPONSE_CONTENT_TYPE
        )

        return Response(
            response_content,
            status=200,
            headers={
                'Server-Authorization': receiver.response_header,
                "Content-type": RESPONSE_CONTENT_TYPE
            }
        )

    except Exception, e:
        e = Except.wrap(e)

        return Response(
            convert.unicode2utf8(convert.value2json(e)),
            status=400,
            headers={
                "Content-type": "application/json"
            }
        )


def submit_data(bucket, permissions, body):
    global containers
    # CONFIRM THIS IS JSON, AND ANNOTATE
    data = {
        "etl": {
            "user": permissions.hawk.id,
            "bucket": bucket,
            "timestamp": Date.now()
        },
        "data": convert.json2value(body)
    }
    confirmed_data = convert.value2json(data)

    storage = containers.get(bucket)
    if storage==None:
        storage = containers[bucket] = Storage(bucket=bucket, public=True, settings=config.aws)
    link = storage.add(confirmed_data)
    return link




def lookup_user(sender):
    for c in all_creds:
        if c.hawk.id == sender:
            return c
    Log.error("Sender not known {{sender}}", sender=sender)


def lookup_credentials(sender):
    return lookup_user(sender).hawk


seen = {}

def seen_nonce(sender_id, nonce, timestamp):
    global seen
    key = '{id}:{nonce}:{ts}'.format(
        id=sender_id,
        nonce=nonce,
        ts=timestamp
    )

    if Random.int(1000) == 0:
        old = (Date.now()-HOUR).unix
        seen = {k: v for k, v in seen.items() if v["timestamp"] >= old}

    if seen.get(key):
        return True
    else:
        seen[key] = {"timestamp": timestamp}
        return False


def main():
    global all_creds
    global config

    try:
        config = startup.read_settings()
        constants.set(config.constants)
        Log.start(config.debug)

        all_creds = jsons.ref.get("file://resources/config/server/server.json")

        app.run(**config.flask)
    except Exception, e:
        Log.error("Serious problem with ActiveData service!  Shutdown completed!", cause=e)
    finally:
        Log.stop()

    sys.exit(0)


if __name__ == '__main__':
    app.run()




#
#
# {
# 	"meta":{
# 		"user":"klahnakoski",
# 		"resource":"code_coverage",
# 		"crypto":{
# 			"algorithm":"aes256",
# 			"nonce":"jfa987h4ofjhfuh",
# 			"timestamp":"1409829348",
# 			"signature":"asdfdsafdsaf"
# 		}
# 	},
# 	"data":{
# 		"test_name":"tester",
# 		"source_file":"run.py",
# 		"lines":[1,2,3]
# 	}
# }
