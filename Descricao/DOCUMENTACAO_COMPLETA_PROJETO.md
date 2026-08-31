# Documentacao Completa do Projeto V28.1

## 1. Identificacao do sistema

O projeto V28.1 e um laboratorio didatico e computacional de transferencia de calor. Ele reune uma aplicacao web Flask, modulos Python de calculo, paginas HTML, scripts JavaScript, imagens tecnicas, relatorios textuais e dois firmwares para placas ESP32.

O sistema trabalha com os seguintes temas:

- calculo e comparacao de aletas;
- comparacao de materiais para uma mesma aleta;
- conveccao natural;
- conveccao forcada;
- condensacao;
- ebulicao;
- bancos ou arranjos de tubos;
- escoamento interno em tubos e dutos;
- circuito termico virtual;
- monitoramento de temperaturas por sensores ESP32;
- apresentacao grafica e relatorios tecnicos.

A aplicacao recebe dados por formularios HTML, requisicoes JSON, valores armazenados no navegador e mensagens HTTP enviadas pelos ESP32. Esses dados sao processados por rotinas especializadas e apresentados em paginas HTML, graficos interativos, cartoes de temperatura e relatorios textuais.

## 2. Organizacao geral

A estrutura funcional do projeto pode ser dividida em cinco grupos:

1. Aplicacao web e rotas: `app.py`.
2. Calculos termicos e fluidodinamicos: modulos Python.
3. Interfaces: templates HTML e JavaScript.
4. Circuito termico virtual: JavaScript incorporado principalmente em `circuito_termico_moderno.html`.
5. Instrumentacao: firmwares ESP32.

O fluxo geral e:

```text
Usuario ou sensor ESP32
        |
        v
Formulario HTML ou requisicao HTTP
        |
        v
app.py
        |
        v
Modulo Python ou logica JavaScript do circuito
        |
        v
Resultados numericos e estruturas de dados
        |
        v
Template HTML, grafico, painel ou relatorio
```

## 3. Tecnologias utilizadas

### Python

Python e utilizado no backend Flask e nos calculos de transferencia de calor. Os modulos fazem uso de estruturas de dados, funcoes matematicas, NumPy, SciPy, Matplotlib e Plotly.

### Flask

Flask fornece:

- inicializacao do servidor web;
- definicao de rotas;
- recebimento de formularios;
- recebimento de JSON;
- redirecionamentos;
- renderizacao de templates Jinja;
- respostas JSON;
- armazenamento global temporario das temperaturas.

### HTML e Jinja

Os templates HTML compoem as telas da aplicacao. Jinja insere dados calculados pelo Python, como resultados, nomes de materiais, parametros, metricas, mensagens e HTML de graficos.

### JavaScript

JavaScript controla:

- selecao de geometrias;
- exibicao condicional de campos;
- envio AJAX;
- consulta periodica do monitoramento;
- atualizacao dos cartoes de temperatura;
- historico do grafico;
- montagem do circuito termico;
- popovers de propriedades;
- relatorios gerados no navegador.

### Plotly e Chart.js

Plotly gera graficos interativos de distribuicao de temperatura e comparacoes de desempenho. Chart.js apresenta o historico das temperaturas recebidas pelo painel de monitoramento.

### ESP32

Os firmwares Arduino/C++ leem sensores termicos, realizam validacao e calibracao, conectam-se ao Wi-Fi e enviam dados ao backend Flask por HTTP.

## 4. Arquivo `app.py`

`app.py` e o ponto central da aplicacao web.

### 4.1 Inicializacao

O arquivo cria uma instancia Flask chamada `app` e configura:

- chave secreta para sessoes e mensagens flash;
- recarregamento automatico de templates;
- desativacao de cache durante o desenvolvimento;
- modo debug;
- host e porta definidos pela execucao da aplicacao.

A funcao `add_no_cache_headers(resp)` e executada depois de cada requisicao. Ela adiciona cabecalhos HTTP que impedem o navegador de reutilizar HTML, JavaScript e CSS armazenados em cache.

### 4.2 Cache de monitoramento

O dicionario global `monitoring_cache` armazena:

