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

from tipos_aletas_config import obter_tipo_aleta, obter_nome_display, TIPOS_ALETAS

def obter_imagem(tipo_aleta):
    tid = obter_tipo_aleta(tipo_aleta)
    if tid and 1 <= tid <= 8:
        return f"static/aletas/{tid}.png"
    return "static/aletas/1.png"

def obter_formula(tipo_aleta):
    tid = obter_tipo_aleta(tipo_aleta)
    if tid and 1 <= tid <= 8:
        return f"static/formulas/{tid}.png"
    return "static/formulas/1.png"

def mostrar_formula(tipo_aleta):
    imagem_aleta = obter_imagem(tipo_aleta)
    formula_aleta = obter_formula(tipo_aleta)
    
    img = None
    formula_img = None

    if not TK_AVAILABLE:
        return

    root = ctk.CTk()
    root.title("Fórmula Utilizada")
    root.geometry("800x900")

    nome_desc = obter_nome_display(tipo_aleta)
    label = ctk.CTkLabel(root, text=f"{nome_desc.replace('_', ' ').title()}:", justify=ctk.LEFT, font=("Arial", 20, "bold"))
    label.pack(pady=10, padx=20)

    if imagem_aleta and os.path.exists(imagem_aleta):
        img_pil = Image.open(imagem_aleta)
        try:
            img_pil = img_pil.resize((600, 400), Image.Resampling.LANCZOS)
        except AttributeError:
            img_pil = img_pil.resize((600, 400))
        img = CTkImage(light_image=img_pil, dark_image=img_pil, size=(700, 400))
        panel = ctk.CTkLabel(root, image=img)
        panel.pack(side=ctk.TOP, padx=10, pady=10)

    if formula_aleta and os.path.exists(formula_aleta):
        formula_img_pil = Image.open(formula_aleta)
        try:
            formula_img_pil = formula_img_pil.resize((700, 400), Image.Resampling.LANCZOS)
        except AttributeError:
            formula_img_pil = formula_img_pil.resize((700, 400))
        formula_img = CTkImage(light_image=formula_img_pil, dark_image=formula_img_pil, size=(700, 400))
        panel_formula = ctk.CTkLabel(root, image=formula_img)
        panel_formula.pack(side=ctk.TOP, padx=10, pady=10)

    close_button = ctk.CTkButton(root, text="Fechar", command=root.destroy)
    close_button.pack(pady=20)

    root.mainloop()

def escolher_material():
    if not TK_AVAILABLE:
        return "Alumínio", 240
    root = ctk.CTk()
    root.title("Escolha o Material")
    root.geometry("500x500")

    def on_select():
        root.mat_tipo = material_var.get()
        root.destroy()

    def on_back():
        root.destroy()
        main()

    material_var = ctk.IntVar(value=1)

    materiais = {
        1: {"nome": "Alumínio", "k": 240},
        2: {"nome": "Cobre", "k": 386},
        3: {"nome": "Aço Inoxidável", "k": 16},
        4: {"nome": "Bronze", "k": 26},
        5: {"nome": "Ferro Fundido", "k": 52},
        6: {"nome": "Prata", "k": 429},
        7: {"nome": "Ouro", "k": 318},
        8: {"nome": "Ferro", "k": 80},
        9: {"nome": "Níquel", "k": 90},
        10: {"nome": "Chumbo", "k": 34},  
    }

    label = ctk.CTkLabel(root, text="Escolha o material (Condutividade Térmica W/m·K):", font=("Arial", 16))
    label.pack(pady=10)

    for i, mat in materiais.items():
        radio = ctk.CTkRadioButton(root, text=f"{i}. {mat['nome']} -- {mat['k']} W/mK", variable=material_var, value=i, command=on_select, font=("Arial", 15))
        radio.pack(anchor=ctk.W)

    root.mainloop()

    mat_tipo = getattr(root, 'mat_tipo', None)
    if mat_tipo is None:
        mat_tipo = 1
    return materiais[mat_tipo]["nome"], materiais[mat_tipo]["k"]

def calcular_taxa_calor_condicao(m, l, h, k, theta_b, T_L, T_inf, condicao_ponta):
    if condicao_ponta == 'adiabatica':
        return np.tanh(m * l)
    elif condicao_ponta == 'conveccao':
        numerador = np.sinh(m * l) + (h / (m * k)) * np.cosh(m * l)
        denominador = np.cosh(m * l) + (h / (m * k)) * np.sinh(m * l)
        if abs(denominador) < 1e-10:
            return float('inf')
        return numerador / denominador
    elif condicao_ponta == 'infinita':
        return 1.0
    elif condicao_ponta == 'temp_especificada':
        if T_L is None:
            T_L = (theta_b / 2.0) + T_inf
        theta_L = T_L - T_inf
        sinh_val = np.sinh(m * l)
        if abs(sinh_val) < 1e-10:
            return 1.0
        return (np.cosh(m * l) - (theta_L / theta_b)) / sinh_val
    else:
        return np.tanh(m * l)

