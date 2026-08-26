import tempfile
import unittest
from pathlib import Path

from overleaf_drive_sync.sincronizacao import (
    copiar_arvore_integral,
)


class TestSincronizacao(unittest.TestCase):
    def criar_arvores(self):
        temporario = tempfile.TemporaryDirectory()
        raiz = Path(temporario.name)
        origem = raiz / "origem"
        destino = raiz / "destino"
        origem.mkdir()
        return temporario, origem, destino

    def test_copia_tudo_recursivamente(self):
        temporario, origem, destino = self.criar_arvores()

        with temporario:
            (origem / "subpasta").mkdir()
            (origem / "figura.png").write_bytes(b"png")
            (origem / "tabela.csv").write_text(
                "a,b\n1,2\n",
                encoding="utf-8",
            )
            (origem / ".oculto").write_text(
                "oculto",
                encoding="utf-8",
            )
            (origem / "subpasta" / "dados.txt").write_text(
                "dados",
                encoding="utf-8",
            )

            resultado = copiar_arvore_integral(
                origem,
                destino,
            )

            self.assertEqual(resultado.novos, 4)
            self.assertEqual(resultado.atualizados, 0)
            self.assertTrue((destino / ".oculto").is_file())
            self.assertTrue(
                (destino / "subpasta" / "dados.txt").is_file()
            )

    def test_segunda_execucao_e_idempotente(self):
        temporario, origem, destino = self.criar_arvores()

        with temporario:
            (origem / "arquivo.txt").write_text(
                "conteúdo",
                encoding="utf-8",
            )

            copiar_arvore_integral(origem, destino)
            resultado = copiar_arvore_integral(origem, destino)

            self.assertEqual(resultado.novos, 0)
            self.assertEqual(resultado.atualizados, 0)
            self.assertEqual(resultado.identicos, 1)

    def test_atualiza_apenas_arquivo_alterado(self):
        temporario, origem, destino = self.criar_arvores()

        with temporario:
            (origem / "a.txt").write_text("A", encoding="utf-8")
            (origem / "b.txt").write_text("B", encoding="utf-8")

            copiar_arvore_integral(origem, destino)

            (origem / "b.txt").write_text(
                "B alterado",
                encoding="utf-8",
            )

            resultado = copiar_arvore_integral(origem, destino)

            self.assertEqual(resultado.atualizados, 1)
            self.assertEqual(resultado.identicos, 1)
            self.assertEqual(
                (destino / "b.txt").read_text(encoding="utf-8"),
                "B alterado",
            )

    def test_modo_incremental_preserva_arquivo_antigo(self):
        temporario, origem, destino = self.criar_arvores()

        with temporario:
            arquivo = origem / "arquivo.txt"
            arquivo.write_text("conteúdo", encoding="utf-8")

            copiar_arvore_integral(origem, destino)
            arquivo.unlink()
            copiar_arvore_integral(origem, destino)

            self.assertTrue((destino / "arquivo.txt").is_file())

    def test_simulacao_nao_modifica_destino(self):
        temporario, origem, destino = self.criar_arvores()

        with temporario:
            (origem / "arquivo.txt").write_text(
                "conteúdo",
                encoding="utf-8",
            )

            resultado = copiar_arvore_integral(
                origem,
                destino,
                simular=True,
            )

            self.assertEqual(resultado.novos, 1)
            self.assertFalse(destino.exists())

    def test_exclusoes_na_raiz(self):
        temporario, origem, destino = self.criar_arvores()

        with temporario:
            (origem / ".pipeline").mkdir()
            (origem / ".pipeline" / "segredo.txt").write_text(
                "não publicar",
                encoding="utf-8",
            )
            (origem / "README.md").write_text(
                "documentação",
                encoding="utf-8",
            )
            (origem / "main.tex").write_text(
                "documento",
                encoding="utf-8",
            )

            copiar_arvore_integral(
                origem,
                destino,
                excluir={".pipeline", "README.md"},
            )

            self.assertTrue((destino / "main.tex").is_file())
            self.assertFalse((destino / ".pipeline").exists())
            self.assertFalse((destino / "README.md").exists())

    def test_rejeita_destino_dentro_da_origem(self):
        with tempfile.TemporaryDirectory() as temporario:
            origem = Path(temporario) / "origem"
            origem.mkdir()
            destino = origem / "destino"

            with self.assertRaises(ValueError):
                copiar_arvore_integral(origem, destino)


if __name__ == "__main__":
    unittest.main()
