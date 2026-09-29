"""
Testes dos checkpoints V30-ENG-01, V30-ENG-02 e V30-ENG-03 (FASE 03, achados C.2, C.8, C.11).

Escopo: apenas conveccao_natural_placa_vertical (Churchill-Chu, placa vertical) e o
helper obter_beta_expansao_termica() que ela usa.
Nao cobre C.1/Hilpert, C.3/cilindro horizontal, C.4/Hausen, C.6/Zukauskas, C.10 (ar).

Sem pytest instalado no ambiente (nao adicionado como dependencia nova, fora de
escopo destes checkpoints) - script standalone, roda com `py tests/test_conveccao_natural_placa_vertical.py`.
Sai com codigo 0 se tudo passar, 1 se algo falhar.
"""
import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conveccao_calculadora import conveccao_natural_placa_vertical, interpolar_propriedades, obter_beta_expansao_termica

FAILURES = []


def churchill_chu_nu(Ra, Pr):
    """Correlacao canonica de Churchill-Chu (Incropera Cap.9 Eq.9.26), sem multiplicador."""
    return (0.825 + (0.387 * Ra ** (1 / 6)) / (1 + (0.492 / Pr) ** (9 / 16)) ** (8 / 27)) ** 2


def L_for_target_Ra(Ra_target, T_s, T_inf, fluido='ar'):
    """Resolve L (forma fechada, Ra = K*L**3) para atingir um Ra alvo com o MESMO
    beta/propriedades que a funcao real usa internamente.

    Atualizado no checkpoint V30-ENG-02: beta para 'ar' agora e 1/T_filme (corrigido
    em C.8), igual ao usado pela funcao real - antes deste checkpoint este helper
    usava o beta hardcoded antigo (3.21e-4), que nao existe mais no codigo."""
    T_filme = (T_s + T_inf) / 2 + 273.15
    props = interpolar_propriedades(fluido, T_filme)
    beta = 1 / T_filme  # gas ideal - mesma formula usada por conveccao_natural_placa_vertical
    g = 9.81
    K = g * beta * abs(T_s - T_inf) / (props['nu'] * props['alpha'])
    return (Ra_target / K) ** (1 / 3)


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    if not condition:
        FAILURES.append(name)
    return condition


def test_churchill_chu_canonical_formula_regression():
    """CANONICAL_FORMULA_REGRESSION_TEST (renomeado no V30-ENG-02; antes chamado
    test_textbook_baseline_cengel_ex9_2a / TEXTBOOK_BASELINE_TEST - nome corrigido
    porque o teste NAO reproduz o exemplo do livro, so garante que nenhum
    multiplicador de calibracao (x1.57/x1.20, removido em C.2) volte a existir.

    Caso usado: Cengel & Ghajar 4a ed., Exemplo 9-2(a), pag.533 (L=0.6m, Ts=90C,
    Tinf=30C, ar) - mantido como entrada de referencia, mas o que se afirma aqui e
    so que Nu_codigo == Churchill-Chu puro aplicado ao proprio Ra/Pr que a funcao
    calculou, independente de qual modelo de propriedades/beta esta em uso.
    Depois da correcao de C.8 (beta), este caso NAO cai mais na antiga janela
    8e7<=Ra<=1e8 do x1.57 (Ra agora e ~7.6e8) - por isso essa checagem de faixa,
    que existia na versao anterior deste teste, foi removida daqui e vive isolada
    em test_regression_case_old_1_57_window (caso sintetico, nao bibliografico).
    """
    print("\n=== CANONICAL_FORMULA_REGRESSION_TEST (Cengel Exemplo 9-2a como entrada) ===")
    r = conveccao_natural_placa_vertical(L=0.6, T_s=90, T_inf=30, fluido='ar')
    Nu_pure = churchill_chu_nu(r['Ra'], r['Pr'])
    h_pure = Nu_pure * r['propriedades']['k'] / 0.6

    ok1 = check(
        "Nu do codigo == Churchill-Chu puro (tol 1e-9 relativo)",
        math.isclose(r['Nu'], Nu_pure, rel_tol=1e-9),
        f"Nu_codigo={r['Nu']:.6f} Nu_puro={Nu_pure:.6f}"
    )
    ok2 = check(
        "h do codigo == Nu_puro*k/L (tol 1e-9 relativo)",
        math.isclose(r['h'], h_pure, rel_tol=1e-9),
        f"h_codigo={r['h']:.6f} h_puro={h_pure:.6f}"
    )

    print(f"  Ra={r['Ra']:.6e}  Nu={r['Nu']:.4f}  h={r['h']:.4f} W/m2K  Pr={r['Pr']:.4f}  beta={r['beta']:.6e}")
    return ok1 and ok2


