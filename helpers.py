from typing import Any, Protocol, TypeVar, Callable, assert_never
from atp_api import (
    Player,
    PlayerMatch,
    PlayerMatch_Played,
    PlayerMatch_Walkover,
    PlayerMatch_Retire,
    PlayerMatch_Default,
    PlayerMatch_Bye,
    PlayerMatch_NotPlayed,
)

# MARK: Str


def to_str_player(p: Player) -> str:
    return f"{p.rank} {p.nationality.flag_emoji} {p.name_first} {p.name_last}"


def to_str_sets(m: PlayerMatch) -> str:
    if isinstance(m, PlayerMatch_Bye):
        return ""

    if isinstance(m, PlayerMatch_NotPlayed):
        return ""

    if isinstance(m, PlayerMatch_Walkover):
        return "Walkover"

    if isinstance(m, PlayerMatch_Played | PlayerMatch_Retire | PlayerMatch_Default):
        result = ""

        for s in m.sets:
            if s:
                result += " "

            if m.win_loss == "W":
                result += str(s.player)
                result += str(s.opponent)
            elif m.win_loss == "L":
                result += str(s.opponent)
                result += str(s.player)
            else:
                assert_never(m.win_loss)

            if s.tie_break:
                result += f"({s.tie_break})"

        return result

    assert_never(m)


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
    os = [o for o in iterable if _can_receive_award(o)]
    return _filter_award(os, count, key, is_max=False)


def filter_award_max(
    iterable: list[THasPlayer],
    count: int,
    key: Callable[[THasPlayer], Any],
) -> list[THasPlayer]:
    os = [o for o in iterable if _can_receive_award(o)]
    return _filter_award(os, count, key, is_max=True)


def filter_award_min_NO_can_receive_award_check(
    iterable: list[T],
    count: int,
    key: Callable[[T], Any],
) -> list[T]:
    return _filter_award(iterable, count, key, is_max=False)


def filter_award_max_NO_can_receive_award_check(
    iterable: list[T],
    count: int,
    key: Callable[[T], Any],
) -> list[T]:
    return _filter_award(iterable, count, key, is_max=True)


def _filter_award(
    iterable: list[T],
    count: int,
    key: Callable[[T], Any],
    is_max: bool,
) -> list[T]:
    os = [(o, key(o)) for o in iterable]
    os_sorted = sorted(os, key=lambda o: o[1], reverse=is_max)

    result = list[T]()
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
