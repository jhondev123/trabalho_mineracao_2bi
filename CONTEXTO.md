# Contexto do trabalho — para quem for continuar

Este arquivo resume tudo o que precisa saber para continuar o trabalho sem depender de quem começou: o que a
disciplina pede, o que já está pronto, as decisões tomadas e o motivo de cada uma, os cuidados para não quebrar nada
e o que falta para entregar. Também serve para colar numa IA (Claude, ChatGPT) como contexto antes de pedir ajuda.

Situação em **02/11/2026**: notebook, modelos, API e rascunho do artigo prontos. Faltam os nomes, o parágrafo sobre o
feedback do seminário, a revisão e a entrega.

---

## 1. O que a disciplina pede (2º bimestre)

Enunciado, resumido:

- Finalizar o projeto do 1º bimestre aplicando o **ciclo completo de Mineração de Dados** e consolidar tudo num
  **artigo acadêmico**, mantendo a mesma equipe e a mesma metodologia (aqui, **CRISP-DM**).
- **Obrigatório:** incorporar as orientações, os feedbacks e os questionamentos feitos na apresentação do seminário.
- O artigo deve documentar:
  - limpeza, filtragem, transformação e tratamento de dados faltantes ou desbalanceados (**NumPy e Pandas**);
  - gráficos e tabelas explicativas (**Matplotlib e Seaborn**);
  - treinamento e escolha de modelos (**Scikit-Learn**), com justificativa e avaliação das métricas;
  - (opcional) disponibilização do modelo por API (ex.: **FastAPI**).
- Usar o modelo do artigo da disciplina: [`artigo/modelo_artigo_disciplina.pdf`](artigo/modelo_artigo_disciplina.pdf)
  (A4, margens de 3 cm, Arial 12, espaçamento 1,5, **14 a 20 páginas**, resumo de 200 a 300 palavras, referências
  ABNT).

**Entrega:** até **16/11/2026, 23h59**, por um representante, no **Classroom**: o artigo em **PDF** com o nome de todos
os integrantes **e** o link deste repositório. Não há apresentação: a nota sai só do artigo e do repositório.

## 2. O problema

> Em quais estados o faturamento do **comércio varejista** e dos **serviços** deve crescer **acima da inflação** nos
> **próximos 3 meses**?

Para cada estado, setor e mês, o modelo responde **1** se o faturamento real (sem inflação) dos 3 meses seguintes
for maior que o dos mesmos 3 meses do ano anterior, e **0** se não. Classificação binária.

**Critério de sucesso:** acertar mais que a regra simples "se cresceu nos últimos 3 meses, vai crescer nos próximos
3" (`media_3m > 0`).

## 3. Os dados

Todos oficiais e públicos, coletados em **14/09/2026** pelos scripts de `coleta/` (1º bimestre) e guardados em
[`dados/dados_brutos_20260914.xlsx`](dados/dados_brutos_20260914.xlsx), uma aba por fonte, exatamente como as APIs
devolveram:

| Aba | Fonte | O que é |
|---|---|---|
| IBGE varejo 8880 | Pesquisa Mensal de Comércio | índice de receita nominal do varejo (média de 2022 = 100), por UF, jan/2012–jun/2026 |
| IBGE serviços 5906 | Pesquisa Mensal de Serviços | índice de receita nominal dos serviços, por UF, jan/2012–jul/2026 |
| IBGE IPCA 1737 | IPCA | inflação oficial (número-índice), Brasil |
| BCB dólar 3698 | Banco Central (SGS) | dólar, média do mês |
| BCB Selic 4189 | Banco Central (SGS) | Selic, % ao ano |

É um **índice**, não R$ (o IBGE não publica faturamento mensal em reais). Termos explicados em
[`docs/guia.md`](docs/guia.md); referências ABNT em [`docs/fontes.md`](docs/fontes.md).

## 4. O que está pronto

