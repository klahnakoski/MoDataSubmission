import sys

import flask
from flask import Flask
from mohawk import Receiver
from werkzeug.wrappers import Response

from pyLibrary import convert, jsons, strings
from pyLibrary.debugs import constants
from pyLibrary.debugs import startup
from pyLibrary.debugs.exceptions import Except
from pyLibrary.debugs.logs import Log


all_creds = []
app = Flask(__name__)

@app.route('/', defaults={'path': ''}, methods=['GET'])
@app.route('/<path:path>')
def service(path):
    try:
        request=flask.request
        auth = request.headers['Authorization']
        user = strings.between(auth, 'id="', '",')
        try:
            receiver = Receiver(
                lookup_credentials,
                auth,
                request.url,
                request.method,
                content=request.data,
                content_type=request.headers['Content-Type']
            )
        except Exception, e:
            e = Except.wrap(e)
            Log.error("Authentication failed", cause=e)

        permissions = lookup_user(user)
        if path not in user.resources:
            Log.error("{{user}} not allowed access to {{resource}}", user=permissions.hawk.id, resource=path)

        submit_data(path, permissions, request.data)

    except Exception, e:
        e = Except.wrap(e)

        return Response(
            convert.unicode2utf8(convert.value2json(e)),
            status=400,
            headers={
                "access-control-allow-origin": "*",
                "Content-type": "application/json"
            }
        )


def submit_data(path, permissions, data):
    # CONFIRM THIS IS JSON
    confirmed_data = convert.value2json(convert.json2value(data))

    #


def lookup_user(sender):
    for c in all_creds:
        if c.hawk.id == sender:
            return c
    Log.error("Sender not known {{sender}}", sender=sender)


def lookup_credentials(sender):
    return lookup_user(sender).hawk


def main():
    global all_creds

    try:
        config = startup.read_settings()
        constants.set(config.constants)
        Log.start(config.debug)

        all_creds = jsons.ref.get("file://resources/config/server/example.json")

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
