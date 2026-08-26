#!/usr/bin/env python3

from __future__ import annotations

import getpass
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


RAIZ_REPOSITORIO = Path(__file__).resolve().parent
SRC = RAIZ_REPOSITORIO / "src"
sys.path.insert(0, str(SRC))

from overleaf_drive_sync.configuracao import (
    ConfiguracaoProjeto,
    detectar_raizes_drive,
    extrair_project_id,
    relativo_ao_drive,
    resolver_no_drive,
    salvar_configuracao,
    validar_caminho_relativo,
)
from overleaf_drive_sync.overleaf_git import (
    executar_fluxo_completo,
)


def perguntar(
    mensagem: str,
    *,
    padrao: str | None = None,
    permitir_vazio: bool = False,
) -> str:
    sufixo = f" [{padrao}]" if padrao is not None else ""

    while True:
        resposta = input(f"{mensagem}{sufixo}: ").strip()

        if resposta:
            return resposta

        if padrao is not None:
            return padrao

        if permitir_vazio:
            return ""

        print("Este campo é obrigatório.")


def confirmar(
    mensagem: str,
    *,
    padrao: bool = True,
) -> bool:
    indicador = "S/n" if padrao else "s/N"

    while True:
        resposta = input(
            f"{mensagem} [{indicador}]: "
        ).strip().lower()

        if not resposta:
            return padrao

        if resposta in {"s", "sim", "y", "yes"}:
            return True

        if resposta in {"n", "não", "nao", "no"}:
            return False

        print("Responda com sim ou não.")


def valor_git_global(campo: str) -> str | None:
    resultado = subprocess.run(
        ["git", "config", "--global", "--get", campo],
        check=False,
        text=True,
        capture_output=True,
    )

    valor = resultado.stdout.strip()
    return valor or None


def escolher_drive() -> Path:
    detectados = detectar_raizes_drive(
        RAIZ_REPOSITORIO
    )

    print("\n=== Google Drive ===")

    if detectados:
        for indice, caminho in enumerate(detectados, start=1):
            print(f"  {indice}. {caminho}")

        resposta = perguntar(
            "Escolha o número ou informe outro caminho",
            padrao="1",
        )

        if resposta.isdigit():
            indice = int(resposta)

            if 1 <= indice <= len(detectados):
                return detectados[indice - 1]

            raise ValueError("Número de Drive inválido.")

        escolhido = Path(resposta).expanduser().resolve()
    else:
        resposta = perguntar(
            "Informe a raiz montada do Google Drive"
        )
        escolhido = Path(resposta).expanduser().resolve()

    if not escolhido.is_dir():
        raise FileNotFoundError(
            f"Raiz do Drive inexistente: {escolhido}"
        )

    return escolhido


def caminho_relativo_do_drive(
    entrada: str,
    drive_root: Path,
    *,
    deve_existir: bool,
) -> str:
    informado = Path(entrada).expanduser()

    if informado.is_absolute():
        relativo = relativo_ao_drive(
            informado,
            drive_root,
        )
    else:
        relativo = informado.as_posix()
        validar_caminho_relativo(
            relativo,
            "caminho relativo ao Drive",
        )

    resolvido = resolver_no_drive(
        relativo,
        drive_root,
    )

    if deve_existir and not resolvido.is_dir():
        raise FileNotFoundError(
            f"Pasta inexistente: {resolvido}"
        )

    return relativo


def preparar_pasta_projeto(
    drive_root: Path,
) -> tuple[Path, str]:
    while True:
        entrada = perguntar(
            "Pasta raiz do novo projeto "
            "(relativa ao Drive ou caminho absoluto)"
        )

        try:
            relativo = caminho_relativo_do_drive(
                entrada,
                drive_root,
                deve_existir=False,
            )
            destino = resolver_no_drive(
                relativo,
                drive_root,
            )
        except (ValueError, FileNotFoundError) as erro:
            print(f"Entrada inválida: {erro}")
            continue

        if destino.exists() and any(destino.iterdir()):
            print(f"\nA pasta já contém arquivos: {destino}")

            if not confirmar(
                "Usar essa pasta sem apagar seu conteúdo?",
                padrao=False,
            ):
                continue

        destino.mkdir(parents=True, exist_ok=True)
        return destino, relativo


