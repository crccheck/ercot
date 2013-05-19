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
            timestamp = doc.xpath("//span[@class='labelValueClass']")[0].text
            timestamp = timestamp.split(" ", 2)[2]
            created = parser.parse(timestamp)
            ctime = int(time.mktime(created.timetuple()))
            labels = [x.text for x in doc.xpath("//span[@class='labelValueClass']")[1:]]
            values = [x.text for x in doc.xpath("//span[@class='labelValueClassBold']")]
            data = dict(zip(labels, values))
            # TODO delete file after parsing
        except AssertionError as e:
            logger.error(e)
            continue
        logger.info("{} {}".format(ctime, data))
        table.insert(data)


if __name__ == "__main__":
    main()
