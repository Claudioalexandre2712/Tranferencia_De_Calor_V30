"""
Teste do checkpoint V30-ENG-03B (FASE 03, achado C.11b).

Escopo: propagacao do helper obter_beta_expansao_termica() (criado em C.11, V30-ENG-03)
para conveccao_natural_placa_horizontal, conveccao_natural_esfera e
conveccao_natural_cilindro_horizontal - SOMENTE o calculo de beta nessas 3 funcoes.

NAO cobre C.1/Hilpert, C.4/Hausen, C.6/Zukauskas. NAO corrige C.3 (fator x1.57 do
cilindro horizontal) - ha um teste abaixo que confirma DELIBERADAMENTE que o x1.57
continua presente (guarda contra correcao acidental fora de escopo).

Sem pytest instalado - script standalone, roda com
`py tests/test_conveccao_natural_outras_geometrias.py`. Sai com codigo 0/1.
"""
import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conveccao_calculadora import (
    conveccao_natural_placa_horizontal,
    conveccao_natural_esfera,
    conveccao_natural_cilindro_horizontal,
    obter_beta_expansao_termica,
)

FAILURES = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    if not condition:
        FAILURES.append(name)
    return condition


def churchill_chu_nu(Ra, Pr, C1=0.825, C2=0.387, expoente=1/6, D1=0.492, D2=9/16, D3=8/27):
    return (C1 + (C2 * Ra ** expoente) / (1 + (D1 / Pr) ** D2) ** D3) ** 2


# Casos usados nesta rodada (mesmos ja usados em V30-ENG-03 para os liquidos, onde aplicavel)
CASOS_AR = {
    'placa_horizontal': dict(fn=conveccao_natural_placa_horizontal,
                              kwargs=dict(Lc=0.2, T_s=80.0, T_inf=25.0, orientacao='superior', fluido='ar')),
    'esfera': dict(fn=conveccao_natural_esfera, kwargs=dict(D=0.1, T_s=80.0, T_inf=25.0, fluido='ar')),
    'cilindro_horizontal': dict(fn=conveccao_natural_cilindro_horizontal,
                                 kwargs=dict(D=0.1, T_s=80.0, T_inf=25.0, fluido='ar')),
}

# Valores AR "antes" capturados via git stash nesta sessao (codigo pre-patch, execucao real) -
# usados so como regressao numerica fixa (nao reexecutam o codigo antigo a cada rodada de teste).
AR_ANTES = {
    'placa_horizontal': dict(beta=3.0707815139e-03, Nu=45.883253, h=6.420860),
    'esfera': dict(beta=3.0707815139e-03, Nu=21.764610, h=6.091439),
    'cilindro_horizontal': dict(beta=3.0707815139e-03, Nu=32.832634, h=9.189138),
}

CASOS_LIQUIDOS = {
    'placa_horizontal': dict(fn=conveccao_natural_placa_horizontal, kwarg_base=dict(Lc=0.2, orientacao='superior')),
    'esfera': dict(fn=conveccao_natural_esfera, kwarg_base=dict(D=0.1)),
    'cilindro_horizontal': dict(fn=conveccao_natural_cilindro_horizontal, kwarg_base=dict(D=0.1)),
}
# (T_s, T_inf) por fluido - mesmas faixas validas usadas em V30-ENG-03
TEMPS_LIQUIDO = {
    'agua': (40.0, 20.0),
    'oleo': (80.0, 20.0),
    'mercurio': (40.0, 20.0),
}


