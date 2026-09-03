import os
import json
os.environ.setdefault('MPLCONFIGDIR', '/tmp/matplotlib')

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from modelo3 import calcular_eficiencia, mostrar_formula, salvar_resultados, salvar_sresultados, normalizar_tipo_aleta
from visualizacao_plotly import (
    gerar_grafico_temperatura_interativo, 
    gerar_grafico_temperatura_multiplos_materiais,
    extrair_dados_curvas_json_interativo,
    extrair_dados_curvas_json_multiplos
)
from metricas_engenharia import calcular_metricas_engenharia, interpretar_metricas, MATERIAIS_DB, DICIONARIO_MATERIAIS_ID
from mudanca_fase_calculadora import calcular_mudanca_fase
from arranjos_tubos_calculadora import calcular_arranjo_tubos
from escoamento_interno import escoamento_interno_tubo_circular
from escoamento_dutos import escoamento_interno_duto
from tipos_aletas_config import (obter_tipo_aleta, validar_campos_obrigatorios, 
                                 obter_campos_formulario, obter_info_tipo, TIPOS_ALETAS, LISTA_TIPOS_ORDENADA,
                                 determinar_campos_para_multiplas_aletas, obter_nome_display)
import numpy as np
import scipy.special as sp
import time
import threading

def find_folder(folder_name):
    base = os.path.abspath(os.path.dirname(__file__))
    candidates = [
        os.path.join(base, folder_name),
        os.path.join(base, 'V29', folder_name),
        os.path.join(os.getcwd(), folder_name),
        os.path.join(os.getcwd(), 'V29', folder_name),
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.isdir(c):
            return c
    return candidates[0]

static_dir = find_folder('static')
template_dir = find_folder('templates')

app = handler = Flask(
    __name__,
    static_folder=static_dir,
    template_folder=template_dir,
    static_url_path='/static'
)
app.secret_key = 'transferencia-calor-laboratorio-flask-2025'

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.errorhandler(Exception)
def handle_all_exceptions(e):
    import traceback
    err_tb = traceback.format_exc()
    print(f"[ERRO 500 SERVER]: {err_tb}")
    return f'''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head><meta charset="utf-8"><title>Erro no Servidor</title></head>
    <body style="font-family: sans-serif; background: #fdf2f2; padding: 30px;">
        <div style="max-width: 800px; margin: 0 auto; background: white; border: 2px solid #e53935; border-radius: 12px; padding: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <h2 style="color: #c62828; margin-top: 0;">⚠️ Detalhes do Erro Interno (500)</h2>
            <p><strong>Exceção:</strong> {type(e).__name__}: {str(e)}</p>
            <pre style="background: #1e1e1e; color: #f8f8f2; padding: 15px; border-radius: 8px; overflow-x: auto; font-size: 12px; line-height: 1.4;">{err_tb}</pre>
            <a href="/" style="display: inline-block; margin-top: 15px; padding: 10px 20px; background: #1976d2; color: white; text-decoration: none; border-radius: 6px; font-weight: bold;">← Voltar para o Início</a>
        </div>
    </body>
    </html>
    ''', 500

@app.after_request
def add_no_cache_headers(resp):
    """Evita que o navegador segure HTML/JS/CSS antigo durante desenvolvimento."""
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

# Configurações globais extras disponíveis nos templates
app.jinja_env.globals.update(zip=zip)



# Cache com controle de concorrência (thread-safe) para monitoramento de temperaturas
monitoring_lock = threading.Lock()
monitoring_cache = {
    't1': 0.0,
    't2': 0.0,
    't3': 0.0,
    't4': 0.0,
    't5': 0.0,
    't6': 0.0
}

# =============================================================================
# FUNÇÕES DE VALIDAÇÃO E UTILITÁRIOS
# =============================================================================

def validar_parametros_fisicos(h, k, T_b, T_inf, l, t=None, w=None, r1=None, r2=None, D=None, T_L=None):
    
    errors = []
    
    # Validação do coeficiente de convecção (h)
    if h <= 0:
        errors.append("Coeficiente de convecção (h) deve ser positivo")
    elif h > 10000:
        errors.append("Coeficiente de convecção (h) muito alto (máx. 10.000 W/m²·K)")
    
    # Validação da condutividade térmica (k)
    if k <= 0:
        errors.append("Condutividade térmica (k) deve ser positiva")
    elif k > 500:
        errors.append("Condutividade térmica (k) muito alta (máx. 500 W/m·K)")
    
    # Validação das temperaturas
    if T_b < -273.15:
        errors.append("Temperatura da base (T_b) não pode ser menor que -273.15°C")
    if T_inf < -273.15:
        errors.append("Temperatura do ambiente (T_inf) não pode ser menor que -273.15°C")
    if T_b == T_inf:
        errors.append("Temperatura da base deve ser diferente da temperatura ambiente")
    
    # Validação do comprimento
    if l is not None:
        if l <= 0:
            errors.append("Comprimento da aleta (L) deve ser positivo")
        elif l > 10:
            errors.append("Comprimento da aleta (L) muito grande (máx. 10 m)")
    elif r1 is not None and r2 is not None:
        if r2 <= r1:
            errors.append("Raio externo (r2) deve ser maior que o raio interno (r1)")
    else:
        errors.append("Comprimento da aleta (L) deve ser fornecido")
    
    # Validações específicas por geometria
    if t is not None:
        if t <= 0:
            errors.append("Espessura (t) deve ser positiva")
        elif t > 1:
            errors.append("Espessura (t) muito grande (máx. 1 m)")
    
    if w is not None:
        if w <= 0:
            errors.append("Largura (w) deve ser positiva")
        elif w > 10:
            errors.append("Largura (w) muito grande (máx. 10 m)")
    
    if D is not None:
        if D <= 0:
            errors.append("Diâmetro (D) deve ser positivo")
        elif D > 5:
            errors.append("Diâmetro (D) muito grande (máx. 5 m)")
    
    if r1 is not None:
        if r1 <= 0:
            errors.append("Raio interno (r1) deve ser positivo")
        elif r1 > 5:
            errors.append("Raio interno (r1) muito grande (máx. 5 m)")
    
    if r2 is not None:
        if r2 <= 0:
            errors.append("Raio externo (r2) deve ser positivo")
        elif r2 > 5:
            errors.append("Raio externo (r2) muito grande (máx. 5 m)")
        if r1 is not None and r2 <= r1:
            errors.append("Raio externo (r2) deve ser maior que o raio interno (r1)")
    
    if T_L is not None:
        if T_L < -273.15:
            errors.append("Temperatura na ponta (T_L) não pode ser menor que -273.15°C")
    
    return len(errors) == 0, errors


# Base centralizada de materiais indexada por ID (unificada com MATERIAIS_DB)
smateriais = DICIONARIO_MATERIAIS_ID




# =============================================================================
# ROTAS PRINCIPAIS DA APLICAÇÃO
# =============================================================================

@app.route('/')
def index():
    """
    🏠 PÁGINA INICIAL DO LABORATÓRIO
    Apresenta todos os módulos disponíveis
    """
    return render_template('index.html')

@app.route('/test_js')
def test_js():
    """Rota de teste - redireciona para index"""
    return redirect(url_for('index'))

@app.route('/sele_aleta', methods=['GET', 'POST'])
def sele_aleta():
    if request.method == 'POST':
        sele_aleta = request.form.get('sele_aleta')
        if not sele_aleta:
            return render_template('sele_aleta.html', error="Por favor, selecione uma aleta.")
        return redirect(url_for('sele_materiais', sele_aleta=sele_aleta))
    return render_template('sele_aleta.html')

@app.route('/sele_materiais', methods=['GET', 'POST'])
def sele_materiais():
    if request.method == 'POST':
        sele_aleta = request.form.get('sele_aleta')  
        smateriais_selecionados = request.form.getlist('smateriais')
        if not smateriais_selecionados:
            return render_template('sele_materiais.html', sele_aleta=sele_aleta, smateriais=smateriais, error="Por favor, selecione pelo menos um material.")
        smateriais_nomes = [smateriais[int(id)]['nome'] for id in smateriais_selecionados]
        smateriais_ks = [str(smateriais[int(id)]['k']) for id in smateriais_selecionados]
        return redirect(url_for('inserir_seledados', sele_aleta=sele_aleta, smateriais=','.join(smateriais_nomes), k=','.join(smateriais_ks)))
    sele_aleta = request.args.get('sele_aleta')

    return render_template('sele_materiais.html', sele_aleta=sele_aleta, smateriais=smateriais)


@app.route('/inserir_seledados/<sele_aleta>/<smateriais>/<k>', methods=['GET', 'POST'])
def inserir_seledados(sele_aleta, smateriais, k):
    smateriais_lista = smateriais.split(',')
    k_lista = k.split(',')
    materiais_selecionados = [{"nome": nome, "k": float(valor_k)} for nome, valor_k in zip(smateriais_lista, k_lista)]
    
    tipo_aleta_id = obter_tipo_aleta(sele_aleta)
    if tipo_aleta_id is None:
        return render_template('inserir_seledados.html', sele_aleta=sele_aleta, smateriais=smateriais_lista, 
                             error="Tipo de aleta inválido ou não encontrado.")
    
    tipo_info = obter_info_tipo(tipo_aleta_id)
    campos_obrigatorios, campos_opcacionais = obter_campos_formulario(tipo_aleta_id)

    if request.method == 'POST':
        h = request.form.get('h')
        T_b = request.form.get('T_b')
        T_inf = request.form.get('T_inf')
        l_form = request.form.get('l')
        t = request.form.get('t')
        w = request.form.get('w')
        r1 = request.form.get('r1')
        r2 = request.form.get('r2')
        D = request.form.get('D')
        condicao_ponta = request.form.get('condicao_ponta', 'adiabatica')
        T_L = request.form.get('T_L')

        # Verificação dos campos térmicos comuns
        if not h or not T_b or not T_inf:
            return render_template('inserir_seledados.html', sele_aleta=sele_aleta, smateriais=smateriais_lista, 
                                 materiais_selecionados=materiais_selecionados, tipo_aleta_id=tipo_aleta_id,
                                 campos_obrigatorios=campos_obrigatorios,
                                 error="Por favor, preencha todos os campos térmicos obrigatórios (h, T_b, T_inf).")

        try:
            h = float(h)
            T_b = float(T_b)
            T_inf = float(T_inf)
            t = float(t) if (t and t.strip()) else None
            w = float(w) if (w and w.strip()) else None
            r1 = float(r1) if (r1 and r1.strip()) else None
            r2 = float(r2) if (r2 and r2.strip()) else None
            D = float(D) if (D and D.strip()) else None
            T_L = float(T_L) if (T_L and T_L.strip()) else None

            # Para tipo 4: L = r2 - r1
            if tipo_aleta_id == 4:
                if r1 is not None and r2 is not None and r2 > r1:
                    l = r2 - r1
                else:
                    l = float(l_form) if (l_form and l_form.strip()) else 0.01
            else:
                if not l_form or not l_form.strip():
                    return render_template('inserir_seledados.html', sele_aleta=sele_aleta, smateriais=smateriais_lista, 
                                         materiais_selecionados=materiais_selecionados, tipo_aleta_id=tipo_aleta_id,
                                         campos_obrigatorios=campos_obrigatorios,
                                         error="Por favor, preencha o comprimento (L).")
                l = float(l_form)
        except ValueError:
            return render_template('inserir_seledados.html', sele_aleta=sele_aleta, smateriais=smateriais_lista, 
                                 materiais_selecionados=materiais_selecionados, tipo_aleta_id=tipo_aleta_id,
                                 campos_obrigatorios=campos_obrigatorios,
                                 error="Por favor, preencha os campos com valores numéricos válidos.")

        # Verificar se T_L é necessário para condição de temperatura especificada
        if condicao_ponta == 'temp_especificada' and not T_L:
            return render_template('inserir_seledados.html', sele_aleta=sele_aleta, smateriais=smateriais_lista, 
                                 materiais_selecionados=materiais_selecionados, tipo_aleta_id=tipo_aleta_id,
                                 campos_obrigatorios=campos_obrigatorios,
                                 error="Por favor, especifique a temperatura na ponta T_L para esta condição de contorno.")

        # Validar parâmetros físicos
        k_material = float(materiais_selecionados[0]['k'])
        is_valid, validation_errors = validar_parametros_fisicos(h, k_material, T_b, T_inf, l, t, w, r1, r2, D, T_L)
        if not is_valid:
            error_msg = "Parâmetros inválidos:\n• " + "\n• ".join(validation_errors)
            return render_template('inserir_seledados.html', sele_aleta=sele_aleta, smateriais=smateriais_lista, 
                                 materiais_selecionados=materiais_selecionados, tipo_aleta_id=tipo_aleta_id,
                                 campos_obrigatorios=campos_obrigatorios, error=error_msg)

        # Validar campos obrigatórios específicos do tipo de aleta
        campos_validos, erros_campos = validar_campos_obrigatorios(tipo_aleta_id, t=t, w=w, r1=r1, r2=r2, D=D, L=l)
        if not campos_validos:
            error_msg = tipo_info['descricao'] + ":\n• " + "\n• ".join(erros_campos)
            return render_template('inserir_seledados.html', sele_aleta=sele_aleta, smateriais=smateriais_lista, 
                                 materiais_selecionados=materiais_selecionados, tipo_aleta_id=tipo_aleta_id,
                                 campos_obrigatorios=campos_obrigatorios, error=error_msg)

        # Processar os dados e redirecionar para a página de resultados
        return redirect(url_for('resultados_sele', sele_aleta=sele_aleta, smateriais=','.join([m['nome'] for m in materiais_selecionados]), 
                              h=h, k=','.join(k_lista), l=l, t=t, w=w, r1=r1, r2=r2, D=D, T_b=T_b, T_inf=T_inf, 
                              condicao_ponta=condicao_ponta, T_L=T_L))
    
    return render_template('inserir_seledados.html', sele_aleta=sele_aleta, smateriais=smateriais_lista, 
                         materiais_selecionados=materiais_selecionados, tipo_aleta_id=tipo_aleta_id, 
                         campos_obrigatorios=campos_obrigatorios)

@app.route('/resultados_sele')
def resultados_sele():
    sele_aleta_param = request.args.get('sele_aleta')
    smateriais_param = request.args.get('smateriais')
    h_param = request.args.get('h')
    k_param = request.args.get('k')
    T_b_param = request.args.get('T_b')
    T_inf_param = request.args.get('T_inf')

    if not all([sele_aleta_param, smateriais_param, h_param, k_param, T_b_param, T_inf_param]):
        return "Parâmetros insuficientes fornecidos", 400

    sele_aleta = [normalizar_tipo_aleta(t) for t in sele_aleta_param.split(',') if t.strip()] if sele_aleta_param else []
    smateriais = smateriais_param.split(',') if smateriais_param else []
    h = float(h_param)
    k = [float(valor_k) for valor_k in k_param.split(',')] if k_param else []
    
    t = request.args.get('t', type=float)
    w = request.args.get('w', type=float)
    r1 = request.args.get('r1', type=float)
    r2 = request.args.get('r2', type=float)
    D = request.args.get('D', type=float)
    
    l_param = request.args.get('l', type=float)
    if (l_param is None or l_param <= 0) and r1 is not None and r2 is not None and r2 > r1:
        l = r2 - r1
    else:
        l = l_param if l_param and l_param > 0 else 0.05
        
    T_b = float(T_b_param)
    T_inf = float(T_inf_param)
    condicao_ponta = request.args.get('condicao_ponta', 'adiabatica')
    T_L = request.args.get('T_L', type=float)

    resultados_sele = []
    metricas_sele_lista = []
    interpretacoes_sele_lista = []
    dados_didaticos_sele_lista = []
    
    for tipo_aleta in sele_aleta:
        tid = obter_tipo_aleta(tipo_aleta)
        for material, valor_k in zip(smateriais, k):
            resultado_calc = calcular_eficiencia(tipo_aleta, h, valor_k, l, t=t, w=w, D=D, r1=r1, r2=r2, T_b=T_b, T_inf=T_inf, condicao_ponta=condicao_ponta, T_L=T_L)
            
            if len(resultado_calc) == 8:
                eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr, dados_didaticos = resultado_calc
            else:
                eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr = resultado_calc
                dados_didaticos = None
            
            metricas = calcular_metricas_engenharia(
                tipo_aleta, h, valor_k, l, t, w, D, r1, r2, T_b, T_inf,
                Q_aleta, A_aleta, eta_aleta, epsilon_a, material
            )
            
            interpretacoes = interpretar_metricas(metricas)
            
            resultados_sele.append((tipo_aleta, material, valor_k, eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr))
            metricas_sele_lista.append(metricas)
            interpretacoes_sele_lista.append(interpretacoes)
            dados_didaticos_sele_lista.append(dados_didaticos)

    # Gráfico interativo Plotly e dados JSON compartilhados da MESMA fonte da verdade
    grafico_html, dados_base = gerar_grafico_temperatura_multiplos_materiais(
        sele_aleta, smateriais, h, k, l, t=t, w=w, D=D, r1=r1, r2=r2, T_b=T_b, T_inf=T_inf, condicao_ponta=condicao_ponta
    )
    dados_grafico_json = json.dumps(dados_base)

    os.makedirs(app.static_folder, exist_ok=True)
    filepath = os.path.join(app.static_folder, 'selerelatorio.txt')
    try:
        salvar_sresultados(filepath, sele_aleta, h, k[0] if k else 222.0, l, t, w, D, r1, r2, T_b, T_inf, resultados_sele)
    except Exception as e_salv:
        print(f"[AVISO] Falha ao gravar selerelatorio.txt: {e_salv}")

    return render_template('resultados_sele.html', 
                         resultados=resultados_sele, 
                         materiais=smateriais, 
                         relatorio_path='selerelatorio.txt', 
                         grafico_html=grafico_html, 
                         dados_grafico_json=dados_grafico_json,
                         condicao_ponta=condicao_ponta, 
                         T_L=T_L,
                         metricas_lista=metricas_sele_lista,
                         interpretacoes_lista=interpretacoes_sele_lista,
                         dados_didaticos_lista=dados_didaticos_sele_lista)


































# Base centralizada de materiais (unificada)
materiais = DICIONARIO_MATERIAIS_ID


@app.route('/tipos_aletas', methods=['GET', 'POST'])
def tipos_aletas():
    if request.method == 'POST':
        tipos_aletas = request.form.getlist('tipo_aleta')
        return redirect(url_for('tipos_materiais', tipos_aletas=','.join(tipos_aletas)))
    return render_template('tipos_aletas.html')

@app.route('/tipos_materiais/<tipos_aletas>', methods=['GET', 'POST'])
def tipos_materiais(tipos_aletas):
    tipos_aletas = tipos_aletas.split(',')
    if request.method == 'POST':
        material_id = int(request.form['material'])
        material = materiais[material_id]
        return redirect(url_for('inserir_dados', tipos_aletas=','.join(tipos_aletas), material=material['nome'], k=material['k']))
    return render_template('tipos_materiais.html', tipos_aletas=tipos_aletas, materiais=materiais)

@app.route('/inserir_dados/<tipos_aletas>/<material>/<k>', methods=['GET', 'POST'])
def inserir_dados(tipos_aletas, material, k):
    tipos_aletas_lista = tipos_aletas.split(',')
    flags_campos = determinar_campos_para_multiplas_aletas(tipos_aletas_lista)
    
    if request.method == 'POST':
        h = request.form.get('h')
        T_b = request.form.get('T_b')
        T_inf = request.form.get('T_inf')
        l_form = request.form.get('l')
        t = request.form.get('t')
        w = request.form.get('w')
        r1 = request.form.get('r1')
        r2 = request.form.get('r2')
        D = request.form.get('D')
        condicao_ponta = request.form.get('condicao_ponta', 'adiabatica')
        T_L = request.form.get('T_L')

        # Verificação dos campos térmicos comuns
        if not h or not T_b or not T_inf:
            return render_template('inserir_dados.html', tipos_aletas=tipos_aletas_lista, material=material, k=k, 
                                 error="Por favor, preencha todos os campos térmicos obrigatórios (h, T_b, T_inf).", **flags_campos)

        try:
            h = float(h)
            T_b = float(T_b)
            T_inf = float(T_inf)
            t = float(t) if (t and t.strip()) else None
            w = float(w) if (w and w.strip()) else None
            r1 = float(r1) if (r1 and r1.strip()) else None
            r2 = float(r2) if (r2 and r2.strip()) else None
            D = float(D) if (D and D.strip()) else None
            T_L = float(T_L) if (T_L and T_L.strip()) else None

            # Determinar L
            if flags_campos.get('precisa_L', True):
                if not l_form or not l_form.strip():
                    return render_template('inserir_dados.html', tipos_aletas=tipos_aletas_lista, material=material, k=k, 
                                         error="Por favor, preencha o comprimento (L).", **flags_campos)
                l = float(l_form)
            else:
                # Caso de apenas aletas anulares
                if r1 is not None and r2 is not None and r2 > r1:
                    l = r2 - r1
                else:
                    l = float(l_form) if (l_form and l_form.strip()) else 0.01
        except ValueError:
            return render_template('inserir_dados.html', tipos_aletas=tipos_aletas_lista, material=material, k=k, 
                                 error="Por favor, preencha todos os campos com valores numéricos válidos.", **flags_campos)

        # Verificar se T_L é necessário para condição de temperatura especificada
        if condicao_ponta == 'temp_especificada' and not T_L:
            return render_template('inserir_dados.html', tipos_aletas=tipos_aletas_lista, material=material, k=k, 
                                 error="Por favor, especifique a temperatura na ponta T_L para esta condição de contorno.", **flags_campos)

        # Validar parâmetros físicos
        k_value = float(k)
        is_valid, validation_errors = validar_parametros_fisicos(h, k_value, T_b, T_inf, l, t, w, r1, r2, D, T_L)
        if not is_valid:
            error_msg = "Parâmetros inválidos:\n• " + "\n• ".join(validation_errors)
            return render_template('inserir_dados.html', tipos_aletas=tipos_aletas_lista, material=material, k=k, error=error_msg, **flags_campos)

        # Validar cada geometria estritamente pelo seu tipo_id (sem checagem por texto!)
        for ta in tipos_aletas_lista:
            tid = obter_tipo_aleta(ta)
            if tid:
                valido, erros = validar_campos_obrigatorios(tid, t=t, w=w, r1=r1, r2=r2, D=D, L=l)
                if not valido:
                    desc = TIPOS_ALETAS[tid]['descricao']
                    return render_template('inserir_dados.html', tipos_aletas=tipos_aletas_lista, material=material, k=k, 
                                         error=f"{desc}: " + "; ".join(erros), **flags_campos)

        return redirect(url_for('resultado', tipos_aletas=','.join(tipos_aletas_lista), material=material, h=h, k=k, l=l, t=t, w=w, r1=r1, r2=r2, D=D, T_b=T_b, T_inf=T_inf, condicao_ponta=condicao_ponta, T_L=T_L))
    
    return render_template('inserir_dados.html', tipos_aletas=tipos_aletas_lista, material=material, k=k, **flags_campos)

@app.route('/resultado')
def resultado():
    tipos_aletas_str = request.args.get('tipos_aletas')
    tipos_aletas = [normalizar_tipo_aleta(t) for t in tipos_aletas_str.split(',') if t.strip()] if tipos_aletas_str else []
    material = request.args.get('material')
    h_str = request.args.get('h')
    h = float(h_str) if h_str else 0.0
    k_str = request.args.get('k')
    k = float(k_str) if k_str else 0.0
    
    t = request.args.get('t', type=float)
    w = request.args.get('w', type=float)
    r1 = request.args.get('r1', type=float)
    r2 = request.args.get('r2', type=float)
    D = request.args.get('D', type=float)
    
    l_str = request.args.get('l')
    l = float(l_str) if l_str else 0.0
    if l <= 0 and r1 is not None and r2 is not None and r2 > r1:
        l = r2 - r1
    if l <= 0:
        l = 0.05
        
    T_b_str = request.args.get('T_b')
    T_b = float(T_b_str) if T_b_str else 0.0
    T_inf_str = request.args.get('T_inf')
    T_inf = float(T_inf_str) if T_inf_str else 0.0
    condicao_ponta = request.args.get('condicao_ponta', 'adiabatica')
    T_L = request.args.get('T_L', type=float)

    resultados = []
    metricas_lista = []
    interpretacoes_lista = []
    dados_didaticos_lista = []
    
    for tipo_aleta in tipos_aletas:
        resultado_calc = calcular_eficiencia(tipo_aleta, h, k, l, t=t, w=w, D=D, r1=r1, r2=r2, T_b=T_b, T_inf=T_inf, condicao_ponta=condicao_ponta, T_L=T_L)
        
        if len(resultado_calc) == 8:
            eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr, dados_didaticos = resultado_calc
            dados_didaticos_lista.append(dados_didaticos)
        else:
            eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr = resultado_calc
            dados_didaticos_lista.append(None)
        
        material_nome = material if material else "Desconhecido"
        metricas = calcular_metricas_engenharia(
            tipo_aleta, h, k, l, t, w, D, r1, r2, T_b, T_inf,
            Q_aleta, A_aleta, eta_aleta, epsilon_a, material_nome
        )
        
        interpretacoes = interpretar_metricas(metricas)
        resultados.append((tipo_aleta, eta_aleta, Q_aleta, A_aleta, epsilon_a, m, P, A_tr))
        metricas_lista.append(metricas)
        interpretacoes_lista.append(interpretacoes)

    # Gerar gráfico interativo com Plotly e dados JSON compartilhados da MESMA fonte da verdade
    grafico_html, dados_base = gerar_grafico_temperatura_interativo(
        tipos_aletas, h, k, l, t=t, w=w, D=D, r1=r1, r2=r2, T_b=T_b, T_inf=T_inf, condicao_ponta=condicao_ponta, material=material
    )
    dados_grafico_json = json.dumps(dados_base)

    # Salvar os resultados em um arquivo de forma segura
    os.makedirs(app.static_folder, exist_ok=True)
    filepath = os.path.join(app.static_folder, 'relatorio.txt')
    try:
        salvar_resultados(filepath, tipos_aletas, h, k, l, t, w, D, r1, r2, T_b, T_inf, resultados)
    except Exception as e_salv:
        print(f"[AVISO] Falha ao gravar relatorio.txt: {e_salv}")

    return render_template('resultado.html', 
                         resultados=resultados, 
                         material=material, 
                         relatorio_path='relatorio.txt', 
                         grafico_html=grafico_html, 
                         dados_grafico_json=dados_grafico_json,
                         condicao_ponta=condicao_ponta, 
                         T_L=T_L,
                         metricas_lista=metricas_lista,
                         interpretacoes_lista=interpretacoes_lista,
                         dados_didaticos_lista=dados_didaticos_lista)

# ================================
# CALCULADORA DE COEFICIENTE CONVECTIVO
# ================================

@app.route('/calculadora_convectivo')
def calculadora_convectivo():
    """Página inicial da calculadora de coeficiente convectivo"""
    return render_template('calculadora_convectivo.html')

@app.route('/calculadora_convectivo', methods=['POST'])
def calculadora_convectivo_post():
    """Processar seleção do tipo de convecção"""
    tipo_conveccao = request.form.get('tipo_conveccao')
    
    if not tipo_conveccao:
        return redirect(url_for('calculadora_convectivo'))
    
    if tipo_conveccao == 'condensacao':
        return redirect(url_for('calculadora_condensacao'))
    elif tipo_conveccao == 'ebulicao':
        return redirect(url_for('calculadora_ebulicao'))
    elif tipo_conveccao == 'arranjos_tubos':
        return redirect(url_for('calculadora_arranjos_tubos'))
    elif tipo_conveccao == 'escoamento_interno':
        return redirect(url_for('calculadora_escoamento_interno'))
    else:
        return redirect(url_for('calculadora_convectivo_tipo', tipo=tipo_conveccao))

@app.route('/calculadora_convectivo/<tipo>')
def calculadora_convectivo_tipo(tipo):
    """Página de cálculo específica para cada tipo de convecção"""
    tipos_validos = ['natural', 'forcada']
    
    if tipo not in tipos_validos:
        return redirect(url_for('calculadora_convectivo'))
    
    return render_template(f'calculadora_{tipo}.html', tipo=tipo)

@app.route('/calculadora_convectivo/<tipo>/calcular', methods=['POST'])
def calculadora_convectivo_calcular(tipo):
    """Processa cálculos de convecção e retorna JSON"""
    try:
        # Verificar se é requisição JSON
        is_json_request = request.is_json or request.headers.get('Content-Type') == 'application/json'
        
        if tipo == 'natural':
            resultado = processar_conveccao_natural_json() if is_json_request else processar_conveccao_natural()
            return resultado if is_json_request else resultado
        elif tipo == 'forcada':
            resultado = processar_conveccao_forcada_json() if is_json_request else processar_conveccao_forcada()
            return resultado if is_json_request else resultado
        else:
            if is_json_request:
                return jsonify({'erro': f'Tipo de convecção não implementado: {tipo}'}), 400
            else:
                flash('Tipo de convecção não implementado ainda.', 'warning')
                return redirect(url_for('calculadora_convectivo_tipo', tipo=tipo))
    except Exception as e:
        # Verificar novamente se é requisição JSON para tratamento de erro
        is_json_request = request.is_json or request.headers.get('Content-Type') == 'application/json'
        if is_json_request:
            return jsonify({'erro': str(e)}), 500
        else:
            flash(f'Erro no cálculo: {str(e)}', 'danger')
            return redirect(url_for('calculadora_convectivo_tipo', tipo=tipo))

def processar_conveccao_natural():
    """Processa cálculos de convecção natural"""
    from conveccao_calculadora import calcular_coeficiente_convectivo
    
    # Obter dados do formulário
    geometria = request.form.get('geometria')
    fluido = request.form.get('fluido')
    
    # Validar campos obrigatórios
    if not geometria:
        flash('Por favor, selecione uma geometria.', 'danger')
        return redirect(url_for('calculadora_convectivo_tipo', tipo='natural'))
    
    if not fluido:
        flash('Por favor, selecione um fluido.', 'danger')
        return redirect(url_for('calculadora_convectivo_tipo', tipo='natural'))
    
    try:
        T_fluido = float(request.form.get('T_fluido') or 0)
        T_superficie = float(request.form.get('T_superficie') or 0)
    except (ValueError, TypeError):
        flash('Por favor, preencha todos os campos numéricos corretamente.', 'danger')
        return redirect(url_for('calculadora_convectivo_tipo', tipo='natural'))
    
    # Parâmetros específicos por geometria
    parametros = {
        'T_s': T_superficie,
        'T_inf': T_fluido,
        'fluido': fluido
    }
    
    # Mapeamento de geometrias e parâmetros adicionais
    try:
        if geometria == 'placa_vertical':
            altura = request.form.get('altura')
            if not altura:
                flash('Por favor, preencha a altura da placa.', 'danger')
                return redirect(url_for('calculadora_convectivo_tipo', tipo='natural'))
            parametros['L'] = float(altura)
            geometria_calc = 'placa_vertical'
        elif geometria == 'cilindro_horizontal':
            diametro = request.form.get('diametro_cilindro')
            if not diametro:
                flash('Por favor, preencha o diâmetro do cilindro.', 'danger')
                return redirect(url_for('calculadora_convectivo_tipo', tipo='natural'))
            parametros['D'] = float(diametro)
            geometria_calc = 'cilindro_horizontal'
        elif geometria == 'esfera':
            diametro = request.form.get('diametro_esfera')
            if not diametro:
                flash('Por favor, preencha o diâmetro da esfera.', 'danger')
                return redirect(url_for('calculadora_convectivo_tipo', tipo='natural'))
            parametros['D'] = float(diametro)
            geometria_calc = 'esfera'
        elif geometria == 'placa_horizontal':
            L_placa = request.form.get('comprimento_placa_h')
            W_placa = request.form.get('largura_placa_h')
            orientacao = request.form.get('orientacao_horizontal', 'superior')
            if not L_placa or not W_placa:
                flash('Por favor, preencha as dimensões da placa (L e W).', 'danger')
                return redirect(url_for('calculadora_convectivo_tipo', tipo='natural'))
            L_v = float(L_placa)
            W_v = float(W_placa)
            lc = (L_v * W_v) / (2 * (L_v + W_v))
            parametros['Lc'] = lc
            parametros['orientacao'] = orientacao
            parametros['L_placa'] = L_v
            parametros['W_placa'] = W_v
            geometria_calc = 'placa_horizontal'
        else:
            flash('Geometria não reconhecida.', 'danger')
            return redirect(url_for('calculadora_convectivo_tipo', tipo='natural'))
    except (ValueError, TypeError):
        flash('Por favor, verifique se todos os valores dimensionais são números válidos.', 'danger')
        return redirect(url_for('calculadora_convectivo_tipo', tipo='natural'))
    
    # Calcular coeficiente
    resultado = calcular_coeficiente_convectivo('natural', geometria_calc, parametros)
    
    if 'erro' in resultado:
        flash(f'Erro no cálculo: {"; ".join(resultado["erro"])}', 'danger')
        return redirect(url_for('calculadora_convectivo_tipo', tipo='natural'))
    
    return render_template('calculadora_natural.html', 
                         tipo='natural', 
                         resultado=resultado)

def processar_conveccao_natural_json():
    """Processa cálculos de convecção natural e retorna JSON"""
    from conveccao_calculadora import calcular_coeficiente_convectivo
    
    try:
        # Obter dados do JSON
        data = request.get_json()
        if not data:
            return jsonify({'erro': 'Dados JSON não fornecidos'}), 400
        
        geometria = data.get('geometria')
        fluido = data.get('fluido', 'ar')
        T_fluido = float(data.get('temperatura_fluido', 20))
        T_superficie = float(data.get('temperatura_superficie', 80))
        
        # Parâmetros específicos por geometria
        parametros = {
            'T_s': T_superficie,
            'T_inf': T_fluido,
            'fluido': fluido
        }
        
        if geometria == 'placa_vertical':
            altura = float(data.get('altura', 0.5))
            parametros['L'] = altura
            geometria_calc = 'placa_vertical'
        elif geometria == 'cilindro_horizontal':
            diametro = float(data.get('diametro', 0.1))
            parametros['D'] = diametro
            geometria_calc = 'cilindro_horizontal'
        elif geometria == 'esfera':
            diametro = float(data.get('diametro', 0.1))
            parametros['D'] = diametro
            geometria_calc = 'esfera'
        elif geometria == 'placa_horizontal':
            L_placa = float(data.get('comprimento_placa', 0))
            W_placa = float(data.get('largura_placa', 0))
            orientacao = data.get('orientacao', 'inferior')
            if L_placa <= 0 or W_placa <= 0:
                return jsonify({'erro': 'Preencha as dimensões da placa (L e W).'}), 400
            lc = (L_placa * W_placa) / (2 * (L_placa + W_placa))
            parametros['Lc'] = lc
            parametros['orientacao'] = orientacao
            parametros['L_placa'] = L_placa
            parametros['W_placa'] = W_placa
            geometria_calc = 'placa_horizontal'
        else:
            return jsonify({'erro': f'Geometria não reconhecida: {geometria}'}), 400
        
        # Calcular coeficiente
        resultado = calcular_coeficiente_convectivo('natural', geometria_calc, parametros)
        
        if isinstance(resultado, dict) and 'erro' in resultado:
            return jsonify(resultado), 400
        
        # Formatar resultado para JSON com dados completos para memória de cálculo
        T_filme_C = resultado.get('T_filme_C', (T_superficie + T_fluido) / 2.0)
        T_filme_K = resultado.get('T_filme_K', T_filme_C + 273.15)
        h_anal = resultado.get('h', 0.0)
        
        # Balanço de energia experimental (se solicitado)
        balanco_exp = None
        T_base_raw = data.get('T_base')
        if T_base_raw is not None:
            try:
                T_agua = float(T_base_raw)
                X_correcao = float(data.get('X_correcao', 0.0))
                T_face_inferior = T_agua - X_correcao
                espessura = float(data.get('espessura', 0.005))
                k_mat = float(data.get('k_material', 222.0))
                emissividade = float(data.get('emissividade', 0.09))
                
                # Área superficial da chapa
                if geometria == 'placa_horizontal':
                    area_s = float(data.get('comprimento_placa', 0.37)) * float(data.get('largura_placa', 0.17))
                else:
                    area_s = float(data.get('area_superficial', 0.0629))
                
                if area_s <= 0:
                    area_s = 0.0629
                
                # 1. Taxa convectiva analítica de referência
                delta_T = T_superficie - T_fluido
                Q_conv_anal = h_anal * area_s * delta_T if delta_T > 0 else 0.0
                
                # 2. Taxa de radiação: Q_rad = eps * sigma * A * (Ts_K^4 - Tinf_K^4)
                sigma = 5.670374419e-8
                Ts_K = max(0.0, T_superficie + 273.15)
                Tinf_K = max(0.0, T_fluido + 273.15)
                Q_rad = emissividade * sigma * area_s * (Ts_K**4 - Tinf_K**4) if Ts_K > Tinf_K else 0.0
                
                # 3. Condução Real pela Lei de Fourier através da chapa (utilizando T_face_inferior corrigida):
                # Q_cond = k_Al * A_s * |T_face_inferior - T_superficie| / espessura
                delta_T_cond = abs(T_face_inferior - T_superficie)
                Q_cond_exp = (k_mat * area_s * delta_T_cond) / espessura if espessura > 0 else 0.0
                
                # 4. Convecção Experimental obtida pelo Balanço de Energia Real:
                # Q_conv_exp = Q_cond - Q_rad
                Q_conv_exp = max(0.0, Q_cond_exp - Q_rad)
                
                # 5. Coeficiente Convectivo Experimental real:
                # h_exp = Q_conv_exp / (A_s * (T_s - T_inf))
                h_exp = (Q_conv_exp / (area_s * delta_T)) if (abs(delta_T) > 1e-4 and area_s > 0) else 0.0
                
                # 6. Divergência Relativa percentual experimental vs teórico
                erro_rel = (abs(h_anal - h_exp) / h_anal * 100.0) if h_anal > 0 else 0.0
                
                # 7. Delta T teórico que existiria se a condução fosse estritamente igual à dissipação teórica (McAdams + Radiação)
                delta_T_conducao_teorico = ((Q_conv_anal + Q_rad) * espessura) / (k_mat * area_s) if (k_mat * area_s > 0) else 0.00254
                
                balanco_exp = {
                    'T_base': round(T_agua, 4),
                    'T_agua': round(T_agua, 4),
                    'X_correcao': round(X_correcao, 4),
                    'T_face_inferior': round(T_face_inferior, 4),
                    'delta_T_cond': round(delta_T_cond, 4),
                    'espessura': espessura,
                    'k_material': k_mat,
                    'emissividade': emissividade,
                    'area_s': round(area_s, 4),
                    'Q_cond': round(Q_cond_exp, 2),
                    'Q_rad': round(Q_rad, 2),
                    'Q_conv': round(Q_conv_exp, 2),
                    'Q_conv_anal': round(Q_conv_anal, 2),
                    'h_exp': round(h_exp, 2),
                    'h_experimental': round(h_exp, 2),
                    'erro_relativo': round(erro_rel, 2),
                    'delta_T_conducao_teorico': round(delta_T_conducao_teorico, 5)
                }
            except Exception as e_bal:
                balanco_exp = {'erro': str(e_bal)}

        resposta = {
            'sucesso': True,
            'tipo': 'natural',
            'geometria': geometria,
            'rayleigh': resultado.get('Ra', 'N/A'),
            'nusselt': resultado.get('Nu', 'N/A'),
            'coef_convectivo': h_anal,
            'prandtl': resultado.get('Pr', 'N/A'),
            'regime': resultado.get('regime', 'N/A'),
            'lc': resultado.get('Lc', parametros.get('Lc', parametros.get('L', parametros.get('D', 'N/A')))),
            'orientacao': resultado.get('orientacao', 'N/A'),
            'T_filme_C': round(T_filme_C, 2),
            'T_filme_K': round(T_filme_K, 2),
            'beta': resultado.get('beta', 1.0 / T_filme_K),
            'propriedades': resultado.get('propriedades', {}),
            'observacoes': resultado.get('observacoes', []),
            'balanco_exp': balanco_exp
        }
        
        return jsonify(resposta)
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

def processar_conveccao_forcada():
    """Processa cálculos de convecção forçada"""
    from conveccao_calculadora import calcular_coeficiente_convectivo
    
    # Obter dados do formulário
    geometria = request.form.get('geometria')
    fluido = request.form.get('fluido')
    
    # Validar campos obrigatórios
    if not geometria:
        flash('Por favor, selecione uma geometria.', 'danger')
        return redirect(url_for('calculadora_convectivo_tipo', tipo='forcada'))
    
    if not fluido:
        flash('Por favor, selecione um fluido.', 'danger')
        return redirect(url_for('calculadora_convectivo_tipo', tipo='forcada'))
    
    try:
        T_fluido_raw = request.form.get('T_fluido')
        T_superficie_raw = request.form.get('T_superficie')
        velocidade_raw = request.form.get('velocidade')
        

        
        T_fluido = float(T_fluido_raw or 0)
        T_superficie = float(T_superficie_raw or 0)
        velocidade = float(velocidade_raw or 0)
        

        
    except (ValueError, TypeError) as e:

        flash('Por favor, preencha todos os campos numéricos corretamente.', 'danger')
        return redirect(url_for('calculadora_convectivo_tipo', tipo='forcada'))
    
    # Parâmetros específicos por geometria
    parametros = {
        'T_s': T_superficie,
        'T_inf': T_fluido,
        'fluido': fluido,
        'v': velocidade
    }
    
    # Mapeamento de geometrias e parâmetros adicionais
    try:
        if geometria == 'tubo':
            diametro = request.form.get('diametro_tubo')
            comprimento = request.form.get('comprimento_tubo')

            if not diametro or not comprimento:
                flash('Por favor, preencha o diâmetro e comprimento do tubo.', 'danger')
                return redirect(url_for('calculadora_convectivo_tipo', tipo='forcada'))
            parametros['D'] = float(diametro)
            parametros['L'] = float(comprimento)
            geometria_calc = 'tubo_interno'
        elif geometria == 'cilindro':
            diametro = request.form.get('diametro_cilindro')
            if not diametro:
                flash('Por favor, preencha o diâmetro do cilindro.', 'danger')
                return redirect(url_for('calculadora_convectivo_tipo', tipo='forcada'))
            parametros['D'] = float(diametro)
            geometria_calc = 'cilindro_cruzado'
        elif geometria == 'placa':
            comprimento = request.form.get('comprimento_placa')
            if not comprimento:
                flash('Por favor, preencha o comprimento da placa.', 'danger')
                return redirect(url_for('calculadora_convectivo_tipo', tipo='forcada'))
            parametros['L'] = float(comprimento)
            geometria_calc = 'placa_plana'

        else:
            flash('Geometria não reconhecida.', 'danger')
            return redirect(url_for('calculadora_convectivo_tipo', tipo='forcada'))
    except (ValueError, TypeError):
        flash('Por favor, verifique se todos os valores dimensionais são números válidos.', 'danger')
        return redirect(url_for('calculadora_convectivo_tipo', tipo='forcada'))
    
    # Calcular coeficiente
    resultado = calcular_coeficiente_convectivo('forcada', geometria_calc, parametros)
    
    if 'erro' in resultado:
        # Melhorar mensagens de erro para o usuário
        erros_formatados = []
        for erro in resultado["erro"]:
            if "muito alta" in erro:
                erros_formatados.append(f"⚠️ {erro}")
            elif "muito baixa" in erro:
                erros_formatados.append(f"⚠️ {erro}")
            elif "muito grande" in erro:
                erros_formatados.append(f"⚠️ {erro}")
            elif "muito pequena" in erro:
                erros_formatados.append(f"⚠️ {erro}")
            else:
                erros_formatados.append(f"❌ {erro}")
        
        flash(f'Valores inválidos encontrados:', 'warning')
        for erro in erros_formatados:
            flash(erro, 'danger')
        return redirect(url_for('calculadora_convectivo_tipo', tipo='forcada'))
    
    return render_template('calculadora_forcada.html', 
                         tipo='forcada', 
                         resultado=resultado)

def processar_conveccao_forcada_json():
    """Processa cálculos de convecção forçada e retorna JSON"""
    from conveccao_calculadora import calcular_coeficiente_convectivo
    
    try:
        # Obter dados do JSON
        data = request.get_json()
        if not data:
            return jsonify({'erro': 'Dados JSON não fornecidos'}), 400
        
        geometria = data.get('geometria')
        fluido = data.get('fluido', 'ar')
        T_fluido = float(data.get('temperatura_fluido', 20))
        T_superficie = float(data.get('temperatura_superficie', 80))
        velocidade = float(data.get('velocidade', 5.0))
        
        # Parâmetros específicos por geometria
        parametros = {
            'T_s': T_superficie,
            'T_inf': T_fluido,
            'fluido': fluido,
            'v': velocidade
        }
        
        if geometria == 'placa' or geometria == 'placa_plana':
            comprimento = float(data.get('comprimento', 1.0))
            parametros['L'] = comprimento
            geometria_calc = 'placa_plana'
        elif geometria == 'cilindro' or geometria == 'cilindro_cruzado':
            diametro = float(data.get('diametro', 0.1))
            parametros['D'] = diametro
            geometria_calc = 'cilindro_cruzado'
        elif geometria == 'tubo' or geometria == 'tubo_interno':
            diametro = float(data.get('diametro', 0.05))
            comprimento = float(data.get('comprimento', 1.0))
            parametros['D'] = diametro
            parametros['L'] = comprimento
            geometria_calc = 'tubo_interno'
        else:
            return jsonify({'erro': f'Geometria não reconhecida: {geometria}'}), 400
        
        # Calcular coeficiente
        resultado = calcular_coeficiente_convectivo('forcada', geometria_calc, parametros)
        
        if isinstance(resultado, dict) and 'erro' in resultado:
            return jsonify(resultado), 400
        
        # Formatar resultado para JSON
        resposta = {
            'sucesso': True,
            'tipo': 'forcada',
            'geometria': geometria,
            'reynolds': resultado.get('Re', 'N/A'),
            'nusselt': resultado.get('Nu', 'N/A'),
            'coef_convectivo': resultado.get('h', 'N/A'),
            'prandtl': resultado.get('Pr', 'N/A'),
            'regime': resultado.get('regime', 'N/A'),
            'propriedades': resultado.get('propriedades', {}),
            'observacoes': resultado.get('observacoes', [])
        }
        
        return jsonify(resposta)
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# ================================
# ROTAS PARA CONDENSAÇÃO E EBULIÇÃO
# ================================

@app.route('/calculadora_condensacao')
def calculadora_condensacao():
    """Página da calculadora de condensação"""
    return render_template('calculadora_condensacao.html')

@app.route('/calculadora_condensacao/calcular', methods=['POST'])
def calculadora_condensacao_calcular():
    """Processa cálculos de condensação"""
    try:
        # Obter dados do formulário
        geometria = request.form.get('geometria')
        fluido = request.form.get('fluido')
        T_sat_str = request.form.get('T_sat')
        T_sat = float(T_sat_str) if T_sat_str else 100.0
        T_parede_str = request.form.get('T_parede')
        T_parede = float(T_parede_str) if T_parede_str else 120.0
        
        if not geometria or not fluido:
            flash('Por favor, selecione geometria e fluido.', 'danger')
            return redirect(url_for('calculadora_condensacao'))
        
        # Parâmetros específicos por geometria
        parametros = {
            'T_sat': T_sat,
            'T_parede': T_parede,
            'fluido': fluido
        }
        
        if geometria == 'placa_vertical':
            altura = request.form.get('altura')
            if not altura:
                flash('Por favor, preencha a altura da placa.', 'danger')
                return redirect(url_for('calculadora_condensacao'))
            parametros['L'] = float(altura)
        elif geometria == 'tubo_horizontal':
            diametro = request.form.get('diametro')
            if not diametro:
                flash('Por favor, preencha o diâmetro do tubo.', 'danger')
                return redirect(url_for('calculadora_condensacao'))
            parametros['D'] = float(diametro)

        
        # Calcular
        resultado = calcular_mudanca_fase('condensacao', geometria, parametros)
        
        if 'erro' in resultado:
            for erro in resultado['erro']:
                flash(erro, 'danger')
            return redirect(url_for('calculadora_condensacao'))
        
        return render_template('calculadora_condensacao.html', resultado=resultado)
        
    except Exception as e:
        flash(f'Erro no cálculo: {str(e)}', 'danger')
        return redirect(url_for('calculadora_condensacao'))

@app.route('/calculadora_ebulicao')
def calculadora_ebulicao():
    """Página da calculadora de ebulição"""
    return render_template('calculadora_ebulicao.html')

@app.route('/calculadora_ebulicao/calcular', methods=['POST'])
def calculadora_ebulicao_calcular():
    """Processa cálculos de ebulição"""
    try:
        # Obter dados do formulário
        tipo_ebulicao = request.form.get('tipo_ebulicao')
        fluido = request.form.get('fluido')
        T_sat_str = request.form.get('T_sat')
        T_sat = float(T_sat_str) if T_sat_str else 100.0
        T_parede_str = request.form.get('T_parede')
        T_parede = float(T_parede_str) if T_parede_str else 120.0
        
        if not tipo_ebulicao or not fluido:
            flash('Por favor, selecione tipo de ebulição e fluido.', 'danger')
            return redirect(url_for('calculadora_ebulicao'))
        
        # Parâmetros específicos por tipo
        parametros = {
            'T_sat': T_sat,
            'T_parede': T_parede,
            'fluido': fluido
        }
        
        if tipo_ebulicao == 'nucleada':
            superficie = request.form.get('superficie', 'comercial')
            geometria_ebul = request.form.get('geometria_ebul', 'placa_horizontal')
            
            # Calcular q_flux baseado no ΔT (sem campo de entrada)
            delta_T = T_parede - T_sat
            parametros['q_flux'] = 50000 * (delta_T ** 2)  
                
            parametros['superficie'] = superficie
            parametros['geometria_ebul'] = geometria_ebul
            
        elif tipo_ebulicao == 'filme':
            dimensao_car = request.form.get('dimensao_car')
            orientacao = request.form.get('orientacao', 'horizontal')
            
            if not dimensao_car:
                flash('Por favor, preencha a dimensão característica.', 'danger')
                return redirect(url_for('calculadora_ebulicao'))
                
            parametros['dimensao_car'] = float(dimensao_car)
            parametros['orientacao'] = orientacao
        
        # Calcular
        resultado = calcular_mudanca_fase('ebulicao', tipo_ebulicao, parametros)
        
        if 'erro' in resultado:
            for erro in resultado['erro']:
                flash(erro, 'danger')
            return redirect(url_for('calculadora_ebulicao'))
        
        return render_template('calculadora_ebulicao.html', resultado=resultado)
        
    except Exception as e:
        flash(f'Erro no cálculo: {str(e)}', 'danger')
        return redirect(url_for('calculadora_ebulicao'))

@app.route('/calculadora_arranjos_tubos')
def calculadora_arranjos_tubos():
    return render_template('calculadora_arranjos_tubos.html')

@app.route('/calculadora_arranjos_tubos', methods=['POST'])
def calculadora_arranjos_tubos_calcular():
    try:
        # Extrair parâmetros do formulário
        parametros = {
            'D': float(request.form['D']),  
            'S_T': float(request.form['S_T']),  
            'S_L': float(request.form['S_L']),  
            'v': float(request.form['v']),
            'T_s': float(request.form['T_s']),
            'T_inf': float(request.form['T_inf']),
            'fluido': request.form['fluido'],
            'arranjo': request.form['arranjo'],
            'N_fileiras': int(request.form['N_fileiras'])
        }
        
        # Calcular usando a correlação de Zukauskas (padrão)
        resultado = calcular_arranjo_tubos('zukauskas', parametros)
        
    except (ValueError, KeyError) as e:
        resultado = {'erro': [f'Erro nos parâmetros de entrada: {str(e)}']}
    except Exception as e:
        resultado = {'erro': [f'Erro no cálculo: {str(e)}']}
    
    return render_template('calculadora_arranjos_tubos.html', resultado=resultado)

# ================================
# CALCULADORA DE ESCOAMENTO INTERNO
# ================================

@app.route('/calculadora_escoamento_interno')
def calculadora_escoamento_interno():
    """Página da calculadora de escoamento interno"""
    return render_template('calculadora_escoamento_interno.html')

@app.route('/calculadora_escoamento_interno', methods=['POST'])
def calcular_escoamento_interno():
    """Processa os cálculos de escoamento interno para diferentes geometrias"""
    try:
        # Extrair geometria e parâmetros básicos
        geometria = request.form['geometria']
        tipo_calculo = request.form.get('tipo_calculo', 'tradicional')
        
        parametros = {
            'L': float(request.form['L']),  # Comprimento em metros
            'fluido': request.form['fluido'],
            'geometria': geometria,
            'tipo_calculo': tipo_calculo
        }
        
        # Extrair dimensões baseadas na geometria
        if geometria == 'circular':
            parametros['D'] = float(request.form['D'])
        elif geometria == 'quadrado':
            parametros['a'] = float(request.form['a'])
        elif geometria == 'retangular':
            parametros['a'] = float(request.form['a_ret'])
            parametros['b'] = float(request.form['b'])
        
        # Determinar qual campo de escoamento foi preenchido
        v_input = request.form.get('v')
        m_dot_input = request.form.get('m_dot')
        vazao_input = request.form.get('vazao_volumetrica')
        
        # Validar que pelo menos um campo de escoamento foi preenchido
        campos_preenchidos = sum([bool(v_input), bool(m_dot_input), bool(vazao_input)])
        if campos_preenchidos == 0:
            raise ValueError("Pelo menos um campo de escoamento deve ser preenchido: velocidade, fluxo de massa ou vazão volumétrica.")
        
        # Parâmetros baseados no tipo de cálculo
        if tipo_calculo == 'tradicional':
            parametros.update({
                'T_s': float(request.form['T_s']),  # Temperatura da parede em °C
                'T_inf': float(request.form['T_inf']),  # Temperatura do fluido em °C
                'condicao_termica': request.form['condicao_termica']
            })
            
            # Adicionar campo de escoamento preenchido
            if v_input:
                parametros['v'] = float(v_input)
                parametros['tipo_entrada'] = 'velocidade'
            elif m_dot_input:
                parametros['m_dot'] = float(m_dot_input)
                parametros['tipo_entrada'] = 'fluxo_massa'
            elif vazao_input:
                parametros['vazao_volumetrica'] = float(vazao_input)
                parametros['tipo_entrada'] = 'vazao_volumetrica'
                
            # Calcular usando o módulo de escoamento em dutos
            resultado = escoamento_interno_duto(parametros)
            
        else:  # tipo_calculo == 'temp_entrada_saida'
            parametros.update({
                'T_entrada': float(request.form['T_entrada']),  # Temperatura de entrada
                'T_saida': float(request.form['T_saida']),  # Temperatura de saída
                'condicao_termica_ts': request.form.get('condicao_termica_ts', 'aquecimento')
            })
            
            # Adicionar campo de escoamento preenchido
            if v_input:
                parametros['v'] = float(v_input)
                parametros['tipo_entrada'] = 'velocidade'
            elif m_dot_input:
                parametros['m_dot'] = float(m_dot_input)
                parametros['tipo_entrada'] = 'fluxo_massa'
            elif vazao_input:
                parametros['vazao_volumetrica'] = float(vazao_input)
                parametros['tipo_entrada'] = 'vazao_volumetrica'
            
            # Calcular h com temperaturas de entrada e saída
            from escoamento_dutos import calcular_h_com_temperaturas
            resultado = calcular_h_com_temperaturas(parametros)
        
    except (ValueError, KeyError) as e:
        resultado = {'erro': [f'Erro nos parâmetros de entrada: {str(e)}']}
    except Exception as e:
        resultado = {'erro': [f'Erro no cálculo: {str(e)}']}
    
    return render_template('calculadora_escoamento_interno.html', resultado=resultado)

@app.route('/calculadora_temperaturas')
def calculadora_temperaturas():
    """Redireciona para calculadora de escoamento interno"""
    return redirect(url_for('calculadora_escoamento_interno'))

@app.route('/calculadora_temperaturas', methods=['POST'])
def calcular_com_temperaturas():
    """Processa os cálculos com temperaturas de entrada e saída conhecidas"""
    try:
        # Extrair parâmetros do formulário
        D = float(request.form['D'])  # Diâmetro em metros (converter de mm)
        L = float(request.form['L'])  # Comprimento em metros
        T_entrada = float(request.form['T_entrada'])  # Temperatura entrada em °C
        T_saida = float(request.form['T_saida'])  # Temperatura saída em °C
        fluido = request.form['fluido']
        tipo_entrada = request.form['tipo_entrada']
        
        # Importar a função do módulo escoamento_dutos
        from escoamento_dutos import calcular_escoamento_com_temperaturas
        
        # Determinar parâmetro de velocidade/vazão
        if tipo_entrada == 'vazao_volumetrica':
            vazao_volumetrica = float(request.form['vazao_volumetrica'])
            resultado = calcular_escoamento_com_temperaturas(D, L, T_entrada, T_saida, fluido, vazao_volumetrica=vazao_volumetrica)
        elif tipo_entrada == 'velocidade':
            v = float(request.form['v'])
            resultado = calcular_escoamento_com_temperaturas(D, L, T_entrada, T_saida, fluido, v=v)
        else:  # fluxo_massico
            m_dot = float(request.form['m_dot'])
            resultado = calcular_escoamento_com_temperaturas(D, L, T_entrada, T_saida, fluido, m_dot=m_dot)
        
    except (ValueError, KeyError) as e:
        resultado = {'erro': f'Erro nos parâmetros de entrada: {str(e)}'}
    except Exception as e:
        resultado = {'erro': f'Erro no cálculo: {str(e)}'}
    
    return redirect(url_for('calculadora_escoamento_interno'))


# ================================
# ROTAS PARA O ANALISADOR DE SISTEMAS TÉRMICOS (CIRCUITO TÉRMICO)
# ================================
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


@app.route('/circuito_termico')
def circuito_termico():
    return render_template('circuito_termico_moderno.html')

@app.route('/calcular_circuito_termico', methods=['POST'])
def calcular_circuito_termico_route():
    data = request.get_json()
    try:
        geometria = data.get('geometria', 'planar')
        
       
        return jsonify({
            'status': 'recebido',
            'mensagem': 'Dados processados pelo laboratório JavaScript',
            'dados_recebidos': data
        })
    except Exception as e:
        return jsonify({'erro': str(e)}), 400

# ================================
# ROTAS BÁSICAS ADICIONAIS
# ================================

@app.route('/calcular', methods=['POST'])
def calcular():
    """Rota principal para cálculo de aletas"""
    try:
        dados = request.form.to_dict()
        tipo_aleta = dados.get('tipo_aleta')
        material = dados.get('material')
        
        
        dados_float = {}
        for key in ['L', 'W', 't', 'D', 'h', 'Tb', 'Tinf']:
            if key in dados and dados[key]:
                dados_float[key] = float(dados[key])
            else:
                dados_float[key] = 0.0
        
        # Calcular eficiência
        resultado = calcular_eficiencia(
            tipo_aleta, material, 
            dados_float.get('L', 0), dados_float.get('W', 0), dados_float.get('t', 0), dados_float.get('D', 0),
            dados_float.get('h', 25), dados_float.get('Tb', 100), dados_float.get('Tinf', 25)
        )
        
        return render_template('resultado.html', resultado=resultado, dados=dados)
    except Exception as e:
        flash(f'Erro no cálculo: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/tipos_materiais')
def tipos_materiais_base():
    """Página de comparação de materiais"""
    from metricas_engenharia import MATERIAIS_DB
    return render_template('tipos_materiais.html', materiais=MATERIAIS_DB)

@app.route('/calculadora_forcada')
def calculadora_forcada():
    """Página da calculadora de convecção forçada"""
    return render_template('calculadora_forcada.html')

@app.route('/calculadora_natural')
def calculadora_natural():
    """Página da calculadora de convecção natural"""
    return render_template('calculadora_natural.html')

@app.route('/processar_conveccao_forcada', methods=['GET', 'POST'])
def processar_conveccao_forcada_basico():
    """Redireciona para o módulo real de convecção forçada"""
    return redirect(url_for('calculadora_convectivo_tipo', tipo='forcada'))

@app.route('/processar_conveccao_natural', methods=['GET', 'POST'])
def processar_conveccao_natural_basico():
    """Redireciona para o módulo real de convecção natural"""
    return redirect(url_for('calculadora_convectivo_tipo', tipo='natural'))

@app.route('/processar_arranjos_tubos', methods=['GET', 'POST'])
def processar_arranjos_tubos():
    """Redireciona para a calculadora real de arranjos de tubos"""
    return redirect(url_for('calculadora_arranjos_tubos'))

@app.route('/processar_escoamento_interno', methods=['GET', 'POST'])
def processar_escoamento_interno():
    """Redireciona para a calculadora real de escoamento interno"""
    return redirect(url_for('calculadora_escoamento_interno'))

@app.route('/circuito_termico_moderno')
def circuito_termico_moderno():
    """Laboratório de circuito térmico moderno"""
    from flask import make_response
    response = make_response(render_template('circuito_termico_moderno.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# ================================
# LABORATÓRIO TÉRMICO  
# ================================

@app.route('/laboratorio_termico')
def laboratorio_termico():
    """Página principal do Laboratório Térmico Virtual"""
    return render_template('circuito_termico_moderno.html')

# =============================================================================
# API DE MONITORAMENTO EM TEMPO REAL (THREAD-SAFE)
# =============================================================================

@app.route('/api/monitoramento', methods=['GET', 'POST'])
def api_monitoramento():
    global monitoring_cache
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            if data:
                with monitoring_lock:
                    if data.get('reset'):
                        for k in ['t1', 't2', 't3', 't4', 't5', 't6']:
                            monitoring_cache[k] = 0.0
                    else:
                        for k in ['t1', 't2', 't3', 't4', 't5', 't6']:
                            if k in data:
                                monitoring_cache[k] = float(data[k])
                    dados_atuais = monitoring_cache.copy()
                
                return jsonify({
                    'success': True,
                    'message': 'Dados atualizados',
                    'data': dados_atuais
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'Nenhum dado enviado'
                }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Erro: {str(e)}'
            }), 500
    
    elif request.method == 'GET':
        with monitoring_lock:
            dados_atuais = monitoring_cache.copy()
        return jsonify({
            'success': True,
            'data': dados_atuais
        }), 200

@app.route('/painel_status')
def painel_status():
    """Página do Painel de Status em Tempo Real"""
    return render_template('painel_status.html')


@app.route('/api/temperaturas', methods=['GET', 'POST'])
def api_temperaturas():
    """
    API para receber e retornar dados de temperatura do ESP32
    
    POST: Recebe dados de temperatura do ESP32 e atualiza o cache de forma thread-safe
    GET: Retorna as últimas temperaturas registradas
    """
    global monitoring_cache
    
    try:
        if request.method == 'POST':
            if request.is_json:
                data = request.get_json()
                
                with monitoring_lock:
                    for k in ['t1', 't2', 't3', 't4', 't5', 't6']:
                        if k in data:
                            monitoring_cache[k] = float(data[k])
                    cache_copia = monitoring_cache.copy()
                
                print(f"[ESP32] Dados recebidos: {data}")
                print(f"[CACHE] Temperaturas atualizadas: {cache_copia}")
                
                return jsonify({
                    'status': 'sucesso',
                    'mensagem': 'Dados recebidos e armazenados',
                    'cache': cache_copia,
                    'timestamp': data.get('timestamp', None)
                }), 200
            else:
                return jsonify({
                    'status': 'erro',
                    'mensagem': 'Content-Type deve ser application/json'
                }), 400
        
        elif request.method == 'GET':
            with monitoring_lock:
                cache_copia = monitoring_cache.copy()
            return jsonify({
                'status': 'sucesso',
                'temperaturas': cache_copia,
                'timestamp': time.time()
            }), 200
    
    except Exception as e:
        print(f"[ERRO] Erro ao processar dados: {str(e)}")
        return jsonify({
            'status': 'erro',
            'mensagem': f'Erro ao processar requisição: {str(e)}'
        }), 500

@app.route('/api/status', methods=['GET'])
def api_status():
    """
    Retorna o status completo do sistema de monitoramento
    """
    with monitoring_lock:
        cache_copia = monitoring_cache.copy()
    
    return jsonify({
        'status': 'online',
        'sistema': 'Monitor de Temperatura - TCC',
        'versao': '1.0',
        'temperaturas': cache_copia,
        'timestamp': time.time(),
        'servidor': 'Flask',
        'ip': request.remote_addr
    }), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', use_reloader=True, threaded=True)

