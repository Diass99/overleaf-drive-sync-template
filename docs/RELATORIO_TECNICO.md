# Relatório técnico: Overleaf Drive Sync v0.1.4

**Autor:** Vinícius José Dias  
**Primeira consolidação:** 15 de outubro de 2026 (v0.1.0)  
**Atualização:** 26 de novembro de 2026 (v0.1.4)  
**Repositório público:** https://github.com/Diass99/overleaf-drive-sync-template  
**Licença:** MIT

## Histórico de versões

| Versão | Commit | Data | Alteração |
|---|---|---|---|
| 0.1.0 | `03d0092` | 26/08/2026 | Versão inicial (20 testes) |
| 0.1.1 | `877b0bc` | 21/10/2026 | Exclusão de metadados de sistema (`desktop.ini`, `Thumbs.db`, `ehthumbs.db`, `.DS_Store`) em qualquer nível; documentação do uso em Windows |
| 0.1.1 | `2618a5f` | 21/10/2026 | Rejeição de caminhos com raiz ou unidade no Windows (`\dados`, `C:dados`) em `validar_caminho_relativo` |
| 0.1.2 | não registrado | entre 25 e 26/11/2026 | Versão intermediária; alterações não documentadas neste relatório |
| 0.1.3 | `f65c3af` | 26/11/2026 | Opção `sincronizacao.recursivo`: com `false`, só os arquivos do primeiro nível da pasta de outputs são copiados (subpastas de cache e backup ficam de fora); 24 testes |
| 0.1.4 | `8a9bc28` | 26/11/2026 | Modo "outputs no próprio projeto": a pasta de outputs do Drive é a mesma pasta publicada no Overleaf, sem cópia intermediária; publicação respeita `recursivo`; o Overleaf nunca sobrescreve os produtos dos códigos; 26 testes |

Estado de `main` em 26/11/2026: `8a9bc28`, todos os commits de autoria exclusiva de Vinícius José Dias, sem tags nem releases publicadas. Suíte de testes: 26 testes, com 1 ignorado fora do Windows (semântica de caminhos com unidade).

## 1. Resumo executivo

Este trabalho produziu uma automação portátil para integrar três componentes do fluxo científico:

- o **Google Drive**, onde permanecem os dados, produtos e cópias persistentes dos projetos;
- o **Google Colab ou qualquer computador com Python e Git**, onde os produtos científicos são gerados e a automação é executada;
- o **Overleaf**, que permanece como fonte oficial dos textos LaTeX.

O sistema foi criado para resolver um fluxo de duas etapas:

1. levar os produtos de uma pasta de outputs escolhida pelo usuário para a árvore de publicação do projeto no Drive;
2. publicar essa árvore no projeto correspondente do Overleaf por meio do Git Bridge.

A principal precaução arquitetural é impedir que uma cópia antiga de um `.tex`, armazenada no Drive, sobrescreva uma edição recente feita no Overleaf. Para isso, cada sincronização começa clonando o estado mais recente do Overleaf. Os arquivos remotos são usados para atualizar a cópia de segurança no Drive, enquanto somente a árvore de outputs configurada é enviada de volta ao Overleaf.

O resultado foi publicado como o repositório público **`Diass99/overleaf-drive-sync-template`**. A versão inicial `0.1.0` tinha 20 testes automatizados e validação prática em um projeto real do Overleaf. A versão vigente, `0.1.4` (26/11/2026), acrescenta o modo em que a pasta de outputs do Drive e a pasta de figuras do Overleaf são a mesma pasta, com o mesmo nome nos dois lados, e eleva a suíte a 26 testes. Esse modo está em uso no projeto `PROJETO_DE_MESTRADO` (Seção 11.2).

## 2. Objetivo e requisitos definidos

O objetivo evoluiu de um script específico para um projeto para um template reutilizável, capaz de configurar novos projetos por perguntas interativas, sem exigir edição manual com `sed`, `nano` ou `gedit`.

Os requisitos consolidados foram:

- funcionar independentemente do computador usado;
- aceitar uma raiz do Google Drive diferente em cada ambiente;
- permitir que o usuário escolha a pasta de outputs de cada projeto;
- copiar todos os arquivos, extensões, arquivos ocultos e subdiretórios, ou somente o primeiro nível, conforme a configuração;
- preservar arquivos antigos no destino no modo incremental;
- não armazenar tokens em código, TOML, URLs ou repositórios;
- não manter o repositório Git operacional dentro de uma montagem Rclone;
- tratar o Overleaf como fonte oficial do texto;
- publicar somente os outputs configurados;
- não criar commits quando não houver alterações;
- oferecer simulação segura antes de uma execução real;
- poder ser executado tanto em Linux quanto no Google Colab;
- incluir documentação, testes, licença e distribuição pelo GitHub.

## 3. Estado inicial e prova de conceito

A primeira implementação, `gitclone.py`, demonstrou que era possível:

1. clonar o Git remoto de um projeto do Overleaf;
2. copiar figuras geradas pelo pipeline;
3. criar um commit;
4. enviar as alterações ao Overleaf;
5. remover o clone temporário.

Essa prova de conceito confirmou a viabilidade do Git Bridge, porém tinha limitações importantes:

- caminhos e nomes de arquivos fixos;
- token do Overleaf inserido diretamente no código ou na URL Git;
- comandos executados de forma pouco estruturada;
- ausência de separação entre texto LaTeX e produtos científicos;
- risco de sobrescrever texto remoto com uma cópia local antiga;
- baixa portabilidade entre Linux, Colab e diferentes montagens do Drive;
- falta de testes, simulação, configuração persistente e tratamento adequado de erros.

O arquivo experimental foi removido depois que suas funções foram absorvidas pela implementação modular.

## 4. Arquitetura final

### 4.1. Fontes oficiais

| Conteúdo | Fonte oficial | Destino secundário |
|---|---|---|
| Texto LaTeX e estrutura editorial | Overleaf | Pasta raiz no Drive, como cópia atualizada |
| Outputs científicos | Pasta de outputs configurada no Drive | Overleaf (diretamente, no modo da v0.1.4) ou subpasta do projeto e Overleaf |
| Código da automação | GitHub e clone Git local | Cópia instalada em cada projeto |
| Tokens | Variável de ambiente, Secret do Colab ou entrada oculta | Nunca são gravados |

### 4.2. Fluxo de uma sincronização

1. A configuração do projeto é carregada de `.pipeline/projeto.toml`.
2. A raiz disponível do Google Drive é detectada.
3. O token é obtido sem ser armazenado.
4. O projeto mais recente é clonado do Overleaf em um diretório temporário.
5. O conteúdo remoto é copiado para a pasta raiz no Drive, preservando o texto recente. No modo da v0.1.4, a pasta de outputs fica fora dessa cópia.
6. A pasta de outputs é copiada para o destino configurado (por exemplo, `figuras/`). No modo da v0.1.4 essa etapa é dispensada, porque a pasta de outputs já é a pasta publicada.
7. Somente a árvore de publicação é copiada para o clone temporário, respeitando `recursivo`.
8. O Git verifica se existem mudanças reais.
9. Havendo mudanças, são executados `commit` e `push`.
10. Sem mudanças, nenhum commit é criado.
11. O clone e os auxiliares temporários são removidos automaticamente.

Esse desenho elimina a disputa entre duas cópias do texto e mantém a operação Git fora do Drive montado por Rclone.

## 5. Estrutura do repositório

```text
overleaf-drive-sync-template/
├── criar_projeto.py
├── .gitignore
├── LICENSE
├── pyproject.toml
├── README.md
├── src/
│   └── overleaf_drive_sync/
│       ├── __init__.py
│       ├── configuracao.py
│       ├── sincronizacao.py
│       └── overleaf_git.py
├── templates/
│   ├── main.tex
│   └── sincronizar.py
└── tests/
    ├── test_configuracao.py
    ├── test_criar_projeto.py
    ├── test_overleaf_git.py
    ├── test_outputs_no_projeto.py
    └── test_sincronizacao.py
```

### 5.1. Responsabilidade dos arquivos

- `criar_projeto.py`: assistente interativo que cria e configura uma nova instância.
- `configuracao.py`: detecção do Drive, validação de caminhos, extração do ID do Overleaf e leitura/escrita do TOML.
- `sincronizacao.py`: mecanismo de cópia incremental e idempotente, recursiva ou só do primeiro nível.
- `overleaf_git.py`: clone temporário, autenticação, backup do remoto, publicação, commit e push; detecção do modo "outputs no próprio projeto".
- `templates/main.tex`: documento mínimo usado na inicialização de um projeto novo.
- `templates/sincronizar.py`: executável autônomo instalado na raiz de cada projeto.
- `tests/`: testes unitários e de integração com repositório Git local descartável.
- `README.md`: manual rápido do repositório.
- `pyproject.toml`: metadados da versão `0.1.4`, Python 3.11 ou superior e autoria.
- `LICENSE`: licença MIT em nome de Vinícius José Dias.

## 6. Estrutura de uma instância gerada

Depois de executar o assistente, cada projeto possui uma estrutura semelhante a:

```text
PASTA_RAIZ_DO_PROJETO/
├── main.tex
├── figuras/
├── sincronizar.py
└── .pipeline/
    ├── projeto.toml
    └── overleaf_drive_sync/
        ├── __init__.py
        ├── configuracao.py
        ├── sincronizacao.py
        └── overleaf_git.py
```

O nome `figuras/` é apenas o padrão. O usuário pode escolher outro destino durante a configuração, inclusive a própria pasta de outputs (Seção 8.9).

## 7. Configuração gerada automaticamente

O assistente grava `.pipeline/projeto.toml`. Um exemplo conceitual é:

```toml
versao_configuracao = 1

[projeto]
nome = "NOME_DO_PROJETO"
arquivo_principal = "main.tex"

[drive]
pasta_outputs = "CAMINHO/RELATIVO/DOS/OUTPUTS"

[overleaf]
project_id = "ID_DE_24_CARACTERES"
token_env = "OVERLEAF_GIT_TOKEN"

[git]
usuario = "Automação científica"
email = "usuario@exemplo.com"
mensagem_commit = "Atualização automática do projeto"

[sincronizacao]
destino_outputs = "figuras"
modo = "incremental"
recursivo = true

[publicacao]
origem = "figuras"
excluir = [".pipeline", "README.md", ".gitignore", "LICENSE", "sincronizar.py"]
```