def test_beta_usa_helper_centralizado():
    """Para AR e para os 3 liquidos, em cada uma das 3 geometrias, o beta retornado
    deve ser EXATAMENTE o que obter_beta_expansao_termica() calcularia (prova que a
    funcao nao calcula beta por conta propria em nenhum caso)."""
    print("\n=== BETA_USA_HELPER_CENTRALIZADO (as 3 geometrias, ar+3 liquidos) ===")
    all_ok = True
    for geom, cfg in CASOS_LIQUIDOS.items():
        for fluido in ['ar', 'agua', 'oleo', 'mercurio']:
            if fluido == 'ar':
                T_s, T_inf = 80.0, 25.0
            else:
                T_s, T_inf = TEMPS_LIQUIDO[fluido]
            kwargs = dict(cfg['kwarg_base'], T_s=T_s, T_inf=T_inf, fluido=fluido)
            r = cfg['fn'](**kwargs)
            T_filme = (T_s + T_inf) / 2 + 273.15
            beta_esperado = obter_beta_expansao_termica(fluido, T_filme)
            ok = check(f"{geom}/{fluido}: beta == obter_beta_expansao_termica()",
                       math.isclose(r['beta'], beta_esperado, rel_tol=1e-12),
                       f"beta_funcao={r['beta']:.8e}  beta_helper={beta_esperado:.8e}")
            all_ok = all_ok and ok
    return all_ok


def test_regressao_ar_zero_mudanca():
    """AR_*_NUMERICAL_CHANGE - Ra/Nu/h do ar devem ficar numericamente identicos ao
    comportamento pre-patch (beta=1/T_filme), pois obter_beta_expansao_termica('ar',...)
    retorna exatamente 1/T_filme."""
    print("\n=== REGRESSAO_AR_ZERO_MUDANCA (comparado a execucao real pre-patch) ===")
    all_ok = True
    for geom, cfg in CASOS_AR.items():
        r = cfg['fn'](**cfg['kwargs'])
        antes = AR_ANTES[geom]
        # tol 1e-6: os valores "antes" foram capturados como literais decimais truncados
        # (%.10e) no momento do git stash, nao com precisao total de float64 - a tolerancia
        # aqui e sobre esse truncamento de captura, nao sobre a comparacao numerica real.
        ok1 = check(f"{geom}: beta(ar) identico ao pre-patch", math.isclose(r['beta'], antes['beta'], rel_tol=1e-6))
        ok2 = check(f"{geom}: Nu(ar) identico ao pre-patch", math.isclose(r['Nu'], antes['Nu'], rel_tol=1e-6))
        ok3 = check(f"{geom}: h(ar) identico ao pre-patch", math.isclose(r['h'], antes['h'], rel_tol=1e-6))
        print(f"  {geom}: beta={r['beta']:.6e}  Nu={r['Nu']:.6f}  h={r['h']:.6f}")
        all_ok = all_ok and ok1 and ok2 and ok3
    return all_ok


def test_liquidos_nao_usam_mais_1_sobre_T():
    """C.11b - regressao central: para as 3 geometrias e os 3 liquidos, beta nunca mais
    deve ser 1/T_filme (o bug antigo que C.11 corrigiu em placa_vertical e agora se
    confirma corrigido aqui tambem)."""
    print("\n=== LIQUIDOS_NAO_USAM_1_SOBRE_T (as 3 geometrias) ===")
    all_ok = True
    for geom, cfg in CASOS_LIQUIDOS.items():
        for fluido, (T_s, T_inf) in TEMPS_LIQUIDO.items():
            kwargs = dict(cfg['kwarg_base'], T_s=T_s, T_inf=T_inf, fluido=fluido)
            r = cfg['fn'](**kwargs)
            T_filme = (T_s + T_inf) / 2 + 273.15
            beta_antigo = 1 / T_filme
            ok = check(f"{geom}/{fluido}: beta != 1/T_filme",
                       not math.isclose(r['beta'], beta_antigo, rel_tol=1e-2),
                       f"beta={r['beta']:.4e}  1/T_filme={beta_antigo:.4e}")
            all_ok = all_ok and ok
    return all_ok


