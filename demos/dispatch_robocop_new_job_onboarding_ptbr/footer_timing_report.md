# Instructional scene timing validation (exactly 8.0s)

Rule: each instructional scene = **8.0s** total (includes typing).
Typing target: 1.0–1.5s. Dim alpha=168.

| Scene | Element | Start | Type end | Arrow | End | Type | Static | Total | Spotlight | Opacity | Result |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `01_open` | Dispatch (Robocop) | 00:00:00,000 | 00:00:01,267 | 00:00:01,267 | 00:00:08,000 | 1.27s | 6.73s | 8.00s | `0.10,0.14,0.90,0.72` | 168 | **PASS** |
|  | dialogue: Dispatch (Robocop) — Como utilizar a aba New Job. / Configure e inicie um job passo a passo. | | | | | | | | | | |
| `02_purpose_a` | Para que serve New Job | 00:00:08,300 | 00:00:09,333 | 00:00:09,333 | 00:00:16,300 | 1.03s | 6.97s | 8.00s | `0.27,0.02,0.83,0.22` | 168 | **PASS** |
|  | dialogue: Para que serve New Job — Configure e inicie uma nova execução no Dispatch. | | | | | | | | | | |
| `02_purpose_b` | O que você decide aqui | 00:00:16,600 | 00:00:17,600 | 00:00:17,600 | 00:00:24,600 | 1.00s | 7.00s | 8.00s | `0.27,0.10,0.83,0.30` | 168 | **PASS** |
|  | dialogue: O que você decide aqui — Origem, destino, consulta e opções do job. | | | | | | | | | | |
| `03_matrix` | Source × Destination | 00:00:24,900 | 00:00:26,300 | 00:00:26,300 | 00:00:32,900 | 1.40s | 6.60s | 8.00s | `0.07,0.04,0.97,0.28` | 168 | **PASS** |
|  | dialogue: Source × Destination — Mostra as combinações permitidas. / Consulte antes de escolher origem e destino. | | | | | | | | | | |
| `04_detected` | Detected source | 00:00:34,133 | 00:00:35,467 | 00:00:35,467 | 00:00:42,133 | 1.33s | 6.67s | 8.00s | `0.12,0.20,0.92,0.32` | 168 | **PASS** |
|  | dialogue: Detected source — Tipo identificado no arquivo SQL. / Confirme se é o job que você quer executar. | | | | | | | | | | |
| `05_source_intro` | Source | 00:00:42,433 | 00:00:43,533 | 00:00:43,533 | 00:00:50,433 | 1.10s | 6.90s | 8.00s | `0.18,0.22,0.54,0.42` | 168 | **PASS** |
|  | dialogue: Source — Define de onde vêm os dados do job. / É a primeira decisão do formulário. | | | | | | | | | | |
| `06_source_sqlfile` | Source → SqlFile | 00:00:50,733 | 00:00:51,733 | 00:00:51,733 | 00:00:58,733 | 1.00s | 7.00s | 8.00s | `0.18,0.22,0.54,0.42` | 168 | **PASS** |
|  | dialogue: Source → SqlFile — Use quando a consulta está em um .sql simples. | | | | | | | | | | |
| `06b_source_sqlfile_effect` | SqlFile — efeito | 00:00:59,967 | 00:01:00,967 | 00:01:00,967 | 00:01:07,967 | 1.00s | 7.00s | 8.00s | `0.18,0.22,0.54,0.42` | 168 | **PASS** |
|  | dialogue: SqlFile — efeito — O Dispatch executa esse arquivo conforme o destino. | | | | | | | | | | |
| `07_dest_intro` | Destination | 00:01:08,267 | 00:01:09,433 | 00:01:09,433 | 00:01:16,267 | 1.17s | 6.83s | 8.00s | `0.52,0.20,0.88,0.40` | 168 | **PASS** |
|  | dialogue: Destination — Define onde o resultado será armazenado. / Depende da origem escolhida. | | | | | | | | | | |
| `08_dest_table` | Destination → Table | 00:01:16,567 | 00:01:17,867 | 00:01:17,867 | 00:01:24,567 | 1.30s | 6.70s | 8.00s | `0.52,0.18,0.88,0.34` | 168 | **PASS** |
|  | dialogue: Destination → Table — Salva o resultado em uma tabela. / Use para consultar depois no ambiente. | | | | | | | | | | |
| `09_dest_csv` | Destination → Csv | 00:01:25,800 | 00:01:26,800 | 00:01:26,800 | 00:01:33,800 | 1.00s | 7.00s | 8.00s | `0.52,0.22,0.88,0.38` | 168 | **PASS** |
|  | dialogue: Destination → Csv — Gera um CSV na pasta em que você abriu o Dispatch. | | | | | | | | | | |
| `09b_dest_csv_when` | Csv — quando usar | 00:01:35,033 | 00:01:36,100 | 00:01:36,100 | 00:01:43,033 | 1.07s | 6.93s | 8.00s | `0.52,0.22,0.88,0.38` | 168 | **PASS** |
|  | dialogue: Csv — quando usar — Use para baixar ou compartilhar o resultado como arquivo. | | | | | | | | | | |
| `10_dest_tablecsv` | Destination → Table+Csv | 00:01:43,333 | 00:01:44,700 | 00:01:44,700 | 00:01:51,333 | 1.37s | 6.63s | 8.00s | `0.52,0.26,0.88,0.42` | 168 | **PASS** |
|  | dialogue: Destination → Table+Csv — Cria a tabela e também gera o CSV. / Use quando precisa dos dois formatos. | | | | | | | | | | |
| `11_queue_a` | Execution Queue | 00:01:52,567 | 00:01:53,767 | 00:01:53,767 | 00:02:00,567 | 1.20s | 6.80s | 8.00s | `0.17,0.34,0.93,0.62` | 168 | **PASS** |
|  | dialogue: Execution Queue — Fila de processamento do job. / Sem marcação, a escolha é automática. | | | | | | | | | | |
| `12_queue_b` | Execution Queue — marcar | 00:02:00,867 | 00:02:01,900 | 00:02:01,900 | 00:02:08,867 | 1.03s | 6.97s | 8.00s | `0.17,0.38,0.93,0.66` | 168 | **PASS** |
|  | dialogue: Execution Queue — marcar — Marque filas só se o projeto indicar qual usar. | | | | | | | | | | |
| `12b_queue_order` | Várias filas | 00:02:10,100 | 00:02:11,100 | 00:02:11,100 | 00:02:18,100 | 1.00s | 7.00s | 8.00s | `0.17,0.38,0.93,0.66` | 168 | **PASS** |
|  | dialogue: Várias filas — Se marcar várias, são tentadas na ordem da lista. | | | | | | | | | | |
| `13_sql_intro` | SQL File | 00:02:18,400 | 00:02:19,400 | 00:02:19,400 | 00:02:26,400 | 1.00s | 7.00s | 8.00s | `0.13,0.44,0.97,0.72` | 168 | **PASS** |
|  | dialogue: SQL File — É a consulta que o job vai executar. | | | | | | | | | | |
| `13b_sql_when` | SQL File — quando | 00:02:26,700 | 00:02:27,700 | 00:02:27,700 | 00:02:34,700 | 1.00s | 7.00s | 8.00s | `0.13,0.44,0.97,0.72` | 168 | **PASS** |
|  | dialogue: SQL File — quando — Obrigatório para SqlFile e MonthlyJob. | | | | | | | | | | |
| `14_sql_picker` | Lista de arquivos SQL | 00:02:35,000 | 00:02:36,200 | 00:02:36,200 | 00:02:43,000 | 1.20s | 6.80s | 8.00s | `0.13,0.44,0.97,0.72` | 168 | **PASS** |
|  | dialogue: Lista de arquivos SQL — Mostra os .sql da pasta atual. / Selecione o arquivo do seu job. | | | | | | | | | | |
| `15_sql_verify` | O que conferir | 00:02:44,233 | 00:02:45,233 | 00:02:45,233 | 00:02:52,233 | 1.00s | 7.00s | 8.00s | `0.13,0.46,0.97,0.78` | 168 | **PASS** |
|  | dialogue: O que conferir — Confirme o nome e o tipo Detected na lista. | | | | | | | | | | |
| `15b_sql_path` | Caminho do SQL File | 00:02:52,533 | 00:02:53,567 | 00:02:53,567 | 00:03:00,533 | 1.03s | 6.97s | 8.00s | `0.13,0.62,0.97,0.78` | 168 | **PASS** |
|  | dialogue: Caminho do SQL File — Após a seleção, o caminho preenche o campo SQL File. | | | | | | | | | | |
| `16_sql_role` | Papel do SQL File | 00:03:00,833 | 00:03:01,833 | 00:03:01,833 | 00:03:08,833 | 1.00s | 7.00s | 8.00s | `0.13,0.58,0.97,0.78` | 168 | **PASS** |
|  | dialogue: Papel do SQL File — Define quais dados serão lidos ou calculados. | | | | | | | | | | |
| `16b_sql_role_dest` | SQL + destino | 00:03:09,133 | 00:03:10,133 | 00:03:10,133 | 00:03:17,133 | 1.00s | 7.00s | 8.00s | `0.13,0.22,0.97,0.50` | 168 | **PASS** |
|  | dialogue: SQL + destino — Source e Destination decidem como entregar o resultado. | | | | | | | | | | |
| `17_email` | Email (notifications) | 00:03:17,433 | 00:03:18,700 | 00:03:18,700 | 00:03:25,433 | 1.27s | 6.73s | 8.00s | `0.16,0.70,0.98,0.82` | 168 | **PASS** |
|  | dialogue: Email (notifications) — Recebe aviso quando o job terminar. / Deixe em branco se não quiser. | | | | | | | | | | |
| `18_subject` | Subject (email) | 00:03:26,667 | 00:03:27,967 | 00:03:27,967 | 00:03:34,667 | 1.30s | 6.70s | 8.00s | `0.16,0.76,0.98,0.88` | 168 | **PASS** |
|  | dialogue: Subject (email) — Assunto do e-mail de notificação. / Use um texto curto que identifique o job. | | | | | | | | | | |
| `19_status_bar` | Status do formulário | 00:03:35,900 | 00:03:36,900 | 00:03:36,900 | 00:03:43,900 | 1.00s | 7.00s | 8.00s | `0.42,0.84,0.98,0.92` | 168 | **PASS** |
|  | dialogue: Status do formulário — Ready to launch = sem problemas bloqueantes. | | | | | | | | | | |
| `19b_actions` | Preview SQL e Launch | 00:03:44,200 | 00:03:45,200 | 00:03:45,200 | 00:03:52,200 | 1.00s | 7.00s | 8.00s | `0.58,0.84,0.98,0.92` | 168 | **PASS** |
|  | dialogue: Preview SQL e Launch — Ficam na barra inferior para revisão e envio. | | | | | | | | | | |
| `20_mj_intro` | MonthlyJob | 00:03:52,500 | 00:03:53,667 | 00:03:53,667 | 00:04:00,500 | 1.17s | 6.83s | 8.00s | `0.16,0.26,0.56,0.46` | 168 | **PASS** |
|  | dialogue: MonthlyJob — Use para cobrir um intervalo de datas, / executando o período mês a mês. | | | | | | | | | | |
| `21_mj_dest` | MonthlyJob → Destination | 00:04:01,733 | 00:04:02,767 | 00:04:02,767 | 00:04:09,733 | 1.03s | 6.97s | 8.00s | `0.14,0.18,0.90,0.42` | 168 | **PASS** |
|  | dialogue: MonthlyJob → Destination — Com MonthlyJob, o destino permitido é só Table. | | | | | | | | | | |
| `21b_mj_dest_blocked` | Csv e Table+Csv | 00:04:10,033 | 00:04:11,033 | 00:04:11,033 | 00:04:18,033 | 1.00s | 7.00s | 8.00s | `0.50,0.24,0.90,0.44` | 168 | **PASS** |
|  | dialogue: Csv e Table+Csv — Ficam indisponíveis neste modo. | | | | | | | | | | |
| `22_mj_sql_rule_a` | SQL no MonthlyJob — regr | 00:04:18,033 | 00:04:19,367 | 00:04:19,367 | 00:04:26,033 | 1.33s | 6.67s | 8.00s | `0.10,0.14,0.90,0.72` | 168 | **PASS** |
|  | dialogue: SQL no MonthlyJob — regra — O .sql precisa conter os dois marcadores: / {date_inicio} e {date_fim} | | | | | | | | | | |
| `23_mj_sql_rule_b` | Como conferir no arquivo | 00:04:26,033 | 00:04:27,233 | 00:04:27,233 | 00:04:34,033 | 1.20s | 6.80s | 8.00s | `0.10,0.14,0.90,0.72` | 168 | **PASS** |
|  | dialogue: Como conferir no arquivo — Abra o .sql e busque exatamente / {date_inicio} e {date_fim}. | | | | | | | | | | |
| `23b_mj_sql_missing` | Se faltar um marcador | 00:04:34,033 | 00:04:35,033 | 00:04:35,033 | 00:04:42,033 | 1.00s | 7.00s | 8.00s | `0.10,0.14,0.90,0.72` | 168 | **PASS** |
|  | dialogue: Se faltar um marcador — O job não pode ser iniciado como MonthlyJob. | | | | | | | | | | |
| `24_mj_sql_rule_c` | O que os marcadores faze | 00:04:42,033 | 00:04:43,033 | 00:04:43,033 | 00:04:50,033 | 1.00s | 7.00s | 8.00s | `0.10,0.14,0.90,0.72` | 168 | **PASS** |
|  | dialogue: O que os marcadores fazem — Reservam início e fim de cada mês do período. | | | | | | | | | | |
| `24b_mj_sql_fill` | Preenchimento das datas | 00:04:50,033 | 00:04:51,100 | 00:04:51,100 | 00:04:58,033 | 1.07s | 6.93s | 8.00s | `0.10,0.14,0.90,0.72` | 168 | **PASS** |
|  | dialogue: Preenchimento das datas — O Dispatch preenche conforme Start Date e End Date. | | | | | | | | | | |
| `25_mj_picker` | SQL do MonthlyJob | 00:04:58,333 | 00:04:59,333 | 00:04:59,333 | 00:05:06,333 | 1.00s | 7.00s | 8.00s | `0.13,0.42,0.97,0.70` | 168 | **PASS** |
|  | dialogue: SQL do MonthlyJob — Na lista, escolha Detected = MonthlyJob. | | | | | | | | | | |
| `25b_mj_picker_confirm` | Detected = MonthlyJob | 00:05:07,567 | 00:05:08,600 | 00:05:08,600 | 00:05:15,567 | 1.03s | 6.97s | 8.00s | `0.13,0.42,0.97,0.70` | 168 | **PASS** |
|  | dialogue: Detected = MonthlyJob — Confirma que os dois marcadores foram encontrados. | | | | | | | | | | |
| `26_mj_schema` | Schema (MonthlyJob) | 00:05:15,867 | 00:05:17,167 | 00:05:17,167 | 00:05:23,867 | 1.30s | 6.70s | 8.00s | `0.18,0.60,0.98,0.72` | 168 | **PASS** |
|  | dialogue: Schema (MonthlyJob) — Schema da tabela de resultado. / Informe o schema correto do seu trabalho. | | | | | | | | | | |
| `27_mj_table` | Table Name (MonthlyJob) | 00:05:24,167 | 00:05:25,167 | 00:05:25,167 | 00:05:32,167 | 1.00s | 7.00s | 8.00s | `0.18,0.66,0.98,0.78` | 168 | **PASS** |
|  | dialogue: Table Name (MonthlyJob) — Nome da tabela com o prefixo do usuário. | | | | | | | | | | |
| `27b_mj_table_suffix` | Sufixo da tabela | 00:05:32,467 | 00:05:33,467 | 00:05:33,467 | 00:05:40,467 | 1.00s | 7.00s | 8.00s | `0.18,0.66,0.98,0.78` | 168 | **PASS** |
|  | dialogue: Sufixo da tabela — Complete só o sufixo; o prefixo já vem preenchido. | | | | | | | | | | |
| `28_mj_start` | Start Date | 00:05:40,767 | 00:05:41,800 | 00:05:41,800 | 00:05:48,767 | 1.03s | 6.97s | 8.00s | `0.18,0.72,0.98,0.84` | 168 | **PASS** |
|  | dialogue: Start Date — Data inicial (AAAA-MM-DD). / Define o primeiro mês a processar. | | | | | | | | | | |
| `29_mj_end` | End Date | 00:05:49,067 | 00:05:50,133 | 00:05:50,133 | 00:05:57,067 | 1.07s | 6.93s | 8.00s | `0.18,0.78,0.98,0.90` | 168 | **PASS** |
|  | dialogue: End Date — Data final (AAAA-MM-DD). / Deve ser igual ou posterior à Start Date. | | | | | | | | | | |
| `30_et_intro` | ExistingTable | 00:05:57,367 | 00:05:58,667 | 00:05:58,667 | 00:06:05,367 | 1.30s | 6.70s | 8.00s | `0.16,0.26,0.56,0.46` | 168 | **PASS** |
|  | dialogue: ExistingTable — Use quando os dados já estão em uma tabela / e você quer exportá-los sem .sql. | | | | | | | | | | |
| `31_et_dest` | ExistingTable → Destinat | 00:06:06,600 | 00:06:07,633 | 00:06:07,633 | 00:06:14,600 | 1.03s | 6.97s | 8.00s | `0.14,0.18,0.90,0.42` | 168 | **PASS** |
|  | dialogue: ExistingTable → Destination — Neste modo o destino permitido é apenas Csv. | | | | | | | | | | |
| `31b_et_dest_blocked` | Table e Table+Csv | 00:06:14,900 | 00:06:15,900 | 00:06:15,900 | 00:06:22,900 | 1.00s | 7.00s | 8.00s | `0.50,0.24,0.90,0.44` | 168 | **PASS** |
|  | dialogue: Table e Table+Csv — Ficam indisponíveis com ExistingTable. | | | | | | | | | | |
| `32_et_no_sql` | Sem SQL File | 00:06:23,200 | 00:06:24,400 | 00:06:24,400 | 00:06:31,200 | 1.20s | 6.80s | 8.00s | `0.10,0.28,0.90,0.56` | 168 | **PASS** |
|  | dialogue: Sem SQL File — A lista e o campo SQL File ficam ocultos. / A origem é a tabela existente. | | | | | | | | | | |
| `33_et_schema_coe` | Schema → coe_enc | 00:06:31,500 | 00:06:32,500 | 00:06:32,500 | 00:06:39,500 | 1.00s | 7.00s | 8.00s | `0.20,0.58,0.76,0.74` | 168 | **PASS** |
|  | dialogue: Schema → coe_enc — Seleciona o schema coe_enc da tabela existente. | | | | | | | | | | |
| `34_et_schema_aa` | Schema → aa_enc | 00:06:40,733 | 00:06:41,767 | 00:06:41,767 | 00:06:48,733 | 1.03s | 6.97s | 8.00s | `0.27,0.58,0.83,0.74` | 168 | **PASS** |
|  | dialogue: Schema → aa_enc — Seleciona o schema aa_enc. / É a opção padrão nesse schema. | | | | | | | | | | |
| `35_et_schema_other` | Schema → other | 00:06:49,967 | 00:06:50,967 | 00:06:50,967 | 00:06:57,967 | 1.00s | 7.00s | 8.00s | `0.34,0.58,0.90,0.74` | 168 | **PASS** |
|  | dialogue: Schema → other — Use quando o schema não é coe_enc nem aa_enc. | | | | | | | | | | |
| `35b_et_other_field` | other → Custom Schema | 00:06:59,200 | 00:07:00,200 | 00:07:00,200 | 00:07:07,200 | 1.00s | 7.00s | 8.00s | `0.18,0.62,0.98,0.78` | 168 | **PASS** |
|  | dialogue: other → Custom Schema — Ao marcar other, aparece o campo Custom Schema. | | | | | | | | | | |
| `36_et_custom` | Custom Schema | 00:07:07,500 | 00:07:08,700 | 00:07:08,700 | 00:07:15,500 | 1.20s | 6.80s | 8.00s | `0.18,0.66,0.98,0.78` | 168 | **PASS** |
|  | dialogue: Custom Schema — Digite o nome do schema personalizado. / Só aparece com Schema = other. | | | | | | | | | | |
| `37_et_table` | Existing Table | 00:07:15,800 | 00:07:16,800 | 00:07:16,800 | 00:07:23,800 | 1.00s | 7.00s | 8.00s | `0.18,0.70,0.98,0.82` | 168 | **PASS** |
|  | dialogue: Existing Table — Informe só o nome da tabela (sem o schema). | | | | | | | | | | |
| `37b_et_full` | Origem completa | 00:07:25,033 | 00:07:26,033 | 00:07:26,033 | 00:07:33,033 | 1.00s | 7.00s | 8.00s | `0.18,0.70,0.98,0.82` | 168 | **PASS** |
|  | dialogue: Origem completa — Com o schema, forma schema.tabela. | | | | | | | | | | |
| `38_rel_standard` | Combinação comum | 00:07:33,333 | 00:07:34,333 | 00:07:34,333 | 00:07:41,333 | 1.00s | 7.00s | 8.00s | `0.08,0.12,0.92,0.56` | 168 | **PASS** |
|  | dialogue: Combinação comum — SqlFile + Csv + .sql sem marcadores de data. | | | | | | | | | | |
| `38b_rel_standard_use` | Fluxo típico | 00:07:42,567 | 00:07:43,567 | 00:07:43,567 | 00:07:50,567 | 1.00s | 7.00s | 8.00s | `0.08,0.12,0.92,0.56` | 168 | **PASS** |
|  | dialogue: Fluxo típico — Gera um CSV a partir de uma consulta. | | | | | | | | | | |
| `39_rel_monthly` | Combinação MonthlyJob | 00:07:50,867 | 00:07:52,000 | 00:07:52,000 | 00:07:58,867 | 1.13s | 6.87s | 8.00s | `0.08,0.10,0.92,0.66` | 168 | **PASS** |
|  | dialogue: Combinação MonthlyJob — MonthlyJob + Table + .sql com / {date_inicio} e {date_fim}. | | | | | | | | | | |
| `39b_rel_monthly_fields` | Campos do MonthlyJob | 00:07:59,167 | 00:08:00,167 | 00:08:00,167 | 00:08:07,167 | 1.00s | 7.00s | 8.00s | `0.15,0.54,0.95,0.86` | 168 | **PASS** |
|  | dialogue: Campos do MonthlyJob — Também: Schema, Table Name, Start Date e End Date. | | | | | | | | | | |
| `40_rel_existing` | Combinação ExistingTable | 00:08:07,467 | 00:08:08,467 | 00:08:08,467 | 00:08:15,467 | 1.00s | 7.00s | 8.00s | `0.08,0.12,0.92,0.60` | 168 | **PASS** |
|  | dialogue: Combinação ExistingTable — ExistingTable + Csv + Schema + Existing Table. | | | | | | | | | | |
| `40b_rel_existing_no_sql` | Sem SQL neste modo | 00:08:15,767 | 00:08:16,767 | 00:08:16,767 | 00:08:23,767 | 1.00s | 7.00s | 8.00s | `0.08,0.12,0.92,0.60` | 168 | **PASS** |
|  | dialogue: Sem SQL neste modo — Não usa SQL File nem MonthlyJob ao mesmo tempo. | | | | | | | | | | |
| `41_rel_incompat` | Combinações indisponívei | 00:08:24,067 | 00:08:25,067 | 00:08:25,067 | 00:08:32,067 | 1.00s | 7.00s | 8.00s | `0.10,0.04,0.94,0.32` | 168 | **PASS** |
|  | dialogue: Combinações indisponíveis — MonthlyJob não aceita Csv ou Table+Csv. | | | | | | | | | | |
| `41b_rel_incompat_et` | ExistingTable — limite | 00:08:32,367 | 00:08:33,367 | 00:08:33,367 | 00:08:40,367 | 1.00s | 7.00s | 8.00s | `0.10,0.04,0.94,0.32` | 168 | **PASS** |
|  | dialogue: ExistingTable — limite — ExistingTable não aceita Table ou Table+Csv. | | | | | | | | | | |
| `42_val_bad` | E-mail inválido | 00:08:40,667 | 00:08:41,700 | 00:08:41,700 | 00:08:48,667 | 1.03s | 6.97s | 8.00s | `0.18,0.68,0.98,0.84` | 168 | **PASS** |
|  | dialogue: E-mail inválido — Se o formato estiver errado, o status mostra o problema. | | | | | | | | | | |
| `43_val_ok` | Formulário pronto | 00:08:48,967 | 00:08:49,967 | 00:08:49,967 | 00:08:56,967 | 1.00s | 7.00s | 8.00s | `0.42,0.84,0.98,0.92` | 168 | **PASS** |
|  | dialogue: Formulário pronto — Com os dados corrigidos, volta Ready to launch. | | | | | | | | | | |
| `43b_val_review` | Revise antes de enviar | 00:08:57,267 | 00:08:58,267 | 00:08:58,267 | 00:09:05,267 | 1.00s | 7.00s | 8.00s | `0.08,0.18,0.92,0.62` | 168 | **PASS** |
|  | dialogue: Revise antes de enviar — Confira origem, destino, arquivo e fila. | | | | | | | | | | |
| `44_preview` | Preview SQL | 00:09:05,567 | 00:09:06,567 | 00:09:06,567 | 00:09:13,567 | 1.00s | 7.00s | 8.00s | `0.30,0.20,0.94,0.76` | 168 | **PASS** |
|  | dialogue: Preview SQL — Mostra o conteúdo que será usado no job. | | | | | | | | | | |
| `44b_preview_check` | O que conferir no Previe | 00:09:14,800 | 00:09:15,833 | 00:09:15,833 | 00:09:22,800 | 1.03s | 6.97s | 8.00s | `0.15,0.17,0.95,0.73` | 168 | **PASS** |
|  | dialogue: O que conferir no Preview — Confira a consulta e o destino antes do envio. | | | | | | | | | | |
| `45_checklist` | Antes de iniciar, confir | 00:09:22,800 | 00:09:23,967 | 00:09:23,967 | 00:09:30,800 | 1.17s | 6.83s | 8.00s | `0.10,0.14,0.90,0.72` | 168 | **PASS** |
|  | dialogue: Antes de iniciar, confirme — Origem, destino, arquivo ou tabela, / e fila de execução. | | | | | | | | | | |
| `45b_checklist_b` | Também confira | 00:09:30,800 | 00:09:31,800 | 00:09:31,800 | 00:09:38,800 | 1.00s | 7.00s | 8.00s | `0.10,0.14,0.90,0.72` | 168 | **PASS** |
|  | dialogue: Também confira — Opções adicionais e e-mail de notificação. | | | | | | | | | | |
| `46_confirm` | Launch Job | 00:09:39,100 | 00:09:40,100 | 00:09:40,100 | 00:09:47,100 | 1.00s | 7.00s | 8.00s | `0.14,0.27,0.86,0.83` | 168 | **PASS** |
|  | dialogue: Launch Job — Inicia o job com as configurações revisadas. | | | | | | | | | | |
| `46b_confirm_read` | Confirme só se estiver c | 00:09:48,333 | 00:09:49,367 | 00:09:49,367 | 00:09:56,333 | 1.03s | 6.97s | 8.00s | `0.14,0.27,0.86,0.83` | 168 | **PASS** |
|  | dialogue: Confirme só se estiver correto — Leia o resumo antes de confirmar o envio. | | | | | | | | | | |
| `47_launched` | Job enviado | 00:09:56,633 | 00:09:57,767 | 00:09:57,767 | 00:10:04,633 | 1.13s | 6.87s | 8.00s | `0.15,0.52,0.95,0.88` | 168 | **PASS** |
|  | dialogue: Job enviado — O job foi enviado pelo Dispatch. / Acompanhe na tela de monitoramento. | | | | | | | | | | |
| `48_overview` | Overview | 00:10:04,933 | 00:10:05,933 | 00:10:05,933 | 00:10:12,933 | 1.00s | 7.00s | 8.00s | `0.02,0.06,0.28,0.38` | 168 | **PASS** |
|  | dialogue: Overview — Após o envio, acompanhe o status no Overview. | | | | | | | | | | |
| `49_close` | Resumo | 00:10:13,867 | 00:10:14,867 | 00:10:14,867 | 00:10:21,867 | 1.00s | 7.00s | 8.00s | `0.10,0.14,0.90,0.72` | 168 | **PASS** |
|  | dialogue: Resumo — Na aba New Job você define, revisa e inicia o job. | | | | | | | | | | |
| `49b_close_b` | Depois do envio | 00:10:21,867 | 00:10:23,133 | 00:10:23,133 | 00:10:29,867 | 1.27s | 6.73s | 8.00s | `0.10,0.14,0.90,0.72` | 168 | **PASS** |
|  | dialogue: Depois do envio — Acompanhe o resultado no Overview. / Revise os campos antes de Launch Job. | | | | | | | | | | |

Instructional scenes: 74
Min/Max scene: 8.000s / 8.000s
Min/Max typing: 1.000s / 1.400s

**Overall: PASS**