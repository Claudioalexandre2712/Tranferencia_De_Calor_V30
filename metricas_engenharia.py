
import math

# Base de dados centralizada e unificada de propriedades dos materiais (Incropera & Çengel)
MATERIAIS_DB = {
    'Alumínio': {
        'id': 1,
        'k': 240,       # W/m·K
        'rho': 2700,    # kg/m³
        'cp': 900,      # J/kg·K
        'custo': 2.5,   # $/kg
        'T_max': 500    # °C
    },
    'Cobre': {
        'id': 2,
        'k': 386,
        'rho': 8960,
        'cp': 385,
        'custo': 8.5,
        'T_max': 800
    },
    'Aço Inoxidável': {
        'id': 3,
        'k': 16,
        'rho': 7900,
        'cp': 500,
        'custo': 4.0,
        'T_max': 1000
    },
    'Bronze': {
        'id': 4,
        'k': 26,
        'rho': 8800,
        'cp': 380,
        'custo': 6.0,
        'T_max': 700
    },
    'Ferro Fundido': {
        'id': 5,
        'k': 52,
        'rho': 7200,
        'cp': 450,
        'custo': 1.2,
        'T_max': 600
    },
    'Prata': {
        'id': 6,
        'k': 429,
        'rho': 10500,
        'cp': 235,
        'custo': 500.0,
        'T_max': 960
    },
    'Ouro': {
        'id': 7,
        'k': 318,
        'rho': 19300,
        'cp': 129,
        'custo': 40000.0,
        'T_max': 1060
    },
    'Ferro': {
        'id': 8,
        'k': 80,
        'rho': 7870,
        'cp': 447,
        'custo': 1.5,
        'T_max': 900
    },
    'Níquel': {
        'id': 9,
        'k': 90,
        'rho': 8900,
        'cp': 444,
        'custo': 15.0,
        'T_max': 1400
    },
    'Chumbo': {
        'id': 10,
        'k': 34,
        'rho': 11340,
        'cp': 130,
        'custo': 2.0,
        'T_max': 320
    }
}

# Dicionário indexado por ID numérico para compatibilidade direta com app.py e templates
DICIONARIO_MATERIAIS_ID = {
    dados['id']: {'nome': nome, 'k': dados['k'], 'rho': dados['rho'], 'cp': dados['cp'], 'custo': dados['custo'], 'T_max': dados['T_max']}
    for nome, dados in MATERIAIS_DB.items()
}

from tipos_aletas_config import obter_tipo_aleta

def calcular_volume_aleta(tipo_aleta, l, t=None, w=None, D=None, r1=None, r2=None):
    """
    Calcula o volume da aleta baseado na geometria identificada pelo ID único (1 a 8).
    
    Returns:
        float: Volume em m³
    """
    tid = obter_tipo_aleta(tipo_aleta) or 1
    
    if tid == 1:  # Retangular Reta (w, L, t)
        if not (t and w and l): return 0
        return float(l) * float(t) * float(w)
        
    elif tid == 2:  # Triangular Reta (w, L, t)
        if not (t and w and l): return 0
        return 0.5 * float(l) * float(t) * float(w)
        
    elif tid == 3:  # Parabólica Reta (w, L, t)
        if not (t and w and l): return 0
        return (2.0 / 3.0) * float(l) * float(t) * float(w)
        
    elif tid == 4:  # Circular de Perfil Retangular (r1, r2, t)
        if not (r1 and r2 and t): return 0
        r1_v, r2_v, t_v = float(r1), float(r2), float(t)
        return math.pi * max(0.0, (r2_v**2 - r1_v**2)) * t_v
        
    elif tid == 5:  # Pino de Perfil Retangular / Cilíndrico Uniforme (D, L)
        if not (D and l): return 0
        D_v, l_v = float(D), float(l)
        return math.pi * (D_v / 2.0)**2 * l_v
        
    elif tid == 6:  # Pino Triangular / Cônica (D, L)
        if not (D and l): return 0
        D_v, l_v = float(D), float(l)
        return (1.0 / 3.0) * math.pi * (D_v / 2.0)**2 * l_v
        
    elif tid == 7:  # Pino Parabólico (D, L)
        if not (D and l): return 0
        D_v, l_v = float(D), float(l)
        return (1.0 / 5.0) * math.pi * (D_v / 2.0)**2 * l_v
        
    elif tid == 8:  # Pino Parabólico Ponta Arredondada (D, L)
        if not (D and l): return 0
        D_v, l_v = float(D), float(l)
        return 0.5 * math.pi * (D_v / 2.0)**2 * l_v
        
    return 0

