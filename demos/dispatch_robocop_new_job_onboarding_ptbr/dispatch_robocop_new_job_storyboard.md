# Storyboard — New Job (silencioso, pt-BR, 10–12s + typing + spotlight)

Sem narração e sem música. Sem seção “Antes de começar”.
Cada cena instrucional: revelação caractere a caractere + leitura estática; duração total 10s (ou 12s se o texto for mais longo).

## 01_open — Abertura

- **Elemento:** Dispatch (Robocop)
- **Capture:** `card:open`
- **Spotlight:** `0.08,0.12,0.92,0.78`
- **Cursor:** move → stop em (0.5, 0.5)
- **Footer:** Dispatch (Robocop) — Como utilizar a aba New Job / Configure e inicie um novo job passo a passo.
- **Badge:** —
- **Text anim:** 00:00:00,000 → 00:00:01,667 (1.67s)
- **Scene end:** 00:00:10,000
- **Total scene:** 10.00s (static after anim: 8.33s)
- **Resultado esperado:** analista entende decisão em “Dispatch (Robocop)”
- **Evidência de verificação:** opening card

## 02_purpose_a — Propósito

- **Elemento:** Para que serve a aba New Job
- **Capture:** `arrive`
- **Spotlight:** `0.02,0.02,0.98,0.30`
- **Cursor:** move → stop em (0.55, 0.12)
- **Footer:** Para que serve a aba New Job — Ela permite configurar e iniciar uma nova execução no Dispatch.
- **Badge:** —
- **Text anim:** 00:00:10,333 → 00:00:12,000 (1.67s)
- **Scene end:** 00:00:20,333
- **Total scene:** 10.00s (static after anim: 8.33s)
- **Resultado esperado:** analista entende decisão em “Para que serve a aba New Job”
- **Evidência de verificação:** NewJobScreen title + form

## 02_purpose_b — Propósito

- **Elemento:** O que você decide aqui
- **Capture:** `arrive`
- **Spotlight:** `0.02,0.02,0.98,0.38`
- **Cursor:** move → stop em (0.55, 0.2)
- **Footer:** O que você decide aqui — Você escolhe a origem dos dados, o destino do resultado, / a consulta e as opções de execução do job.
- **Badge:** —
- **Text anim:** 00:00:20,667 → 00:00:22,900 (2.23s)
- **Scene end:** 00:00:30,667
- **Total scene:** 10.00s (static after anim: 7.77s)
- **Resultado esperado:** analista entende decisão em “O que você decide aqui”
- **Evidência de verificação:** NewJobScreen compose()

## 03_matrix — Matriz

- **Elemento:** Source × Destination
- **Capture:** `matrix`
- **Spotlight:** `0.07,0.04,0.97,0.28`
- **Cursor:** move → stop em (0.52, 0.18) → clique após leitura
- **Footer:** Source × Destination — Tabela de referência com as combinações permitidas. / Consulte-a antes de escolher origem e destino.
- **Badge:** Opcional
- **Text anim:** 00:00:31,000 → 00:00:33,167 (2.17s)
- **Scene end:** 00:00:41,000
- **Total scene:** 10.00s (static after anim: 7.83s)
- **Resultado esperado:** analista entende decisão em “Source × Destination”
- **Evidência de verificação:** matrix-collapsible + LEGAL_CELLS

## 04_detected — Detecção

- **Elemento:** Detected source
- **Capture:** `arrive`
- **Spotlight:** `0.12,0.20,0.92,0.32`
- **Cursor:** move → stop em (0.55, 0.28)
- **Footer:** Detected source — Mostra o tipo identificado no arquivo SQL selecionado. / Confirme se corresponde ao job que você quer executar.
- **Badge:** —
- **Text anim:** 00:00:42,467 → 00:00:44,733 (2.27s)
- **Scene end:** 00:00:52,467
- **Total scene:** 10.00s (static after anim: 7.73s)
- **Resultado esperado:** analista entende decisão em “Detected source”
- **Evidência de verificação:** info-detected + sql.detect_source

## 05_source_intro — Source

- **Elemento:** Source
- **Capture:** `source_sqlfile`
- **Spotlight:** `0.18,0.22,0.54,0.42`
- **Cursor:** move → stop em (0.38, 0.34)
- **Footer:** Source — Define de onde os dados do job serão obtidos. / É a primeira decisão do formulário.
- **Badge:** Obrigatório
- **Text anim:** 00:00:52,800 → 00:00:54,400 (1.60s)
- **Scene end:** 00:01:02,800
- **Total scene:** 10.00s (static after anim: 8.40s)
- **Resultado esperado:** analista entende decisão em “Source”
- **Evidência de verificação:** RadioSet #source

## 06_source_sqlfile — Source