Os caminhos persistidos são relativos à raiz do Drive. Isso permite que o mesmo projeto seja encontrado em caminhos diferentes, como `~/GoogleDrive` no Linux e `/content/drive/MyDrive` no Colab.

## 8. Decisões técnicas relevantes

### 8.1. Cópia de todos os outputs

Não existe manifesto de figuras nem filtragem por extensão. A origem escolhida é copiada integralmente, incluindo:

- PNG, PDF, CSV, NetCDF ou qualquer outra extensão;
- arquivos ocultos;
- subdiretórios (exceto com `recursivo = false`, Seção 8.8);
- arquivos recém-criados ou alterados.

### 8.2. Modo incremental

O modo atual adiciona arquivos novos e atualiza arquivos modificados. Ele não remove automaticamente no destino os arquivos que desapareceram da origem. Essa escolha reduz o risco de exclusões acidentais.

### 8.3. Comparação idempotente

Os arquivos são comparados primeiro por tamanho e depois por SHA-256. Assim:

- a primeira execução copia o necessário;
- a segunda execução, sem mudanças, identifica tudo como idêntico;
- o Git não cria commit vazio;
- uma interrupção é corrigida pela execução seguinte.

### 8.4. Compatibilidade com Rclone

O uso inicial de `shutil.copy2` tentou preservar metadados e atributos estendidos. Na montagem do Google Drive via Rclone isso gerou `OSError: [Errno 5] Input/output error` durante operações de `listxattr`/`copystat`.

A solução foi usar `shutil.copyfile`, que transfere os bytes sem tentar reproduzir metadados incompatíveis. Em 26/11/2026, `cp --no-preserve=all` também falhou na montagem com o mesmo erro de E/S ("setting permissions"). Para alterar arquivos de uma instância no Drive, os procedimentos seguros são:

1. gerar a versão nova em `/tmp`;
2. validar sintaxe e conteúdo;
3. enviar com `rclone copyto` (atualiza o mesmo arquivo, mantendo ID e histórico de versões) ou com `shutil.copyfile`;
4. conferir o MD5 final informado pelo próprio Drive (`rclone lsjson --hash`).

O uso de `sed -i` diretamente na montagem não é recomendado, porque sua estratégia de arquivo temporário e renomeação pode falhar no Rclone.

### 8.5. Clone Git temporário

O clone operacional nunca fica dentro do Drive. Isso evita lentidão, problemas de lock, renomeações atômicas incompatíveis e inconsistências dentro de `.git`.

### 8.6. Metadados de sistema (v0.1.1)

No Windows, o Google Drive para Desktop e o Explorer criam `desktop.ini` nas pastas sincronizadas. Na v0.1.0 esses arquivos seriam copiados para a árvore de publicação e enviados ao Overleaf. A v0.1.1 define o conjunto `ARQUIVOS_DE_SISTEMA` (`desktop.ini`, `thumbs.db`, `ehthumbs.db`, `.ds_store`, com comparação sem distinção de caixa) e ignora esses arquivos em qualquer nível da cópia.

### 8.7. Validação de caminhos no Windows (v0.1.1)

No Windows, `Path("\\dados")` e `Path("C:dados")` não são absolutos, mas possuem raiz ou unidade (`anchor`). A função `validar_caminho_relativo` passou a rejeitar qualquer caminho com `anchor`, além dos absolutos e dos que contêm `..`.

### 8.8. Cópia somente do primeiro nível (v0.1.3)

O padrão de saídas adotado nos códigos mestres mantém as figuras na raiz da pasta de outputs, com nomes descritivos e prefixos numéricos, e duas subpastas que não devem ir ao Overleaf: `00_BACKUP` (versões substituídas, nunca lidas) e `99_OPERACIONAL` (caches NetCDF, CSV, JSON). Com `sincronizacao.recursivo = false`, `copiar_arvore_integral` considera apenas os arquivos do primeiro nível da origem. Até a v0.1.2 a opção era ignorada, o que teria publicado as duas subpastas. Teste associado: `test_nao_recursivo_copia_somente_primeiro_nivel`.

### 8.9. Outputs no próprio projeto (v0.1.4)

Quando `sincronizacao.destino_outputs` resolve para a própria pasta de outputs (`drive.pasta_outputs`), a instância opera no modo "outputs no próprio projeto": a pasta de outputs do Drive e a pasta de figuras do Overleaf são a mesma, com o mesmo nome nos dois lados. Nesse modo:

- `publicacao.origem` deve ser essa mesma pasta (caso contrário, `ValueError`);
- a etapa "Outputs → pasta raiz" é dispensada, pois não há cópia intermediária;
- a publicação respeita `recursivo`, de modo que `00_BACKUP` e `99_OPERACIONAL` permanecem só no Drive;
- a pasta de outputs é excluída da cópia "Overleaf → pasta raiz", de modo que uma versão antiga no Overleaf nunca sobrescreve um produto novo gerado pelos códigos.

