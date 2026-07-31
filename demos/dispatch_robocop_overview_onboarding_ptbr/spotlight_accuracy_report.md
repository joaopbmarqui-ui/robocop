# Spotlight accuracy report (geometry-driven)

Every spotlight is built from captured Textual element bounds (widget region, DataTable column/cell region, or strip glyph span).

| Scene | Discussed element | Actual target element | Target bbox (norm) | Spotlight bbox (px) | Result |
|---|---|---|---|---|---|
| `01_open` | opening-card | opening-card | `[[0.12, 0.14, 0.88, 0.7]]` | `[[80, 100, 1840, 786]]` | **PASS** |
| `02_purpose` | overview-jobs-area | overview-jobs-area | `[[0.135, 0.0714, 0.555, 0.1]]` | `[[541, 52, 1027, 86]]` | **PASS** |
| `20_strip_what` | strip:ALL | strip:ALL | `[[0.14, 0.0429, 0.46, 0.0571]]` | `[[549, 31, 917, 49]]` | **PASS** |
| `20b_strip_learn` | strip:ALL | strip:ALL | `[[0.14, 0.0429, 0.46, 0.0571]]` | `[[549, 31, 917, 49]]` | **PASS** |
| `21_krb_what` | strip:KERBEROS | strip:KERBEROS | `[[0.14, 0.0429, 0.215, 0.0571]]` | `[[549, 31, 640, 49]]` | **PASS** |
| `21b_krb_action` | strip:KERBEROS | strip:KERBEROS | `[[0.14, 0.0429, 0.215, 0.0571]]` | `[[549, 31, 640, 49]]` | **PASS** |
| `21c_krb_password` | strip:KERBEROS | strip:KERBEROS | `[[0.14, 0.0429, 0.215, 0.0571]]` | `[[549, 31, 640, 49]]` | **PASS** |
| `22_running_what` | strip:RUNNING | strip:RUNNING | `[[0.235, 0.0429, 0.3, 0.0571]]` | `[[657, 31, 736, 49]]` | **PASS** |
| `22b_running_learn` | strip:RUNNING | strip:RUNNING | `[[0.235, 0.0429, 0.3, 0.0571]]` | `[[657, 31, 736, 49]]` | **PASS** |
| `23_finished_what` | strip:FINISHED 7D | strip:FINISHED 7D | `[[0.32, 0.0429, 0.385, 0.0571]]` | `[[753, 31, 832, 49]]` | **PASS** |
| `23b_finished_learn` | strip:FINISHED 7D | strip:FINISHED 7D | `[[0.32, 0.0429, 0.385, 0.0571]]` | `[[753, 31, 832, 49]]` | **PASS** |
| `24_failed_what` | strip:FAILED 7D | strip:FAILED 7D | `[[0.405, 0.0429, 0.46, 0.0571]]` | `[[849, 31, 917, 49]]` | **PASS** |
| `24b_failed_action` | strip:FAILED 7D | strip:FAILED 7D | `[[0.405, 0.0429, 0.46, 0.0571]]` | `[[849, 31, 917, 49]]` | **PASS** |
| `30_title_what` | jobs-title | jobs-title | `[[0.135, 0.0714, 0.305, 0.0857]]` | `[[543, 54, 742, 72]]` | **PASS** |
| `30b_title_learn` | jobs-title | jobs-title | `[[0.135, 0.0714, 0.305, 0.0857]]` | `[[543, 54, 742, 72]]` | **PASS** |
| `31_empty_what` | jobs-empty | jobs-empty | `[[0.14, 0.0857, 0.99, 0.1286]]` | `[[547, 64, 1519, 109]]` | **PASS** |
| `31b_empty_action` | jobs-empty | jobs-empty | `[[0.14, 0.0857, 0.99, 0.1286]]` | `[[547, 64, 1519, 109]]` | **PASS** |
| `40_table_what` | jobs-table | jobs-table | `[[0.14, 0.0857, 0.555, 0.1714]]` | `[[547, 64, 1027, 143]]` | **PASS** |
| `40b_table_learn` | jobs-table | jobs-table | `[[0.14, 0.0857, 0.555, 0.1714]]` | `[[547, 64, 1027, 143]]` | **PASS** |
| `41_col_id` | column:ID | column:ID | `[[0.14, 0.0857, 0.22, 0.1714]]` | `[[548, 65, 647, 142]]` | **PASS** |
| `41b_col_id_use` | column:ID | column:ID | `[[0.14, 0.0857, 0.22, 0.1714]]` | `[[548, 65, 647, 142]]` | **PASS** |
| `42_col_src` | column:Source | column:Source | `[[0.22, 0.0857, 0.31, 0.1714]]` | `[[639, 65, 748, 142]]` | **PASS** |
| `42b_col_src_use` | column:Source | column:Source | `[[0.22, 0.0857, 0.31, 0.1714]]` | `[[639, 65, 748, 142]]` | **PASS** |
| `43_col_dst` | column:Destination | column:Destination | `[[0.31, 0.0857, 0.415, 0.1714]]` | `[[740, 65, 867, 142]]` | **PASS** |
| `43b_col_dst_use` | column:Destination | column:Destination | `[[0.31, 0.0857, 0.415, 0.1714]]` | `[[740, 65, 867, 142]]` | **PASS** |
| `44_col_state` | column:State | column:State | `[[0.415, 0.0857, 0.51, 0.1714]]` | `[[859, 65, 975, 142]]` | **PASS** |
| `44b_col_state_learn` | column:State | column:State | `[[0.415, 0.0857, 0.51, 0.1714]]` | `[[859, 65, 975, 142]]` | **PASS** |
| `50_st_pending` | cell:State:PENDING | cell:State:PENDING | `[[0.415, 0.1143, 0.51, 0.1286]]` | `[[860, 89, 974, 107]]` | **PASS** |
| `50b_st_pending_act` | cell:State:PENDING | cell:State:PENDING | `[[0.415, 0.1143, 0.51, 0.1286]]` | `[[860, 89, 974, 107]]` | **PASS** |
| `51_st_running` | cell:State:RUNNING | cell:State:RUNNING | `[[0.415, 0.1, 0.51, 0.1143]]` | `[[860, 78, 974, 95]]` | **PASS** |
| `51b_st_running_act` | cell:State:RUNNING | cell:State:RUNNING | `[[0.415, 0.1, 0.51, 0.1143]]` | `[[860, 78, 974, 95]]` | **PASS** |
| `52_st_ok` | cell:State:SUCCEEDED | cell:State:SUCCEEDED | `[[0.415, 0.1571, 0.51, 0.1714]]` | `[[860, 124, 974, 141]]` | **PASS** |
| `52b_st_ok_act` | cell:State:SUCCEEDED | cell:State:SUCCEEDED | `[[0.415, 0.1571, 0.51, 0.1714]]` | `[[860, 124, 974, 141]]` | **PASS** |
| `53_st_fail` | cell:State:FAILED | cell:State:FAILED | `[[0.415, 0.1429, 0.51, 0.1571]]` | `[[860, 112, 974, 130]]` | **PASS** |
| `53b_st_fail_act` | cell:State:FAILED | cell:State:FAILED | `[[0.415, 0.1429, 0.51, 0.1571]]` | `[[860, 112, 974, 130]]` | **PASS** |
| `54_st_cancel` | cell:State:CANCELLED | cell:State:CANCELLED | `[[0.415, 0.1286, 0.51, 0.1429]]` | `[[860, 101, 974, 118]]` | **PASS** |
| `54b_st_cancel_act` | cell:State:CANCELLED | cell:State:CANCELLED | `[[0.415, 0.1286, 0.51, 0.1429]]` | `[[860, 101, 974, 118]]` | **PASS** |
| `55_col_elapsed` | column:Elapsed | column:Elapsed | `[[0.51, 0.0857, 0.555, 0.1714]]` | `[[967, 65, 1026, 142]]` | **PASS** |
| `55b_col_elapsed_use` | column:Elapsed | column:Elapsed | `[[0.51, 0.0857, 0.555, 0.1714]]` | `[[967, 65, 1026, 142]]` | **PASS** |
| `60_filter_what` | jobs-filter | jobs-filter | `[[0.135, 0.0857, 0.995, 0.1286]]` | `[[542, 65, 1524, 108]]` | **PASS** |
| `60b_filter_when` | jobs-filter | jobs-filter | `[[0.135, 0.0857, 0.995, 0.1286]]` | `[[542, 65, 1524, 108]]` | **PASS** |
| `61_filter_ex` | jobs-filter+table | jobs-filter+table | `[[0.135, 0.0857, 0.995, 0.1286], [0.14, 0.1286, 0.555, 0.1571]]` | `[[541, 64, 1525, 109], [547, 99, 1027, 132]]` | **PASS** |
| `70_detail_what` | detail-pane | detail-pane | `[[0.135, 0.8143, 0.995, 0.9]]` | `[[541, 654, 1525, 734]]` | **PASS** |
| `70b_detail_learn` | detail-pane | detail-pane | `[[0.135, 0.8143, 0.995, 0.9]]` | `[[541, 654, 1525, 734]]` | **PASS** |
| `71_detail_title` | detail-title | detail-title | `[[0.145, 0.8286, 0.985, 0.8429]]` | `[[555, 668, 1512, 685]]` | **PASS** |
| `72_detail_log` | detail-log | detail-log | `[[0.145, 0.8429, 0.985, 0.8857]]` | `[[553, 677, 1514, 722]]` | **PASS** |
| `80_events` | event-trail | event-trail | `[[0.135, 0.9429, 0.795, 0.9857]]` | `[[542, 759, 1297, 802]]` | **PASS** |
| `81_newjob` | new-job | new-job | `[[0.8, 0.9429, 0.86, 0.9857]]` | `[[1295, 759, 1371, 802]]` | **PASS** |
| `82_viewlogs` | view-logs | view-logs | `[[0.865, 0.9429, 0.925, 0.9857]]` | `[[1369, 759, 1445, 802]]` | **PASS** |
| `82b_viewlogs_when` | view-logs | view-logs | `[[0.865, 0.9429, 0.925, 0.9857]]` | `[[1369, 759, 1445, 802]]` | **PASS** |
| `83_cancel` | cancel | cancel | `[[0.93, 0.9429, 0.99, 0.9857]]` | `[[1442, 759, 1518, 802]]` | **PASS** |
| `83b_cancel_note` | cancel | cancel | `[[0.93, 0.9429, 0.99, 0.9857]]` | `[[1442, 759, 1518, 802]]` | **PASS** |
| `90_close` | closing-card | closing-card | `[[0.12, 0.14, 0.88, 0.7]]` | `[[80, 100, 1840, 786]]` | **PASS** |

## Summary

1. Spotlight scenes reviewed: **53**
2. Spotlight scenes corrected: **53**
3. Geometry-driven spotlights: **53**
4. Spotlight validation failures before correction: **51**
5. Spotlight validation failures after correction: **0**

**Overall: PASS**
