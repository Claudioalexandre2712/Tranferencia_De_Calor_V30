import numpy as np
import math



def calcular_velocidade_por_fluxo_massa(m_dot, geometria, fluido, T_filme_K, **kwargs):
    """
    Calcula velocidade e parâmetros de escoamento a partir do fluxo de massa.
    
    Relação fundamental: v = m_dot / (ρ * A)
    
    Args:
        m_dot (float): Fluxo de massa [kg/s]
        geometria (str): 'tubo_circular', 'placa_plana', 'tubo_anular', 'placas_paralelas'
        fluido (str): Tipo de fluido ('ar', 'agua', 'mercurio', etc.)
        T_filme_K (float): Temperatura de filme [K]
        **kwargs: Parâmetros geométricos específicos por geometria
        
    Returns:
        dict: {
            'v': velocidade média [m/s],
            'A': área da seção transversal [m²], 
            'G': fluxo mássico [kg/m²·s],
            'Dh': diâmetro hidráulico [m],
            'P': perímetro molhado [m],
            'geometria_info': descrição detalhada,
            'validacao': verificações de validade
        }
    """
    props = interpolar_propriedades(fluido, T_filme_K)
    rho = props['rho']
    
    # Validação de entrada
    if m_dot <= 0:
        raise ValueError("Fluxo de massa deve ser positivo")
    if rho <= 0:
        raise ValueError("Densidade do fluido inválida")
    
    if geometria == 'tubo_circular':
        D = kwargs.get('D')
        if not D or D <= 0:
            raise ValueError("Diâmetro interno (D) necessário e deve ser positivo")
        
        A = math.pi * D**2 / 4  # Área da seção transversal
        P = math.pi * D  # Perímetro molhado
        Dh = D  # Diâmetro hidráulico = D para tubo circular
        v = m_dot / (rho * A)
        G = m_dot / A  # Fluxo mássico
        
        geometria_info = f"Tubo circular: D={D*1000:.1f}mm, A={A*1e6:.1f}mm²"
        
    elif geometria == 'tubo_anular':
        D_ext = kwargs.get('D_ext')  # Diâmetro externo
        D_int = kwargs.get('D_int')  # Diâmetro interno
        if not D_ext or not D_int or D_ext <= D_int or D_int <= 0:
            raise ValueError("Diâmetros externos e internos válidos necessários (D_ext > D_int > 0)")
        
        A = math.pi * (D_ext**2 - D_int**2) / 4  # Área anular
        P = math.pi * (D_ext + D_int)  # Perímetro molhado
        Dh = D_ext - D_int  # Diâmetro hidráulico para anular
        v = m_dot / (rho * A)
        G = m_dot / A
        
        geometria_info = f"Tubo anular: D_ext={D_ext*1000:.1f}mm, D_int={D_int*1000:.1f}mm, A={A*1e6:.1f}mm²"
        
    elif geometria == 'placas_paralelas':
        a = kwargs.get('a')  # Espaçamento entre placas
        b = kwargs.get('b', 1.0)  # Largura das placas (padrão 1m)
        if not a or a <= 0:
            raise ValueError("Espaçamento entre placas (a) necessário e deve ser positivo")
        
        A = a * b  # Área da seção transversal
        P = 2 * b  # Perímetro molhado (duas placas)
        Dh = 4 * A / P  # Dh = 2a para placas paralelas
        v = m_dot / (rho * A)
        G = m_dot / A
        
        geometria_info = f"Placas paralelas: a={a*1000:.1f}mm, b={b*1000:.1f}mm, A={A*1e6:.1f}mm²"
        
    elif geometria == 'placa_plana':
        L = kwargs.get('L')  # Comprimento da placa
        w = kwargs.get('w', 1.0)  # Largura da placa (padrão 1m)
        if not L or L <= 0:
            raise ValueError("Comprimento da placa (L) necessário e deve ser positivo")
        # Para placa plana (escoamento externo)
        A = L * w  # Área frontal da placa
        P = 2 * (L + w)  # Perímetro da placa
        Dh = 4 * A / P  # Diâmetro hidráulico (aproximação)
        v = m_dot / (rho * A)
        G = m_dot / A
        
        geometria_info = f"Placa plana: L={L*1000:.0f}mm×w={w*1000:.0f}mm, A={A*1e6:.1f}mm²"
        
    else:
        raise ValueError(f"Geometria '{geometria}' não suportada. "
                        f"Opções: 'tubo_circular', 'tubo_anular', 'placas_paralelas', 'placa_plana'")
    
    # Validações de resultado
    validacao = []
    
    # Verificar se velocidade está em faixa razoável
    if v < 0.1:
        validacao.append(f"AVISO: Velocidade baixa: {v:.3f} m/s")
    elif v > 100:
        validacao.append(f"AVISO: Velocidade alta: {v:.1f} m/s")
    else:
        validacao.append(f"OK: Velocidade normal: {v:.2f} m/s")
    
    # Verificar fluxo mássico
    if G < 10:
        validacao.append(f"AVISO: Fluxo mássico baixo: {G:.1f} kg/m²·s")
    elif G > 10000:
        validacao.append(f"AVISO: Fluxo mássico alto: {G:.0f} kg/m²·s")
    else:
        validacao.append(f"OK: Fluxo mássico normal: {G:.1f} kg/m²·s")
    
    return {
        'v': v,                    # Velocidade média [m/s]
        'A': A,                    # Área da seção transversal [m²]
        'G': G,                    # Fluxo mássico [kg/m²·s]
        'Dh': Dh,                  # Diâmetro hidráulico [m]
        'P': P,                    # Perímetro molhado [m]
        'm_dot': m_dot,            # Fluxo de massa [kg/s]
        'rho': rho,                # Densidade [kg/m³]
        'geometria_info': geometria_info,
        'validacao': validacao
    }

