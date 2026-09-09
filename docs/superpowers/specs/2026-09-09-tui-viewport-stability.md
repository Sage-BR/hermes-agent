# Estabilidade do TUI: viewport e composer

## Contexto

O CLI usa `prompt_toolkit` em `full_screen=False` para manter o transcript no
scrollback do terminal e renderizar o composer no rodapé. Em reinícios, redraws
e mudanças de largura, o cursor e a tela anterior podem deixar linhas do
composer no scrollback. O resultado é texto antigo aparecendo fora da área de
entrada, como se houvesse dois campos de mensagem.

## Decisão

Manter o modo não-fullscreen e o transcript no scrollback. A correção será
cirúrgica:

1. normalizar o viewport antes do startup, removendo somente a tela visível;
2. centralizar a sequência de limpeza para reutilização e fallback seguro em
   terminais sem ANSI;
3. resetar o estado de renderização antes de pintar o novo composer;
4. preservar o histórico de transcript e excluir o composer do replay;
5. manter a recuperação de resize/foco e o paste grande atomicamente protegidos;
6. cobrir startup/reentrada, replay, resize e layout com testes regressivos.

Não será adotado `full_screen=True`, pois isso mudaria o contrato de scrollback
e exigiria reimplementar a navegação do transcript.

## Invariantes

- O usuário vê um único composer ativo no final da viewport.
- Limpar a viewport não apaga o transcript, salvo configuração explícita de
  reconstrução de scrollback já existente.
- Redraws não gravam placeholder, prompt ou status bar no histórico.
- Falha de ANSI/PTY não interrompe o CLI nem gera loop de redraw.
- A solução permanece compatível com Windows, SSH, tmux e terminais sem
  suporte completo a sequências ANSI.

## Validação

Executar testes focados do TUI, compilação Python e revisão separada do clone e
da produção antes da sincronização.
