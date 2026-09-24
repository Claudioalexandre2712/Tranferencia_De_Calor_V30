# =============================================================================
# CONFIGURAÇÃO CENTRAL DOS TIPOS DE ALETAS
# =============================================================================
# Este arquivo define a estrutura única para todas as 8 geometrias de aletas.
# Cada tipo possui um ID único (1-8) que determina:
# - Campos de entrada obrigatórios
# - Parâmetros geométricos
# - Equações de cálculo
# - Validações específicas
# =============================================================================

TIPOS_ALETAS = {
    1: {
        'id': 1,
        'nome_interno': 'straight_rectangular',
        'nome_display': '1)aletas retangulares retas',
        'descricao': 'Aletas Retangulares Retas (Planas de Seção Uniforme)',
        'campos_obrigatorios': ['w', 'L', 't'],
        'campos_opcionais': [],
        'parametros_corrigidos': {
            'Lc': 'L + t/2',
            'Ap': 'Lc * t'
        },
        'perfil': 'Seção constante retangular',
        'formula_area_superficial': '2*w*Lc',
        'formula_area_perfil': 'w*t'
    },
    2: {
        'id': 2,
        'nome_interno': 'straight_triangular',
        'nome_display': '2)aletas triangulares retas',
        'descricao': 'Aletas Triangulares Retas',
        'campos_obrigatorios': ['w', 'L', 't'],
        'campos_opcionais': [],
        'parametros_corrigidos': {},
        'perfil': 'y = (t/2) * (1 - x/L)',
        'formula_area_superficial': '2*w*sqrt(L**2 + (t/2)**2)',
        'formula_area_perfil': 'w*t'
    },
    3: {
        'id': 3,
        'nome_interno': 'straight_parabolic',
        'nome_display': '3)aletas parabolicas retas',
        'descricao': 'Aletas Parabólicas Retas',
        'campos_obrigatorios': ['w', 'L', 't'],
        'campos_opcionais': [],
        'parametros_corrigidos': {},
        'perfil': 'y = (t/2) * (1 - x/L)^2',
        'formula_area_superficial': 'w*L*(C1 + (L/t)*ln(t/L + C1))',
        'formula_area_perfil': 'w*t'
    },
    4: {
        'id': 4,
        'nome_interno': 'circular_rectangular',
        'nome_display': '4)aletas circulares de perfil retangular',
        'descricao': 'Aletas Circulares de Perfil Retangular (Aletas Anulares)',
        'campos_obrigatorios': ['r1', 'r2', 't'],
        'campos_opcionais': ['L'],
        'parametros_corrigidos': {
            'r2c': 'r2 + t/2',
            'Lc': '(r2 - r1) + t/2'
        },
        'perfil': 'Seção constante retangular anular',
        'formula_area_superficial': '2*pi*(r2c**2 - r1**2)',
        'formula_area_perfil': 't*(r2c - r1)'
    },
    5: {
        'id': 5,
        'nome_interno': 'pin_rectangular',
        'nome_display': '5)aletas de pino de perfil retangular',
        'descricao': 'Aletas de Pino de Perfil Retangular (Cilíndricas Uniformes)',
        'campos_obrigatorios': ['D', 'L'],
        'campos_opcionais': [],
        'parametros_corrigidos': {
            'Lc': 'L + D/4'
        },
        'perfil': 'Seção constante circular (cilíndrica)',
        'formula_area_superficial': 'pi*D*Lc',
        'formula_area_perfil': 'pi*(D/2)**2'
    },
    6: {
        'id': 6,
        'nome_interno': 'pin_triangular',
        'nome_display': '6)aletas de pino de perfil triangular',
        'descricao': 'Aletas de Pino de Perfil Triangular (Cônicas)',
        'campos_obrigatorios': ['D', 'L'],
        'campos_opcionais': [],
        'parametros_corrigidos': {},
        'perfil': 'y = (D/2) * (1 - x/L)',
        'formula_area_superficial': '(pi*D/2)*sqrt(L**2 + (D/2)**2)',
        'formula_area_perfil': 'pi*(D/2)**2'
    },
    7: {
        'id': 7,
        'nome_interno': 'pin_parabolic',
        'nome_display': '7)aletas de pino de perfil parabolico',
        'descricao': 'Aletas de Pino de Perfil Parabólico',
        'campos_obrigatorios': ['D', 'L'],
        'campos_opcionais': [],
        'parametros_corrigidos': {},
        'perfil': 'y = (D/2) * (1 - x/L)^2',
        'formula_area_superficial': '(pi*L**3)/(8*D)*(C3*C4 - (L/(2*D))*ln((2*D*C4/L + C3)))',
        'formula_area_perfil': 'pi*(D/2)**2'
    },
    8: {
        'id': 8,
        'nome_interno': 'pin_parabolic_rounded',
        'nome_display': '8)aletas de pino de perfilparabolico (ponta arredondada)',
        'descricao': 'Aletas de Pino de Perfil Parabólico (Ponta Arredondada)',
        'campos_obrigatorios': ['D', 'L'],
        'campos_opcionais': [],
        'parametros_corrigidos': {},
        'perfil': 'y = (D/2) * (1 - x/L)^(1/2)',
        'formula_area_superficial': '(pi*D**4)/(96*L**2)*((16*(L/D)**2 + 1)**(3/2) - 1)',
        'formula_area_perfil': 'pi*(D/2)**2'
    }
}

