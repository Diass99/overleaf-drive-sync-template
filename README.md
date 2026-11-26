# Overleaf Drive Sync

Automação portátil entre Google Drive, outputs científicos e o Git Bridge do
Overleaf.

O sistema transfere produtos gerados por pipelines científicos para projetos
LaTeX sem cópia manual e sem permitir que um arquivo `.tex` local antigo
sobrescreva uma edição mais recente feita no Overleaf.

## Arquitetura

O Overleaf é a fonte oficial do texto. A pasta de outputs é a fonte oficial
dos produtos científicos.

Em cada sincronização:

1. o projeto mais recente é clonado do Overleaf;
2. o texto remoto é copiado para a pasta raiz no Drive;
3. todo o conteúdo da pasta de outputs é copiado;
4. somente os outputs são enviados ao Overleaf;
5. commit e push ocorrem apenas quando existem alterações.

## Recursos

- assistente interativo para criação de projetos;
- detecção automática do Google Drive;
- caminhos portáteis entre Linux e Google Colab;
- configuração gerada sem edição manual;
- cópia de arquivos ocultos e subdiretórios;
- comparação por tamanho e SHA-256;
- execução idempotente e modo de simulação;
- token fora do código e do TOML;
- suporte aos Secrets do Google Colab;
- clone Git sempre temporário.

## Requisitos

- Python 3.11 ou superior;
- Git;
- Google Drive montado;
- conta Overleaf com acesso ao Git Bridge;
- token Git do Overleaf.

O programa utiliza somente a biblioteca padrão do Python.

## Instalação

Clone o repositório fora do Drive montado por Rclone:

    git clone https://github.com/Diass99/overleaf-drive-sync-template.git
    cd overleaf-drive-sync-template

## Criar um projeto

Execute:

    python3 criar_projeto.py

O assistente pergunta a raiz do Drive, nome e pasta do projeto, pasta de
outputs, arquivo LaTeX principal, identidade Git e URL do Overleaf. A
configuração é gerada automaticamente.

Quando o projeto ainda não existe no Overleaf, o assistente:

1. cria a pasta raiz;
2. instala a automação;
3. cria um `main.tex` inicial;
4. gera `CRIAR_PROJETO_OVERLEAF.zip`;
5. aguarda o upload em `New Project → Upload Project`;
6. solicita a URL criada;
7. extrai o `project_id`;
8. remove o ZIP temporário.

Essa é a única inicialização manual obrigatória por projeto.

## Sincronização cotidiana

Entre na pasta raiz gerada e simule:

    python3 sincronizar.py --simular

Execute a sincronização real:

    python3 sincronizar.py

Copie apenas os outputs para a pasta raiz:

    python3 sincronizar.py --somente-copiar

Simule somente essa cópia:

    python3 sincronizar.py --somente-copiar --simular

## Token do Overleaf

O token nunca é gravado no código nem em `projeto.toml`.

Se não estiver disponível no ambiente, o programa o solicita de forma oculta.
Em Linux, também pode ser fornecido pela variável:

    OVERLEAF_GIT_TOKEN

Não grave tokens em notebooks, URLs, histórico do terminal ou arquivos
versionados. Revogue imediatamente qualquer token exposto.

## Google Colab

Crie um Secret chamado `OVERLEAF_GIT_TOKEN`.

Na Célula 0, monte o Drive:

    from google.colab import drive
    drive.mount("/content/drive")

Clone ou atualize este repositório em `/content`, não dentro do Drive.

Para executar o assistente no notebook:

    %run /content/overleaf-drive-sync-template/criar_projeto.py

Para sincronizar uma instância existente:

    %run /content/drive/MyDrive/CAMINHO_DO_PROJETO/sincronizar.py --simular

O executável procura o token automaticamente em `google.colab.userdata`.

## Idempotência e segurança

- arquivos idênticos não são regravados;
- somente arquivos novos ou alterados são copiados;
- nenhum commit é criado quando o Overleaf já está atualizado;
- execuções interrompidas são corrigidas na passagem seguinte;
- arquivos antigos não são apagados no modo incremental;
- o clone Git é sempre temporário;
- `.git` nunca é mantido no Google Drive;
- somente `[publicacao].origem` é enviado ao Overleaf;
- metadados do sistema (`desktop.ini`, `Thumbs.db`, `.DS_Store`) são
  ignorados em qualquer nível;
- o token é entregue ao Git por `GIT_ASKPASS` temporário.

## Estrutura gerada

    PASTA_RAIZ/
    ├── main.tex
    ├── figuras/
    ├── sincronizar.py
    └── .pipeline/
        ├── projeto.toml
        └── overleaf_drive_sync/

## Testes

Execute:

    PYTHONPATH=src python3 -m unittest discover -s tests -v

A suíte cobre configuração, caminhos, arquivos ocultos, subdiretórios,
SHA-256, idempotência, simulação, preservação do texto remoto, publicação
exclusiva dos outputs, Git remoto descartável e geração de projetos.

## Estado

Versão atual: `0.1.1-alpha`.

O fluxo completo foi validado em Linux, com Google Drive montado por Rclone,
e em Windows, com Google Drive para Desktop, em projetos reais do Overleaf.

No Windows, a raiz do Drive (`G:\Meu Drive`) não é detectada
automaticamente; defina-a na sessão antes de executar:

    $env:GOOGLE_DRIVE_ROOT = "G:\Meu Drive"

Para que o token seja solicitado pela própria rotina, e não por uma janela
do Git Credential Manager, defina também:

    $env:GCM_INTERACTIVE = "never"

## Licença

MIT License.

Copyright © 2026 Vinícius José Dias.

## Relatório técnico

Arquitetura, decisões, histórico de versões e tutorial: [docs/RELATORIO_TECNICO.md](docs/RELATORIO_TECNICO.md).
