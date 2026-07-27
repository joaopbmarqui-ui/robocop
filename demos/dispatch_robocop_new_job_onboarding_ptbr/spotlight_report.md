# Spotlight manual-review report

Resolution 1920×1080. Overlay alpha=170. Font=Carlito.

| Scene | Topic | Targets | Pre-margin boxes | Final boxes | Margin | Cutouts | Opacity | Review frame | Status | Reason |
|---|---|---|---|---|---|---|---|---|---|---|
| `01_open` | Dispatch (Robocop) | card | `[[0.12, 0.14, 0.88, 0.7]]` | `[[80, 100, 1840, 786]]` | [20] | 1 | 170 | 00:00:03,267 | **PASS** | card content spotlight |
| `02_purpose_a` | Para que serve New Job | radio-panel | `[[0.14, 0.1857, 0.99, 0.3143]]` | `[[532, 130, 1534, 274]]` | [20] | 1 | 170 | 00:00:11,333 | **PASS** |  |
| `02_purpose_b` | O que você decide aqui | source,destination | `[[0.15, 0.2286, 0.555, 0.3], [0.575, 0.2286, 0.98, 0.3]]` | `[[543, 165, 1042, 263], [1024, 165, 1523, 263]]` | [20, 20] | 2 | 170 | 00:00:19,600 | **PASS** |  |
| `03_matrix` | Source × Destination | matrix-collapsible | `[[0.135, 0.0571, 0.995, 0.1714]]` | `[[526, 26, 1540, 158]]` | [20] | 1 | 170 | 00:00:28,300 | **PASS** |  |
| `04_detected` | Detected source | info-detected | `[[0.135, 0.1714, 0.995, 0.1857]]` | `[[532, 130, 1534, 158]]` | [14] | 1 | 170 | 00:00:37,467 | **PASS** |  |
| `05_source_intro` | Source | source | `[[0.15, 0.1571, 0.555, 0.2286]]` | `[[543, 107, 1042, 205]]` | [20] | 1 | 170 | 00:00:45,533 | **PASS** |  |
| `06_source_sqlfile` | Source → SqlFile | src-sqlfile | `[[0.16, 0.1714, 0.545, 0.1857]]` | `[[559, 130, 1026, 158]]` | [16] | 1 | 170 | 00:00:53,733 | **PASS** |  |
| `06b_source_sqlfile_effect` | SqlFile — efeito | src-sqlfile | `[[0.16, 0.1714, 0.545, 0.1857]]` | `[[559, 130, 1026, 158]]` | [16] | 1 | 170 | 00:01:02,967 | **PASS** |  |
| `07_dest_intro` | Destination | destination | `[[0.575, 0.1571, 0.98, 0.2286]]` | `[[1024, 107, 1523, 205]]` | [20] | 1 | 170 | 00:01:11,433 | **PASS** |  |
| `08_dest_table` | Destination → Table | dst-table | `[[0.585, 0.1714, 0.97, 0.1857]]` | `[[1040, 130, 1508, 158]]` | [16] | 1 | 170 | 00:01:19,867 | **PASS** |  |
| `09_dest_csv` | Destination → Csv | dst-csv | `[[0.585, 0.1857, 0.97, 0.2]]` | `[[1040, 142, 1508, 170]]` | [16] | 1 | 170 | 00:01:28,800 | **PASS** |  |
| `09b_dest_csv_when` | Csv — quando usar | dst-csv | `[[0.585, 0.1857, 0.97, 0.2]]` | `[[1040, 142, 1508, 170]]` | [16] | 1 | 170 | 00:01:38,100 | **PASS** |  |
| `10_dest_tablecsv` | Destination → Table+Csv | dst-table-csv | `[[0.585, 0.2, 0.97, 0.2143]]` | `[[1040, 154, 1508, 181]]` | [16] | 1 | 170 | 00:01:46,700 | **PASS** |  |
| `11_queue_a` | Execution Queue | lbl-queue,queue | `[[0.15, 0.2714, 0.98, 0.3714]]` | `[[549, 205, 1517, 314]]` | [14, 20] | 1 | 170 | 00:01:55,767 | **PASS** |  |
| `12_queue_b` | Execution Queue — marcar | lbl-queue,queue | `[[0.15, 0.2714, 0.98, 0.3714]]` | `[[549, 205, 1517, 314]]` | [14, 20] | 1 | 170 | 00:02:03,900 | **PASS** |  |
| `12b_queue_order` | Várias filas | queue-panel | `[[0.14, 0.2571, 0.99, 0.4143]]` | `[[532, 188, 1534, 355]]` | [20] | 1 | 170 | 00:02:13,100 | **PASS** |  |
| `13_sql_intro` | SQL File | lbl-sql-file,sql-file | `[[0.14, 0.5, 0.99, 0.5429]]` | `[[538, 391, 1528, 453]]` | [14, 20] | 1 | 170 | 00:02:21,400 | **PASS** |  |
| `13b_sql_when` | SQL File — quando | lbl-sql-file,sql-file | `[[0.14, 0.5, 0.99, 0.5429]]` | `[[538, 391, 1528, 453]]` | [14, 20] | 1 | 170 | 00:02:29,700 | **PASS** |  |
| `14_sql_picker` | Lista de arquivos SQL | sql-file-picker | `[[0.14, 0.4429, 0.99, 0.4857]]` | `[[532, 343, 1534, 408]]` | [20] | 1 | 170 | 00:02:38,200 | **PASS** |  |
| `15_sql_verify` | O que conferir | sql-file-picker | `[[0.14, 0.4429, 0.99, 0.4857]]` | `[[532, 343, 1534, 408]]` | [20] | 1 | 170 | 00:02:47,233 | **PASS** |  |
| `15b_sql_path` | Caminho do SQL File | lbl-sql-file,sql-file | `[[0.14, 0.5, 0.99, 0.5429]]` | `[[538, 391, 1528, 453]]` | [14, 20] | 1 | 170 | 00:02:55,567 | **PASS** |  |
| `16_sql_role` | Papel do SQL File | lbl-sql-file,sql-file | `[[0.14, 0.5, 0.99, 0.5429]]` | `[[538, 391, 1528, 453]]` | [14, 20] | 1 | 170 | 00:03:03,833 | **PASS** |  |
| `16b_sql_role_dest` | SQL + destino | source,destination | `[[0.15, 0.1571, 0.555, 0.2286], [0.575, 0.1571, 0.98, 0.2286]]` | `[[543, 107, 1042, 205], [1024, 107, 1523, 205]]` | [20, 20] | 2 | 170 | 00:03:12,133 | **PASS** |  |
| `17_email` | Email (notifications) | lbl-email,email | `[[0.14, 0.5714, 0.99, 0.6143]]` | `[[538, 448, 1528, 511]]` | [14, 20] | 1 | 170 | 00:03:20,700 | **PASS** |  |
| `18_subject` | Subject (email) | lbl-subject,subject | `[[0.14, 0.6286, 0.99, 0.6714]]` | `[[538, 495, 1528, 557]]` | [14, 20] | 1 | 170 | 00:03:29,967 | **PASS** |  |
| `19_status_bar` | Status do formulário | validation-summary | `[[0.135, 0.9429, 0.85, 0.9857]]` | `[[526, 748, 1376, 806]]` | [20] | 1 | 170 | 00:03:38,900 | **PASS** |  |
| `19b_actions` | Preview SQL e Launch | preview,launch | `[[0.855, 0.9429, 0.925, 0.9857], [0.93, 0.9429, 0.99, 0.9857]]` | `[[1345, 748, 1457, 806], [1430, 748, 1530, 806]]` | [16, 16] | 2 | 170 | 00:03:47,200 | **PASS** |  |
| `20_mj_intro` | MonthlyJob | src-sqltemplate | `[[0.16, 0.1857, 0.54, 0.2]]` | `[[559, 142, 1021, 170]]` | [16] | 1 | 170 | 00:03:55,667 | **PASS** |  |
| `21_mj_dest` | MonthlyJob → Destination | src-sqltemplate,dst-table | `[[0.16, 0.1857, 0.54, 0.2], [0.58, 0.1714, 0.96, 0.1857]]` | `[[559, 142, 1021, 170], [1034, 130, 1496, 158]]` | [16, 16] | 2 | 170 | 00:04:04,767 | **PASS** |  |
| `21b_mj_dest_blocked` | Csv e Table+Csv | dst-csv,dst-table-csv | `[[0.58, 0.1857, 0.96, 0.2], [0.58, 0.2, 0.96, 0.2143]]` | `[[1034, 142, 1496, 170], [1034, 154, 1496, 181]]` | [16, 16] | 2 | 170 | 00:04:13,033 | **PASS** |  |
| `22_mj_sql_rule_a` | SQL no MonthlyJob — regra | card | `[[0.12, 0.14, 0.88, 0.7]]` | `[[80, 100, 1840, 786]]` | [20] | 1 | 170 | 00:04:21,367 | **PASS** | card content spotlight |
| `23_mj_sql_rule_b` | Como conferir no arquivo | card | `[[0.12, 0.14, 0.88, 0.7]]` | `[[80, 100, 1840, 786]]` | [20] | 1 | 170 | 00:04:29,233 | **PASS** | card content spotlight |
| `23b_mj_sql_missing` | Se faltar um marcador | card | `[[0.12, 0.14, 0.88, 0.7]]` | `[[80, 100, 1840, 786]]` | [20] | 1 | 170 | 00:04:37,033 | **PASS** | card content spotlight |
| `24_mj_sql_rule_c` | O que os marcadores fazem | card | `[[0.12, 0.14, 0.88, 0.7]]` | `[[80, 100, 1840, 786]]` | [20] | 1 | 170 | 00:04:45,033 | **PASS** | card content spotlight |
| `24b_mj_sql_fill` | Preenchimento das datas | card | `[[0.12, 0.14, 0.88, 0.7]]` | `[[80, 100, 1840, 786]]` | [20] | 1 | 170 | 00:04:53,100 | **PASS** | card content spotlight |
| `25_mj_picker` | SQL do MonthlyJob | sql-file-picker | `[[0.14, 0.4571, 0.98, 0.5]]` | `[[532, 355, 1523, 420]]` | [20] | 1 | 170 | 00:05:01,333 | **PASS** |  |
| `25b_mj_picker_confirm` | Detected = MonthlyJob | sql-file-picker | `[[0.14, 0.4571, 0.98, 0.5]]` | `[[532, 355, 1523, 420]]` | [20] | 1 | 170 | 00:05:10,600 | **PASS** |  |
| `26_mj_schema` | Schema (MonthlyJob) | lbl-schema,schema | `[[0.14, 0.5857, 0.98, 0.6286]]` | `[[538, 460, 1517, 523]]` | [14, 20] | 1 | 170 | 00:05:19,167 | **PASS** |  |
| `27_mj_table` | Table Name (MonthlyJob) | lbl-table-name,table-name-prefix,table-name-suffix | `[[0.14, 0.6429, 0.98, 0.6857]]` | `[[538, 506, 1517, 569]]` | [14, 20, 20] | 1 | 170 | 00:05:27,167 | **PASS** |  |
| `27b_mj_table_suffix` | Sufixo da tabela | table-name-prefix,table-name-suffix | `[[0.25, 0.6429, 0.98, 0.6857]]` | `[[657, 505, 1523, 570]]` | [20, 20] | 1 | 170 | 00:05:35,467 | **PASS** |  |
| `28_mj_start` | Start Date | lbl-start-date,start-date | `[[0.14, 0.7, 0.98, 0.7429]]` | `[[538, 553, 1517, 615]]` | [14, 20] | 1 | 170 | 00:05:43,800 | **PASS** |  |
| `29_mj_end` | End Date | lbl-end-date,end-date | `[[0.14, 0.7571, 0.98, 0.8]]` | `[[538, 599, 1517, 662]]` | [14, 20] | 1 | 170 | 00:05:52,133 | **PASS** |  |
| `30_et_intro` | ExistingTable | src-existingtable | `[[0.16, 0.2, 0.545, 0.2143]]` | `[[559, 154, 1026, 181]]` | [16] | 1 | 170 | 00:06:00,667 | **PASS** |  |
| `31_et_dest` | ExistingTable → Destination | src-existingtable,dst-csv | `[[0.16, 0.2, 0.545, 0.2143], [0.585, 0.1857, 0.97, 0.2]]` | `[[559, 154, 1026, 181], [1040, 142, 1508, 170]]` | [16, 16] | 2 | 170 | 00:06:09,633 | **PASS** |  |
| `31b_et_dest_blocked` | Table e Table+Csv | dst-table,dst-table-csv | `[[0.585, 0.1714, 0.97, 0.1857], [0.585, 0.2, 0.97, 0.2143]]` | `[[1040, 130, 1508, 158], [1040, 154, 1508, 181]]` | [16, 16] | 2 | 170 | 00:06:17,900 | **PASS** |  |
| `32_et_no_sql` | Sem SQL File | src-existingtable,dest-hint | `[[0.16, 0.2, 0.545, 0.2143], [0.14, 0.2429, 0.99, 0.2571]]` | `[[559, 154, 1026, 181], [538, 188, 1528, 216]]` | [16, 14] | 2 | 170 | 00:06:26,400 | **PASS** |  |
| `33_et_schema_coe` | Schema → coe_enc | esc-coe-enc | `[[0.26, 0.4714, 0.97, 0.4857]]` | `[[672, 373, 1508, 401]]` | [16] | 1 | 170 | 00:06:34,500 | **PASS** |  |
| `34_et_schema_aa` | Schema → aa_enc | esc-aa-enc | `[[0.26, 0.4857, 0.97, 0.5]]` | `[[672, 385, 1508, 413]]` | [16] | 1 | 170 | 00:06:43,767 | **PASS** |  |
| `35_et_schema_other` | Schema → other | esc-other | `[[0.26, 0.5, 0.97, 0.5143]]` | `[[672, 397, 1508, 424]]` | [16] | 1 | 170 | 00:06:52,967 | **PASS** |  |
| `35b_et_other_field` | other → Custom Schema | lbl-existing-schema-custom,existing-schema-custom | `[[0.14, 0.5143, 0.99, 0.5571]]` | `[[538, 402, 1528, 465]]` | [14, 20] | 1 | 170 | 00:07:02,200 | **PASS** |  |
| `36_et_custom` | Custom Schema | lbl-existing-schema-custom,existing-schema-custom | `[[0.14, 0.5143, 0.99, 0.5571]]` | `[[538, 402, 1528, 465]]` | [14, 20] | 1 | 170 | 00:07:10,700 | **PASS** |  |
| `37_et_table` | Existing Table | lbl-existing-table,existing-table | `[[0.14, 0.5143, 0.99, 0.5571]]` | `[[538, 402, 1528, 465]]` | [14, 20] | 1 | 170 | 00:07:18,800 | **PASS** |  |
| `37b_et_full` | Origem completa | lbl-existing-schema,existing-schema,lbl-existing-table,existing-table | `[[0.14, 0.4571, 0.99, 0.5], [0.14, 0.5143, 0.99, 0.5571]]` | `[[538, 356, 1528, 419], [532, 401, 1534, 466]]` | [14, 20, 14, 20] | 2 | 170 | 00:07:28,033 | **PASS** |  |
| `38_rel_standard` | Combinação comum | src-sqlfile,dst-csv | `[[0.16, 0.1714, 0.545, 0.1857], [0.585, 0.1857, 0.97, 0.2]]` | `[[559, 130, 1026, 158], [1040, 142, 1508, 170]]` | [16, 16] | 2 | 170 | 00:07:36,333 | **PASS** |  |
| `38b_rel_standard_use` | Fluxo típico | src-sqlfile,dst-csv | `[[0.16, 0.1714, 0.545, 0.1857], [0.585, 0.1857, 0.97, 0.2]]` | `[[559, 130, 1026, 158], [1040, 142, 1508, 170]]` | [16, 16] | 2 | 170 | 00:07:45,567 | **PASS** |  |
| `39_rel_monthly` | Combinação MonthlyJob | src-sqltemplate,dst-table | `[[0.16, 0.1857, 0.54, 0.2], [0.58, 0.1714, 0.96, 0.1857]]` | `[[559, 142, 1021, 170], [1034, 130, 1496, 158]]` | [16, 16] | 2 | 170 | 00:07:54,000 | **PASS** |  |
| `39b_rel_monthly_fields` | Campos do MonthlyJob | lbl-schema,schema,lbl-table-name,table-name-prefix,table-name-suffix | `[[0.14, 0.5857, 0.98, 0.6286], [0.14, 0.6429, 0.98, 0.6857]]` | `[[538, 460, 1517, 523], [532, 505, 1523, 570]]` | [14, 20, 14, 20, 20] | 2 | 170 | 00:08:02,167 | **PASS** |  |
| `39c_rel_monthly_dates` | Datas do MonthlyJob | lbl-start-date,start-date,lbl-end-date,end-date | `[[0.14, 0.7, 0.98, 0.7429], [0.14, 0.7571, 0.98, 0.8]]` | `[[538, 553, 1517, 615], [532, 598, 1523, 663]]` | [14, 20, 14, 20] | 2 | 170 | 00:08:10,500 | **PASS** |  |
| `40_rel_existing` | Combinação ExistingTable | src-existingtable,dst-csv | `[[0.16, 0.2, 0.545, 0.2143], [0.585, 0.1857, 0.97, 0.2]]` | `[[559, 154, 1026, 181], [1040, 142, 1508, 170]]` | [16, 16] | 2 | 170 | 00:08:18,767 | **PASS** |  |
| `40b_rel_existing_no_sql` | Sem SQL neste modo | src-existingtable | `[[0.16, 0.2, 0.545, 0.2143]]` | `[[559, 154, 1026, 181]]` | [16] | 1 | 170 | 00:08:27,067 | **PASS** |  |
| `41_rel_incompat` | Combinações indisponíveis | matrix-table | `[[0.155, 0.1, 0.995, 0.1571]]` | `[[549, 61, 1540, 147]]` | [20] | 1 | 170 | 00:08:35,367 | **PASS** |  |
| `41b_rel_incompat_et` | ExistingTable — limite | matrix-table | `[[0.155, 0.1, 0.995, 0.1571]]` | `[[549, 61, 1540, 147]]` | [20] | 1 | 170 | 00:08:43,667 | **PASS** |  |
| `42_val_bad` | E-mail inválido | lbl-email,email,validation-summary | `[[0.14, 0.5714, 0.99, 0.6143], [0.135, 0.9429, 0.85, 0.9857]]` | `[[538, 448, 1528, 511], [526, 748, 1376, 806]]` | [14, 20, 20] | 2 | 170 | 00:08:52,000 | **PASS** |  |
| `43_val_ok` | Formulário pronto | validation-summary | `[[0.135, 0.9429, 0.85, 0.9857]]` | `[[526, 748, 1376, 806]]` | [20] | 1 | 170 | 00:09:00,267 | **PASS** |  |
| `43b_val_review` | Revise antes de enviar | source,destination | `[[0.15, 0.1571, 0.555, 0.2286], [0.575, 0.1571, 0.98, 0.2286]]` | `[[543, 107, 1042, 205], [1024, 107, 1523, 205]]` | [20, 20] | 2 | 170 | 00:09:08,567 | **PASS** |  |
| `44_preview` | Preview SQL | preview | `[[0.855, 0.9429, 0.925, 0.9857]]` | `[[1345, 748, 1457, 806]]` | [16] | 1 | 170 | 00:09:16,867 | **PASS** |  |
| `44b_preview_check` | O que conferir no Preview | preview-header,preview-body | `[[0.13, 0.0571, 1.0, 0.1], [0.14, 0.1143, 0.99, 0.5143]]` | `[[521, 31, 1546, 96], [532, 72, 1534, 436]]` | [20, 20] | 2 | 170 | 00:09:26,133 | **PASS** |  |
| `45_checklist` | Antes de iniciar, confirme | card | `[[0.12, 0.14, 0.88, 0.7]]` | `[[80, 100, 1840, 786]]` | [20] | 1 | 170 | 00:09:34,267 | **PASS** | card content spotlight |
| `45b_checklist_b` | Também confira | card | `[[0.12, 0.14, 0.88, 0.7]]` | `[[80, 100, 1840, 786]]` | [20] | 1 | 170 | 00:09:42,100 | **PASS** | card content spotlight |
| `46_confirm` | Launch Job | confirm-dialog | `[[0.34, 0.3571, 0.66, 0.6714]]` | `[[758, 269, 1161, 563]]` | [20] | 1 | 170 | 00:09:50,400 | **PASS** |  |
| `46b_confirm_read` | Confirme só se estiver corre | confirm-dialog | `[[0.34, 0.3571, 0.66, 0.6714]]` | `[[758, 269, 1161, 563]]` | [20] | 1 | 170 | 00:09:59,667 | **PASS** |  |
| `47_launched` | Job enviado | warning-text | `[[0.135, 0.7714, 0.995, 0.7857]]` | `[[526, 616, 1540, 644]]` | [20] | 1 | 170 | 00:10:08,067 | **PASS** |  |
| `48_overview` | Overview | sidebar-nav | `[[0.0, 0.0571, 0.125, 0.3]]` | `[[374, 26, 555, 263]]` | [20] | 1 | 170 | 00:10:16,233 | **PASS** |  |
| `49_close` | Resumo | card | `[[0.12, 0.14, 0.88, 0.7]]` | `[[80, 100, 1840, 786]]` | [20] | 1 | 170 | 00:10:25,167 | **PASS** | card content spotlight |
| `49b_close_b` | Depois do envio | card | `[[0.12, 0.14, 0.88, 0.7]]` | `[[80, 100, 1840, 786]]` | [20] | 1 | 170 | 00:10:33,433 | **PASS** | card content spotlight |

Scenes with >1 cutout: 18
Total scenes reviewed: 75

**Overall: PASS**