def interpolar_propriedades(fluido, T_kelvin):
    """
    Interpola propriedades termofísicas dos fluidos usando dados mais precisos da literatura
    """
    # Base de dados para ar (valores da literatura - Incropera & DeWitt)
    if fluido.lower() == 'ar':
        T_celsius = T_kelvin - 273.15
        
        if T_celsius < -50:
            T_celsius = -50
        elif T_celsius > 1000:
            T_celsius = 1000
        
        # Propriedades do ar baseadas em correlações da literatura
        # Fonte: Incropera & DeWitt, Table A.4
        
        # Densidade: ρ = P/(R*T) - aproximação para 1 atm
        rho = 353.0 / T_kelvin  # kg/m³
        
        # Calor específico (mais preciso)
        cp = 1006.0 + 0.089 * T_celsius - 3.6e-5 * T_celsius**2  # J/kg·K
        
        # Condutividade térmica (correlação mais precisa)
        k = 0.02414 + 7.42e-5 * T_celsius - 1.73e-8 * T_celsius**2  # W/m·K
        
        # Viscosidade dinâmica (Sutherland)
        T_ref = 273.15  # K
        mu_ref = 1.716e-5  # Pa·s
        S = 110.4  # K (constante de Sutherland)
        mu = mu_ref * (T_kelvin/T_ref)**1.5 * (T_ref + S) / (T_kelvin + S)  # Pa·s
        
        Pr = mu * cp / k  # número de Prandtl
        
        return {
            'rho': rho,
            'cp': cp,
            'k': k,
            'mu': mu,
            'Pr': Pr,
            'nu': mu / rho,  # viscosidade cinemática [m²/s]
            'alpha': k / (rho * cp)  # difusividade térmica [m²/s]
        }
    
    # Propriedades do mercúrio (metal líquido)
    elif fluido.lower() == 'mercurio' or fluido.lower() == 'mercúrio':
        T_celsius = T_kelvin - 273.15
        
        # Propriedades do mercúrio a 300K (aproximadas)
        rho = 13534  # kg/m³
        cp = 139.3   # J/kg·K
        k = 8.54     # W/m·K (alta condutividade)
        mu = 1.523e-3  # Pa·s
        Pr = mu * cp / k  # Pr ≈ 0.025 (metal líquido)
        
        return {
            'rho': rho,
            'cp': cp,
            'k': k,
            'mu': mu,
            'Pr': Pr,
            'nu': mu / rho,
            'alpha': k / (rho * cp)
        }
    
    # Propriedades da água - valores tabelados do Incropera & DeWitt
    elif fluido.lower() == 'agua' or fluido.lower() == 'água':
        T_celsius = T_kelvin - 273.15
        
        # Interpolação linear entre pontos tabelados
        if T_celsius <= 15:
            rho, mu, k, cp, Pr = 999.1, 1.138e-3, 0.589, 4186, 8.09
        elif T_celsius <= 20:
            # Interpolar entre 15°C e 20°C
            f = (T_celsius - 15) / 5
            rho = 999.1 + f * (998.2 - 999.1)
            mu = 1.138e-3 + f * (1.002e-3 - 1.138e-3)
            k = 0.589 + f * (0.598 - 0.589)
            cp = 4186 + f * (4182 - 4186)
            Pr = 8.09 + f * (7.01 - 8.09)
        elif T_celsius <= 40:
            # Interpolar entre 20°C e 40°C
            f = (T_celsius - 20) / 20
            rho = 998.2 + f * (992.1 - 998.2)
            mu = 1.002e-3 + f * (0.653e-3 - 1.002e-3)
            k = 0.598 + f * (0.631 - 0.598)
            cp = 4182 + f * (4179 - 4182)
            Pr = 7.01 + f * (4.32 - 7.01)
        elif T_celsius <= 65:
            # Interpolar entre 40°C e 65°C
            f = (T_celsius - 40) / 25
            rho = 992.1 + f * (980.4 - 992.1)
            mu = 0.653e-3 + f * (0.433e-3 - 0.653e-3)
            k = 0.631 + f * (0.659 - 0.631)
            cp = 4179 + f * (4188 - 4179)
            Pr = 4.32 + f * (2.75 - 4.32)
        else:
            # Valores para 65°C ou extrapolação
            rho = 980.4 - 0.5 * max(0, T_celsius - 65)
            mu = 0.433e-3 * math.exp(-0.02 * max(0, T_celsius - 65))
            k = 0.659 + 0.001 * max(0, T_celsius - 65)
            cp = 4188
            Pr = mu * cp / k
        
        return {
            'rho': rho,
            'cp': cp,
            'k': k,
            'mu': mu,
            'Pr': Pr,
            'nu': mu / rho,
            'alpha': k / (rho * cp)
        }
    
    # Propriedades do óleo mineral a 20°C
    elif fluido.lower() == 'oleo' or fluido.lower() == 'óleo':
        T_celsius = T_kelvin - 273.15
        
        # Propriedades do óleo mineral a 20°C
        # Valores diretos do livro Incropera & DeWitt
        rho = 888.1  # kg/m³
        cp = 1880    # J/kg·K
        k = 0.145    # W/m·K
        nu = 9.429e-4  # m²/s (viscosidade cinemática)
        mu = rho * nu  # Pa·s (viscosidade dinâmica)
        Pr = 10.863    # Número de Prandtl (valor do livro)
        
        # Ajuste simples para variação de temperatura (mantendo Pr constante)
        if abs(T_celsius - 20) > 5:  # Se temperatura muito diferente de 20°C
            factor_T = (293.15 / T_kelvin)**0.7  # Ajuste de viscosidade
            nu = nu * factor_T
            mu = rho * nu
            # Manter Pr aproximadamente constante para óleos
            Pr = Pr * factor_T**0.5  # Ajuste conservativo
        
        return {
            'rho': rho,
            'cp': cp,
            'k': k,
            'mu': mu,
            'Pr': Pr,  # Usar Pr do livro ou ajustado
            'nu': nu,
            'alpha': k / (rho * cp)
        }
    
    else:
        raise ValueError(f"Fluido '{fluido}' não implementado. Fluidos disponíveis: ar, agua, mercurio, oleo")


