from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .sincronizacao import (
    ResultadoCopia,
    copiar_arvore_integral,
)


@dataclass
class ResultadoFluxo:
    backup_overleaf: ResultadoCopia
    copia_outputs: ResultadoCopia
    publicacao: ResultadoCopia
    houve_alteracoes_git: bool
    commit_realizado: bool
    push_realizado: bool


class ErroGit(RuntimeError):
    pass


def executar_git(
    argumentos: list[str],
    *,
    cwd: Path | None = None,
    ambiente: dict[str, str] | None = None,
    codigos_aceitos: set[int] | None = None,
    capturar: bool = False,
) -> subprocess.CompletedProcess:
    codigos_aceitos = codigos_aceitos or {0}

    resultado = subprocess.run(
        ["git", *argumentos],
        cwd=cwd,
        env=ambiente,
        check=False,
        text=True,
        capture_output=capturar,
    )

    if resultado.returncode not in codigos_aceitos:
        detalhe = ""

        if capturar:
            detalhe = (
                resultado.stderr.strip()
                or resultado.stdout.strip()
            )

        mensagem = (
            f"Git falhou com código {resultado.returncode}."
        )

        if detalhe:
            mensagem += f" {detalhe}"

        raise ErroGit(mensagem)

    return resultado


def resolver_dentro(
    raiz: Path,
    relativo: str,
    descricao: str,
) -> Path:
    raiz = raiz.expanduser().resolve()
    caminho = Path(relativo)

    if caminho.is_absolute() or ".." in caminho.parts:
        raise ValueError(
            f"{descricao} deve ser relativo e não pode conter '..'."
        )

    resolvido = (raiz / caminho).resolve()

    try:
        resolvido.relative_to(raiz)
    except ValueError as erro:
        raise ValueError(
            f"{descricao} aponta para fora da raiz permitida."
        ) from erro

    return resolvido


def criar_askpass(
    pasta_temporaria: Path,
) -> Path:
    askpass = pasta_temporaria / "git_askpass.sh"

    askpass.write_text(
        "#!/bin/sh\n"
        'case "$1" in\n'
        '  *Username*) printf "%s\\n" "git" ;;\n'
        '  *) printf "%s\\n" "$OVERLEAF_TOKEN_VALUE" ;;\n'
        "esac\n",
        encoding="utf-8",
    )
    askpass.chmod(0o700)

    return askpass


def criar_ambiente_git(
    pasta_temporaria: Path,
    token: str | None,
) -> dict[str, str]:
    ambiente = os.environ.copy()
    ambiente["GIT_TERMINAL_PROMPT"] = "0"

    if token:
        askpass = criar_askpass(pasta_temporaria)
        ambiente["GIT_ASKPASS"] = str(askpass)
        ambiente["OVERLEAF_TOKEN_VALUE"] = token

    return ambiente


def imprimir_operacoes(
    titulo: str,
    resultado: ResultadoCopia,
) -> None:
    print(f"\n{titulo}")

    for operacao in resultado.operacoes:
        print(operacao)

    print(f"  Novos:       {resultado.novos}")
    print(f"  Atualizados: {resultado.atualizados}")
    print(f"  Idênticos:   {resultado.identicos}")
    print(f"  Diretórios:  {resultado.diretorios}")