def preparar_outputs(
    drive_root: Path,
) -> tuple[Path, str]:
    while True:
        entrada = perguntar(
            "Pasta de outputs "
            "(relativa ao Drive ou caminho absoluto)"
        )

        try:
            relativo = caminho_relativo_do_drive(
                entrada,
                drive_root,
                deve_existir=True,
            )
            return (
                resolver_no_drive(relativo, drive_root),
                relativo,
            )
        except (ValueError, FileNotFoundError) as erro:
            print(f"Entrada inválida: {erro}")


def copiar_automacao(
    pasta_projeto: Path,
) -> None:
    pipeline = pasta_projeto / ".pipeline"
    pacote_destino = pipeline / "overleaf_drive_sync"

    pipeline.mkdir(parents=True, exist_ok=True)

    shutil.copytree(
        SRC / "overleaf_drive_sync",
        pacote_destino,
        dirs_exist_ok=True,
        copy_function=shutil.copyfile,
        ignore=shutil.ignore_patterns(
            "__pycache__",
            "*.pyc",
        ),
    )

    shutil.copyfile(
        RAIZ_REPOSITORIO / "templates" / "sincronizar.py",
        pasta_projeto / "sincronizar.py",
    )


def preparar_main_tex(
    pasta_projeto: Path,
    arquivo_principal: str,
) -> Path:
    destino = pasta_projeto / arquivo_principal

    if destino.exists():
        print(f"Arquivo LaTeX preservado: {destino}")
        return destino

    destino.parent.mkdir(parents=True, exist_ok=True)

    shutil.copyfile(
        RAIZ_REPOSITORIO / "templates" / "main.tex",
        destino,
    )

    print(f"Arquivo LaTeX inicial criado: {destino}")
    return destino


