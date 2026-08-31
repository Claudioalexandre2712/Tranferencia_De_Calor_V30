import numpy as np
import math

# ================================
# PROPRIEDADES DE SATURAÇÃO DOS FLUIDOS
# ================================

PROPRIEDADES_SATURACAO = {
    'agua': {
        'nome': 'Água',
        'propriedades': {
            # Temperatura (°C): P_sat (Pa), rho_l (kg/m³), rho_v (kg/m³), 
            # h_fg (J/kg), mu_l (Pa·s), k_l (W/m·K), cp_l (J/kg·K), sigma (N/m), Pr_l
            100: {
                'P_sat': 101325, 'rho_l': 958.4, 'rho_v': 0.598, 'h_fg': 2257000,
                'mu_l': 2.82e-4, 'k_l': 0.679, 'cp_l': 4217, 'sigma': 0.0589, 'Pr_l': 1.75
            },
            110: {
                'P_sat': 143270, 'rho_l': 950.6, 'rho_v': 0.826, 'h_fg': 2230000,
                'mu_l': 2.58e-4, 'k_l': 0.684, 'cp_l': 4229, 'sigma': 0.0565, 'Pr_l': 1.59
            },
            120: {
                'P_sat': 198530, 'rho_l': 943.1, 'rho_v': 1.121, 'h_fg': 2202000,
                'mu_l': 2.38e-4, 'k_l': 0.686, 'cp_l': 4244, 'sigma': 0.0540, 'Pr_l': 1.47
            },
            150: {
                'P_sat': 475800, 'rho_l': 917.0, 'rho_v': 2.547, 'h_fg': 2114000,
                'mu_l': 1.86e-4, 'k_l': 0.685, 'cp_l': 4313, 'sigma': 0.0466, 'Pr_l': 1.17
            }
        }
    },
    'r134a': {
        'nome': 'Refrigerante R-134a',
        'propriedades': {
            # Propriedades do R-134a em saturação
            -10: {
                'P_sat': 200900, 'rho_l': 1374, 'rho_v': 8.15, 'h_fg': 216800,
                'mu_l': 4.9e-4, 'k_l': 0.105, 'cp_l': 1267, 'sigma': 0.0152, 'Pr_l': 5.9
            },
            0: {
                'P_sat': 292800, 'rho_l': 1334, 'rho_v': 11.31, 'h_fg': 206200,
                'mu_l': 3.6e-4, 'k_l': 0.098, 'cp_l': 1291, 'sigma': 0.0132, 'Pr_l': 4.7
            },
            20: {
                'P_sat': 572100, 'rho_l': 1255, 'rho_v': 20.67, 'h_fg': 184400,
                'mu_l': 2.3e-4, 'k_l': 0.086, 'cp_l': 1351, 'sigma': 0.0094, 'Pr_l': 3.6
            }
        }
    },
    'amonia': {
        'nome': 'Amônia (NH₃)',
        'propriedades': {
            -10: {
                'P_sat': 290800, 'rho_l': 665.1, 'rho_v': 2.16, 'h_fg': 1261000,
                'mu_l': 2.55e-4, 'k_l': 0.547, 'cp_l': 4463, 'sigma': 0.0204, 'Pr_l': 2.09
            },
            0: {
                'P_sat': 429600, 'rho_l': 639.4, 'rho_v': 3.08, 'h_fg': 1235000,
                'mu_l': 2.17e-4, 'k_l': 0.540, 'cp_l': 4467, 'sigma': 0.0180, 'Pr_l': 1.80
            },
            20: {
                'P_sat': 857500, 'rho_l': 594.4, 'rho_v': 5.96, 'h_fg': 1166000,
                'mu_l': 1.56e-4, 'k_l': 0.521, 'cp_l': 4476, 'sigma': 0.0137, 'Pr_l': 1.34
            }
        }
    }
}