- **Elemento:** Source → SqlFile
- **Capture:** `source_sqlfile`
- **Spotlight:** `0.18,0.22,0.54,0.42`
- **Cursor:** move → stop em (0.38, 0.34) → clique após leitura
- **Footer:** Source → SqlFile — Use quando a consulta está em um arquivo .sql simples. / O Dispatch executa essa consulta conforme o destino escolhido.
- **Badge:** Obrigatório
- **Text anim:** 00:01:03,133 → 00:01:05,567 (2.43s)
- **Scene end:** 00:01:15,133
- **Total scene:** 12.00s (static after anim: 9.57s)
- **Resultado esperado:** analista entende decisão em “Source → SqlFile”
- **Evidência de verificação:** src-sqlfile; LEGAL SqlFile→Table/Csv/Table+Csv

## 07_dest_intro — Destination

- **Elemento:** Destination
- **Capture:** `source_sqlfile`
- **Spotlight:** `0.52,0.20,0.88,0.40`
- **Cursor:** move → stop em (0.7, 0.28)
- **Footer:** Destination — Define onde o resultado do job será armazenado. / A escolha depende da origem selecionada.
- **Badge:** Obrigatório
- **Text anim:** 00:01:16,600 → 00:01:18,433 (1.83s)
- **Scene end:** 00:01:26,600
- **Total scene:** 10.00s (static after anim: 8.17s)
- **Resultado esperado:** analista entende decisão em “Destination”
- **Evidência de verificação:** RadioSet #destination

## 08_dest_table — Destination

- **Elemento:** Destination → Table
- **Capture:** `dest_table`
- **Spotlight:** `0.52,0.18,0.88,0.34`
- **Cursor:** move → stop em (0.7, 0.26) → clique após leitura
- **Footer:** Destination → Table — Salva o resultado em uma tabela. / Use quando precisar consultar o resultado depois no ambiente.
- **Badge:** Obrigatório
- **Text anim:** 00:01:26,933 → 00:01:29,000 (2.07s)
- **Scene end:** 00:01:36,933
- **Total scene:** 10.00s (static after anim: 7.93s)
- **Resultado esperado:** analista entende decisão em “Destination → Table”
- **Evidência de verificação:** dst-table

## 09_dest_csv — Destination

- **Elemento:** Destination → Csv
- **Capture:** `source_sqlfile`
- **Spotlight:** `0.52,0.22,0.88,0.38`
- **Cursor:** move → stop em (0.7, 0.3) → clique após leitura
- **Footer:** Destination → Csv — Gera um arquivo CSV na pasta de onde você abriu o Dispatch. / Use quando o resultado precisa ser baixado ou compartilhado como arquivo.
- **Badge:** Obrigatório
- **Text anim:** 00:01:38,400 → 00:01:41,133 (2.73s)
- **Scene end:** 00:01:50,400
- **Total scene:** 12.00s (static after anim: 9.27s)
- **Resultado esperado:** analista entende decisão em “Destination → Csv”
- **Evidência de verificação:** dst-csv; ADR-0003 CSV in launch cwd

## 10_dest_tablecsv — Destination

- **Elemento:** Destination → Table+Csv
- **Capture:** `dest_tablecsv`
- **Spotlight:** `0.52,0.26,0.88,0.42`
- **Cursor:** move → stop em (0.7, 0.34) → clique após leitura
- **Footer:** Destination → Table+Csv — Cria a tabela e também gera o CSV. / Use quando precisa dos dois formatos na mesma execução.
- **Badge:** Obrigatório
- **Text anim:** 00:01:51,867 → 00:01:53,933 (2.07s)
- **Scene end:** 00:02:01,867
- **Total scene:** 10.00s (static after anim: 7.93s)
- **Resultado esperado:** analista entende decisão em “Destination → Table+Csv”
- **Evidência de verificação:** dst-table-csv

## 11_queue_a — Fila

- **Elemento:** Execution Queue
- **Capture:** `queues`
- **Spotlight:** `0.17,0.34,0.93,0.62`
- **Cursor:** move → stop em (0.55, 0.5)
- **Footer:** Execution Queue — Indica a fila de processamento do job. / Sem marcação, o Dispatch escolhe automaticamente.
- **Badge:** Opcional
- **Text anim:** 00:02:03,333 → 00:02:05,233 (1.90s)
- **Scene end:** 00:02:13,333
- **Total scene:** 10.00s (static after anim: 8.10s)
- **Resultado esperado:** analista entende decisão em “Execution Queue”
- **Evidência de verificação:** SelectionList #queue + Auto hint

## 12_queue_b — Fila

- **Elemento:** Execution Queue — quando marcar
- **Capture:** `queues`
- **Spotlight:** `0.17,0.38,0.93,0.66`
- **Cursor:** move → stop em (0.55, 0.54) → clique após leitura
- **Footer:** Execution Queue — quando marcar — Marque uma ou mais filas só se o seu projeto indicar qual usar. / Várias filas são tentadas na ordem da lista.
- **Badge:** Opcional
- **Text anim:** 00:02:13,667 → 00:02:16,200 (2.53s)
- **Scene end:** 00:02:25,667
- **Total scene:** 12.00s (static after anim: 9.47s)
- **Resultado esperado:** analista entende decisão em “Execution Queue — quando marcar”
- **Evidência de verificação:** _QUEUE_CHOICES / _QUEUE_AUTO_HINT