```text
{
    t1: 0.0,
    t2: 0.0,
    t3: 0.0,
    t4: 0.0,
    t5: 0.0,
    t6: 0.0
}
```

Cada chave representa um canal de temperatura. O cache permanece em memoria enquanto o servidor esta em execucao.

### 4.3 `validar_parametros_fisicos`

Recebe:

- `h`: coeficiente de conveccao;
- `k`: condutividade termica;
- `T_b`: temperatura da base;
- `T_inf`: temperatura do ambiente ou fluido;
- `l`: comprimento;
- `t`: espessura;
- `w`: largura;
- `r1`: raio interno;
- `r2`: raio externo;
- `D`: diametro;
- `T_L`: temperatura da ponta.

A funcao cria uma lista de mensagens e verifica limites positivos, limites superiores, temperatura minima e relacao entre raios. Retorna uma tupla:

```text
(validacao, lista_de_erros)
```

### 4.4 Fluxo de comparacao entre geometrias

#### `/tipos_aletas`

Exibe a selecao de geometrias. No POST, coleta todos os campos `tipo_aleta` e redireciona para `/tipos_materiais`.

#### `/tipos_materiais/<tipos_aletas>`

Recebe as geometrias selecionadas e exibe os materiais. No POST, obtem o identificador do material, localiza seu nome e sua condutividade e redireciona para a entrada de dados.

#### `/inserir_dados/<tipos_aletas>/<material>/<k>`

Recebe os parametros termicos e geometricos. Converte os campos de texto para `float`, verifica campos obrigatorios, valida os parametros e verifica quais dimensoes sao necessarias para cada geometria.

Os grupos de parametros sao:

- aletas retangulares, triangulares e parabolicas: `t` e `w`;
- aleta circular de perfil retangular: `r1`, `r2` e a dimensao transversal usada pela tela;
- aletas de perfil ou pinos: `D`;
- todas: `h`, `T_b`, `T_inf` e `l`.

A rota entao redireciona para `/resultado`.

#### `/resultado`

Le os parametros enviados na URL, percorre cada geometria selecionada e chama `calcular_eficiencia` de `modelo3.py`.

Para cada resultado, a rota:

1. extrai eficiencia, calor, area, efetividade, `m`, `P`, `A_tr` e dados didaticos;
2. chama `calcular_metricas_engenharia`;
3. chama `interpretar_metricas`;
4. armazena os dados para o template;
5. gera um grafico Plotly;
6. salva um relatorio textual;
7. renderiza `resultado.html`.

### 4.5 Fluxo de comparacao entre materiais

#### `/sele_aleta`

Recebe uma unica geometria de aleta.

#### `/sele_materiais`

Recebe uma lista de materiais selecionados. Para cada material, extrai nome e condutividade `k`.

#### `/inserir_seledados/<sele_aleta>/<smateriais>/<k>`

Recebe os parametros de operacao e reconstrui a lista de materiais. Depois valida os dados e redireciona para `/resultados_sele`.

#### `/resultados_sele`

Percorre todas as combinacoes de geometria e material:

```text
para cada geometria:
    para cada material:
        calcular aleta
        calcular metricas
        gerar interpretacao
        armazenar resultado
```

Ao final, chama `gerar_grafico_temperatura_multiplos_materiais`, salva `static/selerelatorio.txt` e renderiza `resultados_sele.html`.

### 4.6 Rotas de conveccao

`/calculadora_convectivo` apresenta o menu geral.

O POST do mesmo caminho identifica o tipo selecionado e redireciona para:

- `/calculadora_convectivo/natural`;
- `/calculadora_convectivo/forcada`;
- `/calculadora_condensacao`;
- `/calculadora_ebulicao`;
- `/calculadora_arranjos_tubos`;
- `/calculadora_escoamento_interno`.

As rotas `/calculadora_convectivo/natural/calcular` e `/calculadora_convectivo/forcada/calcular` aceitam formulario ou JSON.

Quando a requisicao e JSON, o backend devolve `jsonify`. Quando e formulario, renderiza novamente a pagina com o resultado.

### 4.7 Conveccao natural

`processar_conveccao_natural` le geometria, fluido, temperatura do fluido e temperatura da superficie.

As geometrias tratadas sao:

- placa vertical;
- cilindro horizontal;
- esfera;
- placa horizontal.

Para placa horizontal, calcula o comprimento caracteristico:

$$
L_c = \frac{LW}{2(L+W)}
$$

Em seguida chama `calcular_coeficiente_convectivo('natural', geometria, parametros)`.

A versao JSON usa nomes equivalentes para os campos recebidos e devolve:

- tipo;
- geometria;
- Rayleigh;
- Nusselt;
- coeficiente convectivo;
- Prandtl;
- regime;
- comprimento caracteristico;
- propriedades;
- observacoes.

### 4.8 Conveccao forcada

`processar_conveccao_forcada` recebe:

- fluido;
- temperatura do fluido;
- temperatura da superficie;
- velocidade;
- geometria;
- dimensoes adicionais.

As geometrias sao mapeadas para:

- `placa` -> `placa_plana`;
- `cilindro` -> `cilindro_cruzado`;
- `tubo` -> `tubo_interno`.

A funcao chama o despachante de conveccao e renderiza o resultado.

A versao JSON devolve Reynolds, Nusselt, coeficiente convectivo, Prandtl, regime, propriedades e observacoes.

### 4.9 Condensacao

A rota `/calculadora_condensacao/calcular` recebe:

- geometria;
- fluido;
- temperatura de saturacao;
- temperatura de parede;
- comprimento ou diametro.

Chama `calcular_mudanca_fase('condensacao', geometria, parametros)` e envia o dicionario resultante para `calculadora_condensacao.html`.

### 4.10 Ebulicao

A rota `/calculadora_ebulicao/calcular` trata:

- ebulicao nucleada;
- ebulicao em filme.

Na modalidade nucleada, calcula um fluxo imposto a partir de:

$$
q'' = 50000(\Delta T)^2
$$

Na modalidade em filme, recebe a dimensao caracteristica e a orientacao.

O resultado e produzido por `calcular_mudanca_fase`.

### 4.11 Arranjos de tubos

A rota `/calculadora_arranjos_tubos` apresenta a interface. O POST coleta todos os parametros numericos e chama `calcular_arranjo_tubos('zukauskas', parametros)`.

### 4.12 Escoamento interno

A rota `/calculadora_escoamento_interno` recebe a geometria e escolhe entre:

- calculo tradicional;
- calculo com temperatura de entrada e saida.

As entradas de escoamento podem ser:

- velocidade `v`;
- fluxo massico `m_dot`;
- vazao volumetrica.

No modo tradicional chama `escoamento_interno_duto`.

No modo com temperaturas conhecidas chama `calcular_h_com_temperaturas`.

### 4.13 Circuito termico

`/circuito_termico`, `/circuito_termico_moderno` e `/laboratorio_termico` renderizam `circuito_termico_moderno.html`.

`/calcular_circuito_termico` recebe JSON e devolve uma confirmacao com os dados recebidos. O calculo principal do circuito ocorre no JavaScript do template.

### 4.14 APIs de temperatura

#### `/api/monitoramento`

No GET, devolve o `monitoring_cache`.

No POST, le as chaves presentes no JSON e converte cada valor para `float`. As chaves recebidas substituem os valores correspondentes no cache.

#### `/api/temperaturas`

Recebe JSON dos ESP32. Atualiza as temperaturas presentes no corpo da requisicao e devolve:

- status;
- mensagem;
- cache atual;
- timestamp recebido.

#### `/api/status`

Fornece o estado geral do servidor e as temperaturas armazenadas.

## 5. Modulo `modelo3.py`

`modelo3.py` e o nucleo de calculo de aletas.

As oito geometrias identificadas sao:

1. aleta retangular reta;
2. aleta triangular reta;
3. aleta parabolica reta;
4. aleta circular de perfil retangular;
5. aleta de perfil retangular;
6. aleta de perfil triangular;
7. aleta de perfil parabolico;
8. aleta de pino parabolico com ponta arredondada.

### 5.1 Funcoes de selecao e exibicao

`escolher_aletas` cria uma interface de selecao de geometrias.

`obter_imagem(tipo_aleta)` retorna o caminho da imagem da aleta.

