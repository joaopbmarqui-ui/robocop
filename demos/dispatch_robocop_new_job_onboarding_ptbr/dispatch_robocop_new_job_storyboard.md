# Storyboard — New Job (8.0s, Carlito, 1920×1080, element spotlights)

Font: Carlito (Carlito-Regular.ttf). Body 38px / title 42px.
Calibri is not installed in this Linux environment. Using Carlito (fonts-crosextra-carlito), the OFL metric-compatible substitute.

## 01_open — Abertura

- **Elemento:** Dispatch (Robocop)
- **Targets:** (card)
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.12, 0.14, 0.88, 0.7]]
- **Final px boxes:** [[80, 100, 1840, 786]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Dispatch (Robocop) — Como utilizar a aba New Job. / Configure e inicie um job passo a passo.
- **Typing:** 00:00:00,000 → 00:00:01,267 (1.27s)
- **Seta:** 00:00:01,267
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** opening card

## 02_purpose_a — Propósito

- **Elemento:** Para que serve New Job
- **Targets:** radio-panel
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.1857, 0.99, 0.3143]]
- **Final px boxes:** [[532, 130, 1534, 274]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Para que serve New Job — Configure e inicie uma nova execução no Dispatch.
- **Typing:** 00:00:08,300 → 00:00:09,333 (1.03s)
- **Seta:** 00:00:09,333
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** NewJobScreen

## 02_purpose_b — Propósito

- **Elemento:** O que você decide aqui
- **Targets:** source, destination
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.15, 0.2286, 0.555, 0.3], [0.575, 0.2286, 0.98, 0.3]]
- **Final px boxes:** [[543, 165, 1042, 263], [1024, 165, 1523, 263]]
- **Cutouts:** 2
- **Overlay opacity:** 170/255
- **Diálogo:** O que você decide aqui — Origem, destino, consulta e opções do job.
- **Typing:** 00:00:16,600 → 00:00:17,600 (1.00s)
- **Seta:** 00:00:17,600
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** NewJobScreen form

## 03_matrix — Matriz

