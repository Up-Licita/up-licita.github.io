"""Testes offline (não acessam a internet). Rode com:  python -m unittest discover -s tests -t ."""

import os
import tempfile
import unittest
from datetime import datetime

from radar import filtro, formatacao, site, urls

AGORA = datetime(2026, 11, 14, 9, 0)


def lic(objeto, fim="2026-11-20T10:00:00", uf="MG", cidade="Extrema", seq=15, **extra):
    base = {
        "numeroControlePNCP": f"12345678000199-1-{seq:06d}/2026",
        "objetoCompra": objeto,
        "dataEncerramentoProposta": fim,
        "dataAberturaProposta": "2026-11-10T08:00:00",
        "dataPublicacaoPncp": "2026-11-13T10:00:00",
        "orgaoEntidade": {"cnpj": "12345678000199", "razaoSocial": "Município de Teste"},
        "unidadeOrgao": {"municipioNome": cidade, "ufSigla": uf, "nomeUnidade": "Secretaria de Educação"},
        "anoCompra": 2026, "sequencialCompra": seq, "numeroCompra": "90015",
        "modalidadeNome": "Pregão - Eletrônico", "valorTotalEstimado": 152340.5,
        "situacaoCompraNome": "Divulgada no PNCP",
        "linkSistemaOrigem": "https://exemplo.gov.br/pregao/15",
    }
    base.update(extra)
    return base


class TestFiltro(unittest.TestCase):
    def test_alimentacao(self):
        self.assertEqual(filtro.classificar(lic("Aquisição de GÊNEROS ALIMENTÍCIOS para a merenda"))[0], "alimentacao")
        self.assertIn("alimentacao", filtro.classificar(lic("Fornecimento de pão francês")))

    def test_construcao(self):
        self.assertEqual(filtro.classificar(lic("Registro de preços de cimento, areia e brita"))[0], "material-de-construcao")

    def test_obras_nao_e_material(self):
        segs = filtro.classificar(lic("Contratação para execução de obra com fornecimento de cimento"))
        self.assertNotIn("material-de-construcao", segs)
        self.assertIn("obras-e-engenharia", segs)

    def test_exclusoes(self):
        self.assertNotIn("alimentacao", filtro.classificar(lic("Fonte de alimentação para computadores")))
        self.assertNotIn("material-de-construcao", filtro.classificar(lic("Aquisição de toner e tinta para impressora")))
        self.assertIn("tecnologia", filtro.classificar(lic("Aquisição de toner e tinta para impressora")))

    def test_palavra_inteira(self):
        self.assertEqual(filtro.classificar(lic("Serviço de padronização de papão")), [])

    def test_prazo_e_novidade(self):
        self.assertFalse(filtro.prazo_aberto(lic("arroz", fim="2026-11-01T10:00:00"), AGORA))
        self.assertTrue(filtro.publicada_recentemente(lic("arroz"), AGORA))
        self.assertFalse(filtro.publicada_recentemente(lic("arroz", dataPublicacaoPncp="2026-10-01T10:00:00"), AGORA))


class TestFormatacao(unittest.TestCase):
    def test_moeda(self):
        self.assertEqual(formatacao.moeda(152340.5), "R$ 152.340,50")
        self.assertEqual(formatacao.moeda(None), "não informado")

    def test_mensagem(self):
        m = formatacao.mensagem(lic("Aquisição de arroz <tipo 1>"), "🍎 Alimentação")
        self.assertIn("&lt;tipo 1&gt;", m)
        self.assertIn("https://pncp.gov.br/app/editais/12345678000199/2026/15", m)
        self.assertIn(urls.absoluta(urls.pagina_licitacao(lic("Aquisição de arroz <tipo 1>"))), m)


class TestSite(unittest.TestCase):
    def test_gera_site(self):
        itens = [
            lic("Aquisição de gêneros alimentícios", seq=1),
            lic("Aquisição de cimento", uf="SP", cidade="São Paulo", seq=2),
            lic("Locação de impressoras", uf="BA", cidade="Feira de Santana", seq=3),
            lic("Encerrada", fim="2026-11-01T10:00:00", seq=4),
        ]
        with tempfile.TemporaryDirectory() as pasta:
            r = site.gerar(itens, AGORA, pasta)
            self.assertEqual(r["licitacoes"], 3)
            for caminho in ["index.html", "busca.html", "alertas.html", "404.html", "sitemap.xml",
                            "robots.txt", "estilo.css", "busca.js", "dados/meta.json", "dados/sp.json",
                            urls.pagina_estado("SP"), urls.pagina_cidade("SP", "São Paulo"),
                            urls.pagina_segmento("alimentacao"), urls.pagina_licitacao(itens[0])]:
                self.assertTrue(os.path.exists(os.path.join(pasta, caminho)), caminho)
            pagina = open(os.path.join(pasta, urls.pagina_licitacao(itens[0])), encoding="utf-8").read()
            self.assertIn("Aquisição de gêneros alimentícios", pagina)
            self.assertIn("t.me/uplicita_alimentos", pagina)
            self.assertIn('href="../estilo.css"', pagina)


if __name__ == "__main__":
    unittest.main()
