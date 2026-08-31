import numpy as np
import math
from conveccao_calculadora import interpolar_propriedades

def escoamento_interno_tubo_circular(parametros):
    """
    Calcula coeficiente de convecção para escoamento interno em tubo circular.
    
    Args:
        parametros (dict): {
            'D': diâmetro interno [m],
            'L': comprimento do tubo [m] (opcional),
            'v': velocidade média [m/s] OU 'm_dot': fluxo de massa [kg/s],
            'T_s': temperatura da parede [°C],
            'T_inf': temperatura do fluido de entrada [°C],
            'fluido': tipo de fluido,
            'condicao_termica': 'Ts_constante' ou 'qs_constante'
        }
        
    Returns:
        dict: Resultados completos incluindo h, Nu, Re, regime, etc.
    """
    
    # Extrair parâmetros
    D = parametros['D']
    L = parametros.get('L', 1.0)  # Comprimento padrão 1m
    T_s = parametros['T_s']
    T_inf = parametros['T_inf']
    fluido = parametros['fluido']
    condicao_termica = parametros.get('condicao_termica', 'Ts_constante')
    
    # Temperatura de filme para propriedades
    T_filme = (T_s + T_inf) / 2
    T_filme_K = T_filme + 273.15
    
    # Obter propriedades do fluido
    props = interpolar_propriedades(fluido, T_filme_K)
    
    # Calcular velocidade se fornecido fluxo de massa
    if 'm_dot' in parametros:
        from conveccao_calculadora import calcular_velocidade_por_fluxo_massa
        resultado_fluxo = calcular_velocidade_por_fluxo_massa(
            parametros['m_dot'], 'tubo_circular', fluido, T_filme_K, D=D
        )
        v = resultado_fluxo['v']
        info_fluxo = resultado_fluxo['geometria_info']
    else:
        v = parametros['v']
        info_fluxo = f"Velocidade fornecida: {v:.2f} m/s"
    
    # Número de Reynolds
    Re = props['rho'] * v * D / props['mu']
    
    # Número de Prandtl
    Pr = props['mu'] * props['cp'] / props['k']
    
    # Determinar regime de escoamento
    if Re < 2300:
        regime = 'Laminar'
        regime_codigo = 'laminar'
    elif Re < 4000:
        regime = 'Transição'
        regime_codigo = 'transicao'
    else:
        regime = 'Turbulento'
        regime_codigo = 'turbulento'
    
    # Calcular comprimentos de entrada
    L_h_laminar = 0.05 * Re * D  # Comprimento de entrada hidrodinâmico
    L_t_laminar = 0.05 * Re * Pr * D  # Comprimento de entrada térmico
    
    # Determinar se escoamento está completamente desenvolvido
    # Para turbulento: L_h ≈ 10D, L_t ≈ 10D (aproximação prática)
    L_entrada_hidro = L_h_laminar if regime_codigo == 'laminar' else 10 * D
    L_entrada_termo = L_t_laminar if regime_codigo == 'laminar' else 10 * D
    
    desenvolvido_hidro = L > L_entrada_hidro
    desenvolvido_termo = L > L_entrada_termo
    
    # Calcular Número de Nusselt baseado no regime e condição térmica
    if regime_codigo == 'laminar' and desenvolvido_termo:
        # Escoamento laminar completamente desenvolvido (Seções 8.3.2 e 8.3.3)
        if condicao_termica == 'Ts_constante':
            Nu = 3.66  # Eq. 8-61: Temperatura da parede constante
            correlacao = "Nu = 3.66 (Eq.8-61: Ts constante, laminar desenvolvido)"
        else:  # qs_constante
            Nu = 4.36  # Eq. 8-60: Fluxo de calor constante na parede
            correlacao = "Nu = 4.36 (Eq.8-60: qs constante, laminar desenvolvido)"
    
    elif regime_codigo == 'laminar' and not desenvolvido_termo:
        # Região de entrada laminar
        if condicao_termica == 'Ts_constante':
            # Correlação para região de entrada com Ts constante
            Nu_fd = 3.66
            Gz = Re * Pr * D / L  # Número de Graetz
            if Gz > 10:
                Nu = 1.86 * (Gz)**(1/3) * (props['mu']/props['mu'])**(0.14)
                correlacao = f"Nu = 1.86·Gz^(1/3) (Região entrada, Ts const), Gz={Gz:.1f}"
            else:
                Nu = Nu_fd
                correlacao = "Nu = 3.66 (Gz baixo, aproximação desenvolvido)"
        else:
            # qs constante na região de entrada
            Gz = Re * Pr * D / L
            if Gz > 10:
                Nu = 2.0 + 0.6 * (Gz)**(1/3)
                correlacao = f"Nu = 2.0 + 0.6·Gz^(1/3) (Região entrada, qs const), Gz={Gz:.1f}"
            else:
                Nu = 4.36
                correlacao = "Nu = 4.36 (Gz baixo, aproximação desenvolvido)"
    
    elif regime_codigo == 'turbulento':
        # Correlação de Gnielinski para escoamento turbulento (Eq. 8-71)
        # Faixa: 3000 ≤ Re ≤ 5×10⁶, 0.5 ≤ Pr ≤ 2000
        if 3000 <= Re <= 5e6 and 0.5 <= Pr <= 2000:
            # Fator de atrito para tubos lisos (Eq. 8-82)
            f = (0.790 * math.log(Re) - 1.64)**(-2)
            # Correlação de Gnielinski
            Nu = (f/8) * (Re - 1000) * Pr / (1 + 12.7 * (f/8)**0.5 * (Pr**(2/3) - 1))
            correlacao = f"Gnielinski (Eq.8-71): Nu = (f/8)(Re-1000)Pr/[1+12.7(f/8)^0.5(Pr^(2/3)-1)], f={f:.4f}"
        else:
            # Correlação de Dittus-Boelter como backup (Eq. 8-68)
            # Faixa: Re ≥ 10,000, 0.7 ≤ Pr ≤ 160
            if condicao_termica == 'Ts_constante' or 'aquecimento' in condicao_termica.lower():
                n = 0.4  # Aquecimento do fluido
            else:
                n = 0.3  # Resfriamento do fluido
            Nu = 0.023 * Re**0.8 * Pr**n
            correlacao = f"Dittus-Boelter (Eq.8-68): Nu = 0.023·Re^0.8·Pr^{n} (backup)"
    
    else:  # Transição
        # Interpolação entre laminar e turbulento
        Nu_lam = 3.66 if condicao_termica == 'Ts_constante' else 4.36
        
        # Calcular Nu turbulento usando Gnielinski ou Dittus-Boelter
        Re_turb = 4000
        if 3000 <= Re_turb <= 5e6 and 0.5 <= Pr <= 2000:
            f = (0.790 * math.log(Re_turb) - 1.64)**(-2)
            Nu_turb = (f/8) * (Re_turb - 1000) * Pr / (1 + 12.7 * (f/8)**0.5 * (Pr**(2/3) - 1))
        else:
            n = 0.4 if condicao_termica == 'Ts_constante' else 0.3
            Nu_turb = 0.023 * Re_turb**0.8 * Pr**n
        
        # Interpolação linear
        Nu = Nu_lam + (Nu_turb - Nu_lam) * (Re - 2300) / (4000 - 2300)
        correlacao = f"Interpolação transição: Nu = {Nu_lam:.2f} → {Nu_turb:.1f}"
    
    # Calcular coeficiente de convecção
    h = Nu * props['k'] / D
    
    # Informações sobre desenvolvimento do escoamento
    info_desenvolvimento = []
    if desenvolvido_hidro and desenvolvido_termo:
        info_desenvolvimento.append("Completamente desenvolvido (hidro + térmico)")
    else:
        if not desenvolvido_hidro:
            info_desenvolvimento.append(f"Região entrada hidrodinâmica (L_h={L_entrada_hidro*1000:.0f}mm)")
        if not desenvolvido_termo:
            info_desenvolvimento.append(f"Região entrada térmica (L_t={L_entrada_termo*1000:.0f}mm)")
    
    # Validações e avisos
    avisos = []
    
    if Re < 2300 and L/D < 10:
        avisos.append("AVISO: L/D baixo para escoamento laminar - considere efeitos de entrada")
    
    if Re > 10000 and L/D < 60:
        avisos.append("AVISO: L/D baixo para turbulento - escoamento pode não estar desenvolvido")
    
    if Pr < 0.6 or Pr > 160:
        avisos.append(f"AVISO: Pr = {Pr:.2f} fora da faixa típica (0.6-160)")
    
    return {
        'h': h,                           # Coeficiente de convecção [W/m²·K]
        'Nu': Nu,                         # Número de Nusselt
        'Re': Re,                         # Número de Reynolds  
        'Pr': Pr,                         # Número de Prandtl
        'regime': regime,                 # Regime de escoamento
        'v': v,                          # Velocidade [m/s]
        'f': locals().get('f', None),    # Fator de atrito (se calculado)
        'correlacao': correlacao,         # Correlação utilizada
        'condicao_termica': condicao_termica,
        'desenvolvido_hidro': desenvolvido_hidro,
        'desenvolvido_termo': desenvolvido_termo,
        'L_entrada_hidro': L_entrada_hidro*1000,  # mm
        'L_entrada_termo': L_entrada_termo*1000,  # mm
        'info_desenvolvimento': info_desenvolvimento,
        'info_fluxo': info_fluxo,
        'propriedades': {
            'rho': props['rho'],
            'mu': props['mu'],
            'k': props['k'],
            'cp': props['cp'],
            'T_filme': T_filme
        },
        'avisos': avisos
    }

# Função de teste
if __name__ == "__main__":
    # Teste exemplo do livro
    parametros_teste = {
        'D': 0.025,          # 25mm
        'L': 2.0,            # 2m
        'v': 1.0,            # 1 m/s
        'T_s': 80,           # 80°C
        'T_inf': 20,         # 20°C
        'fluido': 'ar',
        'condicao_termica': 'Ts_constante'
    }
    
    resultado = escoamento_interno_tubo_circular(parametros_teste)
    
    print("=== TESTE ESCOAMENTO INTERNO ===")
    print(f"h = {resultado['h']:.1f} W/m²·K")
    print(f"Nu = {resultado['Nu']:.1f}")
    print(f"Re = {resultado['Re']:.0f}")
    print(f"Regime: {resultado['regime']}")
    print(f"Correlação: {resultado['correlacao']}")