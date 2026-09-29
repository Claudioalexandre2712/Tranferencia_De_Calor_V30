"""
Teste do checkpoint V30-ENG-05 (fechamento da placa horizontal).

Escopo: C.16 (rotulo/faixa do ramo 'inferior' do McAdams — SEM mudanca de formula),
C.17 (unificar default de orientacao entre rota form e rota JSON), C.19 (garantir que
h_exp nunca e fabricado a partir de h_teor — nem no backend, nem no fallback JS do
frontend) e independencia h_exp/h_teor (secao 13 do checkpoint).

NAO cobre C.1/C.3/C.4/C.6. NAO altera nenhuma correlacao (Nu = 0.54 Ra^(1/4) /
0.15 Ra^(1/3) / 0.27 Ra^(1/4) continuam intocadas — ha teste de nao-regressao abaixo
comparando com os valores exatos ja registrados em V30-ENG-04).

Sem pytest instalado - script standalone, roda com
`py tests/test_placa_horizontal_fechamento.py`. Sai com codigo 0/1.
"""
import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conveccao_calculadora import conveccao_natural_placa_horizontal as f

FAILURES = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    if not condition:
        FAILURES.append(name)
    return condition


L, W = 0.37, 0.17
LC = (L * W) / (2 * (L + W))

# Valores exatos ja registrados na auditoria V30-ENG-04 (execucao real, antes do
# patch C.16) - usados aqui como baseline de nao-regressao para o patch de rotulo.
BASELINE = {
    'superior': dict(Ra=706772.2981574867, Nu=15.657183431915332, h=7.524121037907613),
    'inferior': dict(Ra=706772.2981574867, Nu=7.828591715957666, h=3.7620605189538066),
}


def test_c16_sem_regressao_numerica():
    """C.16 - corrigir SOMENTE o rotulo/faixa do ramo 'inferior' nao pode mudar
    nenhum valor de Ra/Nu/h em nenhuma orientacao."""
    print("\n=== C16_NAO_REGRESSAO (Ra/Nu/h identicos ao pre-patch) ===")
    all_ok = True
    for orient, esperado in BASELINE.items():
        r = f(Lc=LC, T_s=80.0, T_inf=25.0, orientacao=orient, fluido='ar')
        ok1 = check(f"{orient}: Ra inalterado", math.isclose(r['Ra'], esperado['Ra'], rel_tol=1e-12))
        ok2 = check(f"{orient}: Nu inalterado", math.isclose(r['Nu'], esperado['Nu'], rel_tol=1e-12))
        ok3 = check(f"{orient}: h inalterado", math.isclose(r['h'], esperado['h'], rel_tol=1e-12))
        all_ok = all_ok and ok1 and ok2 and ok3
    return all_ok


def test_c16_formula_inferior_unica_em_toda_faixa():
    """C.16 - o ramo 'inferior' deve continuar usando 0.27*Ra^(1/4) em qualquer Ra,
    incluindo pontos acima do antigo limite morto de 3e10 (nao pode ter passado a
    usar uma formula diferente por engano ao corrigir o rotulo)."""
    print("\n=== C16_FORMULA_UNICA (0.27*Ra^1/4 em toda a faixa) ===")
    all_ok = True
    for Ts in [30.0, 80.0, 200.0, 500.0, 900.0]:
        r = f(Lc=LC, T_s=Ts, T_inf=25.0, orientacao='inferior', fluido='ar')
        nu_esperado = 0.27 * r['Ra'] ** (1 / 4)
        ok = check(f"Ts={Ts}: Nu == 0.27*Ra^(1/4)", math.isclose(r['Nu'], nu_esperado, rel_tol=1e-12),
                   f"Ra={r['Ra']:.4e} Nu={r['Nu']:.6f}")
        all_ok = all_ok and ok
    return all_ok