def normalizar_tipo_aleta(tipo_str):
    """
    Normaliza qualquer formato ou identificador de aleta para o nome de exibição canônico.
    """
    tid = obter_tipo_aleta(tipo_str)
    if tid and tid in TIPOS_ALETAS:
        return TIPOS_ALETAS[tid]['nome_display']
    return "1)aletas retangulares retas"

def calcular_eficiencia(tipo_aleta, h, k, l, t=None, w=None, D=None, r1=None, r2=None, T_b=None, T_inf=None, condicao_ponta='adiabatica', T_L=None):
    """
    Cálculo rigoroso de eficiência, transferência de calor e métricas para as 8 geometrias.
    Cada geometria é identificada estritamente pelo seu tipo_id (1-8), sem inferência por texto
    e sem contaminação entre campos de geometrias distintas.
    """
    tipo_id = obter_tipo_aleta(tipo_aleta)
    if tipo_id is None:
        tipo_id = 1
    
    # Valores de contorno padrão seguros
    T_b = 100.0 if T_b is None else float(T_b)
    T_inf = 25.0 if T_inf is None else float(T_inf)
    h = 25.0 if (h is None or float(h) <= 0) else float(h)
    k = 222.0 if (k is None or float(k) <= 0) else float(k)
    l = 0.05 if (l is None or float(l) <= 0) else float(l)
    theta_b = T_b - T_inf

    # =========================================================================
    # TIPO 1: Aleta Retangular Reta (Plana de Seção Uniforme) -> w, L, t
    # =========================================================================
    if tipo_id == 1:
        w_val = 0.1 if (w is None or float(w) <= 0) else float(w)
        t_val = 0.002 if (t is None or float(t) <= 0) else float(t)
        
        P = 2.0 * (w_val + t_val)
        A_tr = w_val * t_val
        m = np.sqrt(h * P / (k * A_tr))
        M = np.sqrt(h * P * k * A_tr) * theta_b
        
        Lc = l + t_val / 2.0
        Ap = Lc * t_val
        
        if condicao_ponta == 'conveccao':
            fator_cond = calcular_taxa_calor_condicao(m, l, h, k, theta_b, T_L, T_inf, 'conveccao')
            Q_aleta = M * fator_cond
            A_aleta = 2.0 * w_val * Lc
            eta_aleta = np.tanh(m * Lc) / (m * Lc) if (m * Lc) > 0 else 1.0
        elif condicao_ponta == 'infinita':
            Q_aleta = M * 1.0
            A_aleta = 2.0 * w_val * l
            eta_aleta = 1.0 / (m * l) if (m * l) > 0 else 1.0
        elif condicao_ponta == 'temp_especificada':
            fator_cond = calcular_taxa_calor_condicao(m, l, h, k, theta_b, T_L, T_inf, 'temp_especificada')
            Q_aleta = M * fator_cond
            A_aleta = 2.0 * w_val * l
            Q_max = h * A_aleta * theta_b
            eta_aleta = Q_aleta / Q_max if Q_max > 0 else 0.0
        else:  # 'adiabatica'
            Q_aleta = M * np.tanh(m * l)
            A_aleta = 2.0 * w_val * l
            eta_aleta = np.tanh(m * l) / (m * l) if (m * l) > 0 else 1.0
            
        Q_sem_aleta = h * A_tr * theta_b
        epsilon_a = Q_aleta / Q_sem_aleta if Q_sem_aleta > 0 else 0.0
        dados_didaticos = gerar_dados_didaticos(tipo_id, h, k, l, t_val, w_val, None, None, None, T_b, T_inf, condicao_ponta, m, P, A_tr, eta_aleta, Q_aleta, epsilon_a)
        return eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr, dados_didaticos

    # =========================================================================
    # TIPO 2: Aleta Triangular Reta -> w, L, t (NÃO utiliza D)
    # =========================================================================
    elif tipo_id == 2:
        w_val = 0.1 if (w is None or float(w) <= 0) else float(w)
        t_val = 0.002 if (t is None or float(t) <= 0) else float(t)
        
        P = 2.0 * (w_val + t_val)
        A_tr = w_val * t_val
        A_aleta = 2.0 * w_val * np.sqrt(l**2 + (t_val / 2.0)**2)
        
        # Parâmetro m característico de aleta reta triangular (Incropera Tabela 3.5)
        m = np.sqrt(2.0 * h / (k * t_val))
        ml = m * l
        
        try:
            val_i0 = i0(2.0 * ml)
            val_i1 = i1(2.0 * ml)
            eta_aleta = (1.0 / ml) * (val_i1 / val_i0) if (ml > 0 and val_i0 > 0) else 1.0
        except (OverflowError, ZeroDivisionError):
            eta_aleta = 1.0 / ml if ml > 10 else np.tanh(ml) / ml
            
        eta_aleta = max(0.0, min(1.0, float(eta_aleta)))
        Q_max = h * A_aleta * theta_b
        Q_aleta = eta_aleta * Q_max
        Q_sem_aleta = h * A_tr * theta_b
        epsilon_a = Q_aleta / Q_sem_aleta if Q_sem_aleta > 0 else 0.0
        dados_didaticos = gerar_dados_didaticos(tipo_id, h, k, l, t_val, w_val, None, None, None, T_b, T_inf, condicao_ponta, m, P, A_tr, eta_aleta, Q_aleta, epsilon_a)
        return eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr, dados_didaticos

    # =========================================================================
    # TIPO 3: Aleta Parabólica Reta -> w, L, t (NÃO utiliza D)
    # =========================================================================
    elif tipo_id == 3:
        w_val = 0.1 if (w is None or float(w) <= 0) else float(w)
        t_val = 0.002 if (t is None or float(t) <= 0) else float(t)
        
        P = 2.0 * (w_val + t_val)
        A_tr = w_val * t_val
        C1 = np.sqrt(1.0 + (t_val / l)**2)
        A_aleta = w_val * l * (C1 + (l / t_val) * np.log(t_val / l + C1))
        
        m = np.sqrt(2.0 * h / (k * t_val))
        ml = m * l
        
        # Equação exata Incropera Tabela 3.5: eta = 2 / (sqrt(4*(ml)^2 + 1) + 1)
        eta_aleta = 2.0 / (np.sqrt(4.0 * (ml**2) + 1.0) + 1.0)
        eta_aleta = max(0.0, min(1.0, float(eta_aleta)))
        
        Q_max = h * A_aleta * theta_b
        Q_aleta = eta_aleta * Q_max
        Q_sem_aleta = h * A_tr * theta_b
        epsilon_a = Q_aleta / Q_sem_aleta if Q_sem_aleta > 0 else 0.0
        dados_didaticos = gerar_dados_didaticos(tipo_id, h, k, l, t_val, w_val, None, None, None, T_b, T_inf, condicao_ponta, m, P, A_tr, eta_aleta, Q_aleta, epsilon_a)
        return eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr, dados_didaticos

    # =========================================================================
    # TIPO 4: Aleta Circular de Perfil Retangular (Anular) -> r1, r2, t (NÃO usa w, NÃO usa D)
    # =========================================================================
    elif tipo_id == 4:
        r1_val = 0.01 if (r1 is None or float(r1) <= 0) else float(r1)
        r2_val = 0.02 if (r2 is None or float(r2) <= 0) else float(r2)
        if r2_val <= r1_val:
            r2_val = r1_val + 0.01
        t_val = 0.002 if (t is None or float(t) <= 0) else float(t)
        
        l_eff = r2_val - r1_val
        r2c = r2_val + t_val / 2.0
        Lc = l_eff + t_val / 2.0
        
        A_tr = 2.0 * np.pi * r1_val * t_val
        P = 2.0 * np.pi * (r1_val + r2_val)
        A_aleta = 2.0 * np.pi * (r2c**2 - r1_val**2)
        
        m = np.sqrt(2.0 * h / (k * t_val))
        
        # Incropera Tabela 3.5: Solução exata com funções de Bessel modificadas
        try:
            u1 = m * r1_val
            u2 = m * r2c
            C2 = (2.0 * r1_val / m) / (r2c**2 - r1_val**2)
            num = k1(u1) * i1(u2) - i1(u1) * k1(u2)
            den = i0(u1) * k1(u2) + k0(u1) * i1(u2)
            if abs(den) > 1e-12:
                eta_aleta = C2 * (num / den)
            else:
                eta_aleta = np.tanh(m * Lc) / (m * Lc)
        except Exception:
            eta_aleta = np.tanh(m * Lc) / (m * Lc)
            
        eta_aleta = max(0.0, min(1.0, float(eta_aleta)))
        Q_max = h * A_aleta * theta_b
        Q_aleta = eta_aleta * Q_max
        Q_sem_aleta = h * A_tr * theta_b
        epsilon_a = Q_aleta / Q_sem_aleta if Q_sem_aleta > 0 else 0.0
        dados_didaticos = gerar_dados_didaticos(tipo_id, h, k, l_eff, t_val, None, None, r1_val, r2_val, T_b, T_inf, condicao_ponta, m, P, A_tr, eta_aleta, Q_aleta, epsilon_a)
        return eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr, dados_didaticos

    # =========================================================================
    # TIPO 5: Aleta de Pino de Perfil Retangular (Cilíndrica Uniforme) -> D, L (NÃO usa w, NÃO usa t)
    # =========================================================================
    elif tipo_id == 5:
        D_val = 0.01 if (D is None or float(D) <= 0) else float(D)
        
        P = np.pi * D_val
        A_tr = np.pi * (D_val**2) / 4.0
        m = np.sqrt(h * P / (k * A_tr))
        M = np.sqrt(h * P * k * A_tr) * theta_b
        
        Lc = l + D_val / 4.0
        
        if condicao_ponta == 'conveccao':
            fator_cond = calcular_taxa_calor_condicao(m, l, h, k, theta_b, T_L, T_inf, 'conveccao')
            Q_aleta = M * fator_cond
            A_aleta = np.pi * D_val * Lc
            eta_aleta = np.tanh(m * Lc) / (m * Lc) if (m * Lc) > 0 else 1.0
        elif condicao_ponta == 'infinita':
            Q_aleta = M * 1.0
            A_aleta = np.pi * D_val * l
            eta_aleta = 1.0 / (m * l) if (m * l) > 0 else 1.0
        elif condicao_ponta == 'temp_especificada':
            fator_cond = calcular_taxa_calor_condicao(m, l, h, k, theta_b, T_L, T_inf, 'temp_especificada')
            Q_aleta = M * fator_cond
            A_aleta = np.pi * D_val * l
            Q_max = h * A_aleta * theta_b
            eta_aleta = Q_aleta / Q_max if Q_max > 0 else 0.0
        else:  # 'adiabatica'
            Q_aleta = M * np.tanh(m * l)
            A_aleta = np.pi * D_val * l
            eta_aleta = np.tanh(m * l) / (m * l) if (m * l) > 0 else 1.0
            
        Q_sem_aleta = h * A_tr * theta_b
        epsilon_a = Q_aleta / Q_sem_aleta if Q_sem_aleta > 0 else 0.0
        dados_didaticos = gerar_dados_didaticos(tipo_id, h, k, l, None, None, D_val, None, None, T_b, T_inf, condicao_ponta, m, P, A_tr, eta_aleta, Q_aleta, epsilon_a)
        return eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr, dados_didaticos

    # =========================================================================
    # TIPO 6: Aleta de Pino de Perfil Triangular (Cônica) -> D, L (NÃO usa w, NÃO usa t)
    # =========================================================================
    elif tipo_id == 6:
        D_val = 0.01 if (D is None or float(D) <= 0) else float(D)
        
        P = np.pi * D_val
        A_tr = np.pi * (D_val**2) / 4.0
        A_aleta = (np.pi * D_val / 2.0) * np.sqrt(l**2 + (D_val / 2.0)**2)
        
        m = np.sqrt(4.0 * h / (k * D_val))
        ml = m * l
        
        # Incropera Tabela 3.5: eta = (2 / (m*L)) * (I2(2*m*L) / I1(2*m*L))
        # Usando I2(z) = I0(z) - (2/z)*I1(z)
        try:
            z = 2.0 * ml
            val_i0 = i0(z)
            val_i1 = i1(z)
            val_i2 = val_i0 - (2.0 / z) * val_i1 if z > 0 else 0.0
            eta_aleta = (2.0 / ml) * (val_i2 / val_i1) if (ml > 0 and val_i1 > 0) else 1.0
        except (OverflowError, ZeroDivisionError):
            eta_aleta = 1.0 / ml if ml > 10 else np.tanh(ml) / ml
            
        eta_aleta = max(0.0, min(1.0, float(eta_aleta)))
        Q_max = h * A_aleta * theta_b
        Q_aleta = eta_aleta * Q_max
        Q_sem_aleta = h * A_tr * theta_b
        epsilon_a = Q_aleta / Q_sem_aleta if Q_sem_aleta > 0 else 0.0
        dados_didaticos = gerar_dados_didaticos(tipo_id, h, k, l, None, None, D_val, None, None, T_b, T_inf, condicao_ponta, m, P, A_tr, eta_aleta, Q_aleta, epsilon_a)
        return eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr, dados_didaticos

    # =========================================================================
    # TIPO 7: Aleta de Pino de Perfil Parabólico -> D, L (NÃO usa w, NÃO usa t)
    # =========================================================================
    elif tipo_id == 7:
        D_val = 0.01 if (D is None or float(D) <= 0) else float(D)
        
        P = np.pi * D_val
        A_tr = np.pi * (D_val**2) / 4.0
        C3 = 1.0 + 2.0 * (D_val / l)**2
        C4 = np.sqrt(1.0 + (D_val / l)**2)
        A_aleta = (np.pi * l**3) / (8.0 * D_val) * (C3 * C4 - (l / (2.0 * D_val)) * np.log((2.0 * D_val * C4 / l + C3)))
        
        m = np.sqrt(4.0 * h / (k * D_val))
        ml = m * l
        
        # Incropera Tabela 3.5: eta = 2 / (sqrt(4/9 * (ml)^2 + 1) + 1)
        eta_aleta = 2.0 / (np.sqrt((4.0 / 9.0) * (ml**2) + 1.0) + 1.0)
        eta_aleta = max(0.0, min(1.0, float(eta_aleta)))
        
        Q_max = h * A_aleta * theta_b
        Q_aleta = eta_aleta * Q_max
        Q_sem_aleta = h * A_tr * theta_b
        epsilon_a = Q_aleta / Q_sem_aleta if Q_sem_aleta > 0 else 0.0
        dados_didaticos = gerar_dados_didaticos(tipo_id, h, k, l, None, None, D_val, None, None, T_b, T_inf, condicao_ponta, m, P, A_tr, eta_aleta, Q_aleta, epsilon_a)
        return eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr, dados_didaticos

    # =========================================================================
    # TIPO 8: Aleta de Pino Parabólica Ponta Arredondada -> D, L (NÃO usa w, NÃO usa t)
    # =========================================================================
    elif tipo_id == 8:
        D_val = 0.01 if (D is None or float(D) <= 0) else float(D)
        
        P = np.pi * D_val
        A_tr = np.pi * (D_val**2) / 4.0
        A_aleta = (np.pi * D_val**4 / (96.0 * l**2)) * ((16.0 * (l / D_val)**2 + 1.0)**(1.5) - 1.0)
        
        m = np.sqrt(4.0 * h / (k * D_val))
        ml = m * l
        
        # Incropera: Solução exata com funções de Bessel de ordem fracionária
        try:
            z = (4.0 / 3.0) * ml
            i_pos = sp.iv(0.75, z)
            i_neg = sp.iv(-0.25, z)
            if ml > 0 and abs(i_neg) > 1e-12:
                eta_aleta = (3.0 / (2.0 * ml)) * (i_pos / i_neg)
            else:
                eta_aleta = 2.0 / (np.sqrt((4.0 / 9.0) * (ml**2) + 1.0) + 1.0)
        except Exception:
            eta_aleta = 2.0 / (np.sqrt((4.0 / 9.0) * (ml**2) + 1.0) + 1.0)
            
        eta_aleta = max(0.0, min(1.0, float(eta_aleta)))
        Q_max = h * A_aleta * theta_b
        Q_aleta = eta_aleta * Q_max
        Q_sem_aleta = h * A_tr * theta_b
        epsilon_a = Q_aleta / Q_sem_aleta if Q_sem_aleta > 0 else 0.0
        dados_didaticos = gerar_dados_didaticos(tipo_id, h, k, l, None, None, D_val, None, None, T_b, T_inf, condicao_ponta, m, P, A_tr, eta_aleta, Q_aleta, epsilon_a)
        return eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr, dados_didaticos

    # Fallback genérico seguro
    return 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, None


