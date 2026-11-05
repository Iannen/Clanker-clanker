#!/usr/bin/env python3
import http.server
import subprocess
import os
import sys
import ssl
import json
import urllib.request

def get_tailscale_ip():
    try:
        result = subprocess.run(
            ["tailscale", "ip", "-4"],
            capture_output=True,
            text=True,
            check=True
        )
        ip = result.stdout.strip()
        if not ip:
            raise ValueError("Tailscale returned an empty IP.")
        return ip
    except Exception as e:
        print(
            f"CRITICAL: Could not determine Tailscale IP. "
            f"Is Tailscale running? Error: {e}",
            file=sys.stderr
        )
        sys.exit(1)


def get_fqdn():
    try:
        result = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        dns_name = data.get("Self", {}).get("DNSName", "")
        if dns_name:
            return dns_name.rstrip(".")
    except Exception:
        pass

    return "gpu-box"


def enter_inference_mode():
    """Stop desktop components and start the llama-cpp inference service."""
    steps = [
        ["systemctl", "--user", "stop", "sunshine.service"],
        ["systemctl", "--user", "stop", "graphical-session.target"],
        ["systemctl", "--user", "stop", "plasma-workspace.target"],
        ["systemctl", "--user", "stop", "plasma-session.scope"],
        [
            "pkill",
            "-u",
            os.environ.get("USER", "user"),
            "-f",
            "kwin_wayland"
        ],
        [
            "pkill",
            "-u",
            os.environ.get("USER", "user"),
            "-f",
            "startplasma-wayland"
        ],
        ["systemctl", "--user", "reset-failed"],
        ["systemctl", "--user", "start", "llama-cpp.service"],
    ]

    for cmd in steps:
        try:
            subprocess.run(cmd, capture_output=True)
        except Exception as e:
            print(
                f"WARNING: Inference-mode step failed: {cmd} ({e})",
                file=sys.stderr
            )

    print(
        "Inference mode active: desktop stopped, llama-cpp.service started.",
        file=sys.stderr
    )


PORT = 8787
TAILSCALE_IP = get_tailscale_ip()
FQDN = get_fqdn()
SHORTNAME = FQDN.split(".")[0]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
CERTS_DIR = os.path.join(BASE_DIR, "certs")
CERT_FILE = os.path.join(CERTS_DIR, f"{FQDN}.crt")
KEY_FILE = os.path.join(CERTS_DIR, f"{FQDN}.key")


class ControllerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_POST(self):
        if self.path == "/api/desktop-mode":
            subprocess.run(
                ["systemctl", "--user", "stop", "llama-cpp.service"],
                capture_output=True
            )
            subprocess.run(
                ["systemctl", "--user", "start", "sunshine.service"],
                capture_output=True
            )

            subprocess.Popen(
                [
                    "systemd-run",
                    "--user",
                    "--scope",
                    "--unit=plasma-session",
                    "--property=BindsTo=graphical-session.target",
                    "--property=After=graphical-session.target",
                    "startplasma-wayland"
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(
                b"Switched to Desktop Mode (Plasma + Sunshine ON)"
            )

        elif self.path == "/api/inference-mode":
            enter_inference_mode()

            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(
                b"Switched to Inference Mode (Desktop Killed, VRAM Purged)"
            )

        elif self.path == "/v1/chat/completions":
            content_length = int(self.headers.get("Content-Length", 0))
            body_data = self.rfile.read(content_length)

            target_url = "http://127.0.0.1:8080/v1/chat/completions"
            req_headers = {
                "Content-Type": "application/json",
                "Authorization": self.headers.get(
                    "Authorization",
                    "Bearer your-super-secret-key"
                )
            }

            try:
                upstream_req = urllib.request.Request(
                    target_url,
                    data=body_data,
                    headers=req_headers,
                    method="POST"
                )

                with urllib.request.urlopen(upstream_req) as upstream_resp:
                    self.send_response(upstream_resp.status)
                    self.send_header(
                        "Content-Type",
                        upstream_resp.headers.get(
                            "Content-Type",
                            "text/event-stream"
                        )
                    )
                    self.send_header("Cache-Control", "no-cache")
                    self.end_headers()

                    while True:
                        chunk = upstream_resp.read(1024)
                        if not chunk:
                            break

                        self.wfile.write(chunk)
                        self.wfile.flush()

            except Exception as e:
                self.send_response(502)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(
                    f"Proxy Error: Could not connect to llama-cpp server ({e})"
                    .encode()
                )

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")


if __name__ == "__main__":
    #enter_inference_mode()

    server = http.server.HTTPServer(
        (TAILSCALE_IP, PORT),
        ControllerHandler
    )

    if os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(
            certfile=CERT_FILE,
            keyfile=KEY_FILE
        )
        server.socket = context.wrap_socket(
            server.socket,
            server_side=True
        )

        print(
            f"HTTPS Server running at https://{SHORTNAME}:{PORT} "
            f"(FQDN: {FQDN}, bound to {TAILSCALE_IP})"
        )
    else:
        print(
            f"WARNING: TLS certificates not found at {CERTS_DIR}. "
            "Falling back to HTTP.",
            file=sys.stderr
        )
        print(f"HTTP Server running at http://{TAILSCALE_IP}:{PORT}")

    server.serve_forever()