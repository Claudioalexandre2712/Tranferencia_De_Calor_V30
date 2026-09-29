# V30 · Laboratório de Transferência de Calor

Calculadoras de engenharia térmica (aletas, convecção natural e forçada, condensação,
ebulição, arranjos de tubos, escoamento interno e circuito térmico) feitas em Flask, e um
painel que mostra em tempo real as temperaturas de uma bancada com dois ESP32.

Site publicado: <https://tranferencia-de-calor-v30.vercel.app/>

## Rodar no computador

```powershell
py -m pip install -r requirements.txt
py app.py
```

O site abre em <http://localhost:5000>. Para ver o erro completo (traceback) na tela
enquanto desenvolve, rode com `$env:FLASK_DEBUG="1"; py app.py`. Sem essa variável o
depurador fica desligado, porque com `host=0.0.0.0` ele ficaria acessível na rede.

## Publicar

### Vercel (recomendado)

1. Em <https://vercel.com/new>, clique em **Import Git Repository**.
2. Quando a Vercel pedir acesso ao GitHub, escolha **Only select repositories** e marque
   só `Tranferencia_De_Calor_V30`. Assim ela não enxerga seus outros repositórios.
   Para conferir depois: GitHub → Settings → Applications → Vercel → Configure.
3. Não mude nada no build: o `vercel.json` já diz como rodar o `app.py`.
4. Em **Settings → Environment Variables**, crie:
   - `FLASK_SECRET_KEY`: uma chave aleatória. Gere com
     `py -c "import secrets; print(secrets.token_hex(32))"`. Sem ela o site funciona, mas
     cada servidor usa uma chave diferente e mensagens de aviso podem se perder.
   - `SITE_URL` (opcional): o endereço público, se você usar um domínio próprio. O padrão é
     `https://tranferencia-de-calor-v30.vercel.app`, e ele é usado na prévia do link.
5. Cada push no branch `main` publica sozinho.

### GitHub Pages

O GitHub Pages só serve arquivos estáticos (HTML, CSS, JS prontos). Este projeto calcula
tudo no servidor em Python, então **as calculadoras não funcionam no GitHub Pages**. Use a
Vercel. Se um dia quiser uma página de apresentação estática no Pages (em
`https://claudioalexandre2712.github.io/...`), ela precisa ser um HTML separado que só
aponte para o site da Vercel. Depois é só ativar em Settings → Pages → *Deploy from a
branch*.

## Segurança do site (em linguagem simples)

### Content-Security-Policy (CSP)

É uma lista, enviada pelo servidor a cada página, que diz ao navegador **de onde** ele pode
carregar código. Se alguém conseguir colocar um `<script>` malicioso na página (por
exemplo, num link com parâmetros forjados), o navegador se recusa a rodar.

A CSP é montada em `app.py` (função `add_security_headers`):

| Regra | O que faz |
|---|---|
| `default-src 'none'` | Começa proibindo tudo; só passa o que está liberado abaixo. |
| `script-src 'self' 'nonce-…' + CDNs` | Só rodam scripts do próprio site, dos CDNs listados e os `<script>` que têm o *nonce* (código aleatório novo a cada acesso). |
| `style-src 'self' 'unsafe-inline' + CDNs` | CSS do site, do Bootstrap, Font Awesome e Google Fonts. |
| `font-src`, `img-src`, `connect-src 'self'` | Fontes dos CDNs; imagens e chamadas `fetch` só do próprio site. |
| `base-uri 'none'`, `object-src 'none'` | Impede trocar a base dos links e embutir plugins. |
| `form-action 'self'` | Formulários só enviam dados para o próprio site. |
| `frame-ancestors 'none'` | Nenhum outro site pode abrir este dentro de um `<iframe>` (evita *clickjacking*). |

Os CDNs liberados ficam nas constantes `CSP_SCRIPT_CDNS`, `CSP_STYLE_CDNS` e
`CSP_FONT_CDNS` no começo do `app.py`. Se uma página passar a usar outra biblioteca
externa, acrescente **só aquele domínio** na constante certa.

### Regras para editar os templates

A CSP usa *nonce*, não hash, então **não há hash para recalcular** quando você edita um
`<script>`. Só três regras:

1. Todo `<script>` precisa de `nonce="{{ csp_nonce }}"`:
   `<script nonce="{{ csp_nonce }}"> ... </script>`.
