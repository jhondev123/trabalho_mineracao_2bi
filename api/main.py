"""API do modelo final: ranking e previsão de crescimento real por estado.

Usa os arquivos que o notebook grava em saidas/:
    modelo_final.joblib    Random Forest treinado com todos os meses que têm alvo
    ranking_previsao.csv   probabilidade de crescimento real nos 3 meses seguintes ao último dado

Rodar, na raiz do repositório:
    pip install -r requirements.txt
    uvicorn api.main:app --reload

Documentação interativa (dá para testar os endereços pelo navegador): http://127.0.0.1:8000/docs
Para usar a pasta saidas/ do Google Drive, defina a variável de ambiente PASTA_SAIDAS.
"""

import os
from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

PASTA_SAIDAS = Path(os.environ.get("PASTA_SAIDAS", Path(__file__).resolve().parent.parent / "saidas"))
SETORES = {"varejo": "COMERCIO_VAREJISTA", "servicos": "SERVICOS"}
Setor = Literal["varejo", "servicos"]

try:
    modelo = joblib.load(PASTA_SAIDAS / "modelo_final.joblib")
except (AttributeError, ModuleNotFoundError, ImportError) as erro:
    raise RuntimeError(
        "modelo_final.joblib foi salvo com outra versão do scikit-learn. Instale a versão do requirements.txt "
        "(pip install -r requirements.txt) ou rode o notebook neste ambiente para gerar o modelo de novo."
    ) from erro
ranking = pd.read_csv(PASTA_SAIDAS / "ranking_previsao.csv", sep=";", decimal=",", encoding="utf-8-sig")

app = FastAPI(
    title="Onde o faturamento vai crescer?",
    description="Probabilidade de o faturamento real (sem inflação) do varejo e dos serviços crescer nos 3 meses "
                "seguintes, por estado. Dados: IBGE (PMC, PMS, IPCA) e Banco Central (dólar, Selic).",
    version="1.0",
)


class Atributos(BaseModel):
    """Os 12 atributos do modelo para um estado, setor e mês (porcentagens em %, ex.: 3.5 = 3,5%)."""

    setor: Setor
    var_anual_real: float = Field(description="crescimento real contra o mesmo mês do ano anterior (%)")
    media_3m: float = Field(description="média de var_anual_real nos últimos 3 meses (%)")
    media_6m: float = Field(description="média de var_anual_real nos últimos 6 meses (%)")
    media_12m: float = Field(description="média de var_anual_real nos últimos 12 meses (%)")
    aceleracao: float = Field(description="media_3m − media_12m (pontos percentuais)")
    oscilacao_12m: float = Field(description="desvio-padrão de var_anual_real em 12 meses (pp)")
    var_anual_real_br: float = Field(description="var_anual_real do mesmo setor no Brasil (%)")
    ipca_12m: float = Field(description="inflação acumulada em 12 meses (%)")
    selic: float = Field(description="Selic do mês (% ao ano)")
    selic_var_12m: float = Field(description="mudança da Selic em 12 meses (pp)")
    dolar_var_12m: float = Field(description="variação do dólar em 12 meses (%)")
    pandemia: int = Field(0, ge=0, le=1, description="1 de mar/2020 a dez/2021; 0 nos demais meses")

    model_config = {"json_schema_extra": {"examples": [{
        "setor": "varejo", "var_anual_real": 7.84, "media_3m": 3.09, "media_6m": 3.46, "media_12m": 3.97,
        "aceleracao": -0.88, "oscilacao_12m": 2.31, "var_anual_real_br": 6.31, "ipca_12m": 5.53, "selic": 14.15,
        "selic_var_12m": 3.5, "dolar_var_12m": 12.76, "pandemia": 0,
    }]}}


def registros(tabela):
    return tabela.to_dict(orient="records")


@app.get("/")
def inicio():
    return {
        "sobre": app.description,
        "enderecos": {
            "GET /ranking?setor=varejo": "estados ordenados pela probabilidade de crescimento real",
            "GET /previsoes/{uf}": "previsão de um estado nos dois setores (ex.: /previsoes/PR)",
            "POST /prever": "probabilidade para um conjunto de atributos",
        },
    }


@app.get("/ranking")
def obter_ranking(setor: Setor = "varejo", limite: int = 27):
    parte = ranking[ranking["setor"] == SETORES[setor]].sort_values("probabilidade_alta", ascending=False)
    return registros(parte.head(limite))


@app.get("/previsoes/{uf}")
def previsoes_do_estado(uf: str):
    parte = ranking[ranking["uf"] == uf.upper()]
    if parte.empty:
        raise HTTPException(status_code=404, detail=f"estado {uf} não encontrado; use a sigla, ex.: PR")
    return registros(parte)


@app.post("/prever")
def prever(atributos: Atributos):
    linha = pd.DataFrame([{**atributos.model_dump(), "setor": SETORES[atributos.setor]}])
    probabilidade = float(modelo.predict_proba(linha)[0, 1])
    return {
        "probabilidade_alta": round(probabilidade, 3),
        "previsao": "cresce" if probabilidade >= 0.5 else "não cresce",
    }
