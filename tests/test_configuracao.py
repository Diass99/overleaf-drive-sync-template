import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from overleaf_drive_sync.configuracao import (
    ConfiguracaoProjeto,
    carregar_configuracao,
    detectar_raizes_drive,
    extrair_project_id,
    relativo_ao_drive,
    salvar_configuracao,
    validar_caminho_relativo,
)


class TestConfiguracao(unittest.TestCase):
    def test_extrai_id_da_url_overleaf(self):
        url = (
            "https://www.overleaf.com/project/"
            "6a8f5f1d5b99d914f178ce0f"
        )
        self.assertEqual(
            extrair_project_id(url),
            "6a8f5f1d5b99d914f178ce0f",
        )

    def test_extrai_id_isolado(self):
        self.assertEqual(
            extrair_project_id("6a8f5f1d5b99d914f178ce0f"),
            "6a8f5f1d5b99d914f178ce0f",
        )

    def test_rejeita_id_invalido(self):
        with self.assertRaises(ValueError):
            extrair_project_id("projeto-sem-id-valido")

    def test_rejeita_caminho_absoluto(self):
        with self.assertRaises(ValueError):
            validar_caminho_relativo(
                "/dados/outputs",
                "pasta_outputs",
            )

    @unittest.skipUnless(os.name == "nt", "semântica de caminhos do Windows")
    def test_rejeita_caminho_com_unidade_ou_raiz_no_windows(self):
        for valor in ("C:\\dados\\outputs", "\\dados\\outputs", "C:dados"):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    validar_caminho_relativo(valor, "pasta_outputs")

    def test_rejeita_subida_de_diretorio(self):
        with self.assertRaises(ValueError):
            validar_caminho_relativo(
                "../outputs",
                "pasta_outputs",
            )

    def test_converte_caminho_para_relativo_ao_drive(self):
        with tempfile.TemporaryDirectory() as temporario:
            drive = Path(temporario)
            outputs = drive / "projeto" / "outputs"
            outputs.mkdir(parents=True)

            self.assertEqual(
                relativo_ao_drive(outputs, drive),
                "projeto/outputs",
            )

    def test_salva_e_carrega_configuracao(self):
        config = ConfiguracaoProjeto(
            nome="Projeto científico",
            arquivo_principal="main.tex",
            pasta_outputs="dados/outputs",
            destino_outputs="figuras",
            overleaf_project_id="6a8f5f1d5b99d914f178ce0f",
            git_usuario="Vinicius",
            git_email="vinicius@example.com",
        )

        with tempfile.TemporaryDirectory() as temporario:
            destino = Path(temporario) / "projeto.toml"

            salvar_configuracao(config, destino)
            carregada = carregar_configuracao(destino)

            self.assertEqual(
                carregada["projeto"]["nome"],
                "Projeto científico",
            )
            self.assertEqual(
                carregada["drive"]["pasta_outputs"],
                "dados/outputs",
            )
            self.assertEqual(
                carregada["overleaf"]["project_id"],
                "6a8f5f1d5b99d914f178ce0f",
            )
            self.assertEqual(
                carregada["publicacao"]["origem"],
                "figuras",
            )

    def test_detecta_drive_por_variavel_de_ambiente(self):
        with tempfile.TemporaryDirectory() as temporario:
            with patch.dict(
                os.environ,
                {"GOOGLE_DRIVE_ROOT": temporario},
                clear=False,
            ):
                encontrados = detectar_raizes_drive(
                    Path(temporario)
                )

            self.assertIn(
                Path(temporario).resolve(),
                encontrados,
            )


if __name__ == "__main__":
    unittest.main()
