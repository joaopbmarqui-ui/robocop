# Storyboard — Overview (typing + 5.0s hold, Carlito, 1920×1080)

Font: Carlito (Carlito-Regular.ttf). Body 38px / title 42px.
Calibri is not installed in this Linux environment. Using Carlito (fonts-crosextra-carlito), the OFL metric-compatible substitute.
Complete-text hold: exactly 5.0s after typing. Original chiptune BGM + UI blip.
Part 2 of the Dispatch onboarding series (after New Job).

## 01_open — Abertura

- **Elemento:** Dispatch (Robocop)
- **Targets:** (card)
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.12, 0.14, 0.88, 0.7]]
- **Final px boxes:** [[80, 100, 1840, 786]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Dispatch (Robocop) — Como utilizar a aba Overview. / Monitore e interprete seus jobs.
- **Typing:** 00:00:00,000 → 00:00:01,167 (1.17s)
- **Hold complete:** 00:00:01,167 → 00:00:06,167 (5.00s)
- **Spotlight group:** open (reused=False)
- **SFX / duck:** 00:00:00,000
- **Seta:** 00:00:01,167
- **Duração cena:** 6.17s
- **Manual review:** PASS
- **Evidência:** opening card

## 02_purpose — Abertura

- **Elemento:** O que é Overview
- **Targets:** jobs-title, jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.135, 0.0714, 0.555, 0.1]]
- **Final px boxes:** [[541, 52, 1027, 86]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** O que é Overview — Tela principal para acompanhar / jobs enviados e seu status.
- **Typing:** 00:00:06,467 → 00:00:07,533 (1.07s)
- **Hold complete:** 00:00:07,533 → 00:00:12,533 (5.00s)
- **Spotlight group:** purpose (reused=False)
- **SFX / duck:** 00:00:06,467
- **Seta:** 00:00:07,533
- **Duração cena:** 6.07s
- **Manual review:** PASS
- **Evidência:** DashboardScreen

## 20_strip_what — Status strip

- **Elemento:** O que é
- **Targets:** status-strip
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.0429, 0.46, 0.0571]]
- **Final px boxes:** [[549, 31, 917, 49]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** O que é — A faixa superior resume autenticação / e o monitoramento dos jobs.
- **Typing:** 00:00:12,833 → 00:00:13,867 (1.03s)
- **Hold complete:** 00:00:13,867 → 00:00:18,867 (5.00s)
- **Spotlight group:** status-strip (reused=False)
- **SFX / duck:** 00:00:12,833
- **Seta:** 00:00:13,867
- **Duração cena:** 6.03s
- **Manual review:** PASS
- **Evidência:** #status-strip

## 20b_strip_learn — Status strip

- **Elemento:** O que você aprende aqui
- **Targets:** status-strip
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.0429, 0.46, 0.0571]]
- **Final px boxes:** [[549, 31, 917, 49]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** O que você aprende aqui — Em um olhar: autenticação, execução / e histórico dos últimos 7 dias.
- **Typing:** 00:00:18,867 → 00:00:20,167 (1.30s)
- **Hold complete:** 00:00:20,167 → 00:00:25,167 (5.00s)
- **Spotlight group:** status-strip (reused=True)
- **SFX / duck:** 00:00:18,867
- **Seta:** 00:00:20,167
- **Duração cena:** 6.30s
- **Manual review:** PASS
- **Evidência:** _update_status_strip

## 21_krb_what — Status strip

- **Elemento:** KERBEROS
- **Targets:** status-strip
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.0429, 0.215, 0.0571]]
- **Final px boxes:** [[549, 31, 640, 49]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** KERBEROS — Indica se sua autenticação / está disponível para executar jobs.
- **Typing:** 00:00:25,467 → 00:00:26,467 (1.00s)
- **Hold complete:** 00:00:26,467 → 00:00:31,467 (5.00s)
- **Spotlight group:** krb (reused=False)
- **SFX / duck:** 00:00:25,467
- **Seta:** 00:00:26,467
- **Duração cena:** 6.00s
- **Manual review:** PASS
- **Evidência:** KERBEROS label

## 21b_krb_action — Status strip

- **Elemento:** Se estiver MISSING ou curto
- **Targets:** status-strip
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.0429, 0.215, 0.0571]]
- **Final px boxes:** [[549, 31, 640, 49]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Se estiver MISSING ou curto — Abra um novo terminal e execute: / kinit
- **Typing:** 00:00:31,467 → 00:00:32,467 (1.00s)
- **Hold complete:** 00:00:32,467 → 00:00:37,467 (5.00s)
- **Spotlight group:** krb (reused=True)
- **SFX / duck:** 00:00:31,467
- **Seta:** 00:00:32,467
- **Duração cena:** 6.00s
- **Manual review:** PASS
- **Evidência:** kinit recovery

## 21c_krb_password — Status strip

- **Elemento:** Senha
- **Targets:** status-strip
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.0429, 0.215, 0.0571]]
- **Final px boxes:** [[549, 31, 640, 49]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Senha — Informe sua senha Windows / quando o terminal solicitar.
- **Typing:** 00:00:37,467 → 00:00:38,467 (1.00s)
- **Hold complete:** 00:00:38,467 → 00:00:43,467 (5.00s)
- **Spotlight group:** krb (reused=True)
- **SFX / duck:** 00:00:37,467
- **Seta:** 00:00:38,467
- **Duração cena:** 6.00s
- **Manual review:** PASS
- **Evidência:** kinit password prompt

## 22_running_what — Status strip

- **Elemento:** RUNNING
- **Targets:** status-strip
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.235, 0.0429, 0.3, 0.0571]]
- **Final px boxes:** [[657, 31, 736, 49]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** RUNNING — Quantos jobs estão em execução agora, / em relação ao limite de vagas.
- **Typing:** 00:00:43,767 → 00:00:44,867 (1.10s)
- **Hold complete:** 00:00:44,867 → 00:00:49,867 (5.00s)
- **Spotlight group:** running-cap (reused=False)
- **SFX / duck:** 00:00:43,767
- **Seta:** 00:00:44,867
- **Duração cena:** 6.10s
- **Manual review:** PASS
- **Evidência:** RUNNING / RUNNING_CAP

## 22b_running_learn — Status strip

- **Elemento:** O que você aprende aqui
- **Targets:** status-strip
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.235, 0.0429, 0.3, 0.0571]]
- **Final px boxes:** [[657, 31, 736, 49]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** O que você aprende aqui — O limite é 2 vagas. Pending e Running / ocupam vaga de execução.
- **Typing:** 00:00:49,867 → 00:00:51,100 (1.23s)
- **Hold complete:** 00:00:51,100 → 00:00:56,100 (5.00s)
- **Spotlight group:** running-cap (reused=True)
- **SFX / duck:** 00:00:49,867
- **Seta:** 00:00:51,100
- **Duração cena:** 6.23s
- **Manual review:** PASS
- **Evidência:** jobs.RUNNING_CAP

## 23_finished_what — Status strip

- **Elemento:** FINISHED 7D
- **Targets:** status-strip
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.32, 0.0429, 0.385, 0.0571]]
- **Final px boxes:** [[753, 31, 832, 49]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** FINISHED 7D — Histórico de jobs com sucesso / nos últimos 7 dias.
- **Typing:** 00:00:56,400 → 00:00:57,400 (1.00s)
- **Hold complete:** 00:00:57,400 → 00:01:02,400 (5.00s)
- **Spotlight group:** finished (reused=False)
- **SFX / duck:** 00:00:56,400
- **Seta:** 00:00:57,400
- **Duração cena:** 6.00s
- **Manual review:** PASS
- **Evidência:** FINISHED 7D

## 23b_finished_learn — Status strip

- **Elemento:** O que você aprende aqui
- **Targets:** status-strip
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.32, 0.0429, 0.385, 0.0571]]
- **Final px boxes:** [[753, 31, 832, 49]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** O que você aprende aqui — Permite ver sete dias de histórico / e confirmar entregas recentes.
- **Typing:** 00:01:02,400 → 00:01:03,667 (1.27s)
- **Hold complete:** 00:01:03,667 → 00:01:08,667 (5.00s)
- **Spotlight group:** finished (reused=True)
- **SFX / duck:** 00:01:02,400
- **Seta:** 00:01:03,667
- **Duração cena:** 6.27s
- **Manual review:** PASS
- **Evidência:** Succeeded count / ACTIVE_WINDOW

## 24_failed_what — Status strip

- **Elemento:** FAILED 7D
- **Targets:** status-strip
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.405, 0.0429, 0.46, 0.0571]]
- **Final px boxes:** [[849, 31, 917, 49]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** FAILED 7D — Histórico de jobs que falharam / nos últimos 7 dias.
- **Typing:** 00:01:08,967 → 00:01:09,967 (1.00s)
- **Hold complete:** 00:01:09,967 → 00:01:14,967 (5.00s)
- **Spotlight group:** failed-count (reused=False)
- **SFX / duck:** 00:01:08,967
- **Seta:** 00:01:09,967
- **Duração cena:** 6.00s
- **Manual review:** PASS
- **Evidência:** FAILED 7D

## 24b_failed_action — Status strip

- **Elemento:** O que fazer
- **Targets:** status-strip
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.405, 0.0429, 0.46, 0.0571]]
- **Final px boxes:** [[849, 31, 917, 49]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** O que fazer — Se o número subir, revise os jobs / FAILED antes de enviar outros.
- **Typing:** 00:01:14,967 → 00:01:16,067 (1.10s)
- **Hold complete:** 00:01:16,067 → 00:01:21,067 (5.00s)
- **Spotlight group:** failed-count (reused=True)
- **SFX / duck:** 00:01:14,967
- **Seta:** 00:01:16,067
- **Duração cena:** 6.10s
- **Manual review:** PASS
- **Evidência:** Failed count

## 30_title_what — Lista

- **Elemento:** Lista de jobs
- **Targets:** jobs-title
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.135, 0.0714, 0.305, 0.0857]]
- **Final px boxes:** [[543, 54, 742, 72]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Lista de jobs — Jobs · running first · last 7 dias: / lista do histórico recente.
- **Typing:** 00:01:21,367 → 00:01:22,467 (1.10s)
- **Hold complete:** 00:01:22,467 → 00:01:27,467 (5.00s)
- **Spotlight group:** jobs-title (reused=False)
- **SFX / duck:** 00:01:21,367
- **Seta:** 00:01:22,467
- **Duração cena:** 6.10s
- **Manual review:** PASS
- **Evidência:** #jobs-title

## 30b_title_learn — Lista

- **Elemento:** O que você aprende aqui
- **Targets:** jobs-title
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.135, 0.0714, 0.305, 0.0857]]
- **Final px boxes:** [[543, 54, 742, 72]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** O que você aprende aqui — Execução no topo; a janela cobre / sete dias de monitoramento.
- **Typing:** 00:01:27,467 → 00:01:28,667 (1.20s)
- **Hold complete:** 00:01:28,667 → 00:01:33,667 (5.00s)
- **Spotlight group:** jobs-title (reused=True)
- **SFX / duck:** 00:01:27,467
- **Seta:** 00:01:28,667
- **Duração cena:** 6.20s
- **Manual review:** PASS
- **Evidência:** active_jobs ACTIVE_WINDOW

## 31_empty_what — Lista

- **Elemento:** Lista vazia
- **Targets:** jobs-empty
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.0857, 0.99, 0.1286]]
- **Final px boxes:** [[547, 64, 1519, 109]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Lista vazia — Quando não há jobs nos últimos 7 dias, / a tela orienta a criar um novo.
- **Typing:** 00:01:33,967 → 00:01:35,133 (1.17s)
- **Hold complete:** 00:01:35,133 → 00:01:40,133 (5.00s)
- **Spotlight group:** empty (reused=False)
- **SFX / duck:** 00:01:33,967
- **Seta:** 00:01:35,133
- **Duração cena:** 6.17s
- **Manual review:** PASS
- **Evidência:** #jobs-empty

## 31b_empty_action — Lista

- **Elemento:** O que fazer
- **Targets:** jobs-empty
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.0857, 0.99, 0.1286]]
- **Final px boxes:** [[547, 64, 1519, 109]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** O que fazer — Pressione N ou New Job para / enviar a primeira execução.
- **Typing:** 00:01:40,133 → 00:01:41,133 (1.00s)
- **Hold complete:** 00:01:41,133 → 00:01:46,133 (5.00s)
- **Spotlight group:** empty (reused=True)
- **SFX / duck:** 00:01:40,133
- **Seta:** 00:01:41,133
- **Duração cena:** 6.00s
- **Manual review:** PASS
- **Evidência:** No jobs in the last 7 days

## 40_table_what — Tabela

- **Elemento:** O que é
- **Targets:** jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.0857, 0.555, 0.1714]]
- **Final px boxes:** [[547, 64, 1027, 143]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** O que é — A tabela lista cada job com identidade, / origem, destino, estado e tempo.
- **Typing:** 00:01:46,433 → 00:01:47,567 (1.13s)
- **Hold complete:** 00:01:47,567 → 00:01:52,567 (5.00s)
- **Spotlight group:** table (reused=False)
- **SFX / duck:** 00:01:46,433
- **Seta:** 00:01:47,567
- **Duração cena:** 6.13s
- **Manual review:** PASS
- **Evidência:** #jobs-table

## 40b_table_learn — Tabela

- **Elemento:** O que você aprende aqui
- **Targets:** jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.0857, 0.555, 0.1714]]
- **Final px boxes:** [[547, 64, 1027, 143]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** O que você aprende aqui — Percorra as linhas para achar / sucesso, execução ou problemas.
- **Typing:** 00:01:52,567 → 00:01:53,767 (1.20s)
- **Hold complete:** 00:01:53,767 → 00:01:58,767 (5.00s)
- **Spotlight group:** table (reused=True)
- **SFX / duck:** 00:01:52,567
- **Seta:** 00:01:53,767
- **Duração cena:** 6.20s
- **Manual review:** PASS
- **Evidência:** DataTable

## 41_col_id — Colunas

- **Elemento:** Coluna ID
- **Targets:** jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.0857, 0.22, 0.1714]]
- **Final px boxes:** [[548, 65, 647, 142]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Coluna ID — Identifica o job de forma curta / para localizar e abrir detalhes.
- **Typing:** 00:01:59,067 → 00:02:00,133 (1.07s)
- **Hold complete:** 00:02:00,133 → 00:02:05,133 (5.00s)
- **Spotlight group:** col-id (reused=False)
- **SFX / duck:** 00:01:59,067
- **Seta:** 00:02:00,133
- **Duração cena:** 6.07s
- **Manual review:** PASS
- **Evidência:** format_job_id

## 41b_col_id_use — Colunas

- **Elemento:** Como usar
- **Targets:** jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.14, 0.0857, 0.22, 0.1714]]
- **Final px boxes:** [[548, 65, 647, 142]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Como usar — Use o ID para filtrar ou / confirmar qual execução está vendo.
- **Typing:** 00:02:05,133 → 00:02:06,133 (1.00s)
- **Hold complete:** 00:02:06,133 → 00:02:11,133 (5.00s)
- **Spotlight group:** col-id (reused=True)
- **SFX / duck:** 00:02:05,133
- **Seta:** 00:02:06,133
- **Duração cena:** 6.00s
- **Manual review:** PASS
- **Evidência:** ID column

## 42_col_src — Colunas

- **Elemento:** Coluna Source
- **Targets:** jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.22, 0.0857, 0.31, 0.1714]]
- **Final px boxes:** [[639, 65, 748, 142]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Coluna Source — Mostra a origem do job: / arquivo SQL, tabela ou tipo.
- **Typing:** 00:02:11,433 → 00:02:12,433 (1.00s)
- **Hold complete:** 00:02:12,433 → 00:02:17,433 (5.00s)
- **Spotlight group:** col-src (reused=False)
- **SFX / duck:** 00:02:11,433
- **Seta:** 00:02:12,433
- **Duração cena:** 6.00s
- **Manual review:** PASS
- **Evidência:** _source_label

## 42b_col_src_use — Colunas

- **Elemento:** Como usar
- **Targets:** jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.22, 0.0857, 0.31, 0.1714]]
- **Final px boxes:** [[639, 65, 748, 142]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Como usar — Confirme se a origem corresponde / ao job que você esperava monitorar.
- **Typing:** 00:02:17,433 → 00:02:18,533 (1.10s)
- **Hold complete:** 00:02:18,533 → 00:02:23,533 (5.00s)
- **Spotlight group:** col-src (reused=True)
- **SFX / duck:** 00:02:17,433
- **Seta:** 00:02:18,533
- **Duração cena:** 6.10s
- **Manual review:** PASS
- **Evidência:** Source column

## 43_col_dst — Colunas

- **Elemento:** Coluna Destination
- **Targets:** jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.31, 0.0857, 0.415, 0.1714]]
- **Final px boxes:** [[740, 65, 867, 142]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Coluna Destination — Mostra para onde o resultado / foi ou será entregue.
- **Typing:** 00:02:23,833 → 00:02:24,833 (1.00s)
- **Hold complete:** 00:02:24,833 → 00:02:29,833 (5.00s)
- **Spotlight group:** col-dst (reused=False)
- **SFX / duck:** 00:02:23,833
- **Seta:** 00:02:24,833
- **Duração cena:** 6.00s
- **Manual review:** PASS
- **Evidência:** _dest_label

## 43b_col_dst_use — Colunas

- **Elemento:** Como usar
- **Targets:** jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.31, 0.0857, 0.415, 0.1714]]
- **Final px boxes:** [[740, 65, 867, 142]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Como usar — Verifique schema.tabela ou Csv / antes de validar o resultado.
- **Typing:** 00:02:29,833 → 00:02:30,833 (1.00s)
- **Hold complete:** 00:02:30,833 → 00:02:35,833 (5.00s)
- **Spotlight group:** col-dst (reused=True)
- **SFX / duck:** 00:02:29,833
- **Seta:** 00:02:30,833
- **Duração cena:** 6.00s
- **Manual review:** PASS
- **Evidência:** Destination column

## 44_col_state — Colunas

- **Elemento:** Coluna State
- **Targets:** jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.415, 0.0857, 0.51, 0.1714]]
- **Final px boxes:** [[859, 65, 975, 142]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Coluna State — Mostra o estado atual do job / com símbolo e rótulo em destaque.
- **Typing:** 00:02:36,133 → 00:02:37,200 (1.07s)
- **Hold complete:** 00:02:37,200 → 00:02:42,200 (5.00s)
- **Spotlight group:** col-state (reused=False)
- **SFX / duck:** 00:02:36,133
- **Seta:** 00:02:37,200
- **Duração cena:** 6.07s
- **Manual review:** PASS
- **Evidência:** format_state

## 44b_col_state_learn — Colunas

- **Elemento:** O que você aprende aqui
- **Targets:** jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.415, 0.0857, 0.51, 0.1714]]
- **Final px boxes:** [[859, 65, 975, 142]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** O que você aprende aqui — Dá para ver rápido se está aguardando, / rodando, ok ou precisa atenção.
- **Typing:** 00:02:42,200 → 00:02:43,533 (1.33s)
- **Hold complete:** 00:02:43,533 → 00:02:48,533 (5.00s)
- **Spotlight group:** col-state (reused=True)
- **SFX / duck:** 00:02:42,200
- **Seta:** 00:02:43,533
- **Duração cena:** 6.33s
- **Manual review:** PASS
- **Evidência:** State column

## 50_st_pending — Estados

- **Elemento:** PENDING
- **Targets:** jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.415, 0.1143, 0.51, 0.1286]]
- **Final px boxes:** [[860, 89, 974, 107]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** PENDING — O job foi aceito e aguarda / início da execução.
- **Typing:** 00:02:48,833 → 00:02:49,833 (1.00s)
- **Hold complete:** 00:02:49,833 → 00:02:54,833 (5.00s)
- **Spotlight group:** state-pending (reused=False)
- **SFX / duck:** 00:02:48,833
- **Seta:** 00:02:49,833
- **Duração cena:** 6.00s
- **Manual review:** PASS
- **Evidência:** Pending

## 50b_st_pending_act — Estados

- **Elemento:** O que fazer
- **Targets:** jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.415, 0.1143, 0.51, 0.1286]]
- **Final px boxes:** [[860, 89, 974, 107]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** O que fazer — Em geral, espere. Confira se / há vaga livre na faixa RUNNING.
- **Typing:** 00:02:54,833 → 00:02:55,867 (1.03s)
- **Hold complete:** 00:02:55,867 → 00:03:00,867 (5.00s)
- **Spotlight group:** state-pending (reused=True)
- **SFX / duck:** 00:02:54,833
- **Seta:** 00:02:55,867
- **Duração cena:** 6.03s
- **Manual review:** PASS
- **Evidência:** Pending slot

## 51_st_running — Estados

- **Elemento:** RUNNING
- **Targets:** jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.415, 0.1, 0.51, 0.1143]]
- **Final px boxes:** [[860, 78, 974, 95]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** RUNNING — O job está em execução agora. / Acompanhe o progresso no painel.
- **Typing:** 00:03:01,167 → 00:03:02,167 (1.00s)
- **Hold complete:** 00:03:02,167 → 00:03:07,167 (5.00s)
- **Spotlight group:** state-running (reused=False)
- **SFX / duck:** 00:03:01,167
- **Seta:** 00:03:02,167
- **Duração cena:** 6.00s
- **Manual review:** PASS
- **Evidência:** Running

## 51b_st_running_act — Estados

- **Elemento:** O que fazer
- **Targets:** jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.415, 0.1, 0.51, 0.1143]]
- **Final px boxes:** [[860, 78, 974, 95]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** O que fazer — Monitore o log. Só cancele se / realmente precisar interromper.
- **Typing:** 00:03:07,167 → 00:03:08,200 (1.03s)
- **Hold complete:** 00:03:08,200 → 00:03:13,200 (5.00s)
- **Spotlight group:** state-running (reused=True)
- **SFX / duck:** 00:03:07,167
- **Seta:** 00:03:08,200
- **Duração cena:** 6.03s
- **Manual review:** PASS
- **Evidência:** Cancel Running only

## 52_st_ok — Estados

- **Elemento:** SUCCEEDED
- **Targets:** jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.415, 0.1571, 0.51, 0.1714]]
- **Final px boxes:** [[860, 124, 974, 141]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** SUCCEEDED — O job terminou com sucesso. / O resultado está disponível.
- **Typing:** 00:03:13,500 → 00:03:14,500 (1.00s)
- **Hold complete:** 00:03:14,500 → 00:03:19,500 (5.00s)
- **Spotlight group:** state-ok (reused=False)
- **SFX / duck:** 00:03:13,500
- **Seta:** 00:03:14,500
- **Duração cena:** 6.00s
- **Manual review:** PASS
- **Evidência:** Succeeded

## 52b_st_ok_act — Estados

- **Elemento:** O que fazer
- **Targets:** jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.415, 0.1571, 0.51, 0.1714]]
- **Final px boxes:** [[860, 124, 974, 141]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** O que fazer — Valide a entrega (tabela ou CSV) / conforme o Destination do job.
- **Typing:** 00:03:19,500 → 00:03:20,567 (1.07s)
- **Hold complete:** 00:03:20,567 → 00:03:25,567 (5.00s)
- **Spotlight group:** state-ok (reused=True)
- **SFX / duck:** 00:03:19,500
- **Seta:** 00:03:20,567
- **Duração cena:** 6.07s
- **Manual review:** PASS
- **Evidência:** Succeeded

## 53_st_fail — Estados

- **Elemento:** FAILED
- **Targets:** jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.415, 0.1429, 0.51, 0.1571]]
- **Final px boxes:** [[860, 112, 974, 130]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** FAILED — O job falhou. Pode aparecer um código / (ex.: SYNTAX) para orientar a análise.
- **Typing:** 00:03:25,867 → 00:03:27,067 (1.20s)
- **Hold complete:** 00:03:27,067 → 00:03:32,067 (5.00s)
- **Spotlight group:** state-fail (reused=False)
- **SFX / duck:** 00:03:25,867
- **Seta:** 00:03:27,067
- **Duração cena:** 6.20s
- **Manual review:** PASS
- **Evidência:** Failed + classify

## 53b_st_fail_act — Estados

- **Elemento:** O que fazer
- **Targets:** jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.415, 0.1429, 0.51, 0.1571]]
- **Final px boxes:** [[860, 112, 974, 130]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** O que fazer — Abra View Logs, entenda a causa / e corrija antes de reenviar.
- **Typing:** 00:03:32,067 → 00:03:33,100 (1.03s)
- **Hold complete:** 00:03:33,100 → 00:03:38,100 (5.00s)
- **Spotlight group:** state-fail (reused=True)
- **SFX / duck:** 00:03:32,067
- **Seta:** 00:03:33,100
- **Duração cena:** 6.03s
- **Manual review:** PASS
- **Evidência:** View Logs

## 54_st_cancel — Estados

- **Elemento:** CANCELLED
- **Targets:** jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.415, 0.1286, 0.51, 0.1429]]
- **Final px boxes:** [[860, 101, 974, 118]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** CANCELLED — A execução foi cancelada. / Não houve conclusão bem-sucedida.
- **Typing:** 00:03:38,400 → 00:03:39,400 (1.00s)
- **Hold complete:** 00:03:39,400 → 00:03:44,400 (5.00s)
- **Spotlight group:** state-cancel (reused=False)
- **SFX / duck:** 00:03:38,400
- **Seta:** 00:03:39,400
- **Duração cena:** 6.00s
- **Manual review:** PASS
- **Evidência:** Cancelled

## 54b_st_cancel_act — Estados

- **Elemento:** O que fazer
- **Targets:** jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.415, 0.1286, 0.51, 0.1429]]
- **Final px boxes:** [[860, 101, 974, 118]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** O que fazer — Confirme se o cancelamento / foi intencional; reenvie se precisar.
- **Typing:** 00:03:44,400 → 00:03:45,500 (1.10s)
- **Hold complete:** 00:03:45,500 → 00:03:50,500 (5.00s)
- **Spotlight group:** state-cancel (reused=True)
- **SFX / duck:** 00:03:44,400
- **Seta:** 00:03:45,500
- **Duração cena:** 6.10s
- **Manual review:** PASS
- **Evidência:** Cancelled

## 55_col_elapsed — Colunas

- **Elemento:** Coluna Elapsed
- **Targets:** jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.51, 0.0857, 0.555, 0.1714]]
- **Final px boxes:** [[967, 65, 1026, 142]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Coluna Elapsed — Tempo decorrido: em Running conta / desde o início; nos demais, a duração.
- **Typing:** 00:03:50,800 → 00:03:52,033 (1.23s)
- **Hold complete:** 00:03:52,033 → 00:03:57,033 (5.00s)
- **Spotlight group:** col-elapsed (reused=False)
- **SFX / duck:** 00:03:50,800
- **Seta:** 00:03:52,033
- **Duração cena:** 6.23s
- **Manual review:** PASS
- **Evidência:** format_elapsed

## 55b_col_elapsed_use — Colunas

- **Elemento:** Como usar
- **Targets:** jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.51, 0.0857, 0.555, 0.1714]]
- **Final px boxes:** [[967, 65, 1026, 142]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Como usar — Compare duração esperada e detecte / jobs longos que merecem atenção.
- **Typing:** 00:03:57,033 → 00:03:58,133 (1.10s)
- **Hold complete:** 00:03:58,133 → 00:04:03,133 (5.00s)
- **Spotlight group:** col-elapsed (reused=True)
- **SFX / duck:** 00:03:57,033
- **Seta:** 00:03:58,133
- **Duração cena:** 6.10s
- **Manual review:** PASS
- **Evidência:** Elapsed

## 60_filter_what — Filtro

- **Elemento:** Filtro
- **Targets:** jobs-filter
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.135, 0.0857, 0.995, 0.1286]]
- **Final px boxes:** [[542, 65, 1524, 108]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Filtro — Pressione / para filtrar a lista / por id, arquivo, tabela ou estado.
- **Typing:** 00:04:03,433 → 00:04:04,500 (1.07s)
- **Hold complete:** 00:04:04,500 → 00:04:09,500 (5.00s)
- **Spotlight group:** filter (reused=False)
- **SFX / duck:** 00:04:03,433
- **Seta:** 00:04:04,500
- **Duração cena:** 6.07s
- **Manual review:** PASS
- **Evidência:** #jobs-filter

## 60b_filter_when — Filtro

- **Elemento:** Quando usar
- **Targets:** jobs-filter
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.135, 0.0857, 0.995, 0.1286]]
- **Final px boxes:** [[542, 65, 1524, 108]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Quando usar — Use para achar rápido um job / ou isolar só FAILED / RUNNING.
- **Typing:** 00:04:09,500 → 00:04:10,500 (1.00s)
- **Hold complete:** 00:04:10,500 → 00:04:15,500 (5.00s)
- **Spotlight group:** filter (reused=True)
- **SFX / duck:** 00:04:09,500
- **Seta:** 00:04:10,500
- **Duração cena:** 6.00s
- **Manual review:** PASS
- **Evidência:** action_filter_jobs

## 61_filter_ex — Filtro

- **Elemento:** Exemplo
- **Targets:** jobs-filter, jobs-table
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.135, 0.0857, 0.995, 0.1286], [0.14, 0.1286, 0.555, 0.1571]]
- **Final px boxes:** [[541, 64, 1525, 109], [547, 99, 1027, 132]]
- **Cutouts:** 2
- **Overlay opacity:** 170/255
- **Diálogo:** Exemplo — Digite failed para ver só falhas. / Esc limpa o filtro e restaura a lista.
- **Typing:** 00:04:15,800 → 00:04:16,933 (1.13s)
- **Hold complete:** 00:04:16,933 → 00:04:21,933 (5.00s)
- **Spotlight group:** filter-ex (reused=False)
- **SFX / duck:** 00:04:15,800
- **Seta:** 00:04:16,933
- **Duração cena:** 6.13s
- **Manual review:** PASS
- **Evidência:** Esc clear_filter

