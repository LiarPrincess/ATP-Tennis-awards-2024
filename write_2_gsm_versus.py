from typing import assert_never
from dataclasses import dataclass
from page import Page, Subtitle, Paragraph, Award, Table, Chart
from atp_api import (
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

_EMOJI_WIN = "🟢"
_EMOJI_LOSS = "🔴"


@dataclass
class _Row:

    MatchData = (
        PlayerMatch_Played
        | PlayerMatch_Walkover
        | PlayerMatch_Retire
        | PlayerMatch_Default
    )

    @dataclass
    class Match:
        tournament: PlayerTournament
        match: "_Row.MatchData"
        opponent: Player
        opponent_rank: int

    player: Player
    player_rank: int
    matches: list[Match]
    matches_against_top_N: list[Match]
    matches_against_top_N_win_count: int
    matches_against_top_N_loss_count: int

    @property
    def matches_against_top_N_len(self) -> int:
        return len(self.matches_against_top_N)


def write_game_set_match_versus(
    page: Page,
    players: list[Player],
    date_from: str,
    top_N: int,
    award_count_unluckiest: int,
):
    "Matrix who played with who."

    # MARK: Data

    rows = list[_Row]()
    id_to_player = {p.id: p for p in players}
    rank_lowest: int | None = None
    rank_highest: int | None = None

    for p in players:
        p_rank = p.rank
        assert p_rank is not None
        row = _Row(p, p_rank, [], [], 0, 0)
        rows.append(row)

        rank_lowest = max2(rank_lowest, p_rank)
        rank_highest = min2(rank_highest, p_rank)

        for t in p.career_tournaments:
            if t.date < date_from:
                continue

            for m in t.matches:
                if isinstance(m, _Row.MatchData):
                    o_id = m.opponent.id
                    o = id_to_player.get(o_id)

                    # None -> player not in the top 10/50/100 etc.
                    if o is not None:
                        assert o.rank is not None
                        match = _Row.Match(t, m, o, o.rank)
                        row.matches.append(match)

                        if o.rank <= top_N:
                            row.matches_against_top_N.append(match)

                            if m.win_loss == "W":
                                row.matches_against_top_N_win_count += 1
                            elif m.win_loss == "L":
                                row.matches_against_top_N_loss_count += 1
                            else:
                                assert_never(m.win_loss)

                elif isinstance(m, PlayerMatch_Bye | PlayerMatch_NotPlayed):
                    pass
                else:
                    assert_never(m)

    assert rank_lowest is not None
    assert rank_highest is not None
    rank_span = rank_lowest - rank_highest + 1

    # MARK: Chart

    date_from_short = substring_until(date_from, "T")
    page.add(Subtitle(f"Match count since {date_from_short}"))
    page.add(
        Paragraph(
            "All games, including Olympics etc. Only singles (as in 1 on 1 matches, not their marriage status)."
        )
    )

    chart = Chart()
    chart.set_show_grid(True)
    chart.set_aspect_rato(1.2, 1)
    page.add(chart)

    chart_data = [[0] * rank_span for _ in range(rank_span)]

    # Transpose to count per opponent
    for r in rows:
        # -1 for '0' indexing
        x = r.player_rank - 1

        for m in r.matches:
            y = m.opponent_rank - 1
            chart_data[x][y] += 1

    # 'pcolorfast' gives incorrect XY ticks
    ranks = range(rank_highest, rank_lowest + 1)
    heatmap = chart.add_heatmap(ranks, ranks, chart_data)
    chart.add_color_bar(heatmap, "Match count")

    # X axis
    x_axis = chart.x_axis
    x_axis.set_label("Player rank")

    # Y axis
    y_axis = chart.y_axis
    y_axis.set_label("Opponent rank")
    chart.y_axis.set_major_ticks(5)
    chart.y_axis.set_minor_ticks(1)

    # MARK: Awards

    page.add(
        Paragraph(
            f"Top {top_N} plays with each other very often, so we separated the awards."
        )
    )

    _write_luckiest_award(
        page=page,
        rows=rows,
        top_N=top_N,
    )

    _write_unluckiest_award(
        page=page,
        rows=rows,
        top_N=top_N,
        award_count=award_count_unluckiest,
    )

    _write_lovebirds_award(
        page=page,
        rows=rows,
        top_N=top_N,
    )


# MARK: Awards


def _write_luckiest_award(
    page: Page,
    rows: list[_Row],
    top_N: int,
):
    page.add(
        Award(
            "🐸",
            f"Frog award for the luckiest player - top {top_N} player with the least matches against the top {top_N}.",
        )
    )

    award_rows = [r for r in rows if r.player_rank <= top_N]
    award_rows.sort(key=lambda r: r.matches_against_top_N_len)

    table = Table()
    page.add(table)

    table.headers.append(Table.Header("Player", is_player_column=True))
    table.headers.append(Table.Header("Match count"))
    table.headers.append(Table.Header("Wins"))
    table.headers.append(Table.Header("Losses"))

    for r in award_rows:
        win = _to_str_match_count(r.matches_against_top_N_win_count, _EMOJI_WIN)
        loss = _to_str_match_count(r.matches_against_top_N_loss_count, _EMOJI_LOSS)
        row = Table.Row([r.player, r.matches_against_top_N_len, win, loss])
        table.rows.append(row)


def _write_unluckiest_award(
    page: Page,
    rows: list[_Row],
    top_N: int,
    award_count: int,
):
    rows_after_top_N = [r for r in rows if r.player_rank > top_N]
    award_rows = filter_award_max(
        rows_after_top_N,
        count=award_count,
        key=lambda r: r.matches_against_top_N_len,
    )

    page.add(
        Award(
            "🐖",
            f"Pig award for the unluckiest player - player outside of the top {top_N} with the most matches against the top {top_N}.",
        )
    )

    top_match_count = award_rows[0].matches_against_top_N_len

    for r in award_rows:
        if r.matches_against_top_N_len != top_match_count:
            break

        p = r.player
        p_s = to_str_player(p)

        if r.matches_against_top_N_win_count == 0:
            wins = ""
        elif r.matches_against_top_N_win_count == 1:
            wins = "1 win"
        else:
            wins = f"{r.matches_against_top_N_win_count} wins"

        if r.matches_against_top_N_loss_count == 0:
            losses = ""
        elif r.matches_against_top_N_loss_count == 1:
            losses = "1 lost"
        else:
            losses = f"{r.matches_against_top_N_loss_count} losses"

        if wins and losses:
            wins += ", "

        page.add(Paragraph(f"{p_s}: {wins}{losses}."))

        table = Table()
        page.add(table)

        table.headers.append(Table.Header("Opponent", is_player_column=True))
        table.headers.append(Table.Header("Win?"))
        table.headers.append(Table.Header("Result"))
        table.headers.append(Table.Header("Tournament"))
        table.headers.append(Table.Header("Round"))

        for m in r.matches_against_top_N:
            tournament = m.tournament.name
            round = m.match.round.id
            sets = to_str_sets(m.match)

            row = Table.Row(
                [
                    m.opponent,
                    _EMOJI_WIN if m.match.win_loss == "W" else _EMOJI_LOSS,
                    sets,
                    tournament,
                    round,
                ]
            )
            table.rows.append(row)

    page.add(Paragraph(f"Honorable mentions:"))

    table = Table()
    page.add(table)

    table.headers.append(Table.Header("Player", is_player_column=True))
    table.headers.append(Table.Header("Match count"))
    table.headers.append(Table.Header("Wins"))
    table.headers.append(Table.Header("Losses"))

    for r in award_rows:
        if r.matches_against_top_N_len != top_match_count:
            win = _to_str_match_count(r.matches_against_top_N_win_count, _EMOJI_WIN)
            loss = _to_str_match_count(r.matches_against_top_N_loss_count, _EMOJI_LOSS)
            row = Table.Row([r.player, r.matches_against_top_N_len, win, loss])
            table.rows.append(row)


def _write_lovebirds_award(
    page: Page,
    rows: list[_Row],
    top_N: int,
):
    page.add(
        Award(
            "🦢❤️🦢",
            f"Lovebird award for the most common pair outside of the top {top_N}.",
        )
    )

    # pair_id = concatenated player ids
    pair_id_to_matches = dict[str, list[tuple[_Row, _Row.Match]]]()

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

    match_lists = filter_award_max_NO_can_receive_award_check(
        list(pair_id_to_matches.values()),
        count=1,
        key=lambda r: len(r),
    )

    for matches in match_lists:
        r, m = matches[0]
        p_str = to_str_player(r.player)
        o_str = to_str_player(m.opponent)

        page.add(Paragraph(f"{p_str} 💏 {o_str}"))

        table = Table()
        page.add(table)

        table.headers.append(Table.Header("Winner", is_player_column=True))
        table.headers.append(Table.Header("Result"))
        table.headers.append(Table.Header("Tournament"))
        table.headers.append(Table.Header("Round"))

        winner_ids = list[str]()
        printed_count = 0

        for r, m in matches:
            win_loss = m.match.win_loss

            if win_loss == "L":
                continue

            assert win_loss == "W", win_loss

            winner = r.player
            winner_str = to_str_player(winner)
            winner_ids.append(winner.id)

            tournament = m.tournament.name
            round = m.match.round.id
            sets = to_str_sets(m.match)

            printed_count += 1

            row = Table.Row([winner_str, sets, tournament, round])
            table.rows.append(row)

        # We have matches for both sides.
        match_count = len(matches) // 2
        assert printed_count == match_count

        r, m = matches[0]
        p1 = r.player
        p2 = m.opponent

        p1_win_count = winner_ids.count(p1.id)
        p2_win_count = winner_ids.count(p2.id)
        assert p1_win_count + p2_win_count == match_count

        min_to_top = match_count * 2 / 3

        if p1_win_count > min_to_top:
            p1_str = to_str_player(p1)
            page.add(Paragraph(f'{p1_str} is truly a "top" in this relationship.'))
        elif p2_win_count > min_to_top:
            p2_str = to_str_player(p2)
            page.add(Paragraph(f'{p2_str} is truly a "top" in this relationship.'))
        else:
            page.add(
                Paragraph(f"We hope they created a lot of happy memories together!")
            )


# MARK: Helpers


def _to_str_match_count(count: int, emoji: str) -> str:
    result = ""

    for i in range(count):
        if i % 3 == 0:
            result += "  "

        result += emoji

    return result
