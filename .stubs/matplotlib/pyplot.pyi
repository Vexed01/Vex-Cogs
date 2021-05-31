from numbers import Number as Number
from typing import Any, Optional

from cycler import cycler as cycler
from matplotlib import cbook as cbook
from matplotlib import cm as cm
from matplotlib import docstring as docstring
from matplotlib import get_backend as get_backend
from matplotlib import interactive as interactive
from matplotlib import mlab as mlab
from matplotlib import rcParams as rcParams
from matplotlib import rcParamsDefault as rcParamsDefault
from matplotlib import rcParamsOrig as rcParamsOrig
from matplotlib import rcsetup as rcsetup
from matplotlib import style as style
from matplotlib.artist import Artist as Artist
from matplotlib.axes import Axes as Axes
from matplotlib.axes import Subplot as Subplot
from matplotlib.backend_bases import FigureCanvasBase as FigureCanvasBase
from matplotlib.backend_bases import MouseButton as MouseButton
from matplotlib.cm import get_cmap as get_cmap
from matplotlib.cm import register_cmap as register_cmap
from matplotlib.colors import Normalize as Normalize
from matplotlib.figure import Figure as Figure
from matplotlib.figure import figaspect as figaspect
from matplotlib.gridspec import GridSpec as GridSpec
from matplotlib.gridspec import SubplotSpec as SubplotSpec
from matplotlib.lines import Line2D as Line2D
from matplotlib.patches import Arrow as Arrow
from matplotlib.patches import Circle as Circle
from matplotlib.patches import Polygon as Polygon
from matplotlib.patches import Rectangle as Rectangle
from matplotlib.projections import PolarAxes as PolarAxes
from matplotlib.scale import get_scale_names as get_scale_names
from matplotlib.text import Annotation as Annotation
from matplotlib.text import Text as Text
from matplotlib.widgets import Button as Button
from matplotlib.widgets import Slider as Slider
from matplotlib.widgets import SubplotTool as SubplotTool
from matplotlib.widgets import Widget as Widget

from .ticker import AutoLocator as AutoLocator
from .ticker import FixedFormatter as FixedFormatter
from .ticker import FixedLocator as FixedLocator
from .ticker import FormatStrFormatter as FormatStrFormatter
from .ticker import Formatter as Formatter
from .ticker import FuncFormatter as FuncFormatter
from .ticker import IndexLocator as IndexLocator
from .ticker import LinearLocator as LinearLocator
from .ticker import Locator as Locator
from .ticker import LogFormatter as LogFormatter
from .ticker import LogFormatterExponent as LogFormatterExponent
from .ticker import LogFormatterMathtext as LogFormatterMathtext
from .ticker import LogLocator as LogLocator
from .ticker import MaxNLocator as MaxNLocator
from .ticker import MultipleLocator as MultipleLocator
from .ticker import NullFormatter as NullFormatter
from .ticker import NullLocator as NullLocator
from .ticker import ScalarFormatter as ScalarFormatter
from .ticker import TickHelper as TickHelper

def install_repl_displayhook() -> None: ...
def uninstall_repl_displayhook() -> None: ...

draw_all: Any

def set_loglevel(*args: Any, **kwargs: Any): ...
def findobj(o: Optional[Any] = ..., match: Optional[Any] = ..., include_self: bool = ...): ...
def switch_backend(newbackend: Any) -> None: ...
def new_figure_manager(*args: Any, **kwargs: Any): ...
def draw_if_interactive(*args: Any, **kwargs: Any): ...
def show(*args: Any, **kwargs: Any): ...
def isinteractive(): ...

class _IoffContext:
    wasinteractive: Any = ...
    def __init__(self) -> None: ...
    def __enter__(self) -> None: ...
    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None: ...

class _IonContext:
    wasinteractive: Any = ...
    def __init__(self) -> None: ...
    def __enter__(self) -> None: ...
    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None: ...

