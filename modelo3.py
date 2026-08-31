# =============================================================================
# IMPORTS E CONFIGURAÇÕES
# =============================================================================

import sys
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/matplotlib')

import math
import datetime
import numpy as np
from scipy.special import i0, i1, k0, k1, i0e, i1e
import scipy.special as sp

# Configuração segura do Matplotlib para Serverless / Vercel
try:
    import matplotlib
    if matplotlib.get_backend().lower() not in ['agg', 'svg', 'pdf']:
        try:
            matplotlib.use('Agg')
        except Exception:
            pass
    import matplotlib.pyplot as plt
except Exception:
    plt = None

# Importação condicional do CustomTkinter e PIL para uso exclusivo quando em modo Desktop GUI
try:
    from PIL import Image, ImageTk
    import customtkinter as ctk
    from customtkinter import CTkImage
    TK_AVAILABLE = True
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
except (ImportError, Exception):
    TK_AVAILABLE = False

# Configuração de funcionalidades adicionais
ALETAS_SVARIAVEL_DISPONIVEL = False

def escolher_aletas():
    def on_select():
        root.tipo_aletas = [tipo for tipo, var in aleta_vars.items() if var.get()]  # type: ignore
        root.destroy()

    root = ctk.CTk()
    root.title("Escolha os tipos de aletas")

    # Tamanho da janela da escolha de Aletas
    root.geometry("500x400")

    tipos = [
        "1)aletas retangulares retas",
        "2)aletas triangulares retas",
        "3)aletas parabolicas retas",
        "4)aletas circulares de perfil retangular",
        "5)aletas de perfil retangular",
        "6)aletas de perfil triangular",
        "7)aletas de perfil parabolico",
        "8)aletas de pino de perfilparabolico (ponta arredondada)"
    ]

    label = ctk.CTkLabel(root, text="Escolha os tipos de aletas:", font=("Arial", 20, "bold"))
    label.pack(pady=10)

    aleta_vars = {tipo: ctk.BooleanVar() for tipo in tipos}

    for tipo in tipos:
        checkbox = ctk.CTkCheckBox(root, text=tipo.replace('_', ' ').title(), variable=aleta_vars[tipo], font=("Arial", 15, "bold"))
        checkbox.pack(anchor=ctk.W, pady=5)

    button_frame = ctk.CTkFrame(root)
    button_frame.pack(pady=10)

    select_button = ctk.CTkButton(button_frame, text="Selecionar", command=on_select)
    select_button.pack(side=ctk.LEFT, padx=5)

    cancel_button = ctk.CTkButton(button_frame, text="Cancelar", command=root.destroy)
    cancel_button.pack(side=ctk.LEFT, padx=5)

    root.mainloop()

    return getattr(root, 'tipo_aletas', [])

def obter_imagem(tipo_aleta):
    imagens = {
        "1)aletas retangulares retas": "static/aletas/1.png",
        "2)aletas triangulares retas": "static/aletas/2.png",
        "3)aletas parabolicas retas": "static/aletas/3.png",
        "4)aletas circulares de perfil retangular": "static/aletas/4.png",
        "5)aletas de perfil retangular": "static/aletas/5.png",
        "6)aletas de perfil triangular": "static/aletas/6.png",
        "7)aletas de perfil parabolico": "static/aletas/7.png",
        "8)aletas de pino de perfilparabolico (ponta arredondada)": "static/aletas/8.png"
    }
    return imagens.get(tipo_aleta)

def obter_formula(tipo_aleta):
    formulas = {
        "1)aletas retangulares retas": "static/formulas/1.png",
        "2)aletas triangulares retas": "static/formulas/2.png",
        "3)aletas parabolicas retas": "static/formulas/3.png",
        "4)aletas circulares de perfil retangular": "static/formulas/4.png",
        "5)aletas de perfil retangular": "static/formulas/5.png",
        "6)aletas de perfil triangular": "static/formulas/6.png",
        "7)aletas de perfil parabolico": "static/formulas/7.png",
        "8)aletas de pino de perfilparabolico (ponta arredondada)": "static/formulas/8.png"
    }
    return formulas.get(tipo_aleta)

def mostrar_formula(tipo_aleta):
    imagem_aleta = obter_imagem(tipo_aleta)
    formula_aleta = obter_formula(tipo_aleta)
    
    # Inicializar variáveis
    img = None
    formula_img = None

    root = ctk.CTk()
    root.title("Fórmula Utilizada")
    root.geometry("800x900")

    label = ctk.CTkLabel(root, text=f"{tipo_aleta.replace('_', ' ').title()}:", justify=ctk.LEFT, font=("Arial", 20, "bold"))
    label.pack(pady=10, padx=20)

    if imagem_aleta:
        img_pil = Image.open(imagem_aleta)
        try:
            img_pil = img_pil.resize((600, 400), Image.Resampling.LANCZOS)
        except AttributeError:
            # Fallback para versões antigas do PIL
            # Fallback simples para compatibilidade
            img_pil = img_pil.resize((600, 400))
        img = CTkImage(light_image=img_pil, dark_image=img_pil, size=(700, 400))
        panel = ctk.CTkLabel(root, image=img)
        panel.pack(side=ctk.TOP, padx=10, pady=10)

    if formula_aleta:
        formula_img_pil = Image.open(formula_aleta)
        try:
            formula_img_pil = formula_img_pil.resize((600, 300), Image.Resampling.LANCZOS)
        except AttributeError:
            # Fallback para versões antigas do PIL
            # Fallback simples para compatibilidade
            formula_img_pil = formula_img_pil.resize((600, 300))
        formula_img = CTkImage(light_image=formula_img_pil, dark_image=formula_img_pil, size=(700, 300))
        formula_panel = ctk.CTkLabel(root, image=formula_img)
        formula_panel.pack(side=ctk.TOP, padx=10, pady=10)

    button_frame = ctk.CTkFrame(root)
    button_frame.pack(pady=10)

    ok_button = ctk.CTkButton(button_frame, text="OK", command=root.destroy)
    ok_button.pack(side=ctk.LEFT, padx=5)

    back_button = ctk.CTkButton(button_frame, text="Voltar", command=lambda: [root.destroy(), main()])
    back_button.pack(side=ctk.LEFT, padx=5)

    root.mainloop()

    return img, formula_img

