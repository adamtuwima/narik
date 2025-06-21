from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver
import json
import threading

replace_enabled = False
replace_url = ''
replace_html = ''
allowed_ip = None  # None — без ограничений по IP

PORT = 8080
CONTROL_PORT = 5000

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global replace_enabled, replace_url, replace_html, allowed_ip

        client_ip = self.client_address[0]

        # Проверяем IP (если установлен)
        if allowed_ip and client_ip != allowed_ip:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b'Forbidden: IP не разрешён')
            return

        # Подмена содержимого, если включено и URL совпадает
        if replace_enabled and replace_url in self.path:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(replace_html.encode('utf-8'))
            print(f"[INFO] Подмена для {client_ip} - {self.path}")
        else:
            # Для простоты возвращаем 404 (т.к. это базовый пример)
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

class ControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global replace_enabled, replace_url, replace_html, allowed_ip
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        data = {
            "enabled": replace_enabled,
            "url": replace_url,
            "html": replace_html,
            "allowed_ip": allowed_ip
        }
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_POST(self):
        global replace_enabled, replace_url, replace_html, allowed_ip
        length = int(self.headers.get('content-length', 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data)
        except:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Bad JSON')
            return

        replace_enabled = data.get('enabled', replace_enabled)
        replace_url = data.get('url', replace_url)
        replace_html = data.get('html', replace_html)
        allowed_ip = data.get('allowed_ip', allowed_ip)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({
            "enabled": replace_enabled,
            "url": replace_url,
            "html": replace_html,
            "allowed_ip": allowed_ip
        }).encode('utf-8'))

def run_proxy():
    print(f"Запуск proxy на порту {PORT}")
    with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
        httpd.serve_forever()

def run_control():
    print(f"Запуск control API на порту {CONTROL_PORT}")
    with socketserver.TCPServer(("", CONTROL_PORT), ControlHandler) as httpd:
        httpd.serve_forever()

if name == "main":
    t1 = threading.Thread(target=run_proxy, daemon=True)
    t2 = threading.Thread(target=run_control, daemon=True)
    t1.start()
    t2.start()
    print("Серверы запущены. CTRL+C для выхода.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nЗавершение работы.")