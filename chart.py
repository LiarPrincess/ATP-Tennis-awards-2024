import matplotlib.pyplot as plt
import matplotlib.axis as pltAxis
import matplotlib.axes as pltAxes
import matplotlib.ticker as pltTicker
import matplotlib.figure as pltFigure
from pypalettes import load_cmap
from typing import (
    Any,
    Literal,
    Iterable,
    Sequence,
    Callable,
)
from helpers import *

# https://www.geophysique.be/2011/01/27/matplotlib-basemap-tutorial-07-shapefiles-unleached/
# import matplotlib as mpl
# mpl.rcParams['font.size'] = 10.
# mpl.rcParams['font.family'] = 'Comic Sans MS'
# mpl.rcParams['axes.labelsize'] = 8.
# mpl.rcParams['xtick.labelsize'] = 6.
# mpl.rcParams['ytick.labelsize'] = 6.

# MARK: Chart


class Chart:
    "Single chart."

    class _AxisBase:

        def __init__(self, ax: pltAxes.Axes, axis: pltAxis.Axis) -> None:
            self.ax = ax
            self.axis = axis

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

    def set_title(self, value: str):
        self.ax.set_title(value)

    def set_aspect_rato(self, width: int, height: int):
        "Aspect_rato 2:1 means 200px:100px."
        self._aspect_rato = (width, height)

    def set_show_grid(self, value: bool):
        self.ax.grid(value)

    Xs = Sequence[int]
    Value = int | float
    Values = Sequence[Value]
    RGBA = tuple[float, float, float, float]

    def add_bar(
        self,
        x: Xs,
        height: Values,
        *,
        bottom: Values | None = None,
        color: Sequence[RGBA] | None = None,
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
        color: Literal["black"] | None = None,
        size: int | None = None,
    ):
        self.ax.scatter(x, y, s=size, c=color, marker=marker)

    def add_legend(self, entries: list[str] | None = None):
        if entries is None:
            self.fig.legend()
        else:
            self.fig.legend(entries)

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


# MARK: Helpers


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
