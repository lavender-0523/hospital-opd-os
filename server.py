"""
server.py
Zero-dependency lightweight HTTP & API Server for Hospital OPD OS Simulator.
Serves the web dashboard from ./web and provides JSON simulation endpoints.
"""

import http.server
import json
import os
import socketserver
import sys
import webbrowser
from hospital_os.patient import Patient
from hospital_os.schedulers import PreemptivePriorityScheduler, RoundRobinScheduler
from hospital_os.synchronization import run_concurrency_test

PORT = 8000
WEB_DIR = os.path.join(os.path.dirname(__file__), "web")


class HospitalOSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        if self.path == "/api/run-priority":
            raw_patients = data.get("patients", [])
            threshold = data.get("aging_threshold", 5)
            patient_objs = [
                Patient(
                    p["token_id"],
                    p["name"],
                    p.get("age", 30),
                    p["category"],
                    p["arrival_time"],
                    p["burst_time"],
                )
                for p in raw_patients
            ]
            scheduler = PreemptivePriorityScheduler(aging_threshold=threshold, verbose=False)
            res = scheduler.run(patient_objs)
            out = {
                "algorithm": res["algorithm"],
                "patients": [p.to_dict() for p in res["patients"]],
                "gantt": res["gantt"],
                "events": res["events"],
                "total_time": res["total_time"],
            }
            self.send_json_response(out)

        elif self.path == "/api/run-round-robin":
            raw_patients = data.get("patients", [])
            tq = data.get("time_quantum", 2)
            patient_objs = [
                Patient(
                    p["token_id"],
                    p["name"],
                    p.get("age", 30),
                    p["category"],
                    p["arrival_time"],
                    p["burst_time"],
                )
                for p in raw_patients
            ]
            scheduler = RoundRobinScheduler(time_quantum=tq, verbose=False)
            res = scheduler.run(patient_objs)
            out = {
                "algorithm": res["algorithm"],
                "patients": [p.to_dict() for p in res["patients"]],
                "gantt": res["gantt"],
                "events": res["events"],
                "total_time": res["total_time"],
            }
            self.send_json_response(out)

        elif self.path == "/api/concurrency":
            desks = data.get("desks", ["Desk-A", "Desk-B", "Desk-C"])
            res = run_concurrency_test(desks=desks, tokens_per_desk=2)
            self.send_json_response(res)
        else:
            self.send_error(404, "Endpoint Not Found")

    def send_json_response(self, data):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()


def start_server():
    server_address = ("", PORT)
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(server_address, HospitalOSRequestHandler) as httpd:
            print("=" * 65)
            print("  MediQueue OS • Hospital OPD Web Visualizer")
            print(f"  Server running live at: http://localhost:{PORT}")
            print("  Press Ctrl+C to terminate.")
            print("=" * 65)
            try:
                webbrowser.open(f"http://localhost:{PORT}")
            except Exception:
                pass
            httpd.serve_forever()
    except OSError as e:
        print(f"Port {PORT} already in use or error: {e}")
        # Try alternate port 8080
        alt_port = 8080
        with socketserver.TCPServer(("", alt_port), HospitalOSRequestHandler) as httpd:
            print(f"MediQueue OS server running at: http://localhost:{alt_port}")
            webbrowser.open(f"http://localhost:{alt_port}")
            httpd.serve_forever()


if __name__ == "__main__":
    start_server()
