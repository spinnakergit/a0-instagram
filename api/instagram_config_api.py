"""API endpoint: Get/set Instagram plugin configuration.
URL: POST /api/plugins/instagram/instagram_config_api
"""
import json
import yaml
from pathlib import Path
from helpers.api import ApiHandler, Request, Response


def _get_config_path() -> Path:
    """Find the writable config path."""
    candidates = [
        Path(__file__).parent.parent / "config.json",
        Path("/a0/usr/plugins/instagram/config.json"),
        Path("/a0/plugins/instagram/config.json"),
    ]
    for p in candidates:
        if p.parent.exists():
            return p
    return candidates[-1]


class InstagramConfigApi(ApiHandler):

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    @classmethod
    def requires_csrf(cls) -> bool:
        return True

    async def process(self, input: dict, request: Request) -> dict | Response:
        action = input.get("action", "get")
        if request.method == "GET" or action == "get":
            return self._get_config()
        else:
            return self._set_config(input)

    def _get_config(self) -> dict:
        try:
            config_path = _get_config_path()
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = json.load(f)
            else:
                default_path = config_path.parent / "default_config.yaml"
                if default_path.exists():
                    with open(default_path, "r") as f:
                        config = yaml.safe_load(f) or {}
                else:
                    config = {}

            # Mask sensitive values
            masked = json.loads(json.dumps(config))
            if masked.get("access_token"):
                token = masked["access_token"]
                if len(token) > 8:
                    masked["access_token"] = token[:3] + "****" + token[-3:]
                else:
                    masked["access_token"] = "********"

            return masked
        except Exception:
            return {"error": "Failed to read configuration."}

    def _set_config(self, input: dict) -> dict:
        try:
            config = input.get("config", input)
            if not config or config == {"action": "set"}:
                return {"error": "No config provided"}
            config.pop("action", None)

            config_path = _get_config_path()
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Merge with existing (preserve masked tokens)
            existing = {}
            if config_path.exists():
                with open(config_path, "r") as f:
                    existing = json.load(f)

            new_token = config.get("access_token", "")
            if new_token and "****" in new_token:
                config["access_token"] = existing.get("access_token", "")

            # Merge: new values override existing
            existing.update(config)

            # Atomic write
            import os
            tmp = config_path.with_suffix(".tmp")
            fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            try:
                with os.fdopen(fd, "w") as f:
                    json.dump(existing, f, indent=2)
            except Exception:
                os.unlink(str(tmp))
                raise
            os.replace(str(tmp), str(config_path))

            return {"ok": True}
        except Exception:
            return {"error": "Failed to save configuration."}
