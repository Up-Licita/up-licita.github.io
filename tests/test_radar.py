"""Testes offline (não acessam a internet). Rode com:  python -m unittest -v"""

import unittest
from datetime import datetime

from radar import filtro, formatacao


def lic(objeto, fim="2099-01-01T10:00:00", **extra):
    base = {
        "numeroControlePNCP": objeto[:20],
        "objetoCompra": objeto,
        "dataEncerramentoProposta": fim,
        "orgaoEntidade": {"cnpj": "12345678000199", "razaoSocial": "Prefeitura Teste"},
        "unidadeOrgao": {"municipioNome": "Extrema", "ufSigla": "MG"},
        "anoCompra": 2026, "sequencialCompra": 15,
        "modalidadeNome": "Pregão - Eletrônico", "valorTotalEstimado": 152340.5,
    }
    base.update(extra)
    return base


class TestFiltro(unittest.TestCase):
    def test_alimentacao(self):
        self.assertEqual(filtro.classificar(lic("Aquisição de GÊNEROS ALIMENTÍCIOS para a merenda")), ["alimentacao"])
        self.assertEqual(filtro.classificar(lic("Fornecimento de pão francês")), ["alimentacao"])

    def test_construcao(self):
        self.assertEqual(filtro.classificar(lic("Registro de preços de cimento, areia e brita")), ["construcao"])
        self.assertEqual(filtro.classificar(lic("Aquisição de materiais hidráulicos e elétricos")), ["construcao"])

    def test_exclusoes(self):
        self.assertEqual(filtro.classificar(lic("Aquisição de ração para cães (alimentos)")), [])
        self.assertEqual(filtro.classificar(lic("Fonte de alimentação para computadores")), [])
        self.assertEqual(filtro.classificar(lic("Aquisição de toner e tinta para impressora")), [])
        self.assertEqual(filtro.classificar(lic("Contratação para execução de obra com fornecimento de cimento")), [])

    def test_palavra_inteira(self):
        self.assertEqual(filtro.classificar(lic("Serviço de padronização de papão")), [])
        self.assertEqual(filtro.classificar(lic("Locação de veículos")), [])

    def test_prazo_encerrado(self):
        agora = datetime(2026, 11, 10)
        g = filtro.separar_por_nicho([lic("compra de arroz", fim="2026-11-01T10:00:00")], agora)
        self.assertEqual(g["alimentacao"], [])


class TestFormatacao(unittest.TestCase):
    def test_moeda(self):
        self.assertEqual(formatacao.moeda(152340.5), "R$ 152.340,50")
        self.assertEqual(formatacao.moeda(None), "não informado")

    def test_mensagem(self):
        m = formatacao.mensagem(lic("Aquisição de arroz <tipo 1>"), "🍎 Alimentação")
        self.assertIn("&lt;tipo 1&gt;", m)  # HTML escapado
        self.assertIn("https://pncp.gov.br/app/editais/12345678000199/2026/15", m)
        self.assertIn("Extrema / MG", m)


if __name__ == "__main__":
    unittest.main()