def test_beta_ideal_gas_regression():
    """BETA_IDEAL_GAS_REGRESSION_TEST (novo no V30-ENG-02, achado C.8).

    Valida SOMENTE a correcao do beta - nao mistura com a divergencia de
    propriedades vs. Tabela A-15 (isso fica em test_textbook_sanity_check_table_a15).

    Recalcula Ra de forma independente dentro do proprio teste, usando:
      - beta_expected = 1/Tf_K (formula canonica, gas ideal)
      - nu/alpha OBTIDOS DA MESMA FUNCAO que o modulo usa internamente
        (interpolar_propriedades) - ou seja, o teste nao assume nenhum valor de
        propriedade "correto" por conta propria, so recalcula o Ra que a funcao
        DEVERIA dar se beta estiver certo, dado o modelo de propriedades atual.
    """
    print("\n=== BETA_IDEAL_GAS_REGRESSION_TEST (achado C.8) ===")
    L, T_s, T_inf, fluido = 0.6, 90.0, 30.0, 'ar'

    Tf_K = (T_s + T_inf) / 2 + 273.15
    beta_expected = 1 / Tf_K
    props = interpolar_propriedades(fluido, Tf_K)
    g = 9.81
    Ra_expected = g * beta_expected * abs(T_s - T_inf) * L ** 3 / (props['nu'] * props['alpha'])

    r = conveccao_natural_placa_vertical(L=L, T_s=T_s, T_inf=T_inf, fluido=fluido)

    ok1 = check(
        "beta retornado == 1/Tf_K (tol 1e-9 relativo)",
        math.isclose(r['beta'], beta_expected, rel_tol=1e-9),
        f"beta_codigo={r['beta']:.8e}  beta_esperado={beta_expected:.8e}"
    )
    ok2 = check(
        "Ra retornado == Ra_expected (beta=1/Tf, propriedades do modulo) — tol 1e-6 relativo",
        math.isclose(r['Ra'], Ra_expected, rel_tol=1e-6),
        f"Ra_codigo={r['Ra']:.6e}  Ra_esperado={Ra_expected:.6e}"
    )
    ok3 = check(
        "beta NAO e mais o valor antigo hardcoded (3.21e-4)",
        not math.isclose(r['beta'], 3.21e-4, rel_tol=1e-3),
        f"beta_codigo={r['beta']:.6e}"
    )

    print(f"  Tf_K={Tf_K:.2f}  beta={r['beta']:.6e}  Ra={r['Ra']:.6e}  Nu={r['Nu']:.4f}  h={r['h']:.4f}")
    return ok1 and ok2 and ok3


