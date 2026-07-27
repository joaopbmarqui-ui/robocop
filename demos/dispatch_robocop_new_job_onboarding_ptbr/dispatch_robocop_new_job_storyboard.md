# Storyboard — New Job (8.0s, GBA dialogue, real spotlight)

Sem narração/música. Cada cena instrucional = exatamente 8.0s (inclui typewriter).
Overlay escuro alpha=168. Caixa branca inferior com borda preta e seta vermelha.

## 01_open — Abertura

- **Elemento:** Dispatch (Robocop)
- **Spotlight target:** Dispatch (Robocop)
- **Spotlight coords (norm):** `0.10,0.14,0.90,0.72`
- **Overlay opacity:** 168/255
- **Diálogo:** Dispatch (Robocop) — Como utilizar a aba New Job. / Configure e inicie um job passo a passo.
- **Typing:** 00:00:00,000 → 00:00:01,267 (1.27s)
- **Seta vermelha:** 00:00:01,267
- **Início/fim:** 00:00:00,000 → 00:00:08,000
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** opening card

## 02_purpose_a — Propósito

- **Elemento:** Para que serve New Job
- **Spotlight target:** Para que serve New Job
- **Spotlight coords (norm):** `0.27,0.02,0.83,0.22`
- **Overlay opacity:** 168/255
- **Diálogo:** Para que serve New Job — Configure e inicie uma nova execução no Dispatch.
- **Typing:** 00:00:08,300 → 00:00:09,333 (1.03s)
- **Seta vermelha:** 00:00:09,333
- **Início/fim:** 00:00:08,300 → 00:00:16,300
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** NewJobScreen

## 02_purpose_b — Propósito

- **Elemento:** O que você decide aqui
- **Spotlight target:** O que você decide aqui
- **Spotlight coords (norm):** `0.27,0.10,0.83,0.30`
- **Overlay opacity:** 168/255
- **Diálogo:** O que você decide aqui — Origem, destino, consulta e opções do job.
- **Typing:** 00:00:16,600 → 00:00:17,600 (1.00s)
- **Seta vermelha:** 00:00:17,600
- **Início/fim:** 00:00:16,600 → 00:00:24,600
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** NewJobScreen form

## 03_matrix — Matriz

- **Elemento:** Source × Destination
- **Spotlight target:** Source × Destination
- **Spotlight coords (norm):** `0.07,0.04,0.97,0.28`
- **Overlay opacity:** 168/255
- **Diálogo:** Source × Destination — Mostra as combinações permitidas. / Consulte antes de escolher origem e destino.
- **Typing:** 00:00:24,900 → 00:00:26,300 (1.40s)
- **Seta vermelha:** 00:00:26,300
- **Início/fim:** 00:00:24,900 → 00:00:32,900
- **Duração total:** 8.00s
- **Ação após a cena:** clique após a cena
- **Evidência:** matrix-collapsible + LEGAL_CELLS

## 04_detected — Detecção

- **Elemento:** Detected source
- **Spotlight target:** Detected source
- **Spotlight coords (norm):** `0.12,0.20,0.92,0.32`
- **Overlay opacity:** 168/255
- **Diálogo:** Detected source — Tipo identificado no arquivo SQL. / Confirme se é o job que você quer executar.
- **Typing:** 00:00:34,133 → 00:00:35,467 (1.33s)
- **Seta vermelha:** 00:00:35,467
- **Início/fim:** 00:00:34,133 → 00:00:42,133
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** info-detected

## 05_source_intro — Source

- **Elemento:** Source
- **Spotlight target:** Source
- **Spotlight coords (norm):** `0.18,0.22,0.54,0.42`
- **Overlay opacity:** 168/255
- **Diálogo:** Source — Define de onde vêm os dados do job. / É a primeira decisão do formulário.
- **Typing:** 00:00:42,433 → 00:00:43,533 (1.10s)
- **Seta vermelha:** 00:00:43,533
- **Início/fim:** 00:00:42,433 → 00:00:50,433
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** RadioSet #source

## 06_source_sqlfile — Source

- **Elemento:** Source → SqlFile
- **Spotlight target:** Source → SqlFile
- **Spotlight coords (norm):** `0.18,0.22,0.54,0.42`
- **Overlay opacity:** 168/255
- **Diálogo:** Source → SqlFile — Use quando a consulta está em um .sql simples.
- **Typing:** 00:00:50,733 → 00:00:51,733 (1.00s)
- **Seta vermelha:** 00:00:51,733
- **Início/fim:** 00:00:50,733 → 00:00:58,733
- **Duração total:** 8.00s
- **Ação após a cena:** clique após a cena
- **Evidência:** src-sqlfile

## 06b_source_sqlfile_effect — Source

- **Elemento:** SqlFile — efeito
- **Spotlight target:** SqlFile — efeito
- **Spotlight coords (norm):** `0.18,0.22,0.54,0.42`
- **Overlay opacity:** 168/255
- **Diálogo:** SqlFile — efeito — O Dispatch executa esse arquivo conforme o destino.
- **Typing:** 00:00:59,967 → 00:01:00,967 (1.00s)
- **Seta vermelha:** 00:01:00,967
- **Início/fim:** 00:00:59,967 → 00:01:07,967
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** LEGAL SqlFile

## 07_dest_intro — Destination

- **Elemento:** Destination
- **Spotlight target:** Destination
- **Spotlight coords (norm):** `0.52,0.20,0.88,0.40`
- **Overlay opacity:** 168/255
- **Diálogo:** Destination — Define onde o resultado será armazenado. / Depende da origem escolhida.
- **Typing:** 00:01:08,267 → 00:01:09,433 (1.17s)
- **Seta vermelha:** 00:01:09,433
- **Início/fim:** 00:01:08,267 → 00:01:16,267
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** #destination

