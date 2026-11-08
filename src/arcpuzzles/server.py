"""Read-only HTTP API over the same catalog used by the CLI."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from urllib.parse import parse_qs, unquote, urlsplit

from .catalog import Catalog


def make_server(catalog: Catalog, host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    """Construct a server; only calling serve_forever starts serving requests."""
    class Handler(BaseHTTPRequestHandler):
        def respond(self, status: int, data: dict) -> None:
            body = (json.dumps(data, ensure_ascii=False) + "\n").encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            url = urlsplit(self.path)
            try:
                params = parse_qs(url.query, keep_blank_values=True)
                if any(len(values) != 1 for values in params.values()):
                    raise ValueError("Each query parameter must occur once")
                query = {key: value[0] for key, value in params.items()}
                if url.path == "/health":
                    if query:
                        raise ValueError("Health endpoint takes no parameters")
                    self.respond(200, {"status": "ok", "api": "arcpuzzles/v1"})
                elif url.path == "/v1/stats":
                    if query:
                        raise ValueError("Stats endpoint takes no parameters")
                    self.respond(200, catalog.stats())
                elif url.path == "/v1/puzzles":
                    allowed = {"approved", "source", "skill", "primitive", "difficulty", "kind", "train_safety",
                               "search", "has_generator", "family", "split", "limit", "offset", "sample", "seed"}
                    unknown = set(query) - allowed
                    if unknown:
                        raise ValueError(f"Unknown filters: {', '.join(sorted(unknown))}")
                    for key in {"approved", "has_generator"} & query.keys():
                        if query[key] not in {"true", "false"}:
                            raise ValueError(f"{key} must be true or false")
                        query[key] = query[key] == "true"
                    for key in {"limit", "offset", "sample", "seed"} & query.keys():
                        query[key] = int(query[key])
                    query.setdefault("limit", 50)
                    if query["limit"] > 1000:
                        raise ValueError("HTTP limit cannot exceed 1000; paginate with offset")
                    items = catalog.query(**query)
                    self.respond(200, {"items": items, "count": len(items), "limit": query["limit"], "offset": query.get("offset", 0)})
                elif url.path.startswith("/v1/puzzles/"):
                    parts = unquote(url.path[len("/v1/puzzles/"):]).split("/")
                    if len(parts) == 2 and parts[1] == "challenge":
                        if set(query) - {"variant"}:
                            raise ValueError("Challenge accepts only variant")
                        self.respond(200, catalog.challenge(parts[0], variant=int(query.get("variant", "0"))))
                    elif len(parts) == 1 and parts[0]:
                        if query:
                            raise ValueError("Puzzle detail takes no parameters")
                        self.respond(200, catalog.get(parts[0]))
                    else:
                        self.respond(404, {"error": "Unknown endpoint"})
                else:
                    self.respond(404, {"error": "Unknown endpoint"})
            except KeyError as exc:
                self.respond(404, {"error": str(exc)})
            except (ValueError, TypeError) as exc:
                self.respond(400, {"error": str(exc)})
            except (OSError, RuntimeError) as exc:
                self.respond(500, {"error": str(exc)})

    return ThreadingHTTPServer((host, port), Handler)