def test_textbook_sanity_check_table_a15():
    """TEXTBOOK_SANITY_CHECK (novo no V30-ENG-02) — benchmark de referencia contra a
    Tabela A-15 (Cengel & Ghajar) para o caso do Exemplo 9-2(a), Tf=60C.

    NAO e um teste de igualdade rigida — a funcao usa seu proprio modelo de
    propriedades (interpolar_propriedades, formulas polinomiais/Sutherland), nao a
    tabela do livro; a divergencia de propriedades e um achado separado
    (AIR_PROPERTY_MODEL_DIVERGENCE, nao corrigido, nao classificado como critico).
    Este teste so falha se a divergencia sair da faixa ja medida e documentada no
    diagnostico V30-ENG-01B/V30-ENG-02 (haveria uma regressao NOVA, nao a
    divergencia de propriedades ja conhecida).

    Referencia (Tabela A-15, Tf=60C): k=0.02953 W/m.K, nu=2.097e-5 m2/s,
    alpha=2.931e-5 m2/s, Pr=0.7154, beta=1/Tf=3.001651e-3 K^-1 (identico ao beta
    agora usado pelo codigo, apos C.8).
    """
    print("\n=== TEXTBOOK_SANITY_CHECK (benchmark vs Tabela A-15, nao e identity test) ===")
    L, T_s, T_inf = 0.6, 90.0, 30.0

    k_ref, nu_ref, alpha_ref, Pr_ref = 0.02953, 2.097e-5, 2.931e-5, 0.7154
    beta_ref = 1 / ((T_s + T_inf) / 2 + 273.15)
    g = 9.81
    Ra_ref = g * beta_ref * abs(T_s - T_inf) * L ** 3 / (nu_ref * alpha_ref)
    Nu_ref = churchill_chu_nu(Ra_ref, Pr_ref)
    h_ref = Nu_ref * k_ref / L

    r = conveccao_natural_placa_vertical(L=L, T_s=T_s, T_inf=T_inf, fluido='ar')

    def pct(cur, ref):
        return (cur - ref) / ref * 100

    diff_Ra = pct(r['Ra'], Ra_ref)
    diff_Nu = pct(r['Nu'], Nu_ref)
    diff_h = pct(r['h'], h_ref)

    # Faixas de tolerancia = divergencia ja medida/documentada em C.8 (AIR_PROPERTY_MODEL_DIVERGENCE),
    # com margem - NAO calibradas para "passar", servem para detectar se a divergencia PIOROU.
    ok1 = check("Ra dentro da faixa de divergencia conhecida (<30%)", abs(diff_Ra) < 30.0,
                f"Ra_codigo={r['Ra']:.6e}  Ra_referencia={Ra_ref:.6e}  diff={diff_Ra:+.2f}%")
    ok2 = check("Nu dentro da faixa de divergencia conhecida (<15%)", abs(diff_Nu) < 15.0,
                f"Nu_codigo={r['Nu']:.4f}  Nu_referencia={Nu_ref:.4f}  diff={diff_Nu:+.2f}%")
    ok3 = check("h dentro da faixa de divergencia conhecida (<10%)", abs(diff_h) < 10.0,
                f"h_codigo={r['h']:.4f}  h_referencia={h_ref:.4f}  diff={diff_h:+.2f}%")

    print("  NOTA: divergencia esperada e conhecida (AIR_PROPERTY_MODEL_DIVERGENCE, nao corrigida "
          "nesta fase) - este teste so serve de sentinela contra regressao futura, nao valida "
          "correcao numerica exata.")
    return ok1 and ok2 and ok3


def test_regression_case_old_1_57_window():
    """REGRESSION_CASE (NAO e exemplo bibliografico) — caso sintetico, fisicamente
    valido, construido para cair dentro da antiga janela 8e7<=Ra<=1e8 do fator x1.57,
    com entradas DIFERENTES do caso do Cengel Exemplo 9-2(a) acima."""
    print("\n=== REGRESSION_CASE (janela antiga do x1.57, caso sintetico) ===")
    T_s, T_inf, fluido = 70.0, 20.0, 'ar'
    L = L_for_target_Ra(9.5e7, T_s, T_inf, fluido)

    r = conveccao_natural_placa_vertical(L=L, T_s=T_s, T_inf=T_inf, fluido=fluido)
    Nu_pure = churchill_chu_nu(r['Ra'], r['Pr'])

    ok1 = check(
        "Ra do caso sintetico cai na antiga faixa 8e7<=Ra<=1e8",
        8e7 <= r['Ra'] <= 1e8,
        f"Ra={r['Ra']:.6e}"
    )
    ok2 = check(
        "Nu do codigo == Churchill-Chu puro (sem x1.57) — tol 1e-9",
        math.isclose(r['Nu'], Nu_pure, rel_tol=1e-9),
        f"Nu_codigo={r['Nu']:.4f} Nu_puro={Nu_pure:.4f}"
    )
    ok3 = check(
        "Nu do codigo NAO e 1.57x o valor puro (prova que o fator sumiu)",
        not math.isclose(r['Nu'], Nu_pure * 1.57, rel_tol=1e-6),
        f"Nu_codigo={r['Nu']:.4f}  Nu_puro*1.57={Nu_pure*1.57:.4f}"
    )

    print(f"  L={L:.4f} m  Ra={r['Ra']:.6e}  Nu={r['Nu']:.4f}  Pr={r['Pr']:.4f}")
    return ok1 and ok2 and ok3


