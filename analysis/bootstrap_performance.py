import os
from itertools import combinations

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats


performance_data = '/mnt/research/woldring_lab/Members/Eaves/PLBAP_Reproducibility/2026-03-30_CASF2016_AllModels_PredsAndTimes.csv'
out_dir = '/mnt/research/woldring_lab/Members/Eaves/PLBAP_Reproducibility/analysis/results'
os.makedirs(out_dir, exist_ok=True)

n_boot = 5000
seed = 42
ci_alpha = 0.05
matplotlib.rcParams.update({'font.size': 12})

models = ['AEScore', 'ConBAP', 'DEAttentionDTA', 'deltaLinF9XGB', 'Dynaformer', 'egGNN', 'EGNA', 'EHIGN-PLA', 'ET-Score', 'GIGN', 'HAC-Net', 'IGModel', 'OnionNet-2', 'PIGNet2', 'saCNN', 'SFCNN']

df = pd.read_csv(performance_data)
df['pdbid'] = df['pdbid'].astype(str).str.lower().str.strip()
df['Model'] = df['Model'].astype(str).str.strip()

required_cols = {'pdbid', 'Model', 'pK_true', 'pK_predicted'}
missing = required_cols - set(df.columns)
if missing:
    raise ValueError(f"Missing required columns in CSV: {missing}")

def pcc(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    if y_true.size < 2:
        return np.nan
    if np.std(y_true) == 0 or np.std(y_pred) == 0:
        return np.nan
    return float(np.corrcoef(y_true, y_pred)[0, 1])

def rmse(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

def bootstrap_ci(y_true, y_pred, metric_funct, rng, n_boot=20000, alpha=0.05):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    n = y_true.shape[0]

    point = metric_funct(y_true, y_pred)

    boots = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        v = metric_funct(y_true[idx], y_pred[idx])
        if np.isfinite(v):
            boots.append(v)

    boots = np.asarray(boots, dtype=float)
    if boots.size == 0:
        return point, np.nan, np.nan

    lo = float(np.quantile(boots, alpha / 2))
    hi = float(np.quantile(boots, 1 - alpha / 2))
    return point, lo, hi

def add_ci_errorbars(ax, plot_df, model_order):
    # plot_df must contain Model, value, ci_lo, ci_hi
    lut = {r['Model']: (r['value'], r['ci_lo'], r['ci_hi']) for _, r in plot_df.iterrows()}

    patches = [p for p in ax.patches if hasattr(p, 'get_x') and hasattr(p, 'get_width')]
    if len(patches) == 0:
        print('[WARN] No bar patches found on this axis.')
        return

    # If seaborn created any extra patches, align to the first len(model_order)
    patches = patches[:len(model_order)]

    for patch, m in zip(patches, model_order):
        if m not in lut:
            continue
        y, lo, hi = lut[m]
        if not (np.isfinite(y) and np.isfinite(lo) and np.isfinite(hi)):
            continue

        x = patch.get_x() + patch.get_width() / 2
        ax.errorbar(
            x, y,
            yerr=[[y - lo], [hi - y]],
            fmt='none',
            ecolor='black',
            capsize=3,
            lw=1.2,
            zorder=10
        )

d = df[df['Model'].isin(models)].copy()

agg = (
    d.groupby(['Model', 'pdbid'], as_index=False)
     .agg(pK_true=('pK_true', 'first'),
          pK_predicted=('pK_predicted', 'mean'))
)

rng = np.random.default_rng(seed)

metric_rows = []
for model in models:
    a = agg[agg['Model'] == model].copy()
    if a.empty:
        continue

    y_true = a['pK_true'].to_numpy()
    y_pred = a['pK_predicted'].to_numpy()

    val, lo, hi = bootstrap_ci(y_true, y_pred, pcc, rng, n_boot=n_boot, alpha=ci_alpha)
    metric_rows.append({'Model': model, 'metric': 'pcc', 'value': val, 'ci_lo': lo, 'ci_hi': hi, 'n': len(a)})

    val, lo, hi = bootstrap_ci(y_true, y_pred, rmse, rng, n_boot=n_boot, alpha=ci_alpha)
    metric_rows.append({'Model': model, 'metric': 'rmse', 'value': val, 'ci_lo': lo, 'ci_hi': hi, 'n': len(a)})

met = pd.DataFrame(metric_rows)
met.to_csv(f'{out_dir}/performance_bootstrap_summary.csv', index=False)