def obter_propriedades_saturacao(fluido, temperatura):
    """
    Obtém propriedades de saturação por interpolação linear
    
    Args:
        fluido (str): Nome do fluido
        temperatura (float): Temperatura em °C
        
    Returns:
        dict: Propriedades de saturação interpoladas
    """
    if fluido not in PROPRIEDADES_SATURACAO:
        raise ValueError(f"Fluido '{fluido}' não encontrado na base de dados")
    
    props_db = PROPRIEDADES_SATURACAO[fluido]['propriedades']
    temperaturas = sorted(props_db.keys())
    
    # Se temperatura exata existe
    if temperatura in props_db:
        return props_db[temperatura].copy()
    
    # Extrapolação ou clamp para limites
    if temperatura < temperaturas[0]:
        return props_db[temperaturas[0]].copy()
    if temperatura > temperaturas[-1]:
        return props_db[temperaturas[-1]].copy()
    
    # Interpolação linear
    for i in range(len(temperaturas) - 1):
        T1, T2 = temperaturas[i], temperaturas[i + 1]
        if T1 <= temperatura <= T2:
            props1 = props_db[T1]
            props2 = props_db[T2]
            fator = (temperatura - T1) / (T2 - T1)
            
            props_interpoladas = {}
            for prop in props1:
                props_interpoladas[prop] = props1[prop] + fator * (props2[prop] - props1[prop])
            
            return props_interpoladas
    
    # Fallback
    return props_db[temperaturas[0]].copy()

# ================================
# CONDENSAÇÃO EM FILME
# ================================

def condensacao_placa_vertical(L, T_sat, T_parede, fluido='agua'):
    """
    Calcula coeficiente de condensação em filme para placa vertical
    
    Correlação de Nusselt modificada:
    Nu = 0.943 * [g * rho_l * (rho_l - rho_v) * h_fg * L³ / (mu_l * k_l * (T_sat - T_parede))]^(1/4)
    
    Args:
        L (float): Altura da placa [m]
        T_sat (float): Temperatura de saturação [°C]
        T_parede (float): Temperatura da parede [°C]
        fluido (str): Tipo de fluido
        
    Returns:
        dict: {h, Nu, Re_filme, regime, propriedades}
    """
    # Propriedades de saturação
    props = obter_propriedades_saturacao(fluido, T_sat)
    
    # Diferença de temperatura
    Delta_T = abs(T_sat - T_parede)
    if Delta_T < 0.1:
        raise ValueError("Diferença de temperatura muito pequena para condensação")
    
    # Constantes físicas
    g = 9.81  # [m/s²]
    
    # Número de Nusselt para condensação em filme (Nusselt, 1916)
    numerador = g * props['rho_l'] * (props['rho_l'] - props['rho_v']) * props['h_fg'] * L**3
    denominador = props['mu_l'] * props['k_l'] * Delta_T
    
    Nu = 0.943 * (numerador / denominador)**(1/4)
    
    # Coeficiente de transferência de calor
    h = Nu * props['k_l'] / L
    
    # Número de Reynolds do filme
    Gamma = props['rho_l'] * g * L**3 / (3 * props['mu_l'])  # Vazão mássica por unidade de largura
    Re_filme = 4 * Gamma / props['mu_l']
    
    # Determinação do regime
    if Re_filme < 30:
        regime = "Filme laminar liso"
    elif Re_filme < 1800:
        regime = "Filme laminar ondulado"
    else:
        regime = "Filme turbulento"
    
    return {
        'h': h,
        'Nu': Nu,
        'Re_filme': Re_filme,
        'regime': regime,
        'Delta_T': Delta_T,
        'propriedades': props,
        'q_fluxo': h * Delta_T
    }

def condensacao_tubo_horizontal(D, T_sat, T_parede, fluido='agua'):
    """
    Calcula coeficiente de condensação em filme para tubo horizontal
    
    Correlação de Nusselt para cilindro:
    Nu = 0.729 * [g * rho_l * (rho_l - rho_v) * h_fg * D³ / (mu_l * k_l * (T_sat - T_parede))]^(1/4)
    
    Args:
        D (float): Diâmetro do tubo [m]
        T_sat (float): Temperatura de saturação [°C]
        T_parede (float): Temperatura da parede [°C]
        fluido (str): Tipo de fluido
        
    Returns:
        dict: {h, Nu, regime, propriedades}
    """
    # Propriedades de saturação
    props = obter_propriedades_saturacao(fluido, T_sat)
    
    # Diferença de temperatura
    Delta_T = abs(T_sat - T_parede)
    if Delta_T < 0.1:
        raise ValueError("Diferença de temperatura muito pequena para condensação")
    
    # Constantes físicas
    g = 9.81  # [m/s²]
    
    # Número de Nusselt para condensação em cilindro horizontal
    numerador = g * props['rho_l'] * (props['rho_l'] - props['rho_v']) * props['h_fg'] * D**3
    denominador = props['mu_l'] * props['k_l'] * Delta_T
    
    Nu = 0.729 * (numerador / denominador)**(1/4)
    
    # Coeficiente de transferência de calor
    h = Nu * props['k_l'] / D
    
    return {
        'h': h,
        'Nu': Nu,
        'regime': "Condensação em filme",
        'Delta_T': Delta_T,
        'propriedades': props,
        'q_fluxo': h * Delta_T
    }