def test_continuity_around_old_thresholds():
    """CONTINUITY_TEST — avalia Nu logo abaixo/acima dos antigos limites Ra~8e7 e
    Ra~1e8, confirmando que nao ha mais salto artificial (x1.57 <-> x1.20) nesses
    pontos. Usa T_s/T_inf fixos e varia L (forma fechada Ra=K*L**3) para atingir
    Ra alvo com passo pequeno (+-1%) em torno de cada antigo limite."""
    print("\n=== CONTINUITY_TEST (antigos limites Ra=8e7 e Ra=1e8) ===")
    T_s, T_inf, fluido = 70.0, 20.0, 'ar'
    all_ok = True

    for label, Ra_center in [("Ra~8e7", 8e7), ("Ra~1e8", 1e8)]:
        Ra_below = Ra_center * 0.99
        Ra_above = Ra_center * 1.01

        L_below = L_for_target_Ra(Ra_below, T_s, T_inf, fluido)
        L_above = L_for_target_Ra(Ra_above, T_s, T_inf, fluido)

        r_below = conveccao_natural_placa_vertical(L=L_below, T_s=T_s, T_inf=T_inf, fluido=fluido)
        r_above = conveccao_natural_placa_vertical(L=L_above, T_s=T_s, T_inf=T_inf, fluido=fluido)

        Nu_below, Nu_above = r_below['Nu'], r_above['Nu']
        variacao_pct = (Nu_above - Nu_below) / Nu_below * 100

        # Para um passo de Ra de +2% em torno do limiar, a formula continua de
        # Churchill-Chu (expoente 1/6 dentro de um quadrado) produz uma variacao de
        # Nu da ordem de poucos % - nao os +57%/+20% do antigo salto discreto.
        ok = check(
            f"{label}: sem salto artificial (variacao Nu < 5% para step de Ra de 2%)",
            abs(variacao_pct) < 5.0,
            f"Nu({Ra_below:.4e})={Nu_below:.4f}  Nu({Ra_above:.4e})={Nu_above:.4f}  "
            f"variacao={variacao_pct:+.3f}%"
        )
        all_ok = all_ok and ok

    return all_ok


def test_real_route_natural_placa_vertical():
    """REGRESSAO FUNCIONAL — rota real /calculadora_convectivo/natural/calcular,
    geometria=placa_vertical, via Flask test_client (sem subir servidor real).

    O frontend real (templates/calculadora_natural.html, funcao enviarCalculoAjax)
    usa fetch() com Content-Type: application/json - testado aqui com o mesmo
    formato de payload e os mesmos nomes de campo que o JS realmente envia."""
    print("\n=== REAL_ROUTE_TEST (/calculadora_convectivo/natural/calcular, JSON, como o frontend real) ===")
    try:
        import app as flask_app
    except Exception as e:
        return check("Rota real: import de app.py sem erro", False, f"erro ao importar app.py: {e}")

    client = flask_app.app.test_client()
    resp = client.post(
        '/calculadora_convectivo/natural/calcular',
        json={
            'geometria': 'placa_vertical',
            'fluido': 'ar',
            'temperatura_superficie': 90.0,
            'temperatura_fluido': 30.0,
            'altura': 0.6,
        },
    )

    ok1 = check("Rota real: HTTP 200", resp.status_code == 200, f"status={resp.status_code}")
    data = resp.get_json(silent=True) or {}
    ok2 = check("Rota real: resposta JSON sem campo 'erro'", 'erro' not in data, f"data={data}")

    chaves_esperadas = {'sucesso', 'tipo', 'geometria', 'rayleigh', 'nusselt', 'coef_convectivo', 'prandtl'}
    chaves_presentes = set(data.keys())
    ok3 = check(
        "Rota real: nenhuma chave de resposta esperada desapareceu",
        chaves_esperadas.issubset(chaves_presentes),
        f"faltando={chaves_esperadas - chaves_presentes}"
    )

    Nu_esperado = None
    if ok2:
        Nu_esperado = data.get('nusselt')
        ok4 = check(
            "Rota real: 'nusselt' retornado bate com Churchill-Chu puro (sem x1.57/x1.20)",
            isinstance(Nu_esperado, (int, float)) and math.isclose(
                Nu_esperado, churchill_chu_nu(data.get('rayleigh'), data.get('prandtl')), rel_tol=1e-6
            ),
            f"nusselt={Nu_esperado}"
        )
    else:
        ok4 = check("Rota real: 'nusselt' retornado bate com Churchill-Chu puro", False, "resposta com erro, pulado")

    print(f"  resposta: rayleigh={data.get('rayleigh')}  nusselt={data.get('nusselt')}  "
          f"coef_convectivo={data.get('coef_convectivo')}  prandtl={data.get('prandtl')}  "
          f"beta={data.get('beta')}")
    return ok1 and ok2 and ok3 and ok4