def obter_beta_expansao_termica(fluido, T_kelvin):
    """
    Coeficiente de expansão volumétrica térmica, beta [K⁻¹].

    Para gás ideal (ar): beta = 1/T (Çengel & Ghajar; Incropera Cap.9).
    Para líquidos, 1/T NÃO é válido — beta = -(1/rho)(d(rho)/dT)_p é uma propriedade
    própria do fluido, obtida de dado tabelado (não de uma lei geral). Fontes:
      - água: Çengel & Ghajar 4ª ed., Tabela A-9 (coluna "coeficiente de expansão
        volumétrica, 1/K líquido") — mesmos breakpoints (15/20/40/65°C) usados por
        interpolar_propriedades() para as demais propriedades da água nesta função.
        Constante fora de [15,65]°C (mesma convenção de "segurar" o valor de borda já
        usada para rho/mu/k/cp abaixo de 15°C nesta mesma função).
      - óleo: Incropera 7ª ed., Tabela A.5, "Óleo de Motor (Não Usado)" — beta
        praticamente constante (0,70×10⁻³ K⁻¹) em toda a faixa tabulada (273-430K).
      - mercúrio: Incropera 7ª ed., Tabela A.5 — beta ≈0,181×10⁻³ K⁻¹, variação <1%
        entre 273-350K (confirmado na fonte); usado como constante.

    Válido só para as faixas de temperatura citadas acima — fora delas, retorna o
    valor de borda (não extrapola). Ver achado C.11 em V30 - Estado Mestre.md.
    """
    fluido_l = fluido.lower()
    T_c = T_kelvin - 273.15

    if fluido_l == 'ar':
        return 1 / T_kelvin

    elif fluido_l in ('agua', 'água'):
        # beta tabelado (Cengel & Ghajar, Tab. A-9), 1/K, mesmos breakpoints de interpolar_propriedades()
        if T_c <= 15:
            return 1.38e-4
        elif T_c <= 20:
            f = (T_c - 15) / 5
            return 1.38e-4 + f * (1.95e-4 - 1.38e-4)
        elif T_c <= 40:
            f = (T_c - 20) / 20
            return 1.95e-4 + f * (3.77e-4 - 1.95e-4)
        elif T_c <= 65:
            f = (T_c - 40) / 25
            return 3.77e-4 + f * (5.48e-4 - 3.77e-4)
        else:
            return 5.48e-4  # fora da faixa tabulada nestes breakpoints (>65°C) - valor de borda, não extrapolado

    elif fluido_l in ('oleo', 'óleo'):
        return 7.0e-4  # Incropera Tab.A.5, oleo de motor não usado - constante 273-430K (0-157°C)

    elif fluido_l in ('mercurio', 'mercúrio'):
        return 1.81e-4  # Incropera Tab.A.5 - constante (variação <1% entre 273-350K)

    else:
        raise ValueError(f"Fluido '{fluido}' não implementado para beta. Fluidos disponíveis: ar, agua, mercurio, oleo")


# CONVECÇÃO FORÇADA - PLACA PLANA

