import sys
import importlib.util
import traceback
import tempfile
import os
from pathlib import Path

os.environ["PYTHAINLP_DATA_DIR"] = str(Path(tempfile.gettempdir()) / "pythainlp-data")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
try:
    MODULE_PATH = ROOT / "api.py"
    spec = importlib.util.spec_from_file_location("pantip_api", MODULE_PATH)
    pantip_api = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = pantip_api
    spec.loader.exec_module(pantip_api)
    fastapi_app = pantip_api.app
    import_error = None
except Exception as exc:
    fastapi_app = None
    import_error = f"{exc.__class__.__name__}: {exc}\n{traceback.format_exc()}"


class ApiPrefixMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in {"http", "websocket"}:
            path = scope.get("path", "")
            if path == "/api/index":
                scope["path"] = "/"
                scope["raw_path"] = b"/"
            elif path.startswith("/api/index/"):
                scope["path"] = path[len("/api/index"):]
                scope["raw_path"] = scope["path"].encode("utf-8")
            elif path == "/api":
                scope["path"] = "/"
                scope["raw_path"] = b"/"
            elif path.startswith("/api/"):
                scope["path"] = path[4:]
                scope["raw_path"] = scope["path"].encode("utf-8")
        if fastapi_app is None:
            if scope["type"] == "http":
                body = import_error.encode("utf-8")
                await send({
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [(b"content-type", b"text/plain; charset=utf-8"),
                                (b"content-length", str(len(body)).encode())],
                })
                await send({"type": "http.response.body", "body": body})
                return
        await self.app(scope, receive, send)


app = ApiPrefixMiddleware(fastapi_app)
