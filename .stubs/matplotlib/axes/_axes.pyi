from typing import Any, Optional

from matplotlib import rcParams as rcParams  # type:ignore
from matplotlib.axes._base import _AxesBase
from matplotlib.axes._secondary_axes import SecondaryAxis as SecondaryAxis
from matplotlib.container import BarContainer as BarContainer
from matplotlib.container import ErrorbarContainer as ErrorbarContainer
from matplotlib.container import StemContainer as StemContainer

class Axes(_AxesBase):
    def get_title(self, loc: str = ...): ...
    def set_title(
        self,
        label: Any,
        fontdict: Optional[Any] = ...,
        loc: Optional[Any] = ...,
        pad: Optional[Any] = ...,
        *,
        y: Optional[Any] = ...,
        **kwargs: Any,
    ): ...
    def get_legend_handles_labels(self, legend_handler_map: Optional[Any] = ...): ...
    legend_: Any = ...
    def legend(self, *args: Any, **kwargs: Any): ...
    def inset_axes(
        self, bounds: Any, *, transform: Optional[Any] = ..., zorder: int = ..., **kwargs: Any
    ): ...
    def indicate_inset(
        self,
        bounds: Any,
        inset_ax: Optional[Any] = ...,
        *,
        transform: Optional[Any] = ...,
        facecolor: str = ...,
        edgecolor: str = ...,
        alpha: float = ...,
        zorder: float = ...,
        **kwargs: Any,
    ): ...
    def indicate_inset_zoom(self, inset_ax: Any, **kwargs: Any): ...
    def secondary_xaxis(self, location: Any, *, functions: Optional[Any] = ..., **kwargs: Any): ...
    def secondary_yaxis(self, location: Any, *, functions: Optional[Any] = ..., **kwargs: Any): ...
    def text(self, x: Any, y: Any, s: Any, fontdict: Optional[Any] = ..., **kwargs: Any): ...
    def annotate(self, text: Any, xy: Any, *args: Any, **kwargs: Any): ...
    def axhline(self, y: int = ..., xmin: int = ..., xmax: int = ..., **kwargs: Any): ...
    def axvline(self, x: int = ..., ymin: int = ..., ymax: int = ..., **kwargs: Any): ...
    def axline(
        self, xy1: Any, xy2: Optional[Any] = ..., *, slope: Optional[Any] = ..., **kwargs: Any
    ): ...
    def axhspan(self, ymin: Any, ymax: Any, xmin: int = ..., xmax: int = ..., **kwargs: Any): ...
    def axvspan(self, xmin: Any, xmax: Any, ymin: int = ..., ymax: int = ..., **kwargs: Any): ...
    def hlines(
        self,
        y: Any,
        xmin: Any,
        xmax: Any,
        colors: Optional[Any] = ...,
        linestyles: str = ...,
        label: str = ...,
        **kwargs: Any,
    ): ...
    def vlines(
        self,
        x: Any,
        ymin: Any,
        ymax: Any,
        colors: Optional[Any] = ...,
        linestyles: str = ...,
        label: str = ...,
        **kwargs: Any,
    ): ...
    def eventplot(
        self,
        positions: Any,
        orientation: str = ...,
        lineoffsets: int = ...,
        linelengths: int = ...,
        linewidths: Optional[Any] = ...,
        colors: Optional[Any] = ...,
        linestyles: str = ...,
        **kwargs: Any,
    ): ...
    def plot(
        self,
        *args: Any,
        scalex: bool = ...,
        scaley: bool = ...,
        data: Optional[Any] = ...,
        **kwargs: Any,
    ): ...
    def plot_date(
        self,
        x: Any,
        y: Any,
        fmt: str = ...,
        tz: Optional[Any] = ...,
        xdate: bool = ...,
        ydate: bool = ...,
        **kwargs: Any,
    ): ...
    def loglog(self, *args: Any, **kwargs: Any): ...
    def semilogx(self, *args: Any, **kwargs: Any): ...
    def semilogy(self, *args: Any, **kwargs: Any): ...
    def acorr(self, x: Any, **kwargs: Any): ...
    def xcorr(
        self,
        x: Any,
        y: Any,
        normed: bool = ...,
        detrend: Any = ...,
        usevlines: bool = ...,
        maxlags: int = ...,
        **kwargs: Any,
    ): ...
    def step(
        self,
        x: Any,
        y: Any,
        *args: Any,
        where: str = ...,
        data: Optional[Any] = ...,
        **kwargs: Any,
    ): ...
    def bar(
        self,
        x: Any,
        height: Any,
        width: float = ...,
        bottom: Optional[Any] = ...,
        *,
        align: str = ...,
        **kwargs: Any,
    ): ...
    def barh(
        self,
        y: Any,
        width: Any,
        height: float = ...,
        left: Optional[Any] = ...,
        *,
        align: str = ...,
        **kwargs: Any,
    ): ...
    def bar_label(
        self,
        container: Any,
        labels: Optional[Any] = ...,
        *,
        fmt: str = ...,
        label_type: str = ...,
        padding: int = ...,
        **kwargs: Any,
    ): ...
    def broken_barh(self, xranges: Any, yrange: Any, **kwargs: Any): ...
    def stem(
        self,
        *args: Any,
        linefmt: Optional[Any] = ...,
        markerfmt: Optional[Any] = ...,
        basefmt: Optional[Any] = ...,
        bottom: int = ...,
        label: Optional[Any] = ...,
        use_line_collection: bool = ...,
        orientation: str = ...,
    ): ...
    def pie(
        self,
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
    ): ...
    def errorbar(
        self,
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
        **kwargs: Any,
    ): ...
    def boxplot(
        self,
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
    ): ...
    def bxp(
        self,
        bxpstats: Any,
        positions: Optional[Any] = ...,
        widths: Optional[Any] = ...,
        vert: bool = ...,
        patch_artist: bool = ...,
        shownotches: bool = ...,
        showmeans: bool = ...,
        showcaps: bool = ...,
        showbox: bool = ...,
        showfliers: bool = ...,
        boxprops: Optional[Any] = ...,
        whiskerprops: Optional[Any] = ...,
        flierprops: Optional[Any] = ...,
        medianprops: Optional[Any] = ...,
        capprops: Optional[Any] = ...,
        meanprops: Optional[Any] = ...,
        meanline: bool = ...,
        manage_ticks: bool = ...,
        zorder: Optional[Any] = ...,
    ): ...
    def scatter(
        self,
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
        **kwargs: Any,
    ): ...
    def hexbin(
        self,
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
        **kwargs: Any,
    ): ...
    def arrow(self, x: Any, y: Any, dx: Any, dy: Any, **kwargs: Any): ...
    def quiverkey(self, Q: Any, X: Any, Y: Any, U: Any, label: Any, **kw: Any): ...
    def quiver(self, *args: Any, **kw: Any): ...
    def barbs(self, *args: Any, **kw: Any): ...
    def fill(self, *args: Any, data: Optional[Any] = ..., **kwargs: Any): ...
    def fill_between(
        self,
        x: Any,
        y1: Any,
        y2: int = ...,
        where: Optional[Any] = ...,
        interpolate: bool = ...,
        step: Optional[Any] = ...,
        **kwargs: Any,
    ): ...
    def fill_betweenx(
        self,
        y: Any,
        x1: Any,
        x2: int = ...,
        where: Optional[Any] = ...,
        step: Optional[Any] = ...,
        interpolate: bool = ...,
        **kwargs: Any,
    ): ...
    def imshow(
        self,
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
        **kwargs: Any,
    ): ...
    def pcolor(
        self,
        *args: Any,
        shading: Optional[Any] = ...,
        alpha: Optional[Any] = ...,
        norm: Optional[Any] = ...,
        cmap: Optional[Any] = ...,
        vmin: Optional[Any] = ...,
        vmax: Optional[Any] = ...,
        **kwargs: Any,
    ): ...
    def pcolormesh(
        self,
        *args: Any,
        alpha: Optional[Any] = ...,
        norm: Optional[Any] = ...,
        cmap: Optional[Any] = ...,
        vmin: Optional[Any] = ...,
        vmax: Optional[Any] = ...,
        shading: Optional[Any] = ...,
        antialiased: bool = ...,
        **kwargs: Any,
    ): ...
    def pcolorfast(
        self,
        *args: Any,
        alpha: Optional[Any] = ...,
        norm: Optional[Any] = ...,
        cmap: Optional[Any] = ...,
        vmin: Optional[Any] = ...,
        vmax: Optional[Any] = ...,
        **kwargs: Any,
    ): ...
    def contour(self, *args: Any, **kwargs: Any): ...
    def contourf(self, *args: Any, **kwargs: Any): ...
    def clabel(self, CS: Any, levels: Optional[Any] = ..., **kwargs: Any): ...
    def hist(
        self,
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
        **kwargs: Any,
    ): ...
    def stairs(
        self,
        values: Any,
        edges: Optional[Any] = ...,
        *,
        orientation: str = ...,
        baseline: int = ...,
        fill: bool = ...,
        **kwargs: Any,
    ): ...
    def hist2d(
        self,
        x: Any,
        y: Any,
        bins: int = ...,
        range: Optional[Any] = ...,
        density: bool = ...,
        weights: Optional[Any] = ...,
        cmin: Optional[Any] = ...,
        cmax: Optional[Any] = ...,
        **kwargs: Any,
    ): ...
    def psd(
        self,
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
        **kwargs: Any,
    ): ...
    def csd(
        self,
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
        **kwargs: Any,
    ): ...
    def magnitude_spectrum(
        self,
        x: Any,
        Fs: Optional[Any] = ...,
        Fc: Optional[Any] = ...,
        window: Optional[Any] = ...,
        pad_to: Optional[Any] = ...,
        sides: Optional[Any] = ...,
        scale: Optional[Any] = ...,
        **kwargs: Any,
    ): ...
    def angle_spectrum(
        self,
        x: Any,
        Fs: Optional[Any] = ...,
        Fc: Optional[Any] = ...,
        window: Optional[Any] = ...,
        pad_to: Optional[Any] = ...,
        sides: Optional[Any] = ...,
        **kwargs: Any,
    ): ...
    def phase_spectrum(
        self,
        x: Any,
        Fs: Optional[Any] = ...,
        Fc: Optional[Any] = ...,
        window: Optional[Any] = ...,
        pad_to: Optional[Any] = ...,
        sides: Optional[Any] = ...,
        **kwargs: Any,
    ): ...
    def cohere(
        self,
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
        **kwargs: Any,
    ): ...
    def specgram(
        self,
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
        **kwargs: Any,
    ): ...
    def spy(
        self,
        Z: Any,
        precision: int = ...,
        marker: Optional[Any] = ...,
        markersize: Optional[Any] = ...,
        aspect: str = ...,
        origin: str = ...,
        **kwargs: Any,
    ): ...
    def matshow(self, Z: Any, **kwargs: Any): ...
    def violinplot(
        self,
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
    ): ...
    def violin(
        self,
        vpstats: Any,
        positions: Optional[Any] = ...,
        vert: bool = ...,
        widths: float = ...,
        showmeans: bool = ...,
        showextrema: bool = ...,
        showmedians: bool = ...,
    ): ...
    table: Any = ...
    stackplot: Any = ...
    streamplot: Any = ...
    tricontour: Any = ...
    tricontourf: Any = ...
    tripcolor: Any = ...
    triplot: Any = ...
