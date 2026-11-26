import subprocess
import tempfile
import unittest
from pathlib import Path

from overleaf_drive_sync.overleaf_git import executar_fluxo_completo


def git(*args, cwd=None):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


class TestOutputsNoProjeto(unittest.TestCase):
    """destino_outputs igual à pasta de outputs: a mesma pasta no Drive e no Overleaf."""

    def preparar(self, base: Path):
        remoto = base / "overleaf.git"
        git("init", "--quiet", "--bare", str(remoto))
        trabalho = base / "trabalho"
        git("clone", "--quiet", str(remoto), str(trabalho))
        (trabalho / "06_OUTPUTS").mkdir()
        (trabalho / "06_OUTPUTS" / "01_figura.png").write_bytes(b"antiga")
        (trabalho / "08_DOC").mkdir()
        (trabalho / "08_DOC" / "main.tex").write_text("tex")
        git("add", "-A", cwd=trabalho)
        git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "--quiet", "-m", "i", cwd=trabalho)
        git("push", "--quiet", "origin", "HEAD", cwd=trabalho)

        raiz = base / "raiz"
        outputs = raiz / "06_OUTPUTS"
        (outputs / "00_BACKUP").mkdir(parents=True)
        (outputs / "99_OPERACIONAL").mkdir()
        (outputs / "01_figura.png").write_bytes(b"nova")
        (outputs / "02_figura.png").write_bytes(b"segunda")
        (outputs / "00_BACKUP" / "velha.png").write_bytes(b"velha")
        (outputs / "99_OPERACIONAL" / "cache.nc").write_bytes(b"nc")
        configuracao = {
            "overleaf": {"project_id": "x"},
            "sincronizacao": {"destino_outputs": "06_OUTPUTS", "recursivo": False},
            "publicacao": {"origem": "06_OUTPUTS", "excluir": [".pipeline", "sincronizar.py"]},
            "git": {"usuario": "t", "email": "t@t", "mensagem_commit": "figuras"},
        }
        return remoto, raiz, outputs, configuracao

    def test_mesma_pasta_publica_so_a_raiz_e_preserva_o_drive(self):
        with tempfile.TemporaryDirectory() as temporario:
            base = Path(temporario)
            remoto, raiz, outputs, configuracao = self.preparar(base)

            resultado = executar_fluxo_completo(
                raiz_projeto=raiz,
                origem_outputs=outputs,
                configuracao=configuracao,
                token=None,
                repo_url=str(remoto),
            )

            self.assertTrue(resultado.push_realizado)
            self.assertEqual(resultado.copia_outputs.alteracoes, 0)
            # o Overleaf nunca sobrescreve os produtos dos códigos
            self.assertEqual((outputs / "01_figura.png").read_bytes(), b"nova")
            # o texto do Overleaf chega à raiz do Drive
            self.assertTrue((raiz / "08_DOC" / "main.tex").is_file())

            conferencia = base / "conferencia"
            git("clone", "--quiet", str(remoto), str(conferencia))
            self.assertEqual((conferencia / "06_OUTPUTS" / "01_figura.png").read_bytes(), b"nova")
            self.assertTrue((conferencia / "06_OUTPUTS" / "02_figura.png").is_file())
            self.assertFalse((conferencia / "06_OUTPUTS" / "00_BACKUP").exists())
            self.assertFalse((conferencia / "06_OUTPUTS" / "99_OPERACIONAL").exists())

            segunda = executar_fluxo_completo(
                raiz_projeto=raiz,
                origem_outputs=outputs,
                configuracao=configuracao,
                token=None,
                repo_url=str(remoto),
            )
            self.assertFalse(segunda.commit_realizado)

    def test_mesma_pasta_exige_publicacao_igual(self):
        with tempfile.TemporaryDirectory() as temporario:
            base = Path(temporario)
            remoto, raiz, outputs, configuracao = self.preparar(base)
            configuracao["publicacao"]["origem"] = "figuras"

            with self.assertRaises(ValueError):
                executar_fluxo_completo(
                    raiz_projeto=raiz,
                    origem_outputs=outputs,
                    configuracao=configuracao,
                    token=None,
                    repo_url=str(remoto),
                )


if __name__ == "__main__":
    unittest.main()
