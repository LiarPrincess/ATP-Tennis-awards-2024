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

# MARK: Str


def to_str_player(p: Player) -> str:
    return f"{p.rank} {p.nationality.flag_emoji} {p.name_first} {p.name_last}"


def to_str_sets(m: PlayerMatch) -> str:
    if isinstance(m, PlayerMatch_Bye):
        return "Bye"

    if isinstance(m, PlayerMatch_NotPlayed):
        return "Not played"

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
U = TypeVar("U")


class HasPlayer(Protocol):
    player: Player


THasPlayer = TypeVar("THasPlayer", bound=HasPlayer)

# MARK: Award


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
    return 1.0 * sum(lst) / len(lst)


# MARK String


def substring_until(s: str, until: str) -> str:
    try:
        index = s.index(until)
        return s[:index]
    except ValueError:
        return s


# MARK: Collections


class groupby(Generic[T, U]):
    "'itertools.groupby' requires sorted data"

    def __init__(self, iterable: list[T], key: Callable[[T], U]):
        self._data = dict[U, list[T]]()

        for o in iterable:
            k = key(o)
            group = self._data.get(k)

            if group is None:
                self._data[k] = [o]
            else:
                group.append(o)

    def __iter__(self) -> Iterator[tuple[U, list[T]]]:
        c = self._data.items()
        return iter(c)
