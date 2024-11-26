import sys
from typing import Any, TypeVar

T = TypeVar("T")


class JSONDict:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data

    def get_str(self, key: str) -> str:
        return self._get(key, str)

    def get_str_or_none(self, key: str) -> str | None:
        return self._get_or_none(key, str)

    def get_int(self, key: str) -> int:
        return self._get(key, int)

    def get_int_or_none(self, key: str) -> int | None:
        return self._get_or_none(key, int)

    def get_bool(self, key: str) -> bool:
        return self._get(key, bool)

    def get_list(self, key: str) -> list:
        return self._get(key, list)

    def get_dict(self, key: str) -> "JSONDict":
        d = self._get(key, dict)
        return JSONDict(d)

    def get_dict_or_none(self, key: str) -> "JSONDict|None":
        d = self._get_or_none(key, dict)
        return JSONDict(d) if d is not None else None

    def _get(self, key: str, T: type[T]) -> T:
        o = self.data[key]
        assert isinstance(o, T), key
        return o

    def _get_or_none(self, key: str, T: type[T]) -> T | None:
        o = self.data.get(key)
        assert isinstance(o, T | None), key
        return o

    def dump_python_type(self, name: str):

        def camel_case(s: str) -> str:
            result = ""

            for c in s:
                if result and c.isupper():
                    result += "_"

                result += c

            return result.lower()

        print(f"class {name}:")
        print(f'    def __init__(self, json: "JSONDict") -> None:')

        for k, v in self.data.items():
            prop = camel_case(k)
            v_type = type(v).__name__
            print(f'        self.{prop} = json.get_{v_type}("{k}")')

        sys.exit(0)
