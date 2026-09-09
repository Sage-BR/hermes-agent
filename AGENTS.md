# AGENTS.md — Hermes Agent integrado ao Hermes Portable

## Escopo

Este clone é a fonte de desenvolvimento usada pelo projeto Hermes Portable.
Todas as respostas e registros de manutenção devem ser escritos em PT-BR.

## Repositórios e precedência

- `origin`: `https://github.com/Sage-BR/hermes-agent.git` — fonte executada,
  sincronizada e publicada para esta versão.
- `upstream`: `https://github.com/NousResearch/hermes-agent.git` — somente
  referência para localizar commits úteis; nunca é a origem direta de execução
  ou download do Portable.
- Portable local: `D:\Documentos\Projetos\Hermes-USB-Portable-main`.
- Produção atualmente instalada: `E:\src\hermes-agent`.

Para regras do Portable, a fonte oficial é
`D:\Documentos\Projetos\Hermes-USB-Portable-main\data\skills\AGENTS.md`.
Não usar `.config/AGENTS.md` para precedência e não mesclar essas fontes.
Quando uma tarefa alterar o comportamento do Portable, ler primeiro o
`data/skills/AGENTS.md` do projeto Portable.

## Integração com o Portable

- O Portable resolve o código por `HERMES_SOURCE_DIR`, depois por
  `data/source-path.txt`, e só então pelo fallback `src/hermes-agent`.
- O ponteiro de desenvolvimento atual aponta para este clone:
  `D:\Documentos\Projetos\hermes-agent`.
- Instalações novas sem checkout externo baixam de
  `https://github.com/Sage-BR/hermes-agent`, atualmente fixadas na revisão
  publicada `eb680fdb80330c8a4ab7f242ff18ffcd6afe4bd1` pelo Portable.
- Alterações em `agent/`, `gateway/`, `hermes_cli/`, `tools/` e demais módulos
  de runtime precisam ser validadas no clone antes de atualizar a produção.
- O Portable contém adaptações próprias no launcher, Smart Router, entrada de
  texto e contexto; não sobrescrever essas adaptações com uma cópia integral do
  upstream.
- `tui_gateway` é dependência efetiva do gateway/dashboard e não deve ser
  removido sem validar todos os caminhos que o importam.

## Como usar o upstream NousResearch

O upstream existe apenas para adaptar commits úteis à variante Sage-BR/Portable:

1. Atualizar referências sem alterar a árvore de trabalho:
   `git fetch upstream --prune`.
2. Procurar commits por área e revisar o diff completo:
   `git log --oneline --all --decorate -- <caminho>` e
   `git show --stat --oneline <commit>`.
3. Selecionar somente commits compatíveis com a versão Sage-BR e com o escopo
   reduzido do Portable.
4. Preferir adaptação manual ou cherry-pick isolado; não fazer merge/rebase
   automático do upstream e não substituir arquivos inteiros sem comparação.
5. Resolver conflitos preservando o comportamento do Portable, especialmente
   roteamento de modelos, compressão, colagem multimídia, callbacks de
   validação e formato de resposta.
6. Validar o clone e só depois sincronizar a cópia de produção em
   `E:\src\hermes-agent`.

Commits que dependam de `apps/`, `website/`, `ui-tui/`, `optional-skills/`,
`native/`, CI, Docker ou instaladores upstream não devem ser trazidos sem uma
necessidade explícita do Portable.

## Validação mínima

- Verificar `git diff --check`.
- Executar os testes direcionados da área alterada.
- Confirmar que o launcher ainda resolve `cli.py` e `run_agent.py` no clone.
- Confirmar que downloads e atualizações apontam para Sage-BR.
- Não expor tokens, chaves, PII, transcripts completos ou logs brutos.

## Formato de saída

Relatórios para o usuário devem separar diagnóstico, correção, riscos e arquivos
alterados. JSON interno de validação nunca deve ser apresentado como resposta
final ao usuário.
