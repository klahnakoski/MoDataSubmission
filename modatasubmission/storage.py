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
from pyLibrary.maths import Math
from pyLibrary.meta import use_settings
from pyLibrary.queries import qb
from pyLibrary.strings import expand_template
from pyLibrary.thread.threads import Thread, Lock
from pyLibrary.times.dates import Date
from pyLibrary.times.durations import DAY, MINUTE, ZERO

DEBUG = True
ZERO_DATE = Date("1 JAN 2015")
BATCH_SIZE = 100
LINK_PATTERN = "https://s3-{{region}}.amazonaws.com/{{bucket}}/{{uid}}.json.gz"
UID_PATH = "etl.source.uid"


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
        self.uid = None
        self.bucket = s3.Bucket(settings=settings)
        self.temp_queue = PersistentQueue(bucket + "_queue.txt")
        self._figure_out_start_point()
        self.push_to_s3 = Thread.run("pushing to " + bucket, self._worker)

    def _figure_out_start_point(self):
        # RECOVER FROM THE QUEUE
        acc = []
        while True:
            d = self.temp_queue.pop(timeout=ZERO)
            if d:
                acc.append(d)
            else:
                break
        self.temp_queue.rollback()

        if acc:
            # WAS IN THE MIDDLE OF A BATCH, FIND count
            data = acc[-1]
            today_ = data[UID_PATH].split(".")[0]
            todays_batch_count = int(data[UID_PATH].split(".")[1])
            count = todays_batch_count * BATCH_SIZE + data.etl.id + 1
            if DEBUG:
                Log.note(
                    "Next uid from queue is {{uid}}.{{count}}",
                    count=count % BATCH_SIZE,
                    uid=today_ + "." + unicode(todays_batch_count)
                )
            self.uid = UID(count)
            return

        # FIND LAST WHOLE BATCH FROM TODAY
        today_ = unicode(today())
        todays_keys = self.bucket.keys(prefix=unicode(today_))
        if not todays_keys:
            if DEBUG:
                Log.note("Next uid is {{uid}}.{{count}}", count=0, uid=today_+".0")
            self.uid = UID()
            return

        todays_batch_count = qb.sort(int(k.split(".")[1]) for k in todays_keys).last() + 1
        max_key = today_ + "." + unicode(todays_batch_count)

        if DEBUG:
            Log.note("Next uid is {{uid}}", uid=max_key)
        count = todays_batch_count * BATCH_SIZE
        self.uid = UID(count)

    def add(self, data):
        data = wrap(data)
        uid, count = self.uid.advance()
        link = expand_template(
            LINK_PATTERN,
            {
                "region": self.bucket.settings.region,
                "bucket": self.bucket.settings.bucket,
                "uid": uid
            }
        )
        data.etl.id = count
        data.etl.source.href = link
        data[UID_PATH] = uid
        self.temp_queue.add(data)
        return link, count

    def _worker(self, please_stop):
        curr = "0.0"
        acc = []
        last_count_written = -1
        next_write = Date.now()

        while not please_stop:
            d = self.temp_queue.pop(timeout=MINUTE)
            if d == None:
                if not acc:
                    continue
                # WRITE THE INCOMPLETE DATA TO S3, BUT NOT TOO OFTEN
                next_write = Date.now() + MINUTE
                try:
                    if last_count_written != len(acc):
                        if DEBUG:
                            Log.note("write incomplete data ({{num}} lines) to {{uid}} in S3 next (time = {{next_write}})", uid=curr, next_write=next_write, num=len(acc))
                        self.bucket.write_lines(curr, (convert.value2json(a) for a in acc))
                        last_count_written = len(acc)
                except Exception, e:
                    Log.note("Problem with write to S3", cause=e)
            elif d[UID_PATH] != curr:
                # WRITE acc TO S3 IF WE ARE MOVING TO A NEW KEY
                try:
                    if acc:
                        if DEBUG:
                            Log.note("write complete data ({{num}} lines) to {{curr}} in S3", num=len(acc), curr=curr)
                        self.bucket.write_lines(curr, (convert.value2json(a) for a in acc))
                        last_count_written = 0
                    curr = d[UID_PATH]
                    acc = [d]
                except Exception, e:
                    Log.warning("Can not store data", cause=e)
                    Thread.sleep(30*MINUTE)
            else:
                acc.append(d)
                now = Date.now()

                if d.etl.id >= BATCH_SIZE - 1:
                    # WRITE THE COMPLETE CONTENTS TO KEY
                    try:
                        if DEBUG:
                            Log.note("batch complete: ({{num}} lines) to {{curr}} in S3", num=len(acc), curr=curr)
                        self.bucket.write_lines(curr, (convert.value2json(a) for a in acc))
                        last_count_written = 0
                        self.temp_queue.commit()
                        curr = d[UID_PATH]
                        acc = []
                    except Exception, e:
                        Log.warning("Can not store data", cause=e)
                        Thread.sleep(30*MINUTE)
                elif now > next_write:
                    # WRITE THE INCOMPLETE DATA TO S3, BUT NOT TOO OFTEN
                    next_write = now + MINUTE
                    try:
                        if DEBUG:
                            Log.note("write incomplete data ({{num}} lines) to {{uid}} in S3 next (time = {{next_write}})", uid=curr, next_write=next_write, num=len(acc))
                        self.bucket.write_lines(curr, (convert.value2json(a) for a in acc))
                        last_count_written = len(acc)
                    except Exception, e:
                        Log.note("Problem with write to S3", cause=e)


class UID(object):
    def __init__(self, count=0):
        self.count = count
        self.today = today()
        self.locker = Lock()

    def advance(self):
        with self.locker:
            try:
                if self.today != today():
                    self.today = today()
                    self.count = 0

                batch = Math.floor(self.count/BATCH_SIZE)
                return unicode(self.today) + "." + unicode(batch), self.count % BATCH_SIZE
            finally:
                self.count += 1


def today():
    return int((Date.today() - ZERO_DATE).floor(DAY) / DAY)