Sem essa condição, o comportamento anterior é mantido integralmente. Testes associados: `test_mesma_pasta_publica_so_a_raiz_e_preserva_o_drive` e `test_mesma_pasta_exige_publicacao_igual` (repositório Git local no papel do Overleaf).

## 9. Segurança e autenticação

### 9.1. Token do Overleaf

O token é procurado nesta ordem:

1. variável de ambiente `OVERLEAF_GIT_TOKEN`;
2. Secret de mesmo nome no Google Colab;
3. solicitação interativa oculta com `getpass`.

O Git recebe a credencial por um `GIT_ASKPASS` temporário. O token não é incluído na URL remota, no código, em `projeto.toml` nem no histórico do repositório.

O token usado no primeiro protótipo, caso tenha sido exposto em código, histórico, captura ou relatório, deve permanecer revogado.

### 9.2. GitHub

O GitHub não aceita senha da conta em operações Git por HTTPS. O primeiro push foi autenticado com um Personal Access Token válido. Esse token serviu apenas como senha temporária e não foi armazenado no projeto.

Desde outubro de 2026, a autenticação no Linux é feita pelo GitHub CLI (`gh`), autenticado como Diass99, e no Windows pelo Git Credential Manager. Um PAT colado no terminal deve ser revogado quando não for mais necessário.

### 9.3. Credencial do Overleaf em cache

No Linux, pushes manuais ao Git Bridge usam `credential.helper` em cache de memória com validade de 8 horas. O armazenamento em texto puro (`credential.helper store`) foi descartado. No Windows, a variável `GCM_INTERACTIVE=never` impede que o Git Credential Manager abra janela própria, de modo que o token informado à rotina é o efetivamente usado.

### 9.4. Verificação de segredos

Antes da publicação foi feita uma busca por padrões `olp_` no repositório. Nenhum token do Overleaf foi encontrado nos arquivos versionados.

### 9.5. Cota da API do Google Drive

O cliente OAuth público do Rclone atinge `403 rateLimitExceeded` em listagens grandes. Desde 26/11/2026, o Rclone usa um cliente OAuth próprio, criado num projeto do Google Cloud do usuário. As credenciais desse cliente não devem ficar no Drive.

## 10. Validação realizada

### 10.1. Testes automatizados

A suíte da v0.1.0 executou **20 testes com sucesso**. A v0.1.1 passou a 22 testes (1 ignorado fora do Windows), a v0.1.3 a 24 e a v0.1.4 a **26 testes**. A cobertura funcional inclui:

- detecção da raiz do Drive;
- conversão para caminhos relativos portáteis;
- rejeição de caminhos absolutos ou com subida `..`;
- extração do ID de uma URL do Overleaf;
- serialização e leitura do TOML;
- cópia recursiva de arquivos ocultos e subdiretórios;
- cópia somente do primeiro nível (v0.1.3);
- atualização exclusiva de arquivos alterados;
- idempotência da segunda execução;
- preservação incremental de arquivos antigos;
- simulação sem efeitos persistentes;
- exclusões administrativas;
- rejeição de destino dentro da origem;
- preservação do texto remoto do Overleaf;
- publicação exclusiva dos outputs;
- commit e push contra um repositório Git descartável;
- modo "outputs no próprio projeto": publicação só da raiz, preservação dos produtos do Drive e exigência de `publicacao.origem` igual (v0.1.4);
- instalação da automação em um novo projeto;
- preservação de um `main.tex` existente;
- geração correta do ZIP inicial;
- exclusão de `desktop.ini` e demais metadados de sistema (v0.1.1);
- rejeição de caminhos com raiz ou unidade no Windows (v0.1.1).

Comando de teste:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

### 10.2. Teste prático

Foi gerada uma instância de teste com:

- um arquivo oculto `.metadados`;
- `resultado.txt`;
- `subpasta/dados.csv`.

O modo simulado mostrou as operações sem alterar o Drive nem o remoto. A execução real publicou os três arquivos no Overleaf. A execução seguinte classificou todos como idênticos e informou que nenhum commit era necessário.

Isso confirmou o fluxo completo: configuração, autenticação, cópia recursiva, publicação, idempotência e preservação do texto remoto.

### 10.3. Validação da v0.1.4 no PROJETO_DE_MESTRADO

Em 26/11/2026, a simulação e a execução real na raiz `03_PROJETO_DE_MESTRADO` resultaram em: 36 arquivos de texto do Overleaf copiados para o Drive (10 diretórios), etapa "Outputs → pasta raiz" dispensada, 55 figuras idênticas entre `06_OUTPUTS` do Drive e `06_OUTPUTS/` do Overleaf e nenhum commit necessário.

## 11. Publicação no GitHub e instâncias

O template foi copiado para um clone operacional fora do Drive:

```text
/home/vinicius/projetos/overleaf-drive-sync-template
```

O repositório foi inicializado na branch `main`, validado, testado e publicado em:

**https://github.com/Diass99/overleaf-drive-sync-template**

Primeiro commit:

```text
03d0092 Initial release: Overleaf Drive Sync v0.1.0
```

Commits posteriores publicaram a v0.1.1 (`877b0bc` e `2618a5f`, 21/10/2026), a v0.1.3 (`f65c3af`, 26/11/2026) e a v0.1.4 (`8a9bc28`, 26/11/2026).