## 08_dest_table — Destination

- **Elemento:** Destination → Table
- **Spotlight target:** Destination → Table
- **Spotlight coords (norm):** `0.52,0.18,0.88,0.34`
- **Overlay opacity:** 168/255
- **Diálogo:** Destination → Table — Salva o resultado em uma tabela. / Use para consultar depois no ambiente.
- **Typing:** 00:01:16,567 → 00:01:17,867 (1.30s)
- **Seta vermelha:** 00:01:17,867
- **Início/fim:** 00:01:16,567 → 00:01:24,567
- **Duração total:** 8.00s
- **Ação após a cena:** clique após a cena
- **Evidência:** dst-table

## 09_dest_csv — Destination

- **Elemento:** Destination → Csv
- **Spotlight target:** Destination → Csv
- **Spotlight coords (norm):** `0.52,0.22,0.88,0.38`
- **Overlay opacity:** 168/255
- **Diálogo:** Destination → Csv — Gera um CSV na pasta em que você abriu o Dispatch.
- **Typing:** 00:01:25,800 → 00:01:26,800 (1.00s)
- **Seta vermelha:** 00:01:26,800
- **Início/fim:** 00:01:25,800 → 00:01:33,800
- **Duração total:** 8.00s
- **Ação após a cena:** clique após a cena
- **Evidência:** dst-csv

## 09b_dest_csv_when — Destination

- **Elemento:** Csv — quando usar
- **Spotlight target:** Csv — quando usar
- **Spotlight coords (norm):** `0.52,0.22,0.88,0.38`
- **Overlay opacity:** 168/255
- **Diálogo:** Csv — quando usar — Use para baixar ou compartilhar o resultado como arquivo.
- **Typing:** 00:01:35,033 → 00:01:36,100 (1.07s)
- **Seta vermelha:** 00:01:36,100
- **Início/fim:** 00:01:35,033 → 00:01:43,033
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** ADR-0003

## 10_dest_tablecsv — Destination

- **Elemento:** Destination → Table+Csv
- **Spotlight target:** Destination → Table+Csv
- **Spotlight coords (norm):** `0.52,0.26,0.88,0.42`
- **Overlay opacity:** 168/255
- **Diálogo:** Destination → Table+Csv — Cria a tabela e também gera o CSV. / Use quando precisa dos dois formatos.
- **Typing:** 00:01:43,333 → 00:01:44,700 (1.37s)
- **Seta vermelha:** 00:01:44,700
- **Início/fim:** 00:01:43,333 → 00:01:51,333
- **Duração total:** 8.00s
- **Ação após a cena:** clique após a cena
- **Evidência:** dst-table-csv

## 11_queue_a — Fila

- **Elemento:** Execution Queue
- **Spotlight target:** Execution Queue
- **Spotlight coords (norm):** `0.17,0.34,0.93,0.62`
- **Overlay opacity:** 168/255
- **Diálogo:** Execution Queue — Fila de processamento do job. / Sem marcação, a escolha é automática.
- **Typing:** 00:01:52,567 → 00:01:53,767 (1.20s)
- **Seta vermelha:** 00:01:53,767
- **Início/fim:** 00:01:52,567 → 00:02:00,567
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** #queue

## 12_queue_b — Fila

- **Elemento:** Execution Queue — marcar
- **Spotlight target:** Execution Queue — marcar
- **Spotlight coords (norm):** `0.17,0.38,0.93,0.66`
- **Overlay opacity:** 168/255
- **Diálogo:** Execution Queue — marcar — Marque filas só se o projeto indicar qual usar.
- **Typing:** 00:02:00,867 → 00:02:01,900 (1.03s)
- **Seta vermelha:** 00:02:01,900
- **Início/fim:** 00:02:00,867 → 00:02:08,867
- **Duração total:** 8.00s
- **Ação após a cena:** clique após a cena
- **Evidência:** _QUEUE_CHOICES

## 12b_queue_order — Fila

- **Elemento:** Várias filas
- **Spotlight target:** Várias filas
- **Spotlight coords (norm):** `0.17,0.38,0.93,0.66`
- **Overlay opacity:** 168/255
- **Diálogo:** Várias filas — Se marcar várias, são tentadas na ordem da lista.
- **Typing:** 00:02:10,100 → 00:02:11,100 (1.00s)
- **Seta vermelha:** 00:02:11,100
- **Início/fim:** 00:02:10,100 → 00:02:18,100
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** _QUEUE_AUTO_HINT

## 13_sql_intro — SQL File

- **Elemento:** SQL File
- **Spotlight target:** SQL File
- **Spotlight coords (norm):** `0.13,0.44,0.97,0.72`
- **Overlay opacity:** 168/255
- **Diálogo:** SQL File — É a consulta que o job vai executar.
- **Typing:** 00:02:18,400 → 00:02:19,400 (1.00s)
- **Seta vermelha:** 00:02:19,400
- **Início/fim:** 00:02:18,400 → 00:02:26,400
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** row-sql-file

## 13b_sql_when — SQL File

- **Elemento:** SQL File — quando
- **Spotlight target:** SQL File — quando
- **Spotlight coords (norm):** `0.13,0.44,0.97,0.72`
- **Overlay opacity:** 168/255
- **Diálogo:** SQL File — quando — Obrigatório para SqlFile e MonthlyJob.
- **Typing:** 00:02:26,700 → 00:02:27,700 (1.00s)
- **Seta vermelha:** 00:02:27,700
- **Início/fim:** 00:02:26,700 → 00:02:34,700
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** required sources

## 14_sql_picker — SQL File

