import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import datetime
import os

# Fixture data (example)
fixture_data = {
    "fixture_1": {"x": 1.0, "y": 2.0, "z": 3.0},
    "fixture_2": {"x": 4.0, "y": 5.0, "z": 6.0}
}

prev_data = fixture_data.copy()
new_data = fixture_data.copy()

HTTP_PORT = 5000
UDP_PORT = 37020
BROADCAST_INTERVAL = 5  # seconds
SAVE_DIR = "received_fixtures"

os.makedirs(SAVE_DIR, exist_ok=True)

#UDP broadcaster
def broadcast_ip():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        print("loop")
        ip = socket.gethostbyname(socket.gethostname())
        msg = json.dumps({"name" : "fixture_server", "ip" : ip, "port": HTTP_PORT})
        udp_socket.sendto(msg.encode(), ('<broadcast>', UDP_PORT))
        time.sleep(BROADCAST_INTERVAL)
        print(ip)

class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/fixtureData":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(fixture_data).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        global new_data, prev_data, fixture_data
        if self.path == "/fixtureData":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            prev_data = new_data.copy()
            new_data = json.loads(post_data)
            #global fixture_data
            #fixture_data = new_data
            print("Received new data:", new_data)

            #Save the data
            cur_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_name = f"fixtures_{cur_time}.json"
            file_path = os.path.join(SAVE_DIR, file_name)
            with open(file_path, 'w') as f:
                json.dump(new_data, f, indent=4)
            print(f"Saved received data to {file_path}")

            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


def read_fixture_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    print("File data: ", data)
    return data

if __name__ == "__main__":
    file_path = "fixtures.json"
    fixture_data = read_fixture_json(file_path)
    threading.Thread(target=broadcast_ip, daemon=True).start()
    print(f"📡 Broadcasting server IP every {BROADCAST_INTERVAL}s on UDP {UDP_PORT}")
    server = HTTPServer(("0.0.0.0", HTTP_PORT), FixtureHandler)
    server.serve_forever()