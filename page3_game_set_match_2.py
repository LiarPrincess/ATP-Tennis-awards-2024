from typing import assert_never
from dataclasses import dataclass
from chart import Chart
from atp import (
    Player,
    PlayerTournament,
    PlayerMatch_Played,
    PlayerMatch_Walkover,
    PlayerMatch_Retire,
    PlayerMatch_Default,
    PlayerMatch_Bye,
    PlayerMatch_NotPlayed,
)
from helpers import *


@dataclass
class Page:

    @dataclass
    class HighestDefeatedRow:

        Data = (
            PlayerMatch_Played
            | PlayerMatch_Walkover
            | PlayerMatch_Retire
            | PlayerMatch_Default
        )

        tournament: PlayerTournament
        match: "Page.HighestDefeatedRow.Data"

        player: Player
        player_rank: int
        opponent: Player
        opponent_rank: int

        @property
        def rank_diff(self) -> int:
            return self.player_rank - self.opponent_rank

    @dataclass
    class GameCountRow:
        player: Player
        player_rank: int
        game_win_count: int
        game_win_tie_break_count: int
        game_lost_count: int
        game_lost_tie_break_count: int

        @property
        def count_all(self) -> int:
            return (
                self.game_win_count
                + self.game_win_tie_break_count
                + self.game_lost_count
                + self.game_lost_tie_break_count
            )

    date_from: str
    player_no_1: Player

    highest_defeated_chart: Chart
    highest_defeated_awards: list[HighestDefeatedRow]
    giant_slayer: Player | None
    defeated_no_1_awards: list[HighestDefeatedRow]

    game_count_chart: Chart
    game_count_awards_max: list[GameCountRow]
    game_count_awards_min: list[GameCountRow]


def page3_game_set_match_2(
    players: list[Player],
    date_from: str,
    award_count_highest_defeated: int,
    award_count_game_count: int,
) -> Page:
    date_from_short = substring_until(date_from, "T")
    player_no_1 = find(players, lambda r: r.rank == 1)

    highest_defeated_rows = _get_highest_defeated_rows(players, date_from)
    highest_defeated_chart = _highest_defeated_chart(highest_defeated_rows)
    highest_defeated_awards, giant_slayer = _get_highest_defeated_awards(
        highest_defeated_rows,
        award_count_highest_defeated,
    )

    defeated_no_1_awards = [
        r
        for r in highest_defeated_rows
        if r.player.can_receive_award and r.opponent_rank == 1
    ]
    defeated_no_1_awards.sort(key=lambda r: r.tournament.date)

    game_count_rows = _get_game_count_rows(players, date_from)
    game_count_chart = _game_count_chart(game_count_rows)
    game_count_awards_max = filter_award_max(
        game_count_rows,
        count=award_count_game_count,
        key=lambda r: r.count_all,
    )
    game_count_awards_min = filter_award_min(
        game_count_rows,
        count=award_count_game_count,
        key=lambda r: r.count_all,
    )

    return Page(
        date_from=date_from_short,
        player_no_1=player_no_1,
        highest_defeated_chart=highest_defeated_chart,
        giant_slayer=giant_slayer,
        highest_defeated_awards=highest_defeated_awards,
        defeated_no_1_awards=defeated_no_1_awards,
        game_count_chart=game_count_chart,
        game_count_awards_max=game_count_awards_max,
        game_count_awards_min=game_count_awards_min,
    )


# MARK: Charts


def _highest_defeated_chart(matches: list[Page.HighestDefeatedRow]) -> Chart:
    chart = Chart()
    chart.set_show_grid(True)

    rank_to_highest_win = dict[int, int]()

    for m in matches:
        p = m.player_rank
        new = m.opponent_rank
        current = rank_to_highest_win.get(p)

        if current is None or new < current:
            rank_to_highest_win[p] = new

    ranks = list(rank_to_highest_win)
    highest_win = [rank_to_highest_win[r] for r in ranks]

    color_map = chart.create_color_map(highest_win, ["pink", "yellow"])
    colors = [color_map[b] for b in highest_win]
    chart.add_bar(ranks, highest_win, color=colors)

    # X axis
    x_axis = chart.x_axis
    x_axis.set_label("Player rank")

    # Y axis
    y_axis = chart.y_axis
    y_axis.set_label("Opponent rank")
    y_axis.set_major_tick_interval(2)

    return chart


