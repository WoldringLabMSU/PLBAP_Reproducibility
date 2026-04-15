# Reproducibility of Protein-Ligand Binding Affinity Prediction Models on CASF-2016
#### Joelle N. Eaves, Annie Needs, Daniel R. Woldring*  
*Corresponding Author (email: woldring@msu.edu)

## Abstract
Protein-ligand binding affinity prediction (PLBAP) models are routinely benchmarked on the CASF-2016 dataset with Pearson correlation coefficient (PCC) as a common measure of scoring power. Published PCC values are frequently reused as baselines for cross-study comparisons. This practice implicitly assumes that published pipelines remain runnable and that reported metrics can be independently verified. To examine this assumption, we conducted a systematic reproducibility audit of 50 PLBAP models published between 2021 and 2024 that reported CASF-2016 scoring power. For each model, we attempted to reproduce the authors' CASF-2016 inference using only publicly available code, documentation, and pretrained weights. To scaffold this audit and to offer a reusable resource for the community, we introduce a minimal five-item reproducibility checklist for PLBAP pipelines, organized around the artifacts a researcher requires to independently re-run inference: (1) a license, (2) preprocessing and featurization, (3) training, and (4) inference code; and (5) pretrained model weights. We find that only 16/50 pipelines satisfied all checklist items to be consistently runnable. Of those 16 runnable models, only 9 were statistically reproducible (56\% of models). We document common gaps, highlight practices that most reliably enabled independent reproduction, and propose the checklist as a lightweight community standard for future PLBAP releases.

## Investigated PLBAP Models
Pipelines published between 2021 and 2024 were included in our audit if they (1) predict affinity as pK, (2) report PCC for CASF-2016, and (3) are structure-based. This resulted in 50 models. The audit assessed the availability of the five reproducibility-critical artifacts defined in our checklist:
1. Software license
2. Preprocessing & featurization code
3. Training code
4. Inference code
5. Pretrained/finetuned model weights


Of the 50 investigated models, only 17 models had all checklist items and, thus, were considered runnable. For these runnable models, we attempted to reproduce their published CASF-2016 inference performance. The following table shows the link to each model's original repository and our study fork for attempting reproduction. Edits to code were only made to add per-complex time logging, write per-complex predictions to a single csv, and enable command-line utility (largely to resolve hard coding). Otherwise, modifications were only made if code was otherwise non-functional (e.g., RDKit errors resulted in a portion of complexes not being featurized).

