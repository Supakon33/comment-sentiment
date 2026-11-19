import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
MODULE_PATH = ROOT / "api.py"
spec = importlib.util.spec_from_file_location("pantip_api", MODULE_PATH)
pantip_api = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pantip_api
spec.loader.exec_module(pantip_api)
fastapi_app = pantip_api.app


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
        await self.app(scope, receive, send)


app = ApiPrefixMiddleware(fastapi_app)
