# Módulos Python (raiz)

| Módulo | Responsabilidade | Função principal | Quem importa |
|---|---|---|---|
| `modelo3.py` | Núcleo de cálculo de eficiência de aletas (retangular, triangular, parabólica, anular, pino...), perfis de temperatura, gravação de relatórios `.txt` | `calcular_eficiencia(tipo_aleta, h, k, l, t=None, w=None, D=None, r1=None, r2=None, T_b=None, T_inf=None, condicao_ponta='adiabatica', T_L=None)` → `(eta, Q, A, epsilon, m, P, A_tr[, dados_didaticos])`; `mostrar_formula`; `salvar_resultados`/`salvar_sresultados` (gravam `static/relatorio.txt`/`static/selerelatorio.txt`); `normalizar_tipo_aleta` | `app.py:6` |
| `visualizacao_plotly.py` | Gráficos Plotly de distribuição de temperatura + extração dos mesmos dados em JSON (fonte única compartilhada gráfico/tabela) | `gerar_grafico_temperatura_interativo`, `gerar_grafico_temperatura_multiplos_materiais` → `(grafico_html, dados_base)`; `extrair_dados_curvas_json_interativo`/`_multiplos` | `app.py:7-12` |
| `metricas_engenharia.py` | Métricas derivadas (volume, área, eficiência) + interpretação textual; banco de materiais | `calcular_metricas_engenharia`, `interpretar_metricas`; expõe `MATERIAIS_DB`, `DICIONARIO_MATERIAIS_ID` | `app.py:13`, reimport local `app.py:1495` |
| `mudanca_fase_calculadora.py` | Condensação (placa vertical, tubo horizontal) e ebulição (nucleada Rohsenow, filme Berenson) | `calcular_mudanca_fase(tipo, subtipo, parametros)` — despachante único | `app.py:14` |
| `arranjos_tubos_calculadora.py` | Convecção em bancos de tubos (Zukauskas, Grimison) | `calcular_arranjo_tubos(tipo_correlacao, parametros)` (correlação usada: `'zukauskas'` fixo) | `app.py:15` |
| `escoamento_interno.py` | Escoamento interno em tubo circular — versão simples/legada, sem chamada direta encontrada nas rotas ativas | `escoamento_interno_tubo_circular(parametros)` | `app.py:16` (importado, uso ativo não confirmado — ver KNOWN_ISSUES) |
| `escoamento_dutos.py` | Escoamento interno generalizado (circular/quadrado/retangular), diâmetro hidráulico | `escoamento_interno_duto` (rota `tradicional`); `calcular_h_com_temperaturas` (import local `app.py:1384`, rota `temp_entrada_saida`); `calcular_escoamento_com_temperaturas` (import local `app.py:1412`, rota legada) | `app.py:17` |
| `tipos_aletas_config.py` | Catálogo/config dos 8 tipos de aletas (campos obrigatórios/opcionais por geometria) | `obter_tipo_aleta`, `validar_campos_obrigatorios`, `obter_campos_formulario`, `obter_info_tipo`, `TIPOS_ALETAS`, `LISTA_TIPOS_ORDENADA`, `determinar_campos_para_multiplas_aletas`, `obter_nome_display` | `app.py:18-20` |
| `conveccao_calculadora.py` | Correlações de convecção natural (placa vertical/horizontal, cilindro, esfera) e forçada (placa, cilindro cruzado, tubo interno) | `calcular_coeficiente_convectivo(tipo, geometria, parametros)` — único ponto de entrada | import **local** dentro de `app.py:735,822,978,1082` (não está no topo do arquivo) |
| `config_otimizada.py` | Dataclasses de configuração de performance/cache | — | **não é importado por `app.py`**; só por `melhorias_sistema.py` |
| `melhorias_sistema.py` | Decorators/logging/cache experimentais | — | **código órfão — nenhum módulo o importa**, ver [KNOWN_ISSUES.md](KNOWN_ISSUES.md) |

## Regra prática

Ao investigar um bug de cálculo, comece pelo módulo específico da tabela acima, não por
`app.py` inteiro — `app.py` só faz roteamento, validação de formulário e orquestração;
a lógica de engenharia térmica está nos módulos.

`conveccao_calculadora.py` é importado **dentro das funções**, não no topo de `app.py` —
se for adicionar um novo import de módulo em `app.py`, siga o padrão existente (a maioria
está no topo, mas convecção é a exceção deliberada).