| Item | Onde | Situação |
|---|---|---|
| Notebook completo (CRISP-DM, do bruto ao ranking) | `trabalho_mineracao_dados.ipynb` | pronto, executado, com saídas salvas |
| Saídas da execução (12 gráficos, dataset preparado, métricas, ranking, modelo) | `saidas/` | prontas |
| API (opcional do enunciado) | `api/main.py` | pronta e testada |
| Rascunho do artigo no modelo | `artigo/artigo_mineracao_dados.docx` | pronto, 19 páginas, com pendências em amarelo |
| O que falta no artigo | `artigo/LEIA-ME.md` | checklist |
| Resumo de cada fase do CRISP-DM | `docs/crisp.md` | pronto |
| Apresentação do seminário (1º bimestre) | `docs/apresentacao_seminario_1bi.pptx` | referência |
| Repositório do 1º bimestre | https://github.com/jhondev123/projeto_mineracao_dados | histórico |

### Como o notebook está organizado

| Seção | Fase | O que faz |
|---|---|---|
| 0 | — | importa bibliotecas, monta o Drive, define as pastas e o estilo dos gráficos |
| 1 | Entendimento do negócio | problema, alvo, critério de sucesso |
| 2 | Entendimento dos dados | carrega o xlsx, tabela de qualidade, estatísticas, gráficos 01 e 02 |
| 3 | Preparação | limpeza, integração, inflação descontada, 12 atributos, alvo, faltantes, divisão no tempo, desbalanceamento, gráficos 03 a 07 |
| 4 | Modelagem | regra de comparação, Regressão Logística, Random Forest, variações testadas na validação |
| 5 | Avaliação | métricas no teste, matrizes de confusão, ROC, importância dos atributos, erros por estado e por ano (gráficos 08 a 11) |
| 6 | Implantação | modelo final, ranking de previsão (gráfico 12), modelo salvo para a API |
| 7 | Conclusão | resumo, limitações, trabalhos futuros |

## 5. Decisões tomadas e por quê

| Decisão | Motivo |
|---|---|
| O notebook parte do **xlsx bruto** e refaz toda a preparação | o enunciado pede para documentar limpeza e transformação; o resultado reproduz exatamente o dataset do 1º bimestre (8.181 linhas, 54 séries) |
| Inflação descontada: `indice_real = indice_receita ÷ ipca` | sem isso, quase todo estado parece crescer só por causa dos preços |
| Comparar com o **mesmo mês do ano anterior** | remove a sazonalidade (dezembro do varejo ~27% acima da média do ano) |
| Atributos calculados **só com meses até o da linha** | evita vazamento de dados (o modelo "ver o futuro") |
| Faltantes **não imputados**: começo das séries removido, fim vira o conjunto de previsão | preencher inventaria crescimento que não existiu |
| Divisão **por data**: treino até 2022, validação 2023, teste 2024–2026 | em série temporal, sortear linhas vaza o futuro |
| Métrica principal: **acurácia balanceada** | 77% de casos de alta no teste: "sempre alta" dá 77% de acurácia e F1 0,87, mas 0,50 de acurácia balanceada |
| Dois modelos: **Regressão Logística** e **Random Forest** | um simples e interpretável, outro não linear com importância dos atributos; no seminário o plano era K-means + Random Forest, trocado porque o objetivo é medir a previsibilidade |
| Busca de parâmetros com `GridSearchCV` + `PredefinedSplit` (treino → validação) | escolhe na validação sem tocar no teste |
| Estado **não** entra como atributo | testado na validação: não melhora |
| Meses da pandemia **ficam** no treino | testado: tirá-los piora os dois modelos |
| Árvores **sem limite de profundidade** fora da busca | davam resultados diferentes entre scikit-learn 1.6 e 1.9; sem elas, Colab e computador dão números idênticos |
| `requirements.txt` fixa **scikit-learn 1.6.1** | é a versão do Colab; o `modelo_final.joblib` só abre na versão em que foi salvo |

## 6. Resultados (conjunto de teste, alvos de 2024 a 2026)

| | Acurácia | Acurácia balanceada | Precisão | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|---|
| Sempre "vai crescer" | 0,769 | 0,500 | 0,769 | 1,000 | 0,869 | 0,500 |
| Regra `media_3m > 0` | 0,775 | 0,699 | 0,864 | 0,840 | 0,851 | 0,787 |
| Regressão Logística | 0,710 | 0,731 | 0,910 | 0,691 | 0,785 | 0,778 |
| **Random Forest** | 0,766 | **0,737** | 0,892 | 0,791 | 0,839 | **0,795** |