# ================================
# EBULIÇÃO
# ================================

def ebulicao_nucleada_rohsenow(q_flux, T_sat, T_parede, fluido='agua', superficie='comercial'):
    """
    Calcula coeficiente de ebulição nucleada usando correlação de Rohsenow
    
    q" = mu_l * h_fg * [(g * (rho_l - rho_v) / sigma)]^(1/2) * 
         [(cp_l * (T_parede - T_sat)) / (C_sf * h_fg * Pr_l^n)]^3
    
    Args:
        q_flux (float): Fluxo de calor [W/m²]
        T_sat (float): Temperatura de saturação [°C]
        T_parede (float): Temperatura da parede [°C] 
        fluido (str): Tipo de fluido
        superficie (str): Tipo de superfície
        
    Returns:
        dict: {h, Delta_T_excesso, regime}
    """
    # Propriedades de saturação
    props = obter_propriedades_saturacao(fluido, T_sat)
    
    # Constantes de Rohsenow (C_sf) por fluido e superfície
    constantes_rohsenow = {
        'agua': {
            'comercial': {'C_sf': 0.013, 'n': 1.0},
            'polida': {'C_sf': 0.013, 'n': 1.0},
            'cromada': {'C_sf': 0.015, 'n': 1.0}
        },
        'r134a': {
            'comercial': {'C_sf': 0.0058, 'n': 1.7},
            'polida': {'C_sf': 0.0058, 'n': 1.7}
        }
    }
    
    if fluido not in constantes_rohsenow:
        # Valores padrão para fluidos não listados
        C_sf, n = 0.013, 1.0
    else:
        surf_data = constantes_rohsenow[fluido].get(superficie, constantes_rohsenow[fluido]['comercial'])
        C_sf, n = surf_data['C_sf'], surf_data['n']
    
    # Constantes físicas
    g = 9.81  # [m/s²]
    
    # Temperatura de excesso
    Delta_T_excesso = T_parede - T_sat
    
    if Delta_T_excesso <= 0:
        raise ValueError("Temperatura da parede deve ser maior que temperatura de saturação")
    
    # Correlação de Rohsenow
    termo1 = props['mu_l'] * props['h_fg']
    termo2 = (g * (props['rho_l'] - props['rho_v']) / props['sigma'])**(1/2)
    termo3 = (props['cp_l'] * Delta_T_excesso / (C_sf * props['h_fg'] * props['Pr_l']**n))**3
    
    q_calculado = termo1 * termo2 * termo3
    
    # Coeficiente de transferência de calor
    h = q_flux / Delta_T_excesso if Delta_T_excesso > 0 else 0
    
    # Determinação do regime
    if Delta_T_excesso < 5:
        regime = "Convecção natural"
    elif Delta_T_excesso < 30:
        regime = "Ebulição nucleada"
    elif Delta_T_excesso < 120:
        regime = "Transição"
    else:
        regime = "Ebulição em filme"
    
    return {
        'h': h,
        'Delta_T_excesso': Delta_T_excesso,
        'q_flux': q_flux,
        'q_calculado_rohsenow': q_calculado,
        'regime': regime,
        'C_sf': C_sf,
        'propriedades': props
    }

