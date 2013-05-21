# New BSD
# https://code.google.com/p/ibkon-wsgi-gzip-middleware/source/browse/trunk/gzip_middleware.py
'''
    A WSGI middleware application that automatically gzips output
    to the client.
    Before doing any gzipping, it first checks the environ to see if
    the client can even support gzipped output. If not, it immediately
    drops out.
    It automatically modifies the headers to include the proper values
    for the 'Accept-Encoding' and 'Vary' headers.

    Example of use:

        from wsgiref.simple_server import WSGIServer, WSGIRequestHandler

        def test_app(environ, start_response):
            status = '200 OK'
            headers = [('content-type', 'text/html')]
            start_response(status, headers)
            return ['Hello gzipped world!']

        app = Gzipper(test_app, compresslevel=8)
        httpd = WSGIServer(('', 8080), WSGIRequestHandler)
        httpd.set_app(app)
        httpd.serve_forever()
'''


from gzip import GzipFile
import cStringIO


__version__ = '1.0.1'


def compress(data, compression_level):
    ''' The `gzip` module didn't provide a way to gzip just a string.
        Had to hack together this. I know, it isn't pretty.
    '''
    buffer = cStringIO.StringIO()
    gz_file = GzipFile(None, 'wb', compression_level, buffer)
    gz_file.write(data)
    gz_file.close()
    return buffer.getvalue()


def parse_encoding_header(header):
    ''' Break up the `HTTP_ACCEPT_ENCODING` header into a dict of
        the form, {'encoding-name':qvalue}.
    '''
    encodings = {'identity': 1.0}
    for encoding in header.split(','):
        if encoding.find(';') > -1:
            encoding, qvalue = encoding.split(';')
            encoding = encoding.strip()
            qvalue = qvalue.split('=', 1)[1]
            if qvalue != '':
                encodings[encoding] = float(qvalue)
            else:
                encodings[encoding] = 1
        else:
            encodings[encoding] = 1
    return encodings


def client_wants_gzip(accept_encoding_header):
    ''' Check to see if the client can accept gzipped output, and whether
        or not it is even the preferred method. If `identity` is higher, then
        no gzipping should occur.
    '''
    encodings = parse_encoding_header(accept_encoding_header)
    if 'gzip' in encodings:
        return encodings['gzip'] >= encodings['identity']
    elif '*' in encodings:
        return encodings['*'] >= encodings['identity']
    else:
        return False


DEFAULT_COMPRESSABLES = set(['text/plain', 'text/html', 'text/css',
'application/json', 'application/x-javascript', 'text/xml',
'application/xml', 'application/xml+rss', 'text/javascript'])


class Gzipper(object):
    ''' WSGI middleware to wrap around and gzip all output.
        This automatically adds the content-encoding header.
    '''
    def __init__(self, app, content_types=DEFAULT_COMPRESSABLES,
        compresslevel=6):
        self.app = app
        self.content_types = content_types
        self.compresslevel = compresslevel

    def __call__(self, environ, start_response):
        ''' Do the actual work. If the host doesn't support gzip
            as a proper encoding,then simply pass over to the
            next app on the wsgi stack.
        '''
        if not client_wants_gzip(environ.get('HTTP_ACCEPT_ENCODING', '')):
            return self.app(environ, start_response)

        buffer = {'to_gzip': False, 'body': ''}

        def _write(body):
            # for WSGI compliance
            buffer['body'] = body

        def _start_response(status, headers, exc_info=None):
            ''' Wrapper around the original `start_response` function.
                The sole purpose being to add the proper headers automatically.
            '''
            for header in headers:
                field = header[0].lower()
                if field == 'content-encoding':
                    # if the content is already encoded, don't compress
                    buffer['to_gzip'] = False
                    break
                elif field == 'content-type':
                    ctype = header[1].split(';')[0]
                    if ctype in self.content_types and not(\
                        'msie' in environ.get('HTTP_USER_AGENT', '').lower()\
                        and 'javascript' in ctype):
                        buffer['to_gzip'] = True

            buffer['status'] = status
            buffer['headers'] = headers
            buffer['exc_info'] = exc_info
            return _write

        data = self.app(environ, _start_response)

        if buffer['status'].startswith('200 ') and buffer['to_gzip']:
            data = ''.join(data)
            if len(data) > 200:
                data = compress(data, self.compresslevel)
                headers = buffer['headers']
                headers.append(('Content-Encoding', 'gzip'))
                headers.append(('Vary', 'Accept-Encoding'))
                for i, header in enumerate(headers):
                    if header[0] == 'Content-Length':
                        headers[i] = ('Content-Length', str(len(data) +
                        len(buffer['body'])))
                        break
            data = [data]

        _writable = start_response(buffer['status'], buffer['headers'],
            buffer['exc_info'])

        if buffer['body']:
            _writable(buffer['body'])

        return data
