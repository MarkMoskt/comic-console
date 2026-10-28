#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cola interface-contract stub.

Serves the landing page, one sample /api/status document, and 501 for every
other documented endpoint. No agent, memory, diary, channel or persona
runtime is included in this repository.
"""
import argparse
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

ROOT = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(ROOT, "web", "index.html")
STARTED = time.time()
MAX_BODY = 1 << 20

GET_ENDPOINTS = (
    "/api/diary",
    "/api/diary/list",
    "/api/diary/calendar",
    "/api/emotion/history",
    "/api/events",
    "/api/memory",
    "/api/traffic",
    "/api/chatlog",
    "/api/chatlog/list",
    "/api/login/poll",
)
POST_ENDPOINTS = (
    "/api/login/request",
    "/api/login/logout",
    "/api/chat",
    "/api/repair",
)


def status_doc():
    return {
        "name": "Cola",
        "series": "Comic",
        "version": "contract-only",
        "service": "stub",
        "implemented": False,
        "uptime_s": int(time.time() - STARTED),
        "rss_mb": 0,
        "channels": [
            {"id": "channel-a", "name": "Assistant A", "peer": "Owner A",
             "messages": 0, "today_messages": 0, "last_seen": ""},
            {"id": "channel-b", "name": "Assistant B", "peer": "Owner B",
             "messages": 0, "today_messages": 0, "last_seen": ""},
        ],
        "counts": {
            "messages": 0,
            "facts": 0,
            "memory_blocks": 0,
            "diary_entries": 0,
            "stickers": 0,
        },
        "diary": {"a": 0, "b": 0, "total": 0, "latest": ""},
        "note": "Sample document. Nothing behind it is implemented in this repository.",
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "ColaContract/1.0"

    def log_message(self, fmt, *args):
        print("[stub] " + (fmt % args), flush=True)

    def _send(self, code, body, ctype):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
                   "application/json; charset=utf-8")

    def _not_implemented(self, path):
        self._json(501, {
            "error": "not_implemented",
            "endpoint": path,
            "docs": "docs/API.md",
            "message": "接口约定已公开，实现请自行完成。",
        })

    def _route(self):
        path = urlsplit(self.path).path.rstrip("/") or "/"
        if self.command in ("GET", "HEAD"):
            if path in ("/", "/index.html"):
                try:
                    with open(INDEX, "rb") as f:
                        self._send(200, f.read(), "text/html; charset=utf-8")
                except OSError:
                    self._send(500, "landing page missing\n", "text/plain; charset=utf-8")
                return
            if path == "/api/status":
                self._json(200, status_doc())
                return
            if path in GET_ENDPOINTS:
                self._not_implemented(path)
                return
        else:
            length = int(self.headers.get("Content-Length") or 0)
            if 0 < length <= MAX_BODY:
                self.rfile.read(length)
            if path in POST_ENDPOINTS:
                self._not_implemented(path)
                return
            if path in GET_ENDPOINTS or path == "/api/status":
                self._json(405, {"error": "method_not_allowed", "endpoint": path})
                return
        if path.startswith("/api/"):
            self._json(404, {"error": "not_found", "endpoint": path,
                             "docs": "docs/API.md"})
        else:
            self._send(404, "not found\n", "text/plain; charset=utf-8")

    do_GET = _route
    do_POST = _route
    do_HEAD = _route


def main():
    ap = argparse.ArgumentParser(description="Cola interface-contract stub")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8088)
    args = ap.parse_args()
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print("Cola contract stub on http://%s:%d  (Ctrl+C to stop)" % (args.host, args.port))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
