"""Independent assistant + public preview. Run: python assistant_service.py

Production entry point: assistant_service:application (use a production WSGI server).
Only exported docs/ files can be served; .env, uploads, and databases cannot be served.
"""
import argparse
import json
import mimetypes
from pathlib import Path
from socketserver import ThreadingMixIn
from urllib.parse import unquote
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server
from assentag.assistant_engine import MAX_BODY, dispatch

PUBLIC = Path(__file__).resolve().parent / 'docs'
STATUS = {200: 'OK', 204: 'No Content', 400: 'Bad Request', 401: 'Unauthorized',
          403: 'Forbidden', 404: 'Not Found', 405: 'Method Not Allowed',
          413: 'Payload Too Large', 415: 'Unsupported Media Type', 429: 'Too Many Requests',
          500: 'Internal Server Error', 503: 'Service Unavailable', 504: 'Gateway Timeout'}


def application(environ, start_response):
    path, method = environ.get('PATH_INFO', '/'), environ.get('REQUEST_METHOD', 'GET')
    headers = {'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'same-origin'}
    if path.startswith('/api/assistant/'):
        try:
            length = int(environ.get('CONTENT_LENGTH') or 0)
        except ValueError:
            length = MAX_BODY + 1
        if length < 0 or length > MAX_BODY:
            status, data = 413, {'error': 'Your message is too large.'}
        else:
            request_headers = {key[5:].lower().replace('_', '-'): value for key, value in environ.items() if key.startswith('HTTP_')}
            request_headers['content-type'] = environ.get('CONTENT_TYPE', '')
            try:
                status, data, extra = dispatch(method, path, request_headers,
                                               environ['wsgi.input'].read(length), environ.get('REMOTE_ADDR', ''))
                headers.update(extra)
            except Exception:
                # Do not print provider or configuration exceptions containing credentials.
                status, data = 500, {'error': 'The assistant is unavailable. Please try again later.'}
        body = b'' if status == 204 else json.dumps(data).encode()
        headers['Content-Type'] = 'application/json; charset=utf-8'
    else:
        file = (PUBLIC / unquote(path).lstrip('/')).resolve()
        if file == PUBLIC:
            file = PUBLIC / 'index.html'
        safe = file.is_relative_to(PUBLIC) and not any(p.startswith('.') for p in file.relative_to(PUBLIC).parts)
        safe = safe and file.suffix.lower() in ('.html', '.css', '.js', '.json', '.png', '.jpg', '.jpeg', '.webp', '.svg', '.ico')
        if method not in ('GET', 'HEAD'):
            status, body = 405, b'Method not allowed'
        elif not safe or not file.is_file():
            status, body = 404, b'Not found'
        else:
            status, body = 200, file.read_bytes()
            headers['Content-Type'] = mimetypes.guess_type(file)[0] or 'application/octet-stream'
            headers['Cache-Control'] = 'no-cache'
    headers['Content-Length'] = str(len(body))
    start_response(f'{status} {STATUS[status]}', list(headers.items()))
    return [b'' if method == 'HEAD' else body]


class ThreadedServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class QuietHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass  # Chat content and access codes are never written to access logs.


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8030)
    args = parser.parse_args()
    print(f'AssentTag + assistant: http://127.0.0.1:{args.port}/login.html', flush=True)
    with make_server('127.0.0.1', args.port, application, ThreadedServer, QuietHandler) as server:
        server.serve_forever()