# Tabela canônica de campos por ID
CAMPOS_POR_TIPO = {
    1: ['w', 'L', 't'],
    2: ['w', 'L', 't'],
    3: ['w', 'L', 't'],
    4: ['r1', 'r2', 't'],
    5: ['D', 'L'],
    6: ['D', 'L'],
    7: ['D', 'L'],
    8: ['D', 'L'],
}

# Mapeamento completo de aliases e variações históricas para identificação inequívoca
ALIASES_PARA_ID = {
    # 1
    1: 1, '1': 1, 'tipo_1': 1, 'tipo 1': 1, 'tipo1': 1,
    'straight_rectangular': 1,
    '1)aletas retangulares retas': 1,
    'aletas retangulares retas': 1,
    'aleta retangular reta': 1,
    
    # 2
    2: 2, '2': 2, 'tipo_2': 2, 'tipo 2': 2, 'tipo2': 2,
    'straight_triangular': 2,
    '2)aletas triangulares retas': 2,
    'aletas triangulares retas': 2,
    'aleta triangular reta': 2,
    
    # 3
    3: 3, '3': 3, 'tipo_3': 3, 'tipo 3': 3, 'tipo3': 3,
    'straight_parabolic': 3,
    '3)aletas parabolicas retas': 3,
    'aletas parabolicas retas': 3,
    'aleta parabolica reta': 3,
    '3)aletas parabólicas retas': 3,
    'aletas parabólicas retas': 3,
    
    # 4
    4: 4, '4': 4, 'tipo_4': 4, 'tipo 4': 4, 'tipo4': 4,
    'circular_rectangular': 4,
    '4)aletas circulares de perfil retangular': 4,
    'aletas circulares de perfil retangular': 4,
    'aleta circular de perfil retangular': 4,
    'aleta anular': 4,
    'aletas anulares': 4,
    
    # 5 (atenção aos aliases históricos que omitiam 'pino')
    5: 5, '5': 5, 'tipo_5': 5, 'tipo 5': 5, 'tipo5': 5,
    'pin_rectangular': 5,
    '5)aletas de pino de perfil retangular': 5,
    'aletas de pino de perfil retangular': 5,
    'aleta de pino de perfil retangular': 5,
    '5)aletas de perfil retangular': 5,
    'aletas de perfil retangular': 5,
    'aleta de perfil retangular': 5,
    
    # 6
    6: 6, '6': 6, 'tipo_6': 6, 'tipo 6': 6, 'tipo6': 6,
    'pin_triangular': 6,
    '6)aletas de pino de perfil triangular': 6,
    'aletas de pino de perfil triangular': 6,
    '6)aletas de perfil triangular': 6,
    'aletas de perfil triangular': 6,
    'aleta de perfil triangular': 6,
    'aleta conica': 6,
    'aletas conicas': 6,
    'aleta cônica': 6,
    'aletas cônicas': 6,
    
    # 7
    7: 7, '7': 7, 'tipo_7': 7, 'tipo 7': 7, 'tipo7': 7,
    'pin_parabolic': 7,
    '7)aletas de pino de perfil parabolico': 7,
    'aletas de pino de perfil parabolico': 7,
    '7)aletas de perfil parabolico': 7,
    'aletas de perfil parabolico': 7,
    'aleta de perfil parabolico': 7,
    '7)aletas de perfil parabólico': 7,
    'aletas de perfil parabólico': 7,
    
    # 8
    8: 8, '8': 8, 'tipo_8': 8, 'tipo 8': 8, 'tipo8': 8,
    'pin_parabolic_rounded': 8,
    '8)aletas de pino de perfilparabolico (ponta arredondada)': 8,
    '8)aletas de pino de perfil parabolico (ponta arredondada)': 8,
    'aletas de pino de perfilparabolico (ponta arredondada)': 8,
    'aletas de pino de perfil parabolico (ponta arredondada)': 8,
    'aleta de pino de perfil parabolico ponta arredondada': 8,
}


