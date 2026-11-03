# Onde o faturamento vai crescer?

Previsão do crescimento real (acima da inflação) do **comércio varejista** e dos **serviços** por estado, com dados
oficiais do IBGE e do Banco Central.

Trabalho da disciplina de **Mineração de Dados** — 2º bimestre · metodologia **CRISP-DM**

**Integrantes:** Jhonattan Curtarelli · _(adicionar os demais integrantes)_

> Vai continuar o trabalho? Comece por [CONTEXTO.md](CONTEXTO.md): decisões, cuidados e o que falta para a entrega.

[![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jhondev123/trabalho_mineracao_2bi/blob/main/trabalho_mineracao_dados.ipynb)

## O problema

Em quais estados o faturamento do varejo e dos serviços deve crescer acima da inflação nos **próximos 3 meses**?

Para cada estado, setor e mês, o modelo responde **1** se o faturamento real dos 3 meses seguintes for maior que o dos
mesmos meses do ano anterior, e **0** se não. Ele só agrega valor se acertar mais que a regra simples "se cresceu nos
últimos 3 meses, vai crescer nos próximos 3".

## Resultado

Avaliação no conjunto de **teste** (alvos de 2024 a 2026, que nenhum modelo viu no treino):

| | Acurácia | Acurácia balanceada | Precisão | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|---|
| Sempre "vai crescer" | 0,769 | 0,500 | 0,769 | 1,000 | 0,869 | 0,500 |
| Regra `media_3m > 0` | 0,775 | 0,699 | 0,864 | 0,840 | 0,851 | 0,787 |
| Regressão Logística | 0,710 | 0,731 | 0,910 | 0,691 | 0,785 | 0,778 |
| **Random Forest** | 0,766 | **0,737** | 0,892 | 0,791 | 0,839 | **0,795** |

- A métrica principal é a **acurácia balanceada**: como 77% dos casos do teste são de alta, responder sempre "vai
  crescer" já dá 77% de acurácia e F1 de 0,87, mas 0,50 de acurácia balanceada.
- O **Random Forest** é o melhor modelo: supera a regra na acurácia balanceada e no ROC-AUC e acerta 68% das quedas,
  contra 56% da regra. O ganho é modesto — a tendência recente já carrega boa parte da informação — e aparece mais
  quando o cenário muda (2025).
- Com os dados coletados em 14/09/2026, o ranking aponta **DF, PE, TO, AC e BA** no varejo (jul–set/2026) e **SE, AP,
  RN, DF e BA** nos serviços (ago–out/2026) como os estados com maior chance de crescimento real.

Detalhes e gráficos no notebook; resumo das fases em [docs/crisp.md](docs/crisp.md).

## Como rodar no Google Colab

1. No Google Drive, em **Meu Drive**, crie a pasta `trabalho_min_dados/dados/`.
2. Baixe [`dados/dados_brutos_20260914.xlsx`](dados/dados_brutos_20260914.xlsx) deste repositório e suba nessa pasta.
3. Abra o notebook pelo botão **Abrir no Colab** acima (ou, no Colab, **Arquivo → Abrir notebook → GitHub** e cole
   o endereço deste repositório).
4. **Ambiente de execução → Executar tudo** e autorize o acesso ao Drive.

```
Meu Drive/
└── trabalho_min_dados/
    ├── dados/
    │   └── dados_brutos_20260914.xlsx   ← você sobe este arquivo
    └── saidas/                          ← o notebook cria
        ├── graficos/*.png               (12 gráficos)
        ├── dataset_modelo.csv           (dados preparados)
        ├── metricas_teste.csv
        ├── ranking_previsao.csv
        └── modelo_final.joblib
```

Leva de 2 a 4 minutos. Para usar outra pasta do Drive, mude `NOME_PASTA` na seção 0 do notebook. Testado com o
scikit-learn 1.6 (versão do Colab) e 1.9: os resultados são idênticos aos salvos neste repositório.

## Como rodar no computador

```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
jupyter notebook trabalho_mineracao_dados.ipynb   # ou abra no VS Code
```

Fora do Colab, o notebook lê a pasta `dados/` e grava em `saidas/`, ao lado dele.

### API (opcional)

Depois de rodar o notebook (ele gera `saidas/modelo_final.joblib`):

```bash
uvicorn api.main:app --reload
```

Abra http://127.0.0.1:8000/docs para testar pelo navegador.

| Endereço | O que devolve |
|---|---|
| `GET /ranking?setor=varejo` | estados ordenados pela probabilidade de crescimento real (`setor=servicos` para serviços) |
| `GET /previsoes/PR` | previsão de um estado nos dois setores |
| `POST /prever` | probabilidade para um conjunto de atributos (exemplo pronto na página `/docs`) |

### Coletar dados novos

Os scripts do 1º bimestre, em `coleta/`, baixam os dados direto das APIs do IBGE e do Banco Central (precisa de
internet, sem cadastro):

```bash
python coleta/planilha_bruta.py   # gera dados/dados_brutos_AAAAMMDD.xlsx, a entrada do notebook
python coleta/dataset.py          # gera dados/faturamento_uf_mensal_AAAAMMDD.csv (tabela já integrada)
```

O notebook usa sempre o `dados_brutos_*.xlsx` mais recente da pasta.

## Como o trabalho segue o CRISP-DM

| Fase | O que foi feito | Onde |
|---|---|---|
| 1. Entendimento do negócio | pergunta, alvo e critério de sucesso | notebook, seção 1 |
| 2. Entendimento dos dados | 5 fontes, qualidade, sazonalidade, nominal × real | `coleta/` e notebook, seção 2 |
| 3. Preparação | limpeza, integração, inflação descontada, 12 atributos sem vazamento do futuro, faltantes, divisão no tempo, desbalanceamento | notebook, seção 3 |
| 4. Modelagem | regra de comparação, Regressão Logística e Random Forest com busca de parâmetros na validação | notebook, seção 4 |
| 5. Avaliação | métricas no teste, matrizes de confusão, curva ROC, importância dos atributos, erros por estado e ano | notebook, seção 5 |
| 6. Implantação | modelo final, ranking de previsão e API | notebook, seção 6, e `api/` |

## Os dados

| Fonte | O que mede | Recorte |
|---|---|---|
| IBGE — Pesquisa Mensal de Comércio, tabela 8880 | índice de receita nominal do varejo (2022 = 100), sem ajuste sazonal | Brasil + 27 UFs, jan/2012–jun/2026 |
| IBGE — Pesquisa Mensal de Serviços, tabela 5906 | índice de receita nominal dos serviços (2022 = 100), sem ajuste sazonal | Brasil + 27 UFs, jan/2012–jul/2026 |
| IBGE — IPCA, tabela 1737 | inflação oficial (número-índice) | Brasil |
| Banco Central — SGS 3698 | dólar (venda), média do mês | Brasil |
| Banco Central — SGS 4189 | Selic do mês, % ao ano | Brasil |

**Limitações:** é um índice, não valor em R$; as pesquisas cobrem empresas formais com 20 ou mais pessoas ocupadas;
IPCA, dólar e Selic são nacionais. Referências em ABNT em [docs/fontes.md](docs/fontes.md).

## Estrutura

```
trabalho_mineracao_2bi/
├── CONTEXTO.md                      # contexto para quem for continuar: decisões, cuidados e pendências
├── trabalho_mineracao_dados.ipynb   # o trabalho: do dado bruto ao ranking (abre no Colab)
├── dados/
│   └── dados_brutos_20260914.xlsx   # dados como vieram das APIs, uma aba por fonte
├── saidas/                          # gerado pelo notebook: gráficos, dataset preparado, métricas, ranking, modelo
├── api/
│   └── main.py                      # API FastAPI com o modelo final
├── coleta/                          # scripts do 1º bimestre: coleta nas APIs do IBGE e do Banco Central
├── artigo/                          # rascunho do artigo, pendências (LEIA-ME.md) e modelo da disciplina
├── docs/
│   ├── crisp.md                     # o que foi feito em cada fase
│   ├── guia.md                      # glossário dos termos técnicos
│   ├── fontes.md                    # fontes e referências (ABNT)
│   └── apresentacao_seminario_1bi.pptx  # apresentação do seminário do 1º bimestre
└── requirements.txt
```
