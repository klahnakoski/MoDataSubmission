# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

from pyLibrary import convert
from pyLibrary.aws import s3
from pyLibrary.collections.persistent_queue import PersistentQueue
from pyLibrary.debugs.logs import Log
from pyLibrary.dot import wrap
from pyLibrary.meta import use_settings
from pyLibrary.strings import expand_template
from pyLibrary.thread.threads import Thread, Lock
from pyLibrary.times.dates import Date
from pyLibrary.times.durations import DAY, MINUTE

REFERENCE = Date("1 JAN 2015")
BATCH_SIZE = 100
LINK_PATTERN = "https://s3-{{region}}.amazonaws.com/{{bucket}}/{{uid}}.json.gz"


class Storage(object):
    @use_settings
    def __init__(
        self,
        bucket,  # NAME OF THE BUCKET
        aws_access_key_id=None,  # CREDENTIAL
        aws_secret_access_key=None,  # CREDENTIAL
        region=None,  # NAME OF AWS REGION, REQUIRED FOR SOME BUCKETS
        public=False,
        debug=False,
        settings=None
    ):
        self.uid = UID()
        self.bucket = s3.Bucket(settings=settings)
        self.temp_queue = PersistentQueue(bucket + "_queue.txt")
        self.push_to_s3 = Thread.run("pushing to " + bucket, self._worker)

    def add(self, data):
        data = wrap(data)
        uid = self.uid.advance()
        link = expand_template(
            LINK_PATTERN,
            {
                "region": self.bucket.settings.region,
                "bucket": self.bucket.settings.bucket,
                "uid": uid
            }
        )
        data.etl.href = link
        data.etl.uid = uid
        data.etl.source.id, data.etl.id = map(int, uid.split("."))
        self.temp_queue.add(data)
        return link

    def _worker(self, please_stop):
        curr = "0.0"
        acc = []
        next_write = Date.now()

        while not please_stop:
            d = self.temp_queue.pop()
            if d.etl.uid != curr:
                try:
                    next_write = Date.now() + MINUTE
                    self.bucket.write_lines(curr, (convert.value2json(a) for a in acc))
                    self.temp_queue.commit()
                    curr = d.etl.uid
                    acc = []
                except Exception, e:
                    self.temp_queue.rollback()
                    Log.warning("Can not store data", cause=e)
                    Thread.sleep(30*MINUTE)
            else:
                acc.append(d)
                if next_write > Date.now():
                    # WRITE THE INCOMPLETE DATA TO S3, BUT NOT TOO OFTEN
                    next_write = Date.now() + MINUTE
                    try:
                        self.bucket.write_lines(curr, (convert.value2json(a) for a in acc))
                    except Exception:
                        pass


class UID(object):
    def __init__(self, count=0, batch=0):
        self.count = count
        self.today = today()
        self.locker = Lock()

    def advance(self):
        with self.locker:
            if self.today != today():
                self.today = today()
                self.count = 0

            batch = self.count % BATCH_SIZE
            self.count += 1
            return unicode(self.today) + "." + unicode(batch)


def today():
    return int((Date.today() - REFERENCE).floor(DAY) / DAY)
