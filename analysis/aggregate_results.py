import pandas as pd
import numpy as np
import os

preds_dir = '/mnt/research/woldring_lab/Members/Eaves/PLBAP_Reproducibility/PLBAP_results'

models = ['AEScore', 'ConBAP', 'DEAttentionDTA', 'delta_LinF9_XGB', 'Dynaformer', 'egGNN', 'EGNA', 'EHIGN-PLA', 'ET-Score', 'GIGN', 'HAC-Net', 'IGModel', 'OnionNet-2', 'PIGNet2', 'saCNN', 'SFCNN']
pdbid_cols = ['pdb_id'] # will change to 'pdbid'
inf_t_cols = ['time_inference_s', 'time_inf_s'] # will change to 't_inf_s'
prep_t_cols = ['time_featurize_s'] # will change to 't_prep_s'
tot_t_cols = ['time_s'] # will change to 't_tot_s'
pred_cols = ['pKa_prediction', 'prediction', 'avg', 'pred_pkd'] # will change to 'pK_predicted'

cols_to_keep = ['pdbid', 'pK_predicted', 't_inf_s', 't_prep_s', 't_tot_s']

df_list = []
for model in models:
    model = model.replace("_", "")
    filename = os.path.join(preds_dir, f'casf2016_{model}_preds_and_times.csv')
    if not os.path.exists(filename):
        filename = os.path.join(preds_dir, f'casf2016_{model.lower()}_preds_and_times.csv')
        if not os.path.exists(filename):
            filename = os.path.join(preds_dir, f'casf2016_{model.replace("-", "").lower()}_preds_and_times.csv')
            if not os.path.exists(filename):
                filename = os.path.join(preds_dir, f'casf2016_{model.replace("-", "")}_preds_and_times.csv')
                if not os.path.exists(filename):
                    raise Exception(f'No success for {model}')
    
    df = pd.read_csv(filename)
    
    if model=='Dynaformer':
        df = df[df['name'].str.endswith('crystal')]
    
    if 'pdb_id' in df.columns:
        df.rename(columns={'pdb_id': 'pdbid'}, inplace=True)
    df['pdbid'] = df['pdbid'].str.split('-', expand=True)[0]
    df['pdbid'] = df['pdbid'].str.split('_', expand=True)[0]

    if 't_inf_s' not in df.columns:
        for col in inf_t_cols:
            if col in df.columns:
                df.rename(columns={col: 't_inf_s'}, inplace=True)
    if 't_prep_s' not in df.columns:
        for col in prep_t_cols:
            if col in df.columns:
                df.rename(columns={col: 't_prep_s'}, inplace=True)
    if 't_tot_s' not in df.columns:
        for col in tot_t_cols:
            if col in df.columns:
                df.rename(columns={col: 't_tot_s'}, inplace=True)
    if 't_tot_s' not in df.columns:
        try:
            df['t_tot_s'] = df['t_inf_s'] + df['t_prep_s']
        except KeyError:
            df['t_tot_s'] = df['t_inf_s']
    if 'pK_predicted' not in df.columns:
        for col in pred_cols:
                df.rename(columns={col: 'pK_predicted'}, inplace=True)
    
    cols_to_drop = []
    for col in df.columns:
        if col not in cols_to_keep:
            cols_to_drop.append(col)
    df.drop(columns=cols_to_drop, inplace=True)
    
    df['Model'] = model
    
    df_list.append(df)

true_df = pd.read_csv('/mnt/research/woldring_lab/Members/Eaves/PLBAP_Reproducibility/test2016.csv')
true_df.rename(columns={'-logKd/Ki': 'pK_true'}, inplace=True)

df = pd.concat(df_list)
df = df.merge(true_df, how='left', on='pdbid')

df.to_csv('/mnt/research/woldring_lab/Members/Eaves/PLBAP_Reproducibility/2026-03-30_CASF2016_AllModels_PredsAndTimes.csv', index=False)