def test_beta_agua_tabela():
    """C.11 - beta da agua: reproduz Cengel & Ghajar Tab.A-9 nos breakpoints (15/20/40/65C,
    mesmos ja usados por interpolar_propriedades() para as demais propriedades da agua) e
    interpola linearmente entre eles."""
    print("\n=== BETA_AGUA_TESTS (Tab.A-9, breakpoints 15/20/40/65C) ===")
    K = 273.15
    ok1 = check("beta(15C) == 1.38e-4 (breakpoint inferior, tabelado)",
                math.isclose(obter_beta_expansao_termica('agua', 15+K), 1.38e-4, rel_tol=1e-9))
    ok2 = check("beta(20C) == 1.95e-4 (breakpoint, tabelado)",
                math.isclose(obter_beta_expansao_termica('agua', 20+K), 1.95e-4, rel_tol=1e-9))
    ok3 = check("beta(40C) == 3.77e-4 (breakpoint, tabelado)",
                math.isclose(obter_beta_expansao_termica('agua', 40+K), 3.77e-4, rel_tol=1e-9))
    ok4 = check("beta(65C) == 5.48e-4 (breakpoint superior, tabelado)",
                math.isclose(obter_beta_expansao_termica('agua', 65+K), 5.48e-4, rel_tol=1e-9))
    # Ponto intermediario de interpolacao (30C, entre os breakpoints 20 e 40C) - NAO e o
    # valor exato da linha de 30C do livro (2.94e-4): a implementacao reusa os mesmos 4
    # breakpoints ja usados pelas demais propriedades da agua nesta funcao (instrucao do
    # checkpoint V30-ENG-03), nao uma tabela nova mais fina. Valor esperado = interpolacao
    # linear entre beta(20C)=1.95e-4 e beta(40C)=3.77e-4.
    beta_30_interp = 1.95e-4 + (30-20)/20*(3.77e-4-1.95e-4)
    ok5 = check("beta(30C) == interpolacao linear 20C-40C (nao a linha exata do livro)",
                math.isclose(obter_beta_expansao_termica('agua', 30+K), beta_30_interp, rel_tol=1e-9),
                f"beta(30C)={obter_beta_expansao_termica('agua', 30+K):.6e}  interp_esperado={beta_30_interp:.6e}  "
                f"(linha exata do livro a 30C seria 2.94e-4, nao usada por design)")
    return ok1 and ok2 and ok3 and ok4 and ok5


def test_beta_oleo_constante():
    """C.11 - beta do oleo: constante 7.0e-4 K^-1 (Incropera Tab.A.5, oleo de motor nao
    usado), confirmado invariante em toda a faixa tabulada (273-430K)."""
    print("\n=== BETA_OLEO_TESTS (Incropera Tab.A.5) ===")
    K = 273.15
    ok1 = check("beta(20C) == 7.0e-4", math.isclose(obter_beta_expansao_termica('oleo', 20+K), 7.0e-4, rel_tol=1e-9))
    ok2 = check("beta(80C) == 7.0e-4 (mesma constante, faixa tabulada)",
                math.isclose(obter_beta_expansao_termica('oleo', 80+K), 7.0e-4, rel_tol=1e-9))
    ok3 = check("beta(150C) == 7.0e-4 (proximo do limite superior tabulado, ~157C)",
                math.isclose(obter_beta_expansao_termica('oleo', 150+K), 7.0e-4, rel_tol=1e-9))
    return ok1 and ok2 and ok3