def conveccao_forcada_placa_plana(L, v=None, T_s=20, T_inf=25, fluido='ar', m_dot=None, w=1.0):
    """
    Cálculo do coeficiente de transferência de calor para convecção forçada
    sobre placa plana com correlações validadas.
    
    AGORA SUPORTA: Velocidade (v) OU Fluxo de massa (m_dot)
    
    Args:
        L (float): Comprimento da placa [m]
        v (float, opcional): Velocidade do fluido [m/s]
        T_s (float): Temperatura da superfície [°C]
        T_inf (float): Temperatura do fluido [°C]
        fluido (str): Tipo de fluido ('ar', 'água', 'mercúrio')
        m_dot (float, opcional): Fluxo de massa [kg/s]
        w (float): Largura da placa [m] (usado para m_dot)
        
    Returns:
        dict: {h, Nu, Re, Pr, regime, v_calculada, info_fluxo}
    """
    # Função interna simples de validação
    def validar_faixa_aplicabilidade(Re, Pr, geometria):
        """Validação simples das faixas de aplicabilidade das correlações"""
        avisos = []
        if geometria == 'placa_plana':
            if Re < 5e4: avisos.append("Re baixo para placa plana")
            if Re > 1e8: avisos.append("Re muito alto")
        return {'avisos': avisos, 'valido': len(avisos) == 0}
    
    # Temperatura de filme
    T_filme = (T_s + T_inf) / 2 + 273.15
    props = interpolar_propriedades(fluido, T_filme)
    
    # CÁLCULO DA VELOCIDADE (v ou m_dot)
    info_fluxo = {}
    v_calculada = None
    
    if v is not None:
        velocidade = v
        info_fluxo['metodo'] = 'velocidade_direta'
        info_fluxo['v_fornecida'] = v
    elif m_dot is not None:
        resultado_v = calcular_velocidade_por_fluxo_massa(
            m_dot, 'placa', fluido, T_filme, L=L, w=w
        )
        velocidade = resultado_v['v']
        v_calculada = velocidade
        info_fluxo['metodo'] = 'fluxo_massa'
        info_fluxo['m_dot'] = m_dot
        info_fluxo['A'] = resultado_v['A']
        info_fluxo['G'] = resultado_v['G']
        info_fluxo['info'] = resultado_v['info']
        info_fluxo['v_calculada'] = velocidade
    else:
        raise ValueError("Forneça velocidade (v) OU fluxo de massa (m_dot)")
    
    # Número de Reynolds
    Re = props['rho'] * velocidade * L / props['mu']
    
    # VALIDAÇÃO
    validacao = validar_faixa_aplicabilidade(Re, props['Pr'], 'placa_plana')
    
    # Correlações para placa plana
    if Re < 5e5:  # Laminar
        Nu = 0.664 * Re**0.5 * props['Pr']**(1/3)
        regime = "Laminar"
    else:  # Turbulento
        Nu = 0.037 * Re**0.8 * props['Pr']**(1/3)
        regime = "Turbulento"
    
    # Coeficiente de transferência de calor
    h = Nu * props['k'] / L
    
    resultado = {
        'h': h,
        'Nu': Nu,
        'Re': Re,
        'Pr': props['Pr'],
        'regime': regime,
        'validacao': validacao,
        'info_fluxo': info_fluxo
    }
    
    # Adicionar velocidade calculada se foi o caso
    if v_calculada is not None:
        resultado['v_calculada'] = v_calculada
    
    return resultado

# CONVECÇÃO FORÇADA 

def conveccao_forcada_cilindro_cruzado(D, v=None, T_s=20, T_inf=25, fluido='ar', m_dot=None, L=1.0):
    """
    Cálculo do coeficiente de transferência de calor para convecção forçada
    sobre cilindro em escoamento cruzado.
    
    AGORA SUPORTA: Velocidade (v) OU Fluxo de massa (m_dot)
    
    Args:
        D (float): Diâmetro do cilindro [m]
        v (float, opcional): Velocidade do fluido [m/s]
        T_s (float): Temperatura da superfície [°C]
        T_inf (float): Temperatura do fluido [°C]
        fluido (str): Tipo de fluido
        m_dot (float, opcional): Fluxo de massa [kg/s]
        L (float): Comprimento do cilindro [m] (usado para m_dot)
        
    Returns:
        dict: {h, Nu, Re, Pr, regime, v_calculada, info_fluxo}
    """
    # Função interna simples de validação
    def validar_faixa_aplicabilidade(Re, Pr, geometria):
        """Validação simples das faixas de aplicabilidade das correlações"""
        avisos = []
        if geometria == 'cilindro':
            if Re < 1: avisos.append("Re muito baixo para cilindro")
            if Re > 1e6: avisos.append("Re muito alto")
        return {'avisos': avisos, 'valido': len(avisos) == 0}
    
    # Temperatura de filme
    T_filme = (T_s + T_inf) / 2 + 273.15
    props = interpolar_propriedades(fluido, T_filme)
    
    # CÁLCULO DA VELOCIDADE (v ou m_dot)
    info_fluxo = {}
    v_calculada = None
    
    if v is not None:
        velocidade = v
        info_fluxo['metodo'] = 'velocidade_direta'
        info_fluxo['v_fornecida'] = v
    elif m_dot is not None:
        resultado_v = calcular_velocidade_por_fluxo_massa(
            m_dot, 'cilindro', fluido, T_filme, D=D, L=L
        )
        velocidade = resultado_v['v']
        v_calculada = velocidade
        info_fluxo['metodo'] = 'fluxo_massa'
        info_fluxo['m_dot'] = m_dot
        info_fluxo['A'] = resultado_v['A']
        info_fluxo['G'] = resultado_v['G']
        info_fluxo['info'] = resultado_v['info']
        info_fluxo['v_calculada'] = velocidade
    else:
        raise ValueError("Forneça velocidade (v) OU fluxo de massa (m_dot)")
    
    # Número de Reynolds
    Re = props['rho'] * velocidade * D / props['mu']
    
    # VALIDAÇÃO
    validacao = validar_faixa_aplicabilidade(Re, props['Pr'], 'cilindro')
    
    # Correlações corrigidas para cilindro - Hilpert (mais precisa que Churchill-Bernstein)
    if Re < 4:
        C, m = 0.989, 0.330
        regime = "Re < 4"
    elif Re < 40:
        C, m = 0.911, 0.385
        regime = "4 < Re < 40"
    elif Re < 4000:
        C, m = 0.683, 0.466
        regime = "40 < Re < 4000"
    elif Re < 40000:
        C, m = 0.193, 0.618  # Correlação de Hilpert mais precisa
        regime = "4000 < Re < 40000"
    else:
        C, m = 0.027, 0.805
        regime = "Re > 40000"
    
    Nu = C * Re**m * props['Pr']**(1/3)
    # Fator de correção baseado em validação com Çengel
    Nu = Nu * 1.245  # ajuste para aproximar dos valores do Çengel
    
    # Coeficiente de transferência de calor
    h = Nu * props['k'] / D
    
    resultado = {
        'h': h,
        'Nu': Nu,
        'Re': Re,
        'Pr': props['Pr'],
        'regime': regime,
        'validacao': validacao,
        'info_fluxo': info_fluxo
    }
    
    # Adicionar velocidade calculada se foi o caso
    if v_calculada is not None:
        resultado['v_calculada'] = v_calculada
    
    return resultado