def calcular_area_superficial(tipo_aleta, l, t=None, w=None, D=None, r1=None, r2=None):
    """
    Calcula a área superficial total da aleta baseada na geometria identificada pelo ID único (1 a 8).
    
    Returns:
        float: Área superficial em m²
    """
    tid = obter_tipo_aleta(tipo_aleta) or 1
    
    if tid == 1:  # Retangular Reta (w, L, t)
        if not (t and w and l): return 0
        l_v, t_v, w_v = float(l), float(t), float(w)
        Lc = l_v + t_v / 2.0
        return 2.0 * w_v * Lc + 2.0 * t_v * l_v
        
    elif tid == 2:  # Triangular Reta (w, L, t)
        if not (t and w and l): return 0
        l_v, t_v, w_v = float(l), float(t), float(w)
        return 2.0 * w_v * math.sqrt(l_v**2 + (t_v / 2.0)**2) + w_v * t_v
        
    elif tid == 3:  # Parabólica Reta (w, L, t)
        if not (t and w and l): return 0
        l_v, t_v, w_v = float(l), float(t), float(w)
        C1 = math.sqrt(1.0 + (t_v / l_v)**2)
        return w_v * l_v * (C1 + (l_v / t_v) * math.log(t_v / l_v + C1))
        
    elif tid == 4:  # Circular de Perfil Retangular (r1, r2, t)
        if not (r1 and r2 and t): return 0
        r1_v, r2_v, t_v = float(r1), float(r2), float(t)
        r2c = r2_v + t_v / 2.0
        return 2.0 * math.pi * max(0.0, (r2c**2 - r1_v**2))
        
    elif tid == 5:  # Pino Retangular / Cilíndrico Uniforme (D, L)
        if not (D and l): return 0
        D_v, l_v = float(D), float(l)
        Lc = l_v + D_v / 4.0
        return math.pi * D_v * Lc
        
    elif tid == 6:  # Pino Triangular / Cônica (D, L)
        if not (D and l): return 0
        D_v, l_v = float(D), float(l)
        return (math.pi * D_v / 2.0) * math.sqrt(l_v**2 + (D_v / 2.0)**2)
        
    elif tid == 7:  # Pino Parabólico (D, L)
        if not (D and l): return 0
        D_v, l_v = float(D), float(l)
        C3 = 1.0 + 2.0 * (D_v / l_v)**2
        C4 = math.sqrt(1.0 + (D_v / l_v)**2)
        return (math.pi * l_v**3) / (8.0 * D_v) * (C3 * C4 - (l_v / (2.0 * D_v)) * math.log((2.0 * D_v * C4 / l_v + C3)))
        
    elif tid == 8:  # Pino Parabólico Ponta Arredondada (D, L)
        if not (D and l): return 0
        D_v, l_v = float(D), float(l)
        return (math.pi * D_v**4 / (96.0 * l_v**2)) * ((16.0 * (l_v / D_v)**2 + 1.0)**(1.5) - 1.0)
        
    return 0

def calcular_metricas_engenharia(tipo_aleta, h, k, l, t, w, D, r1, r2, T_b, T_inf, 
                                Q_aleta, A_aleta, eta_aleta, epsilon_a, material_nome="Alumínio"):
    """
    Calcula métricas simplificadas de engenharia
    
    Returns:
        dict: Dicionário com métricas essenciais
    """
    
    # Obter propriedades do material
    material = MATERIAIS_DB.get(material_nome, MATERIAIS_DB['Alumínio'])
    rho = material['rho']      # kg/m³
    custo_kg = material['custo']  # $/kg
    
    # Calcular volume e massa
    volume = calcular_volume_aleta(tipo_aleta, l, t, w, D, r1, r2)
    massa = volume * rho  # kg
    
    # Custo total da aleta ($)
    custo_total = massa * custo_kg
    
    # Razão custo-benefício (W/$)
    if custo_total > 0:
        razao_custo_beneficio = Q_aleta / custo_total
    else:
        razao_custo_beneficio = 0
    
    return {
        'volume': volume,
        'massa': massa,
        'custo_total': custo_total,
        'razao_custo_beneficio': razao_custo_beneficio,
        'material_properties': material
    }

def interpretar_metricas(metricas):
    """
    Gera interpretações simplificadas
    
    Returns:
        dict: Interpretações essenciais
    """
    
    interpretacoes = {
        'recomendacoes': [],
        'alertas': [],
        'pontos_fortes': []
    }
    
    # Análise da razão custo-benefício
    if metricas['razao_custo_beneficio'] > 10:
        interpretacoes['pontos_fortes'].append("Excelente relação custo-benefício")
    elif metricas['razao_custo_beneficio'] > 5:
        interpretacoes['pontos_fortes'].append("Boa relação custo-benefício")
    elif metricas['razao_custo_beneficio'] < 2:
        interpretacoes['alertas'].append("Baixa relação custo-benefício")
        interpretacoes['recomendacoes'].append("Considerar material mais econômico ou geometria otimizada")
    
    # Análise da massa da aleta
    if metricas['massa'] < 0.1:
        interpretacoes['pontos_fortes'].append("Aleta leve - facilita instalação")
    elif metricas['massa'] > 5:
        interpretacoes['alertas'].append("Aleta pesada - verificar suporte estrutural")
        interpretacoes['recomendacoes'].append("Considerar otimização da geometria para reduzir peso")
    
    return interpretacoes

print("OK Modulo de metricas de engenharia criado com sucesso!")