# =============================================================================
# FUNÇÕES DE DISTRIBUIÇÃO DE TEMPERATURA T(x)
# =============================================================================

def T_aleta_retangular(x, l, T_b, T_inf, h, k, t, w):
    """Tipo 1: Retangular Reta (w, t, L)"""
    P = 2.0 * (w + t)
    A_tr = w * t
    m = np.sqrt(h * P / (k * A_tr))
    return T_inf + (T_b - T_inf) * np.cosh(m * (l - x)) / np.cosh(m * l)

def T_aleta_triangular(x, l, T_b, T_inf, h, k, t, w):
    """Tipo 2: Triangular Reta (w, t, L)"""
    m = np.sqrt(2.0 * h / (k * t))
    return T_inf + (T_b - T_inf) * np.cosh(m * np.sqrt(2.0) * (l - x)) / np.cosh(m * np.sqrt(2.0) * l)

def T_aleta_parabolica(x, l, T_b, T_inf, h, k, t, w):
    """Tipo 3: Parabólica Reta (w, t, L)"""
    m = np.sqrt(2.0 * h / (k * t))
    return T_inf + (T_b - T_inf) * np.cosh(m * np.sqrt(3.0) * (l - x)) / np.cosh(m * np.sqrt(3.0) * l)

def T_aleta_circular(x, l, T_b, T_inf, h, k, t, r1, r2):
    """Tipo 4: Circular de Perfil Retangular (r1, r2, t)"""
    m = np.sqrt(2.0 * h / (k * t))
    return T_inf + (T_b - T_inf) * np.cosh(m * (l - x)) / np.cosh(m * l)