`obter_formula(tipo_aleta)` retorna o caminho da imagem da formula.

`mostrar_formula(tipo_aleta)` apresenta a imagem da geometria e a imagem da formula.

`escolher_material` apresenta materiais e suas condutividades.

### 5.2 `calcular_taxa_calor_condicao`

A funcao calcula o fator associado a condicao de contorno da ponta.

Para ponta adiabatica:

$$
f = \tanh(mL)
$$

Para conveccao na ponta:

$$
f = \frac{\sinh(mL)+\frac{h}{mk}\cosh(mL)}{\cosh(mL)+\frac{h}{mk}\sinh(mL)}
$$

Para aleta infinita:

$$
f = 1
$$

Para temperatura especificada:

$$
\theta_L = T_L-T_{\infty}
$$

$$
f = \frac{\cosh(mL)-\theta_L/\theta_b}{\sinh(mL)}
$$

### 5.3 `calcular_eficiencia`

Recebe tipo de aleta, propriedades do material, dimensoes, temperaturas e condicao de ponta.

Primeiro calcula:

$$
\theta_b = T_b-T_{\infty}
$$

Para todas as geometrias, utiliza a forma geral:

$$
m = \sqrt{\frac{hP}{kA_{tr}}}
$$

$$
M = \sqrt{hPkA_{tr}}\,\theta_b
$$

$$
Q_{aleta}=M f
$$

A efetividade e:

$$
\varepsilon_a = \frac{Q_{aleta}}{hA_{tr}\theta_b}
$$

A funcao retorna normalmente:

```text
eta_aleta,
Q_aleta,
A_aleta,
epsilon_a,
m,
P,
A_tr,
dados_didaticos
```

### 5.4 Geometrias de aletas

#### Retangular reta

$$
P=2(w+t)
$$

$$
A_{tr}=wt
$$

A area superficial e associada a duas faces de largura `w` ao longo do comprimento.

#### Triangular reta

$$
P=w+2\sqrt{(w/2)^2+t^2}
$$

$$
A_{tr}=wt
$$

A eficiencia utiliza funcoes de Bessel modificadas:

$$
\eta = \frac{I_1(mL)}{mL I_0(mL)}
$$

#### Parabolica reta

$$
P=2(w+t)
$$

$$
A_{tr}=wt
$$

A area usa:

$$
C_1=\sqrt{1+(t/L)^2}
$$

$$
A_{aleta}=wL\left[C_1+\frac{L}{t}\ln\left(\frac{t}{L}+C_1\right)\right]
$$

#### Circular de perfil retangular

$$
P=2\pi r_2
$$

$$
A_{tr}=\pi(r_2^2-r_1^2)
$$

#### Perfil retangular

E tratado como um pino cilindrico de secao constante:

$$
P=\pi D
$$

$$
A_{tr}=\pi(D/2)^2
$$

#### Perfil triangular

Utiliza o pino cilindrico afilado e funcoes de Bessel modificadas.

#### Perfil parabolico

Utiliza um pino cilindrico com perfil variavel e fatores geometricos auxiliares.

#### Pino parabolico arredondado

A area e calculada pela expressao geometrica implementada no modulo. A eficiencia e obtida comparando o calor calculado com:

$$
Q_{max}=hA_{aleta}\theta_b
$$

### 5.5 Distribuicao de temperatura

As funcoes `T_aleta_*` calculam a temperatura ao longo da coordenada `x`.

A forma geral utilizada e:

$$
T(x)=T_{\infty}+(T_b-T_{\infty})
\frac{\cosh[m\,f(L-x)]}{\cosh[m\,fL]}
$$

As funcoes sao:

- `T_aleta_retangular`;
- `T_aleta_triangular`;
- `T_aleta_parabolica`;
- `T_aleta_circular`;
- `T_aleta_perfil_retangular`;
- `T_aleta_perfil_triangular`;
- `T_aleta_perfil_parabolico`;
- `T_aleta_pino_parabolico`.

`gerar_distribuicao_temperatura` cria uma figura estatica com Matplotlib.

`sgerar_distribuicao_temperatura` cria uma distribuicao para uma geometria comparando materiais.

### 5.6 Persistencia

