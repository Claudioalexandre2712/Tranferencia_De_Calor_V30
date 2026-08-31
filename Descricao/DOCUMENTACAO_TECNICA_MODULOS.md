# Documentacao Tecnica dos Modulos de Calculo

## Escopo

Este documento descreve detalhadamente os modulos Python de calculo do projeto:

- modelo3.py
- conveccao_calculadora.py
- metricas_engenharia.py
- mudanca_fase_calculadora.py
- arranjos_tubos_calculadora.py
- escoamento_interno.py
- escoamento_dutos.py
- visualizacao_plotly.py
- config_otimizada.py
- melhorias_sistema.py

O foco desta documentacao e registrar responsabilidades, funcoes, variaveis globais relevantes, parametros, formulas implementadas, estruturas de retorno, fluxos de dados e relacoes entre os modulos.

## Visao Geral da Arquitetura

Os modulos se organizam em cinco camadas funcionais:

1. Nucleo de calculo de aletas: modelo3.py.
2. Nucleo de conveccao e escoamento: conveccao_calculadora.py, escoamento_interno.py e escoamento_dutos.py.
3. Nucleo de mudanca de fase e bancos de tubos: mudanca_fase_calculadora.py e arranjos_tubos_calculadora.py.
4. Pos-processamento e apresentacao: metricas_engenharia.py e visualizacao_plotly.py.
5. Infraestrutura de configuracao, validacao, cache e monitoramento: config_otimizada.py e melhorias_sistema.py.

Na aplicacao Flask, app.py consome principalmente:

- calcular_eficiencia, mostrar_formula, salvar_resultados e salvar_sresultados de modelo3.py.
- gerar_grafico_temperatura_interativo e gerar_grafico_temperatura_multiplos_materiais de visualizacao_plotly.py.
- calcular_metricas_engenharia, interpretar_metricas e MATERIAIS_DB de metricas_engenharia.py.
- calcular_mudanca_fase de mudanca_fase_calculadora.py.
- calcular_arranjo_tubos de arranjos_tubos_calculadora.py.
- escoamento_interno_tubo_circular de escoamento_interno.py.
- escoamento_interno_duto de escoamento_dutos.py.

## Fluxo de Dados Entre Modulos

### Fluxo de aletas

1. app.py coleta parametros geometricos, termicos e materiais.
2. app.py chama modelo3.calcular_eficiencia para cada geometria ou combinacao geometria-material.
3. modelo3.py calcula:
   - parametro m,
   - taxa de calor Q_aleta,
   - eficiencia da aleta eta_aleta,
   - efetividade epsilon_a,
   - grandezas geometricas auxiliares,
   - dados didaticos estruturados.
4. metricas_engenharia.py recebe os resultados termicos e calcula volume, massa, custo e razao custo-beneficio.
5. visualizacao_plotly.py usa as funcoes de temperatura de modelo3.py para gerar graficos HTML.
6. modelo3.py tambem grava saidas textuais por meio de salvar_resultados e salvar_sresultados.

### Fluxo de conveccao e escoamento

1. O usuario fornece geometria, temperaturas e velocidade ou vazao.
2. conveccao_calculadora.py calcula propriedades do fluido com interpolar_propriedades.
3. Se necessario, calcular_velocidade_por_fluxo_massa converte fluxo de massa em velocidade media.
4. Correlacoes especificas retornam h, Nu, Re, Pr, regime e metadados.
5. escoamento_interno.py especializa o caso de tubo circular.
6. escoamento_dutos.py generaliza para secoes circular, quadrada e retangular, incluindo casos com temperaturas de entrada e saida conhecidas.

### Fluxo de mudanca de fase e arranjos de tubos

1. app.py encaminha parametros para despachantes de alto nivel.
2. mudanca_fase_calculadora.py usa propriedades de saturacao e escolhe a correlacao de condensacao ou ebulicao.
3. arranjos_tubos_calculadora.py usa interpolar_propriedades de conveccao_calculadora.py para obter propriedades do fluido e calcula h para bancos de tubos.

### Fluxo de infraestrutura

1. config_otimizada.py centraliza materiais, limites fisicos e perfis de desempenho.
2. melhorias_sistema.py encapsula validacao, cache, logging, tratamento de erro e wrappers otimizados para calculos, sobretudo o de aletas.

---

## modelo3.py

### Papel do arquivo

Modulo principal de calculo de aletas. Reune:

- selecao de geometrias e materiais em interface desktop CustomTkinter;
- exibicao de imagens e formulas;
- calculo de desempenho termico para oito geometrias de aletas;
- geracao de distribuicoes de temperatura;
- exportacao de resultados em arquivos texto;
- geracao de dados didaticos passo a passo.

Apesar de conter rotinas de interface grafica desktop, a principal superficie reutilizada pela aplicacao web e o conjunto de funcoes de calculo e de distribuicao de temperatura.

### Variaveis globais relevantes

- ALETAS_SVARIAVEL_DISPONIVEL = False
  - Flag de configuracao de funcionalidade.
- modos globais do CustomTkinter:
  - ctk.set_appearance_mode("system")
  - ctk.set_default_color_theme("blue")

### Geometrias suportadas

As strings de tipo de aleta sao padronizadas e usadas ao longo do sistema:

1. 1)aletas retangulares retas
2. 2)aletas triangulares retas
3. 3)aletas parabolicas retas
4. 4)aletas circulares de perfil retangular
5. 5)aletas de perfil retangular
6. 6)aletas de perfil triangular
7. 7)aletas de perfil parabolico
8. 8)aletas de pino de perfilparabolico (ponta arredondada)

### Funcoes de interface e apoio visual

#### escolher_aletas()

Abre uma janela para selecao multipla das geometrias.

Retorno:

- lista de strings com os tipos de aleta escolhidos.

#### obter_imagem(tipo_aleta)

Mapeia tipo de aleta para o arquivo de imagem em static/aletas.

Retorno:

- caminho da imagem ou None.

#### obter_formula(tipo_aleta)

Mapeia tipo de aleta para o arquivo de formula em static/formulas.

Retorno:

- caminho da imagem da formula ou None.

#### mostrar_formula(tipo_aleta)

Abre uma janela com imagem da geometria e imagem da formula associada.

Retorno:

- tupla com referencias de imagem renderizadas: (img, formula_img).

#### escolher_material()

Exibe lista de materiais e suas condutividades.

Retorno:

- tupla (nome_material, k).

### Funcao-base de condicao de contorno

#### calcular_taxa_calor_condicao(m, l, h, k, theta_b, T_L, T_inf, condicao_ponta)

Calcula o fator adimensional usado na taxa de calor da aleta em funcao da condicao de contorno na ponta.

Parametros:

- m: parametro da aleta, em 1/m.
- l: comprimento da aleta, em m.
- h: coeficiente convectivo, em W/m2.K.
- k: condutividade termica, em W/m.K.
- theta_b: excesso de temperatura na base, dado por Tb - Tinf.
- T_L: temperatura na ponta quando a condicao for temperatura especificada.
- T_inf: temperatura do fluido ambiente.
- condicao_ponta: adiabatica, conveccao, infinita ou temp_especificada.

Formulas implementadas:

- Ponta adiabatica:
  - fator = tanh(mL)
- Conveccao na ponta:
  - fator = [sinh(mL) + h/(mk) cosh(mL)] / [cosh(mL) + h/(mk) sinh(mL)]
- Aleta infinita:
  - fator = 1
- Temperatura especificada na ponta:
  - theta_L = T_L - T_inf
  - fator = [cosh(mL) - theta_L/theta_b] / sinh(mL)

Retorno:

- fator adimensional que multiplica M = sqrt(hPkAtr) theta_b.

### Funcao principal de calculo

#### calcular_eficiencia(tipo_aleta, h, k, l, t=None, w=None, D=None, r1=None, r2=None, T_b=None, T_inf=None, condicao_ponta='adiabatica', T_L=None)

Funcao central do modulo. Calcula o desempenho termico da aleta para cada geometria.

Parametros comuns:

- tipo_aleta: string identificadora da geometria.
- h: coeficiente convectivo.
- k: condutividade termica do material.
- l: comprimento da aleta.
- t: espessura, quando aplicavel.
- w: largura, quando aplicavel.
- D: diametro, quando aplicavel.
- r1, r2: raios interno e externo, quando aplicavel.
- T_b: temperatura da base.
- T_inf: temperatura do meio.
- condicao_ponta: tipo de contorno na ponta.
- T_L: temperatura imposta na ponta, apenas para temp_especificada.

Grandezas calculadas em todas as geometrias:

- theta_b = T_b - T_inf
- P: perimetro molhado ou perimetro caracteristico
- A_tr: area transversal
- m = sqrt(hP / kA_tr)
- M = sqrt(hPkA_tr) theta_b
- fator_condicao = calcular_taxa_calor_condicao(...)
- Q_aleta = M fator_condicao
- epsilon_a = Q_aleta / (h A_tr theta_b), quando o denominador nao for zero
- dados_didaticos = gerar_dados_didaticos(...)

Retorno padrao:

- tupla com oito elementos:
  - eta_aleta
  - Q_aleta
  - A_aleta
  - epsilon_a
  - m
  - P
  - A_tr
  - dados_didaticos

#### Formulacoes por geometria

##### 1) Aletas retangulares retas

- P = 2 (w + t)
- A_tr = w t
- A_superficie usada na eficiencia = 2 w l
- eta_aleta:
  - adiabatica: tanh(mL)/(mL)
  - conveccao: fator_condicao/(mL)
  - infinita: 1/(mL)
  - temp_especificada: fator_condicao/(mL)

##### 2) Aletas triangulares retas

- P = w + 2 sqrt((w/2)^2 + t^2)
- A_tr = w t
- A_aleta = 2 w sqrt(l^2 + (t/2)^2)
- eta_aleta via funcoes de Bessel modificadas:
  - eta = I1(mL) / [mL I0(mL)]
- Ha tratamento de overflow com aproximacoes assintoticas.

##### 3) Aletas parabolicas retas

- P = 2 (w + t)
- A_tr = w t
- C1 = sqrt(1 + (t/l)^2)
- A_aleta = w l [C1 + (l/t) ln(t/l + C1)]
- eta_aleta aproximada:
  - eta = 2 / [mL (1 + mL)]

##### 4) Aletas circulares de perfil retangular

- P = 2 pi r2
- A_tr = pi (r2^2 - r1^2)
- A_aleta = 2 pi (r2^2 - r1^2)
- eta_aleta usa a mesma logica das retangulares de secao constante.

##### 5) Aletas de perfil retangular

Interpretadas como pinos cilindricos de secao constante.

- P = pi D
- A_tr = pi (D/2)^2
- A_aleta = pi D (l + D/4)
- eta_aleta usa a mesma logica de secao constante.

##### 6) Aletas de perfil triangular

Interpretadas como pinos cilindricos afilados.

- P = pi D
- A_tr = pi (D/2)^2
- A_aleta = (pi D / 2) sqrt(l^2 + (D/2)^2)
- eta_aleta aproximada com I1(mL) / [mL I0(mL)]

##### 7) Aletas de perfil parabolico

- P = pi D
- A_tr = pi (D/2)^2
- C3 = 1 + 2 (D/l)^2
- C4 = sqrt(1 + (D/l)^2)
- A_aleta = (pi l^3 / 8D) [C3 C4 - (l / 2D) ln(2D C4 / l + C3)]
- eta_aleta aproximada:
  - eta = 2 / [mL sqrt(1 + mL)]

##### 8) Aletas de pino de perfil parabolico (ponta arredondada)

- P = pi D
- A_tr = pi (D/2)^2
- A_aleta = (pi D^4 / 96 l^2) [ (16 (l/D)^2 + 1)^(3/2) - 1 ]
- Q_max = h A_aleta theta_b
- eta_aleta = Q_aleta / Q_max

### Funcoes de distribuicao de temperatura

#### gerar_distribuicao_temperatura(...)

Gera grafico estatico com Matplotlib para uma ou mais geometrias.

Retorno:

- caminho do arquivo PNG salvo em static/graficos/distribuicao_temperatura.png.

#### sgerar_distribuicao_temperatura(...)

Versao para uma geometria selecionada comparando materiais.

Retorno:

- caminho do arquivo PNG salvo em static/ com timestamp.

#### Funcoes T_aleta_*

As funcoes abaixo retornam arrays de temperatura ao longo da coordenada x:

- T_aleta_retangular
- T_aleta_triangular
- T_aleta_parabolica
- T_aleta_circular
- T_aleta_perfil_retangular
- T_aleta_perfil_triangular
- T_aleta_perfil_parabolico
- T_aleta_pino_parabolico

