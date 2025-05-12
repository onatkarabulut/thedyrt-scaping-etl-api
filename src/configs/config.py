import yaml
from pathlib import Path

class Config:
    def __init__(self, path="src/configs/config.yaml"):
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        self._c = yaml.safe_load(p.read_text())

    @property
    def kafka(self):
        return self._c["kafka"]

    @property
    def api(self):
        return self._c["api"]

    @property
    def geocoder(self):
        return self._c["geocoder"]

    @property
    def database_url(self):
        return self._c["database"]["url"]

    @property
    def logging_level(self):
        return self._c["logging"]["level"]