- **Elemento:** Lista de arquivos SQL
- **Spotlight target:** Lista de arquivos SQL
- **Spotlight coords (norm):** `0.13,0.44,0.97,0.72`
- **Overlay opacity:** 168/255
- **Diálogo:** Lista de arquivos SQL — Mostra os .sql da pasta atual. / Selecione o arquivo do seu job.
- **Typing:** 00:02:35,000 → 00:02:36,200 (1.20s)
- **Seta vermelha:** 00:02:36,200
- **Início/fim:** 00:02:35,000 → 00:02:43,000
- **Duração total:** 8.00s
- **Ação após a cena:** clique após a cena
- **Evidência:** sql-file-picker

## 15_sql_verify — SQL File

- **Elemento:** O que conferir
- **Spotlight target:** O que conferir
- **Spotlight coords (norm):** `0.13,0.46,0.97,0.78`
- **Overlay opacity:** 168/255
- **Diálogo:** O que conferir — Confirme o nome e o tipo Detected na lista.
- **Typing:** 00:02:44,233 → 00:02:45,233 (1.00s)
- **Seta vermelha:** 00:02:45,233
- **Início/fim:** 00:02:44,233 → 00:02:52,233
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** Detected column

## 15b_sql_path — SQL File

- **Elemento:** Caminho do SQL File
- **Spotlight target:** Caminho do SQL File
- **Spotlight coords (norm):** `0.13,0.62,0.97,0.78`
- **Overlay opacity:** 168/255
- **Diálogo:** Caminho do SQL File — Após a seleção, o caminho preenche o campo SQL File.
- **Typing:** 00:02:52,533 → 00:02:53,567 (1.03s)
- **Seta vermelha:** 00:02:53,567
- **Início/fim:** 00:02:52,533 → 00:03:00,533
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** path-hint

## 16_sql_role — SQL File

- **Elemento:** Papel do SQL File
- **Spotlight target:** Papel do SQL File
- **Spotlight coords (norm):** `0.13,0.58,0.97,0.78`
- **Overlay opacity:** 168/255
- **Diálogo:** Papel do SQL File — Define quais dados serão lidos ou calculados.
- **Typing:** 00:03:00,833 → 00:03:01,833 (1.00s)
- **Seta vermelha:** 00:03:01,833
- **Início/fim:** 00:03:00,833 → 00:03:08,833
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** manifest sql_path

## 16b_sql_role_dest — SQL File

- **Elemento:** SQL + destino
- **Spotlight target:** SQL + destino
- **Spotlight coords (norm):** `0.13,0.22,0.97,0.50`
- **Overlay opacity:** 168/255
- **Diálogo:** SQL + destino — Source e Destination decidem como entregar o resultado.
- **Typing:** 00:03:09,133 → 00:03:10,133 (1.00s)
- **Seta vermelha:** 00:03:10,133
- **Início/fim:** 00:03:09,133 → 00:03:17,133
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** LEGAL_CELLS

## 17_email — Notificação

- **Elemento:** Email (notifications)
- **Spotlight target:** Email (notifications)
- **Spotlight coords (norm):** `0.16,0.70,0.98,0.82`
- **Overlay opacity:** 168/255
- **Diálogo:** Email (notifications) — Recebe aviso quando o job terminar. / Deixe em branco se não quiser.
- **Typing:** 00:03:17,433 → 00:03:18,700 (1.27s)
- **Seta vermelha:** 00:03:18,700
- **Início/fim:** 00:03:17,433 → 00:03:25,433
- **Duração total:** 8.00s
- **Ação após a cena:** clique após a cena
- **Evidência:** #email

## 18_subject — Notificação

- **Elemento:** Subject (email)
- **Spotlight target:** Subject (email)
- **Spotlight coords (norm):** `0.16,0.76,0.98,0.88`
- **Overlay opacity:** 168/255
- **Diálogo:** Subject (email) — Assunto do e-mail de notificação. / Use um texto curto que identifique o job.
- **Typing:** 00:03:26,667 → 00:03:27,967 (1.30s)
- **Seta vermelha:** 00:03:27,967
- **Início/fim:** 00:03:26,667 → 00:03:34,667
- **Duração total:** 8.00s
- **Ação após a cena:** clique após a cena
- **Evidência:** #subject

## 19_status_bar — Status

- **Elemento:** Status do formulário
- **Spotlight target:** Status do formulário
- **Spotlight coords (norm):** `0.42,0.84,0.98,0.92`
- **Overlay opacity:** 168/255
- **Diálogo:** Status do formulário — Ready to launch = sem problemas bloqueantes.
- **Typing:** 00:03:35,900 → 00:03:36,900 (1.00s)
- **Seta vermelha:** 00:03:36,900
- **Início/fim:** 00:03:35,900 → 00:03:43,900
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** validation-summary

## 19b_actions — Status

- **Elemento:** Preview SQL e Launch
- **Spotlight target:** Preview SQL e Launch
- **Spotlight coords (norm):** `0.58,0.84,0.98,0.92`
- **Overlay opacity:** 168/255
- **Diálogo:** Preview SQL e Launch — Ficam na barra inferior para revisão e envio.
- **Typing:** 00:03:44,200 → 00:03:45,200 (1.00s)
- **Seta vermelha:** 00:03:45,200
- **Início/fim:** 00:03:44,200 → 00:03:52,200
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** action bar

## 20_mj_intro — MonthlyJob

- **Elemento:** MonthlyJob
- **Spotlight target:** MonthlyJob
- **Spotlight coords (norm):** `0.16,0.26,0.56,0.46`
- **Overlay opacity:** 168/255
- **Diálogo:** MonthlyJob — Use para cobrir um intervalo de datas, / executando o período mês a mês.
- **Typing:** 00:03:52,500 → 00:03:53,667 (1.17s)
- **Seta vermelha:** 00:03:53,667
- **Início/fim:** 00:03:52,500 → 00:04:00,500
- **Duração total:** 8.00s
- **Ação após a cena:** clique após a cena
- **Evidência:** SqlTemplate labeled MonthlyJob

