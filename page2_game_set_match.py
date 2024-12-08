from typing import assert_never
from dataclasses import dataclass
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
from chart import Chart
from helpers import *


@dataclass
class Page:

    @dataclass
    class Row:

        MatchData = (
            PlayerMatch_Played
            | PlayerMatch_Walkover
            | PlayerMatch_Retire
            | PlayerMatch_Default
        )

        @dataclass
        class Match:
            tournament: PlayerTournament
            match: "Page.Row.MatchData"
            opponent: Player
            opponent_rank: int
            result: str

        player: Player
        player_rank: int
        matches: list[Match]
        top_N_matches: list[Match]
        top_N_win_count: int
        top_N_loss_count: int

        @property
        def top_N_count(self) -> int:
            return len(self.top_N_matches)

    @dataclass
    class LoveRow:

        @dataclass
        class Match:
            tournament: PlayerTournament
            match: "Page.Row.MatchData"
            winner: Player
            result: str

        player1: Player
        player2: Player
        matches: list[Match]
        dominant_player: Player | None

    date_from: str
    top_N: int

    versus_chart: Chart
    versus_awards_lucky: list[Row]
    versus_awards_unlucky_main: list[Row]
    versus_awards_unlucky_honorable: list[Row]
    versus_awards_love: list[LoveRow]


def page2_game_set_match(
    players: list[Player],
    date_from: str,
    top_N: int,
    award_count_unlucky: int,
) -> Page:
    rows = _get_rows(players, date_from, top_N)
    date_from_short = substring_until(date_from, "T")
    versus_chart = _create_versus_chart(rows)

    versus_awards_lucky = [r for r in rows if r.player_rank <= top_N]
    versus_awards_lucky.sort(key=lambda r: r.top_N_count)

    unlucky_rows = filter_award_max(
        (r for r in rows if r.player_rank > top_N),
        count=award_count_unlucky,
        key=lambda r: r.top_N_count,
    )
    unlucky_rows_max = unlucky_rows[0].top_N_count
    versus_awards_unlucky_main = [
        r for r in unlucky_rows if r.top_N_count == unlucky_rows_max
    ]
    versus_awards_unlucky_honorable = [
        r for r in unlucky_rows if r.top_N_count != unlucky_rows_max
    ]

    versus_awards_love = _get_love_rows(rows, top_N)

    return Page(
        date_from=date_from_short,
        top_N=top_N,
        versus_chart=versus_chart,
        versus_awards_lucky=versus_awards_lucky,
        versus_awards_unlucky_main=versus_awards_unlucky_main,
        versus_awards_unlucky_honorable=versus_awards_unlucky_honorable,
        versus_awards_love=versus_awards_love,
    )


# MARK: Charts


def _create_versus_chart(rows: list[Page.Row]) -> Chart:
    chart = Chart()
    chart.set_show_grid(True)
    chart.set_aspect_rato(12, 10)

    rank_lowest = max(r.player_rank for r in rows)
    rank_highest = min(r.player_rank for r in rows)
    rank_span = rank_lowest - rank_highest + 1

    chart_data = [[0] * rank_span for _ in range(rank_span)]

    # Transpose to count per opponent
    for r in rows:
        # -1 for '0' indexing
        x = r.player_rank - 1

        for m in r.matches:
            y = m.opponent_rank - 1
            chart_data[x][y] += 1

    ranks = range(rank_highest, rank_lowest + 1)
    heatmap = chart.add_heatmap(ranks, ranks, chart_data)
    chart.add_color_bar(heatmap, "Match count")

    # X axis
    x_axis = chart.x_axis
    x_axis.set_label("Player rank")

    # Y axis
    y_axis = chart.y_axis
    y_axis.set_label("Opponent rank")
    chart.y_axis.set_major_tick_interval(5)
    chart.y_axis.set_minor_tick_interval(1)

    return chart


# MARK: Rows


def _get_rows(players: list[Player], date_from: str, top_N: int) -> list[Page.Row]:
    result = list[Page.Row]()
    id_to_player = {p.id: p for p in players}

    for p in players:
        p_rank = p.rank
        assert p_rank is not None
        row = Page.Row(p, p_rank, [], [], 0, 0)
        result.append(row)

        for t in p.career_tournaments:
            if t.date < date_from:
                continue

            for m in t.matches:
                if isinstance(m, Page.Row.MatchData):
                    o_id = m.opponent.id
                    o = id_to_player.get(o_id)

                    # None -> player not in the top 10/50/100 etc.
                    if o is None:
                        continue

                    assert o.rank is not None
                    m_result = to_str_match_result(m)
                    match = Page.Row.Match(t, m, o, o.rank, m_result)
                    row.matches.append(match)

                    if o.rank <= top_N:
                        row.top_N_matches.append(match)

                        if m.win_loss == "W":
                            row.top_N_win_count += 1
                        elif m.win_loss == "L":
                            row.top_N_loss_count += 1
                        else:
                            assert_never(m.win_loss)

                elif isinstance(m, PlayerMatch_Bye | PlayerMatch_NotPlayed):
                    pass
                else:
                    assert_never(m)

    return result


def _get_love_rows(rows: list[Page.Row], top_N: int) -> list[Page.LoveRow]:
    # pair_id = concatenated player ids
    pair_id_to_matches = dict[str, list[tuple[Page.Row, Page.Row.Match]]]()

    for r in rows:
        for m in r.matches:
            # Both of them need to be able to receive award
            can_receive_award = (
                r.player.can_receive_award and m.opponent.can_receive_award
            )

            if not can_receive_award:
                continue

            # Remove top N player pairs, as they play very often together.
            if r.player_rank <= top_N and m.opponent_rank <= top_N:
                continue

            p1_id, p2_id = sorted((r.player.id, m.opponent.id))
            pair_id = f"{p1_id}_{p2_id}"
            matches = pair_id_to_matches.get(pair_id)

            if matches is None:
                matches = []
                pair_id_to_matches[pair_id] = matches

            matches.append((r, m))

    result = list[Page.LoveRow]()
    max_len = max(len(mhs) for mhs in pair_id_to_matches.values())

    for matches in pair_id_to_matches.values():
        if len(matches) != max_len:
            continue

        r, m = matches[0]
        player = r.player
        opponent = m.opponent
        winner_ids = list[str]()

        love_row = Page.LoveRow(player, opponent, [], None)
        result.append(love_row)

        for r, m in matches:
            win_loss = m.match.win_loss

            if win_loss == "L":
                continue

            assert win_loss == "W", win_loss

            winner = r.player
            winner_ids.append(winner.id)
            match_result = to_str_match_result(m.match)
            lm = Page.LoveRow.Match(m.tournament, m.match, winner, match_result)
            love_row.matches.append(lm)

        # We have matches for both sides.
        match_count = len(matches) // 2
        match_count_to_top = match_count * 2 / 3  # 66%
        player_win_count = winner_ids.count(player.id)
        opponent_win_count = winner_ids.count(opponent.id)

        if player_win_count >= match_count_to_top:
            love_row.dominant_player = player

        if opponent_win_count >= match_count_to_top:
            love_row.dominant_player = opponent

    return result
