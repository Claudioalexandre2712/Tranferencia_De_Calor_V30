import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import os
import datetime
import json

def validar_consistencia_dados(x_m, x_mm, curvas, l):
    """
    Validação automática rigorosa dos dados antes de renderizar o gráfico e exportar CSV (Item 8):
    1. Todas as posições devem ser numéricas e finitas.
    2. Todas as temperaturas devem ser numéricas e finitas.
    3. As posições devem estar em ordem estritamente crescente.
    4. Não pode haver posições negativas.
    5. A posição final deve corresponder ao comprimento real da aleta (l).
    6. O tamanho dos arrays de todas as curvas deve ser rigorosamente idêntico a len(x_m).
    7. A conversão entre metro e milímetro deve ser consistente: L_mm ≈ L_m * 1000.
    """
    l_float = float(l)
    assert len(x_m) > 0, "Array de posições não pode estar vazio"
    assert len(x_m) == len(x_mm), f"Dimensões inconsistentes: {len(x_m)} posições em m vs {len(x_mm)} em mm"

    # 1, 4 e 7. Validação de posições e equivalência de unidades
    for i, (val_m, val_mm) in enumerate(zip(x_m, x_mm)):
        assert np.isfinite(val_m) and val_m >= -1e-12, f"Posição x_m inválida no índice {i}: {val_m}"
        assert np.isfinite(val_mm) and val_mm >= -1e-9, f"Posição x_mm inválida no índice {i}: {val_mm}"
        # L_mm = L_m * 1000 rigoroso
        assert abs(val_mm - (val_m * 1000.0)) < 1e-4, f"Inconsistência metro/milímetro no índice {i}: {val_m} m vs {val_mm} mm"

    # 3. Ordem estritamente crescente
    for i in range(len(x_m) - 1):
        assert x_m[i] < x_m[i+1], f"Posições não estão em ordem estritamente crescente: x[{i}]={x_m[i]} >= x[{i+1}]={x_m[i+1]}"

    # 5. Posição inicial zero e final l
    assert abs(x_m[0] - 0.0) < 1e-9, f"Posição inicial deve ser 0 m, obtido {x_m[0]}"
    assert abs(x_m[-1] - l_float) < 1e-6, f"Posição final {x_m[-1]} difere do comprimento real da aleta {l_float}"

    # 2 e 6. Validação das curvas de temperatura
    assert len(curvas) > 0, "Deve existir ao menos uma curva de temperatura"
    for c in curvas:
        temps = c['temperaturas']
        assert len(temps) == len(x_m), f"Tamanho da curva '{c['nome']}' ({len(temps)}) difere do eixo X ({len(x_m)})"
        for t_idx, t_val in enumerate(temps):
            assert np.isfinite(t_val), f"Temperatura não-finita na curva '{c['nome']}' no índice {t_idx}: {t_val}"


