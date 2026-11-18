"""Local storefront server with cached pages and on-demand public assets."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import argparse, json, urllib.error
from urllib.parse import urlsplit
from mirror import fetch, rewrite, ROOT

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path == '/replica.js':
                data=(ROOT/'replica.js').read_bytes(); typ='application/javascript'
            elif self.path == '/health':
                data=b'{"ok":true}'; typ='application/json'
            elif urlsplit(self.path).path == '/' and not urlsplit(self.path).query:
                # The committed homepage works on a cold serverless instance without network access.
                typ='text/html; charset=utf-8'
                data=rewrite((ROOT/'reference.html').read_bytes(),typ)
            else:
                data,typ=fetch(self.path)
                data=rewrite(data,typ)
            self.send_response(200)
            self.send_header('Content-Type',typ)
            self.send_header('Content-Length',str(len(data)))
            self.send_header('Cache-Control','public, max-age=3600' if '/cdn/' in self.path else 'no-cache')
            self.end_headers(); self.wfile.write(data)
        except urllib.error.HTTPError as e:
            self.send_error(e.code)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError): pass
        except Exception as e:
            print(str(e),flush=True); self.send_error(502,'Asset unavailable')

    def do_POST(self):
        # Demo pages must never forward customer information or orders to the source store.
        self.send_response(400)
        self.send_header('Content-Type','application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'description':'This is a local storefront replica. Live checkout and account services are not connected.'}).encode())

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--port',type=int,default=4173); args=p.parse_args()
    print(f'Amaris replica: http://localhost:{args.port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