def escolher_material():
    def on_select():
        root.mat_tipo = int(material_var.get())  # type: ignore
        root.destroy()

    def on_back():
        root.destroy()
        main()

    root = ctk.CTk()
    root.title("Escolha o material")

    # Tamanho da janela da escolha de material
    root.geometry("600x350")

    material_var = ctk.StringVar(value="1")

    materiais = {
        1: {"nome": "Alumínio", "k": 240},  # Pode variar entre 200-237 W/m·K
        2: {"nome": "Cobre", "k": 386},  
        3: {"nome": "Aço Inoxidável", "k": 16},  # Pode variar entre 14-20 W/m·K
        4: {"nome": "Latão", "k": 120},  
        5: {"nome": "Titânio", "k": 21}, 
        6: {"nome": "Prata", "k": 429}, 
        7: {"nome": "Ouro", "k": 318},  
        8: {"nome": "Ferro", "k": 80},  # Pode variar entre 50-80 W/m·K
        9: {"nome": "Níquel", "k": 90},  
        10: {"nome": "Chumbo", "k": 34},  
    }

    label = ctk.CTkLabel(root, text="Escolha o material levando em consideração sua Condutividade Térmica (W/mK):", font=("Arial", 16))
    label.pack(pady=10)

    for i, mat in materiais.items():
        radio = ctk.CTkRadioButton(root, text=f"{i}. {mat['nome']} -- {mat['k']} W/mK", variable=material_var, value=i, command=on_select, font=("Arial", 15))
        radio.pack(anchor=ctk.W)

    button_frame = ctk.CTkFrame(root)
    button_frame.pack(pady=10)

    back_button = ctk.CTkButton(button_frame, text="Voltar", command=on_back)
    back_button.pack(side=ctk.LEFT, padx=5)

    root.mainloop()

    mat_tipo = getattr(root, 'mat_tipo', None)
    if mat_tipo is None:
        mat_tipo = 1  # Padrão para Alumínio
    return materiais[mat_tipo]["nome"], materiais[mat_tipo]["k"]

import numpy as np
import scipy.special as sp

def calcular_taxa_calor_condicao(m, l, h, k, theta_b, T_L, T_inf, condicao_ponta):
    """
    🎯 CÁLCULO DE TAXA DE CALOR POR CONDIÇÃO DE CONTORNO
    =====================================================
    
    Calcula a taxa de transferência de calor baseada na condição 
    de contorno na ponta da aleta (casos A, B, C, D do Çengel).
    
    ✅ Validado com exemplos Çengel págs. 154, 157, 160
    
    Args:
        m (float): Parâmetro da aleta [1/m]
        l (float): Comprimento da aleta [m] 
        h (float): Coeficiente de convecção [W/m²·K]
        k (float): Condutividade térmica [W/m·K]
        theta_b (float): Diferença de temperatura na base [K]
        T_L (float): Temperatura na ponta (se especificada) [K]
        T_inf (float): Temperatura ambiente [K]
        condicao_ponta (str): 'adiabatica', 'conveccao', 'infinita', 'temp_especificada'
    
    Returns:
        float: Fator adimensional para cálculo de taxa de calor
    """
    
    if condicao_ponta == 'adiabatica':
        # Caso B: Ponta Adiabática
        return np.tanh(m * l)
    
    elif condicao_ponta == 'conveccao':
        # Caso A: Convecção na Ponta
        numerador = np.sinh(m * l) + (h / (m * k)) * np.cosh(m * l)
        denominador = np.cosh(m * l) + (h / (m * k)) * np.sinh(m * l)
        if abs(denominador) < 1e-10:
            return float('inf')  # Evita divisão por zero
        return numerador / denominador
    
    elif condicao_ponta == 'infinita':
        # Caso D: Aleta Infinitamente Comprida
        return 1.0
    
    elif condicao_ponta == 'temp_especificada':
        # Caso C: Temperatura Especificada na Ponta
        if T_L is None:
            raise ValueError("A temperatura T_L é necessária para a condição de temperatura especificada.")
        theta_L = T_L - T_inf
        if abs(np.sinh(m * l)) < 1e-10:
            return float('inf')  # Evita divisão por zero
        return (np.cosh(m * l) - (theta_L / theta_b)) / np.sinh(m * l)
    
    else:
        # Padrão para o caso adiabático se a condição for inválida
        return np.tanh(m * l)