## 21_mj_dest — MonthlyJob

- **Elemento:** MonthlyJob → Destination
- **Spotlight target:** MonthlyJob → Destination
- **Spotlight coords (norm):** `0.14,0.18,0.90,0.42`
- **Overlay opacity:** 168/255
- **Diálogo:** MonthlyJob → Destination — Com MonthlyJob, o destino permitido é só Table.
- **Typing:** 00:04:01,733 → 00:04:02,767 (1.03s)
- **Seta vermelha:** 00:04:02,767
- **Início/fim:** 00:04:01,733 → 00:04:09,733
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** LEGAL SqlTemplate/Table

## 21b_mj_dest_blocked — MonthlyJob

- **Elemento:** Csv e Table+Csv
- **Spotlight target:** Csv e Table+Csv
- **Spotlight coords (norm):** `0.50,0.24,0.90,0.44`
- **Overlay opacity:** 168/255
- **Diálogo:** Csv e Table+Csv — Ficam indisponíveis neste modo.
- **Typing:** 00:04:10,033 → 00:04:11,033 (1.00s)
- **Seta vermelha:** 00:04:11,033
- **Início/fim:** 00:04:10,033 → 00:04:18,033
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** dest hint

## 22_mj_sql_rule_a — MonthlyJob SQL

- **Elemento:** SQL no MonthlyJob — regra
- **Spotlight target:** SQL no MonthlyJob — regra
- **Spotlight coords (norm):** `0.10,0.14,0.90,0.72`
- **Overlay opacity:** 168/255
- **Diálogo:** SQL no MonthlyJob — regra — O .sql precisa conter os dois marcadores: / {date_inicio} e {date_fim}
- **Typing:** 00:04:18,033 → 00:04:19,367 (1.33s)
- **Seta vermelha:** 00:04:19,367
- **Início/fim:** 00:04:18,033 → 00:04:26,033
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** dispatch/sql.py:DATE_INICIO_TOKEN/DATE_FIM_TOKEN, detect_source, template_is_complete, is_malformed_template, monthly_preview; dispatch/screens/new_job.py:_sql_content_issues (requires both tokens for SqlTemplate/MonthlyJob); scr/monthly_query_processor.py:render_monthly_sql; CONTEXT.md (SqlTemplate placeholders); tests/test_monthly_query_processor.py, tools/prod_tui/job_specs.py SMOKE_TEMPLATE_SQL

## 23_mj_sql_rule_b — MonthlyJob SQL

- **Elemento:** Como conferir no arquivo
- **Spotlight target:** Como conferir no arquivo
- **Spotlight coords (norm):** `0.10,0.14,0.90,0.72`
- **Overlay opacity:** 168/255
- **Diálogo:** Como conferir no arquivo — Abra o .sql e busque exatamente / {date_inicio} e {date_fim}.
- **Typing:** 00:04:26,033 → 00:04:27,233 (1.20s)
- **Seta vermelha:** 00:04:27,233
- **Início/fim:** 00:04:26,033 → 00:04:34,033
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** _sql_content_issues

## 23b_mj_sql_missing — MonthlyJob SQL

- **Elemento:** Se faltar um marcador
- **Spotlight target:** Se faltar um marcador
- **Spotlight coords (norm):** `0.10,0.14,0.90,0.72`
- **Overlay opacity:** 168/255
- **Diálogo:** Se faltar um marcador — O job não pode ser iniciado como MonthlyJob.
- **Typing:** 00:04:34,033 → 00:04:35,033 (1.00s)
- **Seta vermelha:** 00:04:35,033
- **Início/fim:** 00:04:34,033 → 00:04:42,033
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** is_malformed_template

## 24_mj_sql_rule_c — MonthlyJob SQL

- **Elemento:** O que os marcadores fazem
- **Spotlight target:** O que os marcadores fazem
- **Spotlight coords (norm):** `0.10,0.14,0.90,0.72`
- **Overlay opacity:** 168/255
- **Diálogo:** O que os marcadores fazem — Reservam início e fim de cada mês do período.
- **Typing:** 00:04:42,033 → 00:04:43,033 (1.00s)
- **Seta vermelha:** 00:04:43,033
- **Início/fim:** 00:04:42,033 → 00:04:50,033
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** render_monthly_sql

## 24b_mj_sql_fill — MonthlyJob SQL

- **Elemento:** Preenchimento das datas
- **Spotlight target:** Preenchimento das datas
- **Spotlight coords (norm):** `0.10,0.14,0.90,0.72`
- **Overlay opacity:** 168/255
- **Diálogo:** Preenchimento das datas — O Dispatch preenche conforme Start Date e End Date.
- **Typing:** 00:04:50,033 → 00:04:51,100 (1.07s)
- **Seta vermelha:** 00:04:51,100
- **Início/fim:** 00:04:50,033 → 00:04:58,033
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** monthly_preview

## 25_mj_picker — MonthlyJob SQL

- **Elemento:** SQL do MonthlyJob
- **Spotlight target:** SQL do MonthlyJob
- **Spotlight coords (norm):** `0.13,0.42,0.97,0.70`
- **Overlay opacity:** 168/255
- **Diálogo:** SQL do MonthlyJob — Na lista, escolha Detected = MonthlyJob.
- **Typing:** 00:04:58,333 → 00:04:59,333 (1.00s)
- **Seta vermelha:** 00:04:59,333
- **Início/fim:** 00:04:58,333 → 00:05:06,333
- **Duração total:** 8.00s
- **Ação após a cena:** clique após a cena
- **Evidência:** detect_source