def ioff(): ...
def ion(): ...
def pause(interval: Any) -> None: ...
def rc(group: Any, **kwargs: Any) -> None: ...
def rc_context(rc: Optional[Any] = ..., fname: Optional[Any] = ...): ...
def rcdefaults() -> None: ...
def getp(obj: Any, *args: Any, **kwargs: Any): ...
def get(obj: Any, *args: Any, **kwargs: Any): ...
def setp(obj: Any, *args: Any, **kwargs: Any): ...
def xkcd(scale: int = ..., length: int = ..., randomness: int = ...): ...

class _xkcd:
    def __init__(self, scale: Any, length: Any, randomness: Any) -> None: ...
    def __enter__(self): ...
    def __exit__(self, *args: Any) -> None: ...

def figure(
    num: Optional[Any] = ...,
    figsize: Optional[Any] = ...,
    dpi: Optional[Any] = ...,
    facecolor: Optional[Any] = ...,
    edgecolor: Optional[Any] = ...,
    frameon: bool = ...,
    FigureClass: Any = ...,
    clear: bool = ...,
    **kwargs: Any,
): ...
def gcf(): ...
def fignum_exists(num: Any): ...
def get_fignums(): ...
def get_figlabels(): ...
def get_current_fig_manager(): ...
def connect(s: Any, func: Any): ...
def disconnect(cid: Any): ...
def close(fig: Optional[Any] = ...) -> None: ...
def clf() -> None: ...
def draw() -> None: ...
def savefig(*args: Any, **kwargs: Any): ...
def figlegend(*args: Any, **kwargs: Any): ...
def axes(arg: Optional[Any] = ..., **kwargs: Any): ...
def delaxes(ax: Optional[Any] = ...) -> None: ...
def sca(ax: Any) -> None: ...
def cla(): ...
def subplot(*args: Any, **kwargs: Any): ...
def subplots(
    nrows: int = ...,
    ncols: int = ...,
    sharex: bool = ...,
    sharey: bool = ...,
    squeeze: bool = ...,
    subplot_kw: Optional[Any] = ...,
    gridspec_kw: Optional[Any] = ...,
    **fig_kw: Any,
): ...
def subplot_mosaic(
    mosaic: Any,
    *,
    subplot_kw: Optional[Any] = ...,
    gridspec_kw: Optional[Any] = ...,
    empty_sentinel: str = ...,
    **fig_kw: Any,
): ...
def subplot2grid(
    shape: Any,
    loc: Any,
    rowspan: int = ...,
    colspan: int = ...,
    fig: Optional[Any] = ...,
    **kwargs: Any,
): ...
def twinx(ax: Optional[Any] = ...): ...
def twiny(ax: Optional[Any] = ...): ...
def subplot_tool(targetfig: Optional[Any] = ...): ...
def tight_layout(
    pad: float = ...,
    h_pad: Optional[Any] = ...,
    w_pad: Optional[Any] = ...,
    rect: Optional[Any] = ...,
) -> None: ...
def box(on: Optional[Any] = ...) -> None: ...
def xlim(*args: Any, **kwargs: Any): ...
def ylim(*args: Any, **kwargs: Any): ...
def xticks(ticks: Optional[Any] = ..., labels: Optional[Any] = ..., **kwargs: Any): ...
def yticks(ticks: Optional[Any] = ..., labels: Optional[Any] = ..., **kwargs: Any): ...
def rgrids(
    radii: Optional[Any] = ...,
    labels: Optional[Any] = ...,
    angle: Optional[Any] = ...,
    fmt: Optional[Any] = ...,
    **kwargs: Any,
): ...
def thetagrids(
    angles: Optional[Any] = ...,
    labels: Optional[Any] = ...,
    fmt: Optional[Any] = ...,
    **kwargs: Any,
): ...
def plotting() -> None: ...
def get_plot_commands(): ...
def colormaps(): ...
def colorbar(
    mappable: Optional[Any] = ..., cax: Optional[Any] = ..., ax: Optional[Any] = ..., **kw: Any
): ...
def clim(vmin: Optional[Any] = ..., vmax: Optional[Any] = ...) -> None: ...
def set_cmap(cmap: Any) -> None: ...
def imread(fname: Any, format: Optional[Any] = ...): ...
def imsave(fname: Any, arr: Any, **kwargs: Any): ...
def matshow(A: Any, fignum: Optional[Any] = ..., **kwargs: Any): ...
def polar(*args: Any, **kwargs: Any): ...
def figimage(
    X: Any,
    xo: int = ...,
    yo: int = ...,
    alpha: Optional[Any] = ...,
    norm: Optional[Any] = ...,
    cmap: Optional[Any] = ...,
    vmin: Optional[Any] = ...,
    vmax: Optional[Any] = ...,
    origin: Optional[Any] = ...,
    resize: bool = ...,
    **kwargs: Any,
): ...
def figtext(x: Any, y: Any, s: Any, fontdict: Optional[Any] = ..., **kwargs: Any): ...
def gca(**kwargs: Any): ...
def gci(): ...
def ginput(
    n: int = ...,
    timeout: int = ...,
    show_clicks: bool = ...,
    mouse_add: Any = ...,
    mouse_pop: Any = ...,
    mouse_stop: Any = ...,
): ...
def subplots_adjust(
    left: Optional[Any] = ...,
    bottom: Optional[Any] = ...,
    right: Optional[Any] = ...,
    top: Optional[Any] = ...,
    wspace: Optional[Any] = ...,
    hspace: Optional[Any] = ...,
): ...
def suptitle(t: Any, **kwargs: Any): ...
def waitforbuttonpress(timeout: int = ...): ...
def acorr(x: Any, *, data: Optional[Any] = ..., **kwargs: Any): ...
def angle_spectrum(
    x: Any,
    Fs: Optional[Any] = ...,
    Fc: Optional[Any] = ...,
    window: Optional[Any] = ...,
    pad_to: Optional[Any] = ...,
    sides: Optional[Any] = ...,
    *,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def annotate(text: Any, xy: Any, *args: Any, **kwargs: Any): ...
def arrow(x: Any, y: Any, dx: Any, dy: Any, **kwargs: Any): ...
def autoscale(enable: bool = ..., axis: str = ..., tight: Optional[Any] = ...): ...
def axhline(y: int = ..., xmin: int = ..., xmax: int = ..., **kwargs: Any): ...
def axhspan(ymin: Any, ymax: Any, xmin: int = ..., xmax: int = ..., **kwargs: Any): ...
def axis(*args: Any, emit: bool = ..., **kwargs: Any): ...
def axline(xy1: Any, xy2: Optional[Any] = ..., *, slope: Optional[Any] = ..., **kwargs: Any): ...
def axvline(x: int = ..., ymin: int = ..., ymax: int = ..., **kwargs: Any): ...
def axvspan(xmin: Any, xmax: Any, ymin: int = ..., ymax: int = ..., **kwargs: Any): ...
def bar(
    x: Any,
    height: Any,
    width: float = ...,
    bottom: Optional[Any] = ...,
    *,
    align: str = ...,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def barbs(*args: Any, data: Optional[Any] = ..., **kw: Any): ...
def barh(
    y: Any,
    width: Any,
    height: float = ...,
    left: Optional[Any] = ...,
    *,
    align: str = ...,
    **kwargs: Any,
): ...
def bar_label(
    container: Any,
    labels: Optional[Any] = ...,
    *,
    fmt: str = ...,
    label_type: str = ...,
    padding: int = ...,
    **kwargs: Any,
): ...
def boxplot(
    x: Any,
    notch: Optional[Any] = ...,
    sym: Optional[Any] = ...,
    vert: Optional[Any] = ...,
    whis: Optional[Any] = ...,
    positions: Optional[Any] = ...,
    widths: Optional[Any] = ...,
    patch_artist: Optional[Any] = ...,
    bootstrap: Optional[Any] = ...,
    usermedians: Optional[Any] = ...,
    conf_intervals: Optional[Any] = ...,
    meanline: Optional[Any] = ...,
    showmeans: Optional[Any] = ...,
    showcaps: Optional[Any] = ...,
    showbox: Optional[Any] = ...,
    showfliers: Optional[Any] = ...,
    boxprops: Optional[Any] = ...,
    labels: Optional[Any] = ...,
    flierprops: Optional[Any] = ...,
    medianprops: Optional[Any] = ...,
    meanprops: Optional[Any] = ...,
    capprops: Optional[Any] = ...,
    whiskerprops: Optional[Any] = ...,
    manage_ticks: bool = ...,
    autorange: bool = ...,
    zorder: Optional[Any] = ...,
    *,
    data: Optional[Any] = ...,
): ...
def broken_barh(xranges: Any, yrange: Any, *, data: Optional[Any] = ..., **kwargs: Any): ...
def clabel(CS: Any, levels: Optional[Any] = ..., **kwargs: Any): ...
def cohere(
    x: Any,
    y: Any,
    NFFT: int = ...,
    Fs: int = ...,
    Fc: int = ...,
    detrend: Any = ...,
    window: Any = ...,
    noverlap: int = ...,
    pad_to: Optional[Any] = ...,
    sides: str = ...,
    scale_by_freq: Optional[Any] = ...,
    *,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def contour(*args: Any, data: Optional[Any] = ..., **kwargs: Any): ...
def contourf(*args: Any, data: Optional[Any] = ..., **kwargs: Any): ...
def csd(
    x: Any,
    y: Any,
    NFFT: Optional[Any] = ...,
    Fs: Optional[Any] = ...,
    Fc: Optional[Any] = ...,
    detrend: Optional[Any] = ...,
    window: Optional[Any] = ...,
    noverlap: Optional[Any] = ...,
    pad_to: Optional[Any] = ...,
    sides: Optional[Any] = ...,
    scale_by_freq: Optional[Any] = ...,
    return_line: Optional[Any] = ...,
    *,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def errorbar(
    x: Any,
    y: Any,
    yerr: Optional[Any] = ...,
    xerr: Optional[Any] = ...,
    fmt: str = ...,
    ecolor: Optional[Any] = ...,
    elinewidth: Optional[Any] = ...,
    capsize: Optional[Any] = ...,
    barsabove: bool = ...,
    lolims: bool = ...,
    uplims: bool = ...,
    xlolims: bool = ...,
    xuplims: bool = ...,
    errorevery: int = ...,
    capthick: Optional[Any] = ...,
    *,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def eventplot(
    positions: Any,
    orientation: str = ...,
    lineoffsets: int = ...,
    linelengths: int = ...,
    linewidths: Optional[Any] = ...,
    colors: Optional[Any] = ...,
    linestyles: str = ...,
    *,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def fill(*args: Any, data: Optional[Any] = ..., **kwargs: Any): ...
def fill_between(
    x: Any,
    y1: Any,
    y2: int = ...,
    where: Optional[Any] = ...,
    interpolate: bool = ...,
    step: Optional[Any] = ...,
    *,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def fill_betweenx(
    y: Any,
    x1: Any,
    x2: int = ...,
    where: Optional[Any] = ...,
    step: Optional[Any] = ...,
    interpolate: bool = ...,
    *,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def grid(b: Optional[Any] = ..., which: str = ..., axis: str = ..., **kwargs: Any): ...
def hexbin(
    x: Any,
    y: Any,
    C: Optional[Any] = ...,
    gridsize: int = ...,
    bins: Optional[Any] = ...,
    xscale: str = ...,
    yscale: str = ...,
    extent: Optional[Any] = ...,
    cmap: Optional[Any] = ...,
    norm: Optional[Any] = ...,
    vmin: Optional[Any] = ...,
    vmax: Optional[Any] = ...,
    alpha: Optional[Any] = ...,
    linewidths: Optional[Any] = ...,
    edgecolors: str = ...,
    reduce_C_function: Any = ...,
    mincnt: Optional[Any] = ...,
    marginals: bool = ...,
    *,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def hist(
    x: Any,
    bins: Optional[Any] = ...,
    range: Optional[Any] = ...,
    density: bool = ...,
    weights: Optional[Any] = ...,
    cumulative: bool = ...,
    bottom: Optional[Any] = ...,
    histtype: str = ...,
    align: str = ...,
    orientation: str = ...,
    rwidth: Optional[Any] = ...,
    log: bool = ...,
    color: Optional[Any] = ...,
    label: Optional[Any] = ...,
    stacked: bool = ...,
    *,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def stairs(
    values: Any,
    edges: Optional[Any] = ...,
    *,
    orientation: str = ...,
    baseline: int = ...,
    fill: bool = ...,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def hist2d(
    x: Any,
    y: Any,
    bins: int = ...,
    range: Optional[Any] = ...,
    density: bool = ...,
    weights: Optional[Any] = ...,
    cmin: Optional[Any] = ...,
    cmax: Optional[Any] = ...,
    *,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def hlines(
    y: Any,
    xmin: Any,
    xmax: Any,
    colors: Optional[Any] = ...,
    linestyles: str = ...,
    label: str = ...,
    *,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def imshow(
    X: Any,
    cmap: Optional[Any] = ...,
    norm: Optional[Any] = ...,
    aspect: Optional[Any] = ...,
    interpolation: Optional[Any] = ...,
    alpha: Optional[Any] = ...,
    vmin: Optional[Any] = ...,
    vmax: Optional[Any] = ...,
    origin: Optional[Any] = ...,
    extent: Optional[Any] = ...,
    *,
    filternorm: bool = ...,
    filterrad: float = ...,
    resample: Optional[Any] = ...,
    url: Optional[Any] = ...,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def legend(*args: Any, **kwargs: Any): ...
def locator_params(axis: str = ..., tight: Optional[Any] = ..., **kwargs: Any): ...
def loglog(*args: Any, **kwargs: Any): ...
def magnitude_spectrum(
    x: Any,
    Fs: Optional[Any] = ...,
    Fc: Optional[Any] = ...,
    window: Optional[Any] = ...,
    pad_to: Optional[Any] = ...,
    sides: Optional[Any] = ...,
    scale: Optional[Any] = ...,
    *,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def margins(*margins: Any, x: Optional[Any] = ..., y: Optional[Any] = ..., tight: bool = ...): ...
def minorticks_off(): ...
def minorticks_on(): ...
def pcolor(
    *args: Any,
    shading: Optional[Any] = ...,
    alpha: Optional[Any] = ...,
    norm: Optional[Any] = ...,
    cmap: Optional[Any] = ...,
    vmin: Optional[Any] = ...,
    vmax: Optional[Any] = ...,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def pcolormesh(
    *args: Any,
    alpha: Optional[Any] = ...,
    norm: Optional[Any] = ...,
    cmap: Optional[Any] = ...,
    vmin: Optional[Any] = ...,
    vmax: Optional[Any] = ...,
    shading: Optional[Any] = ...,
    antialiased: bool = ...,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def phase_spectrum(
    x: Any,
    Fs: Optional[Any] = ...,
    Fc: Optional[Any] = ...,
    window: Optional[Any] = ...,
    pad_to: Optional[Any] = ...,
    sides: Optional[Any] = ...,
    *,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def pie(
    x: Any,
    explode: Optional[Any] = ...,
    labels: Optional[Any] = ...,
    colors: Optional[Any] = ...,
    autopct: Optional[Any] = ...,
    pctdistance: float = ...,
    shadow: bool = ...,
    labeldistance: float = ...,
    startangle: int = ...,
    radius: int = ...,
    counterclock: bool = ...,
    wedgeprops: Optional[Any] = ...,
    textprops: Optional[Any] = ...,
    center: Any = ...,
    frame: bool = ...,
    rotatelabels: bool = ...,
    *,
    normalize: Optional[Any] = ...,
    data: Optional[Any] = ...,
): ...
def plot(
    *args: Any, scalex: bool = ..., scaley: bool = ..., data: Optional[Any] = ..., **kwargs: Any
): ...
def plot_date(
    x: Any,
    y: Any,
    fmt: str = ...,
    tz: Optional[Any] = ...,
    xdate: bool = ...,
    ydate: bool = ...,
    *,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def psd(
    x: Any,
    NFFT: Optional[Any] = ...,
    Fs: Optional[Any] = ...,
    Fc: Optional[Any] = ...,
    detrend: Optional[Any] = ...,
    window: Optional[Any] = ...,
    noverlap: Optional[Any] = ...,
    pad_to: Optional[Any] = ...,
    sides: Optional[Any] = ...,
    scale_by_freq: Optional[Any] = ...,
    return_line: Optional[Any] = ...,
    *,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def quiver(*args: Any, data: Optional[Any] = ..., **kw: Any): ...
def quiverkey(Q: Any, X: Any, Y: Any, U: Any, label: Any, **kw: Any): ...
def scatter(
    x: Any,
    y: Any,
    s: Optional[Any] = ...,
    c: Optional[Any] = ...,
    marker: Optional[Any] = ...,
    cmap: Optional[Any] = ...,
    norm: Optional[Any] = ...,
    vmin: Optional[Any] = ...,
    vmax: Optional[Any] = ...,
    alpha: Optional[Any] = ...,
    linewidths: Optional[Any] = ...,
    *,
    edgecolors: Optional[Any] = ...,
    plotnonfinite: bool = ...,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def semilogx(*args: Any, **kwargs: Any): ...
def semilogy(*args: Any, **kwargs: Any): ...
def specgram(
    x: Any,
    NFFT: Optional[Any] = ...,
    Fs: Optional[Any] = ...,
    Fc: Optional[Any] = ...,
    detrend: Optional[Any] = ...,
    window: Optional[Any] = ...,
    noverlap: Optional[Any] = ...,
    cmap: Optional[Any] = ...,
    xextent: Optional[Any] = ...,
    pad_to: Optional[Any] = ...,
    sides: Optional[Any] = ...,
    scale_by_freq: Optional[Any] = ...,
    mode: Optional[Any] = ...,
    scale: Optional[Any] = ...,
    vmin: Optional[Any] = ...,
    vmax: Optional[Any] = ...,
    *,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def spy(
    Z: Any,
    precision: int = ...,
    marker: Optional[Any] = ...,
    markersize: Optional[Any] = ...,
    aspect: str = ...,
    origin: str = ...,
    **kwargs: Any,
): ...
def stackplot(
    x: Any,
    *args: Any,
    labels: Any = ...,
    colors: Optional[Any] = ...,
    baseline: str = ...,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def stem(
    *args: Any,
    linefmt: Optional[Any] = ...,
    markerfmt: Optional[Any] = ...,
    basefmt: Optional[Any] = ...,
    bottom: int = ...,
    label: Optional[Any] = ...,
    use_line_collection: bool = ...,
    orientation: str = ...,
    data: Optional[Any] = ...,
): ...
def step(
    x: Any, y: Any, *args: Any, where: str = ..., data: Optional[Any] = ..., **kwargs: Any
): ...
def streamplot(
    x: Any,
    y: Any,
    u: Any,
    v: Any,
    density: int = ...,
    linewidth: Optional[Any] = ...,
    color: Optional[Any] = ...,
    cmap: Optional[Any] = ...,
    norm: Optional[Any] = ...,
    arrowsize: int = ...,
    arrowstyle: str = ...,
    minlength: float = ...,
    transform: Optional[Any] = ...,
    zorder: Optional[Any] = ...,
    start_points: Optional[Any] = ...,
    maxlength: float = ...,
    integration_direction: str = ...,
    *,
    data: Optional[Any] = ...,
): ...
def table(
    cellText: Optional[Any] = ...,
    cellColours: Optional[Any] = ...,
    cellLoc: str = ...,
    colWidths: Optional[Any] = ...,
    rowLabels: Optional[Any] = ...,
    rowColours: Optional[Any] = ...,
    rowLoc: str = ...,
    colLabels: Optional[Any] = ...,
    colColours: Optional[Any] = ...,
    colLoc: str = ...,
    loc: str = ...,
    bbox: Optional[Any] = ...,
    edges: str = ...,
    **kwargs: Any,
): ...
def text(x: Any, y: Any, s: Any, fontdict: Optional[Any] = ..., **kwargs: Any): ...
def tick_params(axis: str = ..., **kwargs: Any): ...
def ticklabel_format(
    *,
    axis: str = ...,
    style: str = ...,
    scilimits: Optional[Any] = ...,
    useOffset: Optional[Any] = ...,
    useLocale: Optional[Any] = ...,
    useMathText: Optional[Any] = ...,
): ...
def tricontour(*args: Any, **kwargs: Any): ...
def tricontourf(*args: Any, **kwargs: Any): ...
def tripcolor(
    *args: Any,
    alpha: float = ...,
    norm: Optional[Any] = ...,
    cmap: Optional[Any] = ...,
    vmin: Optional[Any] = ...,
    vmax: Optional[Any] = ...,
    shading: str = ...,
    facecolors: Optional[Any] = ...,
    **kwargs: Any,
): ...
def triplot(*args: Any, **kwargs: Any): ...
def violinplot(
    dataset: Any,
    positions: Optional[Any] = ...,
    vert: bool = ...,
    widths: float = ...,
    showmeans: bool = ...,
    showextrema: bool = ...,
    showmedians: bool = ...,
    quantiles: Optional[Any] = ...,
    points: int = ...,
    bw_method: Optional[Any] = ...,
    *,
    data: Optional[Any] = ...,
): ...
def vlines(
    x: Any,
    ymin: Any,
    ymax: Any,
    colors: Optional[Any] = ...,
    linestyles: str = ...,
    label: str = ...,
    *,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def xcorr(
    x: Any,
    y: Any,
    normed: bool = ...,
    detrend: Any = ...,
    usevlines: bool = ...,
    maxlags: int = ...,
    *,
    data: Optional[Any] = ...,
    **kwargs: Any,
): ...
def sci(im: Any): ...
def title(
    label: Any,
    fontdict: Optional[Any] = ...,
    loc: Optional[Any] = ...,
    pad: Optional[Any] = ...,
    *,
    y: Optional[Any] = ...,
    **kwargs: Any,
): ...
def xlabel(
    xlabel: Any,
    fontdict: Optional[Any] = ...,
    labelpad: Optional[Any] = ...,
    *,
    loc: Optional[Any] = ...,
    **kwargs: Any,
): ...
def ylabel(
    ylabel: Any,
    fontdict: Optional[Any] = ...,
    labelpad: Optional[Any] = ...,
    *,
    loc: Optional[Any] = ...,
    **kwargs: Any,
): ...
def xscale(value: Any, **kwargs: Any): ...
def yscale(value: Any, **kwargs: Any): ...
def autumn() -> None: ...
def bone() -> None: ...
def cool() -> None: ...
def copper() -> None: ...
def flag() -> None: ...
def gray() -> None: ...
def hot() -> None: ...
def hsv() -> None: ...
def jet() -> None: ...
def pink() -> None: ...
def prism() -> None: ...
def spring() -> None: ...
def summer() -> None: ...
def winter() -> None: ...
def magma() -> None: ...
def inferno() -> None: ...
def plasma() -> None: ...
def viridis() -> None: ...
def nipy_spectral() -> None: ...