A cópia histórica do template no Drive permaneceu separada, sem repositório `.git` operacional:

```text
/home/vinicius/GoogleDrive/01_TEMPLATE_PROJETOS/01_MODELO_OVERLEAF_AUTOMATIZADO
```

Daqui em diante, o GitHub e o clone local devem ser tratados como fonte oficial do código da automação.

### 11.1. Instâncias no Drive

Situação em 26/11/2026:

| Instância | Projeto Overleaf | Pasta de outputs | Destino | Versão | Situação |
|---|---|---|---|---|---|
| PROJETO_DE_MESTRADO | (omitido) | `01_ESTUDOS/05_OCEANOGRAFIA/02_MESTRADO/03_PROJETO_DE_MESTRADO/06_OUTPUTS` | `06_OUTPUTS` (mesma pasta) | 0.1.4 | Em uso |
| ARTIGO_DIS (antiga) | (omitido) | `01_ESTUDOS/06_MEUS_ARTIGOS_e_REVISOES/01_ARTIGOS/03_Artigo_DIS/04_OUTPUTS` | `assets` | 0.1.0 | Projeto Overleaf substituído pelo `PROJETO_DE_MESTRADO` |
| Qualificação II (antiga) | (omitido) | antiga `06_OUTPUTS/05_QUALI2` | `assets` | 0.1.1 | Arquivada em `99_ARQUIVO/07_QUALIFICACAO/02_QUALI_2/02_DOCUMENTO_QUALI2` |
| Divulgação Qualificação II (antiga) | (omitido) | antiga `06_OUTPUTS/04_DIVULGACAO_QUALI2` | `figuras` | 0.1.1 | Arquivada em `99_ARQUIVO/07_QUALIFICACAO/02_QUALI_2/01_DIVULGACAO_QUALI2` |
| TESTE_Overleaf_Drive_Sync | (omitido) | `01_TEMPLATE_PROJETOS/00_OUTPUT_TESTE_EXTREMO` | `figuras` | 0.1.0 | Teste |

### 11.2. Instância do PROJETO_DE_MESTRADO

O projeto Overleaf único `PROJETO_DE_MESTRADO` reúne todos os documentos do mestrado, com um `refs.bib` comum na raiz. A pasta `03_PROJETO_DE_MESTRADO` do Drive é a raiz da instância e espelha a raiz do Overleaf:

```text
03_PROJETO_DE_MESTRADO/            (Drive)          PROJETO_DE_MESTRADO (Overleaf)
├── 01_REFERENCIAS/ ... 05_CODIGOS/  só no Drive
├── 06_OUTPUTS/                      mesma pasta      06_OUTPUTS/  (figuras da raiz)
│   ├── 00_BACKUP/                   só no Drive
│   └── 99_OPERACIONAL/              só no Drive
├── 07_QUALIFICACAO_ETAPA1/          .tex + 00_ACOMPANHAMENTO (só no Drive)
├── 08_QUALIFICACAO_ETAPA2/          .tex, apresentacao/, divulgacao/ + 00_ACOMPANHAMENTO
├── 09_ARTIGO_DIS/
├── 10_DISSERTACAO/
├── 99_ARQUIVO/                      só no Drive (manifesto e LEIA_ME)
├── refs.bib, latexmkrc, logos
├── sincronizar.py
└── .pipeline/projeto.toml
```

Configuração em uso (trecho de `projeto.toml`):

```toml
[projeto]
arquivo_principal = "08_QUALIFICACAO_ETAPA2/main_Relatorio_QUALI2.tex"

[drive]
pasta_outputs = "01_ESTUDOS/05_OCEANOGRAFIA/02_MESTRADO/03_PROJETO_DE_MESTRADO/06_OUTPUTS"

[sincronizacao]
destino_outputs = "06_OUTPUTS"
modo = "incremental"
recursivo = false

[publicacao]
origem = "06_OUTPUTS"
excluir = [".pipeline", "README.md", ".gitignore", "LICENSE", "sincronizar.py"]
```

Todos os mains enxergam a pasta comum pelo `\graphicspath` (`{06_OUTPUTS/}` mais `{../06_OUTPUTS/}` ou `{../../06_OUTPUTS/}`, conforme a profundidade do main). Uma figura usada em mais de um documento existe uma única vez. Os nomes das figuras seguem os prefixos dos códigos (`00_` a `08_`); o bloco `9x` é reservado às figuras de documentos entregues e nunca é gerado por código (`90_Q1_` para a Qualificação I, `91_DIVQ2_` para o banner de divulgação da Qualificação II).

Fluxo cotidiano: o código mestre grava a figura na raiz de `06_OUTPUTS`; na raiz do projeto, `python3 sincronizar.py` publica a figura no Overleaf; todos os documentos passam a compilar com a versão nova.

# Tutorial de uso

## 12. Pré-requisitos

Antes de começar, confirme:

- Python 3.11 ou superior;
- Git instalado;
- Google Drive montado e acessível;
- conta Overleaf com Git Bridge habilitado;
- token Git válido do Overleaf;
- espaço para um clone temporário durante cada sincronização.

No Linux:

```bash
python3 --version
git --version
```

## 13. Instalação no Linux