- **Elemento:** Source × Destination
- **Targets:** matrix-collapsible
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.135, 0.0571, 0.995, 0.1714]]
- **Final px boxes:** [[526, 26, 1540, 158]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Source × Destination — Mostra as combinações permitidas. / Consulte antes de escolher origem e destino.
- **Typing:** 00:00:24,900 → 00:00:26,300 (1.40s)
- **Seta:** 00:00:26,300
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** matrix-collapsible + LEGAL_CELLS

## 04_detected — Detecção

- **Elemento:** Detected source
- **Targets:** info-detected
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.135, 0.1714, 0.995, 0.1857]]
- **Final px boxes:** [[532, 130, 1534, 158]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Detected source — Tipo identificado no arquivo SQL. / Confirme se é o job que você quer executar.
- **Typing:** 00:00:34,133 → 00:00:35,467 (1.33s)
- **Seta:** 00:00:35,467
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** info-detected

## 05_source_intro — Source

- **Elemento:** Source
- **Targets:** source
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.15, 0.1571, 0.555, 0.2286]]
- **Final px boxes:** [[543, 107, 1042, 205]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Source — Define de onde vêm os dados do job. / É a primeira decisão do formulário.
- **Typing:** 00:00:42,433 → 00:00:43,533 (1.10s)
- **Seta:** 00:00:43,533
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** RadioSet #source

## 06_source_sqlfile — Source

- **Elemento:** Source → SqlFile
- **Targets:** src-sqlfile
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.16, 0.1714, 0.545, 0.1857]]
- **Final px boxes:** [[559, 130, 1026, 158]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Source → SqlFile — Use quando a consulta está em um .sql simples.
- **Typing:** 00:00:50,733 → 00:00:51,733 (1.00s)
- **Seta:** 00:00:51,733
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** src-sqlfile

## 06b_source_sqlfile_effect — Source

- **Elemento:** SqlFile — efeito
- **Targets:** src-sqlfile
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.16, 0.1714, 0.545, 0.1857]]
- **Final px boxes:** [[559, 130, 1026, 158]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** SqlFile — efeito — O Dispatch executa esse arquivo conforme o destino.
- **Typing:** 00:00:59,967 → 00:01:00,967 (1.00s)
- **Seta:** 00:01:00,967
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** LEGAL SqlFile

## 07_dest_intro — Destination

- **Elemento:** Destination
- **Targets:** destination
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.575, 0.1571, 0.98, 0.2286]]
- **Final px boxes:** [[1024, 107, 1523, 205]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Destination — Define onde o resultado será armazenado. / Depende da origem escolhida.
- **Typing:** 00:01:08,267 → 00:01:09,433 (1.17s)
- **Seta:** 00:01:09,433
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** #destination

## 08_dest_table — Destination

- **Elemento:** Destination → Table
- **Targets:** dst-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.585, 0.1714, 0.97, 0.1857]]
- **Final px boxes:** [[1040, 130, 1508, 158]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Destination → Table — Salva o resultado em uma tabela. / Use para consultar depois no ambiente.
- **Typing:** 00:01:16,567 → 00:01:17,867 (1.30s)
- **Seta:** 00:01:17,867
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** dst-table

## 09_dest_csv — Destination

- **Elemento:** Destination → Csv
- **Targets:** dst-csv
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.585, 0.1857, 0.97, 0.2]]
- **Final px boxes:** [[1040, 142, 1508, 170]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Destination → Csv — Gera um CSV na pasta em que você abriu o Dispatch.
- **Typing:** 00:01:25,800 → 00:01:26,800 (1.00s)
- **Seta:** 00:01:26,800
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** dst-csv

## 09b_dest_csv_when — Destination

- **Elemento:** Csv — quando usar
- **Targets:** dst-csv
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.585, 0.1857, 0.97, 0.2]]
- **Final px boxes:** [[1040, 142, 1508, 170]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Csv — quando usar — Use para baixar ou compartilhar o resultado como arquivo.
- **Typing:** 00:01:35,033 → 00:01:36,100 (1.07s)
- **Seta:** 00:01:36,100
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** ADR-0003

## 10_dest_tablecsv — Destination

- **Elemento:** Destination → Table+Csv
- **Targets:** dst-table-csv
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.585, 0.2, 0.97, 0.2143]]
- **Final px boxes:** [[1040, 154, 1508, 181]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Destination → Table+Csv — Cria a tabela e também gera o CSV. / Use quando precisa dos dois formatos.
- **Typing:** 00:01:43,333 → 00:01:44,700 (1.37s)
- **Seta:** 00:01:44,700
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** dst-table-csv

## 11_queue_a — Fila

- **Elemento:** Execution Queue
- **Targets:** lbl-queue, queue
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.15, 0.2714, 0.98, 0.3714]]
- **Final px boxes:** [[549, 205, 1517, 314]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Execution Queue — Fila de processamento do job. / Sem marcação, a escolha é automática.
- **Typing:** 00:01:52,567 → 00:01:53,767 (1.20s)
- **Seta:** 00:01:53,767
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** #queue

## 12_queue_b — Fila

- **Elemento:** Execution Queue — marcar
- **Targets:** lbl-queue, queue
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.15, 0.2714, 0.98, 0.3714]]
- **Final px boxes:** [[549, 205, 1517, 314]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Execution Queue — marcar — Marque filas só se o projeto indicar qual usar.
- **Typing:** 00:02:00,867 → 00:02:01,900 (1.03s)
- **Seta:** 00:02:01,900
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** _QUEUE_CHOICES

## 12b_queue_order — Fila

- **Elemento:** Várias filas
- **Targets:** queue-panel
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.2571, 0.99, 0.4143]]
- **Final px boxes:** [[532, 188, 1534, 355]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Várias filas — Se marcar várias, são tentadas na ordem da lista.
- **Typing:** 00:02:10,100 → 00:02:11,100 (1.00s)
- **Seta:** 00:02:11,100
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** _QUEUE_AUTO_HINT

## 13_sql_intro — SQL File

- **Elemento:** SQL File
- **Targets:** lbl-sql-file, sql-file
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.5, 0.99, 0.5429]]
- **Final px boxes:** [[538, 391, 1528, 453]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** SQL File — É a consulta que o job vai executar.
- **Typing:** 00:02:18,400 → 00:02:19,400 (1.00s)
- **Seta:** 00:02:19,400
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** row-sql-file

## 13b_sql_when — SQL File

- **Elemento:** SQL File — quando
- **Targets:** lbl-sql-file, sql-file
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.5, 0.99, 0.5429]]
- **Final px boxes:** [[538, 391, 1528, 453]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** SQL File — quando — Obrigatório para SqlFile e MonthlyJob.
- **Typing:** 00:02:26,700 → 00:02:27,700 (1.00s)
- **Seta:** 00:02:27,700
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** required sources

## 14_sql_picker — SQL File

- **Elemento:** Lista de arquivos SQL
- **Targets:** sql-file-picker
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.4429, 0.99, 0.4857]]
- **Final px boxes:** [[532, 343, 1534, 408]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Lista de arquivos SQL — Mostra os .sql da pasta atual. / Selecione o arquivo do seu job.
- **Typing:** 00:02:35,000 → 00:02:36,200 (1.20s)
- **Seta:** 00:02:36,200
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** sql-file-picker

## 15_sql_verify — SQL File

- **Elemento:** O que conferir
- **Targets:** sql-file-picker
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.4429, 0.99, 0.4857]]
- **Final px boxes:** [[532, 343, 1534, 408]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** O que conferir — Confirme o nome e o tipo Detected na lista.
- **Typing:** 00:02:44,233 → 00:02:45,233 (1.00s)
- **Seta:** 00:02:45,233
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** Detected column

## 15b_sql_path — SQL File

- **Elemento:** Caminho do SQL File
- **Targets:** lbl-sql-file, sql-file
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.5, 0.99, 0.5429]]
- **Final px boxes:** [[538, 391, 1528, 453]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Caminho do SQL File — Após a seleção, o caminho preenche o campo SQL File.
- **Typing:** 00:02:52,533 → 00:02:53,567 (1.03s)
- **Seta:** 00:02:53,567
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** path-hint

## 16_sql_role — SQL File

- **Elemento:** Papel do SQL File
- **Targets:** lbl-sql-file, sql-file
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.5, 0.99, 0.5429]]
- **Final px boxes:** [[538, 391, 1528, 453]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Papel do SQL File — Define quais dados serão lidos ou calculados.
- **Typing:** 00:03:00,833 → 00:03:01,833 (1.00s)
- **Seta:** 00:03:01,833
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** manifest sql_path

## 16b_sql_role_dest — SQL File

- **Elemento:** SQL + destino
- **Targets:** source, destination
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.15, 0.1571, 0.555, 0.2286], [0.575, 0.1571, 0.98, 0.2286]]
- **Final px boxes:** [[543, 107, 1042, 205], [1024, 107, 1523, 205]]
- **Cutouts:** 2
- **Overlay opacity:** 170/255
- **Diálogo:** SQL + destino — Source e Destination decidem como entregar o resultado.
- **Typing:** 00:03:09,133 → 00:03:10,133 (1.00s)
- **Seta:** 00:03:10,133
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** LEGAL_CELLS

