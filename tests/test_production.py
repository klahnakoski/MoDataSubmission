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

from pyLibrary import convert, jsons
from pyLibrary.debugs.logs import Log
from pyLibrary.dot import unwrap
from pyLibrary.maths.randoms import Random
from modatasubmission import Client


settings = jsons.ref.get("file://~/MoDataSubmissionClient.json")


data={
    "constant": "this is a test",
    "random-data": convert.bytes2base64(Random.bytes(100))
}
link, id = Client(settings.url, unwrap(settings.hawk)).send(data)
Log.note("Success!  Located at {{link}} id={{id}}", link=link, id=id)


data = settings.example

response = requests.post(settings.url, data=data)
if response.status_code == 200:
    details = convert.json2value(convert.utf82unicode(response.content))
    Log.note("Success!  Located at {{link}} id={{id}}", link=link, id=id)
