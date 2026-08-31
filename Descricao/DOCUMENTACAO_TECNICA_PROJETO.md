# Documentacao Tecnica do Projeto V28.1

## 1. Visao Geral do Sistema

O projeto implementa um laboratorio didatico de transferencia de calor com tres eixos principais:

- simulacao de aletas e comparacao de materiais;
- calculadoras de conveccao, mudanca de fase e escoamento interno;
- monitoramento termico em tempo real integrado a ESP32 e a um laboratorio termico virtual.

O backend Flask centraliza a navegacao, o processamento numerico e as APIs HTTP. Os templates HTML entregam a interface principal. Os scripts JavaScript executam interacoes locais, requisicoes assicronas, organizacao visual e composicao dinamica de resultados. Os firmwares ESP32 alimentam o monitoramento experimental com leituras de sensores e estados de bancada.

## 2. Arquitetura Flask

### 2.1 Arquivo app.py

O arquivo app.py e o ponto central da aplicacao web. Suas responsabilidades principais sao:

- inicializar a aplicacao Flask e configurar recarregamento automatico de templates;
- desabilitar cache de HTML, JS e CSS no ambiente de desenvolvimento;
- manter um cache global simples de monitoramento com as temperaturas t1, t2, t3, t4 e t5;
- expor rotas HTML para navegacao entre os modulos;
- expor rotas JSON para calculos assicronos e para monitoramento em tempo real;
- integrar os modulos numericos de aletas, conveccao, mudanca de fase, escoamento interno e visualizacao Plotly.

### 2.2 Fluxos principais de rotas

#### Simulador de aletas

- / abre a pagina inicial com acesso aos modulos.
- /tipos_aletas inicia o fluxo de comparacao entre geometrias de aletas.
- /tipos_materiais/<tipos_aletas> seleciona um material unico para as geometrias escolhidas.
- /inserir_dados/<tipos_aletas>/<material>/<k> recebe os parametros termicos e geometricos.
- /resultado calcula eficiencia, taxa de calor, efetividade, metricas de engenharia e grafico Plotly.

#### Comparacao de materiais

- /sele_aleta seleciona uma geometria unica de aleta.
- /sele_materiais seleciona multiplos materiais para a mesma geometria.
- /inserir_seledados/<sele_aleta>/<smateriais>/<k> recebe os dados de operacao.
- /resultados_sele compara os materiais escolhidos e gera grafico multitracado.

#### Calculadoras de conveccao e fenomenos correlatos

- /calculadora_convectivo apresenta a selecao do tipo de fenomeno.
- /calculadora_convectivo/<tipo> abre a calculadora especifica de conveccao natural ou forcada.
- /calculadora_convectivo/<tipo>/calcular recebe dados de formulario tradicional ou JSON e responde com HTML ou JSON, conforme o tipo de requisicao.
- /calculadora_condensacao e /calculadora_condensacao/calcular tratam o modulo de condensacao.
- /calculadora_ebulicao e /calculadora_ebulicao/calcular tratam o modulo de ebulicao.
- /calculadora_arranjos_tubos e /calculadora_escoamento_interno atendem modulos especializados de conveccao.

#### Laboratorio termico virtual e monitoramento

- /circuito_termico, /circuito_termico_moderno e /laboratorio_termico apontam para a interface do laboratorio termico virtual.
- /calcular_circuito_termico recebe JSON do laboratorio e confirma o recebimento; a logica principal do laboratorio esta no JavaScript do proprio template.
- /painel_status renderiza o painel de monitoramento em tempo real.
- /api/monitoramento aceita GET e POST para leitura e atualizacao simplificada do cache termico.
- /api/temperaturas aceita GET e POST para integracao com os ESP32, persistindo t1 a t5 no cache global.
- /api/status retorna o estado geral do sistema, incluindo versao, identificacao do servidor e temperaturas atuais.

### 2.3 Uso de APIs Flask

O projeto usa APIs Flask em dois padroes:

- HTML tradicional com render_template e redirecionamentos, principalmente nos fluxos de formularios de aletas e fenomenos termicos.
- APIs JSON com jsonify, principalmente para:
  - calculos assicronos de conveccao natural e forcada;
  - atualizacao do painel de status;
  - ingestao de dados enviados por ESP32;
  - verificacao de status do servidor.

As rotas JSON mais relevantes sao:

- /calculadora_convectivo/natural/calcular
- /calculadora_convectivo/forcada/calcular
- /api/monitoramento
- /api/temperaturas
- /api/status
- /calcular_circuito_termico

## 3. Modulos de simulacao e calculo

### 3.1 modelo3.py

O arquivo modelo3.py concentra a base matematica das aletas. Ele fornece:

- mapeamento entre tipo de aleta, imagem ilustrativa e imagem de formula;
- funcoes para calcular a taxa de calor sob diferentes condicoes de contorno na ponta;
- funcao principal calcular_eficiencia, usada pelas rotas Flask para obter eficiencia, taxa de calor, area, efetividade e dados didaticos;
- suporte a resolucao passo a passo para algumas geometrias, posteriormente exibida nos templates de resultado.

As condicoes de contorno suportadas sao:

- ponta adiabatica;
- conveccao na ponta;
- aleta infinitamente longa;
- temperatura especificada na ponta.

### 3.2 visualizacao_plotly.py

O arquivo visualizacao_plotly.py gera os graficos interativos incorporados diretamente nos templates de resultado. Suas funcoes principais:

- gerar_grafico_temperatura_interativo cria curvas de temperatura ao longo do comprimento da aleta para comparacao entre geometrias;
- gerar_grafico_temperatura_multiplos_materiais cria curvas comparativas para uma mesma geometria com diferentes materiais;
- gerar_graficos_comparativos estrutura visualizacoes adicionais de metricas de desempenho.

Caracteristicas dos graficos:

- eixo x em milimetros;
- hover interativo por curva;
- linhas de referencia para T_infinito e T_base;
- escala vertical ajustada automaticamente a faixa real de temperaturas calculadas.

### 3.3 metricas_engenharia.py

O arquivo metricas_engenharia.py complementa o calculo termico com indicadores de engenharia. Ele calcula:

- volume aproximado da aleta conforme a geometria;
- area superficial total;
- massa estimada a partir da densidade do material;
- custo total aproximado;
- razao custo-beneficio em W por unidade monetaria;
- interpretacoes sinteticas, divididas em pontos fortes, alertas e recomendacoes.

Essas saidas sao renderizadas nos templates de resultados e ampliam o carater didatico e comparativo da aplicacao.

## 4. Templates HTML principais

### 4.1 templates/index.html

E a pagina inicial do sistema. Sua funcao e apresentar o menu de entrada para os modulos principais:

- comparar tipos de aletas;
- comparar materiais;
- calculadora de conveccao;
- painel de status;
- laboratorio termico virtual.

Elementos interativos principais:

- botoes de navegacao ancorados em url_for;
- fundo animado com imagens de aletas flutuantes;
- eventos de mouse nas imagens, com ampliacao, rotacao e realce visual.

O JavaScript local deste template e exclusivamente de apresentacao. Ele constroi dinamicamente 20 imagens flutuantes usando os arquivos em static/aletas e aplica animacoes de hover.

### 4.2 templates/sele_aleta.html

Este template inicia o fluxo de comparacao de materiais para uma unica geometria de aleta. A interface exibe cartoes clicaveis com miniaturas de geometrias.

Funcoes principais:

- selecionar visualmente a geometria;
- atualizar a pre-visualizacao ampliada da aleta e da formula associada;
- controlar a exibicao do botao de confirmacao;
- enviar a selecao para a rota /sele_materiais.

Elementos interativos:

- cartoes com comportamento selected;
- imagens de preview da geometria e formula;
- botoes de confirmar e voltar.

### 4.3 templates/sele_materiais.html

Continua o fluxo de comparacao de materiais. Sua funcao e permitir a marcacao de varios materiais para a geometria escolhida.

Elementos principais:

- lista de checkboxes com nome do material e condutividade k;
- botao de envio para a rota /sele_materiais via POST;
- botao de retorno para a selecao de aleta.

### 4.4 templates/inserir_dados.html

Template de entrada de dados para comparacao entre varios tipos de aletas usando um unico material.

Funcoes do template:

- exibir os tipos de aleta selecionados;
- apresentar apenas os campos geometricos pertinentes a cada familia de geometria;
- coletar h, T_b, T_inf, L e parametros complementares;
- permitir a definicao da condicao de contorno na ponta;
- integrar-se com a calculadora de conveccao para importar um valor de h salvo no localStorage.

Funcoes JavaScript principais:

- toggleTempCampo: mostra ou oculta o campo T_L quando a opcao de temperatura especificada e escolhida;
- abrirCalculadoraConvectivo: abre a calculadora de conveccao em nova aba;
- verificarCoeficienteCalculado: le o coeficiente salvo em localStorage, preenche o campo h e marca visualmente a origem do valor.

### 4.5 templates/inserir_seledados.html

E equivalente ao template anterior, mas aplicado ao fluxo de uma unica aleta comparada com varios materiais.

Comportamentos principais:

- adapta os campos ao texto da geometria selecionada;
- recebe o mesmo conjunto de parametros termicos e geometricos;
- usa o mesmo mecanismo de importacao de h a partir do localStorage;
- envia os dados para a rota que gera comparacao entre materiais.

### 4.6 templates/resultado.html

Apresenta os resultados do fluxo de comparacao entre geometrias para um mesmo material.

Conteudo exibido:

- tabela de metricas de desempenho por geometria;
- descricao da condicao de contorno na ponta;
- fundamentos teoricos de efetividade e eficiencia;
- metricas de engenharia por caso;
- grafico interativo Plotly com distribuicao de temperatura;
- secao didatica com resolucao passo a passo quando os dados didaticos estao disponiveis.

O template funciona como camada de apresentacao dos dados calculados em app.py, modelo3.py, metricas_engenharia.py e visualizacao_plotly.py.

### 4.7 templates/resultados_sele.html

Tem estrutura anloga ao template anterior, mas a tabela principal compara materiais para a mesma geometria de aleta.

Destaques:

- cada linha inclui tipo de aleta, material, efetividade, parametro m, perimetro P e area transversal;
- o grafico Plotly agrega curvas associadas aos diferentes materiais;
- as metricas de engenharia sao repetidas para cada material analisado.

### 4.8 templates/calculadora_convectivo.html

Funciona como menu de escolha para fenomenos convectivos e correlatos.

Cartoes disponiveis:

- conveccao natural;
- conveccao forcada;
- condensacao;
- ebulicao;
- arranjos de tubos;
- escoamento interno.

Comportamento interativo:

- clique em cartao seleciona um radio button oculto;
- o envio do formulario redireciona para a calculadora correta;
- o layout destaca visualmente o tipo ativo.

### 4.9 templates/calculadora_natural.html

E a interface da calculadora de conveccao natural. Ela combina formulario de calculo com painel lateral de monitoramento ao vivo.

#### Elementos interativos

- selecao de geometria por cartoes clicaveis;
- exibicao condicional de campos para placa vertical, placa horizontal, cilindro horizontal e esfera;
- painel lateral com temperaturas T1 a T5;
- botao para importar dados do monitoramento para os campos termicos do calculo;
- submissao AJAX do calculo para obter JSON sem recarregar a pagina.

#### Funcoes JavaScript principais

- buscarDadosMonitoramento: faz GET em /api/monitoramento;
- atualizarCardsTemperatura: atualiza T1, T2, T3, T4 e T5 no painel lateral;
- importarDadosParaCalculos: usa T4 como temperatura do fluido e a media de T1, T2 e T3 como temperatura de superficie;
- mostrarFeedbackImportacao: sinaliza visualmente sucesso ou erro na importacao;
- iniciarMonitoramento e pararMonitoramento: controlam o polling a cada 2 segundos;
- selectGeometry: alterna a geometria ativa e os campos visiveis;
- atualizarLcInfo: calcula e mostra o comprimento caracteristico Lc para placa horizontal;
- enviarCalculoAjax: envia JSON para /calculadora_convectivo/natural/calcular;
- exibirResultados: monta dinamicamente o bloco HTML de resposta com h, Nu, Ra, Pr, regime, Lc e orientacao.

