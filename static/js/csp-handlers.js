/*
 * csp-handlers.js
 *
 * A Content-Security-Policy do site bloqueia atributos como onclick="...".
 * Por isso os templates usam data-onclick / data-onchange / data-oninput /
 * data-onsubmit / data-onkeydown, e este arquivo liga esses atributos a
 * eventos reais, SEM eval e sem new Function.
 *
 * Forma aceita no atributo (instruções separadas por ";"):
 *   funcao(arg1, arg2)            chama uma função global da página
 *   window.funcao(...)            idem
 *   event.stopPropagation()       event.preventDefault()
 *   return false                  cancela a ação padrão
 *   return funcao(...)            cancela se a função devolver false (onsubmit)
 *   try{ funcao(...) }catch{}     ignora erro dessa chamada
 * Argumentos: números, 'texto', "texto", true, false, null, undefined,
 * this, this.value, this.checked, event, this.dataset.x, Number(this.dataset.x).
 *
 * Por segurança só chama funções definidas pelas páginas; funções nativas do
 * navegador (eval, setTimeout, fetch, ...) são recusadas.
 */
(function () {
  'use strict';

  var EVENTOS = ['click', 'change', 'input', 'submit', 'keydown'];
  var SELETOR = EVENTOS.map(function (t) { return '[data-on' + t + ']'; }).join(',');
  var cache = Object.create(null);

  // Divide o texto no separador, ignorando o que está entre aspas, () ou {}.
  function dividir(src, sep) {
    var partes = [], atual = '', nivel = 0, aspas = null;
    for (var i = 0; i < src.length; i++) {
      var c = src[i];
      if (aspas) {
        atual += c;
        if (c === '\\' && i + 1 < src.length) { atual += src[++i]; continue; }
        if (c === aspas) aspas = null;
        continue;
      }
      if (c === '"' || c === "'") { aspas = c; atual += c; continue; }
      if (c === '(' || c === '{' || c === '[') nivel++;
      if (c === ')' || c === '}' || c === ']') nivel--;
      if (c === sep && nivel === 0) { partes.push(atual); atual = ''; continue; }
      atual += c;
    }
    partes.push(atual);
    return partes.map(function (p) { return p.trim(); }).filter(function (p) { return p.length > 0; });
  }

  function erro(msg, codigo) {
    return new Error('[csp-handlers] ' + msg + ': ' + codigo);
  }

  function lerArgumento(tok) {
    var m;
    if (/^-?(\d+\.?\d*|\.\d+)(e[+-]?\d+)?$/i.test(tok)) { var n = Number(tok); return function () { return n; }; }
    if ((m = /^'((?:[^'\\]|\\.)*)'$/.exec(tok)) || (m = /^"((?:[^"\\]|\\.)*)"$/.exec(tok))) {
      var texto = m[1].replace(/\\(.)/g, '$1');
      return function () { return texto; };
    }
    if (tok === 'true') return function () { return true; };
    if (tok === 'false') return function () { return false; };
    if (tok === 'null') return function () { return null; };
    if (tok === 'undefined' || tok === 'NaN') { var v = tok === 'NaN' ? NaN : undefined; return function () { return v; }; }
    if (tok === 'this') return function (el) { return el; };
    if (tok === 'event') return function (el, ev) { return ev; };
    if (tok === 'this.value') return function (el) { return el.value; };
    if (tok === 'this.checked') return function (el) { return el.checked; };
    if ((m = /^this\.dataset\.([A-Za-z_]\w*)$/.exec(tok))) { var k1 = m[1]; return function (el) { return el.dataset[k1]; }; }
    if ((m = /^Number\(this\.dataset\.([A-Za-z_]\w*)\)$/.exec(tok))) { var k2 = m[1]; return function (el) { return Number(el.dataset[k2]); }; }
    throw erro('argumento não suportado', tok);
  }

  function lerChamada(stmt) {
    var m = /^(?:window\.)?([A-Za-z_$][\w$]*)\s*\(([\s\S]*)\)$/.exec(stmt);
    if (!m) return null;
    return { nome: m[1], args: dividir(m[2], ',').map(lerArgumento) };
  }

  function lerInstrucao(stmt) {
    var m;
    if (stmt === 'event.stopPropagation()') return { tipo: 'stop' };
    if (stmt === 'event.preventDefault()') return { tipo: 'prevent' };
    if (stmt === 'return false') return { tipo: 'retornaFalso' };
    if ((m = /^try\s*\{([\s\S]*)\}\s*catch\s*(\(\s*\w*\s*\))?\s*\{\s*\}$/.exec(stmt))) {
      return { tipo: 'try', corpo: compilar(m[1]) };
    }
    if ((m = /^return\s+([\s\S]+)$/.exec(stmt))) {
      var ch = lerChamada(m[1]);
      if (ch) return { tipo: 'retornaChamada', chamada: ch };
    }
    var chamada = lerChamada(stmt);
    if (chamada) return { tipo: 'chamada', chamada: chamada };
    throw erro('instrução não suportada', stmt);
  }

  function compilar(codigo) {
    return dividir(codigo, ';').map(lerInstrucao);
  }

  function obter(codigo) {
    if (!(codigo in cache)) cache[codigo] = compilar(codigo);
    return cache[codigo];
  }

  function funcaoDaPagina(nome) {
    var fn = window[nome];
    if (typeof fn !== 'function') return null;
    if (/\[native code\]/.test(Function.prototype.toString.call(fn))) {
      throw erro('função nativa recusada', nome);
    }
    return fn;
  }

  function chamar(ch, el, ev) {
    var fn = funcaoDaPagina(ch.nome);
    if (!fn) { console.debug('[csp-handlers] função não definida:', ch.nome); return undefined; }
    return fn.apply(undefined, ch.args.map(function (a) { return a(el, ev); }));
  }

  function executar(instrucoes, el, ev) {
    for (var i = 0; i < instrucoes.length; i++) {
      var ins = instrucoes[i];
      switch (ins.tipo) {
        case 'stop': ev.stopPropagation(); break;
        case 'prevent': ev.preventDefault(); break;
        case 'retornaFalso': ev.preventDefault(); return;
        case 'try': try { executar(ins.corpo, el, ev); } catch (e) { /* ignorado, como no original */ } break;
        case 'retornaChamada': if (chamar(ins.chamada, el, ev) === false) ev.preventDefault(); return;
        default: chamar(ins.chamada, el, ev);
      }
    }
  }

  function tratar(ev) {
    var codigo = this.getAttribute('data-on' + ev.type);
    if (!codigo) return;
    executar(obter(codigo), this, ev);
  }

  function ligar(el) {
    for (var i = 0; i < EVENTOS.length; i++) {
      var tipo = EVENTOS[i], marca = '__cspOn' + tipo;
      if (el.hasAttribute('data-on' + tipo) && !el[marca]) {
        el[marca] = true;
        el.addEventListener(tipo, tratar);
      }
    }
  }

  function ligarArvore(raiz) {
    if (raiz.nodeType !== 1) return;
    ligar(raiz);
    var lista = raiz.querySelectorAll(SELETOR);
    for (var i = 0; i < lista.length; i++) ligar(lista[i]);
  }

  // Liga elementos já existentes e os que forem criados depois (innerHTML, appendChild...).
  new MutationObserver(function (mutacoes) {
    for (var i = 0; i < mutacoes.length; i++) {
      var m = mutacoes[i];
      if (m.type === 'attributes') { ligar(m.target); continue; }
      for (var j = 0; j < m.addedNodes.length; j++) ligarArvore(m.addedNodes[j]);
    }
  }).observe(document.documentElement, {
    childList: true, subtree: true, attributes: true,
    attributeFilter: EVENTOS.map(function (t) { return 'data-on' + t; })
  });
  ligarArvore(document.documentElement);
  document.addEventListener('DOMContentLoaded', function () { ligarArvore(document.documentElement); });

  // Pequenos atalhos para o que antes era código solto dentro de onclick.
  window.alternarVisibilidade = function (id) {
    var el = document.getElementById(id);
    if (el) el.hidden = !el.hidden;
  };
  window.rolarAte = function (id) {
    var el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };
  window.imprimirPagina = function () { window.print(); };
  window.irPara = function (url) {
    if (typeof url === 'string' && url.charAt(0) === '/' && url.charAt(1) !== '/') window.location.href = url;
  };
})();
