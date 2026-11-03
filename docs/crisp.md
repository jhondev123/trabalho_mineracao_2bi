# CRISP-DM no projeto

CRISP-DM (*Cross Industry Standard Process for Data Mining*) é o roteiro mais usado em projetos de mineração de
dados. Foi publicado em 2000 por um consórcio de empresas (DaimlerChrysler, SPSS, NCR e OHRA) e divide o trabalho em
**6 fases**. Não é uma sequência rígida: é normal voltar a uma fase anterior quando se descobre algo novo.

```mermaid
flowchart LR
    N["1. Entendimento<br>do negócio"] <--> D["2. Entendimento<br>dos dados"]
    D --> P["3. Preparação<br>dos dados"]
    P <--> M["4. Modelagem"]
    M --> A["5. Avaliação"]
    A --> N
    A --> I["6. Implantação"]
```

Termos técnicos: [guia.md](guia.md). Fontes: [fontes.md](fontes.md).

## Onde cada fase está

| Fase | Status | Onde |
|---|---|---|
| 1. Entendimento do negócio | feito | notebook, seção 1 |
| 2. Entendimento dos dados | feito | `coleta/` (1º bimestre) e notebook, seção 2 |
| 3. Preparação dos dados | feito | notebook, seção 3 |
| 4. Modelagem | feito | notebook, seção 4 |
| 5. Avaliação | feito | notebook, seção 5 |
| 6. Implantação | feito | notebook, seção 6, e `api/` |

---

## Fase 1 — Entendimento do negócio

- **Problema:** antecipar em quais estados o comércio varejista e os serviços tendem a faturar bem nos próximos
  meses — útil para decidir onde abrir um negócio, investir, conceder crédito ou planejar estoque.
- **Objetivo de mineração (classificação):** para cada estado, setor e mês, prever se o faturamento real dos
  **próximos 3 meses** vai ser maior que o dos mesmos meses do ano anterior.
- **Alvo:** `1` se `cresc_real_prox_3m > 0`; `0` se não.
- **Critério de sucesso:** acertar mais que a regra "se cresceu nos últimos 3 meses, vai crescer nos próximos 3"
  (`media_3m > 0`).

## Fase 2 — Entendimento dos dados

- **Coleta (1º bimestre):** `coleta/dataset.py` e `coleta/planilha_bruta.py` baixam 3 tabelas do IBGE (PMC 8880, PMS
  5906, IPCA 1737) e 2 séries do Banco Central (dólar 3698, Selic 4189). A planilha
  `dados/dados_brutos_20260914.xlsx` guarda tudo como as APIs devolveram.
- **Descrição:** 2 setores, 27 estados + Brasil, varejo de jan/2012 a jun/2026 e serviços de jan/2012 a jul/2026
  (9.772 linhas).
- **Qualidade:** sem valores não numéricos, sem duplicadas, sem meses faltando; a Selic tem 1 mês a mais (set/2026,
  em andamento), que sai na junção.
- **Exploração:** sazonalidade forte (dezembro do varejo ~27% acima da média do ano), queda da pandemia em 2020,
  crises de 2015–16 em quase todos os estados.

## Fase 3 — Preparação dos dados

| Tarefa | O que foi feito |
|---|---|
| Selecionar | localidade, período e valor das abas do IBGE; data e valor das do Banco Central |
| Limpar | texto → número (`pd.to_numeric`), símbolos do IBGE descartados, nome do estado → sigla, duplicadas removidas, conferência de meses seguidos |
| Integrar | IPCA, dólar e Selic juntados pelo mês (`merge` à esquerda) |
| Transformar | inflação descontada (`indice_receita ÷ ipca`), variação contra o mesmo mês do ano anterior, 12 atributos só com o passado |
| Faltantes | começo das séries sem histórico (23 meses) removido, sem imputação; fim das séries sem alvo vira o conjunto de previsão |
| Dividir | por data, pelo último mês que o alvo usa: treino até dez/2022, validação 2023, teste depois |
| Desbalanceamento | 42% de alta no treino e 77% no teste → acurácia balanceada como métrica principal e `class_weight` testado na busca |

Resultado: 8.181 linhas de 54 séries (treino 5.724 · validação 648 · teste 1.647 · previsão 162).

## Fase 4 — Modelagem

| | Regressão Logística | Random Forest |
|---|---|---|
| Por quê | simples e interpretável (o sinal do peso mostra o efeito) | capta relações não lineares e mostra a importância dos atributos |
| Pré-processamento | padronização (`StandardScaler`) + setor em 0/1 | setor em 0/1 |
| Busca de parâmetros | `C` e `class_weight` | `max_depth`, `min_samples_leaf` e `class_weight` |
| Escolhido | `C = 0,001`, sem peso por classe | profundidade 4, sem peso por classe |

A busca usa `GridSearchCV` com `PredefinedSplit` (treina no treino, mede na validação) e acurácia balanceada; depois
o modelo é re-treinado com treino + validação. Variações testadas na validação: com o estado como atributo (não
melhora), sem o setor (diferença < 1 ponto) e sem a pandemia no treino (piora).

## Fase 5 — Avaliação (conjunto de teste)

| | Acurácia | Acurácia balanceada | Precisão | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|---|
| Sempre alta | 0,769 | 0,500 | 0,769 | 1,000 | 0,869 | 0,500 |
| Regra `media_3m > 0` | 0,775 | 0,699 | 0,864 | 0,840 | 0,851 | 0,787 |
| Regressão Logística | 0,710 | 0,731 | 0,910 | 0,691 | 0,785 | 0,778 |
| **Random Forest** | 0,766 | **0,737** | 0,892 | 0,791 | 0,839 | **0,795** |

O Random Forest supera a regra na acurácia balanceada e no ROC-AUC e acerta 68% das quedas (a regra, 56%). O ganho é
modesto e aparece mais em 2025, quando o crescimento perdeu força.

## Fase 6 — Implantação

- Random Forest final re-treinado com todos os meses que têm alvo e salvo em `saidas/modelo_final.joblib`.
- Ranking de previsão em `saidas/ranking_previsao.csv` (varejo jul–set/2026 e serviços ago–out/2026, com os dados
  coletados em 14/09/2026).
- API em FastAPI (`api/main.py`): `/ranking`, `/previsoes/{uf}` e `/prever`.
- Atualização: rodar a coleta quando o IBGE publicar um mês novo, rodar o notebook e reiniciar a API.
