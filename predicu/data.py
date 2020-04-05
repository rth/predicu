import itertools
import json
import os
import pickle

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DEFAULT_ICUBAM_PATH = "data/all_bedcounts_2020-04-05_13h03.csv"
DEFAULT_PRE_ICUBAM_PATH = "data/pre_icubam_data.csv"
DEFAULT_ICU_NAME_TO_DEPARTMENT_PATH = "data/icu_name_to_department.json"
CUM_COLUMNS = [
    "n_covid_deaths",
    "n_covid_healed",
    "n_covid_transfered",
    "n_covid_refused",
]
NCUM_COLUMNS = [
    "n_covid_free",
    "n_ncovid_free",
    "n_covid_occ",
    "n_ncovid_occ",
]
BEDCOUNT_COLUMNS = CUM_COLUMNS + NCUM_COLUMNS
ALL_COLUMNS = (
    ["icu_name", "date", "datetime", "department"] + CUM_COLUMNS + NCUM_COLUMNS
)
SPREAD_CUM_JUMPS_MAX_JUMP = {
    "n_covid_deaths": 10,
    "n_covid_transfered": 10,
    "n_covid_refused": 10,
    "n_covid_healed": 10,
}


def load_all_data(
    icubam_path=DEFAULT_ICUBAM_PATH,
    pre_icubam_path=DEFAULT_PRE_ICUBAM_PATH,
    clean=True,
    cache=True,
):
    if cache and os.path.isfile("/tmp/predicu_cache.h5"):
        return pd.read_hdf("/tmp/predicu_cache.h5")
    pre_icubam = load_pre_icubam_data(pre_icubam_path)
    icubam = load_icubam_data(icubam_path)
    dates_in_both = set(icubam.date.unique()) & set(pre_icubam.date.unique())
    pre_icubam = pre_icubam.loc[~pre_icubam.date.isin(dates_in_both)]
    d = pd.concat([pre_icubam, icubam])
    if clean:
        d = clean_data(d)
    d = d.sort_values(by=["date", "icu_name"])
    d = d.loc[d.date < pd.to_datetime("2020-04-05").date()]
    if cache and clean:
        d.to_hdf("/tmp/predicu_cache.h5", "values")
    return d


def load_icubam_data(icubam_path=DEFAULT_ICUBAM_PATH):
    d = load_data_file(icubam_path)
    d = d.rename(columns={"create_date": "date"})
    d = format_data(d)
    return d


def load_pre_icubam_data(pre_icubam_path=DEFAULT_PRE_ICUBAM_PATH):
    d = load_data_file(pre_icubam_path)
    d = d.rename(
        columns={
            "Hopital": "icu_name",
            "NbSortieVivant": "n_covid_healed",
            "NbCOVID": "n_covid_occ",
            "NbLitDispo": "n_covid_free",
            "NbDeces": "n_covid_deaths",
            "Date": "date",
        }
    )
    fix_icu_names = {
        "C-Scweitzer": "C-Schweitzer",
        "Bezannes": "C-Bezannes",
        "NHC-Chir": "NHC-ChirC",
    }
    for wrong_name, fixed_name in fix_icu_names.items():
        d.loc[d.icu_name == wrong_name, "icu_name"] = fixed_name
    fix_same_icu = {
        "CHR-SSPI": "CHR-Thionville",
        "CHR-CCV": "CHR-Thionville",
        "Nancy-NC": "Nancy-RCP",
    }
    for old, new in fix_same_icu.items():
        d.loc[d.icu_name == old, "icu_name"] = new
    missing_columns = [
        "n_covid_transfered",
        "n_covid_refused",
        "n_ncovid_free",
        "n_ncovid_occ",
    ]
    for col in missing_columns:
        d[col] = 0
    d = format_data(d)
    return d