#### Uso de API Flask

- GET /api/monitoramento para dados ao vivo;
- POST JSON para /calculadora_convectivo/natural/calcular.

### 4.10 templates/calculadora_forcada.html

E a interface correspondente para conveccao forcada. Compartilha o mesmo padrao visual e o mesmo painel lateral de monitoramento.

#### Elementos interativos

- selecao de geometria por cartoes;
- campos condicionais para placa plana e cilindro;
- painel lateral T1 a T5 com importacao automatica para o formulario;
- envio assicrono do calculo.

#### Funcoes JavaScript principais

- buscarDadosMonitoramento e atualizarCardsTemperatura: iguais em conceito ao template de conveccao natural;
- importarDadosParaCalculos: usa T4 como temperatura do fluido e a media de T1, T2 e T3 como temperatura da superficie;
- setupFormularioCalculos: registra a submissao AJAX;
- enviarCalculoAjax: envia JSON para /calculadora_convectivo/forcada/calcular;
- exibirResultados: compoe um painel de resultados com h, Nu, Re, Pr e regime de escoamento.

#### Uso de API Flask

- GET /api/monitoramento;
- POST JSON para /calculadora_convectivo/forcada/calcular.

### 4.11 templates/calculadora_condensacao.html

Esse template apresenta uma calculadora orientada a mudanca de fase por condensacao.

Funcoes principais:

- expor o conteudo teorico das correlacoes de Nusselt para placa vertical e tubo horizontal;
- coletar geometria, fluido, temperatura de saturacao e temperatura de parede;
- mostrar campos geometricos especificos para placa ou tubo;
- exibir resultados de h, Nu, regime, diferencial termico e fluxo de calor.

O processamento ocorre no backend Flask pela rota /calculadora_condensacao/calcular.

### 4.12 templates/calculadora_ebulicao.html

Este template implementa a entrada e apresentacao do modulo de ebulicao.

Capacidades exibidas:

- selecao entre ebulicao nucleada e em filme;
- selecao do fluido e temperatura de saturacao;
- definicao da temperatura da superficie;
- campos complementares para superficie e geometria quando o regime escolhido exige esses dados;
- exibicao de resultados de h, fluxo de calor, regime e excesso de temperatura.

O template tambem incorpora blocos explicativos sobre as correlacoes de Rohsenow e Berenson.

### 4.13 templates/calculadora_arranjos_tubos.html

E uma calculadora dedicada a bancos de tubos em linha ou alternados.

Pontos centrais:

- apresenta diagramas simplificados dos dois arranjos;
- coleta diametro dos tubos, espacamentos transversal e longitudinal, numero de fileiras e condicoes do escoamento;
- recolhe temperaturas de superficie e do fluido, velocidade de entrada e fluido de trabalho;
- envia os dados ao backend para calculo do coeficiente convectivo e correlacoes associadas.

### 4.14 templates/calculadora_escoamento_interno.html

Este template atende escoamento interno em tubos e dutos.

Caracteristicas principais:

- documenta no proprio HTML as correlacoes para regime laminar desenvolvido e para regime turbulento via Gnielinski;
- permite selecionar geometria circular, quadrada ou retangular;
- organiza os campos de entrada por geometria e por propriedades de escoamento;
- usa MathJax para renderizar expressoes matematicas diretamente na pagina.

### 4.15 templates/painel_status.html

E a interface de monitoramento em tempo real do sistema experimental.

#### Funcao geral

- apresentar as leituras T1 a T5 em cartoes grandes;
- manter historico recente de temperaturas em um grafico de linhas Chart.js;
- permitir reorganizar visualmente os rotulos dos cartoes por arraste;
- sincronizar continuamente com o cache de monitoramento do Flask.

#### Estrutura do monitoramento