## 25b_mj_picker_confirm — MonthlyJob SQL

- **Elemento:** Detected = MonthlyJob
- **Spotlight target:** Detected = MonthlyJob
- **Spotlight coords (norm):** `0.13,0.42,0.97,0.70`
- **Overlay opacity:** 168/255
- **Diálogo:** Detected = MonthlyJob — Confirma que os dois marcadores foram encontrados.
- **Typing:** 00:05:07,567 → 00:05:08,600 (1.03s)
- **Seta vermelha:** 00:05:08,600
- **Início/fim:** 00:05:07,567 → 00:05:15,567
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** picker Detected

## 26_mj_schema — MonthlyJob campos

- **Elemento:** Schema (MonthlyJob)
- **Spotlight target:** Schema (MonthlyJob)
- **Spotlight coords (norm):** `0.18,0.60,0.98,0.72`
- **Overlay opacity:** 168/255
- **Diálogo:** Schema (MonthlyJob) — Schema da tabela de resultado. / Informe o schema correto do seu trabalho.
- **Typing:** 00:05:15,867 → 00:05:17,167 (1.30s)
- **Seta vermelha:** 00:05:17,167
- **Início/fim:** 00:05:15,867 → 00:05:23,867
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** #schema

## 27_mj_table — MonthlyJob campos

- **Elemento:** Table Name (MonthlyJob)
- **Spotlight target:** Table Name (MonthlyJob)
- **Spotlight coords (norm):** `0.18,0.66,0.98,0.78`
- **Overlay opacity:** 168/255
- **Diálogo:** Table Name (MonthlyJob) — Nome da tabela com o prefixo do usuário.
- **Typing:** 00:05:24,167 → 00:05:25,167 (1.00s)
- **Seta vermelha:** 00:05:25,167
- **Início/fim:** 00:05:24,167 → 00:05:32,167
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** #table-name-prefix

## 27b_mj_table_suffix — MonthlyJob campos

- **Elemento:** Sufixo da tabela
- **Spotlight target:** Sufixo da tabela
- **Spotlight coords (norm):** `0.18,0.66,0.98,0.78`
- **Overlay opacity:** 168/255
- **Diálogo:** Sufixo da tabela — Complete só o sufixo; o prefixo já vem preenchido.
- **Typing:** 00:05:32,467 → 00:05:33,467 (1.00s)
- **Seta vermelha:** 00:05:33,467
- **Início/fim:** 00:05:32,467 → 00:05:40,467
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** #table-name-suffix

## 28_mj_start — MonthlyJob campos

- **Elemento:** Start Date
- **Spotlight target:** Start Date
- **Spotlight coords (norm):** `0.18,0.72,0.98,0.84`
- **Overlay opacity:** 168/255
- **Diálogo:** Start Date — Data inicial (AAAA-MM-DD). / Define o primeiro mês a processar.
- **Typing:** 00:05:40,767 → 00:05:41,800 (1.03s)
- **Seta vermelha:** 00:05:41,800
- **Início/fim:** 00:05:40,767 → 00:05:48,767
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** #start-date

## 29_mj_end — MonthlyJob campos

- **Elemento:** End Date
- **Spotlight target:** End Date
- **Spotlight coords (norm):** `0.18,0.78,0.98,0.90`
- **Overlay opacity:** 168/255
- **Diálogo:** End Date — Data final (AAAA-MM-DD). / Deve ser igual ou posterior à Start Date.
- **Typing:** 00:05:49,067 → 00:05:50,133 (1.07s)
- **Seta vermelha:** 00:05:50,133
- **Início/fim:** 00:05:49,067 → 00:05:57,067
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** #end-date

## 30_et_intro — ExistingTable

- **Elemento:** ExistingTable
- **Spotlight target:** ExistingTable
- **Spotlight coords (norm):** `0.16,0.26,0.56,0.46`
- **Overlay opacity:** 168/255
- **Diálogo:** ExistingTable — Use quando os dados já estão em uma tabela / e você quer exportá-los sem .sql.
- **Typing:** 00:05:57,367 → 00:05:58,667 (1.30s)
- **Seta vermelha:** 00:05:58,667
- **Início/fim:** 00:05:57,367 → 00:06:05,367
- **Duração total:** 8.00s
- **Ação após a cena:** clique após a cena
- **Evidência:** src-existingtable

## 31_et_dest — ExistingTable

- **Elemento:** ExistingTable → Destination
- **Spotlight target:** ExistingTable → Destination
- **Spotlight coords (norm):** `0.14,0.18,0.90,0.42`
- **Overlay opacity:** 168/255
- **Diálogo:** ExistingTable → Destination — Neste modo o destino permitido é apenas Csv.
- **Typing:** 00:06:06,600 → 00:06:07,633 (1.03s)
- **Seta vermelha:** 00:06:07,633
- **Início/fim:** 00:06:06,600 → 00:06:14,600
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** LEGAL ExistingTable/Csv

## 31b_et_dest_blocked — ExistingTable

- **Elemento:** Table e Table+Csv
- **Spotlight target:** Table e Table+Csv
- **Spotlight coords (norm):** `0.50,0.24,0.90,0.44`
- **Overlay opacity:** 168/255
- **Diálogo:** Table e Table+Csv — Ficam indisponíveis com ExistingTable.
- **Typing:** 00:06:14,900 → 00:06:15,900 (1.00s)
- **Seta vermelha:** 00:06:15,900
- **Início/fim:** 00:06:14,900 → 00:06:22,900
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** dest hint

## 32_et_no_sql — ExistingTable

