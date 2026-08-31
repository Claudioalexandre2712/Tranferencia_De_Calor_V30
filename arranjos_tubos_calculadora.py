import numpy as np
import math


FATORES_FILEIRAS = {
    'inline': {1: 0.70, 2: 0.80, 3: 0.86, 4: 0.90, 5: 0.93, 7: 0.96, 10: 0.98, 13: 0.99},
    'staggered': {1: 0.64, 2: 0.76, 3: 0.84, 4: 0.89, 5: 0.93, 7: 0.96, 10: 0.98, 13: 0.99}
}

def obter_correlacao_zukauskas(arranjo, Re_D):
    """
    Obtém os parâmetros C e n da correlação de Zukauskas baseado na Tabela 7-2
    
    Nu_D = C * Re_D^n * Pr^0.36 * (Pr/Pr_s)^0.25
    
    Args:
        arranjo (str): 'inline' ou 'staggered'
        Re_D (float): Número de Reynolds baseado no diâmetro
        
    Returns:
        tuple: (C, n) parâmetros da correlação
    """
    if arranjo == 'inline':
        #Tabela 7-2
        if Re_D < 100:
            return 0.9, 0.4  # Nu_D = 0.9 * Re_D^0.4 * Pr^0.36 * (Pr/Pr_s)^0.25
        elif Re_D < 1000:
            return 0.52, 0.5  # Nu_D = 0.52 * Re_D^0.5 * Pr^0.36 * (Pr/Pr_s)^0.25
        elif Re_D < 2e5:
            return 0.27, 0.63  # Nu_D = 0.27 * Re_D^0.63 * Pr^0.36 * (Pr/Pr_s)^0.25
        else:  # Re_D >= 2e5
            return 0.033, 0.8  # Nu_D = 0.033 * Re_D^0.8 * Pr^0.4 * (Pr/Pr_s)^0.25
    
    else:  
        # Arranjo alternado (escalonado) - Tabela 7-2
        if Re_D < 500:
            return 1.04, 0.4  # Nu_D = 1.04 * Re_D^0.4 * Pr^0.36 * (Pr/Pr_s)^0.25
        elif Re_D < 1000:
            return 0.71, 0.5  # Nu_D = 0.71 * Re_D^0.5 * Pr^0.36 * (Pr/Pr_s)^0.25
        elif Re_D < 2e5:
            # Para este regime, precisamos da razão S_T/S_L
            return 0.35, 0.6  # Nu_D = 0.35 * (S_T/S_L)^0.2 * Re_D^0.6 * Pr^0.36 * (Pr/Pr_s)^0.25
        else:  # Re_D >= 2e5
            return 0.031, 0.8  # Nu_D = 0.031 * (S_T/S_L)^0.2 * Re_D^0.8 * Pr^0.4 * (Pr/Pr_s)^0.25

def obter_fator_fileiras(arranjo, N_fileiras):
    """
    Obtém fator de correção para número de fileiras baseado na Tabela 7-3
    
    Args:
        arranjo (str): 'inline' ou 'staggered'
        N_fileiras (int): Número de fileiras
        
    Returns:
        float: Fator de correção F_N
    """
    fatores = FATORES_FILEIRAS[arranjo]
    
    # Se o número exato está na tabela
    if N_fileiras in fatores:
        return fatores[N_fileiras]
    
    # Interpolação linear para valores intermediários
    fileiras_ordenadas = sorted(fatores.keys())
    
    if N_fileiras < fileiras_ordenadas[0]:
        return fatores[fileiras_ordenadas[0]]
    elif N_fileiras > fileiras_ordenadas[-1]:
        return fatores[fileiras_ordenadas[-1]]
    
    # Encontrar pontos para interpolação
    for i in range(len(fileiras_ordenadas) - 1):
        if fileiras_ordenadas[i] <= N_fileiras <= fileiras_ordenadas[i + 1]:
            x1, x2 = fileiras_ordenadas[i], fileiras_ordenadas[i + 1]
            y1, y2 = fatores[x1], fatores[x2]
            # Interpolação linear
            return y1 + (y2 - y1) * (N_fileiras - x1) / (x2 - x1)
    
    return 1.0  # Fallback



