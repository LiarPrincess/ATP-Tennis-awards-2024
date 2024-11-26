import os
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from matplotlib.axes._axes import Axes
from typing import Literal, Union, Iterable, assert_never
from dataclasses import dataclass
from pypalettes import load_cmap
from api import Player

# MARK: Text


@dataclass
class Title:
    value: str


@dataclass
class Subtitle:
    value: str


@dataclass
class Paragraph:
    value: str


@dataclass
class Award:
    emoji: str
    text: str


@dataclass
class Space:
    count: int


@dataclass
class Table:

    @dataclass
    class Header:
        text: str
        is_player_column: bool = False

    Value = Union[str | int | Player]

    class Row:
        def __init__(self, values: list["Table.Value"] | None = None) -> None:
            self._values = values or []

        def add(self, value: "Table.Value"):
            self._values.append(value)

    def __init__(self, headers: list["Table.Header"] | None = None) -> None:
        self.rows = list[Table.Row]()
        self.headers = headers or []


# MARK: Chart


class Chart:
    "Single chart."

    class XAxis:
        def __init__(self, ax: Axes) -> None:
            self.ax = ax
            self.axis = self.ax.xaxis
            self.ax.set_xmargin(0)
            self.set_major_ticks(5)
            self.set_minor_ticks(1)

        def set_label(self, value: str):
            self.ax.set_xlabel(value)

        def set_major_ticks(self, value: int):
            self.axis.set_major_locator(MultipleLocator(value))

        def set_minor_ticks(self, value: int):
            self.axis.set_minor_locator(MultipleLocator(value))

    class YAxis:
        def __init__(self, ax: Axes) -> None:
            self.ax = ax
            self.axis = self.ax.yaxis
            self.ax.set_ymargin(0)

        def set_label(self, value: str):
            self.ax.set_ylabel(value)

        def set_major_ticks(self, value: int):
            self.axis.set_major_locator(MultipleLocator(value))

        def set_minor_ticks(self, value: int):
            self.axis.set_minor_locator(MultipleLocator(value))

    def __init__(self) -> None:
        self.fig, self.ax = plt.subplots(layout="constrained")
        self.x_axis = Chart.XAxis(self.ax)
        self.y_axis = Chart.YAxis(self.ax)

    def set_title(self, value: str):
        self.ax.set_title(value)

    def set_show_grid(self, value: bool):
        self.ax.grid(value)

    RGBA = tuple[float, float, float, float]

    def add_bar(
        self,
        x: int,
        height: int | float,
        *,
        bottom: int | float | None = None,
        color: RGBA | None = None,
    ):
        self.ax.bar(x, height, bottom=bottom, color=color)

    # https://matplotlib.org/stable/api/markers_api.html
    ScatterMarker = Literal[
        ".", "o", "v", "^", "<", ">", "s", "p", "P", "*", "+", "x", "X", "D", "|", "_"
    ]

    def add_scatter(
        self,
        x: int,
        y: int | float,
        *,
        marker: ScatterMarker | None = None,
        color: Literal["black"] | None = None,
        size: int | None = None,
    ):
        self.ax.scatter(x, y, s=size, c=color, marker=marker)

    def create_color_map(
        self, values: Iterable[int | float]
    ) -> dict[int | float, RGBA]:
        value_to_color = dict[int | float, Chart.RGBA]()
        values_sorted = sorted(values)
        values_len = len(values_sorted)
        cmap = load_cmap("Berry", cmap_type="continuous")

        for i, value in enumerate(values_sorted):
            x = i / values_len
            value_to_color[value] = cmap(x)

        return value_to_color

    def write_img(self, path: str, *, width: int):
        dpi = 100
        self.fig.set_dpi(dpi)
        self.fig.set_figwidth(width / dpi)
        self.fig.savefig(path)
        plt.close(self.fig)


# MARK: Page


class Page:

    # ChartElements = Union[BarChart, MirrorBarChart]
    Element = Union[Title, Subtitle, Paragraph, Award, Space, Table, Chart]

    def __init__(self) -> None:
        self._elements = list[Page.Element]()

    def add(self, element: Element):
        self._elements.append(element)

    def write_html(self, path: str, *, width: int):
        path_dir, path_name = os.path.split(path)
        path_name_without_extension, _ = os.path.splitext(path_name)

        elements_html = list[str]()
        chart_index = 1

        for e in self._elements:
            if isinstance(e, Title):
                elements_html.append(f"# {e.value}")
            elif isinstance(e, Subtitle):
                elements_html.append(f"## {e.value}")
            elif isinstance(e, Paragraph):
                elements_html.append(e.value)
            elif isinstance(e, Award):
                elements_html.append(f"{e.emoji} {e.text}")
            elif isinstance(e, Space):
                elements_html.append("\n" * e.count)

            elif isinstance(e, Table):

                def create_line(values: Iterable[str]) -> str:
                    joined = "|".join(values)
                    return "|" + joined + "|"

                lines = list[str]()
                lines.append(create_line(h.text for h in e.headers))
                lines.append(create_line("-" for h in e.headers))

                for r in e.rows:
                    values = list[str]()

                    for v in r._values:
                        if isinstance(v, str):
                            values.append(v)
                        elif isinstance(v, int):
                            values.append(str(v))
                        elif isinstance(v, Player):
                            assert v.rank is not None
                            flag = v.nationality.emoji
                            rank_pad = " " if v.rank < 10 else ""
                            values.append(
                                f"{rank_pad}{v.rank} {flag} {v.name_first} {v.name_last}"
                            )
                        else:
                            assert_never(v)

                    lines.append(create_line(values))

                joined = "\n".join(lines)
                elements_html.append(joined)

            elif isinstance(e, Chart):
                e_name = f"{path_name_without_extension}_chart_{chart_index}.png"
                e_path = os.path.join(path_dir, e_name)
                chart_index += 1

                e.write_img(e_path, width=width)
                elements_html.append(f"![{e_name}]({e_name})")

            else:
                assert_never(e)

        with open(path, mode="w", encoding="utf-8") as f:
            for e in elements_html:
                f.write(e)
                f.write("\n")
                f.write("\n")