def test_beta_mercurio_constante():
    """C.11 - beta do mercurio: constante 1.81e-4 K^-1 (Incropera Tab.A.5), variacao
    confirmada <1% entre 273-350K na fonte."""
    print("\n=== BETA_MERCURIO_TESTS (Incropera Tab.A.5) ===")
    K = 273.15
    ok1 = check("beta(0C) == 1.81e-4", math.isclose(obter_beta_expansao_termica('mercurio', 0+K), 1.81e-4, rel_tol=1e-9))
    ok2 = check("beta(30C) == 1.81e-4", math.isclose(obter_beta_expansao_termica('mercurio', 30+K), 1.81e-4, rel_tol=1e-9))
    ok3 = check("beta(77C) == 1.81e-4 (limite superior de alta confianca, 350K)",
                math.isclose(obter_beta_expansao_termica('mercurio', 77+K), 1.81e-4, rel_tol=1e-9))
    return ok1 and ok2 and ok3


def test_beta_nao_e_mais_1_sobre_T_para_liquidos():
    """C.11 - regressao central: beta de agua/oleo/mercurio NUNCA deve voltar a ser 1/T_filme
    (o bug original). Para o ar, beta DEVE continuar sendo 1/T_filme (C.8 preservado)."""
    print("\n=== BETA_NOT_1_OVER_T_FOR_LIQUIDS (regressao C.11) ===")
    T_filme = 30 + 273.15
    beta_1_sobre_T = 1 / T_filme
    all_ok = True
    for fluido in ['agua', 'oleo', 'mercurio']:
        beta = obter_beta_expansao_termica(fluido, T_filme)
        ok = check(f"beta({fluido}) != 1/T_filme", not math.isclose(beta, beta_1_sobre_T, rel_tol=1e-2),
                   f"beta={beta:.4e}  1/T_filme={beta_1_sobre_T:.4e}")
        all_ok = all_ok and ok
    ok_ar = check("beta(ar) == 1/T_filme (C.8 preservado)",
                  math.isclose(obter_beta_expansao_termica('ar', T_filme), beta_1_sobre_T, rel_tol=1e-9))
    return all_ok and ok_ar


def test_resultado_agua_antes_depois():
    """C.11 - resultado real antes/depois para agua, caso diagnostico do V30-ENG-02C
    (L=0.6m, Ts=40C, Tinf=20C, Tf=30C - dentro da faixa tabulada 15-65C).
    ANTES = beta=1/T_filme (formula antiga, recalculada aqui so para comparacao - o
    codigo real ja nao usa mais essa formula para agua, ver git diff do checkpoint)."""
    print("\n=== RESULTADO_AGUA_ANTES_DEPOIS ===")
    L, T_s, T_inf, fluido = 0.6, 40.0, 20.0, 'agua'
    r = conveccao_natural_placa_vertical(L=L, T_s=T_s, T_inf=T_inf, fluido=fluido)

    T_filme = (T_s+T_inf)/2 + 273.15
    props = interpolar_propriedades(fluido, T_filme)
    beta_antigo = 1/T_filme
    Ra_antigo = 9.81*beta_antigo*abs(T_s-T_inf)*L**3/(props['nu']*props['alpha'])
    Nu_antigo = churchill_chu_nu(Ra_antigo, props['Pr'])
    h_antigo = Nu_antigo*props['k']/L

    print(f"  ANTES (beta=1/Tf, formula antiga): beta={beta_antigo:.6e} Ra={Ra_antigo:.6e} Nu={Nu_antigo:.4f} h={h_antigo:.4f}")
    print(f"  DEPOIS (execucao real, pos-patch): beta={r['beta']:.6e} Ra={r['Ra']:.6e} Nu={r['Nu']:.4f} h={r['h']:.4f}")
    reducao_h = (r['h']-h_antigo)/h_antigo*100
    print(f"  variacao em h: {reducao_h:+.2f}%")

    ok1 = check("beta DEPOIS != beta ANTES (fator ~11.5x menor)",
                not math.isclose(r['beta'], beta_antigo, rel_tol=1e-2))
    ok2 = check("beta DEPOIS bate com obter_beta_expansao_termica isolado",
                math.isclose(r['beta'], obter_beta_expansao_termica(fluido, T_filme), rel_tol=1e-9))
    ok3 = check("Ra/Nu/h finitos e positivos", all(math.isfinite(x) and x > 0 for x in [r['Ra'], r['Nu'], r['h']]))
    return ok1 and ok2 and ok3