def _game_count_chart(rows: list[Page.GameCountRow]) -> Chart:
    chart = Chart()
    chart.set_show_grid(True)

    ranks = [r.player_rank for r in rows]

    def add_bars(
        count: list[int],
        tie_count: list[int],
        colors: list[Chart.ColorLiteral],
    ):
        color_map = chart.create_color_map(count, colors)
        color = [color_map[c] for c in count]
        chart.add_bar(ranks, count, color=color)

        # Ties are always white
        color_map = chart.create_color_map(tie_count, ["foreground"])
        color = [color_map[c] for c in tie_count]
        chart.add_bar(ranks, tie_count, bottom=count, color=color)

    count = [r.game_win_count for r in rows]
    tie_count = [r.game_win_tie_break_count for r in rows]
    add_bars(count, tie_count, ["pink", "yellow"])

    count = [-r.game_lost_count for r in rows]
    tie_count = [-r.game_lost_tie_break_count for r in rows]
    add_bars(count, tie_count, ["cyan", "purple"])

    chart.add_legend(["Win", "Win tie-break", "Loss", "Loss tie-break"])

    # X axis
    x_axis = chart.x_axis
    x_axis.set_label("Player rank")

    # Y axis
    y_axis = chart.y_axis
    y_axis.set_label("Game count")

    y_max = [r.count_all for r in rows]
    y_axis.set_major_tick_count(y_max, 10, multiple_of=200)

    return chart


# MARK: Awards


def _get_highest_defeated_awards(
    rows: list[Page.HighestDefeatedRow],
    award_count: int,
):
    award_rows = [
        r
        for r in rows
        if r.player.can_receive_award
        and r.opponent.can_receive_award
        and r.rank_diff > 0
    ]
    award_rows = filter_award_max(
        award_rows,
        count=award_count,
        key=lambda r: r.rank_diff,
    )

    player_rows = group_by_key_id(award_rows, key=lambda r: r.player)
    player_max_count = max(len(lst) for _, lst in player_rows)
    player_rows_with_max_count = [
        p for p, lst in player_rows if len(lst) == player_max_count
    ]

    giant_slayer = (
        player_rows_with_max_count[0] if len(player_rows_with_max_count) == 1 else None
    )

    return award_rows, giant_slayer


# MARK: Rows


def _get_highest_defeated_rows(
    players: list[Player],
    date_from: str,
) -> list[Page.HighestDefeatedRow]:
    result = list[Page.HighestDefeatedRow]()
    id_to_player = {p.id: p for p in players}

    for p in players:
        p_rank = p.rank
        assert p_rank is not None

        for t in p.career_tournaments:
            if t.date < date_from:
                continue

            for m in t.matches:
                if m.win_loss == "W":
                    pass
                elif m.win_loss == "L":
                    continue
                else:
                    assert_never(m.win_loss)

                if isinstance(m, Page.HighestDefeatedRow.Data):
                    o_id = m.opponent.id
                    o = id_to_player.get(o_id)

                    if o is not None:
                        assert o.rank is not None
                        result.append(
                            Page.HighestDefeatedRow(t, m, p, p_rank, o, o.rank)
                        )

                elif isinstance(m, PlayerMatch_Bye | PlayerMatch_NotPlayed):
                    pass
                else:
                    assert_never(m)

    return result


def _get_game_count_rows(
    players: list[Player], date_from: str
) -> list[Page.GameCountRow]:
    result = list[Page.GameCountRow]()

    for p in players:
        p_rank = p.rank
        assert p_rank is not None
        row = Page.GameCountRow(p, p_rank, 0, 0, 0, 0)
        result.append(row)

        for t in p.career_tournaments:
            if t.date < date_from:
                continue

            for m in t.matches:
                if isinstance(
                    m,
                    PlayerMatch_Played | PlayerMatch_Retire | PlayerMatch_Default,
                ):
                    for s in m.sets:
                        row.game_win_count += s.player
                        row.game_lost_count += s.opponent

                        if s.tie_break is not None:
                            # 7:6
                            if s.player == 7:
                                assert s.opponent == 6
                                row.game_win_count -= 1
                                row.game_win_tie_break_count += 1
                            elif s.opponent == 7:
                                assert s.player == 6
                                row.game_lost_count -= 1
                                row.game_lost_tie_break_count += 1
                            # 1:0
                            elif s.player == 1:
                                assert s.opponent == 0
                                row.game_win_tie_break_count += 1
                            elif s.opponent == 1:
                                assert s.player == 0
                                row.game_lost_tie_break_count += 1
                            else:
                                assert False, "Tie-break requires 7:6 or 1:0"

                elif isinstance(
                    m,
                    PlayerMatch_Bye | PlayerMatch_NotPlayed | PlayerMatch_Walkover,
                ):
                    pass

                else:
                    assert_never(m)

    return result
