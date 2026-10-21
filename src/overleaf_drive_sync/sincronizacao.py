from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass, field
from pathlib import Path


# Metadados criados pelo sistema operacional ou pelo cliente do Drive
# (desktop.ini: Google Drive para Desktop e Explorer no Windows).
# Nunca fazem parte do projeto e são ignorados em qualquer nível.
ARQUIVOS_DE_SISTEMA = frozenset(
    {
        "desktop.ini",
        "thumbs.db",
        "ehthumbs.db",
        ".ds_store",
    }
)


def e_arquivo_de_sistema(caminho: Path) -> bool:
    return caminho.name.lower() in ARQUIVOS_DE_SISTEMA


@dataclass
class ResultadoCopia:
    novos: int = 0
    atualizados: int = 0
    identicos: int = 0
    diretorios: int = 0
    operacoes: list[str] = field(default_factory=list)

    @property
    def alteracoes(self) -> int:
        return self.novos + self.atualizados


def hash_arquivo(
    caminho: Path,
    tamanho_bloco: int = 1024 * 1024,
) -> str:
    calculador = hashlib.sha256()

    with caminho.open("rb") as arquivo:
        while bloco := arquivo.read(tamanho_bloco):
            calculador.update(bloco)

    return calculador.hexdigest()


def arquivos_iguais(
    origem: Path,
    destino: Path,
) -> bool:
    if not destino.is_file():
        return False

    if origem.stat().st_size != destino.stat().st_size:
        return False

    return hash_arquivo(origem) == hash_arquivo(destino)


def validar_arvores(
    origem: Path,
    destino: Path,
) -> tuple[Path, Path]:
    origem = origem.expanduser().resolve()
    destino = destino.expanduser().resolve()

    if not origem.is_dir():
        raise FileNotFoundError(
            f"Pasta de origem inexistente: {origem}"
        )

    if origem == destino:
        raise ValueError("Origem e destino não podem ser iguais.")

    try:
        destino.relative_to(origem)
    except ValueError:
        pass
    else:
        raise ValueError(
            "O destino não pode estar dentro da origem."
        )

    try:
        origem.relative_to(destino)
    except ValueError:
        pass
    else:
        raise ValueError(
            "A origem não pode estar dentro do destino."
        )

    return origem, destino


def copiar_arvore_integral(
    origem: Path,
    destino: Path,
    *,
    simular: bool = False,
    excluir: set[str] | None = None,
) -> ResultadoCopia:
    origem, destino = validar_arvores(origem, destino)
    excluir = set(excluir or ())
    resultado = ResultadoCopia()

    itens = sorted(
        origem.rglob("*"),
        key=lambda item: item.relative_to(origem).as_posix(),
    )

    for item in itens:
        relativo = item.relative_to(origem)

        if relativo.parts and relativo.parts[0] in excluir:
            continue

        if e_arquivo_de_sistema(item) and not item.is_dir():
            continue

        alvo = destino / relativo

        if item.is_symlink():
            raise RuntimeError(
                f"Link simbólico não suportado: {item}"
            )

        if item.is_dir():
            if alvo.exists() and not alvo.is_dir():
                raise RuntimeError(
                    f"Conflito: deveria ser diretório: {alvo}"
                )

            resultado.diretorios += 1

            if not simular:
                alvo.mkdir(parents=True, exist_ok=True)

            continue

        if not item.is_file():
            raise RuntimeError(
                f"Tipo de arquivo não suportado: {item}"
            )

        if alvo.exists() and not alvo.is_file():
            raise RuntimeError(
                f"Conflito: deveria ser arquivo: {alvo}"
            )

        if arquivos_iguais(item, alvo):
            resultado.identicos += 1
            continue

        if alvo.exists():
            resultado.atualizados += 1
            acao = "ATUALIZAR"
        else:
            resultado.novos += 1
            acao = "COPIAR"

        resultado.operacoes.append(
            f"{acao}: {item} -> {alvo}"
        )

        if not simular:
            alvo.parent.mkdir(parents=True, exist_ok=True)

            # copyfile evita xattrs incompatíveis com Rclone/GDrive.
            # Uma interrupção é corrigida na próxima execução pelo SHA-256.
            shutil.copyfile(item, alvo)

    return resultado
