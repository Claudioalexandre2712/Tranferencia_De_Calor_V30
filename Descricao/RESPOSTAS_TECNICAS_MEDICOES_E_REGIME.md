# Respostas Tecnicas sobre Medicoes, Regime Permanente e Tratamento de Dados

Este documento responde, com base no codigo existente, as cinco questoes relacionadas ao regime permanente, propriedades do ar, velocidade do OneWire, efeito aleta dos sensores e tratamento do ruido metrologico.

A descricao abaixo distingue entre:

- comportamento efetivamente programado;
- valores temporais definidos no codigo;
- calculos que existem em outros modulos, mas nao sao aplicados a determinada finalidade;
- comportamentos que nao estao implementados.

## 1. Regime permanente e calculo de dT/dt

### Resposta direta

O codigo atual nao calcula matematicamente a variacao temporal da temperatura:

$$
\frac{dT}{dt}
$$

Tambem nao existe uma rotina que compare temperaturas de instantes diferentes para determinar se a placa atingiu regime permanente.

Nao existe, na API Flask nem nos firmwares ESP32, uma logica com:

- derivada temporal;
- janela de estabilizacao;
- tolerancia maxima em graus Celsius;
- contador de amostras estaveis;
- bloqueio dos calculos enquanto a temperatura varia;
- liberacao automatica dos calculos apos confirmacao de estabilidade.

### O que existe no Flask

O Flask possui o dicionario global `monitoring_cache`, que armazena os valores mais recentes de `t1` a `t6`.

Quando uma requisicao POST chega em `/api/monitoramento` ou `/api/temperaturas`, os valores recebidos substituem os valores anteriores no cache.

O servidor nao armazena uma serie temporal das temperaturas. Ele nao calcula, por exemplo:

$$
\frac{T(t_2)-T(t_1)}{t_2-t_1}
$$

O servidor tambem nao compara a ultima leitura com uma leitura anterior para avaliar a estabilidade.

As paginas HTML consultam o valor atual do cache e o exibem. O historico mantido por `painel_status.html` serve para visualizacao no navegador e nao e utilizado pelo backend para validar regime permanente.

### O que existe nos ESP32

Os firmwares controlam intervalos de leitura e envio, mas esses intervalos representam periodicidade operacional, nao uma janela de estabilizacao termica.

No `esp32_painel_status.ino`:

```text
INTERVALO_LEITURA = 1000 ms
INTERVALO_ENVIO = 2000 ms
```

No `esp32_monitor_ambiente.ino`:

```text
INTERVALO_LEITURA = 1000 ms
INTERVALO_ENVIO = 2000 ms
```

Esses valores determinam quando uma nova leitura e realizada e quando um novo payload e enviado. Eles nao determinam que a temperatura permaneceu constante durante um periodo especifico.

### Tolerancia de regime permanente

A tolerancia programada para regime permanente e:

```text
nenhuma
```

Nao existe valor em Â°C usado para travar ou liberar calculos.

O valor `MIN_AMOSTRAS_CALIBRACAO = 24` pertence exclusivamente ao procedimento de calibracao por banho de gelo. Ele indica a quantidade minima de amostras validas necessarias para salvar um offset de calibracao. Esse valor nao representa uma tolerancia de estabilidade da placa.

### Janela temporal de estabilidade

A janela temporal programada para confirmar regime permanente e:

```text
nenhuma
```

A rotina de calibracao coleta 30 amostras com aproximadamente 1 segundo entre amostras, mas essa coleta e usada para calcular offsets dos sensores. Ela nao verifica se a placa estabilizou e nao bloqueia os calculos termicos.

### Consequencia funcional no fluxo existente

As equacoes de conveccao, conducao, aletas e circuito termico podem ser executadas quando o usuario envia os dados. O codigo nao exige uma confirmacao anterior de regime permanente.