def construir_dados_distribuicao_temperatura(tipos_aletas, materiais=None, k_list=None, l=0.05, h=25.0, t=None, w=None, D=None, r1=None, r2=None, T_b=100.0, T_inf=25.0, condicao_ponta='adiabatica', n_pontos=201):
    """
    Fonte Única da Verdade para o Gráfico Plotly e para o arquivo CSV.
    Gera o vetor x em METROS e calcula as temperaturas reais analíticas de cada curva.
    """
    from modelo3 import calcular_Tx_para_tipo
    from tipos_aletas_config import obter_tipo_aleta

    if T_b is None: T_b = 100.0
    if T_inf is None: T_inf = 25.0
    if h is None or h <= 0: h = 25.0
    if l is None or l <= 0: l = 0.05
    l = float(l)

    # 1. EIXO X ÚNICO EM METROS (0 até l, com 201 pontos calculados)
    x_m = np.linspace(0.0, l, n_pontos)
    # 2. POSIÇÃO EM MILÍMETROS MATEMATICAMENTE EXATA (L_mm = L_m * 1000)
    x_mm = x_m * 1000.0

    nomes_bonitos = {
        1: "Aleta Retangular Reta",
        2: "Aleta Triangular Reta",
        3: "Aleta Parabólica Reta",
        4: "Aleta Circular Retangular",
        5: "Aleta de Pino Retangular",
        6: "Aleta de Pino Triangular",
        7: "Aleta de Pino Parabólica",
        8: "Aleta de Pino Parabólica (Ponta Arredondada)"
    }

    curvas = []

    # Cenário A: Comparação de Múltiplos Materiais (/resultados_sele)
    if materiais is not None and isinstance(materiais, (list, tuple)) and len(materiais) > 0:
        if k_list is None:
            k_list = [222.0] * len(materiais)
        elif not isinstance(k_list, (list, tuple)):
            k_list = [k_list]

        # Ordem obrigatória: Cobre primeiro, Alumínio depois (não inverter)
        pares = list(zip(materiais, k_list))
        def prioridade_material(item):
            m_str = str(item[0]).strip().lower()
            if 'cobre' in m_str: return 0
            if 'alum' in m_str: return 1
            return 2
        pares.sort(key=prioridade_material)
        materiais_ord = [p[0] for p in pares]
        k_list_ord = [p[1] for p in pares]

        for i, tipo_aleta in enumerate(tipos_aletas):
            tid = obter_tipo_aleta(tipo_aleta) or (i + 1)
            nome_aleta = nomes_bonitos.get(tid, f"Aleta {tid}")
            for j, (mat, k_val) in enumerate(zip(materiais_ord, k_list_ord)):
                try:
                    k_float = float(k_val) if k_val is not None else 222.0
                    T_x = calcular_Tx_para_tipo(tid, x_m, l, T_b, T_inf, h, k_float, t, w, D, r1, r2)
                    # Quando há apenas 1 aleta e múltiplos materiais (ex: Cobre e Alumínio),
                    # o nome da curva é exatamente o nome do material
                    if len(tipos_aletas) == 1:
                        nome_curva = str(mat)
                    else:
                        nome_curva = f"{nome_aleta} ({mat})"
                    curvas.append({
                        "nome": nome_curva,
                        "temperaturas": [round(float(val), 4) for val in T_x]
                    })
                except Exception as e:
                    print(f"Erro no cálculo de T_x para {tipo_aleta} com {mat}: {e}")
                    continue
    else:
        # Cenário B: Comparação entre Geometrias de Aletas (/resultado)
        if isinstance(k_list, (list, tuple)) and len(k_list) > 0:
            k_val = float(k_list[0])
        else:
            k_val = float(k_list if k_list is not None else 222.0)

        for i, tipo_aleta in enumerate(tipos_aletas):
            try:
                tid = obter_tipo_aleta(tipo_aleta) or (i + 1)
                nome = nomes_bonitos.get(tid, f"Aleta {tid}")
                T_x = calcular_Tx_para_tipo(tid, x_m, l, T_b, T_inf, h, k_val, t, w, D, r1, r2)
                curvas.append({
                    "nome": nome,
                    "temperaturas": [round(float(val), 4) for val in T_x]
                })
            except Exception as e:
                print(f"Erro ao calcular temperatura para {tipo_aleta}: {e}")
                continue

    # 3. VALIDAÇÃO AUTOMÁTICA (ITEM 8)
    validar_consistencia_dados(x_m, x_mm, curvas, l)

    # Posicao_x_m representa diretamente L (m)
    dados_base = {
        "Posicao_x_m": [round(float(val), 6) for val in x_m],
        "x_m": [round(float(val), 6) for val in x_m],
        "curvas": curvas,
        "l_m": l,
        "n_pontos": len(x_m),
        "titulo": "Distribuição de Temperatura ao Longo da Aleta",
        "eixo_x_label": "Posição ao longo da aleta (m)",
        "eixo_y_label": "Temperatura (°C)"
    }
    return dados_base


