import os
from itertools import combinations

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import matplotlib.cm as cm
import matplotlib.colors as mcolors

out_dir = '/mnt/research/woldring_lab/Members/Eaves/PLBAP_Reproducibility/analysis/results'
performance_data = '/mnt/research/woldring_lab/Members/Eaves/PLBAP_Reproducibility/2026-04-02_CASF2016_AllModels_PredsAndTimes.csv'
models = ['AEScore', 'ConBAP', 'DEAttentionDTA', 'deltaLinF9XGB', 'Dynaformer', 'egGNN', 'EGNA', 'EHIGN-PLA', 'ET-Score', 'GIGN', 'HAC-Net', 'IGModel', 'OnionNet-2', 'PIGNet2', 'saCNN', 'SFCNN']
rep_models = ['DEAttentionDTA', 'deltaLinF9XGB', 'Dynaformer', 'EGNA', 'EHIGN-PLA', 'GIGN', 'OnionNet-2', 'saCNN', 'SFCNN']
palette = ['0.7', 'w']

def add_times(row):
    if not np.isnan(row['t_tot_s']):
        return row['t_tot_s']
    elif not np.isnan(row['t_prep_s']) and not np.isnan(row['t_inf_s']):
        return row['t_inf_s'] + row['t_prep_s']
    elif not np.isnan(row['t_inf_s']):
        return row['t_inf_s']

statuses = [
    {'Model': 'AEScore', 'Status': 'Not Reproduced', 'Reported PCC': 0.830},
    {'Model': 'ConBAP', 'Status': 'Not Reproduced', 'Reported PCC': 0.864},
    {'Model': 'DEAttentionDTA', 'Status': 'Reproduced', 'Reported PCC': 0.819},
    {'Model': 'deltaLinF9XGB', 'Status': 'Reproduced', 'Reported PCC': 0.845},
    {'Model': 'Dynaformer', 'Status': 'Reproduced', 'Reported PCC': 0.827},
    {'Model': 'egGNN', 'Status': 'Not Reproduced', 'Reported PCC': 0.860},
    {'Model': 'EGNA', 'Status': 'Reproduced', 'Reported PCC': 0.842},
    {'Model': 'EHIGN-PLA', 'Status': 'Reproduced', 'Reported PCC': 0.854},
    {'Model': 'ET-Score', 'Status': 'Not Reproduced', 'Reported PCC': 0.827},
    {'Model': 'GIGN', 'Status': 'Reproduced', 'Reported PCC': 0.840},
    {'Model': 'HAC-Net', 'Status': 'Not Reproduced', 'Reported PCC': 0.830},
    {'Model': 'IGModel', 'Status': 'Not Reproduced', 'Reported PCC': 0.831},
    {'Model': 'OnionNet-2', 'Status': 'Reproduced', 'Reported PCC': 0.864},
    {'Model': 'PIGNet2', 'Status': 'Not Reproduced', 'Reported PCC': 0.747},
    {'Model': 'saCNN', 'Status': 'Reproduced', 'Reported PCC': 0.865},
    {'Model': 'SFCNN', 'Status': 'Reproduced', 'Reported PCC': 0.793}
]
status_df = pd.DataFrame(statuses)

pred_df = pd.read_csv(performance_data)
pred_df['t_tot_s'] = pred_df.apply(add_times, axis=1)

pred_df = pred_df.merge(status_df, on='Model', how='left')

fig, ax = plt.subplots(figsize=(8,4))
g = sns.violinplot(data=pred_df, x='Model', y='t_tot_s', hue='Status', order=models, hue_order=['Reproduced', 'Not Reproduced'], palette=palette, log_scale=10, density_norm='width', linecolor='k')
plt.ylabel('Time Per Complex, Seconds')
plt.xlabel('')
plt.xticks(rotation=45)

# positions = range(1,17)
# count = 0
# for model in models:
#     df = pred_df[pred_df['Model']==model]
#     max_val = np.max(df['t_tot_s'])
#     x_coord = count
#     count += 1
#     label_text = df['Reported PCC'].values[0]
#     ax.annotate(label_text, (x_coord, max_val), textcoords="offset points", xytext=(0, 10), ha='center')

plt.tight_layout()
plt.savefig(f'{out_dir}/compute_time.png', dpi=1200)


fig, ax = plt.subplots(figsize=(6,4))
rep_df = pred_df[pred_df['Status'] == 'Reproduced']
g = sns.violinplot(data=pred_df, x='Model', y='t_tot_s', order=rep_models, color='w', log_scale=10, density_norm='width', linecolor='k')
plt.ylabel('Time Per Complex, Seconds')
plt.xlabel('')
plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig(f'{out_dir}/compute_time-ReproducedOnly.png', dpi=1200)


fig, ax = plt.subplots(figsize=(8,4))
rep_df = pred_df[pred_df['Status'] == 'Reproduced']

norm = mcolors.Normalize(vmin=rep_df['Reported PCC'].min(), vmax=rep_df['Reported PCC'].max())
mapper = cm.ScalarMappable(norm=norm, cmap='binary')
model_colors = [mapper.to_rgba(rep_df[rep_df['Model'] == m]['Reported PCC'].values[0]) for m in rep_models]

g = sns.violinplot(data=rep_df, x='Model', y='t_tot_s', order=rep_models, hue='Reported PCC', log_scale=10, density_norm='width', linecolor='k', palette=model_colors, legend=False)
plt.ylabel('Time Per Complex, Seconds')
plt.xlabel('')
plt.xticks(rotation=45)

cbar = fig.colorbar(mapper, ax=ax)
cbar.set_label('Reported PCC')

plt.tight_layout()
plt.savefig(f'{out_dir}/compute_time-ReproducedOnly-PCC-BW.png', dpi=1200)