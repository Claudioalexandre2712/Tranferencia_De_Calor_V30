import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import os
import datetime

def gerar_grafico_temperatura_interativo(tipos_aletas, h, k, l, t=None, w=None, D=None, r1=None, r2=None, T_b=None, T_inf=None, condicao_ponta='adiabatica'):
    # Auto-dedução de variáveis
    if T_b is None: T_b = 100.0
    if T_inf is None: T_inf = 25.0
    if h is None or h <= 0: h = 25.0
    if k is None or k <= 0: k = 222.0
    if l is None or l <= 0: l = 0.05
    if D is not None and D > 0:
        if t is None or t <= 0: t = D
        if w is None or w <= 0: w = D
        if r1 is None or r1 <= 0: r1 = D / 2.0
        if r2 is None or r2 <= 0: r2 = D
    if D is None or D <= 0:
        if t is not None and w is not None and (t + w) > 0:
            D = 2.0 * (w * t) / (w + t)
        elif t is not None and t > 0: D = t
        elif w is not None and w > 0: D = w
        else: D = 0.01
    if t is None or t <= 0: t = D if (D and D > 0) else 0.002
    if w is None or w <= 0: w = D if (D and D > 0) else 0.1
    if r1 is None or r1 <= 0: r1 = (D / 2.0) if (D and D > 0) else 0.01
    if r2 is None or r2 <= r1: r2 = (r1 * 2.0) if r1 > 0 else 0.02

    from modelo3 import (T_aleta_retangular, T_aleta_triangular, T_aleta_parabolica, 
                        T_aleta_circular, T_aleta_perfil_retangular, T_aleta_perfil_triangular,
                        T_aleta_perfil_parabolico, T_aleta_pino_parabolico, normalizar_tipo_aleta)
    
    tipos_aletas = [normalizar_tipo_aleta(ta) for ta in tipos_aletas]
    
    x = np.linspace(0, l, 100)
    
    # Criar figura
    fig = go.Figure()
    
    # Definir cores para cada tipo de aleta (mais contrastantes)
    cores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#17becf']
    
    for i, tipo_aleta in enumerate(tipos_aletas):
        try:
            if tipo_aleta == "1)aletas retangulares retas":
                T_x = T_aleta_retangular(x, l, T_b, T_inf, h, k, t, w)
                nome = "Retangular Reta"
            elif tipo_aleta == "2)aletas triangulares retas":
                T_x = T_aleta_triangular(x, l, T_b, T_inf, h, k, t, w)
                nome = "Triangular Reta"
            elif tipo_aleta == "3)aletas parabolicas retas":
                T_x = T_aleta_parabolica(x, l, T_b, T_inf, h, k, t, w)
                nome = "Parabólica Reta"
            elif tipo_aleta == "4)aletas circulares de perfil retangular":
                T_x = T_aleta_circular(x, l, T_b, T_inf, h, k, t, r1, r2)
                nome = "Circular Retangular"
            elif tipo_aleta == "5)aletas de perfil retangular":
                T_x = T_aleta_perfil_retangular(x, l, T_b, T_inf, h, k, D)
                nome = "Pino Retangular"
            elif tipo_aleta == "6)aletas de perfil triangular":
                T_x = T_aleta_perfil_triangular(x, l, T_b, T_inf, h, k, D)
                nome = "Pino Triangular"
            elif tipo_aleta == "7)aletas de perfil parabolico":
                T_x = T_aleta_perfil_parabolico(x, l, T_b, T_inf, h, k, D)
                nome = "Pino Parabólico"
            elif tipo_aleta == "8)aletas de pino de perfilparabolico (ponta arredondada)":
                T_x = T_aleta_pino_parabolico(x, l, T_b, T_inf, h, k, D)
                nome = "Pino Parabólico (Arredondado)"
            else:
                T_x = np.full_like(x, T_inf)
                nome = "Desconhecido"
            
            # Adicionar linha simples e limpa
            fig.add_trace(go.Scatter(
                x=x*1000,  # Converter para mm
                y=T_x,
                mode='lines',
                name=nome,
                line=dict(color=cores[i % len(cores)], width=2),
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             'Posição: %{x:.1f} mm<br>' +
                             'Temperatura: %{y:.1f} °C<extra></extra>'
            ))
            
        except Exception as e:
            print(f"Erro ao calcular temperatura para {tipo_aleta}: {e}")
            continue
    
    # Calcular todas as temperaturas primeiro para determinar faixa real
    todas_temperaturas = []
    
    # Calcular temperaturas de todas as aletas para encontrar faixa real
    for tipo_aleta in tipos_aletas:
        try:
            if tipo_aleta == "1)aletas retangulares retas":
                T_temp = T_aleta_retangular(x, l, T_b, T_inf, h, k, t, w)
            elif tipo_aleta == "2)aletas triangulares retas":
                T_temp = T_aleta_triangular(x, l, T_b, T_inf, h, k, t, w)
            elif tipo_aleta == "3)aletas parabolicas retas":
                T_temp = T_aleta_parabolica(x, l, T_b, T_inf, h, k, t, w)
            elif tipo_aleta == "4)aletas circulares de perfil retangular":
                T_temp = T_aleta_circular(x, l, T_b, T_inf, h, k, t, r1, r2)
            elif tipo_aleta == "5)aletas de perfil retangular":
                T_temp = T_aleta_perfil_retangular(x, l, T_b, T_inf, h, k, D)
            elif tipo_aleta == "6)aletas de perfil triangular":
                T_temp = T_aleta_perfil_triangular(x, l, T_b, T_inf, h, k, D)
            elif tipo_aleta == "7)aletas de perfil parabolico":
                T_temp = T_aleta_perfil_parabolico(x, l, T_b, T_inf, h, k, D)
            elif tipo_aleta == "8)aletas de pino de perfilparabolico (ponta arredondada)":
                T_temp = T_aleta_pino_parabolico(x, l, T_b, T_inf, h, k, D)
            else:
                continue
                
            todas_temperaturas.extend(T_temp)
        except (ZeroDivisionError, ValueError, TypeError) as e:
            print(f"Erro no cálculo de temperatura para {tipo_aleta}: {e}")
            continue
    
    # Deixar o eixo Y se ajustar naturalmente às curvas
    if todas_temperaturas:
        temp_min_real = min(todas_temperaturas)
        temp_max_real = max(todas_temperaturas)
        
        # Margem simples e natural (10% de cada lado)
        delta_temp = temp_max_real - temp_min_real
        margem = max(delta_temp * 0.1, 2)  # Margem mínima de 2°C
        
        y_min = temp_min_real - margem
        y_max = temp_max_real + margem
    else:
        # Deixar automático
        y_min = None
        y_max = None

    # Configurar layout
    fig.update_layout(
        title={
            'text': f'🌡️ Distribuição de Temperatura - Condição: {condicao_ponta.title()}',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#2c3e50'}
        },
        xaxis_title='Comprimento da Aleta (mm)',
        yaxis_title='Temperatura (°C)',
        xaxis=dict(
            gridcolor='rgba(128,128,128,0.3)',
            gridwidth=1,
            title_font=dict(size=14, color='#34495e')
        ),
        yaxis=dict(
            gridcolor='rgba(128,128,128,0.2)',
            gridwidth=1,
            title_font=dict(size=14, color='#34495e'),
            range=[y_min, y_max] if y_min is not None and y_max is not None else None,
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
    
    # Adicionar linhas de referência simples
    fig.add_hline(
        y=T_inf, 
        line_dash="dot", 
        line_color="#666",
        annotation_text=f"T∞ = {T_inf}°C",
        annotation_position="bottom right"
    )
    
    fig.add_hline(
        y=T_b, 
        line_dash="dot", 
        line_color="#666",
        annotation_text=f"Tb = {T_b}°C",
        annotation_position="top right"
    )
    
    # Retornar HTML para renderização direta
    return fig.to_html(include_plotlyjs='cdn', div_id="grafico-temperatura")

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

def gerar_grafico_temperatura_multiplos_materiais(tipos_aletas, materiais, h, k_list, l, t=None, w=None, D=None, r1=None, r2=None, T_b=None, T_inf=None, condicao_ponta='adiabatica'):
    """
    Gera gráfico interativo de temperatura para múltiplos materiais
    
    Args:
        tipos_aletas: Lista de tipos de aletas
        materiais: Lista de nomes dos materiais
        h: Coeficiente de convecção
        k_list: Lista de condutividades térmicas
        l: Comprimento da aleta
        ... (outros parâmetros)
    
    Returns:
        str: HTML do gráfico Plotly
    """
    # Importar funções de temperatura do modelo3
    from modelo3 import (T_aleta_retangular, T_aleta_triangular, T_aleta_parabolica, 
                        T_aleta_circular, T_aleta_perfil_retangular, T_aleta_perfil_triangular,
                        T_aleta_perfil_parabolico, T_aleta_pino_parabolico)
    
    x = np.linspace(0, l, 100)
    
    # Criar figura
    fig = go.Figure()
    
    # Cores para diferencial de materiais e aletas
    cores_materiais = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    cores_aletas = ['solid', 'dash', 'dot', 'dashdot', 'longdash']
    
    # Loop para cada combinação de aleta e material
    for i, tipo_aleta in enumerate(tipos_aletas):
        for j, (material, k) in enumerate(zip(materiais, k_list)):
            try:
                if tipo_aleta == "1)aletas retangulares retas":
                    T_x = T_aleta_retangular(x, l, T_b, T_inf, h, k, t, w)
                    nome_aleta = "Retangular"
                elif tipo_aleta == "2)aletas triangulares retas":
                    T_x = T_aleta_triangular(x, l, T_b, T_inf, h, k, t, w)
                    nome_aleta = "Triangular"
                elif tipo_aleta == "3)aletas parabolicas retas":
                    T_x = T_aleta_parabolica(x, l, T_b, T_inf, h, k, t, w)
                    nome_aleta = "Parabólica"
                elif tipo_aleta == "4)aletas circulares de perfil retangular":
                    T_x = T_aleta_circular(x, l, T_b, T_inf, h, k, t, r1, r2)
                    nome_aleta = "Circular"
                elif tipo_aleta == "5)aletas de perfil retangular":
                    T_x = T_aleta_perfil_retangular(x, l, T_b, T_inf, h, k, D)
                    nome_aleta = "Pino Retangular"
                elif tipo_aleta == "6)aletas de perfil triangular":
                    T_x = T_aleta_perfil_triangular(x, l, T_b, T_inf, h, k, D)
                    nome_aleta = "Pino Triangular"
                elif tipo_aleta == "7)aletas de perfil parabolico":
                    T_x = T_aleta_perfil_parabolico(x, l, T_b, T_inf, h, k, D)
                    nome_aleta = "Pino Parabólico"
                elif tipo_aleta == "8)aletas de pino de perfilparabolico (ponta arredondada)":
                    T_x = T_aleta_pino_parabolico(x, l, T_b, T_inf, h, k, D)
                    nome_aleta = "Pino Arredondado"
                else:
                    T_x = np.full_like(x, T_inf)
                    nome_aleta = "Desconhecido"
                
                # Nome da legenda combinando aleta e material
                nome_legenda = f"{nome_aleta} - {material} (k={k:.1f})"
                
                # Adicionar linha com cor específica para material e estilo para aleta
                fig.add_trace(go.Scatter(
                    x=x*1000,  # Converter para mm
                    y=T_x,
                    mode='lines',
                    name=nome_legenda,
                    line=dict(
                        color=cores_materiais[j % len(cores_materiais)],
                        dash=cores_aletas[i % len(cores_aletas)],
                        width=2.5
                    ),
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                'Posição: %{x:.1f} mm<br>' +
                                'Temperatura: %{y:.2f} °C<br>' +
                                '<extra></extra>'
                ))
                
            except Exception as e:
                print(f"Erro ao gerar gráfico para {tipo_aleta} com {material}: {e}")
                continue
    
    # Configurar layout
    fig.update_layout(
        title={
            'text': '🌡️ Distribuição de Temperatura - Múltiplos Materiais',
            'x': 0.5,
            'font': {'size': 18, 'color': '#1976d2'}
        },
        xaxis=dict(
            title='Posição ao longo da aleta (mm)',
            gridcolor='lightgray',
            showgrid=True,
            zeroline=False
        ),
        yaxis=dict(
            title='Temperatura (°C)',
            gridcolor='lightgray', 
            showgrid=True,
            zeroline=False
        ),
        plot_bgcolor='rgba(248, 249, 250, 0.8)',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="lightgray",
            borderwidth=1
        ),
        hovermode='closest',
        margin=dict(l=60, r=150, t=60, b=60)
    )
    
    return fig.to_html(include_plotlyjs='cdn', div_id="grafico-multiplos-materiais")
    return nome_final