Estrutura comum:

- calculam um m local a partir de P e de uma area efetiva chamada A_aleta dentro da propria funcao;
- retornam:
  - T(x) = T_inf + (T_b - T_inf) cosh[m fator (L - x)] / cosh[m fator L]
- o fator varia conforme a geometria:
  - 1 para casos retangulares/circulares/pino parabolico arredondado;
  - sqrt(2) para triangulares;
  - sqrt(3) para parabolicas.

### Persistencia de resultados

#### salvar_resultados(filepath, tipos_aletas, h, k, l, t, w, D, r1, r2, T_b, T_inf, resultados)

Grava resultados de multiplas aletas em arquivo texto, incluindo pontos discretos de temperatura.

Observacoes:

- aceita dois formatos de tupla em resultados, um mais novo e outro legado;
- tambem cria ou sobrescreve Resultados/resultados_aletas.txt com um resumo bruto.

#### salvar_sresultados(filepath, sele_aleta, h, k, l, t, w, D, r1, r2, T_b, T_inf, resultados_sele)

Versao voltada a comparacao da mesma geometria em varios materiais.

### Dados didaticos

#### gerar_dados_didaticos(...)

Cria um objeto DadosDidaticos com atributos como:

- tipo_aleta_original
- tipo_aleta_mapeado
- metodo
- condicao_ponta
- passos_resolucao
- q_base
- eficiencia
- efetividade

O objetivo e encapsular a narrativa de resolucao passo a passo para exibicao ou estudo.

### Superficie publica declarada

__all__ expoe:

- calcular_eficiencia
- mostrar_formula
- gerar_distribuicao_temperatura
- salvar_resultados
- gerar_dados_didaticos

### Relacoes com outros modulos

- E consumido diretamente por app.py.
- E consumido por visualizacao_plotly.py para as funcoes T_aleta_*.
- E consumido por melhorias_sistema.py, que encapsula calcular_eficiencia em um wrapper otimizado.

---

## conveccao_calculadora.py

### Papel do arquivo

Modulo central de conveccao com propriedades de fluidos, conveccao forcada externa e interna, conveccao natural e um despachante unificado.

### Funcoes principais

#### calcular_velocidade_por_fluxo_massa(m_dot, geometria, fluido, T_filme_K, **kwargs)

Converte fluxo de massa em velocidade media e dados geometricos.

Relacao fundamental:

- v = m_dot / (rho A)

Geometrias implementadas:

- tubo_circular
- tubo_anular
- placas_paralelas
- placa_plana

Grandezas calculadas:

- A: area de secao transversal
- P: perimetro molhado
- Dh: diametro hidraulico
- v: velocidade media
- G: fluxo massico por area

Retorno:

- dicionario com:
  - v
  - A
  - G
  - Dh
  - P
  - m_dot
  - rho
  - geometria_info
  - validacao

#### interpolar_propriedades(fluido, T_kelvin)

Fornece propriedades termofisicas para:

- ar
- mercurio
- agua
- oleo

Retorno padrao por fluido:

- rho
- cp
- k
- mu
- Pr
- nu
- alpha

Modelos adotados:

- ar:
  - rho = 353/T
  - cp por polinomio em T Celsius
  - k por polinomio em T Celsius
  - mu por lei de Sutherland
  - Pr = mu cp / k
- agua:
  - interpolacao linear entre faixas tabeladas
- mercurio:
  - propriedades aproximadamente constantes
- oleo:
  - propriedades base em 20 C com ajuste simples na viscosidade

#### conveccao_forcada_placa_plana(L, v=None, T_s=20, T_inf=25, fluido='ar', m_dot=None, w=1.0)

Calcula h para escoamento forcado sobre placa plana.

Passos:

- T_filme = (T_s + T_inf)/2 + 273.15
- propriedades por interpolar_propriedades
- velocidade a partir de v ou m_dot
- Re = rho v L / mu

Correlacoes:

- laminar, Re < 5e5:
  - Nu = 0.664 Re^0.5 Pr^(1/3)
- turbulento:
  - Nu = 0.037 Re^0.8 Pr^(1/3)
- h = Nu k / L

Retorno:

- h, Nu, Re, Pr, regime, validacao, info_fluxo e opcionalmente v_calculada.

#### conveccao_forcada_cilindro_cruzado(D, v=None, T_s=20, T_inf=25, fluido='ar', m_dot=None, L=1.0)

Calcula h para cilindro em escoamento cruzado.

Correlacao base:

- Hilpert, com pares (C, m) por faixa de Re.
- depois aplica ajuste multiplicativo Nu = Nu x 1.245.

Relacoes:

- Re = rho v D / mu
- Nu = C Re^m Pr^(1/3)
- h = Nu k / D

Retorno:

- h, Nu, Re, Pr, regime, validacao, info_fluxo e opcional v_calculada.

#### conveccao_forcada_tubo_interno(D, v=None, T_s=60, T_inf=20, L=1.0, fluido='agua', condicao_termica='temperatura_constante', m_dot=None)

Calcula h para escoamento interno em tubo.

Etapas:

- define T_filme,
- calcula propriedades,
- aceita v direta ou m_dot,
- calcula Re e L/D,
- gera validacao automatica e avisos de engenharia.

Tratamento por regime:

- metais liquidos, Pr < 0.1:
  - turbulento: Nu = 4.8 + 0.0156 Re^0.85 Pr^0.93
  - laminar/transicao: Nu = 7.0 + 0.025 (Re Pr)^0.8
- laminar:
  - Ts constante: Nu = 3.66
  - fluxo constante: Nu = 4.36
  - com correcao de entrada quando L/D < 60
- transicao:
  - usa Gnielinski e emite aviso de evitar o regime
- turbulento:
  - Gnielinski quando 3000 < Re < 5e6 e 0.5 <= Pr <= 2000
  - Dittus-Boelter como fallback

Outras grandezas retornadas:

- fator de atrito f
- incerteza_percentual
- LD_ratio
- validacao
- avisos_engenharia

#### conveccao_natural_placa_vertical(L, T_s, T_inf, fluido='ar')

Usa Ra = g beta DeltaT L^3 / (nu alpha).

Para ar, fixa beta = 3.21e-4, conforme comentario de calibracao.

Correlacao base:

- Churchill-Chu para placa vertical:
  - Nu = [0.825 + 0.387 Ra^(1/6) / (1 + (0.492/Pr)^(9/16))^(8/27)]^2

O codigo aplica fator multiplicativo de calibracao:

- 1.57 para 8e7 <= Ra <= 1e8
- 1.20 nos demais casos laminares

Retorno:

- h, Nu, Ra, Pr e regime.

#### conveccao_natural_placa_horizontal(Lc, T_s, T_inf, orientacao='superior', fluido='ar')

Usa correlacoes de McAdams.

Para face quente superior:

- 10^4 <= Ra <= 10^7:
  - Nu = 0.54 Ra^(1/4)
- 10^7 < Ra <= 10^11:
  - Nu = 0.15 Ra^(1/3)

Para face quente inferior:

- Nu = 0.27 Ra^(1/4)

Retorno:

- h, Nu, Ra, Pr, regime, orientacao, Lc.

#### conveccao_natural_esfera(D, T_s, T_inf, fluido='ar')

Correlacao de Churchill e Chu para esfera:

- Nu = 2 + [0.589 Ra^(1/4)] / [1 + (0.469/Pr)^(9/16)]^(4/9), para Ra < 1e12
- acima disso usa relacao alternativa com 0.6 Ra^(1/4) Pr^(1/3)

Retorno:

- h, Nu, Ra, Pr e regime.

#### conveccao_natural_cilindro_horizontal(D, T_s, T_inf, fluido='ar')

Correlacao de Churchill e Chu corrigida:

- Nu = [0.60 + 0.387 Ra^(1/6) / (1 + (0.559/Pr)^(9/16))^(8/27)]^2

O valor de Nu e multiplicado por 1.57 como ajuste de calibracao.

Retorno:

- h, Nu, Ra, Pr e regime.

#### listar_correlacoes_disponiveis()

Retorna dicionario textual com correlacoes e capacidades implementadas.

#### calcular_coeficiente_convectivo(tipo, geometria, parametros)

Despachante unificado.

Entradas:

- tipo: natural ou forcada
- geometria: placa, placa_plana, cilindro, cilindro_cruzado, tubo_interno, placa_vertical, cilindro_horizontal, esfera, placa_horizontal
- parametros: dicionario com os campos requeridos por cada geometria

Saida:

- o mesmo dicionario retornado pela funcao especializada;
- em erro, retorna {'erro': [mensagens]}.

### Relacoes com outros modulos

- Fornece interpolar_propriedades para escoamento_interno.py, escoamento_dutos.py e arranjos_tubos_calculadora.py.
- Pode ser consumido diretamente pela camada web em calculos convectivos gerais.

---

## metricas_engenharia.py

### Papel do arquivo

Modulo de pos-processamento de aletas. Complementa os resultados termicos com metricas fisicas e economicas simplificadas.

### Variavel global relevante

#### MATERIAIS_DB

Banco simplificado de materiais com:

- k: condutividade termica
- rho: densidade
- custo: custo por kg
- T_max: temperatura maxima de operacao

Materiais cadastrados:

- Aluminio
- Cobre
- Aco Inoxidavel
- Ferro Fundido
- Bronze

### Funcoes

#### calcular_volume_aleta(tipo_aleta, l, t=None, w=None, D=None, r1=None, r2=None)

Calcula o volume da aleta conforme a geometria.

Modelos usados:

- retangular reta: V = l t w
- triangular reta: V = 0.5 l t w
- parabolica reta: V = (2/3) l t w
- circular perfil retangular: V = pi (r2^2 - r1^2) t
- pino perfil retangular: V = pi (D/2)^2 l
- pino triangular: V = (1/3) pi (D/2)^2 l
- pino parabolico: V = (1/2) pi (D/2)^2 l
- pino parabolico arredondado: cilindro + semiesfera

Retorno:

- volume em m3; retorna 0 quando parametros necessarios estao ausentes.

#### calcular_area_superficial(tipo_aleta, l, t=None, w=None, D=None, r1=None, r2=None)

Calcula a area superficial total por aproximacoes geometricas.

Retorno:

- area em m2; retorna 0 se faltarem parametros.

#### calcular_metricas_engenharia(tipo_aleta, h, k, l, t, w, D, r1, r2, T_b, T_inf, Q_aleta, A_aleta, eta_aleta, epsilon_a, material_nome='Aluminio')

Usa o banco MATERIAIS_DB para calcular:

- volume
- massa = volume rho
- custo_total = massa custo_kg
- razao_custo_beneficio = Q_aleta / custo_total
- material_properties

Retorno:

- dicionario com os campos acima.

Observacao:

- Os parametros h, k, T_b, T_inf, A_aleta, eta_aleta e epsilon_a sao recebidos mas, neste modulo, o calculo efetivo usa principalmente geometria, Q_aleta e material_nome.

#### interpretar_metricas(metricas)

Traduz as metricas em tres listas:

- recomendacoes
- alertas
- pontos_fortes

Criterios implementados:

- razao custo-beneficio > 10: excelente
- > 5: boa
- < 2: alerta e recomendacao
- massa < 0.1 kg: aleta leve
- massa > 5 kg: alerta estrutural

### Relacoes com outros modulos

- E chamado por app.py para complementar os resultados vindos de modelo3.py.

---

## mudanca_fase_calculadora.py

### Papel do arquivo

Modulo especializado em transferencia de calor com mudanca de fase, cobrindo condensacao em filme e ebulicao nucleada ou em filme.

### Variavel global relevante

#### PROPRIEDADES_SATURACAO

Base de dados de saturacao para:

- agua
- r134a
- amonia

Cada ponto tabelado inclui:

- P_sat
- rho_l
- rho_v
- h_fg
- mu_l
- k_l
- cp_l
- sigma
- Pr_l

### Funcoes

#### obter_propriedades_saturacao(fluido, temperatura)

Faz interpolacao linear das propriedades de saturacao em funcao da temperatura.

Comportamento:

- retorna ponto exato se existir;
- faz clamp para limites inferior ou superior se a temperatura estiver fora da base;
- interpola linearmente entre temperaturas adjacentes quando necessario.

Retorno:

- dicionario com as propriedades interpoladas.

#### condensacao_placa_vertical(L, T_sat, T_parede, fluido='agua')

Usa a forma de Nusselt para condensacao em filme em placa vertical.

Formula implementada:

- Nu = 0.943 [ g rho_l (rho_l - rho_v) h_fg L^3 / (mu_l k_l DeltaT) ]^(1/4)
- h = Nu k_l / L

Calcula tambem:

- Gamma = rho_l g L^3 / (3 mu_l)
- Re_filme = 4 Gamma / mu_l

Classificacao de regime:

- Re_filme < 30: filme laminar liso
- < 1800: filme laminar ondulado
- acima: filme turbulento

Retorno:

- h, Nu, Re_filme, regime, Delta_T, propriedades, q_fluxo.

#### condensacao_tubo_horizontal(D, T_sat, T_parede, fluido='agua')

Formula implementada:

- Nu = 0.729 [ g rho_l (rho_l - rho_v) h_fg D^3 / (mu_l k_l DeltaT) ]^(1/4)
- h = Nu k_l / D

Retorno:

- h, Nu, regime, Delta_T, propriedades, q_fluxo.

#### ebulicao_nucleada_rohsenow(q_flux, T_sat, T_parede, fluido='agua', superficie='comercial')

Implementa a correlacao de Rohsenow com constantes C_sf e n por fluido e superficie.

Estrutura da correlacao no codigo:

- termo1 = mu_l h_fg
- termo2 = [g (rho_l - rho_v) / sigma]^(1/2)
- termo3 = [cp_l DeltaT_excesso / (C_sf h_fg Pr_l^n)]^3
- q_calculado = termo1 termo2 termo3

O coeficiente retornado e:

- h = q_flux / DeltaT_excesso

Regimes classificados por excesso de temperatura:

- < 5 C: conveccao natural
- < 30 C: ebulicao nucleada
- < 120 C: transicao
- acima: ebulicao em filme

Retorno:

- h, Delta_T_excesso, q_flux, q_calculado_rohsenow, regime, C_sf, propriedades.

#### ebulicao_filme_berenson(T_parede, T_sat, fluido='agua')

Implementa correlacao de Berenson para ebulicao em filme em superficie horizontal.

Grandezas:

- Delta_T = T_parede - T_sat
- propriedades de vapor aproximadas a partir das do liquido:
  - mu_v = 0.1 mu_l
  - k_v = 0.1 k_l
  - cp_v = 0.5 cp_l
- h_fg_mod = h_fg + 0.4 cp_v DeltaT
- L_capilar = [ sigma / (g (rho_l - rho_v)) ]^(1/2)
- Nu = 0.425 [ g rho_v (rho_l - rho_v) h_fg_mod L_capilar^3 / (mu_v k_v DeltaT) ]^(1/4)
- h = Nu k_v / L_capilar

Retorno:

- h, Nu, regime, Delta_T, L_capilar, h_fg_modificado, propriedades.

#### calcular_mudanca_fase(tipo, subtipo, parametros)

Despachante principal.

Entradas:

- tipo: condensacao ou ebulicao
- subtipo:
  - placa_vertical
  - tubo_horizontal
  - nucleada
  - filme
- parametros: dicionario com as variaveis requeridas por cada caso

Saida:

- dicionario da funcao especializada;
- em erro, {'erro': [mensagem]}.

### Relacoes com outros modulos

- E consumido por app.py como modulo de mudanca de fase da interface web.

---

## arranjos_tubos_calculadora.py

### Papel do arquivo

Modulo para estimar coeficientes convectivos em bancos de tubos externos com duas correlacoes: Zukauskas e Grimison.

### Variavel global relevante

#### FATORES_FILEIRAS

Tabela de fatores de correcao F_N por numero de fileiras para arranjos:

- inline
- staggered

### Funcoes

#### obter_correlacao_zukauskas(arranjo, Re_D)

Retorna o par (C, n) conforme a faixa de Re_D e o arranjo.

Base funcional:

- inline:
  - Re < 100: 0.9, 0.4
  - Re < 1000: 0.52, 0.5
  - Re < 2e5: 0.27, 0.63
  - acima: 0.033, 0.8
- staggered:
  - Re < 500: 1.04, 0.4
  - Re < 1000: 0.71, 0.5
  - Re < 2e5: 0.35, 0.6
  - acima: 0.031, 0.8

#### obter_fator_fileiras(arranjo, N_fileiras)

Retorna F_N por consulta exata ou interpolacao linear na tabela global.

#### arranjo_tubos_zukauskas(D, S_T, S_L, v, T_s, T_inf, fluido='ar', arranjo='inline', N_fileiras=10)

Etapas:

- T_filme = (T_s + T_inf)/2 + 273.15
- propriedades do fluido via interpolar_propriedades
- calculo das razoes ST_D e SL_D
- calculo da velocidade maxima no banco:
  - inline: v_max = v S_T / (S_T - D)
  - staggered: usa espacamento diagonal quando aplicavel
- Re_max = rho v_max D / mu
- obtencao de C e n
- obtencao de F_N

Correlacao geral usada:

- Nu = C Re^n Pr^0.36 F_N

Ajustes do codigo:

- para staggered e 1000 <= Re < 2e5, inclui (S_T/S_L)^0.2
- para Re >= 2e5, usa Pr^0.4

Retorno:

- h, Nu, Re_max, velocidade_max, velocidade_entrada, ST_D, SL_D, ST_SL, C, n, fator_fileiras, arranjo, regime, correlacao, T_filme, propriedades.

#### arranjo_tubos_grimison(D, S_T, S_L, v, T_s, T_inf, fluido='ar', arranjo='inline')

Implementa uma forma simplificada:

- Nu = C Re^n Pr^(1/3)

Com C e n definidos pelo arranjo e pela faixa de Re.

Retorno:

- h, Nu, Re_max, velocidade_max, C, n, arranjo, regime, T_filme, propriedades.

#### calcular_arranjo_tubos(tipo_correlacao, parametros)

Despachante principal.

Entradas:

- tipo_correlacao: zukauskas ou grimison
- parametros: dicionario contendo D, S_T, S_L, v, T_s, T_inf, fluido, arranjo e opcional N_fileiras

Saida:

- dicionario da correlacao escolhida;
- em erro, {'erro': [mensagem]}.

### Relacoes com outros modulos

- Importa interpolar_propriedades de conveccao_calculadora.py localmente nas funcoes de correlacao.
- E consumido por app.py.

---

## escoamento_interno.py

### Papel do arquivo

Modulo especializado em escoamento interno de tubo circular, com avaliacao do regime e do desenvolvimento hidrodinamico e termico.

