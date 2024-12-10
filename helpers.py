from typing import (
    Any,
    Iterator,
    Protocol,
    TypeVar,
    Callable,
    Generic,
    Iterable,
    assert_never,
)
from atp import (
    Player,
    PlayerMatch,
    PlayerMatch_Played,
    PlayerMatch_Walkover,
    PlayerMatch_Retire,
    PlayerMatch_Default,
    PlayerMatch_Bye,
    PlayerMatch_NotPlayed,
)

T = TypeVar("T")
U = TypeVar("U")


# MARK: Awards


class HasPlayer(Protocol):
    player: Player


THasPlayer = TypeVar("THasPlayer", bound=HasPlayer)


def filter_award_equal(
    iterable: Iterable[THasPlayer],
    key: Callable[[THasPlayer], bool],
) -> list[THasPlayer]:
    return [o for o in iterable if _can_receive_award(o) and key(o)]


def filter_award_min(
    iterable: Iterable[THasPlayer],
    count: int,
    key: Callable[[THasPlayer], Any],
) -> list[THasPlayer]:
    os = [o for o in iterable if _can_receive_award(o)]
    return _filter_award(os, count, key, is_max=False)


def filter_award_max(
    iterable: Iterable[THasPlayer],
    count: int,
    key: Callable[[THasPlayer], Any],
) -> list[THasPlayer]:
    os = [o for o in iterable if _can_receive_award(o)]
    return _filter_award(os, count, key, is_max=True)


def filter_award_min_NO_can_receive_award_check(
    iterable: Iterable[T],
    count: int,
    key: Callable[[T], Any],
) -> list[T]:
    return _filter_award(iterable, count, key, is_max=False)


def filter_award_max_NO_can_receive_award_check(
    iterable: Iterable[T],
    count: int,
    key: Callable[[T], Any],
) -> list[T]:
    return _filter_award(iterable, count, key, is_max=True)


def _filter_award(
    iterable: Iterable[T],
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


# MARK: String


def substring_until(s: str, until: str) -> str:
    try:
        index = s.index(until)
        return s[:index]
    except ValueError:
        return s


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


def average(xs: Iterable[int | float]) -> float:
    # Iterate only once!
    lst = list(xs)
    s = sum(lst)
    return 1.0 * s / len(lst)


# MARK: Collections


def find(os: Iterable[T], predicate: Callable[[T], bool]) -> T:
    result: T | None = None

    for o in os:
        if predicate(o):
            assert result is None, "Multiple matching"
            result = o

    assert result is not None, "No matching"
    return result


def group_by_key_id(os: list[T], key: Callable[[T], U]) -> list[tuple[U, list[T]]]:
    "Group objects based on id of the key object."
    id_u_to_pair = dict[int, tuple[U, list[T]]]()

    for o in os:
        u = key(o)
        id_u = id(u)
        pair = id_u_to_pair.get(id_u)

        if pair is None:
            pair = (u, list[T]())
            id_u_to_pair[id_u] = pair

        pair[1].append(o)

    return list(id_u_to_pair.values())
