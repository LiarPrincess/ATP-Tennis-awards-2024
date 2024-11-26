from typing import Any, Protocol, TypeVar, Callable
from atp_api import Player

# MARK: ABC

T = TypeVar("T")


class HasPlayer(Protocol):
    player: Player


THasPlayer = TypeVar("THasPlayer", bound=HasPlayer)

# MARK: Award


def filter_award_equal(
    iterable: list[THasPlayer],
    key: Callable[[THasPlayer], bool],
) -> list[THasPlayer]:
    return [o for o in iterable if _can_receive_award(o) and key(o)]


def filter_award_min(
    iterable: list[THasPlayer],
    count: int,
    key: Callable[[THasPlayer], Any],
) -> list[THasPlayer]:
    return _filter_award(iterable, count, key, reverse=False)


def filter_award_max(
    iterable: list[THasPlayer],
    count: int,
    key: Callable[[THasPlayer], Any],
) -> list[THasPlayer]:
    return _filter_award(iterable, count, key, reverse=True)


def _filter_award(
    iterable: list[THasPlayer],
    count: int,
    key: Callable[[THasPlayer], Any],
    reverse: bool,
) -> list[THasPlayer]:
    os = [(o, key(o)) for o in iterable if _can_receive_award(o)]
    os_sorted = sorted(os, key=lambda o: o[1], reverse=reverse)

    result = list[THasPlayer]()
    unique_keys = list[Any]()  # Multiple entries with the same key

    for o, k in os_sorted:
        is_key_equal_previous = unique_keys and unique_keys[-1] == k

        if not is_key_equal_previous:
            unique_keys.append(k)

        if len(unique_keys) > count:
            break

        result.append(o)

    return result


def _can_receive_award(o: HasPlayer) -> bool:
    return o.player.can_receive_award


# MARK: Math


def min2(lhs: T | None, rhs: T, property_name: str | None = None) -> T:
    if lhs is None:
        return rhs

    if property_name is None:
        l = lhs
        r = rhs
    else:
        l = getattr(lhs, property_name)
        r = getattr(rhs, property_name)

    return lhs if l <= r else rhs


def max2(lhs: T | None, rhs: T, property_name: str | None = None) -> T:
    if lhs is None:
        return rhs

    if property_name is None:
        l = lhs
        r = rhs
    else:
        l = getattr(lhs, property_name)
        r = getattr(rhs, property_name)

    return lhs if l >= r else rhs


def round_down(n: int, *, multiple_of: int) -> int:
    return (n // multiple_of) * multiple_of


# MARK String


def substring_until(s: str, until: str) -> str:
    try:
        index = s.index(until)
        return s[:index]
    except ValueError:
        return s
