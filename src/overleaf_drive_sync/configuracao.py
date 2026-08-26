from __future__ import annotations

import json
import os
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path


PROJECT_ID_RE = re.compile(r"(?<![0-9a-f])([0-9a-f]{24})(?![0-9a-f])")


@dataclass(frozen=True)
class ConfiguracaoProjeto:
    nome: str
    arquivo_principal: str
    pasta_outputs: str
    destino_outputs: str
    overleaf_project_id: str
    git_usuario: str
    git_email: str
    mensagem_commit: str = "Atualização automática do projeto"

    def validar(self) -> None:
        if not self.nome.strip():
            raise ValueError("O nome do projeto não pode ficar vazio.")

        if not self.arquivo_principal.endswith(".tex"):
            raise ValueError("O arquivo principal deve terminar em .tex.")

        validar_caminho_relativo(
            self.pasta_outputs,
            "pasta_outputs",
        )
        validar_caminho_relativo(
            self.destino_outputs,
            "destino_outputs",
        )

        if self.overleaf_project_id:
            extrair_project_id(self.overleaf_project_id)

        if not self.git_usuario.strip():
            raise ValueError("O nome do autor Git não pode ficar vazio.")

        if "@" not in self.git_email:
            raise ValueError("O e-mail Git informado não parece válido.")


def validar_caminho_relativo(valor: str, campo: str) -> Path:
    caminho = Path(valor)

    if caminho.is_absolute():
        raise ValueError(f"{campo} deve ser um caminho relativo.")

    if not caminho.parts:
        raise ValueError(f"{campo} não pode ficar vazio.")

    if ".." in caminho.parts:
        raise ValueError(f"{campo} não pode conter '..'.")

    return caminho


def detectar_raizes_drive(
    referencia: Path | None = None,
) -> list[Path]:
    candidatos: list[Path] = []

    variavel = os.environ.get("GOOGLE_DRIVE_ROOT")
    if variavel:
        candidatos.append(Path(variavel).expanduser())

    referencia = (referencia or Path.cwd()).resolve()

    for ancestral in (referencia, *referencia.parents):
        if ancestral.name in {"GoogleDrive", "MyDrive"}:
            candidatos.append(ancestral)
            break

    candidatos.extend(
        [
            Path("/content/drive/MyDrive"),
            Path.home() / "GoogleDrive",
        ]
    )

    encontrados: list[Path] = []
    vistos: set[str] = set()

    for candidato in candidatos:
        try:
            resolvido = candidato.expanduser().resolve()
        except OSError:
            continue

        chave = str(resolvido)

        if resolvido.is_dir() and chave not in vistos:
            encontrados.append(resolvido)
            vistos.add(chave)

    return encontrados


def extrair_project_id(valor: str) -> str:
    correspondencia = PROJECT_ID_RE.search(valor.strip().lower())

    if not correspondencia:
        raise ValueError(
            "Não foi encontrado um project_id válido do Overleaf. "
            "Cole a URL do projeto ou o ID de 24 caracteres."
        )

    return correspondencia.group(1)


def relativo_ao_drive(
    caminho: Path,
    drive_root: Path,
) -> str:
    caminho = caminho.expanduser().resolve()
    drive_root = drive_root.expanduser().resolve()

    try:
        relativo = caminho.relative_to(drive_root)
    except ValueError as erro:
        raise ValueError(
            f"O caminho {caminho} não está dentro do Drive {drive_root}."
        ) from erro

    return relativo.as_posix()


def resolver_no_drive(
    caminho_relativo: str,
    drive_root: Path,
) -> Path:
    relativo = validar_caminho_relativo(
        caminho_relativo,
        "caminho relativo ao Drive",
    )
    resolvido = (drive_root.resolve() / relativo).resolve()

    try:
        resolvido.relative_to(drive_root.resolve())
    except ValueError as erro:
        raise ValueError(
            "O caminho resolvido saiu da raiz do Google Drive."
        ) from erro

    return resolvido


def texto_toml(config: ConfiguracaoProjeto) -> str:
    config.validar()

    q = lambda valor: json.dumps(valor, ensure_ascii=False)

    return (
        "versao_configuracao = 1\n\n"
        "[projeto]\n"
        f"nome = {q(config.nome)}\n"
        f"arquivo_principal = {q(config.arquivo_principal)}\n\n"
        "[drive]\n"
        f"pasta_outputs = {q(config.pasta_outputs)}\n\n"
        "[overleaf]\n"
        f"project_id = {q(config.overleaf_project_id)}\n"
        'token_env = "OVERLEAF_GIT_TOKEN"\n\n'
        "[git]\n"
        f"usuario = {q(config.git_usuario)}\n"
        f"email = {q(config.git_email)}\n"
        f"mensagem_commit = {q(config.mensagem_commit)}\n\n"
        "[sincronizacao]\n"
        f"destino_outputs = {q(config.destino_outputs)}\n"
        'modo = "incremental"\n'
        "recursivo = true\n\n"
        "[publicacao]\n"
        f"origem = {q(config.destino_outputs)}\n"
        'excluir = [".pipeline", "README.md", ".gitignore", '
        '"LICENSE", "sincronizar.py"]\n'
    )


def salvar_configuracao(
    config: ConfiguracaoProjeto,
    destino: Path,
) -> None:
    conteudo = texto_toml(config)

    # Valida o texto produzido antes de gravá-lo.
    tomllib.loads(conteudo)

    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(conteudo, encoding="utf-8")


def carregar_configuracao(
    caminho: Path,
) -> dict:
    if not caminho.is_file():
        raise FileNotFoundError(
            f"Configuração não encontrada: {caminho}"
        )

    with caminho.open("rb") as arquivo:
        dados = tomllib.load(arquivo)

    if dados.get("versao_configuracao") != 1:
        raise ValueError("Versão de configuração não suportada.")

    return dados
