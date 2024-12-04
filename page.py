import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as pltColors
import matplotlib.ticker as pltTicker
import matplotlib.figure as pltFigure
import matplotlib.axes._axes as pltAxes
import matplotlib.collections as pltCollections
from pypalettes import load_cmap
from typing import Any, Literal, Union, Iterable, Sequence, Hashable, assert_never
from dataclasses import dataclass
from atp_api import Player

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

    Value = Union[str | int | Player | None]

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
        def __init__(self, ax: pltAxes.Axes) -> None:
            self.ax = ax
            self.axis = self.ax.xaxis
            self.ax.set_xmargin(0)
            self.set_major_ticks(5)
            self.set_minor_ticks(1)

        def set_label(self, value: str):
            self.ax.set_xlabel(value)

        def set_major_ticks(self, value: int):
            self.axis.set_major_locator(pltTicker.MultipleLocator(value))

        def set_minor_ticks(self, value: int):
            self.axis.set_minor_locator(pltTicker.MultipleLocator(value))

        def set_range(self, min: int | float, max: int | float):
            self.ax.set_xlim(min, max)

    class YAxis:
        def __init__(self, ax: pltAxes.Axes) -> None:
            self.ax = ax
            self.axis = self.ax.yaxis
            self.ax.set_ymargin(0)

        def set_label(self, value: str):
            self.ax.set_ylabel(value)

        def set_major_ticks(self, value: int):
            self.axis.set_major_locator(pltTicker.MultipleLocator(value))

        def set_minor_ticks(self, value: int):
            self.axis.set_minor_locator(pltTicker.MultipleLocator(value))

        def set_range(self, min: int | float, max: int | float):
            self.ax.set_ylim(min, max)

    def __init__(self) -> None:
        self.fig, self.ax = plt.subplots(layout="constrained")
        self.x_axis = Chart.XAxis(self.ax)
        self.y_axis = Chart.YAxis(self.ax)
        self._aspect_rato: tuple[int, int] | None = None

    def set_title(self, value: str):
        self.ax.set_title(value)

    def set_aspect_rato(self, width: int, height: int):
        "Aspect_rato 2:1 means 200px:100px."
        self._aspect_rato = (width, height)

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

    def add_bars(
        self,
        x: Sequence[int],
        height: Sequence[int | float],
        *,
        bottom: Sequence[int | float] | None = None,
        color: Sequence[RGBA] | None = None,
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

    def add_scatters(
        self,
        x: Sequence[int],
        y: Sequence[int | float],
        *,
        marker: ScatterMarker | None = None,
        color: Literal["black"] | None = None,
        size: int | None = None,
    ):
        self.ax.scatter(x, y, s=size, c=color, marker=marker)

    def add_legend(self, entries: list[str]):
        self.fig.legend(entries)

    @dataclass
    class Heatmap:
        im: pltCollections.Collection

    def add_heatmap(
        self,
        xs: Sequence[int],
        ys: Sequence[int],
        values: Sequence[Sequence[int | float]],
        *,
        shading: Literal["flat", "nearest", "auto"] | None = None,
    ) -> Heatmap:
        im = self.ax.pcolor(xs, ys, values, shading=shading)
        return Chart.Heatmap(im)

    def add_color_bar(self, heatmap: Heatmap, label: str | None = None):
        # https://python-graph-gallery.com/heatmap-for-timeseries-matplotlib/
        assert isinstance(self.ax.figure, pltFigure.Figure | pltFigure.SubFigure)
        cb = self.ax.figure.colorbar(heatmap.im, ax=self.ax)

        if label is not None:
            cb.ax.set_ylabel(label)

    def add_horizontal_line(
        self,
        y: int | float,
        x_start: int | float,
        x_end: int | float,
        /,
        color: Literal["black", "red"] = "black",
        line_width: int = 2,
    ):
        self.ax.hlines(
            y,
            x_start,
            x_end,
            colors=color,
            linewidth=line_width,
        )

    def add_vertical_line(
        self,
        x: int | float,
        y_start: int | float,
        y_end: int | float,
        /,
        color: Literal["black", "red"] = "black",
        line_width: int = 2,
    ):
        self.ax.vlines(
            x,
            y_start,
            y_end,
            colors=color,
            linewidth=line_width,
        )

    def create_color_map(
        self, values: Iterable[int | float]
    ) -> dict[int | float, RGBA]:
        values_sorted = sorted(set(values))
        values_len = len(values_sorted)

        value_to_color = dict[int | float, Chart.RGBA]()
        cmap = load_cmap("Berry", cmap_type="continuous")

        for i, value in enumerate(values_sorted):
            x = i / values_len
            value_to_color[value] = cmap(x)

        return value_to_color

    def write_img(self, path: str, *, width: int):
        _write_img(path, self.fig, width, self._aspect_rato)


# MARK: Map

# Data
# https://www.naturalearthdata.com/downloads/110m-cultural-vectors/
#
# Tutorials
# https://python-graph-gallery.com/web-map-europe-with-color-by-country/
# https://python-graph-gallery.com/web-map-with-custom-legend/
# https://www.geophysique.be/2011/01/27/matplotlib-basemap-tutorial-07-shapefiles-unleached/


class MapData:

    class Row:
        def __init__(
            self,
            data: gpd.GeoDataFrame,
            index: Hashable,
            row: pd.Series,
        ) -> None:
            self.data = data
            self.index = index
            self.row = row

        def __getitem__(self, name: str) -> Any:
            return self.data.at[self.index, name]

        def __setitem__(self, name: str, value: Any) -> None:
            self.data.at[self.index, name] = value

    def __init__(self, shp_path: str) -> None:
        data = gpd.read_file(shp_path)
        assert isinstance(data, gpd.GeoDataFrame)
        self.data = data

    def calculate_centroid(self, column_name: str):
        proj = self.data.to_crs(epsg=3035)
        assert isinstance(proj, gpd.GeoDataFrame)
        centroid = proj.geometry.centroid
        assert isinstance(centroid, gpd.GeoSeries)
        self.data[column_name] = centroid.to_crs(self.data.crs)

    def iter_rows(self) -> list[Row]:
        rows = self.data.iterrows()
        return [MapData.Row(self.data, i, r) for i, r in rows]


class Map:

    def __init__(self) -> None:
        self.fig, self.ax = plt.subplots(layout="constrained")
        self.ax.axis("off")
        self.ax.set_xmargin(0)
        self.ax.set_ymargin(0)
        self._aspect_rato: tuple[int, int] | None = None

    def set_aspect_rato(self, width: int, height: int):
        "Aspect_rato 2:1 means 200px:100px."
        self._aspect_rato = (width, height)

    def set_longitude_range(self, east: float, west: float):
        self.ax.set_xlim(east, west)

    def set_latitude_range(self, south: float, north: float):
        self.ax.set_ylim(south, north)

    def annotate(self, x: float, y: float, s: str):
        self.ax.annotate(
            s,
            (x, y),
            ha="center",
            va="center",
            fontsize=12,
            color="black",
        )

    def add_data(self, data: MapData, value_min: int | float, value_max: int | float):
        d = data.data
        cmap = load_cmap("Berry", cmap_type="continuous")
        norm = pltColors.Normalize(vmin=value_min, vmax=value_max)

        d.plot(
            ax=self.ax,
            column="VALUE",
            cmap=cmap,
            norm=norm,
            edgecolor="black",
            linewidth=0.2,
            legend=True,
        )

    def write_img(self, path: str, *, width: int):
        _write_img(path, self.fig, width, self._aspect_rato)


def _write_img(
    path: str,
    fig: pltFigure.Figure,
    width: int,
    aspect_rato: tuple[int, int] | None,
):

    dpi = 100
    fig.set_dpi(dpi)
    fig.set_figwidth(width / dpi)

    if aspect_rato is not None:
        # Aspect_rato 2:1 means 200px:100px, proportions
        # width  | aspect_width
        # height | aspect_height
        a_width, a_height = aspect_rato
        height = width * a_height / a_width
        fig.set_figheight(height / dpi)

    fig.savefig(path)
    plt.close(fig)


# MARK: Page


class Page:

    # ChartElements = Union[BarChart, MirrorBarChart]
    Element = Union[Title, Subtitle, Paragraph, Award, Space, Table, Chart, Map]

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
                            flag = v.nationality.flag_emoji
                            rank_pad = " " if v.rank < 10 else ""
                            values.append(
                                f"{rank_pad}{v.rank} {flag} {v.name_first} {v.name_last}"
                            )
                        elif v is None:
                            values.append("")
                        else:
                            assert_never(v)

                    lines.append(create_line(values))

                joined = "\n".join(lines)
                elements_html.append(joined)

            elif isinstance(e, Chart | Map):
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