- T1: inicio da chama;
- T2: meio da chapa;
- T3: final da chama;
- T4: ambiente;
- T5: baixo da placa.

#### Funcoes JavaScript principais

- inicializarGrafico: cria o grafico Chart.js com cinco series;
- adicionarPontoGrafico: insere amostras no historico e limita a janela a 20 pontos;
- buscarDadosMonitoramento: chama GET /api/monitoramento;
- atualizarCardsTemperatura: atualiza os cartoes e empilha novos pontos no historico;
- aplicarOrdem e salvarOrdem: persistem no localStorage a ordem visual dos rotulos dos cartoes;
- initDragDrop: habilita arraste pelos handles visuais;
- atualizarAgora: executa uma leitura imediata sob demanda.

#### Historico e graficos

O historico usa um objeto temperatureHistory com:

- labels para o horario formatado;
- arrays independentes para t1, t2, t3, t4 e t5.

Cada atualizacao obtida da API cria um novo ponto temporal, e o grafico e atualizado sem animacao extensa. O eixo y e configurado entre 10 e 90 graus Celsius no template.

## 5. Laboratorio termico virtual

### 5.1 templates/circuito_termico_moderno.html

Este e o arquivo mais abrangente da interface. Ele implementa um laboratorio termico virtual client-side para montar circuitos de resistencias termicas em serie, em paralelo, com superficies aletadas, camadas solidas e fluidos convectivos, tanto em geometria planar quanto cilindrica.

### 5.2 Funcoes gerais do laboratorio

O template permite:

- selecionar entre geometria planar e cilindrica;
- adicionar camadas solidas;
- adicionar camadas de fluido;
- adicionar blocos paralelos com ramos independentes;
- adicionar superficies aletadas;
- informar temperaturas de entrada e saida;
- informar q conhecido e T_ref como entradas auxiliares;
- visualizar uma representacao fisica e a traducao em circuito termico;
- calcular resistencias equivalentes e produzir um relatorio detalhado em HTML;
- consultar sensores ao vivo a partir da API /api/monitoramento.

### 5.3 Elementos interativos principais

- geometry-card: alterna entre geometria planar e cilindrica;
- layer-btn: cria camadas ou blocos estruturais;
- layers-list: lista editavel das camadas do modelo;
- circuit-display: area de visualizacao do circuito e da geometria;
- popup de sensores ao vivo ancorado na caixa de temperaturas de contorno;
- botoes Calcular Circuito Termico e Limpar Tudo.

### 5.4 Funcoes JavaScript relevantes do laboratorio

#### Estruturacao da modelagem

- selectGeometry(geometry): troca o modo entre planar e cylindrical, ajustando a representacao do sistema;
- addLayer(type): insere uma camada solida ou de fluido;
- addFinnedSurface(): cria uma camada de superficie aletada com parametros editaveis;
- addParallelBlock(): cria um bloco paralelo com ramos independentes;
- clearAll(): remove toda a configuracao montada e limpa a exibicao dos resultados.

#### Calculo e consolidacao

- calculateThermalCircuit(): executa o processamento principal do circuito termico dentro do navegador;
- summarizeParallelBlock(): calcula a resistencia equivalente de blocos paralelos, inclusive em aninhamento;
- computeBranchResistance() e computeParallelEquivalent(): processam ramos e equivalentes de redes paralelas;
- buildPlanarMetrics(), buildConvMetrics() e buildCylMetrics(): derivam grandezas de resistencia para camadas planas, convectivas ou cilindricas;
- renderMetrics(): atualiza o bloco explicativo de formulas e substituicoes numericas conforme a camada ativa;
- refreshMainMetrics(): atualiza o painel principal de metricas apos alteracoes de entradas.

#### Temperaturas de contorno e sensores

- listeners em temp-in e temp-out sincronizam globalTemps.Tin e globalTemps.Tout;
- entradas q conhecido e T_ref permitem inferencia complementar quando Tin e Tout nao sao usados;
- fetch('/api/monitoramento') atualiza o popup de sensores ao vivo com T1 a T5.

#### Visualizacao e experiencia de uso