def arranjo_tubos_zukauskas(D, S_T, S_L, v, T_s, T_inf, fluido='ar', arranjo='inline', N_fileiras=10):
    """
    Calcula coeficiente de convecção para arranjos de tubos usando correlação de Zukauskas
    
    Correlação geral:
    Nu = C1 * Re_D^m * Pr^0.36 * (Pr/Pr_s)^0.25 * F_N
    
    onde:
    - C1 e m dependem da geometria e arranjo
    - F_N é fator de correção para número de fileiras
    - Re_D baseado na velocidade máxima no banco
    
    Args:
        D (float): Diâmetro dos tubos [m]
        S_T (float): Espaçamento transversal [m]
        S_L (float): Espaçamento longitudinal [m]
        v (float): Velocidade do fluido na entrada [m/s]
        T_s (float): Temperatura da superfície dos tubos [°C]
        T_inf (float): Temperatura do fluido [°C]
        fluido (str): Tipo de fluido
        arranjo (str): 'inline' ou 'staggered'
        N_fileiras (int): Número de fileiras de tubos
        
    Returns:
        dict: {h, Nu, Re_max, velocidade_max, fator_correcao, regime}
    """
    from conveccao_calculadora import interpolar_propriedades
    
    # Temperatura de filme
    T_filme = (T_s + T_inf) / 2 + 273.15
    props = interpolar_propriedades(fluido, T_filme)
    
    # Razões geométricas
    ST_D = S_T / D
    SL_D = S_L / D
    
    # Velocidade máxima no banco de tubos
    if arranjo == 'inline':
        # Para arranjo em linha
        A_min = S_T - D  # Área mínima entre tubos
        v_max = v * S_T / A_min
    else:  # staggered
        # Para arranjo alternado
        S_D = math.sqrt(S_L**2 + (S_T/2)**2)  # Espaçamento diagonal
        if S_D < S_T:
            A_min = S_D - D
        else:
            A_min = S_T - D
        v_max = v * S_T / A_min
    
    # Número de Reynolds baseado na velocidade máxima
    Re_max = props['rho'] * v_max * D / props['mu']
    
    # Obter parâmetros da correlação de Zukauskas (Tabela 7-2)
    C, n = obter_correlacao_zukauskas(arranjo, Re_max)
    
    # Fator de correção para número de fileiras (Tabela 7-3)
    F_N = obter_fator_fileiras(arranjo, N_fileiras)
    
    # Determinar regime de escoamento
    if Re_max < 100:
        regime = "Laminar baixo"
    elif Re_max < 1000:
        regime = "Laminar"
    elif Re_max < 10000:
        regime = "Transição"
    elif Re_max < 2e5:
        regime = "Turbulento"
    else:
        regime = "Turbulento alto"
    
    # Correlação de Zukauskas - Tabela 7-2
    # Nu_D = C * Re_D^n * Pr^0.36 * (Pr/Pr_s)^0.25 * F_N
    
    # Para arranjo alternado em regime 1000-2x10^5, incluir fator (S_T/S_L)^0.2
    if arranjo == 'staggered' and 1000 <= Re_max < 2e5:
        ST_SL_ratio = (S_T / S_L)
        fator_geometrico = ST_SL_ratio**0.2
        Nu = C * fator_geometrico * Re_max**n * props['Pr']**0.36 * F_N
    elif arranjo == 'staggered' and Re_max >= 2e5:
        ST_SL_ratio = (S_T / S_L)
        fator_geometrico = ST_SL_ratio**0.2
        Nu = C * fator_geometrico * Re_max**n * props['Pr']**0.4 * F_N  # Pr^0.4 para Re > 2x10^5
    else:
        # Arranjo em linha ou arranjo alternado em baixo Reynolds
        if arranjo == 'inline' and Re_max >= 2e5:
            Nu = C * Re_max**n * props['Pr']**0.4 * F_N  # Pr^0.4 para Re > 2x10^5
        else:
            Nu = C * Re_max**n * props['Pr']**0.36 * F_N  # Pr^0.36 padrão
    
    # Coeficiente de transferência de calor
    h = Nu * props['k'] / D
    
    return {
        'h': h,
        'Nu': Nu,
        'Re_max': Re_max,
        'velocidade_max': v_max,
        'velocidade_entrada': v,
        'ST_D': ST_D,
        'SL_D': SL_D,
        'ST_SL': S_T / S_L,
        'C': C,
        'n': n,
        'fator_fileiras': F_N,
        'arranjo': arranjo,
        'regime': regime,
        'correlacao': 'Zukauskas Tabela 7-2',
        'T_filme': T_filme - 273.15,
        'propriedades': props
    }