def format_data(d):
    d["datetime"] = pd.to_datetime(d["date"])
    d["date"] = d["datetime"].dt.date
    icu_name_to_department = load_icu_name_to_department()
    d["department"] = d.icu_name.apply(icu_name_to_department.get)
    d = d[ALL_COLUMNS]
    return d


def clean_data(d):
    d.loc[d.icu_name == "Mulhouse-Chir", "n_covid_healed"] = np.clip(
        (
            d.loc[d.icu_name == "Mulhouse-Chir", "n_covid_healed"]
            - d.loc[d.icu_name == "Mulhouse-Chir", "n_covid_transfered"]
        ).values,
        a_min=0,
        a_max=None,
    )
    icu_to_first_input_date = dict(
        d.groupby("icu_name")[["date"]].min().itertuples(name=None)
    )
    d = aggregate_multiple_inputs(d)
    # d = fix_noncum_inputs(d)
    d = get_clean_daily_values(d)
    # d = spread_cum_jumps(d, icu_to_first_input_date)
    d = d[ALL_COLUMNS]
    return d


def aggregate_multiple_inputs(d):
    res_dfs = []
    for icu_name, dg in d.groupby("icu_name"):
        dg = dg.set_index("datetime")
        dg = dg.sort_index()
        mask = (
            (dg.index.to_series().diff(1) > pd.Timedelta("15Min"))
            .shift(-1)
            .fillna(True)
            .astype(bool)
        )
        dg = dg.loc[mask]

        for col in CUM_COLUMNS:
            dg[col] = (
                dg[col]
                .rolling(5, center=True, min_periods=1)
                .median()
                .astype(int)
            )

        for col in NCUM_COLUMNS:
            dg[col] = dg[col].fillna(0)
            dg[col] = (
                dg[col]
                .rolling(3, center=True, min_periods=1)
                .median()
                .astype(int)
            )

        for col in CUM_COLUMNS:
            new_col = []
            last_val = -100000
            for idx, row in dg.iterrows():
                if row[col] >= last_val:
                    new_val = row[col]
                else:
                    new_val = last_val
                new_col.append(new_val)
                last_val = new_val
            dg[col] = new_col

        res_dfs.append(dg.reset_index())
    return pd.concat(res_dfs)


def get_clean_daily_values(d):
    icu_name_to_department = load_icu_name_to_department()
    dates = sorted(list(d.date.unique()))
    icu_names = sorted(list(d.icu_name.unique()))
    clean_data_points = list()
    prev_ncum_vals = dict()
    per_icu_prev_data_point = dict()
    for date, icu_name in itertools.product(dates, icu_names):
        sd = d.loc[(d.date == date) & (d.icu_name == icu_name)]
        sd = sd.sort_values(by="datetime")
        new_data_point = {
            "date": date,
            "icu_name": icu_name,
            "department": icu_name_to_department[icu_name],
            "datetime": date,
        }
        new_data_point.update({col: 0 for col in CUM_COLUMNS})
        new_data_point.update({col: 0 for col in NCUM_COLUMNS})
        if icu_name in per_icu_prev_data_point:
            new_data_point.update(
                {
                    col: per_icu_prev_data_point[icu_name][col]
                    for col in BEDCOUNT_COLUMNS
                }
            )
        if len(sd) > 0:
            new_ncum_vals = {col: sd[col].iloc[-1] for col in NCUM_COLUMNS}
            new_data_point.update(
                {col: sd[col].iloc[-1] for col in BEDCOUNT_COLUMNS}
            )
        per_icu_prev_data_point[icu_name] = new_data_point
        clean_data_points.append(new_data_point)
    return pd.DataFrame(clean_data_points)


