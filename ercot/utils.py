import datetime
import re

from dateutil import parser
from lxml.html import parse
import dj_database_url


# find text (in parentheses):
PARENS_TEXT = re.compile(r'\s\(.+\)')
# these columns are FLOAT:
FLOAT_KEYS = ('current_frequency', 'instantaneous_time_error', )


def guess_type(data_tuple):
    """Cast string data into number types (int or float)."""
    for key, value in data_tuple:
        if key in FLOAT_KEYS:
            yield key, float(value)
        else:
            yield key, int(value)


def normalize_html(f):
    """Extract our data from an html file."""
    doc = parse(f)
    timestamp_text = doc.xpath("//span[@class='labelValueClass']")[0].text
    timestamp_text = timestamp_text.split(" ", 2)[2]
    timestamp = parser.parse(timestamp_text)
    labels = [x.text for x in doc.xpath("//span[@class='labelValueClass']")[1:]]
    values = [x.text for x in doc.xpath("//span[@class='labelValueClassBold']")]
    labels = [PARENS_TEXT.sub('', x) for x in labels]  # strip parentheticals
    labels = [x.lower().replace(' ', '_') for x in labels]  # make_normal_lookin
    data = dict(guess_type(zip(labels, values)))
    data['timestamp'] = timestamp
    return data


# http://stackoverflow.com/questions/455580/json-datetime-between-python-and-javascript
def dthandler(obj):
    """json.dumps handler that handles datetime."""
    return obj.isoformat(sep=' ') if isinstance(obj, datetime.datetime) else None


def get_pg_connect_kwargs(db_url):
    """Transforms a database url into the connection kwargs psycopg2 expects."""
    config = dj_database_url.parse(db_url)
    config_map = dict(
        NAME='database',
        USER='user',
        PASSWORD='password',
        HOST='host',
        PORT='port',
    )
    connect_args = dict([(config_map[k], v) for k, v in config.items()
            if k in config_map])
    return connect_args