def T_aleta_pino_retangular(x, l, T_b, T_inf, h, k, D):
    """Tipo 5: Pino de Perfil Retangular / Cilíndrico Uniforme (D, L)"""
    P = np.pi * D
    A_tr = np.pi * (D**2) / 4.0
    m = np.sqrt(h * P / (k * A_tr))
    return T_inf + (T_b - T_inf) * np.cosh(m * (l - x)) / np.cosh(m * l)

# Alias para compatibilidade reversa com chamadas legadas
def T_aleta_perfil_retangular(x, l, T_b, T_inf, h, k, w=None, t=None, D=None):
    if D is not None and D > 0:
        return T_aleta_pino_retangular(x, l, T_b, T_inf, h, k, D)
    elif w is not None and t is not None:
        return T_aleta_retangular(x, l, T_b, T_inf, h, k, t, w)
    else:
        d_fallback = D if D else (w if w else 0.01)
        return T_aleta_pino_retangular(x, l, T_b, T_inf, h, k, d_fallback)

def T_aleta_perfil_triangular(x, l, T_b, T_inf, h, k, D):
    """Tipo 6: Pino Triangular / Cônica (D, L)"""
    m = np.sqrt(4.0 * h / (k * D))
    return T_inf + (T_b - T_inf) * np.cosh(m * np.sqrt(2.0) * (l - x)) / np.cosh(m * np.sqrt(2.0) * l)