Clone o código em armazenamento local, fora do Drive montado:

```bash
mkdir -p ~/projetos
cd ~/projetos
git clone https://github.com/Diass99/overleaf-drive-sync-template.git
cd overleaf-drive-sync-template
```

Valide a instalação:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -q
```

Não é necessário instalar bibliotecas externas: a versão atual usa somente a biblioteca padrão do Python.

### 13.1. Instalação e uso no Windows (v0.1.1)

Validado em 21/10/2026 com Git para Windows, Python (`py`) e Google Drive para Desktop. A raiz do Drive (`G:\Meu Drive`) não é detectada automaticamente e deve ser informada na sessão do PowerShell, junto com a variável que desativa a janela do Git Credential Manager:

```powershell
cd $env:USERPROFILE
git clone https://github.com/Diass99/overleaf-drive-sync-template
cd overleaf-drive-sync-template
$env:GOOGLE_DRIVE_ROOT = "G:\Meu Drive"
$env:GCM_INTERACTIVE = "never"
py criar_projeto.py
```

A sincronização de uma instância segue o mesmo padrão (`py sincronizar.py --simular` e `py sincronizar.py`). Diferenças de fim de linha (CRLF no Windows, LF no Overleaf) podem aparecer como `ATUALIZAR` no `.tex` da pasta raiz; isso não afeta a publicação, porque o `.tex` nunca é enviado ao Overleaf pela rotina.

## 14. Preparação manual no Overleaf

O Overleaf não oferece, nesse fluxo, uma etapa confiável para criar automaticamente um projeto novo por Git. Portanto, existe uma única intervenção manual na inicialização.

Há dois cenários.

### 14.1. Projeto do Overleaf já existente

Tenha em mãos a URL, por exemplo:

```text
https://www.overleaf.com/project/0123456789abcdef01234567
```

O assistente extrairá automaticamente o ID de 24 caracteres.

### 14.2. Projeto ainda inexistente

O assistente criará `CRIAR_PROJETO_OVERLEAF.zip` e mostrará seu caminho completo. Então:

1. abra o Overleaf;
2. escolha **New Project → Upload Project**;
3. selecione exatamente o ZIP informado;
4. aguarde a criação do projeto;
5. copie a URL do novo projeto;
6. volte ao terminal e cole a URL;
7. o assistente extrairá o ID e removerá o ZIP temporário.

## 15. Criar uma instância do projeto

Na raiz do repositório clonado:

```bash
python3 criar_projeto.py
```

O assistente solicitará:

1. raiz do Google Drive detectada ou informada manualmente;
2. nome do projeto;
3. pasta raiz da nova instância;
4. pasta que contém os outputs;
5. diretório de destino dentro do projeto, com padrão `figuras`;
6. arquivo LaTeX principal, com padrão `main.tex`;
7. nome e e-mail para os commits automáticos;
8. se o projeto já existe no Overleaf;
9. URL ou ID do projeto;
10. se deve testar a integração em modo simulado.

Os caminhos podem ser informados como absolutos ou relativos à raiz do Drive. Na configuração final eles são normalizados para caminhos relativos.

Para usar o modo "outputs no próprio projeto" (Seção 8.9), a pasta de outputs deve ficar dentro da pasta raiz da instância, e `destino_outputs` e `publicacao.origem` devem apontar para ela no `projeto.toml`.

Ao final, o assistente exibirá o caminho do projeto e os comandos cotidianos.

## 16. Primeiro teste seguro

Entre na pasta raiz gerada:

```bash
cd /CAMINHO/DA/PASTA_RAIZ
```

Execute uma simulação:

```bash
python3 sincronizar.py --simular
```

Se o token não estiver no ambiente, ele será solicitado sem aparecer na tela.

Confira no relatório da simulação:

- origem dos outputs correta;
- destino correto dentro do projeto (ou "Dispensado", no modo da v0.1.4);
- arquivos esperados listados;
- ausência de publicação de `.pipeline`, `sincronizar.py` e outros arquivos administrativos;
- indicação explícita de que nenhum arquivo persistente, commit ou push foi realizado.

## 17. Sincronização real

Depois de aprovar a simulação:

```bash
python3 sincronizar.py
```

O resultado esperado na primeira execução inclui cópias e a mensagem:

```text
Overleaf atualizado com sucesso.
```

Repita o comando sem alterar os outputs. O resultado esperado é:

```text
Overleaf já está atualizado; nenhum commit necessário.
```

Essa segunda execução é a verificação operacional de idempotência.

## 18. Copiar outputs sem acessar o Overleaf

Para atualizar apenas a pasta raiz no Drive:

```bash
python3 sincronizar.py --somente-copiar
```

Para apenas visualizar o que seria copiado:

```bash
python3 sincronizar.py --somente-copiar --simular
```

Esses modos não exigem token do Overleaf. No modo da v0.1.4 não há o que copiar, e o comando apenas informa que a etapa é dispensada.

## 19. Fornecer o token no Linux

### 19.1. Entrada interativa

Basta executar o sincronizador e colar o token quando solicitado. A entrada é oculta.

### 19.2. Variável de ambiente temporária

```bash
export OVERLEAF_GIT_TOKEN='SEU_TOKEN'
python3 sincronizar.py --simular
python3 sincronizar.py
unset OVERLEAF_GIT_TOKEN
```

Evite colocar o token diretamente em comandos que ficarão no histórico. Uma alternativa mais segura no Zsh é:

```zsh
read -s 'OVERLEAF_GIT_TOKEN?Token do Overleaf: '
echo
export OVERLEAF_GIT_TOKEN
python3 sincronizar.py
unset OVERLEAF_GIT_TOKEN
```

No Bash, a sintaxe equivalente é:

```bash
read -rsp 'Token do Overleaf: ' OVERLEAF_GIT_TOKEN
echo
export OVERLEAF_GIT_TOKEN
python3 sincronizar.py
unset OVERLEAF_GIT_TOKEN
```

## 20. Uso no Google Colab

### 20.1. Criar o Secret

No painel de Secrets do Colab, crie:

```text
OVERLEAF_GIT_TOKEN
```

Conceda ao notebook permissão para acessá-lo.

### 20.2. Célula inicial

Monte o Drive e mantenha o repositório em `/content`, que é armazenamento temporário rápido:

```python
from google.colab import drive
drive.mount('/content/drive')