- o template usa SVG, animacoes CSS e destaques de camada ativa;
- ha organizacao lado a lado entre representacao fisica e circuito termico;
- blocos paralelos possuem visualizacao resumida e estrutura expandivel;
- a secao de resultados recebe um HTML detalhado com metricas, formulas, contribuicoes e desempenho por camada.

### 5.5 Logica termica implementada no laboratorio

O laboratorio trabalha com tres niveis logicos:

- definicao da topologia do problema: serie, paralelo e subestruturas aninhadas;
- definicao da fisica de cada camada: conducao plana, conducao cilindrica, conveccao simples, conveccao com radiacao linearizada e superficies aletadas;
- consolidacao do circuito equivalente: soma em serie, associacao paralela e calculo de grandezas globais como R_total, q, U e UA.

Em geometria planar, a resistencia de conducao segue o padrao L/(kA), com possibilidade de resistencia de contato. Em camadas fluidas, o template usa 1/(hA) e, quando habilitado, adiciona radiacao linearizada por meio de um h_rad efetivo. Em geometria cilindrica, usa a forma logaritmica ln(r2/r1)/(2pi k L). Para superficies aletadas, calcula eficiencia da aleta, eficiencia global da superficie e resistencia equivalente.

## 6. Scripts JavaScript auxiliares

### 6.1 static/js/popover_content.js

Este script disponibiliza funcoes globais para construir o conteudo HTML dos popovers de edicao de camadas.

Funcoes principais:

- numberInput: gera campos numericos padronizados para os formularios internos;
- createNormalContent(layer, isFluid): monta a interface de propriedades para uma camada de fluido ou de solido;
- createFinnedContent(layer): monta a interface de propriedades de uma superficie aletada e ja mostra metricas derivadas.

Campos gerados para fluidos:

- h;
- T;
- emissividade epsilon;
- T_viz;
- opcao para incluir radiacao linearizada.

Campos gerados para solidos:

- espessura L;
- condutividade k;
- resistencia de contato.

Campos gerados para superficies aletadas:

- numero de aletas N;
- comprimento L;
- espessura ou diametro;
- largura w;
- k da aleta;
- h de base;
- definicao automatica ou manual da area de base.

### 6.2 static/js/popover_avancado.js

Este script controla a camada de edicao avancada do laboratorio termico virtual. Ele cria, posiciona e fecha popovers, renderiza metricas por camada e permite edicao mais rica de estruturas paralelas e superficies aletadas.

Responsabilidades principais:

- destroyCurrent: encerra o popover ativo e remove o painel lateral associado;
- renderFinnedMetrics: calcula e exibe formulas detalhadas para aletas retangulares ou cilindricas;
- createFinnedContent: monta o formulario expandido de superficie aletada;
- positionSmart: posiciona o popover na viewport conforme o elemento de origem;
- header, metricsContainers, actionsBar e footerButtons: constroem o layout base do popover;
- buildPlanarMetrics, buildConvMetrics e buildCylMetrics: suportam a exibicao de formulas e resistencias equivalentes;
- renderMetrics: atualiza a explicacao numerica do tipo de camada selecionado;
- subLayerForm: gera editores inline para subcamadas e blocos paralelos aninhados.

Em termos funcionais, ele e a infraestrutura de edicao detalhada do laboratorio termico, enquanto o template principal retem a topologia e a renderizacao global.

### 6.3 static/js/side_popover_helper.js

Este script cria um painel lateral de imagem associado a um popover principal.

Funcao global:

- openSideImagePopoverFor(anchorEl): abre um quadro lateral fixo contendo um esquema grafico de parede plana ou cilindro, dependendo da geometria selecionada.

Comportamentos implementados:

- escolhe automaticamente a imagem entre /static/formulas/parede.png e /static/formulas/cilindro.png;
- posiciona o painel ao lado do popover principal;
- reage a resize e scroll da janela;
- permite arrastar manualmente o quadro pela cabecalho;
- oferece botoes de reset de posicao e fechamento.

Esse painel funciona como apoio visual para a leitura das notacoes termicas usadas no laboratorio.