## 17_email — Notificação

- **Elemento:** Email (notifications)
- **Targets:** lbl-email, email
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.5714, 0.99, 0.6143]]
- **Final px boxes:** [[538, 448, 1528, 511]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Email (notifications) — Recebe aviso quando o job terminar. / Deixe em branco se não quiser.
- **Typing:** 00:03:17,433 → 00:03:18,700 (1.27s)
- **Seta:** 00:03:18,700
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** #email

## 18_subject — Notificação

- **Elemento:** Subject (email)
- **Targets:** lbl-subject, subject
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.6286, 0.99, 0.6714]]
- **Final px boxes:** [[538, 495, 1528, 557]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Subject (email) — Assunto do e-mail de notificação. / Use um texto curto que identifique o job.
- **Typing:** 00:03:26,667 → 00:03:27,967 (1.30s)
- **Seta:** 00:03:27,967
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** #subject

## 19_status_bar — Status

- **Elemento:** Status do formulário
- **Targets:** validation-summary
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.135, 0.9429, 0.85, 0.9857]]
- **Final px boxes:** [[526, 748, 1376, 806]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Status do formulário — Ready to launch = sem problemas bloqueantes.
- **Typing:** 00:03:35,900 → 00:03:36,900 (1.00s)
- **Seta:** 00:03:36,900
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** validation-summary

## 19b_actions — Status

- **Elemento:** Preview SQL e Launch
- **Targets:** preview, launch
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.855, 0.9429, 0.925, 0.9857], [0.93, 0.9429, 0.99, 0.9857]]
- **Final px boxes:** [[1345, 748, 1457, 806], [1430, 748, 1530, 806]]
- **Cutouts:** 2
- **Overlay opacity:** 170/255
- **Diálogo:** Preview SQL e Launch — Ficam na barra inferior para revisão e envio.
- **Typing:** 00:03:44,200 → 00:03:45,200 (1.00s)
- **Seta:** 00:03:45,200
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** action bar

## 20_mj_intro — MonthlyJob

- **Elemento:** MonthlyJob
- **Targets:** src-sqltemplate
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.16, 0.1857, 0.54, 0.2]]
- **Final px boxes:** [[559, 142, 1021, 170]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** MonthlyJob — Use para cobrir um intervalo de datas, / executando o período mês a mês.
- **Typing:** 00:03:52,500 → 00:03:53,667 (1.17s)
- **Seta:** 00:03:53,667
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** SqlTemplate labeled MonthlyJob

## 21_mj_dest — MonthlyJob

- **Elemento:** MonthlyJob → Destination
- **Targets:** src-sqltemplate, dst-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.16, 0.1857, 0.54, 0.2], [0.58, 0.1714, 0.96, 0.1857]]
- **Final px boxes:** [[559, 142, 1021, 170], [1034, 130, 1496, 158]]
- **Cutouts:** 2
- **Overlay opacity:** 170/255
- **Diálogo:** MonthlyJob → Destination — Com MonthlyJob, o destino permitido é só Table.
- **Typing:** 00:04:01,733 → 00:04:02,767 (1.03s)
- **Seta:** 00:04:02,767
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** LEGAL SqlTemplate/Table

## 21b_mj_dest_blocked — MonthlyJob

