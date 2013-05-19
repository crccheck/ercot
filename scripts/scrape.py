#! /usr/bin/env python
from glob import glob
import os
import sys
import time
import logging

from dateutil import parser
from lxml.html import parse
import dataset

DATA_DIR = "../download"
FLOAT_KEYS = ('Current Frequency', 'Instantaneous Time Error', )


def guess_type(data_tuple):
    """Cast string data into number types (int or float)."""
    for key, value in data_tuple:
        if key in FLOAT_KEYS:
            yield key, float(value)
        else:
            yield key, int(value)


def normalize_html(f):
    """Extract data from a file."""
    doc = parse(f)
    timestamp_text = doc.xpath("//span[@class='labelValueClass']")[0].text
    timestamp_text = timestamp_text.split(" ", 2)[2]
    timestamp = parser.parse(timestamp_text)
    labels = [x.text for x in doc.xpath("//span[@class='labelValueClass']")[1:]]
    values = [x.text for x in doc.xpath("//span[@class='labelValueClassBold']")]
    data = dict(guess_type(zip(labels, values)))
    data['timestamp'] = timestamp
    return data


def process(store, files):
    """Process all the files."""
    for f in files:
        try:
            with open(f, 'r') as fh:
                data = normalize_html(fh)
            ctime = int(time.mktime(data['timestamp'].timetuple()))
            # TODO delete file after parsing
        except AssertionError as e:
            # malformed HTML
            logger.error("{} {}".format(f, e))
            continue
        logger.info("{} {}".format(ctime, data))
        store.upsert(data, ['timestamp'])


def batch_process(store, files, batch=False):
    """Process all the files in batches."""
    # TODO abstract common stuff with `process()`
    for f in files:
        try:
            with open(f, 'r') as fh:
                data = normalize_html(fh)
        except AssertionError as e:
            # malformed HTML
            logger.error("{} {}".format(f, e))
            continue
        yield data


def main(batch):
    # TODO abstract db stuff out of `main`
    db = dataset.connect('sqlite:///test.db')
    table = db['ercot_realtime']
    table.create_index(['timestamp'])  # TODO make this UNIQUE

    files = glob(os.path.join(DATA_DIR, '*.html'))
    if batch:
        table.insert_many(batch_process(table, files, batch))
    else:
        process(table, files)


logger = logging.getLogger(__name__)
if __name__ == "__main__":
    batch = '--initial' in sys.argv
    main(batch)