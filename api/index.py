"""Vercel entry point for the storefront's original page URLs."""
from urllib.parse import parse_qsl, urlencode, urlsplit
from server import Handler


class handler(Handler):
    def do_GET(self):
        request = urlsplit(self.path)
        params = parse_qsl(request.query, keep_blank_values=True)
        path = next((value for key, value in params if key == '__path'), request.path)
        if not path.startswith('/') or path.startswith('//'):
            self.send_error(400, 'Invalid storefront path')
            return
        query = urlencode([(key, value) for key, value in params if key != '__path'])
        self.path = path + ('?' + query if query else '')
        super().do_GET()
