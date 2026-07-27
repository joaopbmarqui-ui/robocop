# Instructional scene timing validation

Rule: each instructional scene total **10.0–12.0s** (includes text-reveal). Standard = 10.0s; long messages may use 12.0s. Text animation ≤ 25% of scene.

| Scene | Element | Anim start | Anim end | Scene end | Anim | Total | Static | Spotlight | Result |
|---|---|---|---|---|---|---|---|---|---|
| `01_open` | Dispatch (Robocop) | 00:00:00,000 | 00:00:01,667 | 00:00:10,000 | 1.67s | 10.00s | 8.33s | `0.08,0.12,0.92,0.78` | **PASS** |
|  | footer: Dispatch (Robocop) — Como utilizar a aba New Job / Configure e inicie um novo job passo a passo. | | | | | | | | |
| `02_purpose_a` | Para que serve a aba New Job | 00:00:10,333 | 00:00:12,000 | 00:00:20,333 | 1.67s | 10.00s | 8.33s | `0.02,0.02,0.98,0.30` | **PASS** |
|  | footer: Para que serve a aba New Job — Ela permite configurar e iniciar uma nova execução no Dispatch. | | | | | | | | |
| `02_purpose_b` | O que você decide aqui | 00:00:20,667 | 00:00:22,900 | 00:00:30,667 | 2.23s | 10.00s | 7.77s | `0.02,0.02,0.98,0.38` | **PASS** |
|  | footer: O que você decide aqui — Você escolhe a origem dos dados, o destino do resultado, / a consulta e as opções de execu | | | | | | | | |
| `03_matrix` | Source × Destination | 00:00:31,000 | 00:00:33,167 | 00:00:41,000 | 2.17s | 10.00s | 7.83s | `0.07,0.04,0.97,0.28` | **PASS** |
|  | footer: Source × Destination — Tabela de referência com as combinações permitidas. / Consulte-a antes de escolher origem  | | | | | | | | |
| `04_detected` | Detected source | 00:00:42,467 | 00:00:44,733 | 00:00:52,467 | 2.27s | 10.00s | 7.73s | `0.12,0.20,0.92,0.32` | **PASS** |
|  | footer: Detected source — Mostra o tipo identificado no arquivo SQL selecionado. / Confirme se corresponde ao job qu | | | | | | | | |
| `05_source_intro` | Source | 00:00:52,800 | 00:00:54,400 | 00:01:02,800 | 1.60s | 10.00s | 8.40s | `0.18,0.22,0.54,0.42` | **PASS** |
|  | footer: Source — Define de onde os dados do job serão obtidos. / É a primeira decisão do formulário. | | | | | | | | |
| `06_source_sqlfile` | Source → SqlFile | 00:01:03,133 | 00:01:05,567 | 00:01:15,133 | 2.43s | 12.00s | 9.57s | `0.18,0.22,0.54,0.42` | **PASS** |
|  | footer: Source → SqlFile — Use quando a consulta está em um arquivo .sql simples. / O Dispatch executa essa consulta  | | | | | | | | |
| `07_dest_intro` | Destination | 00:01:16,600 | 00:01:18,433 | 00:01:26,600 | 1.83s | 10.00s | 8.17s | `0.52,0.20,0.88,0.40` | **PASS** |
|  | footer: Destination — Define onde o resultado do job será armazenado. / A escolha depende da origem selecionada. | | | | | | | | |
| `08_dest_table` | Destination → Table | 00:01:26,933 | 00:01:29,000 | 00:01:36,933 | 2.07s | 10.00s | 7.93s | `0.52,0.18,0.88,0.34` | **PASS** |
|  | footer: Destination → Table — Salva o resultado em uma tabela. / Use quando precisar consultar o resultado depois no amb | | | | | | | | |
| `09_dest_csv` | Destination → Csv | 00:01:38,400 | 00:01:41,133 | 00:01:50,400 | 2.73s | 12.00s | 9.27s | `0.52,0.22,0.88,0.38` | **PASS** |
|  | footer: Destination → Csv — Gera um arquivo CSV na pasta de onde você abriu o Dispatch. / Use quando o resultado preci | | | | | | | | |
| `10_dest_tablecsv` | Destination → Table+Csv | 00:01:51,867 | 00:01:53,933 | 00:02:01,867 | 2.07s | 10.00s | 7.93s | `0.52,0.26,0.88,0.42` | **PASS** |
|  | footer: Destination → Table+Csv — Cria a tabela e também gera o CSV. / Use quando precisa dos dois formatos na mesma execuçã | | | | | | | | |
| `11_queue_a` | Execution Queue | 00:02:03,333 | 00:02:05,233 | 00:02:13,333 | 1.90s | 10.00s | 8.10s | `0.17,0.34,0.93,0.62` | **PASS** |
|  | footer: Execution Queue — Indica a fila de processamento do job. / Sem marcação, o Dispatch escolhe automaticamente. | | | | | | | | |
| `12_queue_b` | Execution Queue — quando mar | 00:02:13,667 | 00:02:16,200 | 00:02:25,667 | 2.53s | 12.00s | 9.47s | `0.17,0.38,0.93,0.66` | **PASS** |
|  | footer: Execution Queue — quando marcar — Marque uma ou mais filas só se o seu projeto indicar qual usar. / Várias filas são tentada | | | | | | | | |
| `13_sql_intro` | SQL File | 00:02:27,133 | 00:02:29,200 | 00:02:37,133 | 2.07s | 10.00s | 7.93s | `0.13,0.44,0.97,0.72` | **PASS** |
|  | footer: SQL File — É a consulta que o job vai executar. / Para SqlFile e MonthlyJob, você precisa selecionar  | | | | | | | | |
| `14_sql_picker` | Lista de arquivos SQL | 00:02:37,467 | 00:02:39,833 | 00:02:49,467 | 2.37s | 12.00s | 9.63s | `0.13,0.44,0.97,0.72` | **PASS** |
|  | footer: Lista de arquivos SQL — Mostra os arquivos .sql da pasta atual. / Selecione o arquivo do job para preencher o cami | | | | | | | | |
| `15_sql_verify` | O que conferir no arquivo | 00:02:50,933 | 00:02:53,333 | 00:03:02,933 | 2.40s | 12.00s | 9.60s | `0.13,0.46,0.97,0.78` | **PASS** |
|  | footer: O que conferir no arquivo — Confirme o nome do arquivo e o tipo Detected na lista. / O caminho aparece no campo SQL Fi | | | | | | | | |
| `16_sql_role` | Papel do SQL File no job | 00:03:03,267 | 00:03:05,900 | 00:03:15,267 | 2.63s | 12.00s | 9.37s | `0.13,0.58,0.97,0.78` | **PASS** |
|  | footer: Papel do SQL File no job — Esse arquivo define quais dados serão lidos ou calculados. / Source e Destination decidem  | | | | | | | | |
| `17_email` | Email (notifications) | 00:03:15,600 | 00:03:17,433 | 00:03:25,600 | 1.83s | 10.00s | 8.17s | `0.16,0.70,0.98,0.82` | **PASS** |
|  | footer: Email (notifications) — Recebe aviso quando o job terminar. / Deixe em branco se não quiser notificação. | | | | | | | | |
| `18_subject` | Subject (email) | 00:03:27,067 | 00:03:28,733 | 00:03:37,067 | 1.67s | 10.00s | 8.33s | `0.16,0.76,0.98,0.88` | **PASS** |
|  | footer: Subject (email) — Assunto do e-mail de notificação. / Use um texto curto que identifique o job. | | | | | | | | |
| `19_status_bar` | Status do formulário | 00:03:38,533 | 00:03:40,767 | 00:03:48,533 | 2.23s | 10.00s | 7.77s | `0.42,0.84,0.98,0.95` | **PASS** |
|  | footer: Status do formulário — Ready to launch indica que não há problemas bloqueantes. / Preview SQL e Launch ficam na b | | | | | | | | |
| `20_mj_intro` | MonthlyJob | 00:03:48,867 | 00:03:50,733 | 00:03:58,867 | 1.87s | 10.00s | 8.13s | `0.16,0.26,0.56,0.46` | **PASS** |
|  | footer: MonthlyJob — Use quando a consulta precisa cobrir um intervalo de datas, / executando o período mês a m | | | | | | | | |
| `21_mj_dest` | MonthlyJob → Destination | 00:04:00,333 | 00:04:02,400 | 00:04:10,333 | 2.07s | 10.00s | 7.93s | `0.14,0.18,0.90,0.42` | **PASS** |
|  | footer: MonthlyJob → Destination — Com MonthlyJob, o destino permitido é apenas Table. / Csv e Table+Csv ficam indisponíveis. | | | | | | | | |
| `22_mj_sql_rule_a` | SQL File no MonthlyJob — reg | 00:04:10,333 | 00:04:12,267 | 00:04:20,333 | 1.93s | 10.00s | 8.07s | `0.08,0.12,0.92,0.78` | **PASS** |
|  | footer: SQL File no MonthlyJob — regra — O arquivo .sql precisa conter os dois marcadores: / {date_inicio} e {date_fim} | | | | | | | | |
| `23_mj_sql_rule_b` | Como conferir no arquivo | 00:04:20,333 | 00:04:23,033 | 00:04:32,333 | 2.70s | 12.00s | 9.30s | `0.08,0.12,0.92,0.78` | **PASS** |
|  | footer: Como conferir no arquivo — Abra o .sql e busque exatamente {date_inicio} e {date_fim}. / Se faltar um deles, o job nã | | | | | | | | |
| `24_mj_sql_rule_c` | O que esses marcadores fazem | 00:04:32,333 | 00:04:35,133 | 00:04:44,333 | 2.80s | 12.00s | 9.20s | `0.08,0.12,0.92,0.78` | **PASS** |
|  | footer: O que esses marcadores fazem — Eles reservam o início e o fim de cada mês no período informado. / O Dispatch preenche as  | | | | | | | | |
| `25_mj_picker` | Selecionar o SQL do MonthlyJ | 00:04:44,667 | 00:04:47,233 | 00:04:56,667 | 2.57s | 12.00s | 9.43s | `0.13,0.42,0.97,0.70` | **PASS** |
|  | footer: Selecionar o SQL do MonthlyJob — Na lista, escolha o arquivo com Detected = MonthlyJob. / Isso confirma que os dois marcado | | | | | | | | |
| `26_mj_schema` | Schema (MonthlyJob) | 00:04:58,133 | 00:04:59,967 | 00:05:08,133 | 1.83s | 10.00s | 8.17s | `0.18,0.60,0.98,0.72` | **PASS** |
|  | footer: Schema (MonthlyJob) — Define o schema da tabela de resultado. / Informe o schema correto do seu trabalho. | | | | | | | | |
| `27_mj_table` | Table Name (MonthlyJob) | 00:05:08,467 | 00:05:10,967 | 00:05:20,467 | 2.50s | 12.00s | 9.50s | `0.18,0.66,0.98,0.78` | **PASS** |
|  | footer: Table Name (MonthlyJob) — Nome da tabela de resultado, com o prefixo do seu usuário. / Complete apenas o sufixo; o p | | | | | | | | |
| `28_mj_start` | Start Date | 00:05:20,800 | 00:05:22,567 | 00:05:30,800 | 1.77s | 10.00s | 8.23s | `0.18,0.72,0.98,0.84` | **PASS** |
|  | footer: Start Date — Data inicial do período do job (formato AAAA-MM-DD). / Define o primeiro mês a processar. | | | | | | | | |
| `29_mj_end` | End Date | 00:05:31,133 | 00:05:32,833 | 00:05:41,133 | 1.70s | 10.00s | 8.30s | `0.18,0.78,0.98,0.90` | **PASS** |
|  | footer: End Date — Data final do período (formato AAAA-MM-DD). / Deve ser igual ou posterior à Start Date. | | | | | | | | |
| `30_et_intro` | ExistingTable | 00:05:41,467 | 00:05:43,400 | 00:05:51,467 | 1.93s | 10.00s | 8.07s | `0.16,0.26,0.56,0.46` | **PASS** |
|  | footer: ExistingTable — Use quando os dados já estão em uma tabela e você / quer exportá-los, sem rodar um arquivo | | | | | | | | |
| `31_et_dest` | ExistingTable → Destination | 00:05:52,933 | 00:05:54,967 | 00:06:02,933 | 2.03s | 10.00s | 7.97s | `0.14,0.18,0.90,0.42` | **PASS** |
|  | footer: ExistingTable → Destination — Neste modo o destino permitido é apenas Csv. / Table e Table+Csv ficam indisponíveis. | | | | | | | | |
| `32_et_no_sql` | Sem SQL File | 00:06:03,267 | 00:06:05,200 | 00:06:13,267 | 1.93s | 10.00s | 8.07s | `0.10,0.28,0.90,0.56` | **PASS** |
|  | footer: Sem SQL File — A lista e o campo SQL File ficam ocultos. / A origem é a tabela existente, não um arquivo  | | | | | | | | |
| `33_et_schema_coe` | Schema → coe_enc | 00:06:13,600 | 00:06:15,533 | 00:06:23,600 | 1.93s | 10.00s | 8.07s | `0.20,0.58,0.76,0.74` | **PASS** |
|  | footer: Schema → coe_enc — Seleciona o schema coe_enc da tabela existente. / Use quando a tabela estiver nesse schema | | | | | | | | |
| `34_et_schema_aa` | Schema → aa_enc | 00:06:25,067 | 00:06:27,100 | 00:06:35,067 | 2.03s | 10.00s | 7.97s | `0.27,0.58,0.83,0.74` | **PASS** |
|  | footer: Schema → aa_enc — Seleciona o schema aa_enc da tabela existente. / É a opção padrão quando a tabela está em  | | | | | | | | |
| `35_et_schema_other` | Schema → other | 00:06:36,533 | 00:06:38,500 | 00:06:46,533 | 1.97s | 10.00s | 8.03s | `0.34,0.58,0.90,0.74` | **PASS** |
|  | footer: Schema → other — Use quando o schema não é coe_enc nem aa_enc. / Ao marcar other, aparece o campo Custom Sc | | | | | | | | |
| `36_et_custom` | Custom Schema | 00:06:48,000 | 00:06:49,567 | 00:06:58,000 | 1.57s | 10.00s | 8.43s | `0.18,0.66,0.98,0.78` | **PASS** |
|  | footer: Custom Schema — Digite o nome do schema personalizado. / Só aparece quando Schema = other. | | | | | | | | |
| `37_et_table` | Existing Table | 00:06:58,333 | 00:07:00,467 | 00:07:08,333 | 2.13s | 10.00s | 7.87s | `0.18,0.70,0.98,0.82` | **PASS** |
|  | footer: Existing Table — Informe só o nome da tabela (sem o schema). / Junto com o schema, forma a origem completa  | | | | | | | | |
| `38_rel_standard` | Combinação comum | 00:07:09,800 | 00:07:12,100 | 00:07:19,800 | 2.30s | 10.00s | 7.70s | `0.08,0.12,0.92,0.56` | **PASS** |
|  | footer: Combinação comum — SqlFile + Csv + arquivo .sql sem marcadores de data. / Fluxo típico para gerar um CSV a pa | | | | | | | | |
| `39_rel_monthly` | Combinação MonthlyJob | 00:07:21,267 | 00:07:23,500 | 00:07:31,267 | 2.23s | 10.00s | 7.77s | `0.08,0.10,0.92,0.66` | **PASS** |
|  | footer: Combinação MonthlyJob — MonthlyJob + Table + .sql com {date_inicio} e {date_fim} / + Schema, Table Name, Start Dat | | | | | | | | |
| `40_rel_existing` | Combinação ExistingTable | 00:07:31,600 | 00:07:33,767 | 00:07:41,600 | 2.17s | 10.00s | 7.83s | `0.08,0.12,0.92,0.60` | **PASS** |
|  | footer: Combinação ExistingTable — ExistingTable + Csv + Schema + Existing Table. / Não usa SQL File nem MonthlyJob ao mesmo  | | | | | | | | |
| `41_rel_incompat` | Combinações indisponíveis | 00:07:41,933 | 00:07:43,933 | 00:07:51,933 | 2.00s | 10.00s | 8.00s | `0.10,0.04,0.94,0.32` | **PASS** |
|  | footer: Combinações indisponíveis — MonthlyJob não aceita Csv ou Table+Csv. / ExistingTable não aceita Table ou Table+Csv. | | | | | | | | |
| `42_val_bad` | E-mail inválido | 00:07:52,267 | 00:07:54,133 | 00:08:02,267 | 1.87s | 10.00s | 8.13s | `0.18,0.68,0.98,0.84` | **PASS** |
|  | footer: E-mail inválido — Se o formato estiver incorreto, o status mostra o problema. / Corrija antes de continuar. | | | | | | | | |
| `43_val_ok` | Formulário pronto | 00:08:02,600 | 00:08:04,700 | 00:08:12,600 | 2.10s | 10.00s | 7.90s | `0.42,0.84,0.98,0.95` | **PASS** |
|  | footer: Formulário pronto — Com os dados corrigidos, o status volta a Ready to launch. / Revise origem, destino, arqui | | | | | | | | |
| `44_preview` | Preview SQL | 00:08:12,933 | 00:08:15,067 | 00:08:22,933 | 2.13s | 10.00s | 7.87s | `0.30,0.20,0.94,0.76` | **PASS** |
|  | footer: Preview SQL — Mostra o conteúdo que será usado no job. / Confira se a consulta e o destino estão correto | | | | | | | | |
| `45_checklist` | Antes de iniciar, confirme: | 00:08:24,067 | 00:08:26,733 | 00:08:36,067 | 2.67s | 12.00s | 9.33s | `0.08,0.12,0.92,0.78` | **PASS** |
|  | footer: Antes de iniciar, confirme: — • origem e destino; / • arquivo ou tabela selecionados; / • fila de execução; / • opções a | | | | | | | | |
| `46_confirm` | Launch Job | 00:08:36,400 | 00:08:38,333 | 00:08:46,400 | 1.93s | 10.00s | 8.07s | `0.14,0.27,0.86,0.83` | **PASS** |
|  | footer: Launch Job — Inicia o job com as configurações revisadas. / Leia o resumo e confirme apenas se estiver  | | | | | | | | |
| `47_launched` | Job enviado | 00:08:47,867 | 00:08:49,533 | 00:08:57,867 | 1.67s | 10.00s | 8.33s | `0.15,0.52,0.95,0.88` | **PASS** |
|  | footer: Job enviado — O job foi enviado pelo Dispatch. / Acompanhe o andamento na tela de monitoramento. | | | | | | | | |
| `48_overview` | Overview | 00:08:58,200 | 00:08:59,700 | 00:09:08,200 | 1.50s | 10.00s | 8.50s | `0.02,0.06,0.28,0.38` | **PASS** |
|  | footer: Overview — Após o envio, acompanhe o status do job no Overview. | | | | | | | | |
| `49_close` | Resumo | 00:09:09,333 | 00:09:12,333 | 00:09:21,333 | 3.00s | 12.00s | 9.00s | `0.08,0.12,0.92,0.78` | **PASS** |
|  | footer: Resumo — Na aba New Job, você: / 1. define a execução; / 2. revisa as configurações; / 3. inicia o  | | | | | | | | |

Instructional scenes: 50
10s scenes: 38
12s scenes: 12
Min scene: 10.00s
Max scene: 12.00s

**Overall: PASS**