import os
from itertools import combinations

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

out_dir = '/mnt/research/woldring_lab/Members/Eaves/PLBAP_Reproducibility/analysis/results'
preds_csv = os.path.join(out_dir, 'performance_bootstrap_summary.csv')
# models = ['AEScore', 'ConBAP', 'DEAttentionDTA', 'Dynaformer', 'egGNN', 'EGNA', 'EHIGN-PLA', 'ET-Score', 'GIGN', 'HAC-Net', 'IGModel', 'OnionNet-2', 'PIGNet2', 'SFCNN']
models = ['AEScore', 'ConBAP', 'DEAttentionDTA', 'deltaLinF9XGB', 'Dynaformer', 'egGNN', 'EGNA', 'EHIGN-PLA', 'ET-Score', 'GIGN', 'HAC-Net', 'IGModel', 'OnionNet-2', 'PIGNet2', 'saCNN', 'SFCNN']
hue_order = ['Original', 'Study']
palette = ['w', '0.6']
# palette = 'colorblind'

reported_pcc = [
    {'Model': 'AEScore', 'PCC': 0.830},
    {'Model': 'ConBAP', 'PCC': 0.864},
    {'Model': 'DEAttentionDTA', 'PCC': 0.819},
    {'Model': 'deltaLinF9XGB', 'PCC': 0.845},
    {'Model': 'Dynaformer', 'PCC': 0.827},
    {'Model': 'egGNN', 'PCC': 0.860},
    {'Model': 'EGNA', 'PCC': 0.842},
    {'Model': 'EHIGN-PLA', 'PCC': 0.854},
    {'Model': 'ET-Score', 'PCC': 0.827},
    {'Model': 'GIGN', 'PCC': 0.840},
    {'Model': 'HAC-Net', 'PCC': 0.830},
    {'Model': 'IGModel', 'PCC': 0.831},
    {'Model': 'OnionNet-2', 'PCC': 0.864},
    {'Model': 'PIGNet2', 'PCC': 0.747},
    {'Model': 'saCNN', 'PCC': 0.865},
    {'Model': 'SFCNN', 'PCC': 0.793}
]

def add_ci_errorbars_for_hue(ax, ci_df, x_order, hue_order, hue_level, y_col='PCC', lo_col='ci_lo', hi_col='ci_hi'):

    lut = {}
    for _, r in ci_df.iterrows():
        lut[str(r['Model'])] = (float(r[y_col]), float(r[lo_col]), float(r[hi_col]))

    if not hasattr(ax, "containers") or len(ax.containers) == 0:
        raise RuntimeError("No bar containers found. Did you call sns.barplot first?")

    if hue_level not in hue_order:
        raise ValueError(f"hue_level='{hue_level}' not in hue_order={hue_order}")

    container = ax.containers[hue_order.index(hue_level)]

    bars = list(container)
    if len(bars) != len(x_order):
        print(f"[WARN] bars for hue='{hue_level}' = {len(bars)} != len(x_order) = {len(x_order)}. "
              "Proceeding by zipping min length.")

    for bar, model in zip(bars, x_order):
        if model not in lut:
            continue

        y, lo, hi = lut[model]
        if not (np.isfinite(y) and np.isfinite(lo) and np.isfinite(hi)):
            continue

        x = bar.get_x() + bar.get_width() / 2
        ax.errorbar(
            x, y,
            yerr=[[y - lo], [hi - y]],
            fmt='none',
            ecolor='black',
            capsize=2,
            lw=1.2,
            zorder=10
        )

reported_df = pd.DataFrame(reported_pcc)
reported_df['Study'] = 'Original'

pred_df = pd.read_csv(preds_csv)
pred_df = pred_df[pred_df['metric'] == 'pcc']
pred_df.rename(columns={'value': 'PCC'}, inplace=True)
pred_df['Study'] = 'Study'

pcc_df = pd.concat([reported_df, pred_df]).reset_index(drop=True)
print(pcc_df)

fig = plt.figure(figsize=(6,4))
g = sns.barplot(
        data=pcc_df,
        x='Model',
        y='PCC',
        hue='Study',
        order=models,
        hue_order=hue_order,
        palette=palette,
        edgecolor='k'
    )
plt.xlabel('')
plt.xticks(rotation=90)
plt.ylim((0.2,0.9))
plt.legend(title='', ncol=2, loc='lower right', bbox_to_anchor=(1, 1.01))

add_ci_errorbars_for_hue(ax=g, ci_df=pred_df, x_order=models, hue_order=hue_order,
    hue_level='Study', y_col='PCC', lo_col='ci_lo', hi_col='ci_hi'
)

plt.tight_layout()
plt.savefig(f'{out_dir}/PCC_reproduction_barplot-BW-FixedLegend.png', dpi=1200)