- **Elemento:** Csv e Table+Csv
- **Targets:** dst-csv, dst-table-csv
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.58, 0.1857, 0.96, 0.2], [0.58, 0.2, 0.96, 0.2143]]
- **Final px boxes:** [[1034, 142, 1496, 170], [1034, 154, 1496, 181]]
- **Cutouts:** 2
- **Overlay opacity:** 170/255
- **Diálogo:** Csv e Table+Csv — Ficam indisponíveis neste modo.
- **Typing:** 00:04:10,033 → 00:04:11,033 (1.00s)
- **Seta:** 00:04:11,033
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** dest hint

## 22_mj_sql_rule_a — MonthlyJob SQL

- **Elemento:** SQL no MonthlyJob — regra
- **Targets:** (card)
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.12, 0.14, 0.88, 0.7]]
- **Final px boxes:** [[80, 100, 1840, 786]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** SQL no MonthlyJob — regra — O .sql precisa conter os dois marcadores: / {date_inicio} e {date_fim}
- **Typing:** 00:04:18,033 → 00:04:19,367 (1.33s)
- **Seta:** 00:04:19,367
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** dispatch/sql.py:DATE_INICIO_TOKEN/DATE_FIM_TOKEN, detect_source, template_is_complete, is_malformed_template, monthly_preview; dispatch/screens/new_job.py:_sql_content_issues (requires both tokens for SqlTemplate/MonthlyJob); scr/monthly_query_processor.py:render_monthly_sql; CONTEXT.md (SqlTemplate placeholders); tests/test_monthly_query_processor.py, tools/prod_tui/job_specs.py SMOKE_TEMPLATE_SQL

## 23_mj_sql_rule_b — MonthlyJob SQL

- **Elemento:** Como conferir no arquivo
- **Targets:** (card)
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.12, 0.14, 0.88, 0.7]]
- **Final px boxes:** [[80, 100, 1840, 786]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Como conferir no arquivo — Abra o .sql e busque exatamente / {date_inicio} e {date_fim}.
- **Typing:** 00:04:26,033 → 00:04:27,233 (1.20s)
- **Seta:** 00:04:27,233
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** _sql_content_issues

## 23b_mj_sql_missing — MonthlyJob SQL

- **Elemento:** Se faltar um marcador
- **Targets:** (card)
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.12, 0.14, 0.88, 0.7]]
- **Final px boxes:** [[80, 100, 1840, 786]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Se faltar um marcador — O job não pode ser iniciado como MonthlyJob.
- **Typing:** 00:04:34,033 → 00:04:35,033 (1.00s)
- **Seta:** 00:04:35,033
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** is_malformed_template

## 24_mj_sql_rule_c — MonthlyJob SQL

- **Elemento:** O que os marcadores fazem
- **Targets:** (card)
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.12, 0.14, 0.88, 0.7]]
- **Final px boxes:** [[80, 100, 1840, 786]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** O que os marcadores fazem — Reservam início e fim de cada mês do período.
- **Typing:** 00:04:42,033 → 00:04:43,033 (1.00s)
- **Seta:** 00:04:43,033
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** render_monthly_sql

## 24b_mj_sql_fill — MonthlyJob SQL

- **Elemento:** Preenchimento das datas
- **Targets:** (card)
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.12, 0.14, 0.88, 0.7]]
- **Final px boxes:** [[80, 100, 1840, 786]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Preenchimento das datas — O Dispatch preenche conforme Start Date e End Date.
- **Typing:** 00:04:50,033 → 00:04:51,100 (1.07s)
- **Seta:** 00:04:51,100
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** monthly_preview

## 25_mj_picker — MonthlyJob SQL

- **Elemento:** SQL do MonthlyJob
- **Targets:** sql-file-picker
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.4571, 0.98, 0.5]]
- **Final px boxes:** [[532, 355, 1523, 420]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** SQL do MonthlyJob — Na lista, escolha Detected = MonthlyJob.
- **Typing:** 00:04:58,333 → 00:04:59,333 (1.00s)
- **Seta:** 00:04:59,333
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** detect_source

## 25b_mj_picker_confirm — MonthlyJob SQL

- **Elemento:** Detected = MonthlyJob
- **Targets:** sql-file-picker
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.4571, 0.98, 0.5]]
- **Final px boxes:** [[532, 355, 1523, 420]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Detected = MonthlyJob — Confirma que os dois marcadores foram encontrados.
- **Typing:** 00:05:07,567 → 00:05:08,600 (1.03s)
- **Seta:** 00:05:08,600
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** picker Detected

## 26_mj_schema — MonthlyJob campos

- **Elemento:** Schema (MonthlyJob)
- **Targets:** lbl-schema, schema
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.5857, 0.98, 0.6286]]
- **Final px boxes:** [[538, 460, 1517, 523]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Schema (MonthlyJob) — Schema da tabela de resultado. / Informe o schema correto do seu trabalho.
- **Typing:** 00:05:15,867 → 00:05:17,167 (1.30s)
- **Seta:** 00:05:17,167
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** #schema

## 27_mj_table — MonthlyJob campos

- **Elemento:** Table Name (MonthlyJob)
- **Targets:** lbl-table-name, table-name-prefix, table-name-suffix
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.6429, 0.98, 0.6857]]
- **Final px boxes:** [[538, 506, 1517, 569]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Table Name (MonthlyJob) — Nome da tabela com o prefixo do usuário.
- **Typing:** 00:05:24,167 → 00:05:25,167 (1.00s)
- **Seta:** 00:05:25,167
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** #table-name-prefix

## 27b_mj_table_suffix — MonthlyJob campos

- **Elemento:** Sufixo da tabela
- **Targets:** table-name-prefix, table-name-suffix
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.25, 0.6429, 0.98, 0.6857]]
- **Final px boxes:** [[657, 505, 1523, 570]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Sufixo da tabela — Complete só o sufixo; o prefixo já vem preenchido.
- **Typing:** 00:05:32,467 → 00:05:33,467 (1.00s)
- **Seta:** 00:05:33,467
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** #table-name-suffix

## 28_mj_start — MonthlyJob campos

- **Elemento:** Start Date
- **Targets:** lbl-start-date, start-date
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.7, 0.98, 0.7429]]
- **Final px boxes:** [[538, 553, 1517, 615]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Start Date — Data inicial (AAAA-MM-DD). / Define o primeiro mês a processar.
- **Typing:** 00:05:40,767 → 00:05:41,800 (1.03s)
- **Seta:** 00:05:41,800
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** #start-date

## 29_mj_end — MonthlyJob campos

- **Elemento:** End Date
- **Targets:** lbl-end-date, end-date
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.7571, 0.98, 0.8]]
- **Final px boxes:** [[538, 599, 1517, 662]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** End Date — Data final (AAAA-MM-DD). / Deve ser igual ou posterior à Start Date.
- **Typing:** 00:05:49,067 → 00:05:50,133 (1.07s)
- **Seta:** 00:05:50,133
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** #end-date

## 30_et_intro — ExistingTable

- **Elemento:** ExistingTable
- **Targets:** src-existingtable
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.16, 0.2, 0.545, 0.2143]]
- **Final px boxes:** [[559, 154, 1026, 181]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** ExistingTable — Use quando os dados já estão em uma tabela / e você quer exportá-los sem .sql.
- **Typing:** 00:05:57,367 → 00:05:58,667 (1.30s)
- **Seta:** 00:05:58,667
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** src-existingtable

## 31_et_dest — ExistingTable

- **Elemento:** ExistingTable → Destination
- **Targets:** src-existingtable, dst-csv
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.16, 0.2, 0.545, 0.2143], [0.585, 0.1857, 0.97, 0.2]]
- **Final px boxes:** [[559, 154, 1026, 181], [1040, 142, 1508, 170]]
- **Cutouts:** 2
- **Overlay opacity:** 170/255
- **Diálogo:** ExistingTable → Destination — Neste modo o destino permitido é apenas Csv.
- **Typing:** 00:06:06,600 → 00:06:07,633 (1.03s)
- **Seta:** 00:06:07,633
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** LEGAL ExistingTable/Csv

