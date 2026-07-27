# Storyboard — Dispatch (Robocop) | New Job (pt-BR)

Mapa seção → tela/ação → narração → texto na tela → destaque → resultado esperado.

## 01_title — Abertura

- **Tempo:** 00:00:00,000 → 00:00:09,494 (9.5s)
- **Tela / ação:** `title` — Cartão de título
- **Narração:** Bem-vindo ao Dispatch, também conhecido como Robocop. Neste vídeo, você vai aprender a usar a aba New Job, do início ao envio.
- **Texto na tela:** Dispatch (Robocop) | Como utilizar a aba New Job
- **Destaque visual:** Cartão de título
- **Resultado esperado:** O espectador entende o tema do vídeo

## 02_objective — Abertura

- **Tempo:** 00:00:09,494 → 00:00:24,340 (14.8s)
- **Tela / ação:** `section` — Texto de objetivo
- **Narração:** A aba New Job serve para configurar e lançar um job no Impala: uma execução de consulta SQL supervisionada pelo Dispatch. Ao final, você saberá preencher o formulário, corrigir erros e enviar o job.
- **Texto na tela:** Objetivo: configurar e lançar um job
- **Destaque visual:** Texto de objetivo
- **Resultado esperado:** Entendimento do propósito da aba

## 03_prereq — Antes de começar

- **Tempo:** 00:00:24,340 → 00:00:48,834 (24.5s)
- **Tela / ação:** `section` — Lista de pré-requisitos
- **Narração:** Antes de começar, tenha pronto: um arquivo SQL na pasta de onde você abriu o Dispatch; um ticket Kerberos válido — o indicador K R B na barra lateral deve mostrar tempo restante; e, se quiser notificação, um e-mail no formato nome arroba domínio. O campo Email (notifications) é opcional; Kerberos e o arquivo SQL são necessários para lançar.
- **Texto na tela:** Antes de começar
- **Destaque visual:** Lista de pré-requisitos
- **Resultado esperado:** Usuário sabe o que preparar

## 04_arrive — Preenchimento dos campos

- **Tempo:** 00:00:48,834 → 00:01:07,280 (18.4s)
- **Tela / ação:** `arrive` — Tela New Job completa
- **Narração:** Você chegou à aba New Job. À esquerda está a navegação; New Job fica destacado. No rodapé da barra lateral, o indicador K R B mostra se a autenticação Kerberos está ok. O formulário começa no topo e desce até os botões Preview SQL e Launch.
- **Texto na tela:** Aba New Job
- **Destaque visual:** Tela New Job completa
- **Resultado esperado:** Orientação espacial da tela

## 05_matrix — Preenchimento dos campos

- **Tempo:** 00:01:07,280 → 00:01:28,438 (21.2s)
- **Tela / ação:** `matrix` — Tabela de células legais
- **Narração:** No topo, a matriz Source vezes Destination legal cells mostra quais combinações são permitidas. SqlFile pode ir para Table, Csv ou Table mais Csv. MonthlyJob só pode ir para Table. ExistingTable só pode ir para Csv. Pressione M para expandir ou recolher essa matriz.
- **Texto na tela:** Matriz Source × Destination
- **Destaque visual:** Tabela de células legais
- **Resultado esperado:** Entende restrições de combinação

## 06_detected — Preenchimento dos campos

- **Tempo:** 00:01:28,438 → 00:01:45,540 (17.1s)
- **Tela / ação:** `arrive` — Linha Detected source
- **Narração:** A linha Detected source informa o tipo detectado no arquivo SQL selecionado. Se o arquivo tiver os marcadores date_inicio e date_fim, o Dispatch trata como MonthlyJob e desativa automaticamente destinos ilegais.
- **Texto na tela:** Detected source
- **Destaque visual:** Linha Detected source
- **Resultado esperado:** Entende detecção automática

## 07_source — Preenchimento dos campos

- **Tempo:** 00:01:45,540 → 00:02:05,786 (20.2s)
- **Tela / ação:** `source_dest` — Radio Source
- **Narração:** O campo Source é obrigatório. SqlFile: consulta SQL comum em um arquivo. MonthlyJob: consulta com intervalo de datas, usando os marcadores date_inicio e date_fim. ExistingTable: exporta uma tabela que já existe no Impala, sem arquivo SQL.
- **Texto na tela:** Source — obrigatório
- **Destaque visual:** Radio Source
- **Resultado esperado:** Escolhe a origem correta