def spread_cum_jumps(d, icu_to_first_input_date):
    assert np.all(d.date.values == d.datetime.values)
    date_begin_transfered_refused = pd.to_datetime("2020-03-25").date()
    dfs = []
    for icu_name, dg in d.groupby("icu_name"):
        fid = icu_to_first_input_date[icu_name]
        dg = dg.sort_values(by="date")
        dg = dg.reset_index()
        already_fixed_col = set()
        for switch_point, cols in (
            (icu_to_first_input_date[icu_name], CUM_COLUMNS),
            (
                date_begin_transfered_refused,
                ["n_covid_transfered", "n_covid_refused"],
            ),
        ):
            beg = max(dg.date.min(), switch_point - pd.Timedelta("2D"),)
            end = min(dg.date.max(), switch_point + pd.Timedelta("2D"),)
            for col in cols:
                if col in already_fixed_col:
                    continue
                beg_val = dg.loc[dg.date == beg, col].values[0]
                end_val = dg.loc[dg.date == end, col].values[0]
                diff = end_val - beg_val
                if diff >= SPREAD_CUM_JUMPS_MAX_JUMP[col]:
                    spread_beg = dg.date.min()
                    spread_end = end
                    spread_range = pd.date_range(
                        spread_beg, spread_end, freq="1D"
                    ).date
                    spread_value = diff // (spread_end - spread_beg).days
                    remaining = diff % (spread_end - spread_beg).days
                    dg.loc[dg.date.isin(spread_range), col] = np.clip(
                        np.cumsum(np.repeat(spread_value, len(spread_range))),
                        a_min=0,
                        a_max=end_val,
                    )
                    dg.loc[dg.date == end, col] = np.clip(
                        dg.loc[dg.date == end, col].values[0] + remaining,
                        a_min=0,
                        a_max=end_val,
                    )
                    already_fixed_col.add(col)
        dfs.append(dg)
    return pd.concat(dfs)


def load_data_file(data_path):
    ext = data_path.rsplit(".", 1)[-1]
    if ext == "pickle":
        with open(data_path, "rb") as f:
            d = pickle.load(f)
    elif ext == "h5":
        d = pd.read_hdf(data_path)
    elif ext == "csv":
        d = pd.read_csv(data_path)
    else:
        raise ValueError(f"unknown extension {ext}")
    return d


def load_icu_name_to_department(
    icu_name_to_department_path=DEFAULT_ICU_NAME_TO_DEPARTMENT_PATH,
):
    with open(icu_name_to_department_path) as f:
        icu_name_to_department = json.load(f)
    icu_name_to_department["St-Dizier"] = "Haute-Marne"
    return icu_name_to_department


def load_department_population():
    return dict(
        pd.read_csv("data/department_population.csv").itertuples(
            name=None, index=False
        )
    )


def load_france_departments():
    return pd.read_json("data/france_departments.json")


def load_public_data():
    d = pd.read_csv(
        "data/donnees-hospitalieres-covid19-2020-04-04-19h00.csv", sep=";",
    )
    d = d.rename(
        columns={
            "dep": "department_code",
            "jour": "date",
            "hosp": "n_hospitalised_patients",
            "rea": "n_icu_patients",
        }
    )
    d["date"] = pd.to_datetime(d["date"]).dt.date
    return d[
        [
            "date",
            "department_code",
            "n_hospitalised_patients",
            "n_icu_patients",
        ]
    ]


DEPARTMENTS = sorted(list(set(list(load_icu_name_to_department().values()))))
DEPARTMENTS_GRAND_EST = sorted(load_pre_icubam_data().department.unique())
ICU_NAMES_GRAND_EST = sorted(load_pre_icubam_data().icu_name.unique())

CODE_TO_DEPARTMENT = dict(
    load_france_departments()[["departmentCode", "departmentName"]].itertuples(
        name=None, index=False,
    ),
)
DEPARTMENT_TO_CODE = dict(
    load_france_departments()[["departmentName", "departmentCode"]].itertuples(
        name=None, index=False,
    ),
)
public_data = pd.read_csv(
    "data/donnees-hospitalieres-covid19-2020-04-04-19h00.csv", sep=";",
)