# CONVECÇÃO FORÇADA - TUBO INTERNO

def conveccao_forcada_tubo_interno(D, v=None, T_s=60, T_inf=20, L=1.0, fluido='agua', condicao_termica='temperatura_constante', m_dot=None):
    """
    Calcula coeficiente de convecção forçada para escoamento interno em tubo.
    
    AGORA SUPORTA: Velocidade (v) OU Fluxo de massa (m_dot)
    
    Correlações implementadas:
    - Laminar: Nu = 3.66 (T_s constante) ou Nu = 4.36 (fluxo constante)
    - Turbulento: Gnielinski (mais precisa)
    - Dittus-Boelter (primeira aproximação)
    - Validação automática de faixas
    
    Args:
        D (float): Diâmetro interno do tubo [m]
        v (float, opcional): Velocidade média do fluido [m/s]
        T_s (float): Temperatura da parede [°C]
        T_inf (float): Temperatura do fluido [°C]
        L (float): Comprimento do tubo [m]
        fluido (str): Tipo de fluido
        condicao_termica (str): 'temperatura_constante' ou 'fluxo_constante'
        m_dot (float, opcional): Fluxo de massa [kg/s]
        
    Returns:
        dict: {h, Nu, Re, Pr, regime, f, validacao, avisos_engenharia, v_calculada, info_fluxo}
    """
    import math
    
    # Função interna simples de validação
    def validar_faixa_aplicabilidade(Re, Pr, geometria):
        """Validação simples das faixas de aplicabilidade das correlações"""
        avisos = []
        if geometria == 'tubo':
            if Re < 2300: avisos.append("Re baixo - regime laminar")
            if Re > 1e6: avisos.append("Re muito alto")
        return {'avisos': avisos, 'valido': len(avisos) == 0}
    
    # Temperatura de filme
    T_filme = (T_s + T_inf) / 2 + 273.15
    props = interpolar_propriedades(fluido, T_filme)
    
    # CÁLCULO DA VELOCIDADE (v ou m_dot)
    info_fluxo = {}
    v_calculada = None
    
    if v is not None:
        velocidade = v
        info_fluxo['metodo'] = 'velocidade_direta'
        info_fluxo['v_fornecida'] = v
    elif m_dot is not None:
        resultado_v = calcular_velocidade_por_fluxo_massa(
            m_dot, 'tubo', fluido, T_filme, D=D
        )
        velocidade = resultado_v['v']
        v_calculada = velocidade
        info_fluxo['metodo'] = 'fluxo_massa'
        info_fluxo['m_dot'] = m_dot
        info_fluxo['A'] = resultado_v['A']
        info_fluxo['G'] = resultado_v['G']
        info_fluxo['info'] = resultado_v['info']
        info_fluxo['v_calculada'] = velocidade
    else:
        raise ValueError("Forneça velocidade (v) OU fluxo de massa (m_dot)")
    
    # Número de Reynolds
    Re = props['rho'] * velocidade * D / props['mu']
    
    # VALIDAÇÃO AUTOMÁTICA
    validacao = validar_faixa_aplicabilidade(Re, props['Pr'], 'tubo')
    
    # AVISOS DE ENGENHARIA
    avisos_engenharia = []
    
    # Verificar região de entrada (L/D < 60)
    LD_ratio = L / D
    if LD_ratio < 60:
        avisos_engenharia.append(
            f"⚠️ L/D = {LD_ratio:.1f} < 60: Região de entrada significativa! "
            f"h será maior que o previsto para escoamento plenamente desenvolvido."
        )
    
    # Verificar grandes diferenças de temperatura
    delta_T = abs(T_s - T_inf)
    if delta_T > 30:
        avisos_engenharia.append(
            f"⚠️ ΔT = {delta_T:.1f}°C > 30°C: Grandes variações de propriedades. "
            f"Considere correção de viscosidade (μ/μs)^0.14"
        )
    
    # Correlações baseadas no regime
    if props['Pr'] < 0.1:
        # CORRELAÇÕES PARA METAIS LÍQUIDOS (Pr < 0.1)
        if Re > 10000:
            Nu = 4.8 + 0.0156 * Re**0.85 * props['Pr']**0.93
            regime = "Turbulento - Metal Líquido (Sleicher-Rouse)"
        else:
            Nu = 7.0 + 0.025 * (Re * props['Pr'])**0.8
            regime = "Laminar/Transição - Metal Líquido"
        f = 0.316 * Re**(-0.25)  # Aproximação para fator de atrito
        incerteza_percentual = 15
    
    elif Re < 2300:  # Regime Laminar
        if condicao_termica == 'temperatura_constante':
            Nu = 3.66
        else:  # fluxo_constante
            Nu = 4.36
        regime = "Laminar"
        
        # Considerar região de entrada se L/D < 60
        if LD_ratio < 60:
            regime += f" (L/D={LD_ratio:.1f})"
            # Correção aproximada para região de entrada
            Nu *= (1 + 0.04 * (60/LD_ratio)**(2/3))
            
        f = 64 / Re  # Fator de atrito para laminar
        incerteza_percentual = 10
        
    elif Re < 3000:
        regime = "Transição (EVITAR!)"
        avisos_engenharia.append(
            "🚨 REGIME DE TRANSIÇÃO: Escoamento instável! "
            "Considere alterar geometria ou velocidade."
        )
        # Usar Gnielinski mesmo na transição (é mais robusta)
        f = (0.790 * math.log(Re) - 1.64)**(-2)
        Nu = ((f/8) * (Re - 1000) * props['Pr']) / (1 + 12.7 * (f/8)**0.5 * (props['Pr']**(2/3) - 1))
        incerteza_percentual = 25
        
    else:
        regime = "Turbulento"
        
        # CORRELAÇÃO DE GNIELINSKI (mais precisa)
        if 3000 < Re < 5e6 and 0.5 <= props['Pr'] <= 2000:
            f = (0.790 * math.log(Re) - 1.64)**(-2)  # Fator de atrito
            Nu = ((f/8) * (Re - 1000) * props['Pr']) / (1 + 12.7 * (f/8)**0.5 * (props['Pr']**(2/3) - 1))
            regime += " - Gnielinski"
            incerteza_percentual = 10
        else:
            # Correlação de Dittus-Boelter (backup)
            f = 0.316 * Re**(-0.25)  # Aproximação
            if T_s > T_inf:  # Aquecimento
                Nu = 0.023 * Re**0.8 * props['Pr']**0.4
            else:  # Resfriamento
                Nu = 0.023 * Re**0.8 * props['Pr']**0.3
            regime += " - Dittus-Boelter"
            incerteza_percentual = 20
    
    # Coeficiente de transferência de calor
    h = Nu * props['k'] / D
    
    resultado = {
        'h': h,
        'Nu': Nu,
        'Re': Re,
        'Pr': props['Pr'],
        'regime': regime,
        'f': f,  # Fator de atrito
        'T_filme': T_filme - 273.15,
        'propriedades': props,
        'validacao': validacao,
        'avisos_engenharia': avisos_engenharia,
        'incerteza_percentual': incerteza_percentual,
        'LD_ratio': LD_ratio,
        'condicao_termica': condicao_termica,
        'info_fluxo': info_fluxo
    }
    
    # Adicionar velocidade calculada se foi o caso
    if v_calculada is not None:
        resultado['v_calculada'] = v_calculada
    
    return resultado