def arranjo_tubos_grimison(D, S_T, S_L, v, T_s, T_inf, fluido='ar', arranjo='inline'):
    """
    Correlação de Grimison para arranjos de tubos (mais simples)
    
    Nu = C * Re_D^n * Pr^(1/3)
    
    Args:
        D, S_T, S_L, v, T_s, T_inf, fluido, arranjo: mesmos parâmetros da função anterior
        
    Returns:
        dict: Resultados similares à correlação de Zukauskas
    """
    from conveccao_calculadora import interpolar_propriedades
    
    # Temperatura de filme
    T_filme = (T_s + T_inf) / 2 + 273.15
    props = interpolar_propriedades(fluido, T_filme)
    
    # Velocidade máxima (simplificada)
    if arranjo == 'inline':
        v_max = v * S_T / (S_T - D)
    else:  # staggered
        v_max = v * S_T / (S_T - D) * 1.2  # Fator de correção para alternado
    
    # Reynolds
    Re_max = props['rho'] * v_max * D / props['mu']
    
    # Constantes de Grimison (simplificadas)
    if arranjo == 'inline':
        if Re_max < 1000:
            C, n = 0.27, 0.63
        else:
            C, n = 0.033, 0.8
    else:  # staggered
        if Re_max < 1000:
            C, n = 0.35, 0.60
        else:
            C, n = 0.031, 0.8
    
    # Correlação de Grimison
    Nu = C * Re_max**n * props['Pr']**(1/3)
    h = Nu * props['k'] / D
    
    return {
        'h': h,
        'Nu': Nu,
        'Re_max': Re_max,
        'velocidade_max': v_max,
        'C': C,
        'n': n,
        'arranjo': arranjo,
        'regime': "Grimison",
        'T_filme': T_filme - 273.15,
        'propriedades': props
    }


def calcular_arranjo_tubos(tipo_correlacao, parametros):
    """
    Função principal para cálculos de arranjos de tubos
    
    Args:
        tipo_correlacao (str): 'zukauskas' ou 'grimison'
        parametros (dict): Parâmetros de entrada (D, S_T, S_L em metros)
        
    Returns:
        dict: Resultados do cálculo
    """
    try:
        # Usar valores diretos em metros
        D_m = parametros['D']
        ST_m = parametros['S_T']
        SL_m = parametros['S_L']
        
        if tipo_correlacao == 'zukauskas':
            return arranjo_tubos_zukauskas(
                D_m, ST_m, SL_m,
                parametros['v'], parametros['T_s'], parametros['T_inf'],
                parametros['fluido'], parametros['arranjo'],
                parametros.get('N_fileiras', 10)
            )
        elif tipo_correlacao == 'grimison':
            return arranjo_tubos_grimison(
                D_m, ST_m, SL_m,
                parametros['v'], parametros['T_s'], parametros['T_inf'],
                parametros['fluido'], parametros['arranjo']
            )
        else:
            return {'erro': ['Tipo de correlação não reconhecido']}
            
    except Exception as e:
        return {'erro': [f'Erro no cálculo: {str(e)}']}

if __name__ == "__main__":
    print("🔧 TESTE DOS ARRANJOS DE TUBOS - CAPÍTULO 8")
    print("="*50)
    
    # Exemplo típico: Trocador de calor com tubos alternados
    parametros = {
        'D': 0.025,        # Diâmetro 0.025 m (25 mm)
        'S_T': 0.050,      # Espaçamento transversal 0.050 m (50 mm)
        'S_L': 0.043,      # Espaçamento longitudinal 0.043 m (43 mm)
        'v': 6.0,          # Velocidade 6 m/s
        'T_s': 80.0,       # Temperatura dos tubos 80°C
        'T_inf': 25.0,     # Temperatura do ar 25°C
        'fluido': 'ar',
        'arranjo': 'staggered',
        'N_fileiras': 8
    }
    
    print("\n1. Correlação de Zukauskas - Arranjo Alternado:")
    resultado = calcular_arranjo_tubos('zukauskas', parametros)
    if 'erro' not in resultado:
        print(f"   h = {resultado['h']:.1f} W/m²·K")
        print(f"   Nu = {resultado['Nu']:.1f}")
        print(f"   Re_max = {resultado['Re_max']:.0f}")
        print(f"   v_max = {resultado['velocidade_max']:.1f} m/s")
        print(f"   Regime: {resultado['regime']}")
    else:
        print(f"   Erro: {resultado['erro']}")
    
    # Testar arranjo em linha
    parametros['arranjo'] = 'inline'
    print("\n2. Correlação de Zukauskas - Arranjo em Linha:")
    resultado = calcular_arranjo_tubos('zukauskas', parametros)
    if 'erro' not in resultado:
        print(f"   h = {resultado['h']:.1f} W/m²·K")
        print(f"   Nu = {resultado['Nu']:.1f}")
        print(f"   v_max = {resultado['velocidade_max']:.1f} m/s")
        print(f"   Regime: {resultado['regime']}")