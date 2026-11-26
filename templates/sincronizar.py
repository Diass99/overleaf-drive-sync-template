#!/usr/bin/env python3

from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path


RAIZ_PROJETO = Path(__file__).resolve().parent
PIPELINE = RAIZ_PROJETO / ".pipeline"
sys.path.insert(0, str(PIPELINE))

from overleaf_drive_sync.configuracao import (
    carregar_configuracao,
    detectar_raizes_drive,
    resolver_no_drive,
)
from overleaf_drive_sync.overleaf_git import (
    executar_fluxo_completo,
    imprimir_operacoes,
    resolver_dentro,
)
from overleaf_drive_sync.sincronizacao import (
    copiar_arvore_integral,
)


def obter_token(nome_variavel: str) -> str:
    token = os.environ.get(nome_variavel)

    if token:
        return token

    try:
        from google.colab import userdata

        token = userdata.get(nome_variavel)
        if token:
            return token
    except (ImportError, KeyError, RuntimeError):
        pass

    return getpass.getpass(
        f"Token do Overleaf ({nome_variavel}): "
    ).strip()


def localizar_drive_projeto() -> Path:
    raizes = detectar_raizes_drive(RAIZ_PROJETO)

    if not raizes:
        informado = input(
            "Raiz do Google Drive não detectada. "
            "Informe o caminho: "
        ).strip()

        caminho = Path(informado).expanduser().resolve()

        if not caminho.is_dir():
            raise FileNotFoundError(
                f"Raiz do Drive inexistente: {caminho}"
            )

        return caminho

    drive = raizes[0]
    print(f"Google Drive: {drive}")
    return drive


def analisar_argumentos():
    parser = argparse.ArgumentParser(
        description=(
            "Sincroniza outputs, pasta raiz e Overleaf."
        )
    )

    parser.add_argument(
        "--simular",
        action="store_true",
        help="Mostra as alterações sem persistir ou enviar.",
    )
    parser.add_argument(
        "--somente-copiar",
        action="store_true",
        help="Executa somente outputs → pasta raiz.",
    )

    return parser.parse_args()


def main() -> int:
    argumentos = analisar_argumentos()

    try:
        config = carregar_configuracao(
            PIPELINE / "projeto.toml"
        )
        drive_root = localizar_drive_projeto()
        origem_outputs = resolver_no_drive(
            config["drive"]["pasta_outputs"],
            drive_root,
        )

        if argumentos.somente_copiar:
            destino = resolver_dentro(
                RAIZ_PROJETO,
                config["sincronizacao"]["destino_outputs"],
                "sincronizacao.destino_outputs",
            )

            resultado = copiar_arvore_integral(
                origem_outputs,
                destino,
                simular=argumentos.simular,
                recursivo=bool(
                    config.get("sincronizacao", {}).get(
                        "recursivo",
                        True,
                    )
                ),
            )
            imprimir_operacoes(
                "Outputs → pasta raiz",
                resultado,
            )
            return 0

        nome_token = config["overleaf"]["token_env"]
        token = obter_token(nome_token)

        if not token:
            raise ValueError(
                "O token do Overleaf não foi informado."
            )

        executar_fluxo_completo(
            raiz_projeto=RAIZ_PROJETO,
            origem_outputs=origem_outputs,
            configuracao=config,
            token=token,
            simular=argumentos.simular,
        )

        return 0

    except (OSError, ValueError, RuntimeError) as erro:
        print(f"\nERRO: {erro}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