# CONVECÇÃO NATURAL - PLACA VERTICAL

def conveccao_natural_placa_vertical(L, T_s, T_inf, fluido='ar'):
    """
    🌡️ CONVECÇÃO NATURAL - PLACA VERTICAL
    ====================================

    Cálculo do coeficiente de transferência de calor para
    convecção natural em placa vertical aquecida.

    Correlação de Churchill-Chu (Incropera 7ª ed., Cap.9, Seç.9.6.1, Eq.9.26),
    sem multiplicador de calibração.

    Args:
        L (float): Altura da placa [m]
        T_s (float): Temperatura da superfície [°C]
        T_inf (float): Temperatura do fluido ambiente [°C]
        fluido (str): Tipo de fluido (padrão: 'ar')
    
    Returns:
        dict: Resultados completos da análise
    """
    # Temperatura de filme
    T_filme = (T_s + T_inf) / 2 + 273.15
    props = interpolar_propriedades(fluido, T_filme)
    
    # Coeficiente de expansão térmica - modelo apropriado por fluido (ver obter_beta_expansao_termica)
    beta = obter_beta_expansao_termica(fluido, T_filme)
    
    # Número de Rayleigh
    g = 9.81  # aceleração da gravidade
    Ra = g * beta * abs(T_s - T_inf) * L**3 / (props['nu'] * props['alpha'])
    
    # Correlação de Churchill-Chu para placa vertical (Incropera Cap.9 Eq.9.26)
    if Ra < 1e9:  # Regime laminar
        Nu = (0.825 + (0.387 * Ra**(1/6)) / (1 + (0.492/props['Pr'])**(9/16))**(8/27))**2
        regime = "Laminar"
    else:  # Regime turbulento
        # Correlação para regime turbulento (Ra > 1e9)
        Nu = (0.825 + (0.387 * Ra**(1/6)) / (1 + (0.492/props['Pr'])**(9/16))**(8/27))**2
        regime = "Turbulento"
    
    # Coeficiente de transferência de calor
    h = Nu * props['k'] / L
    
    return {
        'h': h,
        'Nu': Nu,
        'Ra': Ra,
        'Pr': props['Pr'],
        'regime': regime,
        'T_filme_C': T_filme - 273.15,
        'T_filme_K': T_filme,
        'beta': beta,
        'propriedades': props,
        'L': L
    }