def obter_tipo_aleta(identificador):
    """
    Retorna o ID inteiro único (1 a 8) da aleta a partir de qualquer identificador.
    Pode ser int, string numérica ('1'-'8'), nome canônico, nome interno ou prefixo numérico.
    
    Retorna:
    --------
    int (1 a 8) ou None se não identificado
    """
    if identificador is None:
        return None
    
    # Se já for inteiro no intervalo
    if isinstance(identificador, int) and 1 <= identificador <= 8:
        return identificador
    
    s = str(identificador).strip().lower()
    
    # Se bater direto no dicionário de aliases
    if s in ALIASES_PARA_ID:
        return ALIASES_PARA_ID[s]
    
    # Verificação por prefixo numérico rígido '1)', '2)', ..., '8)'
    for i in range(1, 9):
        if s.startswith(f"{i})") or s.startswith(f"{i} -") or s.startswith(f"{i}."):
            return i
    
    # Verificação direta de dígito isolado
    if s in ['1', '2', '3', '4', '5', '6', '7', '8']:
        return int(s)
    
    # Tratamento de normalização básica de string
    s_clean = s.replace("á", "a").replace("ã", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ç", "c").replace("_", " ").replace("-", " ")
    if s_clean in ALIASES_PARA_ID:
        return ALIASES_PARA_ID[s_clean]
    
    return None


def obter_nome_display(tipo_id):
    """Retorna o nome_display padrão para um tipo_id (1-8)."""
    tid = obter_tipo_aleta(tipo_id)
    if tid in TIPOS_ALETAS:
        return TIPOS_ALETAS[tid]['nome_display']
    return str(tipo_id)


def obter_campos_formulario(tipo_id):
    """
    Retorna lista dos campos estritamente obrigatórios para o tipo de aleta (1-8).
    
    Retorna:
    --------
    (list, list) -> (campos_obrigatorios, campos_opcionais)
    """
    tid = obter_tipo_aleta(tipo_id)
    if tid not in TIPOS_ALETAS:
        return [], []
    return TIPOS_ALETAS[tid]['campos_obrigatorios'], TIPOS_ALETAS[tid]['campos_opcionais']


def obter_info_tipo(tipo_id):
    """Retorna o dicionário de informações completas do tipo (1-8)."""
    tid = obter_tipo_aleta(tipo_id)
    return TIPOS_ALETAS.get(tid, {})


def validar_campos_obrigatorios(tipo_id, t=None, w=None, r1=None, r2=None, D=None, L=None):
    """
    Valida rigorosamente os parâmetros da aleta conforme seu ID geométrico exato.
    
    Regra dos campos:
    - Tipos 1, 2, 3: w > 0, L > 0, t > 0
    - Tipo 4: r1 > 0, r2 > r1, t > 0 (L = r2 - r1)
    - Tipos 5, 6, 7, 8: D > 0, L > 0
    
    Retorna:
    --------
    (bool, list) -> (is_valid, lista_de_erros)
    """
    tid = obter_tipo_aleta(tipo_id)
    if tid is None:
        return False, [f"Tipo de aleta inválido: '{tipo_id}'"]
    
    tipo_info = TIPOS_ALETAS[tid]
    erros = []
    
    def valor_valido(val):
        if val is None:
            return False
        try:
            v = float(val)
            return v > 0 and not (v != v)  # positivo e não-NaN
        except (ValueError, TypeError):
            return False

    # Validação do comprimento L (exceto tipo 4 que deriva de r1 e r2 se L não for dado)
    if tid in [1, 2, 3, 5, 6, 7, 8]:
        if not valor_valido(L):
            erros.append(f"Comprimento (L) deve ser um número positivo para {tipo_info['descricao']}.")
    
    # Validação por tipo
    if tid in [1, 2, 3]:
        # Exige estritamente w e t
        if not valor_valido(w):
            erros.append("Largura (w) deve ser um número positivo.")
        if not valor_valido(t):
            erros.append("Espessura (t) deve ser um número positivo.")
            
    elif tid == 4:
        # Exige estritamente r1, r2 e t
        if not valor_valido(r1):
            erros.append("Raio interno (r1) deve ser um número positivo.")
        if not valor_valido(r2):
            erros.append("Raio externo (r2) deve ser um número positivo.")
        if valor_valido(r1) and valor_valido(r2) and float(r2) <= float(r1):
            erros.append("Raio externo (r2) deve ser estritamente maior que o raio interno (r1).")
        if not valor_valido(t):
            erros.append("Espessura (t) deve ser um número positivo.")
            
    elif tid in [5, 6, 7, 8]:
        # Exige estritamente D
        if not valor_valido(D):
            erros.append("Diâmetro (D) deve ser um número positivo.")
    
    return len(erros) == 0, erros


def determinar_campos_para_multiplas_aletas(tipos_aletas_lista):
    """
    Dado um conjunto de aletas selecionadas, determina quais campos do formulário devem
    ser exibidos de acordo com as geometrias presentes, SEM detecção por texto.
    
    Retorna:
    --------
    dict com chaves booleanas:
      - precisa_w: True se houver tipo 1, 2 ou 3
      - precisa_t: True se houver tipo 1, 2, 3 ou 4
      - precisa_r1_r2: True se houver tipo 4
      - precisa_D: True se houver tipo 5, 6, 7 ou 8
      - precisa_L: True sempre
      - tipo_ids: lista dos IDs identificados
    """
    tipo_ids = []
    for item in tipos_aletas_lista:
        tid = obter_tipo_aleta(item)
        if tid and tid not in tipo_ids:
            tipo_ids.append(tid)
            
    return {
        'tipo_ids': tipo_ids,
        'precisa_w': any(tid in [1, 2, 3] for tid in tipo_ids),
        'precisa_t': any(tid in [1, 2, 3, 4] for tid in tipo_ids),
        'precisa_r1_r2': any(tid == 4 for tid in tipo_ids),
        'precisa_D': any(tid in [5, 6, 7, 8] for tid in tipo_ids),
        'precisa_L': any(tid != 4 for tid in tipo_ids) if tipo_ids else True
    }


# Lista canônica ordenada de nomes para exibição nas rotas
LISTA_TIPOS_ORDENADA = [TIPOS_ALETAS[i]['nome_display'] for i in range(1, 9)]
