import itertools

import matplotlib.cm
import matplotlib.gridspec
import matplotlib.patches
import matplotlib.pyplot as plt
import matplotlib.style
import numpy as np
import pandas as pd
import scipy.interpolate
import seaborn as sns

import predicu.data
import predicu.flow
import predicu.plot
import tikzplotlib

matplotlib.style.use("seaborn-darkgrid")

data = predicu.data.load_all_data()
data = data.loc[data.icu_name.isin(predicu.data.ICU_NAMES_GRAND_EST)]
agg = {col: "sum" for col in predicu.data.BEDCOUNT_COLUMNS}
data = data.groupby(["date", "department"]).agg(agg)
data = data.reset_index()


data = predicu.flow.compute_flow_per_dpt(data)

fig, ax = plt.subplots(1, figsize=(7, 4))

date_idx_range = np.arange(len(data.date.unique()))
sorted_depts = list(
    data.groupby("department")
    .cum_flow.max()
    .sort_values(ascending=False)
    .reset_index()
    .department
)
for i, department in enumerate(sorted_depts):
    y = (
        data.loc[data.department.isin(sorted_depts[i:])]
        .groupby("date")
        .flow.sum()
        .sort_index()
        .values
    )
    predicu.plot.plot_int(
        date_idx_range,
        y,
        ax=ax,
        color=predicu.plot.DEPARTMENT_GRAND_EST_COLOR[department],
        label=department,
        lw=1,
        fill_below=True,
    )
    if i == 0:
        predicu.plot.plot_int(
            date_idx_range, y, ax=ax, color="black", label="Grand Est", lw=3,
        )

ax.set_xticks(np.arange(data.date.unique().shape[0]))
ax.set_xticklabels(
    [date.strftime("%d-%m") for date in sorted(data.date.unique())],
    rotation=45,
)
ax.legend(
    ncol=2,
    handles=[
        matplotlib.patches.Patch(
            facecolor=predicu.plot.DEPARTMENT_GRAND_EST_COLOR[dpt],
            label=dpt,
            linewidth=3,
        )
        for dpt in sorted_depts
    ]
    + [
        matplotlib.patches.Patch(
            facecolor="black", label="Grand Est", linewidth=1,
        )
    ],
    loc="upper left",
)
# fig.tight_layout()
# fig.savefig("fig.png")
# plt.show()
# __import__("sys").exit()

extra_axis_parameters = {
    # r"xticklabel style={font=\scriptsize}",
    # r"yticklabel style={font=\scriptsize}",
}
extra_tikzpicture_parameters = {
    # r"every axis legend/.code={\let\addlegendentry\relax}"
}
tikzplotlib.save(
    "reports/figs/stack_cum_flow_per_dept.tex",
    standalone=True,
    axis_width="14cm",
    axis_height="8cm",
    extra_axis_parameters=extra_axis_parameters,
    extra_tikzpicture_parameters=extra_tikzpicture_parameters,
)