## 31b_et_dest_blocked — ExistingTable

- **Elemento:** Table e Table+Csv
- **Targets:** dst-table, dst-table-csv
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.585, 0.1714, 0.97, 0.1857], [0.585, 0.2, 0.97, 0.2143]]
- **Final px boxes:** [[1040, 130, 1508, 158], [1040, 154, 1508, 181]]
- **Cutouts:** 2
- **Overlay opacity:** 170/255
- **Diálogo:** Table e Table+Csv — Ficam indisponíveis com ExistingTable.
- **Typing:** 00:06:14,900 → 00:06:15,900 (1.00s)
- **Seta:** 00:06:15,900
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** dest hint

## 32_et_no_sql — ExistingTable

- **Elemento:** Sem SQL File
- **Targets:** src-existingtable, dest-hint
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.16, 0.2, 0.545, 0.2143], [0.14, 0.2429, 0.99, 0.2571]]
- **Final px boxes:** [[559, 154, 1026, 181], [538, 188, 1528, 216]]
- **Cutouts:** 2
- **Overlay opacity:** 170/255
- **Diálogo:** Sem SQL File — A lista e o campo SQL File ficam ocultos. / A origem é a tabela existente.
- **Typing:** 00:06:23,200 → 00:06:24,400 (1.20s)
- **Seta:** 00:06:24,400
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** picker display=False

## 33_et_schema_coe — ExistingTable Schema