## 08_destination — Preenchimento dos campos

- **Tempo:** 00:02:05,786 → 00:02:24,160 (18.4s)
- **Tela / ação:** `source_dest` — Radio Destination
- **Narração:** Destination também é obrigatório e depende do Source. Table grava o resultado em uma tabela Impala. Csv grava um arquivo C S V na pasta de lançamento. Table mais Csv faz os dois. Opções ilegais ficam desabilitadas automaticamente.
- **Texto na tela:** Destination — obrigatório
- **Destaque visual:** Radio Destination
- **Resultado esperado:** Escolhe destino permitido

## 09_queue — Preenchimento dos campos

- **Tempo:** 00:02:24,160 → 00:02:40,110 (15.9s)
- **Tela / ação:** `queues` — Lista de filas
- **Narração:** Execution Queue é opcional. Sem seleção, o modo Auto tenta as filas até uma aceitar o job. Você pode marcar uma ou mais filas para restringir; várias são tentadas na ordem da lista. Use Auto se não tiver preferência.
- **Texto na tela:** Execution Queue — opcional
- **Destaque visual:** Lista de filas
- **Resultado esperado:** Entende Auto versus seleção manual

## 10_picker — Preenchimento dos campos

- **Tempo:** 00:02:40,110 → 00:03:00,428 (20.3s)
- **Tela / ação:** `picker` — Picker e campo SQL File
- **Narração:** A lista SQL files mostra os arquivos ponto sql da pasta de lançamento. Selecione um para preencher o caminho. O campo SQL File é obrigatório para SqlFile e MonthlyJob; o arquivo precisa existir. Abaixo, um indicador confirma se o arquivo foi encontrado.
- **Texto na tela:** SQL File — obrigatório para SqlFile/MonthlyJob
- **Destaque visual:** Picker e campo SQL File
- **Resultado esperado:** Seleciona o SQL correto

## 11_email_subject — Preenchimento dos campos

- **Tempo:** 00:03:00,428 → 00:03:18,874 (18.4s)
- **Tela / ação:** `email_ok` — Campos Email e Subject
- **Narração:** O campo Email (notifications) é opcional. Se preencher, use um endereço válido com arroba e domínio. Vários e-mails podem ser separados por vírgula. Subject (email) também é opcional; o padrão é Dispatch Job. Define o assunto da notificação.
- **Texto na tela:** Email (notifications) e Subject — opcionais
- **Destaque visual:** Campos Email e Subject
- **Resultado esperado:** Preenche notificação se desejar

## 12_status — Preenchimento dos campos

- **Tempo:** 00:03:18,874 → 00:03:37,296 (18.4s)
- **Tela / ação:** `ready_actions` — Validation summary e botões
- **Narração:** Na área de status, o Dispatch mostra checagens ao vivo: arquivo SQL encontrado, formato de e-mail e Kerberos. Na barra de ações, a mensagem Ready to launch aparece quando não há problemas. Os botões são Preview SQL tecla P, e Launch tecla L.
- **Texto na tela:** Status e ações
- **Destaque visual:** Validation summary e botões
- **Resultado esperado:** Lê indicadores antes de enviar

## 13_monthly — Preenchimento dos campos

- **Tempo:** 00:03:37,296 → 00:03:55,022 (17.7s)
- **Tela / ação:** `monthly` — Campos Schema, Table, datas
- **Narração:** Ao escolher MonthlyJob, o destino fica limitado a Table. Aparecem campos obrigatórios extras: Schema, Table Name com o prefixo do seu usuário, Start Date e End Date no formato ano-mês-dia. As datas definem o período da consulta mensal.
- **Texto na tela:** MonthlyJob → Table
- **Destaque visual:** Campos Schema, Table, datas
- **Resultado esperado:** Vê dependências do MonthlyJob

## 14_existing — Preenchimento dos campos

- **Tempo:** 00:03:55,022 → 00:04:12,388 (17.4s)
- **Tela / ação:** `existing` — Schema e Existing Table
- **Narração:** Com ExistingTable, o destino fica só em Csv. Escolha o Schema — coe_enc, aa_enc ou other — e informe o nome da tabela existente. Se usar other, aparece Custom Schema. Não há Preview SQL nesse modo.
- **Texto na tela:** ExistingTable → Csv
- **Destaque visual:** Schema e Existing Table
- **Resultado esperado:** Vê dependências do ExistingTable