## 70_detail_what — Detalhe

- **Elemento:** Painel de detalhe
- **Targets:** detail-pane
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.135, 0.8143, 0.995, 0.9]]
- **Final px boxes:** [[541, 654, 1525, 734]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Painel de detalhe — Mostra um resumo do job selecionado / e as últimas linhas do log.
- **Typing:** 00:04:23,167 → 00:04:24,333 (1.17s)
- **Hold complete:** 00:04:24,333 → 00:04:29,333 (5.00s)
- **Spotlight group:** detail (reused=False)
- **SFX / duck:** 00:04:23,167
- **Seta:** 00:04:24,333
- **Duração cena:** 6.17s
- **Manual review:** PASS
- **Evidência:** #detail-pane

## 70b_detail_learn — Detalhe

- **Elemento:** O que você aprende aqui
- **Targets:** detail-pane
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.135, 0.8143, 0.995, 0.9]]
- **Final px boxes:** [[541, 654, 1525, 734]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** O que você aprende aqui — Sem sair da Overview, vê se o job / avança ou se já há erro no log.
- **Typing:** 00:04:29,333 → 00:04:30,600 (1.27s)
- **Hold complete:** 00:04:30,600 → 00:04:35,600 (5.00s)
- **Spotlight group:** detail (reused=True)
- **SFX / duck:** 00:04:29,333
- **Seta:** 00:04:30,600
- **Duração cena:** 6.27s
- **Manual review:** PASS
- **Evidência:** DETAIL_TAIL_LINES

## 71_detail_title — Detalhe

- **Elemento:** Título do detalhe
- **Targets:** detail-title
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.145, 0.8286, 0.985, 0.8429]]
- **Final px boxes:** [[555, 668, 1512, 685]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Título do detalhe — Confirma ID, estado e tempo / do job em foco.
- **Typing:** 00:04:35,900 → 00:04:36,900 (1.00s)
- **Hold complete:** 00:04:36,900 → 00:04:41,900 (5.00s)
- **Spotlight group:** detail-title (reused=False)
- **SFX / duck:** 00:04:35,900
- **Seta:** 00:04:36,900
- **Duração cena:** 6.00s
- **Manual review:** PASS
- **Evidência:** #detail-title

## 72_detail_log — Detalhe

- **Elemento:** Prévia do log
- **Targets:** detail-log
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.145, 0.8429, 0.985, 0.8857]]
- **Final px boxes:** [[553, 677, 1514, 722]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Prévia do log — Últimas linhas do run.log. / Para o log completo, use View Logs.
- **Typing:** 00:04:42,200 → 00:04:43,300 (1.10s)
- **Hold complete:** 00:04:43,300 → 00:04:48,300 (5.00s)
- **Spotlight group:** detail-log (reused=False)
- **SFX / duck:** 00:04:42,200
- **Seta:** 00:04:43,300
- **Duração cena:** 6.10s
- **Manual review:** PASS
- **Evidência:** #detail-log

## 80_events — Ações

- **Elemento:** Eventos recentes
- **Targets:** event-trail
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.135, 0.9429, 0.795, 0.9857]]
- **Final px boxes:** [[542, 759, 1297, 802]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Eventos recentes — Mostra o último aviso da Overview, / como início do Dispatch ou término.
- **Typing:** 00:04:48,600 → 00:04:49,833 (1.23s)
- **Hold complete:** 00:04:49,833 → 00:04:54,833 (5.00s)
- **Spotlight group:** events (reused=False)
- **SFX / duck:** 00:04:48,600
- **Seta:** 00:04:49,833
- **Duração cena:** 6.23s
- **Manual review:** PASS
- **Evidência:** #event-trail

## 81_newjob — Ações

- **Elemento:** New Job [N]
- **Targets:** new-job
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.8, 0.9429, 0.86, 0.9857]]
- **Final px boxes:** [[1295, 759, 1371, 802]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** New Job [N] — Abre a tela para configurar / e enviar um novo job.
- **Typing:** 00:04:55,133 → 00:04:56,133 (1.00s)
- **Hold complete:** 00:04:56,133 → 00:05:01,133 (5.00s)
- **Spotlight group:** btn-new (reused=False)
- **SFX / duck:** 00:04:55,133
- **Seta:** 00:04:56,133
- **Duração cena:** 6.00s
- **Manual review:** PASS
- **Evidência:** #new-job

## 82_viewlogs — Ações

- **Elemento:** View Logs [V]
- **Targets:** view-logs
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.865, 0.9429, 0.925, 0.9857]]
- **Final px boxes:** [[1369, 759, 1445, 802]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** View Logs [V] — Abre o detalhe completo do job / selecionado para diagnóstico.
- **Typing:** 00:05:01,433 → 00:05:02,500 (1.07s)
- **Hold complete:** 00:05:02,500 → 00:05:07,500 (5.00s)
- **Spotlight group:** btn-logs (reused=False)
- **SFX / duck:** 00:05:01,433
- **Seta:** 00:05:02,500
- **Duração cena:** 6.07s
- **Manual review:** PASS
- **Evidência:** #view-logs

## 82b_viewlogs_when — Ações

- **Elemento:** Quando usar
- **Targets:** view-logs
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.865, 0.9429, 0.925, 0.9857]]
- **Final px boxes:** [[1369, 759, 1445, 802]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Quando usar — Use em FAILED ou quando o log / curto do painel não bastar.
- **Typing:** 00:05:07,500 → 00:05:08,500 (1.00s)
- **Hold complete:** 00:05:08,500 → 00:05:13,500 (5.00s)
- **Spotlight group:** btn-logs (reused=True)
- **SFX / duck:** 00:05:07,500
- **Seta:** 00:05:08,500
- **Duração cena:** 6.00s
- **Manual review:** PASS
- **Evidência:** open_job_detail

## 83_cancel — Ações

- **Elemento:** Cancel [C]
- **Targets:** cancel
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.93, 0.9429, 0.99, 0.9857]]
- **Final px boxes:** [[1442, 759, 1518, 802]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Cancel [C] — Inicia o cancelamento somente / se o job selecionado estiver RUNNING.
- **Typing:** 00:05:13,800 → 00:05:14,900 (1.10s)
- **Hold complete:** 00:05:14,900 → 00:05:19,900 (5.00s)
- **Spotlight group:** btn-cancel (reused=False)
- **SFX / duck:** 00:05:13,800
- **Seta:** 00:05:14,900
- **Duração cena:** 6.10s
- **Manual review:** PASS
- **Evidência:** #cancel

## 83b_cancel_note — Ações

- **Elemento:** Atenção
- **Targets:** cancel
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.93, 0.9429, 0.99, 0.9857]]
- **Final px boxes:** [[1442, 759, 1518, 802]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Atenção — Jobs que não estão RUNNING / não podem ser cancelados aqui.
- **Typing:** 00:05:19,900 → 00:05:20,900 (1.00s)
- **Hold complete:** 00:05:20,900 → 00:05:25,900 (5.00s)
- **Spotlight group:** btn-cancel (reused=True)
- **SFX / duck:** 00:05:19,900
- **Seta:** 00:05:20,900
- **Duração cena:** 6.00s
- **Manual review:** PASS
- **Evidência:** Only Running jobs

## 90_close — Encerramento

- **Elemento:** Resumo
- **Targets:** (card)
- **Font:** Carlito 38px
- **Norm cutouts:** [[0.12, 0.14, 0.88, 0.7]]
- **Final px boxes:** [[80, 100, 1840, 786]]
- **Cutouts:** 1
- **Overlay opacity:** 170/255
- **Diálogo:** Resumo — Na Overview você monitora status, / interpreta resultados e age.
- **Typing:** 00:05:25,900 → 00:05:26,900 (1.00s)
- **Hold complete:** 00:05:26,900 → 00:05:31,900 (5.00s)
- **Spotlight group:** close (reused=False)
- **SFX / duck:** 00:05:25,900
- **Seta:** 00:05:26,900
- **Duração cena:** 6.00s
- **Manual review:** PASS
- **Evidência:** closing