- **Elemento:** Schema → coe_enc
- **Targets:** esc-coe-enc
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.26, 0.4714, 0.97, 0.4857]]
- **Final px boxes:** [[672, 373, 1508, 401]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Schema → coe_enc — Seleciona o schema coe_enc da tabela existente.
- **Typing:** 00:06:31,500 → 00:06:32,500 (1.00s)
- **Seta:** 00:06:32,500
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** esc-coe-enc

## 34_et_schema_aa — ExistingTable Schema

- **Elemento:** Schema → aa_enc
- **Targets:** esc-aa-enc
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.26, 0.4857, 0.97, 0.5]]
- **Final px boxes:** [[672, 385, 1508, 413]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Schema → aa_enc — Seleciona o schema aa_enc. / É a opção padrão nesse schema.
- **Typing:** 00:06:40,733 → 00:06:41,767 (1.03s)
- **Seta:** 00:06:41,767
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** esc-aa-enc

## 35_et_schema_other — ExistingTable Schema

- **Elemento:** Schema → other
- **Targets:** esc-other
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.26, 0.5, 0.97, 0.5143]]
- **Final px boxes:** [[672, 397, 1508, 424]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Schema → other — Use quando o schema não é coe_enc nem aa_enc.
- **Typing:** 00:06:49,967 → 00:06:50,967 (1.00s)
- **Seta:** 00:06:50,967
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** esc-other

## 35b_et_other_field — ExistingTable Schema

- **Elemento:** other → Custom Schema
- **Targets:** lbl-existing-schema-custom, existing-schema-custom
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.5143, 0.99, 0.5571]]
- **Final px boxes:** [[538, 402, 1528, 465]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** other → Custom Schema — Ao marcar other, aparece o campo Custom Schema.
- **Typing:** 00:06:59,200 → 00:07:00,200 (1.00s)
- **Seta:** 00:07:00,200
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** #existing-schema-custom

## 36_et_custom — ExistingTable Schema

- **Elemento:** Custom Schema
- **Targets:** lbl-existing-schema-custom, existing-schema-custom
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.5143, 0.99, 0.5571]]
- **Final px boxes:** [[538, 402, 1528, 465]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Custom Schema — Digite o nome do schema personalizado. / Só aparece com Schema = other.
- **Typing:** 00:07:07,500 → 00:07:08,700 (1.20s)
- **Seta:** 00:07:08,700
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** row-existing-schema-custom

## 37_et_table — ExistingTable

- **Elemento:** Existing Table
- **Targets:** lbl-existing-table, existing-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.5143, 0.99, 0.5571]]
- **Final px boxes:** [[538, 402, 1528, 465]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Existing Table — Informe só o nome da tabela (sem o schema).
- **Typing:** 00:07:15,800 → 00:07:16,800 (1.00s)
- **Seta:** 00:07:16,800
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** #existing-table

## 37b_et_full — ExistingTable

- **Elemento:** Origem completa
- **Targets:** lbl-existing-schema, existing-schema, lbl-existing-table, existing-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.4571, 0.99, 0.5], [0.14, 0.5143, 0.99, 0.5571]]
- **Final px boxes:** [[538, 356, 1528, 419], [532, 401, 1534, 466]]
- **Cutouts:** 2
- **Overlay opacity:** 170/255
- **Diálogo:** Origem completa — Com o schema, forma schema.tabela.
- **Typing:** 00:07:25,033 → 00:07:26,033 (1.00s)
- **Seta:** 00:07:26,033
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** validate_full_table

## 38_rel_standard — Relações

- **Elemento:** Combinação comum
- **Targets:** src-sqlfile, dst-csv
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.16, 0.1714, 0.545, 0.1857], [0.585, 0.1857, 0.97, 0.2]]
- **Final px boxes:** [[559, 130, 1026, 158], [1040, 142, 1508, 170]]
- **Cutouts:** 2
- **Overlay opacity:** 170/255
- **Diálogo:** Combinação comum — SqlFile + Csv + .sql sem marcadores de data.
- **Typing:** 00:07:33,333 → 00:07:34,333 (1.00s)
- **Seta:** 00:07:34,333
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** LEGAL SqlFile/Csv

## 38b_rel_standard_use — Relações

- **Elemento:** Fluxo típico
- **Targets:** src-sqlfile, dst-csv
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.16, 0.1714, 0.545, 0.1857], [0.585, 0.1857, 0.97, 0.2]]
- **Final px boxes:** [[559, 130, 1026, 158], [1040, 142, 1508, 170]]
- **Cutouts:** 2
- **Overlay opacity:** 170/255
- **Diálogo:** Fluxo típico — Gera um CSV a partir de uma consulta.
- **Typing:** 00:07:42,567 → 00:07:43,567 (1.00s)
- **Seta:** 00:07:43,567
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** detect_source

## 39_rel_monthly — Relações

- **Elemento:** Combinação MonthlyJob
- **Targets:** src-sqltemplate, dst-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.16, 0.1857, 0.54, 0.2], [0.58, 0.1714, 0.96, 0.1857]]
- **Final px boxes:** [[559, 142, 1021, 170], [1034, 130, 1496, 158]]
- **Cutouts:** 2
- **Overlay opacity:** 170/255
- **Diálogo:** Combinação MonthlyJob — MonthlyJob + Table + .sql com / {date_inicio} e {date_fim}.
- **Typing:** 00:07:50,867 → 00:07:52,000 (1.13s)
- **Seta:** 00:07:52,000
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** LEGAL SqlTemplate/Table

