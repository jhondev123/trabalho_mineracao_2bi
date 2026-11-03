# Artigo — o que falta para entregar

`artigo_mineracao_dados.docx` é o rascunho do artigo, já no formato do modelo da disciplina (A4, margens de 3 cm,
Arial 12, espaçamento 1,5) e com todas as seções pedidas: resumo, introdução, objetivos, fundamentação teórica,
metodologia (as 6 fases do CRISP-DM), resultados e conclusões e referências em ABNT. Todos os números, tabelas e
figuras vêm da execução do notebook salva no repositório.

O modelo original da disciplina está em `modelo_artigo_disciplina.pdf`, nesta pasta. Contexto completo do trabalho em
[`../CONTEXTO.md`](../CONTEXTO.md).

Abre no Word ou no Google Docs (Arquivo → Abrir → Upload). Os trechos com **fundo amarelo** são os que precisam ser
completados.

## Pendências

- [ ] **Nomes dos integrantes** — na primeira página do artigo (2 linhas em amarelo), no topo do notebook e no
      `README.md`.
- [ ] **Feedback do seminário** — o enunciado exige incorporar as orientações e os questionamentos feitos na
      apresentação. Há um parágrafo em amarelo no início da **Metodologia** para descrever cada orientação e como
      foi atendida (a apresentação está em `docs/apresentacao_seminario_1bi.pptx`). Já está escrito o que mudou desde o seminário (dois classificadores comparados no lugar do
      K-means; teste com e sem a pandemia; pesos por classe; regra de comparação).
- [ ] **Revisar o texto** e tirar o realce amarelo.
- [ ] **Conferir o número de páginas** — o modelo pede de 14 a 20. O rascunho tem 19; se as inclusões passarem de
      20, dá para diminuir as figuras (clique na imagem e reduza a largura) ou o espaço entre parágrafos.
- [ ] **Exportar em PDF** — Word: Arquivo → Salvar como → PDF. Google Docs: Arquivo → Fazer download → PDF.
- [ ] **Entregar no Classroom até 16/11, 23h59** — o PDF do artigo e o link do repositório:
      https://github.com/jhondev123/trabalho_mineracao_2bi

## Opcional, mas recomendado

- Rodar o notebook no Colab uma vez (instruções no `README.md`) para confirmar que tudo funciona na conta do grupo.
  O resultado foi testado com o scikit-learn 1.6 (versão do Colab) e 1.9 e dá exatamente os mesmos números.
- As 12 figuras em tamanho original estão em `saidas/graficos/`, caso queiram trocar alguma.

## De onde vêm as figuras do artigo

| Figura do artigo | Arquivo em `saidas/graficos/` |
|---|---|
| 1 – Sazonalidade | `02_sazonalidade.png` |
| 2 – Com e sem inflação | `03_nominal_vs_real.png` |
| 3 – Casos de alta por ano | `05_casos_de_alta_por_ano.png` |
| 4 – Correlação | `06_correlacao_atributos.png` |
| 5 – Matrizes de confusão | `08_matrizes_confusao.png` |
| 6 – Curva ROC | `09_curva_roc.png` |
| 7 – Importância dos atributos | `10_importancia_atributos.png` |
| 8 – Ranking de previsão | `12_ranking_previsao.png` |