def test_c17_default_orientacao_unificado():
    """C.17 - rota JSON sem 'orientacao' deve usar o mesmo default da rota de
    formulario ('superior', que tambem e o valor pre-selecionado no <select> da UI)."""
    print("\n=== C17_DEFAULT_UNIFICADO (rota JSON sem orientacao) ===")
    try:
        import app as flask_app
    except Exception as e:
        return check("import de app.py", False, str(e))
    client = flask_app.app.test_client()
    payload = dict(geometria='placa_horizontal', fluido='ar', temperatura_superficie=80.0,
                    temperatura_fluido=25.0, comprimento_placa=L, largura_placa=W)
    resp = client.post('/calculadora_convectivo/natural/calcular', json=payload)
    data = resp.get_json(silent=True) or {}
    return check("orientacao default == 'superior' (rota JSON)", data.get('orientacao') == 'superior',
                 f"orientacao={data.get('orientacao')}")


def test_c19_sem_h_exp_fabricado_no_backend():
    """C.19 - sem T_base, o backend NUNCA deve retornar um balanco_exp/h_exp -
    nao existe fabricacao de resultado experimental no servidor (a fabricacao
    encontrada em V30-ENG-04 era so no fallback JS do frontend, ja removido)."""
    print("\n=== C19_BACKEND_SEM_FABRICACAO (cenario B: sem T_base) ===")
    import app as flask_app
    client = flask_app.app.test_client()
    payload = dict(geometria='placa_horizontal', fluido='ar', temperatura_superficie=80.0,
                    temperatura_fluido=25.0, comprimento_placa=L, largura_placa=W, orientacao='superior')
    resp = client.post('/calculadora_convectivo/natural/calcular', json=payload)
    data = resp.get_json(silent=True) or {}
    ok1 = check("HTTP 200", resp.status_code == 200)
    ok2 = check("balanco_exp == None (sem T_base)", data.get('balanco_exp') is None,
                f"balanco_exp={data.get('balanco_exp')}")
    ok3 = check("coef_convectivo (h_teor) presente e finito",
                isinstance(data.get('coef_convectivo'), (int, float)) and math.isfinite(data['coef_convectivo']))
    return ok1 and ok2 and ok3


def test_c19_frontend_sem_fallback_fictício():
    """C.19 - confirma no HTML/JS que o fallback fixo (h_teorico*1.116, erro
    fixo em 11.6%) foi removido do template, e que o texto de estado
    'indisponivel' existe para o caso sem dado experimental."""
    print("\n=== C19_FRONTEND_SEM_FALLBACK (grep no template) ===")
    caminho = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'templates', 'calculadora_natural.html')
    with open(caminho, 'r', encoding='utf-8') as fh:
        conteudo = fh.read()
    ok1 = check("fallback 'h_teorico * 1.116' NAO existe mais", 'h_teorico * 1.116' not in conteudo)
    ok2 = check("erro_relativo fixo '11.6' (fallback antigo) NAO existe mais",
                'erro_relativo: 11.6' not in conteudo)
    ok3 = check("texto de estado indisponivel presente",
                'Resultado experimental indisponível' in conteudo)
    ok4 = check("h_exp derivado apenas quando backend confirma numero real (temExperimental)",
                'temExperimental' in conteudo and "typeof bExp.h_experimental === 'number'" in conteudo)
    return ok1 and ok2 and ok3 and ok4


def test_h_exp_h_teor_independentes_variando_teorico():
    """Secao 13, Teste A - variar so parametros teoricos (fluido) mantendo entradas
    experimentais fixas: h_exp nao pode mudar."""
    print("\n=== INDEPENDENCIA_A (variar fluido teorico, h_exp deve ficar igual) ===")
    import app as flask_app
    client = flask_app.app.test_client()
    base_exp = dict(T_base=80.05, X_correcao=0.0, espessura=0.005, k_material=222.0, emissividade=0.09)
    h_exp_vals = []
    for fluido in ['ar', 'agua', 'oleo', 'mercurio']:
        p = dict(geometria='placa_horizontal', fluido=fluido, temperatura_superficie=80.0, temperatura_fluido=25.0,
                  comprimento_placa=L, largura_placa=W, orientacao='superior', **base_exp)
        r = client.post('/calculadora_convectivo/natural/calcular', json=p)
        d = r.get_json(silent=True) or {}
        b = d.get('balanco_exp') or {}
        h_exp_vals.append(b.get('h_experimental'))
    ok = check("h_exp identico para os 4 fluidos teoricos", len(set(h_exp_vals)) == 1, f"valores={h_exp_vals}")
    return ok