## 13_sql_intro — SQL File

- **Elemento:** SQL File
- **Capture:** `picker`
- **Spotlight:** `0.13,0.44,0.97,0.72`
- **Cursor:** move → stop em (0.55, 0.62)
- **Footer:** SQL File — É a consulta que o job vai executar. / Para SqlFile e MonthlyJob, você precisa selecionar um arquivo .sql.
- **Badge:** Obrigatório
- **Text anim:** 00:02:27,133 → 00:02:29,200 (2.07s)
- **Scene end:** 00:02:37,133
- **Total scene:** 10.00s (static after anim: 7.93s)
- **Resultado esperado:** analista entende decisão em “SQL File”
- **Evidência de verificação:** row-sql-file + picker; required for SqlFile/SqlTemplate

## 14_sql_picker — SQL File

- **Elemento:** Lista de arquivos SQL
- **Capture:** `picker`
- **Spotlight:** `0.13,0.44,0.97,0.72`
- **Cursor:** move → stop em (0.55, 0.62) → clique após leitura
- **Footer:** Lista de arquivos SQL — Mostra os arquivos .sql da pasta atual. / Selecione o arquivo do job para preencher o caminho automaticamente.
- **Badge:** Obrigatório
- **Text anim:** 00:02:37,467 → 00:02:39,833 (2.37s)
- **Scene end:** 00:02:49,467
- **Total scene:** 12.00s (static after anim: 9.63s)
- **Resultado esperado:** analista entende decisão em “Lista de arquivos SQL”
- **Evidência de verificação:** sql-file-picker scans launch_cwd/*.sql

## 15_sql_verify — SQL File

- **Elemento:** O que conferir no arquivo
- **Capture:** `picker`
- **Spotlight:** `0.13,0.46,0.97,0.78`
- **Cursor:** move → stop em (0.58, 0.72)
- **Footer:** O que conferir no arquivo — Confirme o nome do arquivo e o tipo Detected na lista. / O caminho aparece no campo SQL File após a seleção.
- **Badge:** Obrigatório
- **Text anim:** 00:02:50,933 → 00:02:53,333 (2.40s)
- **Scene end:** 00:03:02,933
- **Total scene:** 12.00s (static after anim: 9.60s)
- **Resultado esperado:** analista entende decisão em “O que conferir no arquivo”
- **Evidência de verificação:** picker columns File/Detected/Modified + path-hint

## 16_sql_role — SQL File

- **Elemento:** Papel do SQL File no job
- **Capture:** `picker`
- **Spotlight:** `0.13,0.58,0.97,0.78`
- **Cursor:** move → stop em (0.58, 0.72)
- **Footer:** Papel do SQL File no job — Esse arquivo define quais dados serão lidos ou calculados. / Source e Destination decidem como o resultado será entregue.
- **Badge:** Obrigatório
- **Text anim:** 00:03:03,267 → 00:03:05,900 (2.63s)
- **Scene end:** 00:03:15,267
- **Total scene:** 12.00s (static after anim: 9.37s)
- **Resultado esperado:** analista entende decisão em “Papel do SQL File no job”
- **Evidência de verificação:** manifest source sql_path_at_launch

## 17_email — Notificação

- **Elemento:** Email (notifications)
- **Capture:** `email_ok`
- **Spotlight:** `0.16,0.70,0.98,0.82`
- **Cursor:** move → stop em (0.58, 0.78) → clique após leitura
- **Footer:** Email (notifications) — Recebe aviso quando o job terminar. / Deixe em branco se não quiser notificação.
- **Badge:** Opcional
- **Text anim:** 00:03:15,600 → 00:03:17,433 (1.83s)
- **Scene end:** 00:03:25,600
- **Total scene:** 10.00s (static after anim: 8.17s)
- **Resultado esperado:** analista entende decisão em “Email (notifications)”
- **Evidência de verificação:** #email; validation only if filled

## 18_subject — Notificação

- **Elemento:** Subject (email)
- **Capture:** `email_ok`
- **Spotlight:** `0.16,0.76,0.98,0.88`
- **Cursor:** move → stop em (0.58, 0.84) → clique após leitura
- **Footer:** Subject (email) — Assunto do e-mail de notificação. / Use um texto curto que identifique o job.
- **Badge:** Opcional
- **Text anim:** 00:03:27,067 → 00:03:28,733 (1.67s)
- **Scene end:** 00:03:37,067
- **Total scene:** 10.00s (static after anim: 8.33s)
- **Resultado esperado:** analista entende decisão em “Subject (email)”
- **Evidência de verificação:** #subject default Dispatch Job

## 19_status_bar — Status

- **Elemento:** Status do formulário
- **Capture:** `ready_review`
- **Spotlight:** `0.42,0.84,0.98,0.95`
- **Cursor:** move → stop em (0.72, 0.92)
- **Footer:** Status do formulário — Ready to launch indica que não há problemas bloqueantes. / Preview SQL e Launch ficam na barra inferior.
- **Badge:** —
- **Text anim:** 00:03:38,533 → 00:03:40,767 (2.23s)
- **Scene end:** 00:03:48,533
- **Total scene:** 10.00s (static after anim: 7.77s)
- **Resultado esperado:** analista entende decisão em “Status do formulário”
- **Evidência de verificação:** validation-summary + action bar

## 20_mj_intro — MonthlyJob

- **Elemento:** MonthlyJob
- **Capture:** `monthly`
- **Spotlight:** `0.16,0.26,0.56,0.46`
- **Cursor:** move → stop em (0.38, 0.38) → clique após leitura
- **Footer:** MonthlyJob — Use quando a consulta precisa cobrir um intervalo de datas, / executando o período mês a mês.
- **Badge:** Use apenas quando...
- **Text anim:** 00:03:48,867 → 00:03:50,733 (1.87s)
- **Scene end:** 00:03:58,867
- **Total scene:** 10.00s (static after anim: 8.13s)
- **Resultado esperado:** analista entende decisão em “MonthlyJob”
- **Evidência de verificação:** Source SqlTemplate labeled MonthlyJob; CONTEXT.md

## 21_mj_dest — MonthlyJob

- **Elemento:** MonthlyJob → Destination
- **Capture:** `monthly`
- **Spotlight:** `0.14,0.18,0.90,0.42`
- **Cursor:** move → stop em (0.7, 0.28)
- **Footer:** MonthlyJob → Destination — Com MonthlyJob, o destino permitido é apenas Table. / Csv e Table+Csv ficam indisponíveis.
- **Badge:** Obrigatório
- **Text anim:** 00:04:00,333 → 00:04:02,400 (2.07s)
- **Scene end:** 00:04:10,333
- **Total scene:** 10.00s (static after anim: 7.93s)
- **Resultado esperado:** analista entende decisão em “MonthlyJob → Destination”
- **Evidência de verificação:** LEGAL_CELLS (SqlTemplate, Table) only; dest hint

## 22_mj_sql_rule_a — MonthlyJob SQL

- **Elemento:** SQL File no MonthlyJob — regra
- **Capture:** `card:sql_tokens`
- **Spotlight:** `0.08,0.12,0.92,0.78`
- **Cursor:** move → stop em (0.5, 0.45)
- **Footer:** SQL File no MonthlyJob — regra — O arquivo .sql precisa conter os dois marcadores: / {date_inicio} e {date_fim}
- **Badge:** Obrigatório
- **Text anim:** 00:04:10,333 → 00:04:12,267 (1.93s)
- **Scene end:** 00:04:20,333
- **Total scene:** 10.00s (static after anim: 8.07s)
- **Resultado esperado:** analista entende decisão em “SQL File no MonthlyJob — regra”
- **Evidência de verificação:** dispatch/sql.py:DATE_INICIO_TOKEN/DATE_FIM_TOKEN, detect_source, template_is_complete, is_malformed_template, monthly_preview; dispatch/screens/new_job.py:_sql_content_issues (requires both tokens for SqlTemplate/MonthlyJob); scr/monthly_query_processor.py:render_monthly_sql; CONTEXT.md (SqlTemplate placeholders); tests/test_monthly_query_processor.py, tools/prod_tui/job_specs.py SMOKE_TEMPLATE_SQL

## 23_mj_sql_rule_b — MonthlyJob SQL

- **Elemento:** Como conferir no arquivo
- **Capture:** `card:sql_tokens`
- **Spotlight:** `0.08,0.12,0.92,0.78`
- **Cursor:** move → stop em (0.5, 0.5)
- **Footer:** Como conferir no arquivo — Abra o .sql e busque exatamente {date_inicio} e {date_fim}. / Se faltar um deles, o job não pode ser iniciado como MonthlyJob.
- **Badge:** Obrigatório
- **Text anim:** 00:04:20,333 → 00:04:23,033 (2.70s)
- **Scene end:** 00:04:32,333
- **Total scene:** 12.00s (static after anim: 9.30s)
- **Resultado esperado:** analista entende decisão em “Como conferir no arquivo”
- **Evidência de verificação:** new_job._sql_content_issues + is_malformed_template

## 24_mj_sql_rule_c — MonthlyJob SQL

- **Elemento:** O que esses marcadores fazem
- **Capture:** `card:sql_tokens`
- **Spotlight:** `0.08,0.12,0.92,0.78`
- **Cursor:** move → stop em (0.5, 0.55)
- **Footer:** O que esses marcadores fazem — Eles reservam o início e o fim de cada mês no período informado. / O Dispatch preenche as datas conforme Start Date e End Date.
- **Badge:** Obrigatório
- **Text anim:** 00:04:32,333 → 00:04:35,133 (2.80s)
- **Scene end:** 00:04:44,333
- **Total scene:** 12.00s (static after anim: 9.20s)
- **Resultado esperado:** analista entende decisão em “O que esses marcadores fazem”
- **Evidência de verificação:** monthly_preview / render_monthly_sql substitution

## 25_mj_picker — MonthlyJob SQL

- **Elemento:** Selecionar o SQL do MonthlyJob
- **Capture:** `monthly_picker`
- **Spotlight:** `0.13,0.42,0.97,0.70`
- **Cursor:** move → stop em (0.55, 0.6) → clique após leitura
- **Footer:** Selecionar o SQL do MonthlyJob — Na lista, escolha o arquivo com Detected = MonthlyJob. / Isso confirma que os dois marcadores foram encontrados.
- **Badge:** Obrigatório
- **Text anim:** 00:04:44,667 → 00:04:47,233 (2.57s)
- **Scene end:** 00:04:56,667
- **Total scene:** 12.00s (static after anim: 9.43s)
- **Resultado esperado:** analista entende decisão em “Selecionar o SQL do MonthlyJob”
- **Evidência de verificação:** picker Detected column via detect_source

## 26_mj_schema — MonthlyJob campos

- **Elemento:** Schema (MonthlyJob)
- **Capture:** `monthly_fields`
- **Spotlight:** `0.18,0.60,0.98,0.72`
- **Cursor:** move → stop em (0.58, 0.68)
- **Footer:** Schema (MonthlyJob) — Define o schema da tabela de resultado. / Informe o schema correto do seu trabalho.
- **Badge:** Obrigatório
- **Text anim:** 00:04:58,133 → 00:04:59,967 (1.83s)
- **Scene end:** 00:05:08,133
- **Total scene:** 10.00s (static after anim: 8.17s)
- **Resultado esperado:** analista entende decisão em “Schema (MonthlyJob)”
- **Evidência de verificação:** #schema visible when needs_table

## 27_mj_table — MonthlyJob campos

- **Elemento:** Table Name (MonthlyJob)
- **Capture:** `monthly_fields`
- **Spotlight:** `0.18,0.66,0.98,0.78`
- **Cursor:** move → stop em (0.58, 0.74)
- **Footer:** Table Name (MonthlyJob) — Nome da tabela de resultado, com o prefixo do seu usuário. / Complete apenas o sufixo; o prefixo já vem preenchido.
- **Badge:** Obrigatório
- **Text anim:** 00:05:08,467 → 00:05:10,967 (2.50s)
- **Scene end:** 00:05:20,467
- **Total scene:** 12.00s (static after anim: 9.50s)
- **Resultado esperado:** analista entende decisão em “Table Name (MonthlyJob)”
- **Evidência de verificação:** #table-name-prefix + #table-name-suffix

## 28_mj_start — MonthlyJob campos

- **Elemento:** Start Date
- **Capture:** `monthly_fields`
- **Spotlight:** `0.18,0.72,0.98,0.84`
- **Cursor:** move → stop em (0.58, 0.8)
- **Footer:** Start Date — Data inicial do período do job (formato AAAA-MM-DD). / Define o primeiro mês a processar.
- **Badge:** Obrigatório
- **Text anim:** 00:05:20,800 → 00:05:22,567 (1.77s)
- **Scene end:** 00:05:30,800
- **Total scene:** 10.00s (static after anim: 8.23s)
- **Resultado esperado:** analista entende decisão em “Start Date”
- **Evidência de verificação:** #start-date; validate_date_range

## 29_mj_end — MonthlyJob campos

- **Elemento:** End Date
- **Capture:** `monthly_fields`
- **Spotlight:** `0.18,0.78,0.98,0.90`
- **Cursor:** move → stop em (0.58, 0.86)
- **Footer:** End Date — Data final do período (formato AAAA-MM-DD). / Deve ser igual ou posterior à Start Date.
- **Badge:** Obrigatório
- **Text anim:** 00:05:31,133 → 00:05:32,833 (1.70s)
- **Scene end:** 00:05:41,133
- **Total scene:** 10.00s (static after anim: 8.30s)
- **Resultado esperado:** analista entende decisão em “End Date”
- **Evidência de verificação:** #end-date; validate_date_range

## 30_et_intro — ExistingTable

- **Elemento:** ExistingTable
- **Capture:** `existing`
- **Spotlight:** `0.16,0.26,0.56,0.46`
- **Cursor:** move → stop em (0.38, 0.36) → clique após leitura
- **Footer:** ExistingTable — Use quando os dados já estão em uma tabela e você / quer exportá-los, sem rodar um arquivo SQL.
- **Badge:** Use apenas quando...
- **Text anim:** 00:05:41,467 → 00:05:43,400 (1.93s)
- **Scene end:** 00:05:51,467
- **Total scene:** 10.00s (static after anim: 8.07s)
- **Resultado esperado:** analista entende decisão em “ExistingTable”
- **Evidência de verificação:** src-existingtable; no SQL path

## 31_et_dest — ExistingTable

- **Elemento:** ExistingTable → Destination
- **Capture:** `existing`
- **Spotlight:** `0.14,0.18,0.90,0.42`
- **Cursor:** move → stop em (0.7, 0.3)
- **Footer:** ExistingTable → Destination — Neste modo o destino permitido é apenas Csv. / Table e Table+Csv ficam indisponíveis.
- **Badge:** Obrigatório
- **Text anim:** 00:05:52,933 → 00:05:54,967 (2.03s)
- **Scene end:** 00:06:02,933
- **Total scene:** 10.00s (static after anim: 7.97s)
- **Resultado esperado:** analista entende decisão em “ExistingTable → Destination”
- **Evidência de verificação:** LEGAL (ExistingTable, Csv); dest hint

## 32_et_no_sql — ExistingTable

- **Elemento:** Sem SQL File
- **Capture:** `existing`
- **Spotlight:** `0.10,0.28,0.90,0.56`
- **Cursor:** move → stop em (0.55, 0.48)
- **Footer:** Sem SQL File — A lista e o campo SQL File ficam ocultos. / A origem é a tabela existente, não um arquivo .sql.
- **Badge:** Use apenas quando...
- **Text anim:** 00:06:03,267 → 00:06:05,200 (1.93s)
- **Scene end:** 00:06:13,267
- **Total scene:** 10.00s (static after anim: 8.07s)
- **Resultado esperado:** analista entende decisão em “Sem SQL File”
- **Evidência de verificação:** row-sql-file/picker display=False

## 33_et_schema_coe — ExistingTable Schema

- **Elemento:** Schema → coe_enc
- **Capture:** `existing_coe`
- **Spotlight:** `0.20,0.58,0.76,0.74`
- **Cursor:** move → stop em (0.5, 0.68) → clique após leitura
- **Footer:** Schema → coe_enc — Seleciona o schema coe_enc da tabela existente. / Use quando a tabela estiver nesse schema.
- **Badge:** Obrigatório
- **Text anim:** 00:06:13,600 → 00:06:15,533 (1.93s)
- **Scene end:** 00:06:23,600
- **Total scene:** 10.00s (static after anim: 8.07s)
- **Resultado esperado:** analista entende decisão em “Schema → coe_enc”
- **Evidência de verificação:** RadioButton esc-coe-enc

## 34_et_schema_aa — ExistingTable Schema

- **Elemento:** Schema → aa_enc
- **Capture:** `existing_fields`
- **Spotlight:** `0.27,0.58,0.83,0.74`
- **Cursor:** move → stop em (0.55, 0.68) → clique após leitura
- **Footer:** Schema → aa_enc — Seleciona o schema aa_enc da tabela existente. / É a opção padrão quando a tabela está em aa_enc.
- **Badge:** Obrigatório
- **Text anim:** 00:06:25,067 → 00:06:27,100 (2.03s)
- **Scene end:** 00:06:35,067
- **Total scene:** 10.00s (static after anim: 7.97s)
- **Resultado esperado:** analista entende decisão em “Schema → aa_enc”
- **Evidência de verificação:** RadioButton esc-aa-enc

## 35_et_schema_other — ExistingTable Schema

- **Elemento:** Schema → other
- **Capture:** `existing_other`
- **Spotlight:** `0.34,0.58,0.90,0.74`
- **Cursor:** move → stop em (0.6, 0.68) → clique após leitura
- **Footer:** Schema → other — Use quando o schema não é coe_enc nem aa_enc. / Ao marcar other, aparece o campo Custom Schema.
- **Badge:** Use apenas quando...
- **Text anim:** 00:06:36,533 → 00:06:38,500 (1.97s)
- **Scene end:** 00:06:46,533
- **Total scene:** 10.00s (static after anim: 8.03s)
- **Resultado esperado:** analista entende decisão em “Schema → other”
- **Evidência de verificação:** esc-other enables #existing-schema-custom

## 36_et_custom — ExistingTable Schema

- **Elemento:** Custom Schema
- **Capture:** `existing_other`
- **Spotlight:** `0.18,0.66,0.98,0.78`
- **Cursor:** move → stop em (0.58, 0.74)
- **Footer:** Custom Schema — Digite o nome do schema personalizado. / Só aparece quando Schema = other.
- **Badge:** Obrigatório
- **Text anim:** 00:06:48,000 → 00:06:49,567 (1.57s)
- **Scene end:** 00:06:58,000
- **Total scene:** 10.00s (static after anim: 8.43s)
- **Resultado esperado:** analista entende decisão em “Custom Schema”
- **Evidência de verificação:** row-existing-schema-custom

## 37_et_table — ExistingTable

- **Elemento:** Existing Table
- **Capture:** `existing_fields`
- **Spotlight:** `0.18,0.70,0.98,0.82`
- **Cursor:** move → stop em (0.58, 0.78) → clique após leitura
- **Footer:** Existing Table — Informe só o nome da tabela (sem o schema). / Junto com o schema, forma a origem completa schema.tabela.
- **Badge:** Obrigatório
- **Text anim:** 00:06:58,333 → 00:07:00,467 (2.13s)
- **Scene end:** 00:07:08,333
- **Total scene:** 10.00s (static after anim: 7.87s)
- **Resultado esperado:** analista entende decisão em “Existing Table”
- **Evidência de verificação:** #existing-table; validate_full_table

## 38_rel_standard — Relações

- **Elemento:** Combinação comum
- **Capture:** `ready_review`
- **Spotlight:** `0.08,0.12,0.92,0.56`
- **Cursor:** move → stop em (0.55, 0.36) → clique após leitura
- **Footer:** Combinação comum — SqlFile + Csv + arquivo .sql sem marcadores de data. / Fluxo típico para gerar um CSV a partir de uma consulta.
- **Badge:** —
- **Text anim:** 00:07:09,800 → 00:07:12,100 (2.30s)
- **Scene end:** 00:07:19,800
- **Total scene:** 10.00s (static after anim: 7.70s)
- **Resultado esperado:** analista entende decisão em “Combinação comum”
- **Evidência de verificação:** LEGAL SqlFile/Csv; detect_source without tokens

## 39_rel_monthly — Relações

- **Elemento:** Combinação MonthlyJob
- **Capture:** `monthly_fields`
- **Spotlight:** `0.08,0.10,0.92,0.66`
- **Cursor:** move → stop em (0.55, 0.4)
- **Footer:** Combinação MonthlyJob — MonthlyJob + Table + .sql com {date_inicio} e {date_fim} / + Schema, Table Name, Start Date e End Date.
- **Badge:** —
- **Text anim:** 00:07:21,267 → 00:07:23,500 (2.23s)
- **Scene end:** 00:07:31,267
- **Total scene:** 10.00s (static after anim: 7.77s)
- **Resultado esperado:** analista entende decisão em “Combinação MonthlyJob”
- **Evidência de verificação:** LEGAL SqlTemplate/Table + date fields

## 40_rel_existing — Relações

- **Elemento:** Combinação ExistingTable
- **Capture:** `existing_fields`
- **Spotlight:** `0.08,0.12,0.92,0.60`
- **Cursor:** move → stop em (0.55, 0.42)
- **Footer:** Combinação ExistingTable — ExistingTable + Csv + Schema + Existing Table. / Não usa SQL File nem MonthlyJob ao mesmo tempo.
- **Badge:** —
- **Text anim:** 00:07:31,600 → 00:07:33,767 (2.17s)
- **Scene end:** 00:07:41,600
- **Total scene:** 10.00s (static after anim: 7.83s)
- **Resultado esperado:** analista entende decisão em “Combinação ExistingTable”
- **Evidência de verificação:** Source radio exclusive; ExistingTable hides SQL

## 41_rel_incompat — Relações

- **Elemento:** Combinações indisponíveis
- **Capture:** `matrix`
- **Spotlight:** `0.10,0.04,0.94,0.32`
- **Cursor:** move → stop em (0.52, 0.2)
- **Footer:** Combinações indisponíveis — MonthlyJob não aceita Csv ou Table+Csv. / ExistingTable não aceita Table ou Table+Csv.
- **Badge:** —
- **Text anim:** 00:07:41,933 → 00:07:43,933 (2.00s)
- **Scene end:** 00:07:51,933
- **Total scene:** 10.00s (static after anim: 8.00s)
- **Resultado esperado:** analista entende decisão em “Combinações indisponíveis”
- **Evidência de verificação:** LEGAL_CELLS matrix

## 42_val_bad — Validação

- **Elemento:** E-mail inválido
- **Capture:** `email_bad`
- **Spotlight:** `0.18,0.68,0.98,0.84`
- **Cursor:** move → stop em (0.58, 0.78)
- **Footer:** E-mail inválido — Se o formato estiver incorreto, o status mostra o problema. / Corrija antes de continuar.
- **Badge:** —
- **Text anim:** 00:07:52,267 → 00:07:54,133 (1.87s)
- **Scene end:** 00:08:02,267
- **Total scene:** 10.00s (static after anim: 8.13s)
- **Resultado esperado:** analista entende decisão em “E-mail inválido”
- **Evidência de verificação:** Invalid email format in validation-summary

## 43_val_ok — Validação

- **Elemento:** Formulário pronto
- **Capture:** `ready_review`
- **Spotlight:** `0.42,0.84,0.98,0.95`
- **Cursor:** move → stop em (0.72, 0.92)
- **Footer:** Formulário pronto — Com os dados corrigidos, o status volta a Ready to launch. / Revise origem, destino, arquivo e fila.
- **Badge:** —
- **Text anim:** 00:08:02,600 → 00:08:04,700 (2.10s)
- **Scene end:** 00:08:12,600
- **Total scene:** 10.00s (static after anim: 7.90s)
- **Resultado esperado:** analista entende decisão em “Formulário pronto”
- **Evidência de verificação:** Ready to launch

## 44_preview — Preview

- **Elemento:** Preview SQL
- **Capture:** `preview`
- **Spotlight:** `0.30,0.20,0.94,0.76`
- **Cursor:** move → stop em (0.78, 0.92) → clique após leitura
- **Footer:** Preview SQL — Mostra o conteúdo que será usado no job. / Confira se a consulta e o destino estão corretos antes do envio.
- **Badge:** —
- **Text anim:** 00:08:12,933 → 00:08:15,067 (2.13s)
- **Scene end:** 00:08:22,933
- **Total scene:** 10.00s (static after anim: 7.87s)
- **Resultado esperado:** analista entende decisão em “Preview SQL”
- **Evidência de verificação:** Preview SQL [P]; unavailable for ExistingTable

## 45_checklist — Revisão

- **Elemento:** Antes de iniciar, confirme:
- **Capture:** `card:checklist`
- **Spotlight:** `0.08,0.12,0.92,0.78`
- **Cursor:** move → stop em (0.5, 0.5)
- **Footer:** Antes de iniciar, confirme: — • origem e destino; / • arquivo ou tabela selecionados; / • fila de execução; / • opções adicionais; / • e-mail de notificação.
- **Badge:** —
- **Text anim:** 00:08:24,067 → 00:08:26,733 (2.67s)
- **Scene end:** 00:08:36,067
- **Total scene:** 12.00s (static after anim: 9.33s)
- **Resultado esperado:** analista entende decisão em “Antes de iniciar, confirme:”
- **Evidência de verificação:** analyst checklist from form fields

## 46_confirm — Envio

- **Elemento:** Launch Job
- **Capture:** `confirm`
- **Spotlight:** `0.14,0.27,0.86,0.83`
- **Cursor:** move → stop em (0.42, 0.72) → clique após leitura
- **Footer:** Launch Job — Inicia o job com as configurações revisadas. / Leia o resumo e confirme apenas se estiver correto.
- **Badge:** —
- **Text anim:** 00:08:36,400 → 00:08:38,333 (1.93s)
- **Scene end:** 00:08:46,400
- **Total scene:** 10.00s (static after anim: 8.07s)
- **Resultado esperado:** analista entende decisão em “Launch Job”
- **Evidência de verificação:** ConfirmScreen Launch Job

## 47_launched — Envio

- **Elemento:** Job enviado
- **Capture:** `launched`
- **Spotlight:** `0.15,0.52,0.95,0.88`
- **Cursor:** move → stop em (0.55, 0.88)
- **Footer:** Job enviado — O job foi enviado pelo Dispatch. / Acompanhe o andamento na tela de monitoramento.
- **Badge:** —
- **Text anim:** 00:08:47,867 → 00:08:49,533 (1.67s)
- **Scene end:** 00:08:57,867
- **Total scene:** 10.00s (static after anim: 8.33s)
- **Resultado esperado:** analista entende decisão em “Job enviado”
- **Evidência de verificação:** Launched Job message; no Impala success claim

## 48_overview — Overview

- **Elemento:** Overview
- **Capture:** `overview`
- **Spotlight:** `0.02,0.06,0.28,0.38`
- **Cursor:** move → stop em (0.12, 0.22) → clique após leitura
- **Footer:** Overview — Após o envio, acompanhe o status do job no Overview.
- **Badge:** —
- **Text anim:** 00:08:58,200 → 00:08:59,700 (1.50s)
- **Scene end:** 00:09:08,200
- **Total scene:** 10.00s (static after anim: 8.50s)
- **Resultado esperado:** analista entende decisão em “Overview”
- **Evidência de verificação:** DashboardScreen / Overview nav

## 49_close — Encerramento

- **Elemento:** Resumo
- **Capture:** `card:close`
- **Spotlight:** `0.08,0.12,0.92,0.78`
- **Cursor:** move → stop em (0.5, 0.5)
- **Footer:** Resumo — Na aba New Job, você: / 1. define a execução; / 2. revisa as configurações; / 3. inicia o job; / 4. acompanha o resultado no Overview. /  / Em caso de dúvida, revise os campos antes de selecionar Launch Job.
- **Badge:** —
- **Text anim:** 00:09:09,333 → 00:09:12,333 (3.00s)
- **Scene end:** 00:09:21,333
- **Total scene:** 12.00s (static after anim: 9.00s)
- **Resultado esperado:** analista entende decisão em “Resumo”
- **Evidência de verificação:** closing summary