def criar_zip_inicial(
    pasta_projeto: Path,
    destino_outputs: str,
) -> Path:
    zip_path = (
        pasta_projeto / "CRIAR_PROJETO_OVERLEAF.zip"
    )

    exclusoes = {
        ".pipeline",
        ".git",
        "README.md",
        ".gitignore",
        "LICENSE",
        "sincronizar.py",
        "CRIAR_PROJETO_OVERLEAF.zip",
        Path(destino_outputs).parts[0],
    }

    with zipfile.ZipFile(
        zip_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as arquivo_zip:
        for item in sorted(pasta_projeto.rglob("*")):
            relativo = item.relative_to(pasta_projeto)

            if relativo.parts[0] in exclusoes:
                continue

            if item.is_file():
                arquivo_zip.write(
                    item,
                    relativo.as_posix(),
                )

    return zip_path


def solicitar_projeto_overleaf(
    pasta_projeto: Path,
    destino_outputs: str,
) -> str:
    print("\n=== Overleaf ===")

    if confirmar(
        "O projeto já existe no Overleaf?",
        padrao=False,
    ):
        entrada = perguntar(
            "Cole a URL ou o project_id do Overleaf"
        )
        return extrair_project_id(entrada)

    zip_path = criar_zip_inicial(
        pasta_projeto,
        destino_outputs,
    )

    print(
        "\nFoi criado o pacote inicial:\n"
        f"  {zip_path}\n\n"
        "No Overleaf:\n"
        "  1. New Project → Upload Project\n"
        "  2. selecione o ZIP acima\n"
        "  3. aguarde a compilação\n"
        "  4. copie a URL do projeto criado\n"
    )

    while True:
        entrada = perguntar(
            "Cole agora a URL ou o project_id"
        )

        try:
            project_id = extrair_project_id(entrada)
            break
        except ValueError as erro:
            print(f"Entrada inválida: {erro}")

    try:
        zip_path.unlink()
    except OSError:
        print(
            f"Aviso: remova manualmente o ZIP: {zip_path}"
        )

    return project_id


def main() -> int:
    print(
        "\n"
        "============================================\n"
        " OVERLEAF DRIVE SYNC — CONFIGURAÇÃO INICIAL\n"
        "============================================\n"
    )

    try:
        drive_root = escolher_drive()
        print(f"Drive selecionado: {drive_root}")

        nome = perguntar("Nome do projeto")
        pasta_projeto, relativo_projeto = (
            preparar_pasta_projeto(drive_root)
        )
        origem_outputs, relativo_outputs = (
            preparar_outputs(drive_root)
        )

        destino_outputs = perguntar(
            "Diretório dos outputs dentro do projeto",
            padrao="figuras",
        )
        validar_caminho_relativo(
            destino_outputs,
            "destino_outputs",
        )

        arquivo_principal = perguntar(
            "Arquivo LaTeX principal",
            padrao="main.tex",
        )

        if not arquivo_principal.endswith(".tex"):
            raise ValueError(
                "O arquivo principal deve terminar em .tex."
            )

        usuario_git = perguntar(
            "Nome usado nos commits",
            padrao=(
                valor_git_global("user.name")
                or "Automação científica"
            ),
        )
        email_git = perguntar(
            "E-mail usado nos commits",
            padrao=(
                valor_git_global("user.email")
                or "automacao@projeto.local"
            ),
        )

        copiar_automacao(pasta_projeto)
        preparar_main_tex(
            pasta_projeto,
            arquivo_principal,
        )

        project_id = solicitar_projeto_overleaf(
            pasta_projeto,
            destino_outputs,
        )

        config = ConfiguracaoProjeto(
            nome=nome,
            arquivo_principal=arquivo_principal,
            pasta_outputs=relativo_outputs,
            destino_outputs=destino_outputs,
            overleaf_project_id=project_id,
            git_usuario=usuario_git,
            git_email=email_git,
        )

        salvar_configuracao(
            config,
            pasta_projeto / ".pipeline" / "projeto.toml",
        )

        print(
            "\nConfiguração criada com sucesso:\n"
            f"  Projeto: {pasta_projeto}\n"
            f"  Drive: {drive_root}\n"
            f"  Caminho relativo: {relativo_projeto}\n"
            f"  Outputs: {origem_outputs}\n"
            f"  Overleaf ID: {project_id}\n"
        )

        if confirmar(
            "Testar agora toda a integração em modo simulado?",
            padrao=True,
        ):
            token = getpass.getpass(
                "Token do Overleaf "
                "(não será armazenado): "
            ).strip()

            if not token:
                raise ValueError(
                    "Token não informado."
                )

            executar_fluxo_completo(
                raiz_projeto=pasta_projeto,
                origem_outputs=origem_outputs,
                configuracao={
                    **{
                        "projeto": {
                            "nome": config.nome,
                            "arquivo_principal": (
                                config.arquivo_principal
                            ),
                        },
                        "drive": {
                            "pasta_outputs": (
                                config.pasta_outputs
                            ),
                        },
                        "overleaf": {
                            "project_id": (
                                config.overleaf_project_id
                            ),
                            "token_env": (
                                "OVERLEAF_GIT_TOKEN"
                            ),
                        },
                        "git": {
                            "usuario": config.git_usuario,
                            "email": config.git_email,
                            "mensagem_commit": (
                                config.mensagem_commit
                            ),
                        },
                        "sincronizacao": {
                            "destino_outputs": (
                                config.destino_outputs
                            ),
                        },
                        "publicacao": {
                            "origem": (
                                config.destino_outputs
                            ),
                            "excluir": [
                                ".pipeline",
                                "README.md",
                                ".gitignore",
                                "LICENSE",
                                "sincronizar.py",
                            ],
                        },
                    }
                },
                token=token,
                simular=True,
            )

        print(
            "\nProjeto pronto.\n"
            "Para sincronizar futuramente:\n\n"
            f"  cd {pasta_projeto}\n"
            "  python3 sincronizar.py --simular\n"
            "  python3 sincronizar.py\n"
        )

        return 0

    except KeyboardInterrupt:
        print("\nConfiguração cancelada.")
        return 130
    except (OSError, ValueError, RuntimeError) as erro:
        print(f"\nERRO: {erro}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
