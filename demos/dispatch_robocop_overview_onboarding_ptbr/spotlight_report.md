# Spotlight manual-review report

Resolution 1920×1080. Overlay alpha=170. Font=Carlito.
Source: Textual runtime geometry (no percentage estimates).

| Scene | Topic | Discussed | Actual target | Pre-margin boxes | Final boxes | Margin | Cutouts | Status | Reason |
|---|---|---|---|---|---|---|---|---|---|
| `01_open` | Dispatch (Robocop) | opening-card | opening-card | `[[0.12, 0.14, 0.88, 0.7]]` | `[[80, 100, 1840, 786]]` | [4] | 1 | **PASS** | card content spotlight |
| `02_purpose` | O que é Overview | overview-jobs-area | overview-jobs-area | `[[0.135, 0.0714, 0.555, 0.1]]` | `[[541, 52, 1027, 86]]` | [5] | 1 | **PASS** | geometry-driven |
| `20_strip_what` | O que é | strip:ALL | strip:ALL | `[[0.14, 0.0429, 0.46, 0.0571]]` | `[[549, 31, 917, 49]]` | [3] | 1 | **PASS** | geometry-driven |
| `20b_strip_learn` | O que você aprende aqui | strip:ALL | strip:ALL | `[[0.14, 0.0429, 0.46, 0.0571]]` | `[[549, 31, 917, 49]]` | [3] | 1 | **PASS** | geometry-driven |
| `21_krb_what` | KERBEROS | strip:KERBEROS | strip:KERBEROS | `[[0.14, 0.0429, 0.215, 0.0571]]` | `[[549, 31, 640, 49]]` | [3] | 1 | **PASS** | geometry-driven |
| `21b_krb_action` | Se estiver MISSING ou curto | strip:KERBEROS | strip:KERBEROS | `[[0.14, 0.0429, 0.215, 0.0571]]` | `[[549, 31, 640, 49]]` | [3] | 1 | **PASS** | geometry-driven |
| `21c_krb_password` | Senha | strip:KERBEROS | strip:KERBEROS | `[[0.14, 0.0429, 0.215, 0.0571]]` | `[[549, 31, 640, 49]]` | [3] | 1 | **PASS** | geometry-driven |
| `22_running_what` | RUNNING | strip:RUNNING | strip:RUNNING | `[[0.235, 0.0429, 0.3, 0.0571]]` | `[[657, 31, 736, 49]]` | [3] | 1 | **PASS** | geometry-driven |
| `22b_running_learn` | O que você aprende aqui | strip:RUNNING | strip:RUNNING | `[[0.235, 0.0429, 0.3, 0.0571]]` | `[[657, 31, 736, 49]]` | [3] | 1 | **PASS** | geometry-driven |
| `23_finished_what` | FINISHED 7D | strip:FINISHED 7D | strip:FINISHED 7D | `[[0.32, 0.0429, 0.385, 0.0571]]` | `[[753, 31, 832, 49]]` | [3] | 1 | **PASS** | geometry-driven |
| `23b_finished_learn` | O que você aprende aqui | strip:FINISHED 7D | strip:FINISHED 7D | `[[0.32, 0.0429, 0.385, 0.0571]]` | `[[753, 31, 832, 49]]` | [3] | 1 | **PASS** | geometry-driven |
| `24_failed_what` | FAILED 7D | strip:FAILED 7D | strip:FAILED 7D | `[[0.405, 0.0429, 0.46, 0.0571]]` | `[[849, 31, 917, 49]]` | [3] | 1 | **PASS** | geometry-driven |
| `24b_failed_action` | O que fazer | strip:FAILED 7D | strip:FAILED 7D | `[[0.405, 0.0429, 0.46, 0.0571]]` | `[[849, 31, 917, 49]]` | [3] | 1 | **PASS** | geometry-driven |
| `30_title_what` | Lista de jobs | jobs-title | jobs-title | `[[0.135, 0.0714, 0.305, 0.0857]]` | `[[543, 54, 742, 72]]` | [3] | 1 | **PASS** | geometry-driven |
| `30b_title_learn` | O que você aprende aqui | jobs-title | jobs-title | `[[0.135, 0.0714, 0.305, 0.0857]]` | `[[543, 54, 742, 72]]` | [3] | 1 | **PASS** | geometry-driven |
| `31_empty_what` | Lista vazia | jobs-empty | jobs-empty | `[[0.14, 0.0857, 0.99, 0.1286]]` | `[[547, 64, 1519, 109]]` | [5] | 1 | **PASS** | geometry-driven |
| `31b_empty_action` | O que fazer | jobs-empty | jobs-empty | `[[0.14, 0.0857, 0.99, 0.1286]]` | `[[547, 64, 1519, 109]]` | [5] | 1 | **PASS** | geometry-driven |
| `40_table_what` | O que é | jobs-table | jobs-table | `[[0.14, 0.0857, 0.555, 0.1714]]` | `[[547, 64, 1027, 143]]` | [5] | 1 | **PASS** | geometry-driven |
| `40b_table_learn` | O que você aprende aqui | jobs-table | jobs-table | `[[0.14, 0.0857, 0.555, 0.1714]]` | `[[547, 64, 1027, 143]]` | [5] | 1 | **PASS** | geometry-driven |
| `41_col_id` | Coluna ID | column:ID | column:ID | `[[0.14, 0.0857, 0.22, 0.1714]]` | `[[548, 65, 647, 142]]` | [4] | 1 | **PASS** | geometry-driven |
| `41b_col_id_use` | Como usar | column:ID | column:ID | `[[0.14, 0.0857, 0.22, 0.1714]]` | `[[548, 65, 647, 142]]` | [4] | 1 | **PASS** | geometry-driven |
| `42_col_src` | Coluna Source | column:Source | column:Source | `[[0.22, 0.0857, 0.31, 0.1714]]` | `[[639, 65, 748, 142]]` | [4] | 1 | **PASS** | geometry-driven |
| `42b_col_src_use` | Como usar | column:Source | column:Source | `[[0.22, 0.0857, 0.31, 0.1714]]` | `[[639, 65, 748, 142]]` | [4] | 1 | **PASS** | geometry-driven |
| `43_col_dst` | Coluna Destination | column:Destination | column:Destination | `[[0.31, 0.0857, 0.415, 0.1714]]` | `[[740, 65, 867, 142]]` | [4] | 1 | **PASS** | geometry-driven |
| `43b_col_dst_use` | Como usar | column:Destination | column:Destination | `[[0.31, 0.0857, 0.415, 0.1714]]` | `[[740, 65, 867, 142]]` | [4] | 1 | **PASS** | geometry-driven |
| `44_col_state` | Coluna State | column:State | column:State | `[[0.415, 0.0857, 0.51, 0.1714]]` | `[[859, 65, 975, 142]]` | [4] | 1 | **PASS** | geometry-driven |
| `44b_col_state_learn` | O que você aprende aqui | column:State | column:State | `[[0.415, 0.0857, 0.51, 0.1714]]` | `[[859, 65, 975, 142]]` | [4] | 1 | **PASS** | geometry-driven |
| `50_st_pending` | PENDING | cell:State:PENDING | cell:State:PENDING | `[[0.415, 0.1143, 0.51, 0.1286]]` | `[[860, 89, 974, 107]]` | [3] | 1 | **PASS** | geometry-driven |
| `50b_st_pending_act` | O que fazer | cell:State:PENDING | cell:State:PENDING | `[[0.415, 0.1143, 0.51, 0.1286]]` | `[[860, 89, 974, 107]]` | [3] | 1 | **PASS** | geometry-driven |
| `51_st_running` | RUNNING | cell:State:RUNNING | cell:State:RUNNING | `[[0.415, 0.1, 0.51, 0.1143]]` | `[[860, 78, 974, 95]]` | [3] | 1 | **PASS** | geometry-driven |
| `51b_st_running_act` | O que fazer | cell:State:RUNNING | cell:State:RUNNING | `[[0.415, 0.1, 0.51, 0.1143]]` | `[[860, 78, 974, 95]]` | [3] | 1 | **PASS** | geometry-driven |
| `52_st_ok` | SUCCEEDED | cell:State:SUCCEEDED | cell:State:SUCCEEDED | `[[0.415, 0.1571, 0.51, 0.1714]]` | `[[860, 124, 974, 141]]` | [3] | 1 | **PASS** | geometry-driven |
| `52b_st_ok_act` | O que fazer | cell:State:SUCCEEDED | cell:State:SUCCEEDED | `[[0.415, 0.1571, 0.51, 0.1714]]` | `[[860, 124, 974, 141]]` | [3] | 1 | **PASS** | geometry-driven |
| `53_st_fail` | FAILED | cell:State:FAILED | cell:State:FAILED | `[[0.415, 0.1429, 0.51, 0.1571]]` | `[[860, 112, 974, 130]]` | [3] | 1 | **PASS** | geometry-driven |
| `53b_st_fail_act` | O que fazer | cell:State:FAILED | cell:State:FAILED | `[[0.415, 0.1429, 0.51, 0.1571]]` | `[[860, 112, 974, 130]]` | [3] | 1 | **PASS** | geometry-driven |
| `54_st_cancel` | CANCELLED | cell:State:CANCELLED | cell:State:CANCELLED | `[[0.415, 0.1286, 0.51, 0.1429]]` | `[[860, 101, 974, 118]]` | [3] | 1 | **PASS** | geometry-driven |
| `54b_st_cancel_act` | O que fazer | cell:State:CANCELLED | cell:State:CANCELLED | `[[0.415, 0.1286, 0.51, 0.1429]]` | `[[860, 101, 974, 118]]` | [3] | 1 | **PASS** | geometry-driven |
| `55_col_elapsed` | Coluna Elapsed | column:Elapsed | column:Elapsed | `[[0.51, 0.0857, 0.555, 0.1714]]` | `[[967, 65, 1026, 142]]` | [4] | 1 | **PASS** | geometry-driven |
| `55b_col_elapsed_use` | Como usar | column:Elapsed | column:Elapsed | `[[0.51, 0.0857, 0.555, 0.1714]]` | `[[967, 65, 1026, 142]]` | [4] | 1 | **PASS** | geometry-driven |
| `60_filter_what` | Filtro | jobs-filter | jobs-filter | `[[0.135, 0.0857, 0.995, 0.1286]]` | `[[542, 65, 1524, 108]]` | [4] | 1 | **PASS** | geometry-driven |
| `60b_filter_when` | Quando usar | jobs-filter | jobs-filter | `[[0.135, 0.0857, 0.995, 0.1286]]` | `[[542, 65, 1524, 108]]` | [4] | 1 | **PASS** | geometry-driven |
| `61_filter_ex` | Exemplo | jobs-filter+table | jobs-filter+table | `[[0.135, 0.0857, 0.995, 0.1286], [0.14, 0.1286, 0.555, 0.1571]]` | `[[541, 64, 1525, 109], [547, 99, 1027, 132]]` | [5, 5] | 2 | **PASS** | geometry-driven |
| `70_detail_what` | Painel de detalhe | detail-pane | detail-pane | `[[0.135, 0.8143, 0.995, 0.9]]` | `[[541, 654, 1525, 734]]` | [5] | 1 | **PASS** | geometry-driven |
| `70b_detail_learn` | O que você aprende aqui | detail-pane | detail-pane | `[[0.135, 0.8143, 0.995, 0.9]]` | `[[541, 654, 1525, 734]]` | [5] | 1 | **PASS** | geometry-driven |
| `71_detail_title` | Título do detalhe | detail-title | detail-title | `[[0.145, 0.8286, 0.985, 0.8429]]` | `[[555, 668, 1512, 685]]` | [3] | 1 | **PASS** | geometry-driven |
| `72_detail_log` | Prévia do log | detail-log | detail-log | `[[0.145, 0.8429, 0.985, 0.8857]]` | `[[553, 677, 1514, 722]]` | [5] | 1 | **PASS** | geometry-driven |
| `80_events` | Eventos recentes | event-trail | event-trail | `[[0.135, 0.9429, 0.795, 0.9857]]` | `[[542, 759, 1297, 802]]` | [4] | 1 | **PASS** | geometry-driven |
| `81_newjob` | New Job [N] | new-job | new-job | `[[0.8, 0.9429, 0.86, 0.9857]]` | `[[1295, 759, 1371, 802]]` | [4] | 1 | **PASS** | geometry-driven |
| `82_viewlogs` | View Logs [V] | view-logs | view-logs | `[[0.865, 0.9429, 0.925, 0.9857]]` | `[[1369, 759, 1445, 802]]` | [4] | 1 | **PASS** | geometry-driven |
| `82b_viewlogs_when` | Quando usar | view-logs | view-logs | `[[0.865, 0.9429, 0.925, 0.9857]]` | `[[1369, 759, 1445, 802]]` | [4] | 1 | **PASS** | geometry-driven |
| `83_cancel` | Cancel [C] | cancel | cancel | `[[0.93, 0.9429, 0.99, 0.9857]]` | `[[1442, 759, 1518, 802]]` | [4] | 1 | **PASS** | geometry-driven |
| `83b_cancel_note` | Atenção | cancel | cancel | `[[0.93, 0.9429, 0.99, 0.9857]]` | `[[1442, 759, 1518, 802]]` | [4] | 1 | **PASS** | geometry-driven |
| `90_close` | Resumo | closing-card | closing-card | `[[0.12, 0.14, 0.88, 0.7]]` | `[[80, 100, 1840, 786]]` | [4] | 1 | **PASS** | card content spotlight |

Scenes with >1 cutout: 1
Total scenes reviewed: 53

**Overall: PASS**