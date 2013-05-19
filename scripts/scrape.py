from glob import glob
import datetime
import os
import time

from dateutil import parser
from lxml.html import parse

DATA_DIR = "download"


def main(days=None):
    files = glob(os.path.join(DATA_DIR, '*.html'))
    outfile = open("test.csv", "w")
    header_written = False
    if days is not None:
        start = datetime.datetime.now() - datetime.timedelta(days=int(days))
    else:
        start = datetime.datetime.utcfromtimestamp(0)
    for f in files:
        try:
            doc = parse(open(f, "r"))
            timestamp = doc.xpath("//span[@class='labelValueClass']")[0].text
            timestamp = timestamp.split(" ", 2)[2]
            created = parser.parse(timestamp)
            if created < start:
                continue
            ctime = int(time.mktime(created.timetuple()))
            labels = [x.text for x in doc.xpath("//span[@class='labelValueClass']")[1:]]
            values = [x.text for x in doc.xpath("//span[@class='labelValueClassBold']")]
            data = zip(labels, values)
            # TODO delete file after parsing
        except AssertionError:
            continue
        #import ipdb; ipdb.set_trace()
        #break
        # print f, ctime
        if header_written is False:
            outfile.write("ctime,date," + ",".join(labels))
            outfile.write("\n")
            header_written = True
        outfile.write(",".join([str(ctime), timestamp] + values))
        outfile.write("\n")
    outfile.close()


if __name__ == "__main__":
    main()
