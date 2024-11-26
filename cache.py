import os


class Cache:
    def __init__(self, dir: str) -> None:
        self.dir = dir
        os.makedirs(dir, exist_ok=True)

    def get(self, key: str) -> str | None:
        path = self._get_path(key)

        try:
            with open(path, "r") as f:
                return f.read()
        except IOError:
            return None

    def put(self, key: str, value: str):
        path = self._get_path(key)

        with open(path, "w") as f:
            f.write(value)

    def _get_path(self, key: str) -> str:
        key = key.replace("/", "").replace(":", "").replace("&", "")
        return os.path.join(self.dir, key)