### 6.4 new_function_content.js

Este arquivo contem um gerador de HTML rico para exibicao de resultados do circuito termico. Ele trabalha como um fragmento de composicao textual baseado em objetos JavaScript previamente calculados.

Entradas logicas utilizadas pelo arquivo:

- result, contendo R_total, q, deltaT e layers;
- boundaryTemps, contendo T_in e T_out;
- selectedGeometry;
- planarParams;
- auxiliaryInputs.

Estrutura funcional:

- funcoes utilitarias fmt e fmtExp para formatacao numerica;
- leitura de dados globais de resultado e filtragem de camadas por tipo;
- composicao de cards de metricas globais, como R_total, q, U e UA;
- composicao de uma secao especifica para superficies aletadas, com parametros geometricos e desempenho;
- composicao de uma analise por camada, com contribuicoes percentuais e formulas;
- montagem de tabela resumo por camada.

O objetivo do arquivo e produzir uma saida detalhada, com viés de relatorio tecnico, diretamente no front-end.

## 7. Estilo visual reutilizavel

### 7.1 static/css/popover.css

Este arquivo define estilos reutilizaveis para acoes em popovers e paineis de propriedades.

Classes principais:

- btn-pop: estilo base para botoes de popover;
- btn-pop-save: variante de confirmacao;
- btn-pop-cancel: variante de cancelamento;
- btn-pop-secondary: variante secundaria;
- btn-pop-danger: variante destrutiva;
- prop-actions: organizacao do rodape de acoes;
- prop-actions.compact: variacao com margem reduzida.

Ele padroniza a experiencia visual dos controles que aparecem nos editores de propriedades do laboratorio termico.

## 8. Fluxo de monitoramento termico em tempo real

O monitoramento do projeto gira em torno do objeto monitoring_cache em app.py, com as chaves t1, t2, t3, t4 e t5.

### 8.1 Atualizacao de dados

- um ESP32 pode atualizar o cache por POST em /api/monitoramento;
- os ESP32 de bancada tambem podem postar em /api/temperaturas;
- o backend converte os valores recebidos para float e substitui as leituras atuais no cache.

### 8.2 Consumo pelos templates

- painel_status.html faz polling periodico de /api/monitoramento e alimenta cards e grafico;
- calculadora_natural.html e calculadora_forcada.html fazem polling do mesmo endpoint para preencher seus paineis laterais;
- circuito_termico_moderno.html consulta /api/monitoramento para alimentar o popup de sensores ao vivo.

### 8.3 Historico e grafico

O historico de temperaturas e mantido no navegador, nao no servidor. O fluxo e:

- cada resposta da API adiciona um timestamp local formatado em hh:mm:ss;
- os valores T1 a T5 sao empilhados em arrays por serie;
- o grafico Chart.js renderiza as cinco curvas;
- a janela historica e limitada aos 20 pontos mais recentes.

## 9. Firmwares ESP32

### 9.1 esp32_monitor_ambiente/esp32_monitor_ambiente.ino

Esse firmware opera como monitor de ambiente e base da placa, identificado no proprio banner serial como ESP32 #02.

#### Objetivo funcional

- ler dois sensores DS18B20 no barramento OneWire ligado ao pino D4;
- associar esses sensores a T4 e T5;
- aplicar calibracao por offset individual;
- reenviar periodicamente os dados ao servidor Flask via HTTP POST em /api/temperaturas.

#### Mapeamento de sensores

- T4 corresponde ao ambiente;
- T5 corresponde ao baixo da placa.

Os indices INDICE_T4 e INDICE_T5 determinam qual endereco do barramento sera associado a cada funcao fisica.

#### Robustez de leitura

O firmware contem logica de confiabilidade:

- valida se o sensor retornou leitura diferente de DEVICE_DISCONNECTED_C;
- descarta o valor padrao 85.0 e leituras fora da faixa fisica de operacao do sensor;
- acompanha erros consecutivos por sensor;
- depois de cinco falhas seguidas, invalida o sensor, zera o estado e forca um novo scan do barramento.