- **Elemento:** Sem SQL File
- **Spotlight target:** Sem SQL File
- **Spotlight coords (norm):** `0.10,0.28,0.90,0.56`
- **Overlay opacity:** 168/255
- **Diálogo:** Sem SQL File — A lista e o campo SQL File ficam ocultos. / A origem é a tabela existente.
- **Typing:** 00:06:23,200 → 00:06:24,400 (1.20s)
- **Seta vermelha:** 00:06:24,400
- **Início/fim:** 00:06:23,200 → 00:06:31,200
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** picker display=False

## 33_et_schema_coe — ExistingTable Schema

- **Elemento:** Schema → coe_enc
- **Spotlight target:** Schema → coe_enc
- **Spotlight coords (norm):** `0.20,0.58,0.76,0.74`
- **Overlay opacity:** 168/255
- **Diálogo:** Schema → coe_enc — Seleciona o schema coe_enc da tabela existente.
- **Typing:** 00:06:31,500 → 00:06:32,500 (1.00s)
- **Seta vermelha:** 00:06:32,500
- **Início/fim:** 00:06:31,500 → 00:06:39,500
- **Duração total:** 8.00s
- **Ação após a cena:** clique após a cena
- **Evidência:** esc-coe-enc

## 34_et_schema_aa — ExistingTable Schema

- **Elemento:** Schema → aa_enc
- **Spotlight target:** Schema → aa_enc
- **Spotlight coords (norm):** `0.27,0.58,0.83,0.74`
- **Overlay opacity:** 168/255
- **Diálogo:** Schema → aa_enc — Seleciona o schema aa_enc. / É a opção padrão nesse schema.
- **Typing:** 00:06:40,733 → 00:06:41,767 (1.03s)
- **Seta vermelha:** 00:06:41,767
- **Início/fim:** 00:06:40,733 → 00:06:48,733
- **Duração total:** 8.00s
- **Ação após a cena:** clique após a cena
- **Evidência:** esc-aa-enc

## 35_et_schema_other — ExistingTable Schema

- **Elemento:** Schema → other
- **Spotlight target:** Schema → other
- **Spotlight coords (norm):** `0.34,0.58,0.90,0.74`
- **Overlay opacity:** 168/255
- **Diálogo:** Schema → other — Use quando o schema não é coe_enc nem aa_enc.
- **Typing:** 00:06:49,967 → 00:06:50,967 (1.00s)
- **Seta vermelha:** 00:06:50,967
- **Início/fim:** 00:06:49,967 → 00:06:57,967
- **Duração total:** 8.00s
- **Ação após a cena:** clique após a cena
- **Evidência:** esc-other

## 35b_et_other_field — ExistingTable Schema

- **Elemento:** other → Custom Schema
- **Spotlight target:** other → Custom Schema
- **Spotlight coords (norm):** `0.18,0.62,0.98,0.78`
- **Overlay opacity:** 168/255
- **Diálogo:** other → Custom Schema — Ao marcar other, aparece o campo Custom Schema.
- **Typing:** 00:06:59,200 → 00:07:00,200 (1.00s)
- **Seta vermelha:** 00:07:00,200
- **Início/fim:** 00:06:59,200 → 00:07:07,200
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** #existing-schema-custom

## 36_et_custom — ExistingTable Schema

- **Elemento:** Custom Schema
- **Spotlight target:** Custom Schema
- **Spotlight coords (norm):** `0.18,0.66,0.98,0.78`
- **Overlay opacity:** 168/255
- **Diálogo:** Custom Schema — Digite o nome do schema personalizado. / Só aparece com Schema = other.
- **Typing:** 00:07:07,500 → 00:07:08,700 (1.20s)
- **Seta vermelha:** 00:07:08,700
- **Início/fim:** 00:07:07,500 → 00:07:15,500
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** row-existing-schema-custom

## 37_et_table — ExistingTable

- **Elemento:** Existing Table
- **Spotlight target:** Existing Table
- **Spotlight coords (norm):** `0.18,0.70,0.98,0.82`
- **Overlay opacity:** 168/255
- **Diálogo:** Existing Table — Informe só o nome da tabela (sem o schema).
- **Typing:** 00:07:15,800 → 00:07:16,800 (1.00s)
- **Seta vermelha:** 00:07:16,800
- **Início/fim:** 00:07:15,800 → 00:07:23,800
- **Duração total:** 8.00s
- **Ação após a cena:** clique após a cena
- **Evidência:** #existing-table

## 37b_et_full — ExistingTable

- **Elemento:** Origem completa
- **Spotlight target:** Origem completa
- **Spotlight coords (norm):** `0.18,0.70,0.98,0.82`
- **Overlay opacity:** 168/255
- **Diálogo:** Origem completa — Com o schema, forma schema.tabela.
- **Typing:** 00:07:25,033 → 00:07:26,033 (1.00s)
- **Seta vermelha:** 00:07:26,033
- **Início/fim:** 00:07:25,033 → 00:07:33,033
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** validate_full_table

## 38_rel_standard — Relações

- **Elemento:** Combinação comum
- **Spotlight target:** Combinação comum
- **Spotlight coords (norm):** `0.08,0.12,0.92,0.56`
- **Overlay opacity:** 168/255
- **Diálogo:** Combinação comum — SqlFile + Csv + .sql sem marcadores de data.
- **Typing:** 00:07:33,333 → 00:07:34,333 (1.00s)
- **Seta vermelha:** 00:07:34,333
- **Início/fim:** 00:07:33,333 → 00:07:41,333
- **Duração total:** 8.00s
- **Ação após a cena:** clique após a cena
- **Evidência:** LEGAL SqlFile/Csv

## 38b_rel_standard_use — Relações

- **Elemento:** Fluxo típico
- **Spotlight target:** Fluxo típico
- **Spotlight coords (norm):** `0.08,0.12,0.92,0.56`
- **Overlay opacity:** 168/255
- **Diálogo:** Fluxo típico — Gera um CSV a partir de uma consulta.
- **Typing:** 00:07:42,567 → 00:07:43,567 (1.00s)
- **Seta vermelha:** 00:07:43,567
- **Início/fim:** 00:07:42,567 → 00:07:50,567
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** detect_source