def executar_fluxo_completo(
    *,
    raiz_projeto: Path,
    origem_outputs: Path,
    configuracao: dict,
    token: str | None,
    simular: bool = False,
    repo_url: str | None = None,
) -> ResultadoFluxo:
    raiz_projeto = raiz_projeto.expanduser().resolve()
    origem_outputs = origem_outputs.expanduser().resolve()

    if not raiz_projeto.is_dir():
        raise FileNotFoundError(
            f"Pasta raiz inexistente: {raiz_projeto}"
        )

    if not origem_outputs.is_dir():
        raise FileNotFoundError(
            f"Pasta de outputs inexistente: {origem_outputs}"
        )

    project_id = configuracao["overleaf"]["project_id"]
    destino_relativo = configuracao[
        "sincronizacao"
    ]["destino_outputs"]
    publicacao_relativa = configuracao[
        "publicacao"
    ]["origem"]

    destino_outputs = resolver_dentro(
        raiz_projeto,
        destino_relativo,
        "sincronizacao.destino_outputs",
    )
    origem_publicacao = resolver_dentro(
        raiz_projeto,
        publicacao_relativa,
        "publicacao.origem",
    )

    exclusoes = set(
        configuracao.get("publicacao", {}).get(
            "excluir",
            [],
        )
    )
    exclusoes.add(".git")

    if repo_url is None:
        if not project_id:
            raise ValueError(
                "O project_id do Overleaf não foi configurado."
            )

        if not token:
            raise ValueError(
                "O token do Overleaf não foi fornecido."
            )

        repo_url = (
            f"https://git@git.overleaf.com/{project_id}"
        )

    with tempfile.TemporaryDirectory(
        prefix="overleaf_drive_sync_"
    ) as temporario_texto:
        temporario = Path(temporario_texto)
        clone = temporario / "clone"
        ambiente = criar_ambiente_git(
            temporario,
            token,
        )

        print("\nClonando o projeto mais recente do Overleaf...")

        executar_git(
            ["clone", "--quiet", repo_url, str(clone)],
            ambiente=ambiente,
            capturar=True,
        )

        # Overleaf é a fonte oficial do texto.
        backup = copiar_arvore_integral(
            clone,
            raiz_projeto,
            simular=simular,
            excluir=exclusoes,
        )
        imprimir_operacoes(
            "Overleaf → pasta raiz",
            backup,
        )

        # Outputs são a fonte oficial dos produtos gerados.
        copia_outputs = copiar_arvore_integral(
            origem_outputs,
            destino_outputs,
            simular=simular,
        )
        imprimir_operacoes(
            "Outputs → pasta raiz",
            copia_outputs,
        )

        if simular:
            # Monta em área temporária o estado que seria publicado.
            sombra = temporario / "publicacao_sombra"
            sombra.mkdir()

            if origem_publicacao.is_dir():
                copiar_arvore_integral(
                    origem_publicacao,
                    sombra,
                )

            copiar_arvore_integral(
                origem_outputs,
                sombra,
            )

            fonte_publicacao = sombra
        else:
            fonte_publicacao = origem_publicacao

        destino_clone = resolver_dentro(
            clone,
            publicacao_relativa,
            "publicacao.origem no clone",
        )

        publicacao = copiar_arvore_integral(
            fonte_publicacao,
            destino_clone,
        )
        imprimir_operacoes(
            "Pasta raiz → clone do Overleaf",
            publicacao,
        )

        executar_git(
            [
                "config",
                "user.name",
                configuracao["git"]["usuario"],
            ],
            cwd=clone,
            ambiente=ambiente,
        )
        executar_git(
            [
                "config",
                "user.email",
                configuracao["git"]["email"],
            ],
            cwd=clone,
            ambiente=ambiente,
        )

        executar_git(
            [
                "add",
                "-A",
                "--",
                publicacao_relativa,
            ],
            cwd=clone,
            ambiente=ambiente,
        )

        diferenca = executar_git(
            ["diff", "--cached", "--quiet"],
            cwd=clone,
            ambiente=ambiente,
            codigos_aceitos={0, 1},
        )

        houve_alteracoes = diferenca.returncode == 1

        if simular:
            print(
                "\nSIMULAÇÃO: nenhum arquivo persistente, "
                "commit ou push foi realizado."
            )

            return ResultadoFluxo(
                backup,
                copia_outputs,
                publicacao,
                houve_alteracoes,
                False,
                False,
            )

        if not houve_alteracoes:
            print(
                "\nOverleaf já está atualizado; "
                "nenhum commit necessário."
            )

            return ResultadoFluxo(
                backup,
                copia_outputs,
                publicacao,
                False,
                False,
                False,
            )

        instante = datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M UTC"
        )
        mensagem = (
            f'{configuracao["git"]["mensagem_commit"]}'
            f" — {instante}"
        )

        executar_git(
            ["commit", "--quiet", "-m", mensagem],
            cwd=clone,
            ambiente=ambiente,
        )
        executar_git(
            ["push", "--quiet", "origin", "HEAD"],
            cwd=clone,
            ambiente=ambiente,
            capturar=True,
        )

        print("\nOverleaf atualizado com sucesso.")

        return ResultadoFluxo(
            backup,
            copia_outputs,
            publicacao,
            True,
            True,
            True,
        )