def ebulicao_filme_berenson(T_parede, T_sat, fluido='agua'):
    """
    Calcula coeficiente de ebulição em filme usando correlação de Berenson
    
    Para superfícies horizontais:
    Nu = 0.425 * [g * rho_v * (rho_l - rho_v) * h_fg' * L³ / (mu_v * k_v * (T_parede - T_sat))]^(1/4)
    
    onde h_fg' = h_fg + 0.4 * cp_v * (T_parede - T_sat)
    e L = [sigma / (g * (rho_l - rho_v))]^(1/2) (comprimento capilar)
    
    Args:
        T_parede (float): Temperatura da parede [°C]
        T_sat (float): Temperatura de saturação [°C]
        fluido (str): Tipo de fluido
        
    Returns:
        dict: {h, Nu, regime, L_capilar}
    """
    # Propriedades de saturação
    props = obter_propriedades_saturacao(fluido, T_sat)
    
    # Temperatura de excesso
    Delta_T = T_parede - T_sat
    
    if Delta_T <= 0:
        raise ValueError("Temperatura da parede deve ser maior que temperatura de saturação")
    
    # Propriedades do vapor (aproximação)
    # Para simplificação, usando propriedades do vapor em T_filme = (T_parede + T_sat)/2
    T_filme = (T_parede + T_sat) / 2
    
    # Propriedades do vapor (estimativas simplificadas)
    rho_v = props['rho_v']
    mu_v = props['mu_l'] * 0.1  # Aproximação: viscosidade do vapor ~10% da do líquido
    k_v = props['k_l'] * 0.1    # Aproximação: condutividade do vapor ~10% da do líquido
    cp_v = props['cp_l'] * 0.5  # Aproximação: cp do vapor ~50% do líquido
    
    # Entalpia modificada de vaporização
    h_fg_mod = props['h_fg'] + 0.4 * cp_v * Delta_T
    
    # Constantes físicas
    g = 9.81  # [m/s²]
    
    # Comprimento capilar
    L_capilar = (props['sigma'] / (g * (props['rho_l'] - rho_v)))**(1/2)
    
    # Correlação de Berenson
    numerador = g * rho_v * (props['rho_l'] - rho_v) * h_fg_mod * L_capilar**3
    denominador = mu_v * k_v * Delta_T
    
    Nu = 0.425 * (numerador / denominador)**(1/4)
    
    # Coeficiente de transferência de calor
    h = Nu * k_v / L_capilar
    
    return {
        'h': h,
        'Nu': Nu,
        'regime': "Ebulição em filme",
        'Delta_T': Delta_T,
        'L_capilar': L_capilar,
        'h_fg_modificado': h_fg_mod,
        'propriedades': props
    }

# ================================
# FUNÇÃO PRINCIPAL DE CÁLCULO
# ================================

def calcular_mudanca_fase(tipo, subtipo, parametros):
    """
    Função principal para cálculos de transferência de calor com mudança de fase
    
    Args:
        tipo (str): 'condensacao' ou 'ebulicao'
        subtipo (str): Geometria ou tipo específico
        parametros (dict): Parâmetros de entrada
        
    Returns:
        dict: Resultados do cálculo
    """
    try:
        if tipo == 'condensacao':
            if subtipo == 'placa_vertical':
                return condensacao_placa_vertical(
                    parametros['L'], parametros['T_sat'], 
                    parametros['T_parede'], parametros['fluido']
                )
            elif subtipo == 'tubo_horizontal':
                return condensacao_tubo_horizontal(
                    parametros['D'], parametros['T_sat'],
                    parametros['T_parede'], parametros['fluido']
                )

                
        elif tipo == 'ebulicao':
            if subtipo == 'nucleada':
                return ebulicao_nucleada_rohsenow(
                    parametros.get('q_flux', 100000), parametros['T_sat'],
                    parametros['T_parede'], parametros['fluido'],
                    parametros.get('superficie', 'comercial')
                )
            elif subtipo == 'filme':
                return ebulicao_filme_berenson(
                    parametros['T_parede'], parametros['T_sat'],
                    parametros['fluido']
                )


        
        return {'erro': ['Tipo ou subtipo não reconhecido']}
        
    except Exception as e:
        return {'erro': [f'Erro no cálculo: {str(e)}']}

if __name__ == "__main__":
    print("🔥 TESTE DAS CORRELAÇÕES DE MUDANÇA DE FASE")
    print("="*50)
    
    # Teste condensação
    print("\n1. Condensação em placa vertical - Água:")
    resultado = condensacao_placa_vertical(1.0, 100, 90, 'agua')
    print(f"   h = {resultado['h']:.1f} W/m²·K")
    print(f"   Nu = {resultado['Nu']:.1f}")
    print(f"   Regime: {resultado['regime']}")
    
    # Teste ebulição
    print("\n2. Ebulição nucleada - Água:")
    resultado = ebulicao_nucleada_rohsenow(100000, 100, 105, 'agua')
    print(f"   h = {resultado['h']:.1f} W/m²·K")
    print(f"   ΔT_excesso = {resultado['Delta_T_excesso']:.1f} °C")
    print(f"   Regime: {resultado['regime']}")