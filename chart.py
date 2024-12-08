import matplotlib.pyplot as plt
import matplotlib.axes as pltAxes
import matplotlib.axis as pltAxis
import matplotlib.colors as pltColors
import matplotlib.figure as pltFigure
import matplotlib.ticker as pltTicker
import matplotlib.collections as pltCollections
import matplotlib.font_manager as pltFontManager
from dataclasses import dataclass
from typing import (
    Any,
    Literal,
    Iterable,
    Sequence,
    Callable,
)
from helpers import *

_COLOR_BACKGROUND = "#282a36"
_COLOR_SELECTION = "#44475a"
_COLOR_FOREGROUND = "#f8f8f2"
_COLOR_COMMENT = "#6272a4"
_COLOR_PINK = "#ff79c6"
_COLOR_PURPLE = "#bd93f9"
_COLOR_CYAN = "#8be9fd"
_COLOR_GREEN = "#50fa7b"
_COLOR_YELLOW = "#f1fa8c"
_COLOR_ORANGE = "#ffb86c"
_COLOR_RED = "#ff5555"

_FONT_NAME = "Inconsolata"
pltFontManager.fontManager.addfont("assets/Inconsolata-VariableFont_wdth,wght.ttf")

_BACKGROUND_COLOR = _COLOR_BACKGROUND
_GRID_COLOR = _COLOR_SELECTION
_AXIS_LABEL_COLOR = _COLOR_FOREGROUND
_AXIS_LABEL_FONT_SIZE = 20
_AXIS_TICK_COLOR = _COLOR_FOREGROUND
_AXIS_TICK_FONT_SIZE = 16

# MARK: Chart


class Chart:
    "Single chart."

    Xs = Sequence[int]
    Value = int | float
    Values = Sequence[Value]
    ColorLiteral = Literal[
        "background",
        "selection",
        "foreground",
        "comment",
        "cyan",
        "green",
        "orange",
        "pink",
        "purple",
        "red",
        "yellow",
    ]
    ColorRGBA = tuple[float, float, float, float]
    Color = ColorLiteral | ColorRGBA

    Gradient = Literal[
        "yellow_pink",
        "pink_purple",
        "purple_cyan",
        "cyan_green",
        "red_pink",
        "red_orange_yellow_green_cyan_purple_pink",
    ]

    class _AxisBase:

        def __init__(self, ax: pltAxes.Axes, axis: pltAxis.Axis) -> None:
            self.ax = ax
            self.axis = axis
            self.axis.label.set_fontsize(_AXIS_LABEL_FONT_SIZE)
            self.axis.label.set_fontname(_FONT_NAME)
            self.axis.label.set_color(_AXIS_LABEL_COLOR)

            # https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.tick_params.html
            self.axis.set_tick_params(
                which="both",
                labelsize=_AXIS_TICK_FONT_SIZE,
                labelcolor=_AXIS_LABEL_COLOR,
                labelfontfamily=_FONT_NAME,
                color=_AXIS_TICK_COLOR,
                grid_color=_GRID_COLOR,
            )

            self.ax.spines["top"].set_visible(False)
            self.ax.spines["right"].set_visible(False)
            self.ax.spines["bottom"].set_color(_AXIS_TICK_COLOR)
            self.ax.spines["left"].set_color(_AXIS_TICK_COLOR)

        def set_major_tick_interval(self, interval: int):
            loc = pltTicker.MultipleLocator(interval)
            self.axis.set_major_locator(loc)

        def set_minor_tick_interval(self, value: int):
            loc = pltTicker.MultipleLocator(value)
            self.axis.set_minor_locator(loc)

        def set_major_tick_count(
            self,
            values: "Chart.Values",
            count: int,
            multiple_of: int = 1,
        ):
            values_min = min(o for o in values)
            values_max = max(o for o in values)
            spread = values_max - values_min

            interval_float = spread / count
            interval = round_down(int(interval_float), multiple_of=multiple_of)
            self.set_major_tick_interval(interval)

        def set_major_formatter_fn(self, fn: Callable[[float, Any], str]):
            fmt = pltTicker.FuncFormatter(fn)
            self.axis.set_major_formatter(fmt)

    class XAxis(_AxisBase):
        def __init__(self, ax: pltAxes.Axes) -> None:
            super().__init__(ax, ax.xaxis)
            self.ax.set_xmargin(0)
            self.set_major_tick_interval(5)
            self.set_minor_tick_interval(1)

        def set_label(self, value: str):
            self.ax.set_xlabel(value)

        def set_range(self, min: int | float, max: int | float):
            self.ax.set_xlim(min, max)

    class YAxis(_AxisBase):
        def __init__(self, ax: pltAxes.Axes) -> None:
            super().__init__(ax, ax.yaxis)
            self.ax.set_ymargin(0)

        def set_label(self, value: str):
            self.ax.set_ylabel(value)

        def set_range(self, min: int | float, max: int | float):
            self.ax.set_ylim(min, max)

    def __init__(self) -> None:
        self.fig, self.ax = plt.subplots(layout="constrained")
        self.x_axis = Chart.XAxis(self.ax)
        self.y_axis = Chart.YAxis(self.ax)
        self._aspect_rato: tuple[int, int] | None = None
        self.ax.set_facecolor(_BACKGROUND_COLOR)  # Inner plot background
        self.fig.set_facecolor(_BACKGROUND_COLOR)  # Outside plot Background

    def set_title(self, value: str):
        self.ax.set_title(value)

    def set_aspect_rato(self, width: int, height: int):
        "Aspect_rato 2:1 means 200px:100px."
        self._aspect_rato = (width, height)

    def set_show_grid(self, value: bool):
        self.ax.grid(value)

    def add_bar(
        self,
        x: Xs,
        height: Values,
        *,
        bottom: Values | None = None,
        color: Sequence[ColorRGBA] | None = None,
    ):
        self.ax.bar(x, height, bottom=bottom, color=color)

    # https://matplotlib.org/stable/api/markers_api.html
    ScatterMarker = Literal[
        ".", "o", "v", "^", "<", ">", "s", "p", "P", "*", "+", "x", "X", "D", "|", "_"
    ]

    def add_scatter(
        self,
        x: Sequence[int],
        y: Sequence[int | float],
        *,
        marker: ScatterMarker | None = None,
        color: ColorLiteral | None = None,
        size: int | None = None,
    ):
        color_2 = _color_literal_to_hex_or_none(color)
        self.ax.scatter(x, y, s=size, c=color_2, marker=marker)

    @dataclass
    class Heatmap:
        im: pltCollections.Collection
        y_ticks: list["Chart.Value"]

    def add_heatmap(
        self,
        xs: Xs,
        ys: Xs,
        values: Sequence[Values],
    ) -> Heatmap:
        cmap = pltColors.LinearSegmentedColormap.from_list(
            "heatmap",
            [
                _COLOR_BACKGROUND,
                _COLOR_SELECTION,
                _COLOR_COMMENT,
                _COLOR_CYAN,
                _COLOR_PURPLE,
                _COLOR_PINK,
                _COLOR_FOREGROUND,
            ],
        )

        values_unique = set[Chart.Value]()

        for vs in values:
            for v in vs:
                values_unique.add(v)

        y_ticks = sorted(values_unique)

        # https://matplotlib.org/stable/users/explain/colors/colorbar_only.html#discrete-and-extended-colorbar-with-continuous-colorscale
        #
        # https://stackoverflow.com/a/71453476:
        # The first figure shows 10 colors, so 11 boundaries are needed.
        values_bounds = list(y_ticks)
        values_bounds.append(values_bounds[-1] + 1)
        norm = pltColors.BoundaryNorm(values_bounds, cmap.N)

        # 'pcolorfast' gives incorrect XY ticks
        im = self.ax.pcolor(xs, ys, values, cmap=cmap, norm=norm)
        return Chart.Heatmap(im, y_ticks)

    def add_color_bar(self, heatmap: Heatmap, label: str | None = None):
        cb = self.fig.colorbar(
            heatmap.im,
            ax=self.ax,
            ticks=heatmap.y_ticks,
        )

        # This will apply color theme
        y_axis = Chart.YAxis(cb.ax)

        if label is not None:
            y_axis.set_label(label)

    def add_legend(self, entries: list[str] | None = None):
        if entries is None:
            self.fig.legend()
        else:
            self.fig.legend(entries)

    def create_color_map(
        self,
        values: Iterable[int | float],
        colors: Gradient | list[ColorLiteral],
    ) -> dict[int | float, ColorRGBA]:
        colors_2 = list[str]()

        if isinstance(colors, list):
            colors_2.extend(map(_color_literal_to_hex, colors))
        else:
            gr = _gradient_to_hex(colors)
            colors_2.extend(gr)

        if len(colors_2) == 1:
            # Add 2nd color
            colors_2 = colors_2 + colors_2

        cmap_name = "_".join(colors)
        cmap = pltColors.LinearSegmentedColormap.from_list(cmap_name, colors_2)

        values_sorted = sorted(set(values))
        values_len = len(values_sorted)

        value_to_color = dict[int | float, Chart.ColorRGBA]()

        for i, value in enumerate(values_sorted):
            x = i / values_len
            value_to_color[value] = cmap(x)

        return value_to_color

    def write_img(self, path: str, *, width: int):
        _write_img(path, self.fig, width, self._aspect_rato)


