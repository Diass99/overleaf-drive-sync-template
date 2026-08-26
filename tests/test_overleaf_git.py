import subprocess
import tempfile
import unittest
from pathlib import Path

from overleaf_drive_sync.overleaf_git import (
    executar_fluxo_completo,
)


def git(*argumentos, cwd=None):
    subprocess.run(
        ["git", *argumentos],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def configuracao_teste():
    return {
        "projeto": {
            "nome": "Projeto de teste",
            "arquivo_principal": "main.tex",
        },
        "overleaf": {
            "project_id": "6a8f5f1d5b99d914f178ce0f",
        },
        "git": {
            "usuario": "Teste automatizado",
            "email": "teste@example.com",
            "mensagem_commit": "Atualiza outputs",
        },
        "sincronizacao": {
            "destino_outputs": "figuras",
        },
        "publicacao": {
            "origem": "figuras",
            "excluir": [
                ".pipeline",
                "README.md",
                ".gitignore",
                "LICENSE",
                "sincronizar.py",
            ],
        },
    }


class TestOverleafGit(unittest.TestCase):
    def preparar_remoto(self, raiz):
        remoto = raiz / "overleaf.git"
        semente = raiz / "semente"

        git("init", "--bare", "--initial-branch=master", remoto)
        git("init", "--initial-branch=master", semente)
        git("config", "user.name", "Teste", cwd=semente)
        git(
            "config",
            "user.email",
            "teste@example.com",
            cwd=semente,
        )

        (semente / "main.tex").write_text(
            "texto mais recente do Overleaf",
            encoding="utf-8",
        )

        git("add", "main.tex", cwd=semente)
        git("commit", "-m", "Projeto inicial", cwd=semente)
        git("remote", "add", "origin", str(remoto), cwd=semente)
        git("push", "-u", "origin", "master", cwd=semente)

        return remoto

    def test_fluxo_preserva_texto_remoto_e_publica_outputs(self):
        with tempfile.TemporaryDirectory() as temporario:
            raiz = Path(temporario)
            remoto = self.preparar_remoto(raiz)
            projeto = raiz / "projeto"
            outputs = raiz / "outputs"

            projeto.mkdir()
            outputs.mkdir()

            (projeto / "main.tex").write_text(
                "texto local antigo",
                encoding="utf-8",
            )
            (outputs / "figura.png").write_bytes(b"imagem nova")

            resultado = executar_fluxo_completo(
                raiz_projeto=projeto,
                origem_outputs=outputs,
                configuracao=configuracao_teste(),
                token=None,
                repo_url=str(remoto),
            )

            self.assertEqual(
                (projeto / "main.tex").read_text(
                    encoding="utf-8"
                ),
                "texto mais recente do Overleaf",
            )
            self.assertEqual(
                (projeto / "figuras" / "figura.png").read_bytes(),
                b"imagem nova",
            )
            self.assertTrue(resultado.commit_realizado)
            self.assertTrue(resultado.push_realizado)

            verificacao = raiz / "verificacao"
            git("clone", str(remoto), verificacao)

            self.assertEqual(
                (verificacao / "main.tex").read_text(
                    encoding="utf-8"
                ),
                "texto mais recente do Overleaf",
            )
            self.assertEqual(
                (
                    verificacao
                    / "figuras"
                    / "figura.png"
                ).read_bytes(),
                b"imagem nova",
            )

            segunda = executar_fluxo_completo(
                raiz_projeto=projeto,
                origem_outputs=outputs,
                configuracao=configuracao_teste(),
                token=None,
                repo_url=str(remoto),
            )

            self.assertFalse(segunda.commit_realizado)
            self.assertFalse(segunda.push_realizado)

    def test_simulacao_nao_altera_projeto_nem_remoto(self):
        with tempfile.TemporaryDirectory() as temporario:
            raiz = Path(temporario)
            remoto = self.preparar_remoto(raiz)
            projeto = raiz / "projeto"
            outputs = raiz / "outputs"

            projeto.mkdir()
            outputs.mkdir()

            (projeto / "main.tex").write_text(
                "texto local antigo",
                encoding="utf-8",
            )
            (outputs / "figura.png").write_bytes(b"imagem nova")

            resultado = executar_fluxo_completo(
                raiz_projeto=projeto,
                origem_outputs=outputs,
                configuracao=configuracao_teste(),
                token=None,
                simular=True,
                repo_url=str(remoto),
            )

            self.assertEqual(
                (projeto / "main.tex").read_text(
                    encoding="utf-8"
                ),
                "texto local antigo",
            )
            self.assertFalse((projeto / "figuras").exists())
            self.assertFalse(resultado.commit_realizado)
            self.assertFalse(resultado.push_realizado)
            self.assertTrue(resultado.houve_alteracoes_git)

            verificacao = raiz / "verificacao"
            git("clone", str(remoto), verificacao)

            self.assertFalse(
                (verificacao / "figuras" / "figura.png").exists()
            )


if __name__ == "__main__":
    unittest.main()