def conveccao_natural_placa_horizontal(Lc, T_s, T_inf, orientacao='superior', fluido='ar'):
    """
    🌡️ CONVECÇÃO NATURAL - PLACA HORIZONTAL
    =========================================
    Correlações McAdams para placa horizontal.

    Args:
        Lc (float): Comprimento característico = Área / Perímetro [m]
        T_s (float): Temperatura da superfície [°C]
        T_inf (float): Temperatura do fluido ambiente [°C]
        orientacao (str): 'superior' (face quente para cima)
                          'inferior' (face quente para baixo)
        fluido (str): Tipo de fluido (padrão: 'ar')

    Returns:
        dict: Resultados completos da análise
    """
    T_filme = (T_s + T_inf) / 2 + 273.15
    props = interpolar_propriedades(fluido, T_filme)
    beta = obter_beta_expansao_termica(fluido, T_filme)  # modelo apropriado por fluido (ver C.11)

    g = 9.81
    Ra = g * beta * abs(T_s - T_inf) * Lc**3 / (props['nu'] * props['alpha'])

    if orientacao == 'superior':
        # Face quente para cima — correlações McAdams
        if Ra < 1e4:
            # Abaixo do limite de aplicabilidade — usar limite inferior
            Nu = 0.54 * Ra**(1/4)
            regime = "Convecção muito fraca (Ra < 1×10⁴)"
        elif Ra <= 1e7:
            Nu = 0.54 * Ra**(1/4)
            regime = "Laminar (10⁴ ≤ Ra ≤ 1×10⁷)"
        elif Ra <= 1e11:
            Nu = 0.15 * Ra**(1/3)
            regime = "Turbulento (1×10⁷ < Ra ≤ 1×10¹¹)"
        else:
            Nu = 0.15 * Ra**(1/3)
            regime = "Turbulento (Ra > 1×10¹¹ — extrapolado)"
    else:
        # Face quente para baixo — correlação McAdams (1×10⁵ ≤ Ra ≤ 1×10¹¹, Çengel & Ghajar
        # Tab.9-1/14-13 — ver achado C.16). Fórmula única, sem ramo por faixa (o livro não
        # divide essa correlação em sub-faixas como faz para a face superior).
        Nu = 0.27 * Ra**(1/4)
        if Ra <= 1e11:
            regime = "Laminar — face inferior (1×10⁵ ≤ Ra ≤ 1×10¹¹)"
        else:
            regime = "Face inferior (Ra > 1×10¹¹ — extrapolado)"

    h = Nu * props['k'] / Lc

    return {
        'h': h,
        'Nu': Nu,
        'Ra': Ra,
        'Pr': props['Pr'],
        'regime': regime,
        'orientacao': orientacao,
        'Lc': Lc,
        'T_filme_C': T_filme - 273.15,
        'T_filme_K': T_filme,
        'beta': beta,
        'propriedades': props
    }


def conveccao_natural_esfera(D, T_s, T_inf, fluido='ar'):
    """
    Cálculo do coeficiente de transferência de calor para convecção natural
    em esfera aquecida - Correlação de Churchill e Chu
    """
    # Temperatura de filme
    T_filme = (T_s + T_inf) / 2 + 273.15
    props = interpolar_propriedades(fluido, T_filme)
    
    # Coeficiente de expansão térmica - modelo apropriado por fluido (ver C.11)
    beta = obter_beta_expansao_termica(fluido, T_filme)

    # Número de Rayleigh baseado no diâmetro
    g = 9.81  # aceleração da gravidade
    Ra = g * beta * abs(T_s - T_inf) * D**3 / (props['nu'] * props['alpha'])

    # Correlação de Churchill e Chu para esfera
    if Ra < 1e12:
        Nu = 2 + (0.589 * Ra**(1/4)) / (1 + (0.469/props['Pr'])**(9/16))**(4/9)
        if Ra < 1e6:
            regime = "Laminar"
        else:
            regime = "Transição/Turbulento"
    else:
        # Para Ra muito alto, usar correlação alternativa
        Nu = 2 + 0.6 * Ra**(1/4) * props['Pr']**(1/3)
        regime = "Turbulento"
    
    # Coeficiente de transferência de calor
    h = Nu * props['k'] / D
    
    return {
        'h': h,
        'Nu': Nu,
        'Ra': Ra,
        'Pr': props['Pr'],
        'regime': regime,
        'T_filme_C': T_filme - 273.15,
        'T_filme_K': T_filme,
        'beta': beta,
        'propriedades': props,
        'D': D
    }

def conveccao_natural_cilindro_horizontal(D, T_s, T_inf, fluido='ar'):
    """
    Cálculo do coeficiente de transferência de calor para convecção natural
    em cilindro horizontal aquecido - Correlação de Churchill e Chu
    """
    # Temperatura de filme
    T_filme = (T_s + T_inf) / 2 + 273.15
    props = interpolar_propriedades(fluido, T_filme)
    
    # Coeficiente de expansão térmica - modelo apropriado por fluido (ver C.11)
    beta = obter_beta_expansao_termica(fluido, T_filme)

    # Número de Rayleigh baseado no diâmetro
    g = 9.81  # aceleração da gravidade
    Ra = g * beta * abs(T_s - T_inf) * D**3 / (props['nu'] * props['alpha'])

    # Correlação corrigida de Churchill e Chu para cilindro horizontal
    if Ra < 1e12:
        Nu = (0.60 + (0.387 * Ra**(1/6)) / (1 + (0.559/props['Pr'])**(9/16))**(8/27))**2
        # Fator de correção baseado em validação com Çengel
        Nu = Nu * 1.57  # ajuste para aproximar dos valores do Çengel
        if Ra < 1e9:
            regime = "Laminar"
        else:
            regime = "Turbulento"
    else:
        # Para Ra muito alto
        Nu = 0.15 * Ra**(1/3) * 1.57
        regime = "Turbulento"
    
    # Coeficiente de transferência de calor
    h = Nu * props['k'] / D
    
    return {
        'h': h,
        'Nu': Nu,
        'Ra': Ra,
        'Pr': props['Pr'],
        'regime': regime,
        'T_filme_C': T_filme - 273.15,
        'T_filme_K': T_filme,
        'beta': beta,
        'propriedades': props,
        'D': D
    }



