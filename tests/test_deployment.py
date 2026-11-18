import http.client
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from api.index import handler
from server import Handler


class DeploymentTests(unittest.TestCase):
    def test_rewrite_preserves_product_path_and_query(self):
        request = handler.__new__(handler)
        request.path = '/api?__path=%2Fproducts%2Fimperial-taj-earcuffs&variant=49835063672987'
        with patch.object(Handler, 'do_GET') as serve:
            request.do_GET()
        self.assertEqual(request.path, '/products/imperial-taj-earcuffs?variant=49835063672987')
        serve.assert_called_once()

    def test_root_rewrite(self):
        request = handler.__new__(handler)
        request.path = '/api?__path=/'
        with patch.object(Handler, 'do_GET'):
            request.do_GET()
        self.assertEqual(request.path, '/')

    def test_rejects_external_path(self):
        request = handler.__new__(handler)
        request.path = '/api?__path=//example.com'
        with patch.object(Handler, 'do_GET') as serve, patch.object(handler, 'send_error') as error:
            request.do_GET()
        error.assert_called_once_with(400, 'Invalid storefront path')
        serve.assert_not_called()

    def test_cold_instance_homepage_and_browser_script(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch('server.fetch', side_effect=AssertionError('Homepage must not depend on upstream')):
                client = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=30)
                client.request('GET', '/api?__path=/')
                response = client.getresponse()
                html = response.read().decode()
                self.assertEqual(response.status, 200)
                self.assertIn('Amaris Jewels', html)
                self.assertIn('src="/replica.js"', html)
                self.assertNotIn('//www.amarisjewels.com/cdn/', html)
                client.close()
                client = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=30)
                client.request('GET', '/api?__path=/replica.js')
                response = client.getresponse()
                self.assertEqual(response.status, 200)
                self.assertIn(b'amaris-preview-cart', response.read())
                client.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