2. Não use `onclick="..."`, `onchange="..."` etc.: o navegador bloqueia. Use o mesmo texto
   com `data-` na frente: `data-onclick="minhaFuncao(1, 'texto')"`. Quem liga isso ao clique
   é `static/js/csp-handlers.js`, que aceita chamadas de função com argumentos simples
   (números, textos, `this`, `this.value`, `event`), `event.stopPropagation()` e
   `return false`.
3. Efeitos de hover vão no CSS (`:hover`), não em `onmouseover`.

Para conferir tudo de uma vez (rode na pasta do projeto):

```powershell
py -c "import re,glob; ruins=[(f,m.group(0)) for f in glob.glob('templates/*.html') for m in re.finditer(r'(?m)^\s*<script(?![^>]*nonce=)[^>]*>|\son[a-z]+\s*=\s*[\x22\x27]', open(f,encoding='utf-8').read())]; print('\n'.join(f'{f}: {t}' for f,t in ruins) or 'OK: todos os <script> têm nonce e não há onclick/onchange inline')"
```

### Outros cabeçalhos (no `vercel.json`)

| Cabeçalho | Para que serve |
|---|---|
| `X-Frame-Options: DENY` | Mesmo papel do `frame-ancestors`, para navegadores antigos. |
| `X-Content-Type-Options: nosniff` | O navegador não "adivinha" o tipo do arquivo; um `.txt` nunca vira script. |
| `Referrer-Policy: no-referrer` | Ao clicar num link externo, o outro site não fica sabendo de qual página você veio. |
| `Permissions-Policy` | Desliga câmera, microfone, localização, pagamento e USB, que o site não usa. |
| `Cross-Origin-Opener-Policy: same-origin` | Isola a aba do site de janelas abertas por outros sites. |
| `Strict-Transport-Security` | Depois da primeira visita, o navegador só acessa o site por HTTPS, por 2 anos. |

Rodando localmente (`py app.py`), o próprio Flask envia esses cabeçalhos, menos o HSTS, que
só faz sentido com HTTPS.

### Sensores no site público

Na Vercel (variável `VERCEL=1`, definida por ela automaticamente) as rotas que **gravam**
dados (`POST /api/temperaturas`, `/api/monitoramento`, `/api/temperatura-alvo`) respondem
`403`, para que ninguém de fora injete leituras falsas. No laboratório, com `py app.py`,
tudo continua funcionando como antes.

### Wi-Fi do firmware

O nome e a senha do Wi-Fi não ficam mais nos `.ino`. Em cada pasta de firmware
(`esp32_painel_status/` e `esp32_monitor_ambiente/`):

1. copie `secrets.example.h` para `secrets.h`;
2. preencha `WIFI_SSID` e `WIFI_PASSWORD`.

O `secrets.h` está no `.gitignore` e nunca vai para o GitHub.

## Prévia do link (LinkedIn, WhatsApp)

As tags `og:*` ficam em `templates/_meta.html` e a imagem em `static/og.png`
(1200×630). O LinkedIn guarda a prévia em cache por uns 7 dias. Depois de mudar a imagem
ou o texto:

1. publique a mudança (push no `main`);
2. abra <https://www.linkedin.com/post-inspector/>, cole
   `https://tranferencia-de-calor-v30.vercel.app/` e clique em **Inspect**. Isso força o
   LinkedIn a ler a página de novo;
3. se a imagem antiga continuar, troque o nome do arquivo (por exemplo `og-v2.png`) e
   atualize o `og:image` em `templates/_meta.html`.

No WhatsApp o cache é do próprio aplicativo; mandar o link com `?v=2` no final força uma
prévia nova.

## Onde fica cada coisa

- `app.py`: rotas Flask, CSP e cabeçalhos de segurança.
- Módulos de cálculo: `modelo3.py`, `conveccao_calculadora.py`,
  `mudanca_fase_calculadora.py`, `arranjos_tubos_calculadora.py`, `escoamento_dutos.py`.
- `templates/`: páginas; `templates/_meta.html` é incluído em todas.
- `static/js/csp-handlers.js`: liga os `data-onclick` aos cliques sem precisar de `eval`.
- Firmware: `esp32_painel_status/` (ESP32 #01, T1-T4) e `esp32_monitor_ambiente/`
  (ESP32 #02, T5-T6). Os nomes das pastas são historicamente trocados; ver
  `docs/code-map/KNOWN_ISSUES.md`.
- Documentação técnica: `docs/code-map/INDEX.md`.
