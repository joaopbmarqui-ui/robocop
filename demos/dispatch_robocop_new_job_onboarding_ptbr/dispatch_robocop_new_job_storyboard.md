# Storyboard — New Job (silencioso, pt-BR)

Vídeo sem narração e sem música. Explicações on-screen + cursor/cliques.

## 01_open — Abertura

- **Tempo:** 00:00:00,000 → 00:00:03,500 (3.5s)
- **Tela:** `card:open`
- **Destaque / cursor:** (0.5, 0.5)
- **Badge:** —
- **Texto na tela:** Dispatch (Robocop) — Como utilizar a aba New Job / Configure e inicie um novo job passo a passo.
- **Resultado esperado:** analista entende o uso prático de “Dispatch (Robocop)”

## 02_purpose — Propósito

- **Tempo:** 00:00:03,500 → 00:00:08,300 (4.8s)
- **Tela:** `arrive`
- **Destaque / cursor:** (0.55, 0.12)
- **Badge:** —
- **Texto na tela:** Para que serve — A aba New Job permite configurar e iniciar uma nova execução no Dispatch. / Você define a origem, o destino, a consulta e as opções de execução do job.
- **Resultado esperado:** analista entende o uso prático de “Para que serve”

## 03_ready — Antes de começar

- **Tempo:** 00:00:08,300 → 00:00:12,800 (4.5s)
- **Tela:** `card:ready`
- **Destaque / cursor:** (0.5, 0.45)
- **Badge:** —
- **Texto na tela:** Antes de começar — Tenha pronto: / • o arquivo SQL do seu job (quando usar SqlFile ou MonthlyJob); / • a origem e o destino desejados; / • e-mail de notificação, se quiser receber aviso.
- **Resultado esperado:** analista entende o uso prático de “Antes de começar”

## 04_matrix — Matriz

- **Tempo:** 00:00:12,800 → 00:00:17,400 (4.6s)
- **Tela:** `matrix`
- **Destaque / cursor:** (0.52, 0.18) + clique
- **Badge:** Opcional
- **Texto na tela:** Source × Destination — Mostra quais combinações de origem e destino são permitidas. / Use como referência rápida antes de escolher as opções.
- **Resultado esperado:** analista entende o uso prático de “Source × Destination”

## 05_detected — Detecção

- **Tempo:** 00:00:17,400 → 00:00:21,500 (4.1s)
- **Tela:** `arrive`
- **Destaque / cursor:** (0.55, 0.28)
- **Badge:** —
- **Texto na tela:** Detected source — Indica o tipo detectado no arquivo SQL selecionado. / Confira se corresponde ao que você pretende executar.
- **Resultado esperado:** analista entende o uso prático de “Detected source”

## 06_source — Source

- **Tempo:** 00:00:21,500 → 00:00:27,300 (5.8s)
- **Tela:** `source_sqlfile`
- **Destaque / cursor:** (0.38, 0.36) + clique
- **Badge:** Obrigatório
- **Texto na tela:** Source — Define de onde os dados serão obtidos. / SqlFile: consulta em arquivo SQL. / MonthlyJob: consulta com período de datas. / ExistingTable: exporta uma tabela já existente.
- **Resultado esperado:** analista entende o uso prático de “Source”

## 07_destination — Destination

- **Tempo:** 00:00:27,300 → 00:00:32,900 (5.6s)
- **Tela:** `source_sqlfile`
- **Destaque / cursor:** (0.68, 0.36) + clique
- **Badge:** Obrigatório
- **Texto na tela:** Destination — Define onde o resultado do job será armazenado. / Table: salva em tabela. / Csv: gera arquivo CSV. / Table+Csv: faz os dois.
- **Resultado esperado:** analista entende o uso prático de “Destination”

## 08_queue — Fila

- **Tempo:** 00:00:32,900 → 00:00:38,200 (5.3s)
- **Tela:** `queues`
- **Destaque / cursor:** (0.55, 0.52) + clique
- **Badge:** Opcional
- **Texto na tela:** Execution Queue — Define a fila em que o job será processado. / Sem seleção = automático. / Escolha conforme a orientação do seu projeto.
- **Resultado esperado:** analista entende o uso prático de “Execution Queue”

