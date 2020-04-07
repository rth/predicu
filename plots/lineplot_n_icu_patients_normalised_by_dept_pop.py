import datetime
import json

import matplotlib.gridspec
import matplotlib.lines
import matplotlib.patches
import matplotlib.pyplot as plt
import matplotlib.style
import numpy as np
import pandas as pd
import seaborn as sns

import predicu.data
import predicu.plot
import tikzplotlib

matplotlib.style.use("seaborn-whitegrid")

d = predicu.data.load_combined_icubam_public()

fig, (ax1, ax2) = plt.subplots(2, figsize=(20, 10), sharex=True)

date_range_idx = np.arange(len(d.date.unique()))
for dept, dg in d.groupby("department"):
    dg = dg.sort_values(by="date")
    predicu.plot.plot_int(
        x=date_range_idx,
        y=dg.n_hospitalised_patients / dg.department_pop * 100e3,
        ax=ax1,
        marker=None,
        color=predicu.plot.DEPARTMENT_GRAND_EST_COLOR[dept],
        label=dept,
        lw=2,
    )
    y1 = dg.n_icu_patients_icubam / dg.department_pop * 100e3
    predicu.plot.plot_int(
        x=date_range_idx,
        y=y1,
        ax=ax2,
        marker=None,
        color=predicu.plot.DEPARTMENT_GRAND_EST_COLOR[dept],
        ls="dashed",
        lw=2,
    )
    y2 = dg.n_icu_patients_public / dg.department_pop * 100e3
    predicu.plot.plot_int(
        x=date_range_idx,
        y=y2,
        ax=ax2,
        marker=None,
        color=predicu.plot.DEPARTMENT_GRAND_EST_COLOR[dept],
        ls="solid",
        label=dept,
        lw=2,
    )
    ax2.fill_between(
        x=date_range_idx,
        y1=y1,
        y2=y2,
        facecolor=predicu.plot.DEPARTMENT_GRAND_EST_COLOR[dept],
        alpha=0.3,
    )

ax1.set_ylabel("Patients hospitalisés / 100,000")
ax1.set_title("Évolution du nombre de patients hospitalisés / 100,000 hab.")
ax1.legend(ncol=2)
ax2.set_ylabel("Patients en réanimation / 100,000")
ax2.set_title("Évolution du nombre de patients en réanimation / 100,000 hab.")

ax2.set_xticks(date_range_idx)
ax2.set_xticklabels(
    [date.strftime("%d-%m") for date in sorted(d.date.unique())], rotation=45,
)
ax2.legend(
    [
        matplotlib.lines.Line2D([0], [0], color="k", lw=2, ls="solid"),
        matplotlib.lines.Line2D([0], [0], color="k", lw=2, ls="dashed"),
    ],
    ["Donnée publique", "Donnée ICUBAM"],
    ncol=1,
)
ax2.set_xlim(0, len(date_range_idx) - 1)


# plt.show()
# __import__("sys").exit()

extra_axis_parameters = {
    # r"xticklabel style={font=\tiny}",
}
extra_tikzpicture_parameters = {
    # r"every axis legend/.code={\let\addlegendentry\relax}"
}
tikzplotlib.save(
    "reports/figs/lineplot_n_icu_patients_normalised_by_dept_pop.tex",
    standalone=True,
    axis_width="12cm",
    axis_height="8cm",
    extra_axis_parameters=extra_axis_parameters,
    extra_tikzpicture_parameters=extra_tikzpicture_parameters,
    # strict=True,
)
