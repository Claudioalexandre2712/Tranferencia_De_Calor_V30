
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

def calcular_volume_aleta(tipo_aleta, l, t=None, w=None, D=None, r1=None, r2=None):
    """
    Calcula o volume da aleta baseado na geometria
    
    Returns:
        float: Volume em m³
    """
    
    if tipo_aleta in ["1)aletas retangulares retas", "2)aletas triangulares retas"]:
        if not (t and w):
            return 0
        if tipo_aleta == "1)aletas retangulares retas":
            volume = l * t * w  # V = L × t × w
        else:  # triangular
            volume = 0.5 * l * t * w  # V = 0.5 × L × t × w
            
    elif tipo_aleta == "3)aletas parabolicas retas":
        if not (t and w):
            return 0
        volume = (2/3) * l * t * w  # Aproximação parabólica
        
    elif tipo_aleta == "4)aletas circulares de perfil retangular":
        if not (r1 and r2 and t):
            return 0
        # Volume da seção anular
        volume = math.pi * (r2**2 - r1**2) * t
        
    elif tipo_aleta == "5)aletas de perfil retangular":
        if not D:
            return 0
        # Pino cilíndrico
        volume = math.pi * (D/2)**2 * l
        
    elif tipo_aleta in ["6)aletas de perfil triangular", "7)aletas de perfil parabolico"]:
        if not D:
            return 0
        if tipo_aleta == "6)aletas de perfil triangular":
            volume = (1/3) * math.pi * (D/2)**2 * l  # Cone
        else:  # parabólico
            volume = (1/2) * math.pi * (D/2)**2 * l  # Aproximação
            
    elif tipo_aleta == "8)aletas de pino de perfilparabolico (ponta arredondada)":
        if not D:
            return 0
        # Cilindro + semiesfera
        volume_cilindro = math.pi * (D/2)**2 * l
        volume_esfera = (2/3) * math.pi * (D/2)**3
        volume = volume_cilindro + volume_esfera
        
    else:
        volume = 0
    
    return volume

def calcular_area_superficial(tipo_aleta, l, t=None, w=None, D=None, r1=None, r2=None):
    """
    Calcula a área superficial total da aleta (incluindo base)
    
    Returns:
        float: Área superficial em m²
    """
    
    if tipo_aleta == "1)aletas retangulares retas":
        if not (t and w):
            return 0
        # 2 faces principais + 2 laterais + ponta
        area = 2 * l * w + 2 * l * t + t * w
        
    elif tipo_aleta == "2)aletas triangulares retas":
        if not (t and w):
            return 0
        # Aproximação para aleta triangular
        area = 2 * math.sqrt((l**2) + (w/2)**2) * w + l * t
        
    elif tipo_aleta == "3)aletas parabolicas retas":
        if not (t and w):
            return 0
        # Aproximação parabólica
        area = 2.1 * l * w + 2 * l * t + 0.5 * t * w
        
    elif tipo_aleta == "4)aletas circulares de perfil retangular":
        if not (r1 and r2 and t):
            return 0
        # Superfícies cilíndricas interna e externa + face anular
        area = 2 * math.pi * r2 * t + 2 * math.pi * r1 * t + math.pi * (r2**2 - r1**2)
        
    elif tipo_aleta == "5)aletas de perfil retangular":
        if not D:
            return 0
        # Superfície cilíndrica + base circular
        area = math.pi * D * l + math.pi * (D/2)**2
        
    elif tipo_aleta == "6)aletas de perfil triangular":
        if not D:
            return 0
        # Superfície cônica + base
        area = math.pi * (D/2) * math.sqrt(l**2 + (D/2)**2) + math.pi * (D/2)**2
        
    elif tipo_aleta == "7)aletas de perfil parabolico":
        if not D:
            return 0
        # Aproximação parabólica
        area = 1.1 * math.pi * D * l + math.pi * (D/2)**2
        
    elif tipo_aleta == "8)aletas de pino de perfilparabolico (ponta arredondada)":
        if not D:
            return 0
        # Cilindro + superfície esférica
        area = math.pi * D * l + 2 * math.pi * (D/2)**2
        
    else:
        area = 0
    
    return area

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