`salvar_resultados` grava resultados de varias geometrias em arquivo texto.

`salvar_sresultados` grava resultados de varias combinacoes de materiais.

`gerar_dados_didaticos` organiza informacoes de resolucao passo a passo, como tipo original, tipo mapeado, metodo, condicao de ponta, etapas, calor, eficiencia e efetividade.

## 6. Modulo `conveccao_calculadora.py`

Este modulo contem propriedades de fluidos e calculos de conveccao natural e forcada.

### 6.1 `interpolar_propriedades`

Recebe o nome do fluido e a temperatura em Kelvin.

Retorna propriedades como:

- densidade `rho`;
- calor especifico `cp`;
- condutividade `k`;
- viscosidade dinamica `mu`;
- Prandtl `Pr`;
- viscosidade cinematica `nu`;
- difusividade termica `alpha`.

Os fluidos tratados incluem ar, agua, oleo e mercurio.

### 6.2 `calcular_velocidade_por_fluxo_massa`

Converte fluxo massico em velocidade media:

$$
v=\frac{\dot m}{\rho A}
$$

Tambem calcula area, perimetro, diametro hidraulico, fluxo massico por area e informacoes geometricas.

### 6.3 Conveccao forcada

Para placa plana:

$$
Re=\frac{\rho vL}{\mu}
$$

Em regime laminar:

$$
Nu=0.664Re^{1/2}Pr^{1/3}
$$

Em regime turbulento:

$$
Nu=0.037Re^{0.8}Pr^{1/3}
$$

O coeficiente e:

$$
h=\frac{Nu k}{L}
$$

Para cilindro em escoamento cruzado, utiliza correlacao de Hilpert:

$$
Nu=CRe^mPr^{1/3}
$$

Para tubo interno, utiliza classificacao por Reynolds, comprimento de entrada, Gnielinski, Dittus-Boelter e valores constantes de Nusselt para escoamento laminar desenvolvido.

### 6.4 Conveccao natural

O numero de Rayleigh e calculado por:

$$
Ra=\frac{g\beta\Delta T L^3}{\nu\alpha}
$$

Para placa vertical, usa a correlacao de Churchill-Chu.

Para placa horizontal, usa correlacoes de McAdams, diferenciando face quente superior e inferior.

Para esfera, utiliza Churchill-Chu para esfera.

Para cilindro horizontal, utiliza uma expressao de Churchill-Chu modificada.

`listar_correlacoes_disponiveis` retorna um dicionario textual com as correlacoes existentes.

`calcular_coeficiente_convectivo` seleciona a funcao correta com base no tipo e na geometria.

## 7. Modulo `mudanca_fase_calculadora.py`

Este modulo trata condensacao e ebullicao com propriedades de saturacao.

### 7.1 `obter_propriedades_saturacao`

Recebe fluido e temperatura. Consulta a tabela de propriedades e realiza:

- retorno direto para temperatura tabelada;
- interpolacao entre pontos;
- uso do limite inferior ou superior quando a temperatura esta fora dos pontos intermediarios.

As propriedades incluem densidades, viscosidade, condutividade, calor latente, tensao superficial e Prandtl.

### 7.2 Condensacao

Para placa vertical, usa Nusselt para filme:

$$
Nu=0.943\left[
\frac{g\rho_l(\rho_l-\rho_v)h_{fg}L^3}
{\mu_l k_l\Delta T}
\right]^{1/4}
$$

$$
h=\frac{Nu k_l}{L}
$$

Para tubo horizontal, utiliza expressao equivalente com diametro e constante diferente.

O regime do filme e classificado por `Re_filme`.

### 7.3 Ebulicao nucleada

A funcao `ebulicao_nucleada_rohsenow` utiliza propriedades do liquido, excesso de temperatura e constantes da superficie.

O fluxo calculado segue a estrutura:

$$
q''=(\mu_lh_{fg})
\left[\frac{g(\rho_l-\rho_v)}{\sigma}\right]^{1/2}
\left[\frac{c_p\Delta T}{C_{sf}h_{fg}Pr_l^n}\right]^3
$$

O coeficiente e:

$$
h=\frac{q''}{\Delta T}
$$

### 7.4 Ebulicao em filme