## 39_rel_monthly — Relações

- **Elemento:** Combinação MonthlyJob
- **Spotlight target:** Combinação MonthlyJob
- **Spotlight coords (norm):** `0.08,0.10,0.92,0.66`
- **Overlay opacity:** 168/255
- **Diálogo:** Combinação MonthlyJob — MonthlyJob + Table + .sql com / {date_inicio} e {date_fim}.
- **Typing:** 00:07:50,867 → 00:07:52,000 (1.13s)
- **Seta vermelha:** 00:07:52,000
- **Início/fim:** 00:07:50,867 → 00:07:58,867
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** LEGAL SqlTemplate/Table

## 39b_rel_monthly_fields — Relações

- **Elemento:** Campos do MonthlyJob
- **Spotlight target:** Campos do MonthlyJob
- **Spotlight coords (norm):** `0.15,0.54,0.95,0.86`
- **Overlay opacity:** 168/255
- **Diálogo:** Campos do MonthlyJob — Também: Schema, Table Name, Start Date e End Date.
- **Typing:** 00:07:59,167 → 00:08:00,167 (1.00s)
- **Seta vermelha:** 00:08:00,167
- **Início/fim:** 00:07:59,167 → 00:08:07,167
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** date fields

## 40_rel_existing — Relações

- **Elemento:** Combinação ExistingTable
- **Spotlight target:** Combinação ExistingTable
- **Spotlight coords (norm):** `0.08,0.12,0.92,0.60`
- **Overlay opacity:** 168/255
- **Diálogo:** Combinação ExistingTable — ExistingTable + Csv + Schema + Existing Table.
- **Typing:** 00:08:07,467 → 00:08:08,467 (1.00s)
- **Seta vermelha:** 00:08:08,467
- **Início/fim:** 00:08:07,467 → 00:08:15,467
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** ExistingTable flow

## 40b_rel_existing_no_sql — Relações

- **Elemento:** Sem SQL neste modo
- **Spotlight target:** Sem SQL neste modo
- **Spotlight coords (norm):** `0.08,0.12,0.92,0.60`
- **Overlay opacity:** 168/255
- **Diálogo:** Sem SQL neste modo — Não usa SQL File nem MonthlyJob ao mesmo tempo.
- **Typing:** 00:08:15,767 → 00:08:16,767 (1.00s)
- **Seta vermelha:** 00:08:16,767
- **Início/fim:** 00:08:15,767 → 00:08:23,767
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** source exclusive

## 41_rel_incompat — Relações

- **Elemento:** Combinações indisponíveis
- **Spotlight target:** Combinações indisponíveis
- **Spotlight coords (norm):** `0.10,0.04,0.94,0.32`
- **Overlay opacity:** 168/255
- **Diálogo:** Combinações indisponíveis — MonthlyJob não aceita Csv ou Table+Csv.
- **Typing:** 00:08:24,067 → 00:08:25,067 (1.00s)
- **Seta vermelha:** 00:08:25,067
- **Início/fim:** 00:08:24,067 → 00:08:32,067
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** LEGAL_CELLS

## 41b_rel_incompat_et — Relações

- **Elemento:** ExistingTable — limite
- **Spotlight target:** ExistingTable — limite
- **Spotlight coords (norm):** `0.10,0.04,0.94,0.32`
- **Overlay opacity:** 168/255
- **Diálogo:** ExistingTable — limite — ExistingTable não aceita Table ou Table+Csv.
- **Typing:** 00:08:32,367 → 00:08:33,367 (1.00s)
- **Seta vermelha:** 00:08:33,367
- **Início/fim:** 00:08:32,367 → 00:08:40,367
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** LEGAL_CELLS

## 42_val_bad — Validação

- **Elemento:** E-mail inválido
- **Spotlight target:** E-mail inválido
- **Spotlight coords (norm):** `0.18,0.68,0.98,0.84`
- **Overlay opacity:** 168/255
- **Diálogo:** E-mail inválido — Se o formato estiver errado, o status mostra o problema.
- **Typing:** 00:08:40,667 → 00:08:41,700 (1.03s)
- **Seta vermelha:** 00:08:41,700
- **Início/fim:** 00:08:40,667 → 00:08:48,667
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** Invalid email

## 43_val_ok — Validação

- **Elemento:** Formulário pronto
- **Spotlight target:** Formulário pronto
- **Spotlight coords (norm):** `0.42,0.84,0.98,0.92`
- **Overlay opacity:** 168/255
- **Diálogo:** Formulário pronto — Com os dados corrigidos, volta Ready to launch.
- **Typing:** 00:08:48,967 → 00:08:49,967 (1.00s)
- **Seta vermelha:** 00:08:49,967
- **Início/fim:** 00:08:48,967 → 00:08:56,967
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** Ready to launch

## 43b_val_review — Validação

- **Elemento:** Revise antes de enviar
- **Spotlight target:** Revise antes de enviar
- **Spotlight coords (norm):** `0.08,0.18,0.92,0.62`
- **Overlay opacity:** 168/255
- **Diálogo:** Revise antes de enviar — Confira origem, destino, arquivo e fila.
- **Typing:** 00:08:57,267 → 00:08:58,267 (1.00s)
- **Seta vermelha:** 00:08:58,267
- **Início/fim:** 00:08:57,267 → 00:09:05,267
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** form review

## 44_preview — Preview

