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
from mohawk import Sender

CONTENT_TYPE = b"application/json"


class Client(object):
    """
    A MINIMAL DEPENDENCY CLIENT FOR SENDING, AND SIGNING, DATA TO A STORAGE SERVICE
    """

    def __init__(self, url, hawk_credentials):
        """
        :param url: server:port/path TO A MoDataSubmission SERVER
        :param hawk_credentials: A dict WITH
            "id": "kyle@example.com",
            "key": "secret",
            "algorithm": "sha256"
        :return:
        """
        self.url=url
        self.hawk=hawk_credentials

    def send(self, value):
        """
        :param json_data: A dict OF DATA TO SEND
        :return: URL OF WHERE DATA WAS STORED
        """
        content = json.dumps(value)

        # Hawk Sender WILL DO THE WORK OF SIGNINGs
        sender = Sender(
            self.hawk,
            self.url,
            b"POST",
            content=content,
            content_type=CONTENT_TYPE
        )

        # STANDARD POST
        response = requests.post(
            url=self.url,
            data=content,
            headers={
                'Authorization': sender.request_header,
                'Content-Type': CONTENT_TYPE
            }
        )

        if response.status_code != 200:
            raise Exception(response.content)

        # SERVER SIGNED THE RESPONSE. VERIFY IT
        sender.accept_response(
            response.headers['Server-Authorization'],
            content=response.content,
            content_type=response.headers['Content-Type']
        )

        link = json.loads(response.content)["link"]
        return link