- **Escolhido:** Random Forest, profundidade 4, sem peso por classe, 300 árvores.
- Acerto nas quedas: regra 56%, Random Forest 68%, Regressão Logística 77%.
- Ganho modesto sobre a regra, maior em 2025 (quando o crescimento perdeu força).
- Atributos que mais pesam: crescimento real do mês, médias de 3 e 6 meses, setor no Brasil. Selic, dólar e inflação
  entram com sinal negativo (esperado), mas pesam menos.
- Ranking (dados de 14/09/2026): varejo jul–set/2026 lidera com DF, PE, TO, AC, BA; serviços ago–out/2026 com SE, AP,
  RN, DF, BA. 24 dos 27 estados acima de 50% em cada setor.

## 7. Como rodar

**Google Colab** (o jeito principal):

1. No Drive, em **Meu Drive**, criar `trabalho_min_dados/dados/` e subir `dados/dados_brutos_20260914.xlsx`.
2. Abrir o notebook pelo botão **Abrir no Colab** do README e usar **Ambiente de execução → Executar tudo**.
3. As saídas vão para `Meu Drive/trabalho_min_dados/saidas/`. Leva de 2 a 4 minutos.

**No computador:** `pip install -r requirements.txt` e abrir o notebook ao lado da pasta `dados/`.

**API:** depois de rodar o notebook no mesmo ambiente, `uvicorn api.main:app --reload` e abrir
http://127.0.0.1:8000/docs.

## 8. Cuidados para não quebrar nada

- **Os números do artigo vêm da execução salva no notebook.** Se mudar qualquer coisa no notebook (parâmetros,
  atributos, divisão, dados), rode de novo e **atualize as tabelas e o texto do artigo**, do README e do
  `docs/crisp.md`.
- **Não volte a colocar `max_depth=None` na busca do Random Forest**: os resultados passam a variar conforme a versão
  do scikit-learn.
- **Coletar dados novos** (`coleta/planilha_bruta.py`) muda todos os números. Para a entrega, mantenha o arquivo de
  14/09/2026.
- O `modelo_final.joblib` só abre com o **scikit-learn 1.6.1**. Se der erro na API, instale o `requirements.txt` ou
  rode o notebook de novo no mesmo ambiente.
- O nome da pasta no Drive está na variável `NOME_PASTA` (seção 0 do notebook).
- O artigo tem **19 páginas** e o limite é 20: mantenha as inclusões curtas, ou reduza figuras.

## 9. O que falta para entregar

- [ ] Nomes dos integrantes: artigo (1ª página), notebook (topo) e `README.md`.
- [ ] Parágrafo sobre o **feedback do professor no seminário** (em amarelo no início da Metodologia do artigo):
      descrever cada orientação ou pergunta e como foi atendida. A apresentação do seminário está em
      `docs/apresentacao_seminario_1bi.pptx`.
- [ ] Revisar o texto do artigo e tirar o realce amarelo.
- [ ] Exportar o artigo em PDF (Word: Salvar como → PDF; Google Docs: Fazer download → PDF) e conferir que ficou entre
      14 e 20 páginas.
- [ ] (Recomendado) Rodar o notebook uma vez no Colab da conta do grupo.
- [ ] Entregar no Classroom até 16/11, 23h59: PDF + link https://github.com/jhondev123/trabalho_mineracao_2bi

## 10. Mapa do repositório

```
trabalho_mineracao_2bi/
├── CONTEXTO.md                      # este arquivo
├── README.md                        # visão geral, resultado e como rodar
├── trabalho_mineracao_dados.ipynb   # o trabalho: do dado bruto ao ranking (Colab)
├── requirements.txt                 # bibliotecas (scikit-learn fixo em 1.6.1)
├── dados/dados_brutos_20260914.xlsx # dados como vieram das APIs
├── saidas/                          # gerado pelo notebook: gráficos, dataset, métricas, ranking, modelo
├── api/main.py                      # API FastAPI
├── coleta/                          # scripts do 1º bimestre (coleta nas APIs do IBGE e do BCB)
├── artigo/
│   ├── artigo_mineracao_dados.docx  # rascunho do artigo
│   ├── LEIA-ME.md                   # pendências do artigo
│   └── modelo_artigo_disciplina.pdf # modelo da disciplina
└── docs/
    ├── crisp.md                     # o que foi feito em cada fase
    ├── guia.md                      # glossário
    ├── fontes.md                    # fontes e referências ABNT
    └── apresentacao_seminario_1bi.pptx
```
