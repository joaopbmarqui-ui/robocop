# Spotlight manual-review report

Resolution 1920×1080. Overlay alpha=170. Font=Carlito.

| Scene | Topic | Targets | Pre-margin boxes | Final boxes | Margin | Cutouts | Opacity | Review frame | Status | Reason |
|---|---|---|---|---|---|---|---|---|---|---|
| `01_open` | Dispatch (Robocop) | card | `[[0.12, 0.14, 0.88, 0.7]]` | `[[80, 100, 1840, 786]]` | [20] | 1 | 170 | 00:00:03,267 | **PASS** | card content spotlight |
| `02_purpose` | O que é New Job | radio-panel | `[[0.14, 0.1857, 0.99, 0.3143]]` | `[[532, 130, 1534, 274]]` | [20] | 1 | 170 | 00:00:09,667 | **PASS** |  |
| `10_source_what` | O que é | source | `[[0.15, 0.1571, 0.555, 0.2286]]` | `[[543, 107, 1042, 205]]` | [20] | 1 | 170 | 00:00:15,967 | **PASS** |  |
| `10b_source_decide` | O que você decide aqui | source | `[[0.15, 0.1571, 0.555, 0.2286]]` | `[[543, 107, 1042, 205]]` | [20] | 1 | 170 | 00:00:21,967 | **PASS** |  |
| `11_source_sqlfile` | SqlFile | src-sqlfile | `[[0.16, 0.1714, 0.545, 0.1857]]` | `[[559, 130, 1026, 158]]` | [16] | 1 | 170 | 00:00:28,267 | **PASS** |  |
| `11b_source_sqlfile_effect` | Efeito | src-sqlfile | `[[0.16, 0.1714, 0.545, 0.1857]]` | `[[559, 130, 1026, 158]]` | [16] | 1 | 170 | 00:00:35,200 | **PASS** |  |
| `20_dest_what` | O que é | destination | `[[0.575, 0.1571, 0.98, 0.2286]]` | `[[1024, 107, 1523, 205]]` | [20] | 1 | 170 | 00:00:41,500 | **PASS** |  |
| `20b_dest_decide` | O que você decide aqui | destination | `[[0.575, 0.1571, 0.98, 0.2286]]` | `[[1024, 107, 1523, 205]]` | [20] | 1 | 170 | 00:00:47,600 | **PASS** |  |
| `21_dest_csv` | Csv | dst-csv | `[[0.585, 0.1857, 0.97, 0.2]]` | `[[1040, 142, 1508, 170]]` | [16] | 1 | 170 | 00:00:53,900 | **PASS** |  |
| `21b_dest_csv_effect` | Efeito | dst-csv | `[[0.585, 0.1857, 0.97, 0.2]]` | `[[1040, 142, 1508, 170]]` | [16] | 1 | 170 | 00:01:00,833 | **PASS** |  |
| `35_detected` | Detected source | info-detected | `[[0.135, 0.1714, 0.995, 0.1857]]` | `[[532, 130, 1534, 158]]` | [14] | 1 | 170 | 00:01:07,267 | **PASS** |  |
| `36_matrix` | Source × Destination | matrix-collapsible | `[[0.135, 0.0571, 0.995, 0.1714]]` | `[[526, 26, 1540, 158]]` | [20] | 1 | 170 | 00:01:13,833 | **PASS** |  |
| `40_queue_what` | O que é | lbl-queue,queue | `[[0.15, 0.2714, 0.98, 0.3714]]` | `[[549, 205, 1517, 314]]` | [14, 20] | 1 | 170 | 00:01:21,067 | **PASS** |  |
| `40b_queue_none` | Sem marcação | queue-panel | `[[0.15, 0.2714, 0.98, 0.3714]]` | `[[549, 205, 1517, 314]]` | [14, 20] | 1 | 170 | 00:01:27,267 | **PASS** |  |
| `40c_queue_decide` | O que você decide aqui | queue-panel | `[[0.15, 0.2714, 0.98, 0.3714]]` | `[[549, 205, 1517, 314]]` | [14, 20] | 1 | 170 | 00:01:33,667 | **PASS** |  |
| `41_queue_example` | Exemplo de escolha | queue | `[[0.15, 0.3, 0.98, 0.3714]]` | `[[543, 223, 1523, 320]]` | [20] | 1 | 170 | 00:01:40,000 | **PASS** |  |
| `30_sql_what` | O que é | lbl-sql-file,sql-file | `[[0.14, 0.5, 0.99, 0.5429]]` | `[[538, 391, 1528, 453]]` | [14, 20] | 1 | 170 | 00:01:47,233 | **PASS** |  |
| `30b_sql_decide` | O que você decide aqui | lbl-sql-file,sql-file | `[[0.14, 0.5, 0.99, 0.5429]]` | `[[538, 391, 1528, 453]]` | [14, 20] | 1 | 170 | 00:01:53,533 | **PASS** |  |
| `31_sql_picker` | Lista de arquivos SQL | sql-file-picker | `[[0.14, 0.4429, 0.99, 0.4857]]` | `[[532, 343, 1534, 408]]` | [20] | 1 | 170 | 00:01:59,967 | **PASS** |  |
| `31b_sql_path` | Efeito | lbl-sql-file,sql-file | `[[0.14, 0.4429, 0.99, 0.4857]]` | `[[532, 343, 1534, 408]]` | [20] | 1 | 170 | 00:02:06,900 | **PASS** |  |
| `32_sql_dest` | SQL File e Destination | sql-file,destination | `[[0.25, 0.5, 0.99, 0.5429], [0.575, 0.1571, 0.98, 0.2286]]` | `[[657, 390, 1534, 454], [1024, 107, 1523, 205]]` | [20, 20] | 2 | 170 | 00:02:13,333 | **PASS** |  |
| `50_email` | Email (notifications) | lbl-email,email | `[[0.14, 0.5714, 0.99, 0.6143]]` | `[[538, 448, 1528, 511]]` | [14, 20] | 1 | 170 | 00:02:19,900 | **PASS** |  |
| `51_subject` | Subject (email) | lbl-subject,subject | `[[0.14, 0.6286, 0.99, 0.6714]]` | `[[538, 495, 1528, 557]]` | [14, 20] | 1 | 170 | 00:02:27,233 | **PASS** |  |
| `60_mj_what` | O que é | src-sqltemplate | `[[0.16, 0.1857, 0.54, 0.2]]` | `[[559, 142, 1021, 170]]` | [16] | 1 | 170 | 00:02:34,600 | **PASS** |  |
| `60b_mj_decide` | O que você decide aqui | src-sqltemplate | `[[0.16, 0.1857, 0.54, 0.2]]` | `[[559, 142, 1021, 170]]` | [16] | 1 | 170 | 00:02:41,767 | **PASS** |  |
| `61_mj_dest` | Destination = Table | dst-table | `[[0.58, 0.1714, 0.96, 0.1857]]` | `[[1034, 130, 1496, 158]]` | [16] | 1 | 170 | 00:02:48,167 | **PASS** |  |
| `62_mj_sql_a` | Regra do arquivo SQL | card | `[[0.12, 0.14, 0.88, 0.7]]` | `[[80, 100, 1840, 786]]` | [20] | 1 | 170 | 00:02:54,167 | **PASS** | card content spotlight |
| `62b_mj_sql_b` | Marcadores obrigatórios | card | `[[0.12, 0.14, 0.88, 0.7]]` | `[[80, 100, 1840, 786]]` | [20] | 1 | 170 | 00:03:00,167 | **PASS** | card content spotlight |
| `62c_mj_sql_c` | Como conferir | card | `[[0.12, 0.14, 0.88, 0.7]]` | `[[80, 100, 1840, 786]]` | [20] | 1 | 170 | 00:03:06,167 | **PASS** | card content spotlight |
| `63_mj_picker` | SQL do MonthlyJob | sql-file-picker | `[[0.14, 0.4571, 0.98, 0.5]]` | `[[532, 355, 1523, 420]]` | [20] | 1 | 170 | 00:03:12,467 | **PASS** |  |
| `64_mj_schema` | Schema | lbl-schema,schema | `[[0.14, 0.5857, 0.98, 0.6286]]` | `[[538, 460, 1517, 523]]` | [14, 20] | 1 | 170 | 00:03:19,700 | **PASS** |  |
| `65_mj_table` | Table Name | lbl-table-name,table-name-prefix,table-name-suffix | `[[0.14, 0.6429, 0.98, 0.6857]]` | `[[538, 506, 1517, 569]]` | [14, 20, 20] | 1 | 170 | 00:03:26,033 | **PASS** |  |
| `66_mj_start` | Start Date | lbl-start-date,start-date | `[[0.14, 0.7, 0.98, 0.7429]]` | `[[538, 553, 1517, 615]]` | [14, 20] | 1 | 170 | 00:03:32,467 | **PASS** |  |
| `66b_mj_start_ex` | Exemplo | lbl-start-date,start-date | `[[0.14, 0.7, 0.98, 0.7429]]` | `[[538, 553, 1517, 615]]` | [14, 20] | 1 | 170 | 00:03:38,467 | **PASS** |  |
| `67_mj_end` | End Date | lbl-end-date,end-date | `[[0.14, 0.7571, 0.98, 0.8]]` | `[[538, 599, 1517, 662]]` | [14, 20] | 1 | 170 | 00:03:44,800 | **PASS** |  |
| `67b_mj_end_ex` | Exemplo | lbl-end-date,end-date | `[[0.14, 0.7571, 0.98, 0.8]]` | `[[538, 599, 1517, 662]]` | [14, 20] | 1 | 170 | 00:03:50,800 | **PASS** |  |
| `68_mj_dates_rel` | Start Date e End Date | lbl-start-date,start-date,lbl-end-date,end-date | `[[0.14, 0.7, 0.98, 0.7429], [0.14, 0.7571, 0.98, 0.8]]` | `[[538, 553, 1517, 615], [532, 598, 1523, 663]]` | [14, 20, 14, 20] | 2 | 170 | 00:03:57,133 | **PASS** |  |
| `70_et_what` | O que é | src-existingtable | `[[0.16, 0.2, 0.545, 0.2143]]` | `[[559, 154, 1026, 181]]` | [16] | 1 | 170 | 00:04:03,467 | **PASS** |  |
| `70b_et_decide` | O que você decide aqui | src-existingtable | `[[0.16, 0.2, 0.545, 0.2143]]` | `[[559, 154, 1026, 181]]` | [16] | 1 | 170 | 00:04:10,600 | **PASS** |  |
| `71_et_dest` | Destination = Csv | dst-csv | `[[0.585, 0.1857, 0.97, 0.2]]` | `[[1040, 142, 1508, 170]]` | [16] | 1 | 170 | 00:04:17,067 | **PASS** |  |
| `72_et_schema` | Schema | lbl-existing-schema,existing-schema | `[[0.14, 0.4571, 0.99, 0.5]]` | `[[538, 356, 1528, 419]]` | [14, 20] | 1 | 170 | 00:04:23,367 | **PASS** |  |
| `72b_et_other` | Custom Schema | lbl-existing-schema-custom,existing-schema-custom | `[[0.14, 0.5143, 0.99, 0.5571]]` | `[[538, 402, 1528, 465]]` | [14, 20] | 1 | 170 | 00:04:30,800 | **PASS** |  |
| `73_et_table` | Existing Table | lbl-existing-table,existing-table | `[[0.14, 0.5143, 0.99, 0.5571]]` | `[[538, 402, 1528, 465]]` | [14, 20] | 1 | 170 | 00:04:37,100 | **PASS** |  |
| `73b_et_effect` | Efeito | lbl-existing-table,existing-table | `[[0.14, 0.5143, 0.99, 0.5571]]` | `[[538, 402, 1528, 465]]` | [14, 20] | 1 | 170 | 00:04:44,033 | **PASS** |  |
| `80_status` | Status do formulário | validation-summary | `[[0.135, 0.9429, 0.555, 0.9857]]` | `[[526, 748, 1042, 806]]` | [20] | 1 | 170 | 00:04:50,433 | **PASS** |  |
| `81_val_bad` | Validação | validation-summary | `[[0.135, 0.9429, 0.555, 0.9857]]` | `[[526, 748, 1042, 806]]` | [20] | 1 | 170 | 00:04:56,733 | **PASS** |  |
| `82_val_ok` | Formulário pronto | validation-summary | `[[0.135, 0.9429, 0.555, 0.9857]]` | `[[526, 748, 1042, 806]]` | [20] | 1 | 170 | 00:05:03,033 | **PASS** |  |
| `83_preview` | Preview SQL | preview | `[[0.855, 0.9429, 0.925, 0.9857]]` | `[[1345, 748, 1457, 806]]` | [16] | 1 | 170 | 00:05:09,333 | **PASS** |  |
| `83b_preview_check` | O que conferir | preview-header,preview-body | `[[0.13, 0.0571, 1.0, 0.1], [0.14, 0.1143, 0.99, 0.5143]]` | `[[521, 31, 1546, 96], [532, 72, 1534, 436]]` | [20, 20] | 2 | 170 | 00:05:16,567 | **PASS** |  |
| `84_check_a` | Antes de iniciar, confirme | card | `[[0.12, 0.14, 0.88, 0.7]]` | `[[80, 100, 1840, 786]]` | [20] | 1 | 170 | 00:05:22,667 | **PASS** | card content spotlight |
| `84b_check_b` | Também confira | card | `[[0.12, 0.14, 0.88, 0.7]]` | `[[80, 100, 1840, 786]]` | [20] | 1 | 170 | 00:05:28,667 | **PASS** | card content spotlight |
| `85_launch` | Launch | launch | `[[0.93, 0.9429, 0.99, 0.9857]]` | `[[1430, 748, 1530, 806]]` | [16] | 1 | 170 | 00:05:34,967 | **PASS** |  |
| `86_confirm` | Confirmação | confirm-dialog | `[[0.34, 0.3571, 0.66, 0.6714]]` | `[[758, 269, 1161, 563]]` | [20] | 1 | 170 | 00:05:41,267 | **PASS** |  |
| `87_launched` | Job enviado | warning-text | `[[0.135, 0.7714, 0.995, 0.7857]]` | `[[526, 616, 1540, 644]]` | [20] | 1 | 170 | 00:05:48,567 | **PASS** |  |
| `88_overview` | Overview | sidebar-nav | `[[0.0, 0.0571, 0.125, 0.3]]` | `[[374, 26, 555, 263]]` | [20] | 1 | 170 | 00:05:54,867 | **PASS** |  |
| `89_close` | Resumo | card | `[[0.12, 0.14, 0.88, 0.7]]` | `[[80, 100, 1840, 786]]` | [20] | 1 | 170 | 00:06:01,800 | **PASS** | card content spotlight |
| `89b_close_b` | Depois do envio | card | `[[0.12, 0.14, 0.88, 0.7]]` | `[[80, 100, 1840, 786]]` | [20] | 1 | 170 | 00:06:07,800 | **PASS** | card content spotlight |

Scenes with >1 cutout: 3
Total scenes reviewed: 57

**Overall: PASS**