# MARK: Helpers

_COLOR_LITERAL_TO_HEX_MAP: dict[Chart.ColorLiteral, str] = {
    "background": _COLOR_BACKGROUND,
    "selection": _COLOR_SELECTION,
    "foreground": _COLOR_FOREGROUND,
    "comment": _COLOR_COMMENT,
    "cyan": _COLOR_CYAN,
    "green": _COLOR_GREEN,
    "orange": _COLOR_ORANGE,
    "pink": _COLOR_PINK,
    "purple": _COLOR_PURPLE,
    "red": _COLOR_RED,
    "yellow": _COLOR_YELLOW,
}


def _color_literal_to_hex(color: Chart.ColorLiteral) -> str:
    return _COLOR_LITERAL_TO_HEX_MAP[color]


def _color_literal_to_hex_or_none(color: Chart.ColorLiteral | None) -> str | None:
    if color is None:
        return None

    return _COLOR_LITERAL_TO_HEX_MAP[color]


_GRADIENT_TO_HEX: dict[Chart.Gradient, list[str]] = {
    "yellow_pink": [_COLOR_YELLOW, _COLOR_PINK],
    "pink_purple": [_COLOR_PINK, _COLOR_PURPLE],
    "purple_cyan": [_COLOR_PURPLE, _COLOR_CYAN],
    "cyan_green": [_COLOR_CYAN, _COLOR_GREEN],
    "red_pink": [_COLOR_RED, _COLOR_PINK],
    "red_orange_yellow_green_cyan_purple_pink": [
        _COLOR_RED,
        _COLOR_ORANGE,
        _COLOR_YELLOW,
        _COLOR_GREEN,
        _COLOR_CYAN,
        _COLOR_PURPLE,
        _COLOR_PINK,
    ],
}


def _gradient_to_hex(gradient: Chart.Gradient) -> list[str]:
    return _GRADIENT_TO_HEX[gradient]


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

    fig.savefig(
        path,
        facecolor=fig.get_facecolor(),
        edgecolor=fig.get_edgecolor(),
    )
    plt.close(fig)