def test_resultado_oleo_antes_depois():
    """C.11 - resultado real antes/depois para oleo (L=0.6m, Ts=80C, Tinf=20C, Tf=50C -
    dentro da faixa tabulada 0-157C)."""
    print("\n=== RESULTADO_OLEO_ANTES_DEPOIS ===")
    L, T_s, T_inf, fluido = 0.6, 80.0, 20.0, 'oleo'
    r = conveccao_natural_placa_vertical(L=L, T_s=T_s, T_inf=T_inf, fluido=fluido)

    T_filme = (T_s+T_inf)/2 + 273.15
    props = interpolar_propriedades(fluido, T_filme)
    beta_antigo = 1/T_filme
    Ra_antigo = 9.81*beta_antigo*abs(T_s-T_inf)*L**3/(props['nu']*props['alpha'])
    Nu_antigo = churchill_chu_nu(Ra_antigo, props['Pr'])
    h_antigo = Nu_antigo*props['k']/L

    print(f"  ANTES (beta=1/Tf, formula antiga): beta={beta_antigo:.6e} Ra={Ra_antigo:.6e} Nu={Nu_antigo:.4f} h={h_antigo:.4f}")
    print(f"  DEPOIS (execucao real, pos-patch): beta={r['beta']:.6e} Ra={r['Ra']:.6e} Nu={r['Nu']:.4f} h={r['h']:.4f}")
    reducao_h = (r['h']-h_antigo)/h_antigo*100
    print(f"  variacao em h: {reducao_h:+.2f}%")

    ok1 = check("beta DEPOIS != beta ANTES (fator ~4.4x menor)",
                not math.isclose(r['beta'], beta_antigo, rel_tol=1e-2))
    ok2 = check("beta DEPOIS == 7.0e-4 (constante Incropera Tab.A.5)",
                math.isclose(r['beta'], 7.0e-4, rel_tol=1e-9))
    ok3 = check("Ra/Nu/h finitos e positivos", all(math.isfinite(x) and x > 0 for x in [r['Ra'], r['Nu'], r['h']]))
    return ok1 and ok2 and ok3


def test_resultado_mercurio_antes_depois():
    """C.11 - resultado real antes/depois para mercurio (L=0.6m, Ts=40C, Tinf=20C,
    Tf=30C - dentro da faixa de alta confianca 0-77C / 273-350K)."""
    print("\n=== RESULTADO_MERCURIO_ANTES_DEPOIS ===")
    L, T_s, T_inf, fluido = 0.6, 40.0, 20.0, 'mercurio'
    r = conveccao_natural_placa_vertical(L=L, T_s=T_s, T_inf=T_inf, fluido=fluido)

    T_filme = (T_s+T_inf)/2 + 273.15
    props = interpolar_propriedades(fluido, T_filme)
    beta_antigo = 1/T_filme
    Ra_antigo = 9.81*beta_antigo*abs(T_s-T_inf)*L**3/(props['nu']*props['alpha'])
    Nu_antigo = churchill_chu_nu(Ra_antigo, props['Pr'])
    h_antigo = Nu_antigo*props['k']/L

    print(f"  ANTES (beta=1/Tf, formula antiga): beta={beta_antigo:.6e} Ra={Ra_antigo:.6e} Nu={Nu_antigo:.4f} h={h_antigo:.4f}")
    print(f"  DEPOIS (execucao real, pos-patch): beta={r['beta']:.6e} Ra={r['Ra']:.6e} Nu={r['Nu']:.4f} h={r['h']:.4f}")
    reducao_h = (r['h']-h_antigo)/h_antigo*100
    print(f"  variacao em h: {reducao_h:+.2f}%")

    ok1 = check("beta DEPOIS != beta ANTES (fator ~18x menor)",
                not math.isclose(r['beta'], beta_antigo, rel_tol=1e-2))
    ok2 = check("beta DEPOIS == 1.81e-4 (constante Incropera Tab.A.5)",
                math.isclose(r['beta'], 1.81e-4, rel_tol=1e-9))
    ok3 = check("Ra/Nu/h finitos e positivos", all(math.isfinite(x) and x > 0 for x in [r['Ra'], r['Nu'], r['h']]))
    return ok1 and ok2 and ok3


