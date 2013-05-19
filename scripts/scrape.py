#! /usr/bin/env python
from glob import glob
import os
import time
import logging

from dateutil import parser
from lxml.html import parse
import dataset

DATA_DIR = "../download"


def main():
    logger = logging.getLogger(__name__)
    db = dataset.connect('sqlite:///test.db')
    table = db['ercot_realtime']

    files = glob(os.path.join(DATA_DIR, '*.html'))
    for f in files:
        try:
            doc = parse(open(f, "r"))
            timestamp_text = doc.xpath("//span[@class='labelValueClass']")[0].text
            timestamp_text = timestamp_text.split(" ", 2)[2]
            timestamp = parser.parse(timestamp_text)
            ctime = int(time.mktime(timestamp.timetuple()))
            labels = [x.text for x in doc.xpath("//span[@class='labelValueClass']")[1:]]
            values = [x.text for x in doc.xpath("//span[@class='labelValueClassBold']")]
            data = dict(zip(labels, values))
            data['timestamp'] = timestamp
            # TODO delete file after parsing
        except AssertionError as e:
            logger.error(e)
            continue
        logger.info("{} {}".format(ctime, data))
        table.insert(data)


if __name__ == "__main__":
    main()