`ebulicao_filme_berenson` calcula propriedades aproximadas do vapor, comprimento capilar, calor latente modificado, Nusselt e coeficiente convectivo.

### 7.5 Despachante

`calcular_mudanca_fase` seleciona a funcao conforme `tipo` e `subtipo` e retorna o dicionario do calculo.

## 8. Modulo `arranjos_tubos_calculadora.py`

Calcula conveccao externa em bancos de tubos.

As configuracoes sao:

- `inline`: tubos alinhados;
- `staggered`: tubos alternados.

### 8.1 Correlacao de Zukauskas

A funcao seleciona constantes `C` e `n` conforme arranjo e Reynolds.

A velocidade maxima depende da geometria do banco. O Reynolds e:

$$
Re_D=\frac{\rho v_{max}D}{\mu}
$$

A correlacao geral e:

$$
Nu=CRe_D^nPr^{0.36}F_N
$$

O fator `F_N` representa o efeito do numero de fileiras.

### 8.2 Correlacao de Grimison

Utiliza uma forma simplificada:

$$
Nu=CRe^nPr^{1/3}
$$

### 8.3 `calcular_arranjo_tubos`

Seleciona Zukauskas ou Grimison conforme o tipo informado e retorna os resultados da correlacao escolhida.

## 9. Modulo `metricas_engenharia.py`

Complementa os resultados das aletas com grandezas fisicas e economicas.

### `calcular_volume_aleta`

Calcula volume segundo a geometria. Os resultados sao expressos em metros cubicos.

### `calcular_area_superficial`

Calcula a area superficial aproximada em metros quadrados.

### `calcular_metricas_engenharia`

Consulta `MATERIAIS_DB` e calcula:

$$
 massa=volume\,rho
$$

$$
 custo=massa\,custo_{kg}
$$

$$
 razao\ custo-beneficio=\frac{Q_{aleta}}{custo}
$$

O retorno contem volume, massa, custo, razao custo-beneficio e propriedades do material.

### `interpretar_metricas`

Organiza os dados em listas de pontos fortes, alertas e recomendacoes textuais conforme os valores calculados de massa e relacao custo-beneficio.

## 10. Modulos de configuracao e suporte

### `config_otimizada.py`

Define dataclasses para materiais, validacao, performance, interface, aletas e conveccao.

A classe `ConfiguracaoSistema` agrupa essas configuracoes, carrega `config.json`, salva configuracoes, localiza materiais, valida a configuracao e aplica perfis de performance.

### `melhorias_sistema.py`

Fornece validacao centralizada, cache, monitoramento de tempo, tratamento de erros, decoradores de cache, decoradores para arrays NumPy, propriedades de materiais e wrappers para calculos.

`PerformanceMonitor` armazena tempos em `tempos_execucao` e quantidade de chamadas em `contadores`.

## 11. Templates HTML

Os templates em `templates/` formam a camada visual.

- `index.html`: menu inicial.
- `tipos_aletas.html`: selecao de varias geometrias.
- `tipos_materiais.html`: selecao de material.
- `inserir_dados.html`: parametros para comparacao de geometrias.
- `resultado.html`: resultados de varias geometrias.
- `sele_aleta.html`: selecao de uma geometria.
- `sele_materiais.html`: selecao de varios materiais.
- `inserir_seledados.html`: entrada para comparacao de materiais.
- `resultados_sele.html`: resultados de combinacoes de materiais.
- `calculadora_convectivo.html`: menu convectivo.
- `calculadora_natural.html`: conveccao natural.
- `calculadora_forcada.html`: conveccao forcada.
- `calculadora_condensacao.html`: condensacao.
- `calculadora_ebulicao.html`: ebulicao.
- `calculadora_arranjos_tubos.html`: bancos de tubos.
- `calculadora_escoamento_interno.html`: tubos e dutos.
- `painel_status.html`: temperaturas e historico.
- `circuito_termico_moderno.html`: circuito virtual.

## 12. Circuito termico virtual

O circuito termico e modelado como uma rede de resistencias.

Para condu b)cao plana:

$$
R=\frac{L}{kA}
$$

Para conveccao:

$$
R=\frac{1}{hA}
$$