## 15_validation_bad — Revisão

- **Tempo:** 00:04:12,388 → 00:04:29,202 (16.8s)
- **Tela / ação:** `email_bad` — Campo Email + validation summary
- **Narração:** Vamos demonstrar um erro comum. No fluxo SqlFile para Csv, se o e-mail for inválido, como apenas a palavra invalido, o resumo mostra issue Invalid email format, e o indicador de e-mail fica vermelho. Corrija antes de lançar.
- **Texto na tela:** Erro: Invalid email format
- **Destaque visual:** Campo Email + validation summary
- **Resultado esperado:** Reconhece e interpreta validação

## 16_validation_fix — Revisão

- **Tempo:** 00:04:29,202 → 00:04:48,008 (18.8s)
- **Tela / ação:** `ready_review` — Formulário pronto
- **Narração:** Corrigindo para analyst arroba example ponto com, o erro some. O status volta a Ready to launch. Revise: Source SqlFile, Destination Csv, arquivo export_sales ponto sql, fila em Auto, e-mail válido e Kerberos ok.
- **Texto na tela:** ✓ Ready to launch
- **Destaque visual:** Formulário pronto
- **Resultado esperado:** Confirma configuração válida

## 17_preview — Revisão

- **Tempo:** 00:04:48,008 → 00:05:01,942 (13.9s)
- **Tela / ação:** `preview` — Tela de preview
- **Narração:** Antes de enviar, use Preview SQL com a tecla P para ver o SQL que será executado. Confirme se a consulta está correta e volte com Esc. Preview não está disponível para ExistingTable.
- **Texto na tela:** SQL Preview
- **Destaque visual:** Tela de preview
- **Resultado esperado:** Revisa SQL antes do envio

## 18_confirm — Envio do job

- **Tempo:** 00:05:01,942 → 00:05:19,380 (17.4s)
- **Tela / ação:** `confirm` — Modal de confirmação
- **Narração:** Ao pressionar Launch ou a tecla L, abre a confirmação Launch Job. Ela resume Source, Destination, tabela alvo, fila, caminho do C S V e e-mail. Launch confirma; Review cancela para ajustar. Confirme com Y ou Enter.
- **Texto na tela:** Confirmação Launch Job
- **Destaque visual:** Modal de confirmação
- **Resultado esperado:** Lê o resumo antes de confirmar

## 19_launched — Envio do job

- **Tempo:** 00:05:19,380 → 00:05:33,074 (13.7s)
- **Tela / ação:** `launched` — Mensagem de sucesso
- **Narração:** Após confirmar, o Dispatch cria o job e inicia o runner em segundo plano, mostrando a mensagem Launched Job com o identificador. A interface não fica responsável pela execução durável do job.
- **Texto na tela:** ✓ Launched Job …
- **Destaque visual:** Mensagem de sucesso
- **Resultado esperado:** Vê confirmação imediata do envio

## 20_next — Próximos passos

- **Tempo:** 00:05:33,074 → 00:05:48,136 (15.1s)
- **Tela / ação:** `overview` — Tela Overview para monitorar
- **Narração:** Para acompanhar, volte à Overview com Esc ou B. Nessa tela você monitora jobs em execução e recentes, além dos logs. O status final no Impala depende do ambiente real; use Overview e View Logs para acompanhar.
- **Texto na tela:** Próximo: Overview
- **Destaque visual:** Tela Overview para monitorar
- **Resultado esperado:** Sabe para onde ir depois

## 21_checklist — Próximos passos

- **Tempo:** 00:05:48,136 → 00:06:09,486 (21.4s)
- **Tela / ação:** `checklist` — Lista de verificação
- **Narração:** Checklist final: Kerberos válido; combinação Source e Destination permitida; arquivo SQL existente quando necessário; campos extras do MonthlyJob ou ExistingTable preenchidos; e-mail vazio ou válido; status Ready to launch; revise no Preview e na confirmação Launch Job. Até a próxima!
- **Texto na tela:** Checklist antes de enviar
- **Destaque visual:** Lista de verificação
- **Resultado esperado:** Memoriza checagens-chave
