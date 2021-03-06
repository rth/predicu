import matplotlib.pyplot as plt
import seaborn as sns

data_source = ["bedcounts"]
preprocesing_args = {"bedcounts": {"full": False}}


def plot(data):
    counts = data.groupby(["date", "icu_name"]).datetime.count().values
    fig, ax = plt.subplots(1, figsize=(12, 8))
    sns.countplot(counts)
    # ax.set_title('Distributions des nombres de saisies par date et par ICU')
    ax.set_xlabel("Number of inputs per day")
    ax.set_ylabel("Count")
    return fig, dict()