def T_aleta_perfil_parabolico(x, L, T_b, T_inf, h, k, D):
    """Tipo 7: Pino Parabólico (D, L)"""
    m = np.sqrt(4.0 * h / (k * D))
    return T_inf + (T_b - T_inf) * np.cosh(m * np.sqrt(3.0) * (L - x)) / np.cosh(m * np.sqrt(3.0) * L)

def T_aleta_pino_parabolico(x, L, T_b, T_inf, h, k, D):
    """Tipo 8: Pino Parabólico com Ponta Arredondada (D, L)"""
    m = np.sqrt(4.0 * h / (k * D))
    return T_inf + (T_b - T_inf) * np.cosh(m * (L - x)) / np.cosh(m * L)


def calcular_Tx_para_tipo(tipo_aleta, x, l, T_b, T_inf, h, k, t=None, w=None, D=None, r1=None, r2=None):
    """Calcula T(x) utilizando o ID geométrico estrito da aleta."""
    tid = obter_tipo_aleta(tipo_aleta)
    if tid == 1:
        return T_aleta_retangular(x, l, T_b, T_inf, h, k, t or 0.002, w or 0.1)
    elif tid == 2:
        return T_aleta_triangular(x, l, T_b, T_inf, h, k, t or 0.002, w or 0.1)
    elif tid == 3:
        return T_aleta_parabolica(x, l, T_b, T_inf, h, k, t or 0.002, w or 0.1)
    elif tid == 4:
        r1_v = r1 or 0.01
        r2_v = r2 or (r1_v + l if l else 0.02)
        return T_aleta_circular(x, l, T_b, T_inf, h, k, t or 0.002, r1_v, r2_v)
    elif tid == 5:
        return T_aleta_pino_retangular(x, l, T_b, T_inf, h, k, D or 0.01)
    elif tid == 6:
        return T_aleta_perfil_triangular(x, l, T_b, T_inf, h, k, D or 0.01)
    elif tid == 7:
        return T_aleta_perfil_parabolico(x, l, T_b, T_inf, h, k, D or 0.01)
    elif tid == 8:
        return T_aleta_pino_parabolico(x, l, T_b, T_inf, h, k, D or 0.01)
    else:
        return np.full_like(x, T_inf)