def normalizar_tipo_aleta(tipo_str):
    """
    Normaliza qualquer formato de nome de aleta para a string canônica padrão.
    Suporta variações com acento, sem acento, com número, sem número, maiúsculas,
    minúsculas, espaços e hífens.
    """
    if not tipo_str:
        return "1)aletas retangulares retas"
    
    t = str(tipo_str).strip().lower()
    t = t.replace("á", "a").replace("ã", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ç", "c").replace("_", " ").replace("-", " ")
    
    # 4. Circular
    if "4" in t or "circular" in t:
        return "4)aletas circulares de perfil retangular"
    
    # 8. Pino Parabólico com ponta arredondada
    elif "8" in t or "arredondada" in t or ("pino" in t and "parabol" in t):
        return "8)aletas de pino de perfilparabolico (ponta arredondada)"
    
    # 7. Perfil Parabólico
    elif "7" in t or ("perfil" in t and "parabol" in t):
        return "7)aletas de perfil parabolico"
    
    # 6. Perfil Triangular
    elif "6" in t or ("perfil" in t and "triangul" in t):
        return "6)aletas de perfil triangular"
    
    # 5. Perfil Retangular
    elif "5" in t or ("perfil" in t and "retangul" in t):
        return "5)aletas de perfil retangular"
    
    # 3. Parabólica Reta
    elif "3" in t or "parabol" in t:
        return "3)aletas parabolicas retas"
    
    # 2. Triangular Reta
    elif "2" in t or "triangul" in t:
        return "2)aletas triangulares retas"
    
    # 1. Retangular Reta
    elif "1" in t or "retangul" in t:
        return "1)aletas retangulares retas"
    
    return "1)aletas retangulares retas"

def calcular_eficiencia(tipo_aleta, h, k, l, t=None, w=None, D=None, r1=None, r2=None, T_b=None, T_inf=None, condicao_ponta='adiabatica', T_L=None):
    tipo_aleta = normalizar_tipo_aleta(tipo_aleta)
    # Verificações de parâmetros obrigatórios
    if T_b is None or T_inf is None:
        raise ValueError("T_b e T_inf são obrigatórios")
    
    # Dados didáticos serão gerados ao final
    dados_didaticos = None
    
    theta_b = T_b - T_inf
    if tipo_aleta == "1)aletas retangulares retas":
        if w is None or t is None:
            raise ValueError("Largura (w) e espessura (t) são obrigatórias para aletas retangulares")
        P = 2 * (w + t)  # Perímetro
        A_tr = w * t  # Área da seção transversal
        m = np.sqrt(h * P / (k * A_tr))
        
        # Calcular M (parâmetro base)
        M = np.sqrt(h * P * k * A_tr) * theta_b
        
        # Calcular fator baseado na condição de contorno
        fator_condicao = calcular_taxa_calor_condicao(m, l, h, k, theta_b, T_L, T_inf, condicao_ponta)
        
        # Taxa de transferência de calor com condição de contorno correta
        Q_aleta = M * fator_condicao
        
        # Área superficial baseada na condição de contorno (Çengel & Ghajar / Incropera)
        if condicao_ponta == 'conveccao':
            A_aleta = 2 * w * (l + t / 2)  # Comprimento corrigido Lc = L + t/2
        else:
            A_aleta = 2 * w * l  # Área das faces ativas (caso adiabático / infinito)
        
        # Eficiência baseada na condição de contorno
        if condicao_ponta == 'adiabatica':
            eta_aleta = np.tanh(m * l) / (m * l)
        elif condicao_ponta == 'conveccao':
            eta_aleta = fator_condicao / (m * l)
        elif condicao_ponta == 'infinita':
            eta_aleta = 1.0 / (m * l)
        elif condicao_ponta == 'temp_especificada':
            eta_aleta = fator_condicao / (m * l)
        else:
            eta_aleta = np.tanh(m * l) / (m * l)
        
        # Calcular efetividade
        Q_sem_aleta = h * A_tr * theta_b
        epsilon_a = Q_aleta / Q_sem_aleta if Q_sem_aleta != 0 else 0
        
        # Gerar dados didáticos
        dados_didaticos = gerar_dados_didaticos(tipo_aleta, h, k, l, t, w, D, r1, r2, T_b, T_inf, condicao_ponta, m, P, A_tr, eta_aleta, Q_aleta, epsilon_a)
        
        return eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr, dados_didaticos

    elif tipo_aleta == "2)aletas triangulares retas":
        if w is None or t is None:
            raise ValueError("Largura (w) e espessura (t) são obrigatórias para aletas triangulares")
        P = w + 2 * np.sqrt((w / 2)**2 + t**2)  # Perímetro
        A_tr = w * t  # Área da seção transversal
        A_aleta = 2 * w * np.sqrt(l**2 + (t / 2)**2)
        m = np.sqrt(h * P / (k * A_tr))
        
        # Calcular M (parâmetro base)
        M = np.sqrt(h * P * k * A_tr) * theta_b
        
        # Calcular fator baseado na condição de contorno
        fator_condicao = calcular_taxa_calor_condicao(m, l, h, k, theta_b, T_L, T_inf, condicao_ponta)
        
        # Taxa de transferência de calor
        Q_aleta = M * fator_condicao
        
        # Eficiência específica para aletas triangulares
        # Para aleta triangular: I1(ml)/[mlI0(ml)] onde I são funções Bessel modificadas
        ml = m * l
        try:
            eta_aleta = i1(ml) / (ml * i0(ml)) if ml > 0 else 1.0
        except (OverflowError, ZeroDivisionError):
            # Para valores muito grandes, usar aproximação assintótica
            eta_aleta = 1.0 / ml if ml > 10 else np.tanh(ml) / ml
        
        # Calcular efetividade
        Q_sem_aleta = h * A_tr * theta_b
        epsilon_a = Q_aleta / Q_sem_aleta if Q_sem_aleta != 0 else 0
        
        # Gerar dados didáticos
        dados_didaticos = gerar_dados_didaticos(tipo_aleta, h, k, l, t, w, D, r1, r2, T_b, T_inf, condicao_ponta, m, P, A_tr, eta_aleta, Q_aleta, epsilon_a)
        
        return eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr, dados_didaticos

    elif tipo_aleta == "3)aletas parabolicas retas":
        if w is None or t is None:
            raise ValueError("Largura (w) e espessura (t) são obrigatórias para aletas parabólicas")
        P = 2 * (w + t)  # Perímetro
        A_tr = w * t  # Área da seção transversal
        C1 = np.sqrt(1 + (t / l)**2)
        A_aleta = w * l * (C1 + (l / t) * np.log(t / l + C1))
        m = np.sqrt(h * P / (k * A_tr))
        
        # Calcular M (parâmetro base)
        M = np.sqrt(h * P * k * A_tr) * theta_b
        
        # Calcular fator baseado na condição de contorno
        fator_condicao = calcular_taxa_calor_condicao(m, l, h, k, theta_b, T_L, T_inf, condicao_ponta)
        
        # Taxa de transferência de calor
        Q_aleta = M * fator_condicao
        
        # Eficiência específica para aletas parabólicas
        # Para aleta parabólica: solução analítica específica
        ml = m * l
        try:
            # Aproximação para aleta parabólica baseada em Çengel
            if ml > 0:
                eta_aleta = 2.0 / (ml * (1 + ml))
            else:
                eta_aleta = 1.0
        except (OverflowError, ZeroDivisionError):
            eta_aleta = 1.0 / ml if ml > 10 else 2.0 / (ml * (1 + ml))
        
        # Calcular efetividade
        Q_sem_aleta = h * A_tr * theta_b
        epsilon_a = Q_aleta / Q_sem_aleta if Q_sem_aleta != 0 else 0
        
        # Gerar dados didáticos
        dados_didaticos = gerar_dados_didaticos(tipo_aleta, h, k, l, t, w, D, r1, r2, T_b, T_inf, condicao_ponta, m, P, A_tr, eta_aleta, Q_aleta, epsilon_a)
        
        return eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr, dados_didaticos

    elif tipo_aleta == "4)aletas circulares de perfil retangular":
        if r1 is None or r2 is None:
            raise ValueError("Raio interno (r1) e externo (r2) são obrigatórios para aletas circulares")
        P = 2 * np.pi * r2  # Perímetro
        A_tr = np.pi * (r2**2 - r1**2)  # Área da seção transversal
        A_aleta = 2 * np.pi * (r2**2 - r1**2)
        if A_aleta == 0:
            raise ValueError("Área da aleta não pode ser zero.")
        m = np.sqrt(h * P / (k * A_tr))
        
        # Calcular M (parâmetro base)
        M = np.sqrt(h * P * k * A_tr) * theta_b
        
        # Calcular fator baseado na condição de contorno
        fator_condicao = calcular_taxa_calor_condicao(m, l, h, k, theta_b, T_L, T_inf, condicao_ponta)
        
        # Taxa de transferência de calor
        Q_aleta = M * fator_condicao
        
        # Eficiência baseada na condição de contorno
        if condicao_ponta == 'adiabatica':
            eta_aleta = np.tanh(m * l) / (m * l)
        elif condicao_ponta == 'conveccao':
            eta_aleta = fator_condicao / (m * l)
        elif condicao_ponta == 'infinita':
            eta_aleta = 1.0 / (m * l)
        elif condicao_ponta == 'temp_especificada':
            eta_aleta = fator_condicao / (m * l)
        else:
            eta_aleta = np.tanh(m * l) / (m * l)
        
        # Calcular efetividade
        Q_sem_aleta = h * A_tr * theta_b
        epsilon_a = Q_aleta / Q_sem_aleta if Q_sem_aleta != 0 else 0
        
        # Gerar dados didáticos
        dados_didaticos = gerar_dados_didaticos(tipo_aleta, h, k, l, t, w, D, r1, r2, T_b, T_inf, condicao_ponta, m, P, A_tr, eta_aleta, Q_aleta, epsilon_a)
        
        return eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr, dados_didaticos

    elif tipo_aleta == "5)aletas de perfil retangular":
        if D is None:
            raise ValueError("Diâmetro (D) é obrigatório para aletas de perfil retangular")
        P = np.pi * D  # Perímetro
        A_tr = np.pi * (D / 2)**2  # Área da seção transversal
        A_aleta = np.pi * D * (l + D / 4)  # Área superficial para aletas cilíndricas
        
        # Parâmetro m para aletas cilíndricas
        m = np.sqrt(h * P / (k * A_tr))
        
        # Calcular M (parâmetro base)
        M = np.sqrt(h * P * k * A_tr) * theta_b
        
        # Calcular fator baseado na condição de contorno
        fator_condicao = calcular_taxa_calor_condicao(m, l, h, k, theta_b, T_L, T_inf, condicao_ponta)
        
        # Taxa de transferência de calor correta
        Q_aleta = M * fator_condicao
        
        # Eficiência baseada na condição de contorno
        if condicao_ponta == 'adiabatica':
            eta_aleta = np.tanh(m * l) / (m * l)
        elif condicao_ponta == 'conveccao':
            eta_aleta = fator_condicao / (m * l)
        elif condicao_ponta == 'infinita':
            eta_aleta = 1.0 / (m * l)
        elif condicao_ponta == 'temp_especificada':
            eta_aleta = fator_condicao / (m * l)
        else:
            eta_aleta = np.tanh(m * l) / (m * l)
        
        # Calcular efetividade
        Q_sem_aleta = h * A_tr * theta_b
        epsilon_a = Q_aleta / Q_sem_aleta if Q_sem_aleta != 0 else 0
        
        # Gerar dados didáticos
        dados_didaticos = gerar_dados_didaticos(tipo_aleta, h, k, l, t, w, D, r1, r2, T_b, T_inf, condicao_ponta, m, P, A_tr, eta_aleta, Q_aleta, epsilon_a)
        
        return eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr, dados_didaticos

    elif tipo_aleta == "6)aletas de perfil triangular":
        if D is None:
            raise ValueError("Diâmetro (D) é obrigatório para aletas de perfil triangular")
        P = np.pi * D  # Perímetro
        A_tr = np.pi * (D / 2)**2  # Área da seção transversal
        A_aleta = (np.pi * D / 2) * np.sqrt(l**2 + (D / 2)**2)
        m = np.sqrt(h * P / (k * A_tr))
        
        # Calcular M (parâmetro base)
        M = np.sqrt(h * P * k * A_tr) * theta_b
        
        # Calcular fator baseado na condição de contorno
        fator_condicao = calcular_taxa_calor_condicao(m, l, h, k, theta_b, T_L, T_inf, condicao_ponta)
        
        # Taxa de transferência de calor
        Q_aleta = M * fator_condicao
        
        # Eficiência específica para aleta de perfil triangular cilíndrica
        # Para aletas cilíndricas com perfil triangular: aproximação baseada em Çengel
        ml = m * l
        try:
            # Aproximação para aleta triangular cilíndrica
            eta_aleta = i1(ml) / (ml * i0(ml)) if ml > 0 else 1.0
        except (OverflowError, ZeroDivisionError):
            # Fallback se scipy não disponível ou overflow
            eta_aleta = 1.0 / ml if ml > 10 else np.tanh(ml) / ml
        
        # Calcular efetividade
        Q_sem_aleta = h * A_tr * theta_b
        epsilon_a = Q_aleta / Q_sem_aleta if Q_sem_aleta != 0 else 0
        
        # Gerar dados didáticos
        dados_didaticos = gerar_dados_didaticos(tipo_aleta, h, k, l, t, w, D, r1, r2, T_b, T_inf, condicao_ponta, m, P, A_tr, eta_aleta, Q_aleta, epsilon_a)
        
        return eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr, dados_didaticos

    elif tipo_aleta == "7)aletas de perfil parabolico":
        if D is None:
            raise ValueError("Diâmetro (D) é obrigatório para aletas de perfil parabólico")
        P = np.pi * D  # Perímetro
        A_tr = np.pi * (D / 2)**2  # Área da seção transversal
        C3 = 1 + 2 * (D / l)**2
        C4 = np.sqrt(1 + (D / l)**2)
        A_aleta = (np.pi * l**3) / (8 * D) * (C3 * C4 - (l / (2 * D)) * np.log((2 * D * C4 / l + C3)))
        m = np.sqrt(h * P / (k * A_tr))
        
        # Calcular M (parâmetro base)
        M = np.sqrt(h * P * k * A_tr) * theta_b
        
        # Calcular fator baseado na condição de contorno
        fator_condicao = calcular_taxa_calor_condicao(m, l, h, k, theta_b, T_L, T_inf, condicao_ponta)
        
        # Taxa de transferência de calor
        Q_aleta = M * fator_condicao
        
        # Eficiência específica para aleta de perfil parabólico cilíndrica
        # Para aletas cilíndricas com perfil parabólico: solução analítica
        ml = m * l
        try:
            # Aproximação para aleta parabólica cilíndrica baseada em Çengel
            if ml > 0:
                eta_aleta = 2.0 / (ml * np.sqrt(1 + ml))
            else:
                eta_aleta = 1.0
        except (OverflowError, ZeroDivisionError):
            eta_aleta = 1.0 / ml if ml > 10 else 2.0 / (ml * np.sqrt(1 + ml))
        
        # Calcular efetividade
        Q_sem_aleta = h * A_tr * theta_b
        epsilon_a = Q_aleta / Q_sem_aleta if Q_sem_aleta != 0 else 0
        
        # Gerar dados didáticos
        dados_didaticos = gerar_dados_didaticos(tipo_aleta, h, k, l, t, w, D, r1, r2, T_b, T_inf, condicao_ponta, m, P, A_tr, eta_aleta, Q_aleta, epsilon_a)
        
        return eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr, dados_didaticos

    elif tipo_aleta == "8)aletas de pino de perfilparabolico (ponta arredondada)":
        if D is None:
            raise ValueError("Diâmetro (D) é obrigatório para aletas de pino parabólico")
        P = np.pi * D  # Perímetro
        A_tr = np.pi * (D / 2)**2  # Área da seção transversal
        A_aleta = (np.pi * D**4 / (96 * l**2)) * ((16 * (l / D)**2 + 1)**(3 / 2) - 1)
        m = np.sqrt(h * P / (k * A_tr))
        
        # Calcular M (parâmetro base)
        M = np.sqrt(h * P * k * A_tr) * theta_b
        
        # Calcular fator baseado na condição de contorno
        fator_condicao = calcular_taxa_calor_condicao(m, l, h, k, theta_b, T_L, T_inf, condicao_ponta)
        
        # Taxa de transferência de calor
        Q_aleta = M * fator_condicao
        
        # Eficiência da aleta: η = Q_aleta / Q_max
        Q_max = h * A_aleta * theta_b  # Calor máximo se toda aleta estivesse a T_b
        eta_aleta = Q_aleta / Q_max if Q_max != 0 else 0
        
        # Calcular efetividade
        Q_sem_aleta = h * A_tr * theta_b
        epsilon_a = Q_aleta / Q_sem_aleta if Q_sem_aleta != 0 else 0
        
        # Gerar dados didáticos
        dados_didaticos = gerar_dados_didaticos(tipo_aleta, h, k, l, t, w, D, r1, r2, T_b, T_inf, condicao_ponta, m, P, A_tr, eta_aleta, Q_aleta, epsilon_a)
        
        return eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr, dados_didaticos

    else:
        raise ValueError("Tipo de aleta desconhecido.")

def on_submit(h_entry, l_entry, t_entry, w_entry, D_entry, r1_entry, r2_entry, T_inf_entry, T_b_entry, error_label, root):
    try:
        h = float(h_entry.get())
        l = float(l_entry.get())
        t = float(t_entry.get()) if t_entry else None
        w = float(w_entry.get()) if w_entry else None
        D = float(D_entry.get()) if D_entry else None
        r1 = float(r1_entry.get()) if r1_entry else None
        r2 = float(r2_entry.get()) if r2_entry else None
        T_inf = float(T_inf_entry.get())
        T_b = float(T_b_entry.get())
        if h > 0 and l > 0 and (t is None or t > 0) and (w is None or w > 0) and (D is None or D > 0) and (r1 is None or r1 > 0) and (r2 is None or r2 > 0):
            root.h = h  # type: ignore
            root.l = l  # type: ignore
            root.t = t  # type: ignore
            root.w = w  # type: ignore
            root.D = D  # type: ignore
            root.r1 = r1  # type: ignore
            root.r2 = r2  # type: ignore
            root.T_inf = T_inf  # type: ignore
            root.T_b = T_b  # type: ignore
            root.destroy()
        else:
            error_label.config(text="Erro: Todos os valores devem ser números positivos.")
    except ValueError:
        error_label.config(text="Erro: Certifique-se de inserir números válidos.")

def sgerar_distribuicao_temperatura(sele_aleta, h, k, l, t, w, D, r1, r2, T_b, T_inf, smateriais):
    x = np.linspace(0, l, 100)
    plt.figure()

    for material, valor_k in zip(smateriais, k):
        T = None  # Inicializar T
        if sele_aleta[0] == "4)aletas circulares de perfil retangular":
            if t is not None and r1 is not None and r2 is not None:
                T = T_aleta_circular(x, l, T_b, T_inf, h, valor_k, t, r1, r2)
            else:
                raise ValueError("Espessura (t), raio interno (r1) e raio externo (r2) são necessários para aletas circulares de perfil retangular.")
        elif sele_aleta[0] == "5)aletas de perfil retangular":
            if D is not None:
                T = T_aleta_perfil_retangular(x, l, T_b, T_inf, h, valor_k, D)
            else:
                raise ValueError("Diâmetro (D) é necessário para aletas de perfil retangular.")
        elif sele_aleta[0] in ["6)aletas de perfil triangular", "7)aletas de perfil parabolico", "8)aletas de pino de perfilparabolico (ponta arredondada)"]:
            if D is not None:
                if sele_aleta[0] == "6)aletas de perfil triangular":
                    T = T_aleta_perfil_triangular(x, l, T_b, T_inf, h, valor_k, D)
                elif sele_aleta[0] == "7)aletas de perfil parabolico":
                    T = T_aleta_perfil_parabolico(x, l, T_b, T_inf, h, valor_k, D)
                elif sele_aleta[0] == "8)aletas de pino de perfilparabolico (ponta arredondada)":
                    T = T_aleta_pino_parabolico(x, l, T_b, T_inf, h, valor_k, D)
            else:
                raise ValueError("Diâmetro (D) é necessário para aletas de perfil triangular, parabolico e pino de perfilparabolico.")
        else:
            if t is not None and w is not None:
                T = T_aleta_retangular(x, l, T_b, T_inf, h, valor_k, t, w)
            else:
                raise ValueError("Espessura (t) e largura (w) são necessárias para aletas retangulares.")
        
        if T is not None:
            plt.plot(x, T, label=f'{material} (k={valor_k})')

    plt.xlabel('Comprimento da aleta (m)')
    plt.ylabel('Temperatura (°C)')
    plt.title('Distribuição de Temperatura ao Longo da Aleta')
    plt.legend()
    plt.grid(True)

    grafico_path = f'static/distribuicao_temperatura_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.png'
    plt.savefig(grafico_path)
    plt.close()

    return grafico_path

def gerar_distribuicao_temperatura(tipos_aletas, h, k, l, t, w, D, r1, r2, T_b, T_inf):
    x = np.linspace(0, l, 100)
    plt.figure()

    for tipo_aleta in tipos_aletas:
        if tipo_aleta == "1)aletas retangulares retas":
            T_x = T_aleta_retangular(x, l, T_b, T_inf, h, k, t, w)
        elif tipo_aleta == "2)aletas triangulares retas":
            T_x = T_aleta_triangular(x, l, T_b, T_inf, h, k, t, w)
        elif tipo_aleta == "3)aletas parabolicas retas":
            T_x = T_aleta_parabolica(x, l, T_b, T_inf, h, k, t, w)
        elif tipo_aleta == "4)aletas circulares de perfil retangular":
            T_x = T_aleta_circular(x, l, T_b, T_inf, h, k, t, r1, r2)
        elif tipo_aleta == "5)aletas de perfil retangular":
            T_x = T_aleta_perfil_retangular(x, l, T_b, T_inf, h, k, D)
        elif tipo_aleta == "6)aletas de perfil triangular":
            T_x = T_aleta_perfil_triangular(x, l, T_b, T_inf, h, k, D)
        elif tipo_aleta == "7)aletas de perfil parabolico":
            T_x = T_aleta_perfil_parabolico(x, l, T_b, T_inf, h, k, D)
        elif tipo_aleta == "8)aletas de pino de perfilparabolico (ponta arredondada)":
            T_x = T_aleta_pino_parabolico(x, l, T_b, T_inf, h, k, D)
        else:
            T_x = np.zeros_like(x)

        plt.plot(x, T_x, label=tipo_aleta)

    plt.xlabel('Comprimento (m)')
    plt.ylabel('Temperatura (°C)')
    plt.title('Distribuição de Temperatura')
    plt.grid(True)
    plt.legend()

    # Garantir que o diretório exista
    os.makedirs('static/graficos', exist_ok=True)
    
    grafico_path = 'static/graficos/distribuicao_temperatura.png'
    plt.savefig(grafico_path)
    plt.close()
    
    return grafico_path

def T_aleta_retangular(x, l, T_b, T_inf, h, k, t, w):
    P = 2 * (w + t)  # Perímetro
    A_aleta = 2 * w * (l + t / 2)  # Área da seção transversal
    m = np.sqrt(h * P / (k * A_aleta))
    return T_inf + (T_b - T_inf) * np.cosh(m * (l - x)) / np.cosh(m * l)

def T_aleta_triangular(x, l, T_b, T_inf, h, k, t, w):
    P = w + 2 * np.sqrt((w / 2)**2 + t**2)  # Perímetro
    A_aleta = 2 * w * np.sqrt(l**2 + (t / 2)**2)
    m = np.sqrt(h * P / (k * A_aleta))
    return T_inf + (T_b - T_inf) * np.cosh(m * np.sqrt(2) * (l - x)) / np.cosh(m * np.sqrt(2) * l)

def T_aleta_parabolica(x, l, T_b, T_inf, h, k, t, w):
    P = 2 * (w + t)  # Perímetro
    C1 = np.sqrt(1 + (t / l)**2)
    A_aleta = w * l * (C1 + (l / t) * np.log(t / l + C1))
    m = np.sqrt(h * P / (k * A_aleta))
    return T_inf + (T_b - T_inf) * np.cosh(m * np.sqrt(3) * (l - x)) / np.cosh(m * np.sqrt(3) * l)

def T_aleta_circular(x, l, T_b, T_inf, h, k, t, r1, r2):
    P = 2 * np.pi * r2  # Perímetro
    A_aleta = 2 * np.pi * (r2**2 - r1**2)
    if A_aleta == 0:
        raise ValueError("Área da aleta não pode ser zero.")
    m = np.sqrt(h * P / (k * A_aleta))
    return T_inf + (T_b - T_inf) * np.cosh(m * (l - x)) / np.cosh(m * l)

def T_aleta_perfil_retangular(x, l, T_b, T_inf, h, k, D):
    P = np.pi * D  # Perímetro
    A_aleta = np.pi * D * (l + D / 4)
    m = np.sqrt(h * P / (k * A_aleta))
    return T_inf + (T_b - T_inf) * np.cosh(m * (l - x)) / np.cosh(m * l)

def T_aleta_perfil_triangular(x, l, T_b, T_inf, h, k, D):
    P = np.pi * D  # Perímetro
    A_aleta = (np.pi * D / 2) * np.sqrt(l**2 + (D / 2)**2)
    m = np.sqrt(h * P / (k * A_aleta))
    return T_inf + (T_b - T_inf) * np.cosh(m * np.sqrt(2) * (l - x)) / np.cosh(m * np.sqrt(2) * l)

def T_aleta_perfil_parabolico(x, L, T_b, T_inf, h, k, D):
    P = np.pi * D  # Perímetro
    C3 = 1 + 2 * (D / L)**2
    C4 = np.sqrt(1 + (D / L)**2)
    A_aleta = (np.pi * L**3) / (8 * D) * (C3 * C4 - (L / (2 * D)) * np.log((2 * D * C4 / L + C3)))
    m = np.sqrt(h * P / (k * A_aleta))
    return T_inf + (T_b - T_inf) * np.cosh(m * np.sqrt(3) * (L - x)) / np.cosh(m * np.sqrt(3) * L)

def T_aleta_pino_parabolico(x, L, T_b, T_inf, h, k, D):
    P = np.pi * D  # Perímetro
    A_aleta = (np.pi * D**4 / (96 * L**2)) * ((16 * (L / D)**2 + 1)**(3 / 2) - 1)
    m = np.sqrt(h * P / (k * A_aleta))
    return T_inf + (T_b - T_inf) * np.cosh(m * (L - x)) / np.cosh(m * L)

def main():
    tipos_aletas = escolher_aletas()
    if not tipos_aletas:
        print("Nenhum tipo de aleta selecionado.")
        return

    material, k = escolher_material()

    root = ctk.CTk()
    root.title("Insira os valores")
    root.geometry("650x450")

    frame = ctk.CTkFrame(root)
    frame.pack(pady=10)

    ctk.CTkLabel(frame, text="Coeficiente de transferência de calor (h) (W/m²K):").grid(row=0, column=0, padx=5, pady=5, sticky=ctk.W)
    h_entry = ctk.CTkEntry(frame)
    h_entry.grid(row=0, column=1, padx=5, pady=5)

    ctk.CTkLabel(frame, text="Comprimento (l) (m):").grid(row=1, column=0, padx=5, pady=5, sticky=ctk.W)
    l_entry = ctk.CTkEntry(frame)
    l_entry.grid(row=1, column=1, padx=5, pady=5)

    t_entry = None
    w_entry = None
    D_entry = None
    r1_entry = None
    r2_entry = None

    if any(tipo in tipos_aletas for tipo in ["1)aletas retangulares retas", "2)aletas triangulares retas", "3)aletas parabolicas retas"]):
        ctk.CTkLabel(frame, text="Espessura (t) (m):").grid(row=2, column=0, padx=5, pady=5, sticky=ctk.W)
        t_entry = ctk.CTkEntry(frame)
        t_entry.grid(row=2, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame, text="Largura (w) (m):").grid(row=3, column=0, padx=5, pady=5, sticky=ctk.W)
        w_entry = ctk.CTkEntry(frame)
        w_entry.grid(row=3, column=1, padx=5, pady=5)

    if any(tipo in tipos_aletas for tipo in ["4)aletas circulares de perfil retangular"]):
        ctk.CTkLabel(frame, text="Raio interno (r1) (m):").grid(row=4, column=0, padx=5, pady=5, sticky=ctk.W)
        r1_entry = ctk.CTkEntry(frame)
        r1_entry.grid(row=4, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame, text="Raio externo (r2) (m):").grid(row=5, column=0, padx=5, pady=5, sticky=ctk.W)
        r2_entry = ctk.CTkEntry(frame)
        r2_entry.grid(row=5, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame, text="Espessura (t) (m):").grid(row=6, column=0, padx=5, pady=5, sticky=ctk.W)
        t_entry = ctk.CTkEntry(frame)
        t_entry.grid(row=6, column=1, padx=5, pady=5)

    if any(tipo in tipos_aletas for tipo in ["5)aletas de perfil retangular", "6)aletas de perfil triangular", "7)aletas de perfil parabolico", "8)aletas de pino de perfilparabolico (ponta arredondada)"]):
        ctk.CTkLabel(frame, text="Diâmetro (D) (m):").grid(row=7, column=0, padx=5, pady=5, sticky=ctk.W)
        D_entry = ctk.CTkEntry(frame)
        D_entry.grid(row=7, column=1, padx=5, pady=5)

    ctk.CTkLabel(frame, text="Temperatura do meio (T∞) (°C):").grid(row=8, column=0, padx=5, pady=5, sticky=ctk.W)
    T_inf_entry = ctk.CTkEntry(frame)
    T_inf_entry.grid(row=8, column=1, padx=5, pady=5)

    ctk.CTkLabel(frame, text="Temperatura da base da aleta (Tb) (°C):").grid(row=9, column=0, padx=5, pady=5, sticky=ctk.W)
    T_b_entry = ctk.CTkEntry(frame)
    T_b_entry.grid(row=9, column=1, padx=5, pady=5)

    error_label = ctk.CTkLabel(frame, text="", text_color="red")
    error_label.grid(row=10, column=0, columnspan=2, pady=5)

    button_frame = ctk.CTkFrame(root)
    button_frame.pack(pady=10)

    submit_button = ctk.CTkButton(button_frame, text="Confirmar", command=lambda: on_submit(h_entry, l_entry, t_entry, w_entry, D_entry, r1_entry, r2_entry, T_inf_entry, T_b_entry, error_label, root))
    submit_button.pack(side=ctk.LEFT, padx=5)

    back_button = ctk.CTkButton(button_frame, text="Voltar", command=lambda: [root.destroy(), main()])
    back_button.pack(side=ctk.LEFT, padx=5)

    root.mainloop()

    h = getattr(root, 'h', None)
    l = getattr(root, 'l', None)
    t = getattr(root, 't', None)
    w = getattr(root, 'w', None)
    D = getattr(root, 'D', None)
    r1 = getattr(root, 'r1', None)
    r2 = getattr(root, 'r2', None)
    T_inf = getattr(root, 'T_inf', None)
    T_b = getattr(root, 'T_b', None)

    if h is None or l is None or T_inf is None or T_b is None or (t is None and w is None and D is None and r1 is None and r2 is None):
        print("Valores não fornecidos.")
        return

    

   
def salvar_resultados(filepath, tipos_aletas, h, k, l, t, w, D, r1, r2, T_b, T_inf, resultados):
    try:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write("Resultados das Aletas\n")
            for resultado in resultados:
                if len(resultado) == 8:  # Novo formato com métricas de desempenho
                    tipo_aleta, eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr = resultado
                    file.write(f"Tipo de Aleta: {tipo_aleta}\n")
                    file.write(f"Eficiência (eta_aleta): {eta_aleta:.6f}\n")
                    file.write(f"Taxa de Transferência de Calor (Q_aleta): {Q_aleta:.6f} W\n")
                    file.write(f"Efetividade (epsilon_a): {epsilon_a:.6f}\n")
                    file.write(f"Parâmetro m: {m:.6f} m^-1\n")
                    file.write(f"Perímetro P: {P:.6f} m\n")
                    file.write(f"Área Transversal A_tr: {A_tr:.9f} m^2\n")
                else:  # Formato antigo para compatibilidade
                    tipo_aleta, eta_aleta, Q_aleta, A_aleta = resultado
                    file.write(f"Tipo de Aleta: {tipo_aleta}\n")
                    file.write(f"Eficiência (eta_aleta): {eta_aleta:.6f}\n")
                    file.write(f"Taxa de Transferência de Calor (Q_aleta): {Q_aleta:.6f} W\n")
                file.write("Comprimento (m) x Temperatura (°C):\n")
                x = np.linspace(0, l, 15)  
                if tipo_aleta == "1)aletas retangulares retas":
                    T_x = T_aleta_retangular(x, l, T_b, T_inf, h, k, t, w)
                elif tipo_aleta == "2)aletas triangulares retas":
                    T_x = T_aleta_triangular(x, l, T_b, T_inf, h, k, t, w)
                elif tipo_aleta == "3)aletas parabolicas retas":
                    T_x = T_aleta_parabolica(x, l, T_b, T_inf, h, k, t, w)
                elif tipo_aleta == "4)aletas circulares de perfil retangular":
                    T_x = T_aleta_circular(x, l, T_b, T_inf, h, k, t, r1, r2)
                elif tipo_aleta == "5)aletas de perfil retangular":
                    T_x = T_aleta_perfil_retangular(x, l, T_b, T_inf, h, k, D)
                elif tipo_aleta == "6)aletas de perfil triangular":
                    T_x = T_aleta_perfil_triangular(x, l, T_b, T_inf, h, k, D)
                elif tipo_aleta == "7)aletas de perfil parabolico":
                    T_x = T_aleta_perfil_parabolico(x, l, T_b, T_inf, h, k, D)
                elif tipo_aleta == "8)aletas de pino de perfilparabolico (ponta arredondada)":
                    T_x = T_aleta_pino_parabolico(x, l, T_b, T_inf, h, k, D)
                else:
                    T_x = np.zeros_like(x)
                for xi, Ti in zip(x, T_x):
                    file.write(f"{xi:.6f} m: {Ti:.6f} °C\n")
                file.write("\n")
    except Exception as e:
        print(f"[AVISO] Erro ao salvar relatório em {filepath}: {e}")

    try:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Resultados")
        os.makedirs(output_dir, exist_ok=True)
        results_filepath = os.path.join(output_dir, "resultados_aletas.txt")
        with open(results_filepath, 'w', encoding='utf-8') as file:
            file.write(f"Tipos de Aletas: {tipos_aletas}\n")
            file.write(f"h: {h}, k: {k}, l: {l}, t: {t}, w: {w}, D: {D}, r1: {r1}, r2: {r2}, T_b: {T_b}, T_inf: {T_inf}\n")
            for res in resultados:
                file.write(f"{res}\n")
    except Exception as e2:
        print(f"[AVISO] Erro ao salvar resultados_aletas.txt: {e2}")
            
def salvar_sresultados(filepath, sele_aleta, h, k, l, t, w, D, r1, r2, T_b, T_inf, resultados_sele):
    try:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("Resultados das Aletas\n")
            f.write(f"Seleção de Aletas: {', '.join(sele_aleta)}\n")
            for resultado_sele in resultados_sele:
                if len(resultado_sele) == 10:  # Novo formato com métricas de desempenho
                    tipo_aleta, material, valor_k, eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr = resultado_sele
                    f.write(f"Tipo de Aleta: {tipo_aleta}\n")
                    f.write(f"Material: {material}\n")
                    f.write(f"k: {valor_k}\n")
                    f.write(f"Eficiência da Aleta: {eta_aleta:.6f}\n")
                    f.write(f"Taxa de Transferência de Calor: {Q_aleta:.6f} W\n")
                    f.write(f"Área da Aleta: {A_aleta:.6f} m²\n")
                    f.write(f"Efetividade (epsilon_a): {epsilon_a:.6f}\n")
                    f.write(f"Parâmetro m: {m:.6f} m^-1\n")
                    f.write(f"Perímetro P: {P:.6f} m\n")
                    f.write(f"Área Transversal A_tr: {A_tr:.9f} m^2\n")
                else:  # Formato antigo para compatibilidade
                    tipo_aleta, material, valor_k, eta_aleta, Q_aleta, A_aleta = resultado_sele
                    f.write(f"Tipo de Aleta: {tipo_aleta}\n")
                    f.write(f"Material: {material}\n")
                    f.write(f"k: {valor_k}\n")
                    f.write(f"Eficiência da Aleta: {eta_aleta:.6f}\n")
                    f.write(f"Taxa de Transferência de Calor: {Q_aleta:.6f} W\n")
                    f.write(f"Área da Aleta: {A_aleta:.6f} m²\n")
                f.write("Comprimento (m) x Temperatura (°C):\n")
                x = np.linspace(0, l, 15)
                if tipo_aleta == "1)aletas retangulares retas":
                    if t is not None and w is not None:
                        T_x = T_aleta_retangular(x, l, T_b, T_inf, h, valor_k, t, w)
                    else:
                        T_x = np.zeros_like(x)
                elif tipo_aleta == "2)aletas triangulares retas":
                    if t is not None and w is not None:
                        T_x = T_aleta_triangular(x, l, T_b, T_inf, h, valor_k, t, w)
                    else:
                        T_x = np.zeros_like(x)
                elif tipo_aleta == "3)aletas parabolicas retas":
                    if t is not None and w is not None:
                        T_x = T_aleta_parabolica(x, l, T_b, T_inf, h, valor_k, t, w)
                    else:
                        T_x = np.zeros_like(x)
                elif tipo_aleta == "4)aletas circulares de perfil retangular":
                    if t is not None and r1 is not None and r2 is not None:
                        T_x = T_aleta_circular(x, l, T_b, T_inf, h, valor_k, t, r1, r2)
                    else:
                        T_x = np.zeros_like(x)
                elif tipo_aleta == "5)aletas de perfil retangular":
                    if D is not None:
                        T_x = T_aleta_perfil_retangular(x, l, T_b, T_inf, h, valor_k, D)
                    else:
                        T_x = np.zeros_like(x)
                elif tipo_aleta == "6)aletas de perfil triangular":
                    if D is not None:
                        T_x = T_aleta_perfil_triangular(x, l, T_b, T_inf, h, valor_k, D)
                    else:
                        T_x = np.zeros_like(x)
                elif tipo_aleta == "7)aletas de perfil parabolico":
                    if D is not None:
                        T_x = T_aleta_perfil_parabolico(x, l, T_b, T_inf, h, valor_k, D)
                    else:
                        T_x = np.zeros_like(x)
                elif tipo_aleta == "8)aletas de pino de perfilparabolico (ponta arredondada)":
                    if D is not None:
                        T_x = T_aleta_pino_parabolico(x, l, T_b, T_inf, h, valor_k, D)
                    else:
                        T_x = np.zeros_like(x)
                else:
                    T_x = np.zeros_like(x)
                for xi, Ti in zip(x, T_x):
                    f.write(f"{xi:.6f} m: {Ti:.6f} °C\n")
                f.write("\n")
    except Exception as e_s:
        print(f"[AVISO] Erro ao salvar selerelatorio em {filepath}: {e_s}")
            
if __name__ == "__main__":
    main()

def gerar_dados_didaticos(tipo_aleta, h, k, l, t, w, D, r1, r2, T_b, T_inf, condicao_ponta, m, P, A_tr, eta_aleta, Q_aleta, epsilon_a):
    """Gera dados didáticos com resolução passo a passo para aletas de seção variável"""
    
    class DadosDidaticos:
        def __init__(self):
            self.tipo_aleta_original = tipo_aleta
            self.tipo_aleta_mapeado = tipo_aleta
            self.metodo = "Análise de Transferência de Calor em Aletas"
            self.condicao_ponta = condicao_ponta
            self.passos_resolucao = []
            self.q_base = Q_aleta
            self.eficiencia = eta_aleta
            self.efetividade = epsilon_a
    
    dados = DadosDidaticos()
    theta_b = T_b - T_inf
    
    # Passo 1: Identificação dos parâmetros
    passo1 = {
        'titulo': '1. Identificação dos Parâmetros da Aleta',
        'equacao': f'θ_b = T_b - T_∞ = {T_b} - {T_inf} = {theta_b} °C',
        'explicacao': f'Calculamos a diferença de temperatura na base da aleta. Este é o potencial de transferência de calor disponível.',
        'valores': f'h = {h} W/m²·K, k = {k} W/m·K, L = {l} m'
    }
    dados.passos_resolucao.append(passo1)
    
    # Passo 2: Cálculo das propriedades geométricas
    if "retangular" in tipo_aleta.lower():
        passo2 = {
            'titulo': '2. Propriedades Geométricas da Aleta Retangular',
            'equacao': f'P = 2(w + t) = 2({w} + {t}) = {P:.6f} m',
            'explicacao': 'O perímetro da aleta inclui todas as superfícies expostas ao fluido.',
            'valores': f'A_tr = w × t = {w} × {t} = {A_tr:.9f} m²'
        }
    elif "triangular" in tipo_aleta.lower():
        passo2 = {
            'titulo': '2. Propriedades Geométricas da Aleta Triangular',
            'equacao': f'P = w + 2√((w/2)² + t²) = {P:.6f} m',
            'explicacao': 'Para aleta triangular, consideramos a base e as duas faces inclinadas.',
            'valores': f'A_tr = w × t = {w} × {t} = {A_tr:.9f} m²'
        }
    elif "perfil retangular" in tipo_aleta.lower():
        passo2 = {
            'titulo': '2. Propriedades Geométricas da Aleta de Perfil Retangular',
            'equacao': f'P = π × D = π × {D} = {P:.6f} m',
            'explicacao': 'Para aleta de perfil retangular (cilíndrica), o perímetro é a circunferência da seção circular.',
            'valores': f'A_tr = π × D²/4 = π × {D}²/4 = {A_tr:.9f} m²'
        }
    elif "cilíndrica" in tipo_aleta.lower() or "pino" in tipo_aleta.lower():
        passo2 = {
            'titulo': '2. Propriedades Geométricas da Aleta Cilíndrica',
            'equacao': f'P = π × D = π × {D} = {P:.6f} m',
            'explicacao': 'Para aleta cilíndrica (pino), o perímetro é a circunferência.',
            'valores': f'A_tr = π × D²/4 = π × {D}²/4 = {A_tr:.9f} m²'
        }
    else:
        passo2 = {
            'titulo': '2. Propriedades Geométricas da Aleta',
            'equacao': f'P = {P:.6f} m, A_tr = {A_tr:.9f} m²',
            'explicacao': 'Calculamos o perímetro e área transversal baseados na geometria específica.',
            'valores': f'Geometria: {tipo_aleta}'
        }
    dados.passos_resolucao.append(passo2)
    
    # Passo 3: Parâmetro m
    passo3 = {
        'titulo': '3. Cálculo do Parâmetro m',
        'equacao': f'm = √(hP/kA_tr) = √({h} × {P:.6f}/({k} × {A_tr:.9f})) = {m:.6f} m⁻¹',
        'explicacao': 'O parâmetro m caracteriza a variação exponencial de temperatura ao longo da aleta. Quanto maior m, mais rápida é a queda de temperatura.',
        'valores': f'mL = {m:.6f} × {l} = {m*l:.6f} (adimensional)'
    }
    dados.passos_resolucao.append(passo3)
    
    # Passo 4: Eficiência da aleta
    if condicao_ponta == 'adiabatica':
        passo4 = {
            'titulo': '4. Eficiência da Aleta (Ponta Adiabática)',
            'equacao': f'η = tanh(mL)/(mL) = tanh({m*l:.6f})/{m*l:.6f} = {eta_aleta:.6f}',
            'explicacao': 'Para ponta adiabática, a eficiência é calculada usando a função tangente hiperbólica. Esta condição assume que não há perda de calor pela extremidade.',
            'valores': f'η = {eta_aleta:.4f} = {eta_aleta*100:.2f}%'
        }
    elif condicao_ponta == 'conveccao':
        passo4 = {
            'titulo': '4. Eficiência da Aleta (Convecção na Ponta)',
            'equacao': f'η = tanh(mL + h/(mk))/(mL + h/(mk))',
            'explicacao': 'Para convecção na ponta, consideramos a transferência de calor pela extremidade da aleta.',
            'valores': f'η = {eta_aleta:.4f} = {eta_aleta*100:.2f}%'
        }
    else:
        passo4 = {
            'titulo': '4. Eficiência da Aleta',
            'equacao': f'η = {eta_aleta:.6f}',
            'explicacao': f'Eficiência calculada para condição: {condicao_ponta}',
            'valores': f'η = {eta_aleta:.4f} = {eta_aleta*100:.2f}%'
        }
    dados.passos_resolucao.append(passo4)
    
    # Passo 5: Taxa de transferência de calor
    passo5 = {
        'titulo': '5. Taxa de Transferência de Calor',
        'equacao': f'Q = η × h × A_s × θ_b = {eta_aleta:.6f} × {h} × A_s × {theta_b}',
        'explicacao': 'A taxa de transferência de calor é o produto da eficiência, coeficiente convectivo, área superficial e diferença de temperatura.',
        'valores': f'Q = {Q_aleta:.3f} W'
    }
    dados.passos_resolucao.append(passo5)
    
    # Passo 6: Efetividade
    passo6 = {
        'titulo': '6. Efetividade da Aleta',
        'equacao': f'ε = Q_aleta/Q_sem_aleta = {Q_aleta:.3f}/{h*A_tr*theta_b:.3f} = {epsilon_a:.3f}',
        'explicacao': 'A efetividade compara a transferência de calor com a aleta versus sem a aleta. Valores > 1 indicam que a aleta melhora a transferência.',
        'valores': f'ε = {epsilon_a:.3f} ({"Recomendado" if epsilon_a > 2 else "Aceitável" if epsilon_a > 1 else "Não recomendado"})'
    }
    dados.passos_resolucao.append(passo6)
    
    return dados

__all__ = ['normalizar_tipo_aleta', 'calcular_eficiencia', 'mostrar_formula', 'gerar_distribuicao_temperatura', 'salvar_resultados', 'gerar_dados_didaticos']
