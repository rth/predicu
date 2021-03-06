import matplotlib.gridspec
import matplotlib.lines
import matplotlib.patches
import matplotlib.pyplot as plt
import matplotlib.style
import numpy as np

from predicu.plot import DEPARTMENT_COLOR, plot_int

data_source = ["combined_bedcounts_public"]


def plot(data):
    fig, (ax1, ax2) = plt.subplots(2, figsize=(10, 10), sharex=True)
    date_range_idx = np.arange(len(data.date.unique()))
    for dept, dg in data.groupby("department"):
        dg = dg.sort_values(by="date")
        plot_int(
            x=date_range_idx,
            y=dg.n_hospitalised_patients / dg.department_pop * 100e3,
            ax=ax1,
            marker=None,
            color=DEPARTMENT_COLOR[dept],
            label=dept,
            lw=2,
        )
        y1 = dg.n_icu_patients_icubam / dg.department_pop * 100e3
        plot_int(
            x=date_range_idx,
            y=y1,
            ax=ax2,
            marker=None,
            color=DEPARTMENT_COLOR[dept],
            ls="dashed",
            lw=2,
        )
        y2 = dg.n_icu_patients_public / dg.department_pop * 100e3
        plot_int(
            x=date_range_idx,
            y=y2,
            ax=ax2,
            marker=None,
            color=DEPARTMENT_COLOR[dept],
            ls="solid",
            label=dept,
            lw=2,
        )
        ax2.fill_between(
            x=date_range_idx,
            y1=y1,
            y2=y2,
            facecolor=DEPARTMENT_COLOR[dept],
            alpha=0.3,
        )

    ax1.set_ylabel("Population-normalised nb of hospitalised patients")
    ax1.set_title(
        "Evolution of nb of hospitalised patients / 100,000 inhabitants"
    )
    ax1.legend(ncol=2)
    ax2.set_ylabel("Population-normalised nb of ICU patients")
    ax2.set_title("Evolution of nb of ICU patients / 100,000 inhabitants")
    dates = np.array(sorted(data.date.unique().flatten()))
    xticks = np.arange(0, len(dates), 3)
    for ax in [ax1, ax2]:
        ax.set_xticks(xticks)
        ax.set_xticklabels(
            [date.strftime("%d-%m") for date in dates[xticks]], rotation=45,
        )
    ax2.legend(
        [
            matplotlib.lines.Line2D([0], [0], color="k", lw=2, ls="solid"),
            matplotlib.lines.Line2D([0], [0], color="k", lw=2, ls="dashed"),
        ],
        ["Public data", "ICUBAM data"],
        ncol=1,
    )
    ax2.set_xlim(0, len(date_range_idx) - 1)
    tikzplotlib_kwargs = dict(axis_width="12cm", axis_height="8cm",)
    return fig, tikzplotlib_kwargs