## 09_picker — SQL

- **Tempo:** 00:00:38,200 → 00:00:43,000 (4.8s)
- **Tela:** `picker`
- **Destaque / cursor:** (0.55, 0.62) + clique
- **Badge:** Obrigatório
- **Texto na tela:** Lista de arquivos SQL — Lista os arquivos .sql da pasta atual. / Selecione o arquivo do job para preencher o caminho.
- **Resultado esperado:** analista entende o uso prático de “Lista de arquivos SQL”

## 10_sql_file — SQL

- **Tempo:** 00:00:43,000 → 00:00:47,200 (4.2s)
- **Tela:** `picker`
- **Destaque / cursor:** (0.58, 0.72)
- **Badge:** Obrigatório
- **Texto na tela:** SQL File — Caminho do arquivo SQL que será usado no job. / Confirme se o arquivo indicado é o correto.
- **Resultado esperado:** analista entende o uso prático de “SQL File”

## 11_email — Notificação

- **Tempo:** 00:00:47,200 → 00:00:52,000 (4.8s)
- **Tela:** `email_ok`
- **Destaque / cursor:** (0.58, 0.78) + clique
- **Badge:** Opcional
- **Texto na tela:** Email (notifications) — Envia aviso quando o job terminar. / Deixe em branco se não precisar de notificação.
- **Resultado esperado:** analista entende o uso prático de “Email (notifications)”

## 12_subject — Notificação

- **Tempo:** 00:00:52,000 → 00:00:56,400 (4.4s)
- **Tela:** `email_ok`
- **Destaque / cursor:** (0.58, 0.84) + clique
- **Badge:** Opcional
- **Texto na tela:** Subject (email) — Define o assunto do e-mail de notificação. / Use um texto curto que identifique o job.
- **Resultado esperado:** analista entende o uso prático de “Subject (email)”

## 13_monthly — MonthlyJob

- **Tempo:** 00:00:56,400 → 00:01:02,400 (6.0s)
- **Tela:** `monthly`
- **Destaque / cursor:** (0.38, 0.4) + clique
- **Badge:** Use apenas quando...
- **Texto na tela:** MonthlyJob — Use quando o job precisa rodar com um intervalo de datas. / Neste modo o destino fica em Table e aparecem Schema, / Table Name, Start Date e End Date.
- **Resultado esperado:** analista entende o uso prático de “MonthlyJob”

## 14_monthly_fields — MonthlyJob

- **Tempo:** 00:01:02,400 → 00:01:07,800 (5.4s)
- **Tela:** `monthly_fields`
- **Destaque / cursor:** (0.58, 0.78)
- **Badge:** Obrigatório
- **Texto na tela:** Campos do MonthlyJob — Schema e Table Name: onde o resultado será salvo. / Start Date e End Date: período da consulta. / Revise as datas antes de continuar.
- **Resultado esperado:** analista entende o uso prático de “Campos do MonthlyJob”

## 15_existing — ExistingTable

- **Tempo:** 00:01:07,800 → 00:01:13,600 (5.8s)
- **Tela:** `existing`
- **Destaque / cursor:** (0.38, 0.44) + clique
- **Badge:** Use apenas quando...
- **Texto na tela:** ExistingTable — Use quando os dados já estão em uma tabela e você / só precisa exportar o resultado em CSV. / Neste modo o destino fica limitado a Csv.
- **Resultado esperado:** analista entende o uso prático de “ExistingTable”

## 16_existing_fields — ExistingTable

- **Tempo:** 00:01:13,600 → 00:01:18,400 (4.8s)
- **Tela:** `existing_fields`
- **Destaque / cursor:** (0.58, 0.72)
- **Badge:** Obrigatório
- **Texto na tela:** Schema e Existing Table — Escolha o schema e informe o nome da tabela existente. / Se o schema não estiver na lista, use other.
- **Resultado esperado:** analista entende o uso prático de “Schema e Existing Table”

## 17_back_sqlfile — Exemplo