def sgerar_distribuicao_temperatura(sele_aleta, h, k, l, t, w, D, r1, r2, T_b, T_inf, smateriais):
    x = np.linspace(0, l, 100)
    plt.figure()

    aleta_nome = sele_aleta[0] if isinstance(sele_aleta, list) else sele_aleta
    for material, valor_k in zip(smateriais, k):
        T = calcular_Tx_para_tipo(aleta_nome, x, l, T_b, T_inf, h, valor_k, t, w, D, r1, r2)
        plt.plot(x, T, label=f'{material} (k={valor_k})')

    plt.xlabel('Comprimento da aleta (m)')
    plt.ylabel('Temperatura (°C)')
    plt.title('Distribuição de Temperatura ao Longo da Aleta')
    plt.legend()
    plt.grid(True)

    os.makedirs('static', exist_ok=True)
    grafico_path = f'static/distribuicao_temperatura_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.png'
    plt.savefig(grafico_path)
    plt.close()
    return grafico_path


def gerar_distribuicao_temperatura(tipos_aletas, h, k, l, t, w, D, r1, r2, T_b, T_inf):
    x = np.linspace(0, l, 100)
    plt.figure()

    for tipo_aleta in tipos_aletas:
        T_x = calcular_Tx_para_tipo(tipo_aleta, x, l, T_b, T_inf, h, k, t, w, D, r1, r2)
        plt.plot(x, T_x, label=obter_nome_display(tipo_aleta))

    plt.xlabel('Comprimento (m)')
    plt.ylabel('Temperatura (°C)')
    plt.title('Distribuição de Temperatura')
    plt.grid(True)
    plt.legend()

    os.makedirs('static/graficos', exist_ok=True)
    grafico_path = 'static/graficos/distribuicao_temperatura.png'
    plt.savefig(grafico_path)
    plt.close()
    return grafico_path


