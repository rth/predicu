import numpy as np

from predicu.data import CUM_COLUMNS
from predicu.preprocessing import preprocess_bedcounts
from predicu.tests.utils import load_test_data


def test_bedcounts_data_preprocessing():
    test_data = load_test_data()
    preprocessed = preprocess_bedcounts(test_data["bedcounts"])
    assert len(preprocessed) > 0
    for icu_name, dg in preprocessed.groupby("icu_name"):
        dg = dg.sort_values(by="date")
        for col in CUM_COLUMNS:
            diffs = dg[col].diff(1).fillna(0).values
            assert np.all(diffs >= 0)