def test_real_route_liquidos():
    """C.11 - REGRESSAO FUNCIONAL para agua/oleo/mercurio via a rota real
    /calculadora_convectivo/natural/calcular, mesmo payload JSON que o frontend envia."""
    print("\n=== REAL_ROUTE_TEST_LIQUIDOS ===")
    try:
        import app as flask_app
    except Exception as e:
        return check("Rota real (liquidos): import de app.py sem erro", False, f"erro ao importar app.py: {e}")

    client = flask_app.app.test_client()
    casos = {
        'agua':     dict(temperatura_superficie=40.0, temperatura_fluido=20.0, altura=0.6),
        'oleo':     dict(temperatura_superficie=80.0, temperatura_fluido=20.0, altura=0.6),
        'mercurio': dict(temperatura_superficie=40.0, temperatura_fluido=20.0, altura=0.6),
    }
    all_ok = True
    for fluido, params in casos.items():
        payload = dict(geometria='placa_vertical', fluido=fluido, **params)
        resp = client.post('/calculadora_convectivo/natural/calcular', json=payload)
        ok1 = check(f"{fluido}: HTTP 200", resp.status_code == 200, f"status={resp.status_code}")
        data = resp.get_json(silent=True) or {}
        ok2 = check(f"{fluido}: resposta sem 'erro'", 'erro' not in data, f"data={data}")
        chaves_esperadas = {'sucesso', 'tipo', 'geometria', 'rayleigh', 'nusselt', 'coef_convectivo', 'prandtl', 'beta'}
        ok3 = check(f"{fluido}: nenhuma chave esperada desapareceu",
                    chaves_esperadas.issubset(set(data.keys())), f"faltando={chaves_esperadas - set(data.keys())}")
        vals = [data.get('rayleigh'), data.get('nusselt'), data.get('coef_convectivo')]
        ok4 = check(f"{fluido}: Ra/Nu/h finitos", all(isinstance(v, (int, float)) and math.isfinite(v) for v in vals),
                    f"rayleigh={data.get('rayleigh')} nusselt={data.get('nusselt')} coef_convectivo={data.get('coef_convectivo')}")
        print(f"  {fluido}: beta={data.get('beta')}  rayleigh={data.get('rayleigh')}  nusselt={data.get('nusselt')}  "
              f"coef_convectivo={data.get('coef_convectivo')}")
        all_ok = all_ok and ok1 and ok2 and ok3 and ok4
    return all_ok


if __name__ == '__main__':
    results = [
        test_churchill_chu_canonical_formula_regression(),
        test_beta_ideal_gas_regression(),
        test_textbook_sanity_check_table_a15(),
        test_regression_case_old_1_57_window(),
        test_continuity_around_old_thresholds(),
        test_real_route_natural_placa_vertical(),
        test_beta_agua_tabela(),
        test_beta_oleo_constante(),
        test_beta_mercurio_constante(),
        test_beta_nao_e_mais_1_sobre_T_para_liquidos(),
        test_resultado_agua_antes_depois(),
        test_resultado_oleo_antes_depois(),
        test_resultado_mercurio_antes_depois(),
        test_real_route_liquidos(),
    ]
    print("\n=== RESUMO ===")
    print(f"TESTS_PASSED = {sum(results)}")
    print(f"TESTS_FAILED = {len(results) - sum(results)}")
    if FAILURES:
        print("Falhas:", ", ".join(FAILURES))
    sys.exit(0 if all(results) else 1)
