# Footer timing validation

Required hold: **15.0s** (static, after full message visible).

| Scene | Start | End | Duration | Result |
|---|---|---|---|---|
| `01_open` | 00:00:00,000 | 00:00:15,000 | 15.00s | **PASS** |
|  | footer: Dispatch (Robocop) — Como utilizar a aba New Job / Configure e inicie um novo job passo a passo. | | | |
| `02_purpose_a` | 00:00:15,400 | 00:00:30,400 | 15.00s | **PASS** |
|  | footer: Para que serve a aba New Job — Ela permite configurar e iniciar uma nova execução no Dispatch. | | | |
| `02_purpose_b` | 00:00:30,800 | 00:00:45,800 | 15.00s | **PASS** |
|  | footer: O que você decide aqui — Você escolhe a origem dos dados, o destino do resultado, / a consulta e as opçõe | | | |
| `03_matrix` | 00:00:46,200 | 00:01:01,200 | 15.00s | **PASS** |
|  | footer: Source × Destination — Tabela de referência com as combinações permitidas. / Consulte-a antes de escolh | | | |
| `04_detected` | 00:01:03,733 | 00:01:18,733 | 15.00s | **PASS** |
|  | footer: Detected source — Mostra o tipo identificado no arquivo SQL selecionado. / Confirme se corresponde | | | |
| `05_source_intro` | 00:01:19,133 | 00:01:34,133 | 15.00s | **PASS** |
|  | footer: Source — Define de onde os dados do job serão obtidos. / É a primeira decisão do formulár | | | |
| `06_source_sqlfile` | 00:01:34,533 | 00:01:49,533 | 15.00s | **PASS** |
|  | footer: Source → SqlFile — Use quando a consulta está em um arquivo .sql simples. / O Dispatch executa essa | | | |
| `07_dest_intro` | 00:01:52,067 | 00:02:07,067 | 15.00s | **PASS** |
|  | footer: Destination — Define onde o resultado do job será armazenado. / A escolha depende da origem se | | | |
| `08_dest_table` | 00:02:07,467 | 00:02:22,467 | 15.00s | **PASS** |
|  | footer: Destination → Table — Salva o resultado em uma tabela. / Use quando precisar consultar o resultado dep | | | |
| `09_dest_csv` | 00:02:25,000 | 00:02:40,000 | 15.00s | **PASS** |
|  | footer: Destination → Csv — Gera um arquivo CSV na pasta de onde você abriu o Dispatch. / Use quando o resul | | | |
| `10_dest_tablecsv` | 00:02:42,533 | 00:02:57,533 | 15.00s | **PASS** |
|  | footer: Destination → Table+Csv — Cria a tabela e também gera o CSV. / Use quando precisa dos dois formatos na mes | | | |
| `11_queue_a` | 00:03:00,067 | 00:03:15,067 | 15.00s | **PASS** |
|  | footer: Execution Queue — Indica a fila de processamento do job. / Sem marcação, o Dispatch escolhe automa | | | |
| `12_queue_b` | 00:03:15,467 | 00:03:30,467 | 15.00s | **PASS** |
|  | footer: Execution Queue — quando marcar — Marque uma ou mais filas só se o seu projeto indicar qual usar. / Várias filas s | | | |
| `13_sql_intro` | 00:03:33,000 | 00:03:48,000 | 15.00s | **PASS** |
|  | footer: SQL File — É a consulta que o job vai executar. / Para SqlFile e MonthlyJob, você precisa s | | | |
| `14_sql_picker` | 00:03:48,400 | 00:04:03,400 | 15.00s | **PASS** |
|  | footer: Lista de arquivos SQL — Mostra os arquivos .sql da pasta atual. / Selecione o arquivo do job para preenc | | | |
| `15_sql_verify` | 00:04:05,933 | 00:04:20,933 | 15.00s | **PASS** |
|  | footer: O que conferir no arquivo — Confirme o nome do arquivo e o tipo Detected na lista. / O caminho aparece no ca | | | |
| `16_sql_role` | 00:04:21,333 | 00:04:36,333 | 15.00s | **PASS** |
|  | footer: Papel do SQL File no job — Esse arquivo define quais dados serão lidos ou calculados. / Source e Destinatio | | | |
| `17_email` | 00:04:36,733 | 00:04:51,733 | 15.00s | **PASS** |
|  | footer: Email (notifications) — Recebe aviso quando o job terminar. / Deixe em branco se não quiser notificação. | | | |
| `18_subject` | 00:04:54,267 | 00:05:09,267 | 15.00s | **PASS** |
|  | footer: Subject (email) — Assunto do e-mail de notificação. / Use um texto curto que identifique o job. | | | |
| `19_status_bar` | 00:05:11,800 | 00:05:26,800 | 15.00s | **PASS** |
|  | footer: Status do formulário — Ready to launch indica que não há problemas bloqueantes. / Preview SQL e Launch  | | | |
| `20_mj_intro` | 00:05:27,200 | 00:05:42,200 | 15.00s | **PASS** |
|  | footer: MonthlyJob — Use quando a consulta precisa cobrir um intervalo de datas, / executando o perío | | | |
| `21_mj_dest` | 00:05:44,733 | 00:05:59,733 | 15.00s | **PASS** |
|  | footer: MonthlyJob → Destination — Com MonthlyJob, o destino permitido é apenas Table. / Csv e Table+Csv ficam indi | | | |
| `22_mj_sql_rule_a` | 00:05:59,733 | 00:06:14,733 | 15.00s | **PASS** |
|  | footer: SQL File no MonthlyJob — regra — O arquivo .sql precisa conter os dois marcadores: / {date_inicio} e {date_fim} | | | |
| `23_mj_sql_rule_b` | 00:06:14,733 | 00:06:29,733 | 15.00s | **PASS** |
|  | footer: Como conferir no arquivo — Abra o .sql e busque exatamente {date_inicio} e {date_fim}. / Se faltar um deles | | | |
| `24_mj_sql_rule_c` | 00:06:29,733 | 00:06:44,733 | 15.00s | **PASS** |
|  | footer: O que esses marcadores fazem — Eles reservam o início e o fim de cada mês no período informado. / O Dispatch pr | | | |
| `25_mj_picker` | 00:06:45,133 | 00:07:00,133 | 15.00s | **PASS** |
|  | footer: Selecionar o SQL do MonthlyJob — Na lista, escolha o arquivo com Detected = MonthlyJob. / Isso confirma que os do | | | |
| `26_mj_schema` | 00:07:02,667 | 00:07:17,667 | 15.00s | **PASS** |
|  | footer: Schema (MonthlyJob) — Define o schema da tabela de resultado. / Informe o schema correto do seu trabal | | | |
| `27_mj_table` | 00:07:18,067 | 00:07:33,067 | 15.00s | **PASS** |
|  | footer: Table Name (MonthlyJob) — Nome da tabela de resultado, com o prefixo do seu usuário. / Complete apenas o s | | | |
| `28_mj_start` | 00:07:33,467 | 00:07:48,467 | 15.00s | **PASS** |
|  | footer: Start Date — Data inicial do período do job (formato AAAA-MM-DD). / Define o primeiro mês a p | | | |
| `29_mj_end` | 00:07:48,867 | 00:08:03,867 | 15.00s | **PASS** |
|  | footer: End Date — Data final do período (formato AAAA-MM-DD). / Deve ser igual ou posterior à Star | | | |
| `30_et_intro` | 00:08:04,267 | 00:08:19,267 | 15.00s | **PASS** |
|  | footer: ExistingTable — Use quando os dados já estão em uma tabela e você / quer exportá-los, sem rodar  | | | |
| `31_et_dest` | 00:08:21,800 | 00:08:36,800 | 15.00s | **PASS** |
|  | footer: ExistingTable → Destination — Neste modo o destino permitido é apenas Csv. / Table e Table+Csv ficam indisponí | | | |
| `32_et_no_sql` | 00:08:37,200 | 00:08:52,200 | 15.00s | **PASS** |
|  | footer: Sem SQL File — A lista e o campo SQL File ficam ocultos. / A origem é a tabela existente, não u | | | |
| `33_et_schema_coe` | 00:08:52,600 | 00:09:07,600 | 15.00s | **PASS** |
|  | footer: Schema → coe_enc — Seleciona o schema coe_enc da tabela existente. / Use quando a tabela estiver ne | | | |
| `34_et_schema_aa` | 00:09:10,133 | 00:09:25,133 | 15.00s | **PASS** |
|  | footer: Schema → aa_enc — Seleciona o schema aa_enc da tabela existente. / É a opção padrão quando a tabel | | | |
| `35_et_schema_other` | 00:09:27,667 | 00:09:42,667 | 15.00s | **PASS** |
|  | footer: Schema → other — Use quando o schema não é coe_enc nem aa_enc. / Ao marcar other, aparece o campo | | | |
| `36_et_custom` | 00:09:45,200 | 00:10:00,200 | 15.00s | **PASS** |
|  | footer: Custom Schema — Digite o nome do schema personalizado. / Só aparece quando Schema = other. | | | |
| `37_et_table` | 00:10:00,600 | 00:10:15,600 | 15.00s | **PASS** |
|  | footer: Existing Table — Informe só o nome da tabela (sem o schema). / Junto com o schema, forma a origem | | | |
| `38_rel_standard` | 00:10:18,133 | 00:10:33,133 | 15.00s | **PASS** |
|  | footer: Combinação comum — SqlFile + Csv + arquivo .sql sem marcadores de data. / Fluxo típico para gerar u | | | |
| `39_rel_monthly` | 00:10:35,667 | 00:10:50,667 | 15.00s | **PASS** |
|  | footer: Combinação MonthlyJob — MonthlyJob + Table + .sql com {date_inicio} e {date_fim} / + Schema, Table Name, | | | |
| `40_rel_existing` | 00:10:51,067 | 00:11:06,067 | 15.00s | **PASS** |
|  | footer: Combinação ExistingTable — ExistingTable + Csv + Schema + Existing Table. / Não usa SQL File nem MonthlyJob | | | |
| `41_rel_incompat` | 00:11:06,467 | 00:11:21,467 | 15.00s | **PASS** |
|  | footer: Combinações indisponíveis — MonthlyJob não aceita Csv ou Table+Csv. / ExistingTable não aceita Table ou Tabl | | | |
| `42_val_bad` | 00:11:21,867 | 00:11:36,867 | 15.00s | **PASS** |
|  | footer: E-mail inválido — Se o formato estiver incorreto, o status mostra o problema. / Corrija antes de c | | | |
| `43_val_ok` | 00:11:37,267 | 00:11:52,267 | 15.00s | **PASS** |
|  | footer: Formulário pronto — Com os dados corrigidos, o status volta a Ready to launch. / Revise origem, dest | | | |
| `44_preview` | 00:11:52,667 | 00:12:07,667 | 15.00s | **PASS** |
|  | footer: Preview SQL — Mostra o conteúdo que será usado no job. / Confira se a consulta e o destino est | | | |
| `45_checklist` | 00:12:09,800 | 00:12:24,800 | 15.00s | **PASS** |
|  | footer: Antes de iniciar, confirme: — • origem e destino; / • arquivo ou tabela selecionados; / • fila de execução; /  | | | |
| `46_confirm` | 00:12:25,200 | 00:12:40,200 | 15.00s | **PASS** |
|  | footer: Launch Job — Inicia o job com as configurações revisadas. / Leia o resumo e confirme apenas s | | | |
| `47_launched` | 00:12:42,733 | 00:12:57,733 | 15.00s | **PASS** |
|  | footer: Job enviado — O job foi enviado pelo Dispatch. / Acompanhe o andamento na tela de monitorament | | | |
| `48_overview` | 00:12:58,133 | 00:13:13,133 | 15.00s | **PASS** |
|  | footer: Overview — Após o envio, acompanhe o status do job no Overview. | | | |
| `49_close` | 00:13:15,267 | 00:13:30,267 | 15.00s | **PASS** |
|  | footer: Resumo — Na aba New Job, você: / 1. define a execução; / 2. revisa as configurações; / 3. | | | |

Instructional footers: 50
Minimum instructional duration: 15.00s

**Overall: PASS**