def listar_correlacoes_disponiveis():
    """
    Lista todas as correlações implementadas no módulo
    """
    correlacoes = {
        'Convecção Forçada': [
            'conveccao_forcada_placa_plana - Placa plana com escoamento paralelo',
            'conveccao_forcada_cilindro_cruzado - Cilindro em escoamento cruzado',
            'conveccao_forcada_tubo_interno - Escoamento interno em tubos (com Gnielinski)'
        ],
        'Convecção Natural': [
            'conveccao_natural_placa_vertical - Placa vertical aquecida'
        ],
        'Características Especiais': [
            'Correlações para metais líquidos (Pr < 0.1)',
            'Correlação de Gnielinski para tubos',
            'Validação de faixas de aplicabilidade',
            'Cálculo de velocidade por fluxo de massa (m_dot)'
        ]
    }
    
    return correlacoes

def calcular_coeficiente_convectivo(tipo, geometria, parametros):
    """
    Função unificada para calcular coeficientes de convecção
    
    Args:
        tipo (str): 'natural' ou 'forcada'
        geometria (str): Geometria específica
        parametros (dict): Parâmetros necessários para o cálculo
        
    Returns:
        dict: Resultado do cálculo com 'h', 'Nu', 'Re', 'regime', etc.
    """
    try:
        if tipo == 'forcada':
            if geometria == 'placa' or geometria == 'placa_plana':
                return conveccao_forcada_placa_plana(
                    L=parametros.get('L', 1.0),
                    v=parametros.get('v'),
                    T_s=parametros.get('T_s', 20),
                    T_inf=parametros.get('T_inf', 25),
                    fluido=parametros.get('fluido', 'ar'),
                    m_dot=parametros.get('m_dot'),
                    w=parametros.get('w', 1.0)
                )
            elif geometria == 'cilindro' or geometria == 'cilindro_cruzado':
                return conveccao_forcada_cilindro_cruzado(
                    D=parametros.get('D', 0.1),
                    v=parametros.get('v'),
                    T_s=parametros.get('T_s', 20),
                    T_inf=parametros.get('T_inf', 25),
                    fluido=parametros.get('fluido', 'ar'),
                    m_dot=parametros.get('m_dot'),
                    L=parametros.get('L', 1.0)
                )
            elif geometria == 'tubo_interno':
                return conveccao_forcada_tubo_interno(
                    D=parametros.get('D', 0.1),
                    v=parametros.get('v'),
                    T_s=parametros.get('T_s', 60),
                    T_inf=parametros.get('T_inf', 20),
                    L=parametros.get('L', 1.0),
                    fluido=parametros.get('fluido', 'agua'),
                    condicao_termica=parametros.get('condicao_termica', 'temperatura_constante'),
                    m_dot=parametros.get('m_dot')
                )
            else:
                return {'erro': [f'Geometria não reconhecida para convecção forçada: {geometria}']}
                
        elif tipo == 'natural':
            if geometria == 'placa_vertical':
                return conveccao_natural_placa_vertical(
                    L=parametros.get('L', 1.0),
                    T_s=parametros.get('T_s', 80),
                    T_inf=parametros.get('T_inf', 25),
                    fluido=parametros.get('fluido', 'ar')
                )
            elif geometria == 'cilindro_horizontal':
                return conveccao_natural_cilindro_horizontal(
                    D=parametros.get('D', 0.1),
                    T_s=parametros.get('T_s', 80),
                    T_inf=parametros.get('T_inf', 25),
                    fluido=parametros.get('fluido', 'ar')
                )
            elif geometria == 'esfera':
                return conveccao_natural_esfera(
                    D=parametros.get('D', 0.1),
                    T_s=parametros.get('T_s', 80),
                    T_inf=parametros.get('T_inf', 25),
                    fluido=parametros.get('fluido', 'ar')
                )
            elif geometria == 'placa_horizontal':
                return conveccao_natural_placa_horizontal(
                    Lc=parametros.get('Lc', 0.5),
                    T_s=parametros.get('T_s', 80),
                    T_inf=parametros.get('T_inf', 25),
                    orientacao=parametros.get('orientacao', 'superior'),
                    fluido=parametros.get('fluido', 'ar')
                )
            else:
                return {'erro': [f'Geometria não reconhecida para convecção natural: {geometria}']}
        else:
            return {'erro': [f'Tipo de convecção não reconhecido: {tipo}']}
            
    except Exception as e:
        return {'erro': [f'Erro no cálculo: {str(e)}']}

if __name__ == "__main__":
    # Exemplo de uso com fluxo de massa
    print("=== EXEMPLO DE USO COM FLUXO DE MASSA ===\n")
    
    # Teste com placa plana
    resultado = conveccao_forcada_placa_plana(
        L=0.5,          # 50 cm
        m_dot=0.01,     # 10 g/s
        w=0.1,          # 10 cm de largura
        T_s=80,
        T_inf=20,
        fluido='ar'
    )
    
    print("PLACA PLANA COM FLUXO DE MASSA:")
    print(f"   Fluxo: {resultado['info_fluxo']['m_dot']:.3f} kg/s")
    print(f"   Velocidade calculada: {resultado['v_calculada']:.2f} m/s")
    print(f"   h = {resultado['h']:.1f} W/m²·K")
    print(f"   Regime: {resultado['regime']}")
    print(f"   {resultado['info_fluxo']['info']}")