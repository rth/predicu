import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from predicu.data import DEPARTMENT_POPULATION

data_source = ["bedcounts"]


def plot(data):
    d = data
    d = d.groupby(["date", "department"]).sum().reset_index()
    d = d.sort_values(by="date")
    fig, ax = plt.subplots(1, figsize=(20, 10))
    x = d.date.values
    y = (
        d.n_covid_deaths.values
        / d.department.apply(DEPARTMENT_POPULATION.get).values
        * 1e5
    )
    sns.barplot(x=x, y=y, ax=ax, capsize=0.2)
    ax.axvline(6.5, c="red", alpha=0.7, ls="dotted", lw=6.0)
    dates = np.array(sorted(data.date.unique().flatten()))
    xticks = np.arange(0, len(dates), 3)
    ax.set_xticks(xticks)
    ax.set_xticklabels(
        [date.strftime("%d-%m") for date in dates[xticks]], rotation=45,
    )
    ax.set_ylabel("Deaths / 100,000 inhabitants")
    ax.set_xlabel(None)
    txt = ax.text(
        7, 5, r"Start \texttt{ICUBAM}", fontsize="xx-large", color="red"
    )
    txt.set_horizontalalignment("left")
    tikzplotlib_args = {"axis_width": "10cm"}
    return fig, tikzplotlib_args
