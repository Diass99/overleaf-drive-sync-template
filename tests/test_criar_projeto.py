import tempfile
import unittest
import zipfile
from pathlib import Path

import criar_projeto


class TestCriarProjeto(unittest.TestCase):
    def test_instala_automacao_no_projeto(self):
        with tempfile.TemporaryDirectory() as temporario:
            projeto = Path(temporario) / "projeto"
            projeto.mkdir()

            criar_projeto.copiar_automacao(projeto)

            self.assertTrue(
                (projeto / "sincronizar.py").is_file()
            )
            self.assertTrue(
                (
                    projeto
                    / ".pipeline"
                    / "overleaf_drive_sync"
                    / "configuracao.py"
                ).is_file()
            )
            self.assertTrue(
                (
                    projeto
                    / ".pipeline"
                    / "overleaf_drive_sync"
                    / "sincronizacao.py"
                ).is_file()
            )
            self.assertTrue(
                (
                    projeto
                    / ".pipeline"
                    / "overleaf_drive_sync"
                    / "overleaf_git.py"
                ).is_file()
            )

    def test_main_existente_nao_e_sobrescrito(self):
        with tempfile.TemporaryDirectory() as temporario:
            projeto = Path(temporario) / "projeto"
            projeto.mkdir()
            main = projeto / "main.tex"
            main.write_text(
                "conteúdo original",
                encoding="utf-8",
            )

            criar_projeto.preparar_main_tex(
                projeto,
                "main.tex",
            )

            self.assertEqual(
                main.read_text(encoding="utf-8"),
                "conteúdo original",
            )

    def test_zip_inicial_exclui_automacao_e_outputs(self):
        with tempfile.TemporaryDirectory() as temporario:
            projeto = Path(temporario) / "projeto"
            projeto.mkdir()

            (projeto / ".pipeline").mkdir()
            (projeto / "figuras").mkdir()

            (projeto / "main.tex").write_text(
                "documento",
                encoding="utf-8",
            )
            (projeto / "sincronizar.py").write_text(
                "automação",
                encoding="utf-8",
            )
            (
                projeto / ".pipeline" / "projeto.toml"
            ).write_text(
                "configuração",
                encoding="utf-8",
            )
            (projeto / "figuras" / "figura.png").write_bytes(
                b"imagem"
            )

            zip_path = criar_projeto.criar_zip_inicial(
                projeto,
                "figuras",
            )

            with zipfile.ZipFile(zip_path) as arquivo_zip:
                nomes = set(arquivo_zip.namelist())

            self.assertEqual(nomes, {"main.tex"})


if __name__ == "__main__":
    unittest.main()