def salvar_resultados(filepath, tipos_aletas, h, k, l, t, w, D, r1, r2, T_b, T_inf, resultados):
    try:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write("Resultados das Aletas\n")
            for resultado in resultados:
                if len(resultado) == 8:
                    tipo_aleta, eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr = resultado
                    file.write(f"Tipo de Aleta: {obter_nome_display(tipo_aleta)}\n")
                    file.write(f"Eficiência (eta_aleta): {eta_aleta:.6f}\n")
                    file.write(f"Taxa de Transferência de Calor (Q_aleta): {Q_aleta:.6f} W\n")
                    file.write(f"Efetividade (epsilon_a): {epsilon_a:.6f}\n")
                    file.write(f"Parâmetro m: {m:.6f} m^-1\n")
                    file.write(f"Perímetro P: {P:.6f} m\n")
                    file.write(f"Área Transversal A_tr: {A_tr:.9f} m^2\n")
                else:
                    tipo_aleta, eta_aleta, Q_aleta, A_aleta = resultado
                    file.write(f"Tipo de Aleta: {obter_nome_display(tipo_aleta)}\n")
                    file.write(f"Eficiência (eta_aleta): {eta_aleta:.6f}\n")
                    file.write(f"Taxa de Transferência de Calor (Q_aleta): {Q_aleta:.6f} W\n")
                
                file.write("Comprimento (m) x Temperatura (°C):\n")
                x = np.linspace(0, l, 15)
                T_x = calcular_Tx_para_tipo(tipo_aleta, x, l, T_b, T_inf, h, k, t, w, D, r1, r2)
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
            f.write(f"Seleção de Aletas: {', '.join([obter_nome_display(a) for a in sele_aleta])}\n")
            for resultado_sele in resultados_sele:
                if len(resultado_sele) == 10:
                    tipo_aleta, material, valor_k, eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr = resultado_sele
                    f.write(f"Tipo de Aleta: {obter_nome_display(tipo_aleta)}\n")
                    f.write(f"Material: {material}\n")
                    f.write(f"k: {valor_k}\n")
                    f.write(f"Eficiência da Aleta: {eta_aleta:.6f}\n")
                    f.write(f"Taxa de Transferência de Calor: {Q_aleta:.6f} W\n")
                    f.write(f"Área da Aleta: {A_aleta:.6f} m²\n")
                    f.write(f"Efetividade (epsilon_a): {epsilon_a:.6f}\n")
                    f.write(f"Parâmetro m: {m:.6f} m^-1\n")
                    f.write(f"Perímetro P: {P:.6f} m\n")
                    f.write(f"Área Transversal A_tr: {A_tr:.9f} m^2\n")
                else:
                    tipo_aleta, material, valor_k, eta_aleta, Q_aleta, A_aleta = resultado_sele
                    f.write(f"Tipo de Aleta: {obter_nome_display(tipo_aleta)}\n")
                    f.write(f"Material: {material}\n")
                    f.write(f"k: {valor_k}\n")
                    f.write(f"Eficiência da Aleta: {eta_aleta:.6f}\n")
                    f.write(f"Taxa de Transferência de Calor: {Q_aleta:.6f} W\n")
                    f.write(f"Área da Aleta: {A_aleta:.6f} m²\n")
                
                f.write("Comprimento (m) x Temperatura (°C):\n")
                x = np.linspace(0, l, 15)
                T_x = calcular_Tx_para_tipo(tipo_aleta, x, l, T_b, T_inf, h, valor_k, t, w, D, r1, r2)
                for xi, Ti in zip(x, T_x):
                    f.write(f"{xi:.6f} m: {Ti:.6f} °C\n")
                f.write("\n")
    except Exception as e_s:
        print(f"[AVISO] Erro ao salvar selerelatorio em {filepath}: {e_s}")