def test_h_exp_h_teor_independentes_variando_experimental():
    """Secao 13, Teste B - variar so entrada experimental (T_base) mantendo
    parametros teoricos fixos: h_teor nao pode mudar."""
    print("\n=== INDEPENDENCIA_B (variar T_base, h_teor deve ficar igual) ===")
    import app as flask_app
    client = flask_app.app.test_client()
    h_teor_vals = []
    for T_base in [80.05, 82.0, 90.0, 120.0]:
        p = dict(geometria='placa_horizontal', fluido='ar', temperatura_superficie=80.0, temperatura_fluido=25.0,
                  comprimento_placa=L, largura_placa=W, orientacao='superior',
                  T_base=T_base, X_correcao=0.0, espessura=0.005, k_material=222.0, emissividade=0.09)
        r = client.post('/calculadora_convectivo/natural/calcular', json=p)
        d = r.get_json(silent=True) or {}
        h_teor_vals.append(d.get('coef_convectivo'))
    ok = check("h_teor identico para os 4 T_base", len(set(h_teor_vals)) == 1, f"valores={h_teor_vals}")
    return ok


def test_real_route_ambas_orientacoes():
    """Rota real - face para cima e para baixo, HTTP 200, JSON valido, campos
    finitos, sem 'erro', sem numero experimental inventado quando T_base ausente."""
    print("\n=== REAL_ROUTE_ORIENTACOES ===")
    import app as flask_app
    client = flask_app.app.test_client()
    all_ok = True
    for orient in ['superior', 'inferior']:
        p = dict(geometria='placa_horizontal', fluido='ar', temperatura_superficie=80.0, temperatura_fluido=25.0,
                  comprimento_placa=L, largura_placa=W, orientacao=orient)
        r = client.post('/calculadora_convectivo/natural/calcular', json=p)
        d = r.get_json(silent=True) or {}
        ok1 = check(f"{orient}: HTTP 200", r.status_code == 200)
        ok2 = check(f"{orient}: sem 'erro'", 'erro' not in d, f"data={d}")
        ok3 = check(f"{orient}: orientacao ecoada corretamente", d.get('orientacao') == orient)
        vals = [d.get('rayleigh'), d.get('nusselt'), d.get('coef_convectivo')]
        ok4 = check(f"{orient}: Ra/Nu/h finitos", all(isinstance(v, (int, float)) and math.isfinite(v) for v in vals))
        ok5 = check(f"{orient}: balanco_exp None (sem T_base, sem numero inventado)", d.get('balanco_exp') is None)
        all_ok = all_ok and ok1 and ok2 and ok3 and ok4 and ok5
    return all_ok


if __name__ == '__main__':
    results = [
        test_c16_sem_regressao_numerica(),
        test_c16_formula_inferior_unica_em_toda_faixa(),
        test_c17_default_orientacao_unificado(),
        test_c19_sem_h_exp_fabricado_no_backend(),
        test_c19_frontend_sem_fallback_fictício(),
        test_h_exp_h_teor_independentes_variando_teorico(),
        test_h_exp_h_teor_independentes_variando_experimental(),
        test_real_route_ambas_orientacoes(),
    ]
    print("\n=== RESUMO ===")
    print(f"TESTS_PASSED = {sum(results)}")
    print(f"TESTS_FAILED = {len(results) - sum(results)}")
    if FAILURES:
        print("Falhas:", ", ".join(FAILURES))
    sys.exit(0 if all(results) else 1)