#### Calibracao

Cada sensor recebe um offset fixo:

- OFFSET_T4 para ambiente;
- OFFSET_T5 para baixo da placa.

As leituras validas sao corrigidas antes de serem armazenadas em temperaturasAtuais.

#### Ciclo operacional

- setup inicializa Serial, Wi-Fi, sensores DS18B20 e sincronizacao NTP;
- loop executa reconexao Wi-Fi periodica, tentativa de redescoberta de sensores, leitura termica a cada 1 segundo e envio HTTP a cada 2 segundos.

#### Comunicacao HTTP com Flask

O firmware monta um payload JSON contendo apenas t4, t5 e timestamp. A decisao de enviar somente t4 e t5 evita sobrescrever dados de t1, t2 e t3 que pertencem ao outro ESP32 da bancada.

Estrutura tipica do payload:

- t4, quando a leitura do sensor ambiente e valida;
- t5, quando a leitura do sensor inferior da placa e valida;
- timestamp com base em millis().

#### Saida serial

O monitor serial mostra:

- detalhes de conexao Wi-Fi;
- enderecos dos sensores encontrados;
- temperatura atual de cada canal;
- status do sistema e memoria livre;
- URL, payload e resposta HTTP de cada envio.

### 9.2 esp32_painel_status/esp32_painel_status.ino

Esse firmware implementa um painel de estado local baseado em HX711 e indicadores LED, voltado a leitura de flexao.

#### Objetivo funcional

- ler um conversor HX711 por interface de clock e dados;
- calibrar um ponto de zero e uma flexao maxima de referencia;
- determinar se o sistema esta em repouso ou flexionado;
- sinalizar o estado por LEDs e por mensagens no monitor serial.

#### Hardware e sinais

- PIN_SCK e PIN_DT controlam a leitura do HX711;
- LED_VERDE indica repouso;
- LED_AZUL e usado como indicacao visual do estado flexionado;
- LED_BOARD atua com brilho proporcional ao percentual de flexao.

#### Funcoes principais

- lerHX711: realiza a leitura bruta de 24 bits no canal A com ganho 128;
- mediaRapida: faz media curta de amostras validas para reduzir ruido;
- atualizarLeds: traduz o percentual de flexao para o estado dos LEDs;
- calibrarZero: define o nivel basal sem carga;
- calibrarFlexaoMaxima: mede a maior deflexao e ajusta automaticamente os limiares de histerese.

#### Logica de histerese

O estado de flexao nao muda por um unico valor instantaneo. O firmware usa dois limiares:

- limiarEntrarFlexao para entrar no estado FLEXIONADO;
- limiarSairFlexao para sair desse estado e retornar a REPOUSO.

Esse mecanismo reduz oscilacoes rapidas de estado quando a leitura esta proxima do ponto de transicao.

#### Interacao serial

O usuario pode enviar comandos pelo monitor serial:

- Z ou z para calibrar zero;
- M ou m para calibrar flexao maxima.

#### Telemetria serial

A cada segundo, o firmware imprime:

- leitura bruta;
- delta em relacao ao zero;
- percentual de flexao;
- estado FLEXIONADO ou REPOUSO;
- valor zero calibrado;
- valor maximo de flexao calibrado.

Esse firmware nao publica dados ao Flask. Seu papel e fornecer monitoramento local de flexao e sinalizacao instantanea na propria placa.

## 10. Relacao entre interface, calculo e bancada

O sistema completo integra tres camadas:

- a camada web de ensino e simulacao, organizada em Flask, templates e JavaScript;
- a camada de calculo, organizada nos modulos Python de aletas, conveccao, metricas e visualizacao;
- a camada experimental, organizada nos firmwares ESP32 que alimentam as temperaturas do painel e os estados fisicos da bancada.

Esse arranjo permite que os usuarios:

- acompanhem temperaturas reais da bancada;
- importem essas leituras para calculadoras de conveccao;
- montem circuitos termicos virtuais com interpretacao grafica e formulaica;
- comparem geometrias de aletas e materiais com suporte numerico e visual.