## 39b_rel_monthly_fields — Relações

- **Elemento:** Campos do MonthlyJob
- **Targets:** lbl-schema, schema, lbl-table-name, table-name-prefix, table-name-suffix
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.5857, 0.98, 0.6286], [0.14, 0.6429, 0.98, 0.6857]]
- **Final px boxes:** [[538, 460, 1517, 523], [532, 505, 1523, 570]]
- **Cutouts:** 2
- **Overlay opacity:** 170/255
- **Diálogo:** Campos do MonthlyJob — Schema e Table Name entram no nome da tabela.
- **Typing:** 00:07:59,167 → 00:08:00,167 (1.00s)
- **Seta:** 00:08:00,167
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** date fields

## 39c_rel_monthly_dates — Relações

- **Elemento:** Datas do MonthlyJob
- **Targets:** lbl-start-date, start-date, lbl-end-date, end-date
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.7, 0.98, 0.7429], [0.14, 0.7571, 0.98, 0.8]]
- **Final px boxes:** [[538, 553, 1517, 615], [532, 598, 1523, 663]]
- **Cutouts:** 2
- **Overlay opacity:** 170/255
- **Diálogo:** Datas do MonthlyJob — Start Date e End Date definem o intervalo mês a mês.
- **Typing:** 00:08:07,467 → 00:08:08,500 (1.03s)
- **Seta:** 00:08:08,500
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** monthly dates

## 40_rel_existing — Relações

- **Elemento:** Combinação ExistingTable
- **Targets:** src-existingtable, dst-csv
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.16, 0.2, 0.545, 0.2143], [0.585, 0.1857, 0.97, 0.2]]
- **Final px boxes:** [[559, 154, 1026, 181], [1040, 142, 1508, 170]]
- **Cutouts:** 2
- **Overlay opacity:** 170/255
- **Diálogo:** Combinação ExistingTable — ExistingTable + Csv + Schema + Existing Table.
- **Typing:** 00:08:15,767 → 00:08:16,767 (1.00s)
- **Seta:** 00:08:16,767
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** ExistingTable flow

## 40b_rel_existing_no_sql — Relações

- **Elemento:** Sem SQL neste modo
- **Targets:** src-existingtable
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.16, 0.2, 0.545, 0.2143]]
- **Final px boxes:** [[559, 154, 1026, 181]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Sem SQL neste modo — Não usa SQL File nem MonthlyJob ao mesmo tempo.
- **Typing:** 00:08:24,067 → 00:08:25,067 (1.00s)
- **Seta:** 00:08:25,067
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** source exclusive

## 41_rel_incompat — Relações

- **Elemento:** Combinações indisponíveis
- **Targets:** matrix-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.155, 0.1, 0.995, 0.1571]]
- **Final px boxes:** [[549, 61, 1540, 147]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Combinações indisponíveis — MonthlyJob não aceita Csv ou Table+Csv.
- **Typing:** 00:08:32,367 → 00:08:33,367 (1.00s)
- **Seta:** 00:08:33,367
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** LEGAL_CELLS

## 41b_rel_incompat_et — Relações

- **Elemento:** ExistingTable — limite
- **Targets:** matrix-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.155, 0.1, 0.995, 0.1571]]
- **Final px boxes:** [[549, 61, 1540, 147]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** ExistingTable — limite — ExistingTable não aceita Table ou Table+Csv.
- **Typing:** 00:08:40,667 → 00:08:41,667 (1.00s)
- **Seta:** 00:08:41,667
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** LEGAL_CELLS

## 42_val_bad — Validação

- **Elemento:** E-mail inválido
- **Targets:** lbl-email, email, validation-summary
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.5714, 0.99, 0.6143], [0.135, 0.9429, 0.85, 0.9857]]
- **Final px boxes:** [[538, 448, 1528, 511], [526, 748, 1376, 806]]
- **Cutouts:** 2
- **Overlay opacity:** 170/255
- **Diálogo:** E-mail inválido — Se o formato estiver errado, o status mostra o problema.
- **Typing:** 00:08:48,967 → 00:08:50,000 (1.03s)
- **Seta:** 00:08:50,000
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** Invalid email

## 43_val_ok — Validação

- **Elemento:** Formulário pronto
- **Targets:** validation-summary
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.135, 0.9429, 0.85, 0.9857]]
- **Final px boxes:** [[526, 748, 1376, 806]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Formulário pronto — Com os dados corrigidos, volta Ready to launch.
- **Typing:** 00:08:57,267 → 00:08:58,267 (1.00s)
- **Seta:** 00:08:58,267
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** Ready to launch

## 43b_val_review — Validação

- **Elemento:** Revise antes de enviar
- **Targets:** source, destination
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.15, 0.1571, 0.555, 0.2286], [0.575, 0.1571, 0.98, 0.2286]]
- **Final px boxes:** [[543, 107, 1042, 205], [1024, 107, 1523, 205]]
- **Cutouts:** 2
- **Overlay opacity:** 170/255
- **Diálogo:** Revise antes de enviar — Confira origem, destino, arquivo e fila.
- **Typing:** 00:09:05,567 → 00:09:06,567 (1.00s)
- **Seta:** 00:09:06,567
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** form review