def test_c3_permanece_pendente():
    """Guarda de escopo: confirma que o fator x1.57 (C.3, cilindro horizontal) NAO foi
    tocado neste checkpoint - Nu ainda deve ser 1.57x o valor puro de Churchill-Chu."""
    print("\n=== C3_STATUS_GUARD (x1.57 deve continuar presente - C.3 = PENDING) ===")
    D, T_s, T_inf, fluido = 0.1, 80.0, 25.0, 'ar'
    r = conveccao_natural_cilindro_horizontal(D=D, T_s=T_s, T_inf=T_inf, fluido=fluido)
    Nu_puro = churchill_chu_nu(r['Ra'], r['Pr'], C1=0.60, C2=0.387, D1=0.559)
    ok = check("Nu ainda == 1.57 x Churchill-Chu puro (C.3 intencionalmente NAO corrigido)",
               math.isclose(r['Nu'], Nu_puro * 1.57, rel_tol=1e-9),
               f"Nu_codigo={r['Nu']:.4f}  Nu_puro*1.57={Nu_puro*1.57:.4f}")
    return ok


def test_real_route_outras_geometrias():
    """REGRESSAO FUNCIONAL - rotas reais para placa_horizontal, esfera e
    cilindro_horizontal, via Flask test_client, ar + 3 liquidos onde aplicavel."""
    print("\n=== REAL_ROUTE_TEST (placa_horizontal, esfera, cilindro_horizontal) ===")
    try:
        import app as flask_app
    except Exception as e:
        return check("Rotas reais: import de app.py sem erro", False, f"erro ao importar app.py: {e}")

    client = flask_app.app.test_client()
    all_ok = True

    payloads = {
        'esfera': lambda fluido, T_s, T_inf: dict(geometria='esfera', fluido=fluido,
                                                    temperatura_superficie=T_s, temperatura_fluido=T_inf, diametro=0.1),
        'cilindro_horizontal': lambda fluido, T_s, T_inf: dict(geometria='cilindro_horizontal', fluido=fluido,
                                                                 temperatura_superficie=T_s, temperatura_fluido=T_inf, diametro=0.1),
        'placa_horizontal': lambda fluido, T_s, T_inf: dict(geometria='placa_horizontal', fluido=fluido,
                                                              temperatura_superficie=T_s, temperatura_fluido=T_inf,
                                                              comprimento_placa=0.37, largura_placa=0.17, orientacao='superior'),
    }

    for geom, make_payload in payloads.items():
        for fluido in ['ar', 'agua', 'oleo', 'mercurio']:
            T_s, T_inf = (80.0, 25.0) if fluido == 'ar' else TEMPS_LIQUIDO[fluido]
            resp = client.post('/calculadora_convectivo/natural/calcular', json=make_payload(fluido, T_s, T_inf))
            ok1 = check(f"{geom}/{fluido}: HTTP 200", resp.status_code == 200, f"status={resp.status_code}")
            data = resp.get_json(silent=True) or {}
            ok2 = check(f"{geom}/{fluido}: sem 'erro'", 'erro' not in data, f"data={data}")
            vals = [data.get('rayleigh'), data.get('nusselt'), data.get('coef_convectivo')]
            ok3 = check(f"{geom}/{fluido}: Ra/Nu/h finitos",
                        all(isinstance(v, (int, float)) and math.isfinite(v) for v in vals),
                        f"rayleigh={data.get('rayleigh')} nusselt={data.get('nusselt')} coef_convectivo={data.get('coef_convectivo')}")
            all_ok = all_ok and ok1 and ok2 and ok3
    return all_ok


if __name__ == '__main__':
    results = [
        test_beta_usa_helper_centralizado(),
        test_regressao_ar_zero_mudanca(),
        test_liquidos_nao_usam_mais_1_sobre_T(),
        test_c3_permanece_pendente(),
        test_real_route_outras_geometrias(),
    ]
    print("\n=== RESUMO ===")
    print(f"TESTS_PASSED = {sum(results)}")
    print(f"TESTS_FAILED = {len(results) - sum(results)}")
    if FAILURES:
        print("Falhas:", ", ".join(FAILURES))
    sys.exit(0 if all(results) else 1)