def criar_figura_plotly_temperatura(dados_base, T_b=100.0, T_inf=25.0):
    """
    Constrói a figura interativa Plotly utilizando rigorosamente os dados da base única (Item 3).
    Eixo X: METROS ('Posição ao longo da aleta (m)').
    Eixo Y: 'Temperatura (°C)'.
    """
    fig = go.Figure()
    cores = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B', '#2B50AA', '#FF6B6B', '#4ECDC4']
    
    todas_temperaturas = []
    x_m = dados_base['x_m']

    for i, curva in enumerate(dados_base['curvas']):
        temps = curva['temperaturas']
        todas_temperaturas.extend(temps)
        fig.add_trace(go.Scatter(
            x=x_m,  # Posição ao longo da aleta em METROS (ex: 0 a 0.5 m)
            y=temps,
            mode='lines',
            name=curva['nome'],
            line=dict(color=cores[i % len(cores)], width=2.5),
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Posição: %{x:.4f} m<br>' +
                         'Temperatura: %{y:.2f} °C<extra></extra>'
        ))

    if todas_temperaturas:
        temp_min_real = min(todas_temperaturas)
        temp_max_real = max(todas_temperaturas)
        delta_temp = temp_max_real - temp_min_real
        margem = max(delta_temp * 0.1, 2.0)
        y_min = temp_min_real - margem
        y_max = temp_max_real + margem
    else:
        y_min = None
        y_max = None

    fig.update_layout(
        title={
            'text': dados_base['titulo'],
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#1976d2'}
        },
        xaxis_title=dados_base['eixo_x_label'],
        yaxis_title=dados_base['eixo_y_label'],
        xaxis=dict(
            title=dados_base['eixo_x_label'],
            gridcolor='rgba(128,128,128,0.3)',
            gridwidth=1,
            title_font=dict(size=14, color='#34495e'),
            zeroline=False
        ),
        yaxis=dict(
            title=dados_base['eixo_y_label'],
            gridcolor='rgba(128,128,128,0.2)',
            gridwidth=1,
            title_font=dict(size=14, color='#34495e'),
            range=[y_min, y_max] if (y_min is not None and y_max is not None) else None,
            showgrid=True,
            zeroline=False
        ),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(128,128,128,0.5)",
            borderwidth=1
        ),
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=60, r=150, b=60, l=60),
        height=500
    )

    if T_inf is not None:
        fig.add_hline(
            y=T_inf, 
            line_dash="dot", 
            line_color="#666",
            annotation_text=f"T∞ = {T_inf}°C",
            annotation_position="bottom right"
        )
    if T_b is not None:
        fig.add_hline(
            y=T_b, 
            line_dash="dot", 
            line_color="#666",
            annotation_text=f"Tb = {T_b}°C",
            annotation_position="top right"
        )

    return fig


def gerar_grafico_temperatura_interativo(tipos_aletas, h, k, l, t=None, w=None, D=None, r1=None, r2=None, T_b=None, T_inf=None, condicao_ponta='adiabatica', material=None, n_pontos=201):
    """
    Gera o gráfico interativo de temperatura ao longo da aleta e retorna a tupla:
    (grafico_html, dados_base) onde ambos compartilham rigorosamente a MESMA base de dados.
    """
    dados_base = construir_dados_distribuicao_temperatura(
        tipos_aletas=tipos_aletas,
        materiais=None,
        k_list=k,
        l=l, h=h, t=t, w=w, D=D, r1=r1, r2=r2,
        T_b=T_b, T_inf=T_inf,
        condicao_ponta=condicao_ponta,
        n_pontos=n_pontos
    )
    fig = criar_figura_plotly_temperatura(dados_base, T_b=T_b, T_inf=T_inf)
    html_grafico = fig.to_html(include_plotlyjs='cdn', div_id="grafico-temperatura")
    return html_grafico, dados_base

