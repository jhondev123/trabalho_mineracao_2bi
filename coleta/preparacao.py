"""Preparacao dos dados (fase 3 do CRISP-DM): desconta a inflacao, cria os
atributos e o alvo do modelo e separa treino, validacao e teste.

Le o CSV mais recente do dataset.py e grava em dados/:
    dataset_modelo_AAAAMMDD.csv     uma linha por setor x UF x mes, com atributos e alvo
    perfil_series_AAAAMMDD.csv      uma linha por setor x UF, resumo para o K-means
    dados_preparados_AAAAMMDD.xlsx  as duas tabelas + aba Leia-me com o dicionario

Regras:
- nenhum atributo usa informacao posterior ao mes da linha (sem vazamento);
- as linhas do Brasil (BR) nao entram no modelo: viram o atributo var_anual_real_br;
- a divisao e por tempo, pelo ultimo mes que o alvo usa.

Uso:
    python preparacao.py
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font

from planilha_bruta import FONTE, FUNDO_CABECALHO, escrever_aba

PASTA_DADOS = Path(__file__).resolve().parent.parent / "dados"  # pasta dados/ na raiz do repositório

PANDEMIA = (202003, 202112)  # de marco/2020 (inicio das restricoes) a dezembro/2021
FIM_TREINO = 202212  # ultimo mes que o alvo pode usar para a linha ser de treino
FIM_VALIDACAO = 202312

ATRIBUTOS = [
    "var_anual_real", "media_3m", "media_6m", "media_12m", "aceleracao", "oscilacao_12m",
    "var_anual_real_br", "ipca_12m", "selic", "selic_var_12m", "dolar_var_12m", "pandemia",
]

COLUNAS_MODELO = (
    ["setor", "uf", "ano", "mes", "indice_receita", "ipca", "indice_real"]
    + ATRIBUTOS
    + ["cresc_real_prox_3m", "alvo", "conjunto"]
)

PERCENTUAIS = [
    "var_anual_real", "media_3m", "media_6m", "media_12m", "aceleracao", "oscilacao_12m",
    "var_anual_real_br", "ipca_12m", "selic_var_12m", "dolar_var_12m", "cresc_real_prox_3m",
]

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

PASSOS = [
    "1. Descontar a inflação: indice_real = indice_receita ÷ ipca, reescalado para a média de 2022 de cada "
    "estado e setor valer 100.",
    "2. Comparar cada mês com o mesmo mês do ano anterior (var_anual_real), o que tira o efeito do Natal e de "
    "outras datas.",
    "3. Criar atributos só com o passado de cada mês: médias, aceleração, oscilação, desempenho do setor no "
    "Brasil, inflação, Selic, dólar e pandemia.",
    "4. Criar o alvo: 1 se o faturamento real dos 3 meses seguintes for maior que o dos mesmos meses do ano "
    "anterior; 0 se não.",
    "5. Tirar do modelo as linhas do Brasil (viraram o atributo var_anual_real_br) e os primeiros 23 meses de "
    "cada série, que ainda não têm histórico para os atributos.",
    "6. Dividir por tempo, pelo último mês que o alvo usa: treino até dez/2022, validação em 2023 e teste "
    "depois. Os meses mais recentes, sem alvo ainda, ficam como previsão.",
    "7. Montar o perfil de cada estado e setor para o K-means, com as colunas também padronizadas (z).",
]

DICIONARIO_MODELO = [
    ("setor", "COMERCIO_VAREJISTA ou SERVICOS", "copiado do dataset"),
    ("uf", "sigla do estado", "as linhas do Brasil (BR) ficam fora do modelo"),
    ("ano, mes", "mês de referência da linha (t)", "copiado do dataset"),
    ("indice_receita", "faturamento como o IBGE publica (média de 2022 = 100)", "copiado do dataset"),
    ("ipca", "índice da inflação oficial", "copiado do dataset"),
    ("indice_real", "faturamento sem inflação (média de 2022 = 100)",
     "indice_receita ÷ ipca, reescalado para a média de 2022 do estado e setor valer 100"),
    ("var_anual_real", "crescimento real contra o mesmo mês do ano anterior (%)",
     "indice_real(t) ÷ indice_real(t−12) − 1"),
    ("media_3m, media_6m, media_12m", "média do crescimento real nos últimos 3, 6 e 12 meses (%)",
     "média de var_anual_real de t−2, t−5 e t−11 até t"),
    ("aceleracao", "positivo = crescimento acelerando; negativo = freando (pontos percentuais)",
     "media_3m − media_12m"),
    ("oscilacao_12m", "quanto o crescimento real oscilou no último ano (pontos percentuais)",
     "desvio-padrão de var_anual_real de t−11 até t"),
    ("var_anual_real_br", "crescimento real do mesmo setor no Brasil (%)", "var_anual_real da linha BR no mês t"),
    ("ipca_12m", "inflação acumulada em 12 meses (%)", "ipca(t) ÷ ipca(t−12) − 1"),
    ("selic", "Selic do mês (% ao ano)", "copiado do dataset"),
    ("selic_var_12m", "mudança da Selic em 12 meses (pontos percentuais)", "selic(t) − selic(t−12)"),
    ("dolar_var_12m", "variação do dólar em 12 meses (%)", "dolar(t) ÷ dolar(t−12) − 1"),
    ("pandemia", "1 de mar/2020 a dez/2021; 0 nos demais meses", "marca o período fora do padrão"),
    ("cresc_real_prox_3m", "crescimento real dos 3 meses seguintes contra os mesmos meses do ano anterior (%)",
     "soma indice_real(t+1 a t+3) ÷ soma indice_real(t−11 a t−9) − 1. Usa o futuro: é o que se quer prever e "
     "nunca entra como atributo"),
    ("alvo", "1 = vai crescer acima da inflação; 0 = não", "cresc_real_prox_3m > 0"),
    ("conjunto", "treino, validacao, teste ou previsao",
     "pelo último mês usado no alvo (t+3): até dez/2022 treino; até dez/2023 validação; depois teste; sem alvo "
     "ainda = previsão"),
]

DICIONARIO_PERFIL = [
    ("cresc_real_medio", "média do crescimento real anual de 2013 a 2025 (%)"),
    ("oscilacao_anual", "desvio-padrão desse crescimento anual (pontos percentuais)"),
    ("queda_2020", "crescimento real em 2020, ano da pandemia (%)"),
    ("recuperacao_2022_vs_2019", "faturamento real de 2022 contra 2019 (%)"),
    ("cresc_2025", "crescimento real em 2025 (%)"),
    ("pico_dezembro", "quanto dezembro fatura acima do mês médio do ano (%), média dos anos sem 2020"),
    ("z_…", "a mesma coluna padronizada (média 0, desvio-padrão 1), para o K-means comparar colunas de escalas "
            "diferentes"),
]


def mes_ano(periodo):
    return f"{MESES[periodo % 100 - 1]}/{periodo // 100}"


def carregar():
    arquivos = sorted(PASTA_DADOS.glob("faturamento_uf_mensal_*.csv"))
    if not arquivos:
        sys.exit("nenhum CSV em dados/ - rode python dataset.py antes")
    df = pd.read_csv(arquivos[-1], sep=";", decimal=",", encoding="utf-8-sig")
    df["periodo"] = df["ano"] * 100 + df["mes"]
    return df.sort_values(["setor", "uf", "periodo"]).reset_index(drop=True), arquivos[-1].name


def conferir_meses_seguidos(df):
    """Os deslocamentos de 12 meses so valem se nenhuma serie tiver buraco."""
    indice_mes = df["ano"] * 12 + df["mes"]
    salto = indice_mes.groupby([df["setor"], df["uf"]]).diff()
    if (salto > 1).any():
        sys.exit("ha meses faltando em alguma serie; rode o dataset.py de novo")


def descontar_inflacao(df):
    real = df["indice_receita"] / df["ipca"]
    base_2022 = real[df["ano"] == 2022].groupby([df["setor"], df["uf"]]).mean().rename("base_2022")
    df = df.join(base_2022, on=["setor", "uf"])
    df["indice_real"] = real / df["base_2022"] * 100
    return df.drop(columns="base_2022")


def criar_atributos(df):
    serie = df.groupby(["setor", "uf"], sort=False)
    df["var_anual_real"] = (df["indice_real"] / serie["indice_real"].shift(12) - 1) * 100

    variacao = df.groupby(["setor", "uf"], sort=False)["var_anual_real"]
    for meses in (3, 6, 12):
        df[f"media_{meses}m"] = variacao.transform(lambda s: s.rolling(meses).mean())
    df["aceleracao"] = df["media_3m"] - df["media_12m"]
    df["oscilacao_12m"] = variacao.transform(lambda s: s.rolling(12).std())

    brasil = df[df["uf"] == "BR"].set_index(["setor", "periodo"])["var_anual_real"].rename("var_anual_real_br")
    df = df.join(brasil, on=["setor", "periodo"])

    macro = df[["periodo", "ipca", "dolar", "selic"]].drop_duplicates("periodo").set_index("periodo").sort_index()
    macro["ipca_12m"] = (macro["ipca"] / macro["ipca"].shift(12) - 1) * 100
    macro["selic_var_12m"] = macro["selic"] - macro["selic"].shift(12)
    macro["dolar_var_12m"] = (macro["dolar"] / macro["dolar"].shift(12) - 1) * 100
    df = df.join(macro[["ipca_12m", "selic_var_12m", "dolar_var_12m"]], on="periodo")

    df["pandemia"] = df["periodo"].between(*PANDEMIA).astype(int)
    return df


def criar_alvo(df):
    real = df.groupby(["setor", "uf"], sort=False)["indice_real"]
    proximos_3m = real.shift(-1) + real.shift(-2) + real.shift(-3)
    mesmos_meses_ano_anterior = real.shift(11) + real.shift(10) + real.shift(9)
    df["cresc_real_prox_3m"] = (proximos_3m / mesmos_meses_ano_anterior - 1) * 100
    df["alvo"] = (df["cresc_real_prox_3m"] > 0).astype("Int64").where(df["cresc_real_prox_3m"].notna())

    # ultimo mes que o alvo usa (t+3), no formato AAAAMM
    meses = df["ano"] * 12 + df["mes"] - 1 + 3
    fim_alvo = (meses // 12) * 100 + meses % 12 + 1
    df["conjunto"] = "teste"
    df.loc[fim_alvo <= FIM_VALIDACAO, "conjunto"] = "validacao"
    df.loc[fim_alvo <= FIM_TREINO, "conjunto"] = "treino"
    df.loc[df["alvo"].isna(), "conjunto"] = "previsao"
    return df


def montar_dataset_modelo(df):
    modelo = df[df["uf"] != "BR"].dropna(subset=ATRIBUTOS).copy()
    modelo[PERCENTUAIS] = modelo[PERCENTUAIS].round(2)
    modelo["indice_real"] = modelo["indice_real"].round(4)
    return modelo


def perfil_series(df):
    anos = df[(df["uf"] != "BR") & df["ano"].between(2012, 2025)]
    anual = anos.groupby(["setor", "uf", "ano"])["indice_real"].sum()
    crescimento = (anual.groupby(level=["setor", "uf"]).pct_change() * 100).unstack("ano")

    perfil = pd.DataFrame({
        "cresc_real_medio": crescimento.loc[:, 2013:2025].mean(axis=1),
        "oscilacao_anual": crescimento.loc[:, 2013:2025].std(axis=1),
        "queda_2020": crescimento[2020],
        "recuperacao_2022_vs_2019": (anual.xs(2022, level="ano") / anual.xs(2019, level="ano") - 1) * 100,
        "cresc_2025": crescimento[2025],
    })

    sem_2020 = anos[anos["ano"] != 2020].copy()
    media_do_ano = sem_2020.groupby(["setor", "uf", "ano"])["indice_receita"].transform("mean")
    sem_2020["relativo"] = sem_2020["indice_receita"] / media_do_ano * 100
    perfil["pico_dezembro"] = sem_2020[sem_2020["mes"] == 12].groupby(["setor", "uf"])["relativo"].mean() - 100

    for coluna in list(perfil.columns):
        perfil[f"z_{coluna}"] = (perfil[coluna] - perfil[coluna].mean()) / perfil[coluna].std()
    return perfil.round(3).reset_index()


def resumir(modelo):
    grupos = modelo.groupby("conjunto")
    resumo = pd.DataFrame({
        "linhas": grupos.size(),
        "pct_alta": grupos["alvo"].mean() * 100,
        "inicio": grupos["periodo"].min(),
        "fim": grupos["periodo"].max(),
    })
    return resumo.reindex(["treino", "validacao", "teste", "previsao"]).reset_index()


def valores_celula(tabela):
    """Linhas da tabela com NaN/NA viradas em None (celula vazia no Excel)."""
    return tabela.astype(object).where(tabela.notna(), None).itertuples(index=False, name=None)


def escrever_leia_me(aba, origem, gerado, resumo):
    normal = Font(name=FONTE, size=10)
    negrito = Font(name=FONTE, size=10, bold=True)
    quebra = Alignment(wrap_text=True, vertical="top")

    def linha(valores, fonte=normal, cabecalho=False):
        aba.append(valores)
        for celula in aba[aba.max_row]:
            celula.font = fonte
            celula.alignment = quebra
            if cabecalho:
                celula.fill = FUNDO_CABECALHO

    aba.append(["Dados preparados para o modelo"])
    aba["A1"].font = Font(name=FONTE, size=14, bold=True)
    linha([f"Fase 3 do CRISP-DM. Gerado em {gerado:%d/%m/%Y às %H:%M} pelo preparacao.py, a partir de {origem}."])
    linha([])

    linha(["O que foi feito"], negrito)
    for passo in PASSOS:
        linha([passo])
    linha([])

    linha(["Conjunto", "Linhas", "Casos de alta (alvo = 1)", "Meses das linhas"], negrito, cabecalho=True)
    for item in resumo.itertuples(index=False):
        alta = "—" if pd.isna(item.pct_alta) else f"{item.pct_alta:.1f}%".replace(".", ",")
        linha([item.conjunto, int(item.linhas), alta, f"{mes_ano(item.inicio)} a {mes_ano(item.fim)}"])
    linha(["", "Valores calculados pelo preparacao.py no momento em que a planilha foi gerada."])
    linha([])

    linha(["Coluna (aba Dataset do modelo)", "O que é", "Como é calculado"], negrito, cabecalho=True)
    for valores in DICIONARIO_MODELO:
        linha(list(valores))
    linha([])

    linha(["Coluna (aba Perfil para K-means)", "O que é"], negrito, cabecalho=True)
    for valores in DICIONARIO_PERFIL:
        linha(list(valores))

    for coluna, largura in zip("ABCD", (30, 60, 70, 24)):
        aba.column_dimensions[coluna].width = largura


def main():
    df, origem = carregar()
    conferir_meses_seguidos(df)
    df = descontar_inflacao(df)
    df = criar_atributos(df)
    df = criar_alvo(df)

    modelo = montar_dataset_modelo(df)
    perfil = perfil_series(df)
    resumo = resumir(modelo)

    print(f"dataset do modelo: {len(modelo)} linhas, {modelo.groupby(['setor', 'uf']).ngroups} séries")
    print(resumo.to_string(index=False))

    gerado = datetime.now()
    carimbo = f"{gerado:%Y%m%d}"
    PASTA_DADOS.mkdir(exist_ok=True)
    tabela_modelo = modelo[COLUNAS_MODELO]
    for nome, tabela in [("dataset_modelo", tabela_modelo), ("perfil_series", perfil)]:
        caminho = PASTA_DADOS / f"{nome}_{carimbo}.csv"
        tabela.to_csv(caminho, index=False, sep=";", decimal=",", encoding="utf-8-sig")
        print(f"salvo: {caminho}")

    wb = Workbook()
    escrever_leia_me(wb.active, origem, gerado, resumo)
    wb.active.title = "Leia-me"
    larguras = {"setor": 22, "cresc_real_prox_3m": 18, "var_anual_real_br": 17}
    escrever_aba(wb, "Dataset do modelo", COLUNAS_MODELO, valores_celula(tabela_modelo), larguras)
    escrever_aba(wb, "Perfil para K-means", list(perfil.columns), valores_celula(perfil), larguras)
    caminho = PASTA_DADOS / f"dados_preparados_{carimbo}.xlsx"
    wb.save(caminho)
    print(f"salvo: {caminho}")


if __name__ == "__main__":
    main()