from pathlib import Path
import subprocess

repo = Path('/content/overleaf-drive-sync-template')

if not (repo / '.git').is_dir():
    subprocess.run([
        'git', 'clone',
        'https://github.com/Diass99/overleaf-drive-sync-template.git',
        str(repo),
    ], check=True)
else:
    subprocess.run([
        'git', '-C', str(repo), 'pull', '--ff-only'
    ], check=True)
```

### 20.3. Criar novo projeto pelo Colab

```python
%run /content/overleaf-drive-sync-template/criar_projeto.py
```

Responda às perguntas. A raiz normal do Drive será `/content/drive/MyDrive`.

### 20.4. Sincronizar uma instância existente

```python
%run /content/drive/MyDrive/CAMINHO_DO_PROJETO/sincronizar.py --simular
```

Depois da conferência:

```python
%run /content/drive/MyDrive/CAMINHO_DO_PROJETO/sincronizar.py
```

O executável tenta obter `OVERLEAF_GIT_TOKEN` automaticamente por `google.colab.userdata`.

## 21. Atualizar a automação

No clone operacional:

```bash
cd ~/projetos/overleaf-drive-sync-template
git pull --ff-only
PYTHONPATH=src python3 -m unittest discover -s tests -q
```

O código já instalado em projetos antigos é uma cópia autônoma. Uma atualização futura do repositório não altera automaticamente essas instâncias.

Atualização de uma instância no Linux, preservando `projeto.toml`: enviar cada arquivo com `rclone copyto` a partir do clone local e conferir o MD5 (Seção 8.4). Exemplo para um arquivo:

```bash
rclone copyto ~/projetos/overleaf-drive-sync-template/src/overleaf_drive_sync/overleaf_git.py "gdrive:CAMINHO/DA/PASTA_RAIZ/.pipeline/overleaf_drive_sync/overleaf_git.py"
rclone lsjson --hash "gdrive:CAMINHO/DA/PASTA_RAIZ/.pipeline/overleaf_drive_sync/overleaf_git.py"
```

O `sincronizar.py` da raiz vem de `templates/sincronizar.py`. Em 26/11/2026 a instância do `PROJETO_DE_MESTRADO` foi atualizada para a v0.1.4 por um script que faz esse envio, confere o MD5 de cada arquivo e guarda os originais em `~/Downloads/ORGANIZACAO_DRIVE`.

## 22. Diagnóstico de problemas

| Sintoma | Causa provável | Correção |
|---|---|---|
| `OSError: [Errno 5] Input/output error` em `copystat` ou `listxattr` | tentativa de preservar metadados numa montagem Rclone | use a versão atual, baseada em `shutil.copyfile`; evite `copy2` |
| `cp --no-preserve=all` falha com erro de E/S na montagem | ajuste de permissões não suportado pelo Rclone | use `rclone copyto` ou `shutil.copyfile` e confira o MD5 |
| `sed -i` retorna erro no Drive | renomeação temporária incompatível com a montagem | altere em `/tmp`, valide e envie com `rclone copyto` |
| `403 rateLimitExceeded` em listagens | cota do cliente OAuth público do Rclone | usar o cliente OAuth próprio (Seção 9.5) |
| subpastas `00_BACKUP`/`99_OPERACIONAL` publicadas no Overleaf | instância anterior à v0.1.3 ou `recursivo = true` | atualizar a instância e usar `recursivo = false` |
| figura antiga do Overleaf volta para o Drive | instância anterior à v0.1.4 com destino igual à pasta de outputs | atualizar para a v0.1.4 |
| `Password authentication is not supported` no GitHub | foi usada a senha da conta | use PAT, GitHub CLI, credential manager ou SSH |
| GitHub API responde HTTP 401 | token inválido, incompleto ou colado incorretamente | gere/revise o PAT e suas permissões; não use token `olp_` |
| `read: -p: no coprocess` no Zsh | foi usada sintaxe de Bash no Zsh | use `read -s 'VAR?Mensagem: '` |
| `zsh: no matches found` | glob não encontrou arquivos ou não foi protegido por aspas | confirme o diretório atual e use aspas (`--include='*.tex'`) |
| Overleaf não recebe commit | não houve diferença no conteúdo | comportamento esperado; confira a mensagem de idempotência |
| raiz do Drive não detectada | montagem está em caminho não convencional | informe o caminho no assistente ou defina `GOOGLE_DRIVE_ROOT` |
| `desktop.ini` publicado no Overleaf | instância na v0.1.0 executada no Windows | atualizar a instância e apagar os `desktop.ini` do Overleaf |
| token pedido por janela do Git Credential Manager | GCM interceptando a autenticação no Windows | definir `$env:GCM_INTERACTIVE = "never"` na sessão |
| ID do projeto rejeitado | URL/ID não contém 24 caracteres hexadecimais | copie a URL completa da página do projeto |
| projeto local parece desatualizado | o modo simulado não persiste o backup | execute a sincronização real após validar a simulação |
| nova estrutura não aparece em `~/GoogleDrive` | cache de diretórios da montagem (72 h) após mudanças feitas pelo `rclone` direto | `systemctl --user restart rclone-gdrive.service` |
| outputs antigos continuam no destino | modo incremental não apaga arquivos | remova manualmente após conferência ou implemente modo espelho futuro |

## 23. Regras operacionais recomendadas

1. Escreva e edite o texto no Overleaf.
2. Gere resultados científicos na pasta de outputs configurada, com as figuras na raiz.
3. Execute primeiro `--simular` após mudanças de configuração.
4. Execute a sincronização real para publicar os produtos.
5. Não edite a URL Git para inserir o token.
6. Não versione `.env`, tokens ou credenciais.
7. Não mantenha `.git` dentro do Drive montado por Rclone.
8. Não copie a raiz inteira para o Overleaf; publique somente a árvore de outputs.
9. Rode os testes antes de publicar mudanças no código da automação.
10. Use `git pull --ff-only` para evitar merges implícitos na atualização do template.
11. Não edite manualmente a pasta de outputs no Overleaf; ela é alimentada pelo Drive.

## 24. Limpeza e itens temporários

Durante o desenvolvimento foram usados diretórios e arquivos descartáveis. A remoção deve ser feita somente depois de conferir os caminhos. Entre os candidatos registrados estavam:

```text
/home/vinicius/GoogleDrive/01_TEMPLATE_PROJETOS/00_OUTPUT_TESTE_EXTREMO
/home/vinicius/GoogleDrive/01_TEMPLATE_PROJETOS/02_TESTE_GERADO
/tmp/main.aux
/tmp/main.log
/tmp/main.pdf
/tmp/configuracao.py
/tmp/test_configuracao.py
/tmp/README.md
```

O projeto de teste no Overleaf também pode ser movido para a lixeira quando não for mais necessário. Este relatório não pressupõe que essa limpeza tenha sido executada.

## 25. Limitações atuais e próximos passos

- A criação inicial do projeto no Overleaf ainda requer upload manual do ZIP.
- O modo de sincronização é incremental, não espelho; exclusões não são propagadas.
- Instâncias já geradas não recebem automaticamente novas versões da automação.
- O assistente `criar_projeto.py` ainda não pergunta pelo modo "outputs no próprio projeto"; a configuração é ajustada no `projeto.toml`.
- O programa ainda não oferece uma interface gráfica.
- Não há integração automática com GitHub Actions, pois o fluxo principal depende do Drive e do Overleaf autenticados.
- As instâncias ARTIGO_DIS (antiga) e TESTE_Overleaf_Drive_Sync permanecem na v0.1.0.
- Não há tags nem releases publicadas no GitHub.

Melhorias possíveis:

1. comando de diagnóstico, como `sincronizar.py --verificar`;
2. pergunta do modo "outputs no próprio projeto" no assistente;
3. rotina segura para atualizar a automação instalada em projetos existentes;
4. modo espelho opcional com confirmação e lista prévia das exclusões;
5. logs estruturados e relatório final em JSON;
6. publicação de releases e tags semânticas no GitHub;
7. integração contínua para executar os 26 testes em diferentes versões do Python;
8. documentação específica para macOS (Windows documentado na v0.1.1);
9. pacote instalável com comando de terminal próprio.

## 26. Conclusão

O protótipo manual foi transformado em um sistema modular, testado e reutilizável. A solução preserva as características centrais solicitadas: escolha livre da pasta de outputs, cópia integral ou só do primeiro nível, funcionamento em diferentes computadores, configuração interativa, segurança do token, clone temporário e atualização automática do Overleaf.

O ponto decisivo foi estabelecer autoridades distintas: o Overleaf controla o texto e a pasta de outputs controla os produtos científicos. A v0.1.4 leva essa separação ao limite natural: a pasta de outputs dos códigos é a própria pasta de figuras dos documentos, com o mesmo nome no Drive e no Overleaf, sem cópia intermediária e sem risco de o Overleaf sobrescrever um produto novo.

Com o repositório público, a licença MIT, a documentação, os testes e a validação em Linux e Windows, o projeto deixou de ser um script específico para se tornar um template de automação científica que pode ser clonado, configurado e reutilizado em relatórios, qualificações, dissertações, teses e artigos futuros.