### Dependencia externa principal

- interpolar_propriedades de conveccao_calculadora.py.

### Funcao principal

#### escoamento_interno_tubo_circular(parametros)

Parametros esperados em parametros:

- D: diametro interno
- L: comprimento do tubo, opcional, padrao 1.0
- v ou m_dot
- T_s: temperatura da parede
- T_inf: temperatura do fluido de entrada
- fluido
- condicao_termica: Ts_constante ou qs_constante

Passos do calculo:

1. T_filme = (T_s + T_inf)/2
2. propriedades em T_filme_K = T_filme + 273.15
3. se houver m_dot, chama calcular_velocidade_por_fluxo_massa com geometria tubo_circular
4. Re = rho v D / mu
5. Pr = mu cp / k
6. classifica regime:
   - Re < 2300: laminar
   - 2300 <= Re < 4000: transicao
   - >= 4000: turbulento
7. calcula comprimentos de entrada:
   - laminar: 0.05 Re D e 0.05 Re Pr D
   - turbulento: 10D para ambos

Correlacoes implementadas:

- laminar desenvolvido:
  - Ts_constante: Nu = 3.66
  - qs_constante: Nu = 4.36
- laminar em entrada:
  - Ts_constante: Nu = 1.86 Gz^(1/3) quando Gz > 10
  - qs_constante: Nu = 2.0 + 0.6 Gz^(1/3) quando Gz > 10
  - Gz = Re Pr D / L
- turbulento:
  - Gnielinski quando em faixa de validade
  - Dittus-Boelter como backup
- transicao:
  - interpolacao linear entre valor laminar e turbulento de referencia

Retorno:

- h
- Nu
- Re
- Pr
- regime
- v
- f quando calculado
- correlacao
- condicao_termica
- desenvolvido_hidro
- desenvolvido_termo
- L_entrada_hidro em mm
- L_entrada_termo em mm
- info_desenvolvimento
- info_fluxo
- propriedades com rho, mu, k, cp, T_filme
- avisos

### Relacoes com outros modulos

- Reutiliza conveccao_calculadora.py para propriedades e eventualmente para conversao de m_dot em velocidade.
- E consumido por app.py.

---

## escoamento_dutos.py

### Papel do arquivo

Modulo mais geral de escoamento interno, cobrindo tubos circulares e dutos quadrados ou retangulares, alem de variantes com temperaturas de entrada e saida conhecidas.

### Dependencia externa principal

- interpolar_propriedades de conveccao_calculadora.py.

### Funcoes

#### calcular_diametro_hidraulico(geometria, **dimensoes)

Geometrias suportadas:

- circular
- quadrado
- retangular

Formulas:

- circular:
  - A = pi (D/2)^2
  - P = pi D
  - Dh = D
- quadrado:
  - A = a^2
  - P = 4a
  - Dh = a
- retangular:
  - A = ab
  - P = 2(a+b)
  - Dh = 2ab/(a+b)

Retorno:

- Dh, A, P e info.

#### escoamento_interno_duto(parametros)

Generaliza o calculo para diferentes secoes.

Entradas tipicas:

- geometria
- D ou a e b
- L
- v, m_dot ou vazao_volumetrica
- T_s
- T_inf
- fluido
- condicao_termica

Etapas principais:

- calcula Dh e A
- calcula propriedades em T_filme
- converte entrada de vazao para velocidade quando necessario
- Re = rho v Dh / mu
- usa Pr fornecido por interpolar_propriedades
- calcula comprimentos de entrada
- decide se usa correlacao de entrada para laminar

Correlacoes implementadas:

- laminar desenvolvido circular:
  - Ts_constante: Nu = 3.66
  - qs_constante: Nu = 4.36
- laminar desenvolvido nao circular:
  - quadrado Ts_constante: Nu = 2.98
  - quadrado qs_constante: Nu = 3.61
  - retangular: aproximacoes por razao de aspecto
- turbulento:
  - Dittus-Boelter como padrao
  - Gnielinski calculado para circular, embora o codigo mantenha Dittus-Boelter para compatibilidade
- transicao:
  - interpolacao entre Nu laminar e turbulento
- entrada laminar:
  - forma de Hausen ajustada empiricamente em uma faixa

Retorno:

- h, Nu, Re, Pr, regime, v, Dh, A, L_entrada_hidro, L_entrada_termo, desenvolvido_hidro, desenvolvido_termo, correlacao, condicao_termica, info_geometria, info_fluxo, info_desenvolvimento, avisos, propriedades.

#### calcular_escoamento_com_temperaturas(D, L, T_entrada, T_saida, fluido, vazao_volumetrica=None, v=None, m_dot=None)

Caso especifico para tubo circular com temperaturas de entrada e saida conhecidas.

Etapas:

- T_media = (T_entrada + T_saida)/2
- propriedades na temperatura media
- calcula velocidade a partir de vazao, m_dot ou v
- Re = v D / nu
- identifica regime
- usa correlacoes de entrada ou plenamente desenvolvido

Retorno:

- Reynolds
- Nusselt
- h
- regime
- velocidade
- fluxo_massico
- Prandtl
- temperatura_media
- entrada_ou_desenvolvido
- comprimento_entrada
- propriedades internas

#### calcular_h_com_temperaturas(parametros)

Versao mais completa para geometria circular, quadrada ou retangular com temperaturas de entrada e saida conhecidas.

Entradas em parametros:

- geometria
- dimensoes geometricas
- L
- T_entrada
- T_saida
- fluido
- vazao_volumetrica, v ou m_dot

Etapas adicionais:

- calcula area transversal, perimetro molhado e D_h
- avalia desenvolvimento hidro e termo
- estima Q_fluido = m_dot cp (T_saida - T_entrada)
- calcula A_superficie = P_molhado L

Retorno:

- h, Nu, Re, Pr, regime, correlacao, desenvolvido_hidro, desenvolvido_termo, L_entrada_hidro, L_entrada_termo, condicao_termica, v, vazao_volumetrica, T_entrada, T_saida, T_media, Q_fluido, A_superficie, propriedades, avisos, info_entrada, m_dot_calculado;
- ou {'erro': [mensagem]} em caso de falha.

#### teste_exemplo_8_5() e teste_exemplo_8_6()

Funcoes de validacao manual baseadas em exemplos do livro, imprimindo comparacoes numericas.

### Relacoes com outros modulos