| Original Model Repository | Study Fork |
| :--- | :--- |
| [AEScore](https://github.com/RMeli/aescore)<sup>1</sup> | [Study Fork](https://github.com/jeavesj/aescore) |
| [ConBAP](https://github.com/ld139/ConBAP)<sup>2</sup> | [Study Fork](https://github.com/jeavesj/ConBAP) |
| [DEAttentionDTA](https://github.com/whatamazing1/DEAttentionDTA)<sup>3</sup> | [Study Fork](https://github.com/jeavesj/DEAttentionDTA) |
| [delta_LinF9_XGB](https://github.com/cyangNYU/delta_LinF9_XGB)<sup>4</sup> | [Study Fork](https://github.com/jeavesj/delta_LinF9_XGB) |
| [Dynaformer](https://github.com/Minys233/Dynaformer)<sup>5</sup> | [Study Fork](https://github.com/jeavesj/Dynaformer) |
| [egGNN](https://github.com/xfcui/egGNN)<sup>6</sup> | [Study Fork](https://github.com/jeavesj/egGNN) |
| [EGNA](https://github.com/chunqiux/EGNA)<sup>7</sup> | [Study Fork](https://github.com/jeavesj/EGNA) |
| [EHIGN_PLA](https://github.com/guaguabujianle/EHIGN_PLA)<sup>8</sup> | [Study Fork](https://github.com/jeavesj/ehign_pla) |
| [ET_Score](https://github.com/miladrayka/ET_Score)<sup>9</sup> | [Study Fork](https://github.com/jeavesj/ET_Score) |
| [GIGN](https://github.com/guaguabujianle/GIGN)<sup>10</sup> | [Study Fork](https://github.com/jeavesj/GIGN) |
| [HAC-Net](https://github.com/gregory-kyro/HAC-Net)<sup>11</sup> | [Study Fork](https://github.com/jeavesj/HAC-Net) |
| [IGModel](https://github.com/zchwang/IGModel)<sup>12</sup> | [Study Fork](https://github.com/jeavesj/IGModel) |
| [OnionNet-2](https://github.com/zchwang/OnionNet-2)<sup>13</sup> | [Study Fork](https://github.com/jeavesj/OnionNet-2) |
| [PIGNet2](https://github.com/ACE-KAIST/PIGNet2)<sup>14</sup> | [Study Fork](https://github.com/jeavesj/PIGNet2) |
| [saCNN](https://github.com/xfcui/saCNN)<sup>15</sup> | [Study Fork](https://github.com/jeavesj/saCNN) |
| [Sfcnn](https://github.com/bioinfocqupt/Sfcnn)<sup>16</sup> | [Study Fork](https://github.com/jeavesj/Sfcnn) |
| [TopoFormer](https://github.com/WeilabMSU/TopoFormer)<sup>17</sup> | [Study Fork](https://github.com/jeavesj/TopoFormer) |

## Per-complex Predictions & Time Logging
For each above model, per-complex CASF-2016 predictions and associcated preprocessing and inference times are provided as csv files in [PLBAP_results](https://github.com/WoldringLabMSU/PLBAP_Reproducibility/tree/main/PLBAP_results). Aggregated results across all 16 models are also provided in [`2026-03-30_CASF2016_AllModels_PredsAndTimes.csv`](https://github.com/WoldringLabMSU/PLBAP_Reproducibility/blob/main/2026-03-30_CASF2016_AllModels_PredsAndTimes.csv), which was created using [`analysis/aggregate_results.py`](https://github.com/WoldringLabMSU/PLBAP_Reproducibility/blob/main/analysis/aggregate_results.py).

## Data Visualization
Scripts for plotting all manuscript figures, including intermediate bootstrapping, are included in [`analysis/`](https://github.com/WoldringLabMSU/PLBAP_Reproducibility/tree/main/analysis).

## Metadata
Initial attempts at metadata parsing leveraged CLAUDE Code<sup>18</sup> to help create an interactive metadata logging script [`create_reports.py`](https://github.com/WoldringLabMSU/PLBAP_Reproducibility/blob/main/create_reports.py) which was used to generate the per-model metadata reports contained in [`json_reports`](https://github.com/WoldringLabMSU/PLBAP_Reproducibility/tree/main/json_reports).

## References
1. Meli, R., Anighoro, A., Bodkin, M. J., Morris, G. M., & Biggin, P. C. (2021). Learning protein-ligand binding affinity with atomic environment vectors. Journal of Cheminformatics, 13(1), 59.
2. Luo, D., Liu, D., Qu, X., Dong, L., & Wang, B. (2024). Enhancing generalizability in protein–ligand binding affinity prediction with multimodal contrastive learning. Journal of chemical information and modeling, 64(6), 1892-1906.
3. Chen, X., Huang, J., Shen, T., Zhang, H., Xu, L., Yang, M., ... & Yan, J. (2024). DEAttentionDTA: protein–ligand binding affinity prediction based on dynamic embedding and self-attention. Bioinformatics, 40(6), btae319.
4. Yang, C., & Zhang, Y. (2022). Delta machine learning to improve scoring-ranking-screening performances of protein–ligand scoring functions. Journal of chemical information and modeling, 62(11), 2696-2712.
5. Min, Y., Wei, Y., Wang, P., Wang, X., Li, H., Wu, N., ... & Zeng, J. (2024). From Static to Dynamic Structures: Improving Binding Affinity Prediction with Graph‐Based Deep Learning. Advanced Science, 11(40), 2405404.
6. Jiao, Q., Qiu, Z., Wang, Y., Chen, C., Yang, Z., & Cui, X. (2021, December). Edge-gated graph neural network for predicting protein-ligand binding affinities. In 2021 IEEE international conference on bioinformatics and biomedicine (BIBM) (pp. 334-339). IEEE.
7. Xia, C., Feng, S. H., Xia, Y., Pan, X., & Shen, H. B. (2023). Leveraging scaffold information to predict protein–ligand binding affinity with an empirical graph neural network. Briefings in bioinformatics, 24(1), bbac603.
8. Yang, Z., Zhong, W., Lv, Q., Dong, T., Chen, G., & Chen, C. Y. C. (2024). Interaction-based inductive bias in graph neural networks: enhancing protein-ligand binding affinity predictions from 3d structures. IEEE Transactions on Pattern Analysis and Machine Intelligence, 46(12), 8191-8208.
9. Rayka, M., Karimi‐Jafari, M. H., & Firouzi, R. (2021). ET‐score: Improving Protein‐ligand Binding Affinity Prediction Based on Distance‐weighted Interatomic Contact Features Using Extremely Randomized Trees Algorithm. Molecular Informatics, 40(8), 2060084.
10. Yang, Z., Zhong, W., Lv, Q., Dong, T., & Yu-Chian Chen, C. (2023). Geometric interaction graph neural network for predicting protein–ligand binding affinities from 3d structures (gign). The journal of physical chemistry letters, 14(8), 2020-2033.
11. Kyro, G. W., Brent, R. I., & Batista, V. S. (2023). Hac-net: A hybrid attention-based convolutional neural network for highly accurate protein–ligand binding affinity prediction. Journal of Chemical Information and Modeling, 63(7), 1947-1960.
12. Wang, Z., Wang, S., Li, Y., Guo, J., Wei, Y., Mu, Y., ... & Li, W. (2024). A new paradigm for applying deep learning to protein–ligand interaction prediction. Briefings in Bioinformatics, 25(3), bbae145.
13. Wang, Z., Zheng, L., Liu, Y., Qu, Y., Li, Y. Q., Zhao, M., ... & Li, W. (2021). OnionNet-2: a convolutional neural network model for predicting protein-ligand binding affinity based on residue-atom contacting shells. Frontiers in chemistry, 9, 753002.
14. Moon, S., Hwang, S. Y., Lim, J., & Kim, W. Y. (2024). PIGNet2: a versatile deep learning-based protein–ligand interaction prediction model for binding affinity scoring and virtual screening. Digital Discovery, 3(2), 287-299.
15. Wang, Y., Qiu, Z., Jiao, Q., Chen, C., Meng, Z., & Cui, X. (2021, December). Structure-based protein-drug affinity prediction with spatial attention mechanisms. In 2021 IEEE international conference on bioinformatics and biomedicine (BIBM) (pp. 92-97). IEEE.
16. Wang, Y., Wei, Z., & Xi, L. (2022). Sfcnn: a novel scoring function based on 3D convolutional neural network for accurate and stable protein–ligand affinity prediction. BMC bioinformatics, 23(1), 222.
17. Chen, D., Liu, J., & Wei, G. W. (2024). Multiscale topology-enabled structure-to-sequence transformer for protein–ligand interaction predictions. Nature Machine Intelligence, 6(7), 799-810.
18. Anthropic. (2026). Claude 4.6 Sonnet.