O sistema, portanto, utiliza as temperaturas fornecidas ou lidas no momento da consulta. A decisao de considerar essas temperaturas representativas de uma condicao estacionaria nao e automatizada por uma rotina de `dT/dt`.

## 2. Interpolacao das propriedades termofisicas do ar

### Resposta direta

Para o ar, a funcao `interpolar_propriedades(fluido, T_kelvin)` nao consulta uma tabela discreta nem executa interpolacao linear entre pontos de 300 K, 350 K ou outros pontos tabelados.

O codigo usa correlacoes continuas em funcao da temperatura.

O nome da funcao contem a palavra `interpolar`, mas o ramo especifico do ar calcula as propriedades por formulas.

### Conversao da temperatura

A funcao recebe `T_kelvin` e calcula:

$$
T_{C}=T_{K}-273.15
$$

Para o ar, a temperatura em Celsius e limitada ao intervalo de -50 Â°C a 1000 Â°C antes de ser usada nas correlacoes de `cp` e `k`.

A temperatura em Kelvin original continua sendo utilizada na densidade e na viscosidade.

### Densidade

A densidade do ar e calculada pela aproximacao:

$$
\rho=\frac{353}{T_K}
$$

O resultado e expresso em kg/mÂ³.

### Calor especifico

O calor especifico e calculado por um polinomio em Celsius:

$$
 c_p=1006+0.089T_C-3.6\times10^{-5}T_C^2
$$

O resultado e expresso em J/(kg K).

### Condutividade termica

A condutividade termica e calculada por outro polinomio:

$$
 k=0.02414+7.42\times10^{-5}T_C-1.73\times10^{-8}T_C^2
$$

O resultado e expresso em W/(m K).

### Viscosidade dinamica

A viscosidade dinamica usa a lei de Sutherland:

$$
\mu=\mu_{ref}
\left(\frac{T_K}{T_{ref}}\right)^{3/2}
\frac{T_{ref}+S}{T_K+S}
$$

Os valores definidos no codigo sao:

```text
T_ref = 273.15 K
mu_ref = 1.716e-5 Pa.s
S = 110.4 K
```

### Numero de Prandtl

O Prandtl e calculado a partir das propriedades obtidas:

$$
Pr=\frac{\mu c_p}{k}
$$

Portanto, o codigo nao extrai o Prandtl de uma tabela separada.

### Viscosidade cinematica

A viscosidade cinematica e derivada de viscosidade dinamica e densidade:

$$
\nu=\frac{\mu}{\rho}
$$

A unidade e mÂ²/s.

### Difusividade termica

A difusividade termica e calculada por:

$$
\alpha=\frac{k}{\rho c_p}
$$

A unidade e mÂ²/s.

### Temperatura de filme

Os calculos de conveccao normalmente produzem a temperatura de filme por:

$$
T_f=\frac{T_s+T_{\infty}}{2}
$$

Depois convertem o resultado para Kelvin e chamam `interpolar_propriedades`.

Se, por exemplo, a temperatura de filme for 305,4 K, o codigo aplica diretamente as formulas continuas acima. Nao procura o ponto mais proximo de uma tabela nem combina dois pontos discretos por interpolacao linear.

### Comparacao com a agua

O ramo da agua possui comportamento diferente. Para a agua, o codigo efetivamente faz interpolacao linear entre faixas tabeladas, por exemplo entre 15 Â°C e 20 Â°C ou entre 20 Â°C e 40 Â°C.

Para uma faixa generica, o fator e:

$$
 f=\frac{T-T_1}{T_2-T_1}
$$

E cada propriedade e calculada como:

$$
P=P_1+f(P_2-P_1)
$$

Essa interpolacao linear por pontos tabelados existe para agua. O ramo do ar, entretanto, usa formulas continuas de densidade, polinomios, Sutherland e relacoes derivadas.

## 3. Ciclo de leitura e velocidade do OneWire

### Resposta direta

O codigo define um intervalo nominal de leitura de 1 segundo e um intervalo nominal de envio de 2 segundos em ambos os ESP32.