Para conducao cilindrica:

$$
R=\frac{\ln(r_2/r_1)}{2\pi kL}
$$

Resistencias em serie sao somadas:

$$
R_{total}=R_1+R_2+\cdots+R_n
$$

Resistencias em paralelo sao combinadas por:

$$
\frac{1}{R_{eq}}=\sum_i\frac{1}{R_i}
$$

O fluxo termico e obtido por:

$$
q=\frac{T_{in}-T_{out}}{R_{total}}
$$

O circuito aceita camadas solidas, fluidos, resistencias de contato, radiacao linearizada, aletas e blocos paralelos aninhados.

As funcoes JavaScript do template calculam resistencias, equivalentes, metricas, temperaturas, contribuicoes percentuais e relatorio final.

## 13. JavaScript do circuito e popovers

### `static/js/popover_content.js`

Cria campos HTML para propriedades de fluidos, solidos e superficies aletadas.

### `static/js/popover_avancado.js`

Controla popovers, edicao de propriedades, blocos paralelos, subcamadas, metricas e formulas.

### `static/js/side_popover_helper.js`

Cria uma janela lateral com esquema de parede plana ou cilindro. O painel pode ser reposicionado, arrastado, resetado e fechado.

### `new_function_content.js`

Monta o relatorio HTML do circuito termico com metricas globais, superficies aletadas, contribuicoes e tabela por camada.

## 14. Monitoramento de temperaturas

O monitoramento usa o cache global do Flask.

O fluxo e:

```text
ESP32 mede temperatura
        |
        v
Aplica validacao e offset
        |
        v
Envia JSON para /api/temperaturas
        |
        v
Flask atualiza monitoring_cache
        |
        v
Navegador consulta /api/monitoramento
        |
        v
Cartoes e graficos sao atualizados
```

`painel_status.html` mantem um historico local no navegador. Cada consulta adiciona horario e valores aos arrays de temperatura. O historico visual utiliza os pontos mais recentes.

As paginas de conveccao natural e forcada usam T4 como temperatura do fluido e a media de T1, T2 e T3 como temperatura da superficie quando o usuario importa os dados do monitoramento.

## 15. Firmware `esp32_painel_status.ino`

Este firmware utiliza:

- tres sensores DS18B20 no barramento OneWire;
- um sensor DHT11;
- Wi-Fi;
- HTTP;
- memoria `Preferences`.

Os DS18B20 sao identificados como T1, T2 e T3. O DHT11 e identificado como T4 ambiente.

O firmware localiza sensores pelos enderecos ROM, configura resolucao de 10 bits, realiza leituras, verifica valores invalidos e soma offsets individuais.

A leitura corrigida e:

$$
T_{corrigida}=T_{bruta}+offset
$$

A calibracao coleta varias amostras e calcula um novo offset a partir da temperatura de referencia.

Os valores sao enviados ao endpoint Flask configurado por `SERVER_HOST`, `SERVER_PORT` e `SERVER_PATH`.

## 16. Firmware `esp32_monitor_ambiente.ino`

Este firmware utiliza dois sensores DS18B20 no barramento OneWire.

Os canais sao identificados como:

- T5 baixo da placa;
- T6 baixo da placa.

Os indices `INDICE_T5` e `INDICE_T6` associam os sensores fisicos aos canais logicos.

O firmware realiza:

- conexao Wi-Fi;
- descoberta de sensores;
- leitura a cada intervalo definido;
- aplicacao de offset;
- validacao de leitura;
- contagem de falhas consecutivas;
- nova descoberta apos falhas sucessivas;
- envio HTTP periodico.

Cada envio pode conter somente os canais validos daquele ESP32, preservando no servidor os valores enviados pelo outro dispositivo.

## 17. Arquivos estaticos

### `static/aletas/`

Contem imagens das oito geometrias de aletas utilizadas nas selecoes e visualizacoes.

### `static/formulas/`

Contem imagens das formulas associadas as aletas e esquemas de parede plana e cilindro.

### `static/graficos/`

Diretorio destinado as imagens geradas para distribuicoes de temperatura.

### `static/css/popover.css`

Define estilos para botoes de salvar, cancelar, secundarios, perigosos e barras de acoes dos popovers.