def gerar_graficos_comparativos(resultados, material=None):
    """
    Gera gráficos de barras comparativos para Taxa de Calor e Efetividade
    
    Args:
        resultados: Lista de tuplas com resultados (tipo_aleta, eta, Q, A, eps, m, P, A_tr)
        material: Nome do material (opcional)
    
    Returns:
        str: HTML dos gráficos comparativos
    """
    
    if not resultados:
        return "<p>Nenhum resultado para comparar</p>"
    
    # Extrair dados
    tipos = []
    taxas_calor = []
    efetividades = []
    eficiencias = []
    
    for resultado in resultados:
        if len(resultado) >= 5:
            tipo_aleta, eta_aleta, Q_aleta, A_aleta, epsilon_a = resultado[:5]
            
            # Simplificar nomes para visualização
            nome_simples = tipo_aleta.split(')')[1] if ')' in tipo_aleta else tipo_aleta
            nome_simples = nome_simples.replace('aletas ', '').replace('de ', '').title()
            if len(nome_simples) > 20:
                nome_simples = nome_simples[:17] + "..."
            
            tipos.append(nome_simples)
            taxas_calor.append(Q_aleta)
            efetividades.append(epsilon_a)
            eficiencias.append(eta_aleta * 100)  # Converter para porcentagem
    
    # Criar subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            '🔥 Taxa de Transferência de Calor (W)',
            '⚡ Efetividade da Aleta (εₐ)', 
            '📊 Eficiência da Aleta (%)',
            '📈 Comparação Normalizada'
        ],
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "scatter"}]]
    )
    
    # Definir cores baseadas na performance
    cores_calor = ['#27ae60' if q > max(taxas_calor)*0.8 else '#f39c12' if q > max(taxas_calor)*0.5 else '#e74c3c' for q in taxas_calor]
    cores_efetividade = ['#27ae60' if e >= 2 else '#f39c12' if e > 1 else '#e74c3c' for e in efetividades]
    cores_eficiencia = ['#27ae60' if e > 80 else '#f39c12' if e > 50 else '#e74c3c' for e in eficiencias]
    
    # Gráfico 1: Taxa de Calor
    fig.add_trace(
        go.Bar(
            x=tipos, y=taxas_calor,
            marker_color=cores_calor,
            name='Taxa de Calor',
            text=[f'{q:.2f} W' for q in taxas_calor],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Taxa: %{y:.2f} W<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Gráfico 2: Efetividade
    fig.add_trace(
        go.Bar(
            x=tipos, y=efetividades,
            marker_color=cores_efetividade,
            name='Efetividade',
            text=[f'{e:.1f}' for e in efetividades],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Efetividade: %{y:.2f}<extra></extra>'
        ),
        row=1, col=2
    )
    
    # Gráfico 3: Eficiência
    fig.add_trace(
        go.Bar(
            x=tipos, y=eficiencias,
            marker_color=cores_eficiencia,
            name='Eficiência',
            text=[f'{e:.1f}%' for e in eficiencias],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Eficiência: %{y:.1f}%<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Gráfico 4: Análise Normalizada (Scatter)
    # Normalizar valores para comparação
    taxa_norm = [q/max(taxas_calor) for q in taxas_calor]
    efet_norm = [min(e/5, 1) for e in efetividades]  # Normalizar efetividade (máx 5 -> 1)
    
    fig.add_trace(
        go.Scatter(
            x=taxa_norm, y=efet_norm,
            mode='markers+text',
            marker=dict(
                size=[15 + 10*e for e in efet_norm],
                color=eficiencias,
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title="Eficiência (%)", x=1.1, len=0.4, y=0.2)
            ),
            text=[t[:10] + '...' if len(t) > 10 else t for t in tipos],
            textposition='middle center',
            name='Comparação',
            hovertemplate='<b>%{text}</b><br>' +
                         'Taxa Norm.: %{x:.2f}<br>' +
                         'Efetiv. Norm.: %{y:.2f}<extra></extra>'
        ),
        row=2, col=2
    )
    
    # Configurar layout
    fig.update_layout(
        title={
            'text': f'📊 Análise Comparativa de Aletas{" - " + material if material else ""}',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#2c3e50'}
        },
        showlegend=False,
        height=800,
        plot_bgcolor='rgba(248,249,250,0.9)',
        paper_bgcolor='white'
    )
    
    # Configurar eixos
    fig.update_xaxes(title_font=dict(size=12))
    fig.update_yaxes(title_font=dict(size=12))
    
    # Adicionar linha de referência para efetividade = 2
    fig.add_hline(y=2, line_dash="dot", line_color="green", 
                  annotation_text="εₐ = 2 (Mínimo Recomendado)", 
                  row="1", col="2")
    
    # Configurar subplot 4 (scatter)
    fig.update_xaxes(title_text="Taxa de Calor Normalizada", row=2, col=2)
    fig.update_yaxes(title_text="Efetividade Normalizada", row=2, col=2)
    
    return fig.to_html(include_plotlyjs='cdn', div_id="graficos-comparativos")

def salvar_grafico_interativo(fig, nome_arquivo='grafico_interativo.html'):
    """
    Salva gráfico interativo como arquivo HTML para download
    
    Args:
        fig: Figura do Plotly
        nome_arquivo: Nome do arquivo a ser salvo
    
    Returns:
        str: Caminho do arquivo salvo
    """
    os.makedirs('static/downloads', exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_final = f"static/downloads/{timestamp}_{nome_arquivo}"
    
    fig.write_html(nome_final, include_plotlyjs='cdn')
    
    return nome_final

def gerar_grafico_temperatura_multiplos_materiais(tipos_aletas, materiais, h, k_list, l, t=None, w=None, D=None, r1=None, r2=None, T_b=None, T_inf=None, condicao_ponta='adiabatica', n_pontos=201):
    """
    Gera o gráfico interativo de temperatura para múltiplos materiais (ou aletas) e retorna:
    (grafico_html, dados_base) onde ambos compartilham rigorosamente a MESMA base de dados.
    """
    dados_base = construir_dados_distribuicao_temperatura(
        tipos_aletas=tipos_aletas,
        materiais=materiais,
        k_list=k_list,
        l=l, h=h, t=t, w=w, D=D, r1=r1, r2=r2,
        T_b=T_b, T_inf=T_inf,
        condicao_ponta=condicao_ponta,
        n_pontos=n_pontos
    )
    fig = criar_figura_plotly_temperatura(dados_base, T_b=T_b, T_inf=T_inf)
    html_grafico = fig.to_html(include_plotlyjs='cdn', div_id="grafico-multiplos-materiais")
    return html_grafico, dados_base


def extrair_dados_curvas_json_interativo(tipos_aletas, h, k, l, t=None, w=None, D=None, r1=None, r2=None, T_b=None, T_inf=None, condicao_ponta='adiabatica', n_pontos=201):
    """Retorna os dados JSON compartilhados da base única para /resultado."""
    dados_base = construir_dados_distribuicao_temperatura(
        tipos_aletas=tipos_aletas,
        materiais=None,
        k_list=k,
        l=l, h=h, t=t, w=w, D=D, r1=r1, r2=r2,
        T_b=T_b, T_inf=T_inf,
        condicao_ponta=condicao_ponta,
        n_pontos=n_pontos
    )
    return json.dumps(dados_base)


def extrair_dados_curvas_json_multiplos(tipos_aletas, materiais, h, k_list, l, t=None, w=None, D=None, r1=None, r2=None, T_b=None, T_inf=None, condicao_ponta='adiabatica', n_pontos=201):
    """Retorna os dados JSON compartilhados da base única para /resultados_sele."""
    dados_base = construir_dados_distribuicao_temperatura(
        tipos_aletas=tipos_aletas,
        materiais=materiais,
        k_list=k_list,
        l=l, h=h, t=t, w=w, D=D, r1=r1, r2=r2,
        T_b=T_b, T_inf=T_inf,
        condicao_ponta=condicao_ponta,
        n_pontos=n_pontos
    )
    return json.dumps(dados_base)