```text
INTERVALO_LEITURA = 1000 ms
INTERVALO_ENVIO = 2000 ms
```

Existe ainda um `delay(50)` no final do `loop`, usado nos dois firmwares.

Esses sao os tempos explicitamente programados para o ciclo operacional. O tempo real de uma leitura pode ser maior porque inclui conversao dos sensores, comunicacao OneWire, impressao serial, reconexao Wi-Fi e requisicao HTTP.

### ESP32 da placa

O `esp32_painel_status.ino` possui tres DS18B20 no mesmo barramento OneWire.

A funcao `lerTemperaturas` executa:

1. ativa espera pela conversao com `setWaitForConversion(true)`;
2. chama `sensors.requestTemperatures()`;
3. le cada sensor disponivel pelo endereco salvo;
4. tenta uma nova leitura individual apos `delay(100)` quando a leitura e invalida;
5. le o DHT11;
6. armazena as leituras validas.

A conversao dos tres DS18B20 e solicitada em conjunto pelo barramento. A leitura posterior de cada endereco acessa os valores da conversao realizada.

A resolucao configurada e de 10 bits:

```text
sensors.setResolution(10)
```

O proprio codigo identifica essa resolucao como aproximadamente 0,25 Â°C. O intervalo de leitura do loop continua definido como 1000 ms.

### ESP32 dos sensores T5 e T6

O `esp32_monitor_ambiente.ino` possui dois DS18B20 no mesmo barramento OneWire.

A funcao `lerTemperaturas` executa:

1. verifica se algum sensor foi encontrado;
2. solicita conversao com `sensors.requestTemperatures()`;
3. le T5 pelo endereco associado;
4. le T6 pelo endereco associado;
5. aplica os offsets;
6. marca as leituras como validas ou invalidas;
7. imprime os valores.

A resolucao tambem e configurada para 10 bits.

### Tempo exato do ciclo

O codigo nao mede nem registra a duracao real de `lerTemperaturas` usando `millis()`, `micros()` ou um cronometro.

Assim, o tempo exato de execucao nao e produzido pelo programa. O que existe e o agendamento nominal:

```text
uma tentativa de leitura a cada 1000 ms;
uma tentativa de envio a cada 2000 ms;
```

A conversao do DS18B20 ocorre dentro de `requestTemperatures`. O tempo fisico da conversao depende da resolucao e da biblioteca DallasTemperature. Esse tempo nao e calculado pelo codigo como parte de um relatorio de sincronismo.

### Os cinco sensores sao lidos simultaneamente?

Os cinco sensores nao sao lidos por um unico ciclo OneWire.

Eles estao divididos entre dois dispositivos:

- ESP32 #01: T1, T2, T3 e T4;
- ESP32 #02: T5 e T6.

Cada ESP32 faz seu proprio ciclo de leitura e envio. Os ciclos nao possuem sincronizacao temporal entre si e nao ha timestamp comum de aquisicao entre os dois dispositivos.

O campo `timestamp` enviado no JSON e baseado em `millis()` de cada ESP32. Portanto, ele representa o contador local de cada dispositivo, e nao um relogio compartilhado.

### Tratamento da diferenca temporal entre sensores

Nao existe rotina que calcule:

$$
\Delta t_{sensores}=t_{ultimo}-t_{primeiro}
$$

Tambem nao existe interpolacao temporal, sincronizacao de leituras ou correcao do gradiente com base nessa diferenca.

O backend apenas recebe os valores disponiveis e atualiza as chaves correspondentes do cache.

Consequentemente, o codigo nao quantifica matematicamente uma eventual distorcao temporal do gradiente utilizado posteriormente pelo usuario.

## 4. Formulacao do efeito aleta dos sensores

### Resposta direta

Nao existe, no codigo de leitura dos ESP32 ou na API Flask, uma formulacao termica que modele os fios, o encapsulamento ou o sensor DS18B20 como aletas intrusas.

Nao ha calculo de:

- resistencia condutiva do fio do sensor;
- area superficial do encapsulamento;
- coeficiente convectivo do fio;
- perda de calor do sensor para o ar;
- temperatura efetiva de contato;
- erro termico causado pela haste ou pelos fios;
- correcao da temperatura medida usando um modelo de aleta.

### O que o firmware faz com o sensor

O firmware le o valor fornecido pelo sensor, verifica se ele esta dentro da faixa aceita e soma um offset de calibracao:

$$
T_{corrigida}=T_{bruta}+OFFSET
$$

Esse offset representa uma correcao fixa de calibracao. Ele nao representa um modelo fisico de conducao pelo fio ou dissipacao convectiva do encapsulamento.

### Resistencias de contato

Existe um campo chamado `contact_resistance` no circuito termico virtual, implementado no JavaScript do laboratorio.

Esse campo permite representar uma resistencia de contato entre camadas do circuito:

$$
R_{total}=R_{conducao}+R_{contato}
$$

Entretanto, essa resistencia pertence a uma camada configurada pelo usuario no circuito termico virtual. Ela nao e automaticamente associada aos sensores DS18B20, aos fios de cobre ou ao encapsulamento.

A API de temperaturas nao recebe resistencia de contato e nao modifica os valores de T1 a T6 com base nessa grandeza.

### Efeito aleta nas calculadoras de aletas

`modelo3.py` possui formulacoes para aletas geometricas definidas pelo usuario, como aletas retangulares, triangulares, parabolicas, circulares e pinos.

Essas formulacoes pertencem ao objeto termico que o usuario esta simulando. Elas nao sao aplicadas automaticamente ao conjunto sensor-fio-encapsulamento.

### Fluxo real da temperatura medida

```text
Sensor DS18B20 ou DHT11
        |
        v
Leitura bruta
        |
        v
Teste de validade
        |
        v
Soma de offset de calibracao
        |
        v
Temperatura armazenada
        |
        v
JSON enviado ao Flask
```

Nao existe uma etapa de correcao por resistencia de aleta ou resistencia de contato do sensor.

## 5. Ruido metrologico e dados usados na Lei de Fourier

### Resposta direta

O codigo nao aplica media movel, filtro passa-baixa, filtro de Kalman, media exponencial, regressao temporal ou propagacao de incerteza antes de disponibilizar as temperaturas no dashboard.

As leituras validas sao armazenadas e enviadas com o valor corrigido pelo offset.

### Validacao das leituras no ESP32 da placa

A funcao `leituraValida` do `esp32_painel_status.ino` aceita uma temperatura quando:

```text
temperatura != DEVICE_DISCONNECTED_C
temperatura != 85.0
-55.0 < temperatura < 150.0
```

Se uma leitura falha, o firmware marca `leiturasValidas[i]` como falsa e incrementa o contador de erros. O ultimo valor numerico permanece armazenado na variavel, mas a flag indica que a leitura atual nao e valida.

O DHT11 usa uma faixa de validade diferente:

```text
nao NaN
-40.0 < temperatura < 80.0
```

### Validacao no ESP32 T5/T6

O firmware `esp32_monitor_ambiente.ino` verifica:

```text
valor diferente de DEVICE_DISCONNECTED_C;
valor diferente de 85.0;
valor maior que -55.0.
```

Quando a leitura e valida, o offset e somado. Quando e invalida, o canal e marcado como invalido.

Apos cinco falhas consecutivas, o sensor e desabilitado e o firmware forca uma nova descoberta do barramento.

### Calibracao por media

Existe uma media aritmetica no procedimento de calibracao por banho de gelo.

Para cada sensor, o firmware acumula leituras validas:

$$
S=\sum_{i=1}^{N}T_i
$$

Depois calcula:

$$
T_{medio}=\frac{S}{N}
$$

E define o offset:

$$
OFFSET=T_{referencia}-T_{medio}
$$

No firmware da placa:

```text
NUM_AMOSTRAS_CALIBRACAO = 30
MIN_AMOSTRAS_CALIBRACAO = 24
```

No firmware de T5/T6, os mesmos valores sao usados.

Essa media e realizada somente durante a calibracao. Ela nao e aplicada continuamente as leituras normais e nao funciona como filtro de ruido do dashboard.

### O dashboard aplica filtro?

`painel_status.html` mantem um historico no navegador, adicionando periodicamente os valores recebidos pela API.

Esse historico:

- registra horarios;
- armazena series para T1, T2, T3, T4 e T5 ou T6 conforme a tela;
- limita a quantidade de pontos mantidos;
- alimenta o grafico Chart.js.

O historico nao altera os valores por media e nao calcula uma temperatura filtrada.

As funcoes de atualizacao fazem conversao para numero e formatacao visual, por exemplo com `toFixed(1)`, mas essa formatacao nao e filtragem metrologica.

### Lei de Fourier

Nos arquivos analisados, nao existe uma rotina que receba diretamente as temperaturas T1 a T6 e aplique a Lei de Fourier para calcular automaticamente um fluxo condutivo experimental com tratamento estatistico.

Tambem nao existe um mecanismo que:

- estime a incerteza do gradiente;
- calcule a incerteza de `q_cond`;
- descarte automaticamente gradientes pequenos;
- limite automaticamente o valor de `h` obtido experimentalmente;
- combine varias leituras em uma regressao de temperatura;
- propague a incerteza de cada sensor para o resultado.

As calculadoras recebem temperaturas como entradas numericas e executam os modelos correspondentes. A origem desses valores pode ser manual ou importada do monitoramento, mas o fluxo de importacao nao aplica filtro estatistico.

### Funcao algoritimica existente do dashboard

A parte experimental do dashboard tem as seguintes funcoes efetivamente implementadas:

1. receber leituras dos ESP32;
2. armazenar os ultimos valores no cache Flask;
3. disponibilizar os valores por API;
4. atualizar cartoes de temperatura;
5. construir historico visual local;
6. permitir importacao de temperaturas para calculadoras de conveccao;
7. exibir estado de disponibilidade e validade conforme os dados recebidos.

Ela nao possui uma etapa automatica de confirmacao de regime permanente, correcao do efeito aleta dos sensores ou tratamento estatistico continuo para a Lei de Fourier.

## 6. Resumo objetivo das cinco respostas

| Questao | Comportamento existente no codigo |
|---|---|
| Regime permanente | Nao ha calculo de `dT/dt`, janela de estabilidade ou tolerancia em Â°C. |
| Propriedades do ar | Usa formulas continuas: densidade idealizada, polinomios para `cp` e `k`, Sutherland para `mu`; `nu`, `Pr` e `alpha` sao derivados. |
| OneWire | Leitura nominal a cada 1000 ms e envio nominal a cada 2000 ms; dois ESP32 operam independentemente. |
| Efeito aleta dos sensores | Nao ha modelo de fio, encapsulamento, perda parasita ou resistencia de contato vinculada aos sensores. |
| Ruido metrologico | Ha validacao de faixa e calibracao por media; nao ha filtro temporal, media movel ou propagacao de incerteza no dashboard. |

## 7. Fluxo real dos dados experimentais

```text
DS18B20 ou DHT11
        |
        v
Conversao pelo sensor
        |
        v
Leitura no ESP32
        |
        v
Teste de valores invalidos
        |
        v
Aplicacao de offset fixo
        |
        v
Armazenamento no firmware
        |
        v
POST JSON para /api/temperaturas
        |
        v
Atualizacao parcial de monitoring_cache
        |
        v
GET /api/monitoramento
        |
        v
Cartoes, historico e importacao para calculadoras
```

Em nenhum ponto desse fluxo aparece uma etapa de calculo de regime permanente, sincronizacao entre os dois ESP32, modelagem de aleta intrusa ou filtragem temporal continua.