- **Elemento:** Preview SQL
- **Spotlight target:** Preview SQL
- **Spotlight coords (norm):** `0.30,0.20,0.94,0.76`
- **Overlay opacity:** 168/255
- **Diálogo:** Preview SQL — Mostra o conteúdo que será usado no job.
- **Typing:** 00:09:05,567 → 00:09:06,567 (1.00s)
- **Seta vermelha:** 00:09:06,567
- **Início/fim:** 00:09:05,567 → 00:09:13,567
- **Duração total:** 8.00s
- **Ação após a cena:** clique após a cena
- **Evidência:** Preview SQL [P]

## 44b_preview_check — Preview

- **Elemento:** O que conferir no Preview
- **Spotlight target:** O que conferir no Preview
- **Spotlight coords (norm):** `0.15,0.17,0.95,0.73`
- **Overlay opacity:** 168/255
- **Diálogo:** O que conferir no Preview — Confira a consulta e o destino antes do envio.
- **Typing:** 00:09:14,800 → 00:09:15,833 (1.03s)
- **Seta vermelha:** 00:09:15,833
- **Início/fim:** 00:09:14,800 → 00:09:22,800
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** preview screen

## 45_checklist — Revisão

- **Elemento:** Antes de iniciar, confirme
- **Spotlight target:** Antes de iniciar, confirme
- **Spotlight coords (norm):** `0.10,0.14,0.90,0.72`
- **Overlay opacity:** 168/255
- **Diálogo:** Antes de iniciar, confirme — Origem, destino, arquivo ou tabela, / e fila de execução.
- **Typing:** 00:09:22,800 → 00:09:23,967 (1.17s)
- **Seta vermelha:** 00:09:23,967
- **Início/fim:** 00:09:22,800 → 00:09:30,800
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** checklist

## 45b_checklist_b — Revisão

- **Elemento:** Também confira
- **Spotlight target:** Também confira
- **Spotlight coords (norm):** `0.10,0.14,0.90,0.72`
- **Overlay opacity:** 168/255
- **Diálogo:** Também confira — Opções adicionais e e-mail de notificação.
- **Typing:** 00:09:30,800 → 00:09:31,800 (1.00s)
- **Seta vermelha:** 00:09:31,800
- **Início/fim:** 00:09:30,800 → 00:09:38,800
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** checklist

## 46_confirm — Envio

- **Elemento:** Launch Job
- **Spotlight target:** Launch Job
- **Spotlight coords (norm):** `0.14,0.27,0.86,0.83`
- **Overlay opacity:** 168/255
- **Diálogo:** Launch Job — Inicia o job com as configurações revisadas.
- **Typing:** 00:09:39,100 → 00:09:40,100 (1.00s)
- **Seta vermelha:** 00:09:40,100
- **Início/fim:** 00:09:39,100 → 00:09:47,100
- **Duração total:** 8.00s
- **Ação após a cena:** clique após a cena
- **Evidência:** ConfirmScreen

## 46b_confirm_read — Envio

- **Elemento:** Confirme só se estiver correto
- **Spotlight target:** Confirme só se estiver correto
- **Spotlight coords (norm):** `0.14,0.27,0.86,0.83`
- **Overlay opacity:** 168/255
- **Diálogo:** Confirme só se estiver correto — Leia o resumo antes de confirmar o envio.
- **Typing:** 00:09:48,333 → 00:09:49,367 (1.03s)
- **Seta vermelha:** 00:09:49,367
- **Início/fim:** 00:09:48,333 → 00:09:56,333
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** Launch Job

## 47_launched — Envio

- **Elemento:** Job enviado
- **Spotlight target:** Job enviado
- **Spotlight coords (norm):** `0.15,0.52,0.95,0.88`
- **Overlay opacity:** 168/255
- **Diálogo:** Job enviado — O job foi enviado pelo Dispatch. / Acompanhe na tela de monitoramento.
- **Typing:** 00:09:56,633 → 00:09:57,767 (1.13s)
- **Seta vermelha:** 00:09:57,767
- **Início/fim:** 00:09:56,633 → 00:10:04,633
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** Launched Job

## 48_overview — Overview

- **Elemento:** Overview
- **Spotlight target:** Overview
- **Spotlight coords (norm):** `0.02,0.06,0.28,0.38`
- **Overlay opacity:** 168/255
- **Diálogo:** Overview — Após o envio, acompanhe o status no Overview.
- **Typing:** 00:10:04,933 → 00:10:05,933 (1.00s)
- **Seta vermelha:** 00:10:05,933
- **Início/fim:** 00:10:04,933 → 00:10:12,933
- **Duração total:** 8.00s
- **Ação após a cena:** clique após a cena
- **Evidência:** DashboardScreen

## 49_close — Encerramento

- **Elemento:** Resumo
- **Spotlight target:** Resumo
- **Spotlight coords (norm):** `0.10,0.14,0.90,0.72`
- **Overlay opacity:** 168/255
- **Diálogo:** Resumo — Na aba New Job você define, revisa e inicia o job.
- **Typing:** 00:10:13,867 → 00:10:14,867 (1.00s)
- **Seta vermelha:** 00:10:14,867
- **Início/fim:** 00:10:13,867 → 00:10:21,867
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** closing

## 49b_close_b — Encerramento

- **Elemento:** Depois do envio
- **Spotlight target:** Depois do envio
- **Spotlight coords (norm):** `0.10,0.14,0.90,0.72`
- **Overlay opacity:** 168/255
- **Diálogo:** Depois do envio — Acompanhe o resultado no Overview. / Revise os campos antes de Launch Job.
- **Typing:** 00:10:21,867 → 00:10:23,133 (1.27s)
- **Seta vermelha:** 00:10:23,133
- **Início/fim:** 00:10:21,867 → 00:10:29,867
- **Duração total:** 8.00s
- **Ação após a cena:** avançar para a próxima cena
- **Evidência:** closing