### `static/selerelatorio.txt`

Arquivo textual utilizado para registrar resultados da comparacao entre materiais.

### `Resultados/resultados_aletas.txt`

Arquivo textual utilizado para registrar resultados do calculo de aletas.

## 18. Relacao integrada entre os componentes

A aplicacao conecta as partes da seguinte forma:

```text
index.html
    |
    +--> selecao de aletas
    |       |
    |       +--> modelo3.py
    |       +--> metricas_engenharia.py
    |       +--> visualizacao_plotly.py
    |       +--> resultado.html
    |
    +--> selecao de materiais
    |       |
    |       +--> modelo3.py para cada material
    |       +--> resultados_sele.html
    |
    +--> calculadoras convectivas
    |       |
    |       +--> conveccao_calculadora.py
    |       +--> mudanca_fase_calculadora.py
    |       +--> arranjos_tubos_calculadora.py
    |       +--> escoamento_dutos.py
    |       +--> templates especificos
    |
    +--> painel de status
    |       |
    |       +--> /api/monitoramento
    |       +--> Chart.js
    |
    +--> circuito termico virtual
            |
            +--> JavaScript do template
            +--> popovers
            +--> formulas de resistencia
            +--> relatorio HTML
```

## 19. Sequencia de execucao do sistema

1. O processo Python inicia `app.py`.
2. Flask registra as rotas e configura o ambiente.
3. O navegador acessa a pagina inicial.
4. O usuario escolhe um modulo.
5. O template apresenta os campos correspondentes.
6. Os dados sao enviados por formulario ou JSON.
7. `app.py` converte, organiza e encaminha os parametros.
8. O modulo especializado executa as formulas.
9. Os resultados sao armazenados em dicionarios, listas ou tuplas.
10. O backend chama metricas e geradores de graficos quando o fluxo utiliza aletas.
11. O template recebe os resultados e os apresenta.
12. Os relatorios textuais sao gravados quando o fluxo de aletas e executado.
13. Paralelamente, os ESP32 podem enviar temperaturas para as APIs.
14. As paginas de monitoramento consultam o cache e atualizam sua exibicao.

## 20. CONTEXTO COMPLETO DO PROJETO

O projeto V28.1 representa um laboratorio de transferencia de calor com componentes simulados e experimentais.

A camada Flask recebe requisicoes, apresenta paginas e integra os calculos. `modelo3.py` representa o nucleo de aletas. `conveccao_calculadora.py` representa o nucleo de propriedades de fluidos e conveccao. `mudanca_fase_calculadora.py` representa os calculos de condensacao e ebulicao. `arranjos_tubos_calculadora.py` representa bancos de tubos. `escoamento_interno.py` e `escoamento_dutos.py` representam escoamentos internos. `metricas_engenharia.py` transforma resultados de aletas em metricas fisicas e economicas. `visualizacao_plotly.py` transforma distribuicoes numericas em graficos.

Os templates HTML formam as telas de entrada, selecao, calculo, comparacao, monitoramento e circuito termico. Os scripts JavaScript acrescentam interacoes, atualizacoes assincronas, popovers, edicao de camadas e relatorios no navegador.

Os firmwares ESP32 representam a camada experimental. Eles leem sensores termicos, aplicam calibracao, enviam valores por HTTP e alimentam o cache de monitoramento do Flask.

Assim, o fluxo completo do projeto e:

```text
Parametros de engenharia, dados de sensores ou configuracao de circuito
        |
        v
Interface web, JSON ou firmware ESP32
        |
        v
Flask e seus despachantes
        |
        v
Correlacoes, propriedades, resistencias e calculos de aletas
        |
        v
Resultados termicos, metricas, graficos e relatorios
        |
        v
Paginas HTML, painel de temperaturas e laboratorio virtual
```

O sistema produz como saidas principais valores de coeficiente convectivo, Reynolds, Rayleigh, Nusselt, Prandtl, regime de escoamento, taxas de calor, eficiencia de aletas, efetividade, areas, volumes, massas, custos, resistencias termicas, fluxos termicos, distribuicoes de temperatura, historicos de sensores e relatorios tecnicos.