## 44_preview — Preview

- **Elemento:** Preview SQL
- **Targets:** preview
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.855, 0.9429, 0.925, 0.9857]]
- **Final px boxes:** [[1345, 748, 1457, 806]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Preview SQL — Mostra o conteúdo que será usado no job.
- **Typing:** 00:09:13,867 → 00:09:14,867 (1.00s)
- **Seta:** 00:09:14,867
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** Preview SQL [P]

## 44b_preview_check — Preview

- **Elemento:** O que conferir no Preview
- **Targets:** preview-header, preview-body
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.13, 0.0571, 1.0, 0.1], [0.14, 0.1143, 0.99, 0.5143]]
- **Final px boxes:** [[521, 31, 1546, 96], [532, 72, 1534, 436]]
- **Cutouts:** 2
- **Overlay opacity:** 170/255
- **Diálogo:** O que conferir no Preview — Confira a consulta e o destino antes do envio.
- **Typing:** 00:09:23,100 → 00:09:24,133 (1.03s)
- **Seta:** 00:09:24,133
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** preview screen

## 45_checklist — Revisão

- **Elemento:** Antes de iniciar, confirme
- **Targets:** (card)
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.12, 0.14, 0.88, 0.7]]
- **Final px boxes:** [[80, 100, 1840, 786]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Antes de iniciar, confirme — Origem, destino, arquivo ou tabela, / e fila de execução.
- **Typing:** 00:09:31,100 → 00:09:32,267 (1.17s)
- **Seta:** 00:09:32,267
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** checklist

## 45b_checklist_b — Revisão

- **Elemento:** Também confira
- **Targets:** (card)
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.12, 0.14, 0.88, 0.7]]
- **Final px boxes:** [[80, 100, 1840, 786]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Também confira — Opções adicionais e e-mail de notificação.
- **Typing:** 00:09:39,100 → 00:09:40,100 (1.00s)
- **Seta:** 00:09:40,100
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** checklist

## 46_confirm — Envio

- **Elemento:** Launch Job
- **Targets:** confirm-dialog
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.34, 0.3571, 0.66, 0.6714]]
- **Final px boxes:** [[758, 269, 1161, 563]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Launch Job — Inicia o job com as configurações revisadas.
- **Typing:** 00:09:47,400 → 00:09:48,400 (1.00s)
- **Seta:** 00:09:48,400
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** ConfirmScreen

## 46b_confirm_read — Envio

- **Elemento:** Confirme só se estiver correto
- **Targets:** confirm-dialog
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.34, 0.3571, 0.66, 0.6714]]
- **Final px boxes:** [[758, 269, 1161, 563]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Confirme só se estiver correto — Leia o resumo antes de confirmar o envio.
- **Typing:** 00:09:56,633 → 00:09:57,667 (1.03s)
- **Seta:** 00:09:57,667
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** Launch Job

## 47_launched — Envio

- **Elemento:** Job enviado
- **Targets:** warning-text
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.135, 0.7714, 0.995, 0.7857]]
- **Final px boxes:** [[526, 616, 1540, 644]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Job enviado — O job foi enviado pelo Dispatch. / Acompanhe na tela de monitoramento.
- **Typing:** 00:10:04,933 → 00:10:06,067 (1.13s)
- **Seta:** 00:10:06,067
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** Launched Job

## 48_overview — Overview

- **Elemento:** Overview
- **Targets:** sidebar-nav
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.0, 0.0571, 0.125, 0.3]]
- **Final px boxes:** [[374, 26, 555, 263]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Overview — Após o envio, acompanhe o status no Overview.
- **Typing:** 00:10:13,233 → 00:10:14,233 (1.00s)
- **Seta:** 00:10:14,233
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** DashboardScreen

## 49_close — Encerramento

- **Elemento:** Resumo
- **Targets:** (card)
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.12, 0.14, 0.88, 0.7]]
- **Final px boxes:** [[80, 100, 1840, 786]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Resumo — Na aba New Job você define, revisa e inicia o job.
- **Typing:** 00:10:22,167 → 00:10:23,167 (1.00s)
- **Seta:** 00:10:23,167
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** closing

## 49b_close_b — Encerramento

- **Elemento:** Depois do envio
- **Targets:** (card)
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.12, 0.14, 0.88, 0.7]]
- **Final px boxes:** [[80, 100, 1840, 786]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Depois do envio — Acompanhe o resultado no Overview. / Revise os campos antes de Launch Job.
- **Typing:** 00:10:30,167 → 00:10:31,433 (1.27s)
- **Seta:** 00:10:31,433
- **Duração:** 8.00s
- **Manual review:** PASS
- **Evidência:** closing