- **Tempo:** 00:01:18,400 → 00:01:23,200 (4.8s)
- **Tela:** `ready_review`
- **Destaque / cursor:** (0.55, 0.36) + clique
- **Badge:** —
- **Texto na tela:** Exemplo prático — Voltamos para SqlFile → Csv com o arquivo export_sales.sql. / Este é o fluxo mais comum para gerar um CSV.
- **Resultado esperado:** analista entende o uso prático de “Exemplo prático”

## 18_validation_bad — Validação

- **Tempo:** 00:01:23,200 → 00:01:27,800 (4.6s)
- **Tela:** `email_bad`
- **Destaque / cursor:** (0.58, 0.78)
- **Badge:** —
- **Texto na tela:** E-mail inválido — Revise o formato antes de continuar. / O status mostra o problema até a correção.
- **Resultado esperado:** analista entende o uso prático de “E-mail inválido”

## 19_validation_fix — Validação

- **Tempo:** 00:01:27,800 → 00:01:32,600 (4.8s)
- **Tela:** `ready_review`
- **Destaque / cursor:** (0.72, 0.92)
- **Badge:** —
- **Texto na tela:** Pronto para enviar — Com o e-mail corrigido, o status volta a Ready to launch. / Confira origem, destino, arquivo e fila antes do envio.
- **Resultado esperado:** analista entende o uso prático de “Pronto para enviar”

## 20_preview — Preview

- **Tempo:** 00:01:32,600 → 00:01:37,900 (5.3s)
- **Tela:** `preview`
- **Destaque / cursor:** (0.78, 0.92) + clique
- **Badge:** —
- **Texto na tela:** Preview — Revise a configuração e o conteúdo do job antes do envio. / Confirme se a consulta e o destino estão corretos.
- **Resultado esperado:** analista entende o uso prático de “Preview”

## 21_checklist — Revisão

- **Tempo:** 00:01:37,900 → 00:01:42,900 (5.0s)
- **Tela:** `card:checklist`
- **Destaque / cursor:** (0.5, 0.5)
- **Badge:** —
- **Texto na tela:** Antes de iniciar, confirme: — • origem e destino; / • arquivo selecionado; / • fila de execução; / • opções adicionais; / • e-mail de notificação.
- **Resultado esperado:** analista entende o uso prático de “Antes de iniciar, confirme:”

## 22_confirm — Envio

- **Tempo:** 00:01:42,900 → 00:01:48,200 (5.3s)
- **Tela:** `confirm`
- **Destaque / cursor:** (0.42, 0.72) + clique
- **Badge:** —
- **Texto na tela:** Launch Job — Inicia o job com as configurações revisadas. / Leia o resumo e confirme apenas se estiver correto.
- **Resultado esperado:** analista entende o uso prático de “Launch Job”

## 23_launched — Envio

- **Tempo:** 00:01:48,200 → 00:01:52,800 (4.6s)
- **Tela:** `launched`
- **Destaque / cursor:** (0.55, 0.88)
- **Badge:** —
- **Texto na tela:** Job enviado — O job foi enviado pelo Dispatch. / Acompanhe o andamento na tela de monitoramento.
- **Resultado esperado:** analista entende o uso prático de “Job enviado”

## 24_overview — Overview

- **Tempo:** 00:01:52,800 → 00:01:57,400 (4.6s)
- **Tela:** `overview`
- **Destaque / cursor:** (0.12, 0.22) + clique
- **Badge:** —
- **Texto na tela:** Próximo passo — Após o envio, acompanhe o status do job no Overview.
- **Resultado esperado:** analista entende o uso prático de “Próximo passo”

## 25_close — Encerramento

- **Tempo:** 00:01:57,400 → 00:02:03,400 (6.0s)
- **Tela:** `card:close`
- **Destaque / cursor:** (0.5, 0.5)
- **Badge:** —
- **Texto na tela:** Resumo — Na aba New Job, você: / 1. define a execução; / 2. revisa as configurações; / 3. inicia o job; / 4. acompanha o resultado no Overview. /  / Em caso de dúvida, revise os campos antes de selecionar Launch Job.
- **Resultado esperado:** analista entende o uso prático de “Resumo”