def gerar_dados_didaticos(tipo_id_ou_nome, h, k, l, t=None, w=None, D=None, r1=None, r2=None, T_b=100.0, T_inf=25.0, condicao_ponta='adiabatica', m=1.0, P=1.0, A_tr=1.0, eta_aleta=1.0, Q_aleta=1.0, epsilon_a=1.0):
    """Gera dados didáticos com resolução passo a passo estritamente baseada no ID da geometria (1 a 8)."""
    tid = obter_tipo_aleta(tipo_id_ou_nome) or 1
    tipo_info = TIPOS_ALETAS.get(tid, TIPOS_ALETAS[1])
    
    class DadosDidaticos:
        def __init__(self):
            self.tipo_aleta_original = tipo_info['nome_display']
            self.tipo_aleta_mapeado = tipo_info['descricao']
            self.metodo = "Análise de Transferência de Calor em Aletas (Incropera & Çengel)"
            self.condicao_ponta = condicao_ponta
            self.passos_resolucao = []
            self.q_base = Q_aleta
            self.eficiencia = eta_aleta
            self.efetividade = epsilon_a
    
    dados = DadosDidaticos()
    theta_b = T_b - T_inf
    
    # Passo 1: Parâmetros térmicos de base
    dados.passos_resolucao.append({
        'titulo': '1. Identificação dos Parâmetros Térmicos',
        'equacao': f'θ_b = T_b - T_∞ = {T_b:.2f} - {T_inf:.2f} = {theta_b:.2f} °C',
        'explicacao': 'Diferença de temperatura na base da aleta, que representa o potencial térmico motriz.',
        'valores': f'h = {h:.2f} W/m²·K, k = {k:.2f} W/m·K, L = {l:.4f} m'
    })
    
    # Passo 2: Propriedades geométricas específicas de cada geometria
    if tid in [1, 2, 3]:
        dados.passos_resolucao.append({
            'titulo': f'2. Geometria: {tipo_info["descricao"]}',
            'equacao': f'P = 2(w + t) = 2({w} + {t}) = {P:.6f} m | A_tr = w × t = {w} × {t} = {A_tr:.8f} m²',
            'explicacao': f'Perfil com largura w = {w} m e espessura t = {t} m. Perímetro molhado e área transversal na base.',
            'valores': f'w = {w} m, t = {t} m, L = {l} m'
        })
    elif tid == 4:
        dados.passos_resolucao.append({
            'titulo': f'2. Geometria: {tipo_info["descricao"]}',
            'equacao': f'A_tr = 2π·r₁·t = 2π·({r1})·({t}) = {A_tr:.8f} m²',
            'explicacao': f'Aleta anular concêntrica montada sobre tubo de raio interno r₁ = {r1} m e raio externo r₂ = {r2} m.',
            'valores': f'r₁ = {r1} m, r₂ = {r2} m, t = {t} m'
        })
    else:  # 5, 6, 7, 8
        dados.passos_resolucao.append({
            'titulo': f'2. Geometria: {tipo_info["descricao"]}',
            'equacao': f'P = π·D = π·({D}) = {P:.6f} m | A_tr = π·D²/4 = {A_tr:.8f} m²',
            'explicacao': f'Aleta de pino com diâmetro de base D = {D} m e comprimento L = {l} m.',
            'valores': f'D = {D} m, L = {l} m'
        })
        
    # Passo 3: Parâmetro m
    dados.passos_resolucao.append({
        'titulo': '3. Parâmetro Característico (m)',
        'equacao': f'm = √(h·P / (k·A_tr)) = {m:.6f} m⁻¹',
        'explicacao': 'Mede a taxa de decaimento de temperatura ao longo da aleta.',
        'valores': f'm·L = {m * l:.4f} (adimensional)'
    })
    
    # Passo 4: Eficiência
    dados.passos_resolucao.append({
        'titulo': f'4. Eficiência da Aleta (ηₐ)',
        'equacao': f'ηₐ = {eta_aleta:.6f} ({eta_aleta*100:.2f}%)',
        'explicacao': f'Calculada pelas equações exatas para a geometria {tipo_info["nome_display"]}.',
        'valores': f'ηₐ = {eta_aleta:.4f}'
    })
    
    # Passo 5: Taxa de transferência de calor
    dados.passos_resolucao.append({
        'titulo': '5. Taxa de Transferência de Calor (Q_aleta)',
        'equacao': f'Q_aleta = {Q_aleta:.4f} W',
        'explicacao': 'Calor total transferido pela aleta para o fluido.',
        'valores': f'Q = {Q_aleta:.4f} W'
    })
    
    # Passo 6: Efetividade
    dados.passos_resolucao.append({
        'titulo': '6. Efetividade da Aleta (εₐ)',
        'equacao': f'εₐ = Q_aleta / Q_sem_aleta = {epsilon_a:.4f}',
        'explicacao': 'Razão entre o calor transferido com aleta e o calor que seria transferido pela base desprovida de aleta.',
        'valores': f'εₐ = {epsilon_a:.2f} ({"Excelente (≥ 2)" if epsilon_a >= 2 else "Aceitável (> 1)" if epsilon_a > 1 else "Ineficiente (≤ 1)"})'
    })
    
    return dados

__all__ = [
    'normalizar_tipo_aleta', 'calcular_eficiencia', 'mostrar_formula',
    'gerar_distribuicao_temperatura', 'sgerar_distribuicao_temperatura',
    'salvar_resultados', 'salvar_sresultados', 'gerar_dados_didaticos',
    'T_aleta_retangular', 'T_aleta_triangular', 'T_aleta_parabolica',
    'T_aleta_circular', 'T_aleta_pino_retangular', 'T_aleta_perfil_retangular',
    'T_aleta_perfil_triangular', 'T_aleta_perfil_parabolico', 'T_aleta_pino_parabolico',
    'obter_imagem', 'obter_formula'
]

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

    # Função lambda chamada aqui para processar inputs
    # Nota: a função on_submit original foi assumida existir e ser compatível
    def on_submit_local():
        from __main__ import on_submit
        on_submit(h_entry, l_entry, t_entry, w_entry, D_entry, r1_entry, r2_entry, T_inf_entry, T_b_entry, error_label, root)
    
    submit_button = ctk.CTkButton(button_frame, text="Confirmar", command=on_submit_local)
    submit_button.pack(side=ctk.LEFT, padx=5)

    back_button = ctk.CTkButton(button_frame, text="Voltar", command=lambda: [root.destroy(), main()])
    back_button.pack(side=ctk.LEFT, padx=5)

    root.mainloop()

if __name__ == "__main__":
    main()