- Compartilha fonte de propriedades com conveccao_calculadora.py.
- E consumido por app.py.

---

## visualizacao_plotly.py

### Papel do arquivo

Modulo de visualizacao interativa dos resultados de aletas. Produz HTML Plotly para incorporacao na interface web.

### Dependencias relevantes

- plotly.graph_objects, plotly.express, make_subplots
- numpy
- importa dinamicamente de modelo3.py as funcoes T_aleta_*

### Funcoes

#### gerar_grafico_temperatura_interativo(tipos_aletas, h, k, l, t=None, w=None, D=None, r1=None, r2=None, T_b=None, T_inf=None, condicao_ponta='adiabatica')

Para cada tipo de aleta:

- gera um vetor x com 100 pontos entre 0 e l;
- calcula T(x) via funcao T_aleta_* correspondente;
- adiciona serie em grafico Plotly.

Caracteristicas do grafico:

- eixo x em mm;
- duas linhas horizontais de referencia para T_inf e T_b;
- ajuste automatico da faixa do eixo y com base no minimo e maximo reais das curvas;
- retorno em HTML via fig.to_html(include_plotlyjs='cdn', div_id='grafico-temperatura').

#### gerar_graficos_comparativos(resultados, material=None)

Recebe lista de resultados de aletas e gera quatro subgraficos:

- barras de taxa de calor
- barras de efetividade
- barras de eficiencia percentual
- scatter de comparacao normalizada

Entrada esperada:

- resultados contendo pelo menos cinco elementos por item:
  - tipo_aleta, eta_aleta, Q_aleta, A_aleta, epsilon_a

Retorno:

- HTML Plotly com div_id graficos-comparativos.

#### salvar_grafico_interativo(fig, nome_arquivo='grafico_interativo.html')

Salva um objeto Figure do Plotly como HTML em static/downloads com timestamp.

Retorno:

- caminho do arquivo salvo.

#### gerar_grafico_temperatura_multiplos_materiais(tipos_aletas, materiais, h, k_list, l, t=None, w=None, D=None, r1=None, r2=None, T_b=None, T_inf=None, condicao_ponta='adiabatica')

Gera curvas T(x) para varias combinacoes de geometria e material.

Caracteristicas:

- cor identifica material;
- estilo de linha identifica geometria;
- eixo x em mm;
- retorno como HTML Plotly.

### Relacoes com outros modulos

- Depende diretamente das funcoes T_aleta_* de modelo3.py.
- E consumido por app.py.

---

## config_otimizada.py

### Papel do arquivo

Modulo de configuracao centralizada do sistema, com foco em materiais, limites de validacao, parametros de performance, interface e configuracoes especificas de aletas e conveccao.

### Estruturas de dados e classes

#### PropriedadesMaterial

Dataclass com:

- nome
- k
- rho
- cp
- k_min
- k_max
- temp_max
- custo_relativo

#### MATERIAIS_OTIMIZADOS

Banco estruturado com chaves normalizadas:

- aluminio
- cobre
- aco_inoxidavel
- ferro

#### LimitesValidacao

Dataclass com limites fisicos para:

- temperatura
- dimensoes
- coeficiente convectivo h
- condutividade termica k

#### ConfigPerformance

Dataclass com:

- cache_ttl_segundos
- cache_max_items
- cache_auto_cleanup
- precisao_numerica
- max_iteracoes
- tolerancia_convergencia
- usar_multiprocessing
- max_processos
- nivel_log
- salvar_logs
- arquivo_log
- monitor_performance
- salvar_metricas

#### ConfigInterface

Dataclass com:

- debug_mode
- port
- host
- auto_reload_templates
- cache_templates
- resolucao_grafico
- largura_grafico
- altura_grafico
- tema_grafico
- formats_export
- qualidade_export

#### ConfigAletas

Dataclass com:

- condicoes_disponiveis
- condicao_padrao
- razao_aspecto_max
- razao_aspecto_min
- pontos_distribuicao_temp
- usar_funcoes_bessel

#### ConfigConveccao

Dataclass com:

- fluidos_disponiveis
- fluido_padrao
- correlacao_padrao_natural
- correlacao_padrao_forcada
- re_min
- re_max
- pr_min
- pr_max

#### ConfiguracaoSistema

Classe agregadora das configuracoes anteriores.

Responsabilidades:

- inicializar as secoes materiais, validacao, performance, interface, aletas e conveccao;
- carregar configuracao de config.json, quando existir;
- salvar configuracao em JSON;
- obter material por nome normalizado;
- validar coerencia da propria configuracao;
- aplicar perfis predefinidos de performance.

### Variavel global relevante

#### config

Instancia global de ConfiguracaoSistema, usada como ponto unico de acesso.

### Funcoes utilitarias

#### obter_limites_material(nome_material)

Retorna (k_min, k_max) do material configurado ou limites genericos.

#### validar_parametro_fisico(valor, tipo, nome='')

Valida temperatura, dimensao ou coeficiente_h usando os limites da configuracao global.

Retorno:

- tupla (bool, lista_de_erros).

#### gerar_relatorio_configuracao()

Monta uma string textual com o estado atual da configuracao, incluindo performance, validacao fisica e interface.

### Relacoes com outros modulos

- E importado opcionalmente por melhorias_sistema.py para servir como backend de configuracao otimizada.

---

## melhorias_sistema.py

### Papel do arquivo

Modulo de infraestrutura e unificacao operacional. Ele adiciona:

- logging estruturado;
- cache com TTL;
- validacao centralizada;
- monitoramento de performance;
- tratamento consistente de erros;
- wrappers otimizados sobre calculos do sistema;
- relatorios e rotinas de teste/manutencao.

### Variaveis globais relevantes

- logger
- config: instancia local de ConfiguracaoSistema simplificada
- config_performance: aponta para config_otimizada.config quando a importacao funciona; caso contrario usa ConfigBasica
- cache_sistema
- cache_materiais
- monitor_performance

### Classes e estruturas

#### ConfiguracaoSistema

Dataclass simplificada de configuracao operacional com:

- cache_ttl
- max_cache_size
- tolerancia_erro
- validacao_rigorosa
- nivel_log
- salvar_logs
- precisao_numerica
- max_iteracoes

#### CacheInteligente

Implementa cache em memoria com TTL e estatisticas.

Metodos:

- get(key)
- set(key, value)
- clear()
- stats()

Retorno de stats:

- hits
- misses
- hit_rate
- items
- ttl

#### TipoValidacao

Enum com:

- TEMPERATURA
- DIMENSAO
- COEFICIENTE
- PROPRIEDADE

#### ResultadoValidacao

Dataclass com:

- valido
- erros
- avisos
- valor_corrigido opcional

#### ValidadorCentralizado

Metodos estaticos:

- validar_temperatura
- validar_dimensao
- validar_coeficiente_conveccao

Cada metodo retorna ResultadoValidacao.

#### PerformanceMonitor

Monitora tempo de execucao por operacao.

Recursos:

- medir_tempo(nome_operacao) como context manager
- relatorio_performance()

#### ErroCalculoTermico

Excecao customizada com:

- mensagem
- codigo_erro
- detalhes

#### TratadorErro

Fornece o decorador tratar_erro_calculo, que converte excecoes comuns em ErroCalculoTermico com codigos padronizados.

### Funcoes

#### validar_parametro_fisico(valor, tipo, nome='')

Versao basica local que apenas verifica positividade e retorna (bool, lista).

#### validar_entrada_aleta(h, k, T_b, T_inf, l, **kwargs)

Executa validacao robusta de entradas de aletas.

Valida:

- h
- k
- T_b
- T_inf
- diferenca de temperatura
- l
- dimensoes t, w, D, r1, r2, quando presentes

Retorno:

- tupla (bool, erros).

#### cache_resultado(ttl_seconds=300)

Decorador de cache por argumentos de funcao.

#### otimizar_array_numpy(func)

Decorador que converte listas posicionais em arrays NumPy.

#### _obter_propriedades_fallback(material)

Fornece propriedades simplificadas para materiais basicos ou um fallback generico.

#### calcular_propriedades_material_otimizado(material, temperatura=25.0)

Funcao decorada com cache_resultado e otimizar_array_numpy.

Fluxo:

- mede tempo com monitor_performance;
- busca no cache_materiais;
- se necessario, usa _obter_propriedades_fallback;
- armazena em cache.

Retorno:

- dicionario com k, rho e cp.

#### calcular_eficiencia_otimizado(tipo_aleta, h, k, l, **kwargs)

Wrapper sobre modelo3.calcular_eficiencia.

Fluxo:

1. valida entradas com validar_entrada_aleta;
2. monta chave de cache com tipo, temperaturas e demais kwargs;
3. consulta cache_sistema;
4. chama modelo3.calcular_eficiencia quando necessario;
5. converte a tupla do modulo base para um dicionario enriquecido.

Retorno:

- tupla (sucesso, resultado)

Formato quando sucesso e o retorno base e a tupla esperada:

- resultado = {
  - eta_aleta
  - Q_aleta
  - A_aleta
  - epsilon_a
  - m
  - P
  - A_tr
  - dados_didaticos
  - tempo_calculo
  - cache_usado
}

Formato de erro:

- False, {
  - erro
  - codigo
  - detalhes ou tipo_aleta
}

#### gerar_relatorio_completo()

Gera relatorio textual consolidando:

- estatisticas dos caches
- configuracao ativa
- melhorias ativas
- relatorio de performance
- recomendacoes baseadas no hit rate e no tamanho do cache

#### testar_sistema_completo()

Executa verificacoes internas de:

- cache de materiais
- validacao
- funcao otimizada de aletas
- monitor de performance

Retorno:

- bool.

#### guia_migracao_sistema()

Retorna texto orientando a substituir chamadas antigas por wrappers otimizados e utilitarios centralizados.

#### limpar_sistema()

Limpa caches e contadores.

#### status_sistema()

Retorna dicionario estruturado com:

- cache_sistema
- cache_materiais
- performance
- configuracao

### Relacoes com outros modulos

- Importa opcionalmente config_otimizada.config.
- Importa dinamicamente modelo3.calcular_eficiencia dentro de calcular_eficiencia_otimizado.
- Atua como camada transversal de infraestrutura, nao como motor fisico independente.

---

## Relacoes Cruzadas Entre Modulos

### Dependencias diretas mais importantes

- modelo3.py e a base termica das aletas.
- visualizacao_plotly.py depende das funcoes T_aleta_* de modelo3.py.
- melhorias_sistema.py depende de modelo3.py para o calculo de eficiencia otimizado.
- escoamento_interno.py depende de conveccao_calculadora.py para propriedades e velocidade via m_dot.
- escoamento_dutos.py depende de conveccao_calculadora.py para propriedades.
- arranjos_tubos_calculadora.py depende de conveccao_calculadora.py para propriedades.
- app.py orquestra todos esses modulos na interface web.

### Padroes de retorno adotados

- Aletas em modelo3.py: tuplas posicionais com ate oito campos.
- Conveccao, escoamento, mudanca de fase e arranjos de tubos: dicionarios nomeados.
- Wrappers de melhorias_sistema.py: tupla (sucesso, resultado), sendo resultado um dicionario enriquecido ou um erro estruturado.

### Padroes de entrada adotados

- Modulos de aletas usam parametros nomeados explicitos na assinatura.
- Modulos de escoamento e despachantes usam dicionarios parametros.
- Despachantes principais retornam {'erro': [mensagem]} quando a combinacao tipo/subtipo ou tipo/geometria nao e reconhecida.

---

## Resumo Funcional por Modulo

- modelo3.py: calculo detalhado de aletas, distribuicao de temperatura, exportacao e dados didaticos.
- conveccao_calculadora.py: propriedades de fluidos e correlacoes de conveccao natural e forcada.
- metricas_engenharia.py: metricas de massa, custo e interpretacao de resultados de aletas.
- mudanca_fase_calculadora.py: condensacao e ebulicao com propriedades de saturacao tabeladas.
- arranjos_tubos_calculadora.py: conveccao externa em bancos de tubos por Zukauskas e Grimison.
- escoamento_interno.py: tubo circular com avaliacao de desenvolvimento e escolha de correlacoes por regime.
- escoamento_dutos.py: generalizacao para diferentes secoes, incluindo casos com temperaturas de entrada e saida conhecidas.
- visualizacao_plotly.py: graficos HTML interativos derivados das distribuicoes de temperatura das aletas.
- config_otimizada.py: repositorio central de parametros de sistema, materiais e limites fisicos.
- melhorias_sistema.py: camada transversal de cache, validacao, monitoramento, tratamento de erro e wrappers otimizados.
