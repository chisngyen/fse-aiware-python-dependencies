#!/usr/bin/env python3
# Server tĩnh cho app Q&A hybrid (vector + lexical), chạy offline.
# Gửi header cross-origin-isolation để onnxruntime-web (WASM threads) chạy được.
import http.server, socketserver, webbrowser, threading, sys, os

PORT = 8000
os.chdir(os.path.dirname(os.path.abspath(__file__)))

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()
    def guess_type(self, path):
        if path.endswith('.wasm'): return 'application/wasm'
        if path.endswith('.mjs') or path.endswith('.js'): return 'text/javascript'
        return super().guess_type(path)
    def log_message(self, *a): pass

def open_browser():
    webbrowser.open(f'http://localhost:{PORT}/index.html')

if __name__ == '__main__':
    try:
        socketserver.TCPServer.allow_reuse_address = True
        httpd = socketserver.TCPServer(('127.0.0.1', PORT), Handler)
    except OSError:
        print(f'Cổng {PORT} đang bận. Mở sẵn: http://localhost:{PORT}/index.html')
        sys.exit(1)
    print(f'>> App Q&A chạy tại http://localhost:{PORT}/index.html')
    print('>> Lần đầu sẽ nạp model ~112MB (vài giây). Nhấn Ctrl+C để tắt.')
    threading.Timer(1.2, open_browser).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nĐã tắt server.')
