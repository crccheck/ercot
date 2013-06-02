import re

from dateutil import parser
from lxml.html import parse


FLOAT_KEYS = ('current_frequency', 'instantaneous_time_error', )
pattern = re.compile(r'\s\(.+\)')


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
    labels = [pattern.sub('', x) for x in labels]  # strip parentheticals
    labels = [x.lower().replace(' ', '_') for x in labels]  # make_normal_lookin
    data = dict(guess_type(zip(labels, values)))
    data['timestamp'] = timestamp
    return data
