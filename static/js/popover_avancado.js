(function(){
 if(window.__ADV_POPOVER_INSTALLED__) return; // evitar dupla
 window.__ADV_POPOVER_INSTALLED__ = true;
 let installingLogPrefix = '[PopoverAvancado]';
 function destroyCurrent(){
  if(window.currentPopover){
    try{ window.currentPopover.remove(); }catch{}
    window.currentPopover=null;
  }
  // Remover painel lateral de imagem, se existir
  try {
    const side = document.getElementById('side-image-popover');
    if (side) side.remove();
  } catch {}
 }

 function renderFinnedMetrics(pop, layer) {
   const metricsBox = pop.querySelector('#fin-metrics');
   if(!metricsBox) return;
   
   const finType = layer.fin_type || 'rectangular';
   const isRectangular = finType === 'rectangular';
   const N = layer.N_fins || 1;
   const h = layer.convection || 100;
   const k = layer.conductivity || 200;
   const L = layer.fin_length || 0.02;
   const A_base = layer.A_base || 1.0;
   const useTipCorrection = layer.use_tip_correction || false;
   
   let geometryCalcs, parameterCalcs, surfaceCalcs;
   let eta_f, A_f, A_b, A_t, eta_o, R_aletada;
   
   if (isRectangular) {
     const w = layer.fin_width || 0.02;
     const t = layer.fin_thickness || 0.002;
     const P = 2*(w+t);
     const A_c = w*t;
     const m = Math.sqrt((h*P)/(k*A_c));
     const L_c = useTipCorrection ? L + t/2 : L;
     const mL = m * L_c;
     eta_f = Math.tanh(mL) / mL;
     
     // Área das aletas
     A_f = N * (2*w*L + 2*t*L + (useTipCorrection ? w*t : 0));
     A_b = A_base - N*w*t;
     A_t = A_b + A_f;
     eta_o = 1 - (A_f/A_t)*(1-eta_f);
     R_aletada = 1/(eta_o*h*A_t);
     
     geometryCalcs = `P = 2(w + t) = 2(${w.toFixed(4)}+${t.toFixed(4)}) = ${P.toFixed(4)} m<br>
A_c = w·t = ${w.toFixed(4)}·${t.toFixed(4)} = ${A_c.toExponential(3)} m²`;
     
     parameterCalcs = `m = √(h·P/(k·A_c)) = √(${h.toFixed(3)}·${P.toFixed(4)}/(${k.toFixed(3)}·${A_c.toExponential(3)})) = ${m.toFixed(4)} 1/m<br>
${useTipCorrection ? `L_c = L + t/2 ≈ ${L_c.toFixed(4)} m<br>` : ''}
m L${useTipCorrection?'_c':''} = ${mL.toFixed(4)} ⇒ η_f = tanh(m L${useTipCorrection?'_c':''})/(m L${useTipCorrection?'_c':''}) = ${eta_f.toFixed(3)}`;
     
     surfaceCalcs = `A_f ≈ N·(2·w·L + 2·t·L${useTipCorrection ? ' + w·t[ponta]' : ''}) = ${A_f.toExponential(3)} m²<br>
A_b = A_base − N·w·t = ${A_b.toExponential(3)} m²<br>
A_t = A_b + A_f = ${A_t.toExponential(3)} m²<br>
η₀ = 1 − (A_f/A_t)(1−η_f) = ${eta_o.toFixed(3)}<br>
R_aletada = 1/(η₀·h·A_t) = ${R_aletada.toExponential(3)} K/W`;
   } else {
     const D = layer.fin_diameter || 0.005;
     const A_c = Math.PI*D*D/4;
     const P = Math.PI*D;
     const m = Math.sqrt((4*h)/(k*D));
     const L_c = useTipCorrection ? L + D/4 : L;
     const mL = m * L_c;
     eta_f = Math.tanh(mL) / mL;
     
     // Área das aletas cilíndricas
     const A_aleta = Math.PI*D*L_c;
     A_f = N * A_aleta;
     A_b = A_base - N*(Math.PI*D*D/4);
     A_t = A_b + A_f;
     eta_o = 1 - (A_f/A_t)*(1-eta_f);
     R_aletada = 1/(eta_o*h*A_t);
     
     geometryCalcs = `A_c = πD²/4 = π(${D.toFixed(4)})²/4 = ${A_c.toExponential(3)} m²<br>
P = πD = π(${D.toFixed(4)}) = ${P.toFixed(4)} m<br>
A_aleta = P·L${useTipCorrection?'_c':''} = ${P.toFixed(4)}·${L_c.toFixed(4)} = ${A_aleta.toExponential(3)} m²`;
     
     parameterCalcs = `m = √(4h/(kD)) = √(4·${h.toFixed(3)}/(${k.toFixed(3)}·${D.toFixed(4)})) = ${m.toFixed(4)} 1/m<br>
${useTipCorrection ? `L_c = L + D/4 ≈ ${L_c.toFixed(4)} m<br>` : ''}
m L${useTipCorrection?'_c':''} = ${mL.toFixed(4)} ⇒ η_f = tanh(m L${useTipCorrection?'_c':''})/(m L${useTipCorrection?'_c':''}) = ${eta_f.toFixed(3)}`;
     
     surfaceCalcs = `A_a = N·A_aleta = ${N}·${A_aleta.toExponential(3)} = ${A_f.toExponential(3)} m²<br>
A_b = A_base − N·(πD²/4) = ${A_b.toExponential(3)} m²<br>
A_t = A_b + A_a = ${A_t.toExponential(3)} m²<br>
η₀ = 1 − (A_a/A_t)(1−η_f) = ${eta_o.toFixed(3)}<br>
R_total_eq = 1/(η₀·h·A_t) = ${R_aletada.toExponential(3)} K/W`;
   }
   
   metricsBox.innerHTML = `<strong>Etapa 1: Aleta ${isRectangular ? 'Retangular (Placa)' : 'Cilíndrica (Pino)'}</strong><br>
${geometryCalcs}<br>
${parameterCalcs}<br><br>
<strong>Etapa 2: Superfície Aletada (Conjunto de ${isRectangular ? 'Placas' : 'Pinos'})</strong><br>
${surfaceCalcs}<br><br>
<div style='background:#c8e6c9; padding:8px; border-radius:6px; margin-top:8px;'>
<strong>Resultados:</strong><br>
η_f ${eta_f.toFixed(3)}<br>
η_o ${eta_o.toFixed(3)}<br>
R_aletada ${R_aletada.toExponential(3)} K/W<br>
A_t ${A_t.toExponential(3)} m²<br>
A_f ${A_f.toExponential(3)} m²<br>
A_b ${A_b.toExponential(3)} m²<br>
${isRectangular ? 
  `P ${(2*((layer.fin_width||0.02)+(layer.fin_thickness||0.002))).toFixed(4)} m<br>A_c ${((layer.fin_width||0.02)*(layer.fin_thickness||0.002)).toExponential(3)} m²<br>` : 
  `A_c ${(Math.PI*(layer.fin_diameter||0.005)*(layer.fin_diameter||0.005)/4).toExponential(3)} m²<br>P ${(Math.PI*(layer.fin_diameter||0.005)).toFixed(4)} m<br>`
}m ${isRectangular ? Math.sqrt((h*2*((layer.fin_width||0.02)+(layer.fin_thickness||0.002)))/(k*(layer.fin_width||0.02)*(layer.fin_thickness||0.002))).toFixed(4) : Math.sqrt((4*h)/(k*(layer.fin_diameter||0.005))).toFixed(4)}<br>
mL ${(isRectangular ? Math.sqrt((h*2*((layer.fin_width||0.02)+(layer.fin_thickness||0.002)))/(k*(layer.fin_width||0.02)*(layer.fin_thickness||0.002))) * (useTipCorrection ? L + (layer.fin_thickness||0.002)/2 : L) : Math.sqrt((4*h)/(k*(layer.fin_diameter||0.005))) * (useTipCorrection ? L + (layer.fin_diameter||0.005)/4 : L)).toFixed(4)}
</div>`;
 }

 function createFinnedContent(layer) {
   const finType = layer.fin_type || 'rectangular'; // 'rectangular' ou 'cylindrical'
   const isRectangular = finType === 'rectangular';
   
   // Parâmetros comuns
   const N = layer.N_fins || 1;
   const h = layer.convection || 100;
   const k = layer.conductivity || 200;
   const L = layer.fin_length || 0.02;
   const A_base = layer.A_base || 1.0;
   
   // Parâmetros específicos por tipo
   let specificParams = '';
   let geometryCalcs = '';
   let parameterCalcs = '';
   
   if (isRectangular) {
     // Aleta Retangular (Placa)
     const w = layer.fin_width || 0.02;
     const t = layer.fin_thickness || 0.002;
     const useTipCorrection = layer.use_tip_correction || false;
     
     specificParams = `
       <div style='display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; margin-bottom:16px;'>
         <div><label style='font-size:.63rem;font-weight:600;'>Largura w (m)</label><input id='fin-width' type='number' step='0.001' value='${w}' style='width:100%;'></div>
         <div><label style='font-size:.63rem;font-weight:600;'>Espessura t (m)</label><input id='fin-thickness' type='number' step='0.0001' value='${t}' style='width:100%;'></div>
       </div>
       <label style='display:flex; align-items:center; gap:6px; margin-bottom:12px; font-size:.65rem; font-weight:600;'>
         <input id='fin-tip-correction' type='checkbox' ${useTipCorrection?'checked':''} style='transform:scale(1.1);'> Usar correção de ponta (L_c)
       </label>`;
     
     geometryCalcs = `
       P = 2(w + t) = 2(${w.toFixed(4)}+${t.toFixed(4)}) = ${(2*(w+t)).toFixed(4)} m<br>
       A_c = w·t = ${w.toFixed(4)}·${t.toFixed(4)} = ${(w*t).toExponential(3)} m²`;
     
     const P = 2*(w+t);
     const A_c = w*t;
     const m = Math.sqrt((h*P)/(k*A_c));
     const L_c = useTipCorrection ? L + t/2 : L;
     const mL = m * L_c;
     const eta_f = Math.tanh(mL) / mL;
     
     parameterCalcs = `
       m = √(h·P/(k·A_c)) = √(${h.toFixed(3)}·${P.toFixed(4)}/(${k.toFixed(3)}·${A_c.toExponential(3)})) = ${m.toFixed(4)} 1/m<br>
       ${useTipCorrection ? `L_c = L + t/2 ≈ ${L_c.toFixed(4)} m<br>` : ''}
       m L${useTipCorrection?'_c':''} = ${mL.toFixed(4)} ⇒ η_f = tanh(m L${useTipCorrection?'_c':''})/(m L${useTipCorrection?'_c':''}) = ${eta_f.toFixed(3)}`;
   } else {
     // Aleta Cilíndrica (Pino)
     const D = layer.fin_diameter || 0.005;
     const useTipCorrection = layer.use_tip_correction || false;
     
     specificParams = `
       <div style='display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; margin-bottom:16px;'>
         <div><label style='font-size:.63rem;font-weight:600;'>Diâmetro D (m)</label><input id='fin-diameter' type='number' step='0.0001' value='${D}' style='width:100%;'></div>
       </div>
       <label style='display:flex; align-items:center; gap:6px; margin-bottom:12px; font-size:.65rem; font-weight:600;'>
         <input id='fin-tip-correction' type='checkbox' ${useTipCorrection?'checked':''} style='transform:scale(1.1);'> Usar correção de ponta (L_c)
       </label>`;
     
     geometryCalcs = `
       A_c = πD²/4 = π(${D.toFixed(4)})²/4 = ${(Math.PI*D*D/4).toExponential(3)} m²<br>
       P = πD = π(${D.toFixed(4)}) = ${(Math.PI*D).toFixed(4)} m<br>
       A_aleta = P·L = ${(Math.PI*D).toFixed(4)}·${L.toFixed(4)} = ${(Math.PI*D*L).toExponential(3)} m²`;
     
     const A_c = Math.PI*D*D/4;
     const P = Math.PI*D;
     const m = Math.sqrt((4*h)/(k*D)); // Fórmula simplificada para cilíndrica
     const L_c = useTipCorrection ? L + D/4 : L;
     const mL = m * L_c;
     const eta_f = Math.tanh(mL) / mL;
     
     parameterCalcs = `
       m = √(4h/(kD)) = √(4·${h.toFixed(3)}/(${k.toFixed(3)}·${D.toFixed(4)})) = ${m.toFixed(4)} 1/m<br>
       ${useTipCorrection ? `L_c = L + D/4 ≈ ${L_c.toFixed(4)} m<br>` : ''}
       m L${useTipCorrection?'_c':''} = ${mL.toFixed(4)} ⇒ η_f = tanh(m L${useTipCorrection?'_c':''})/(m L${useTipCorrection?'_c':''}) = ${eta_f.toFixed(3)}`;
   }
   
   return `<div style='background:#e0f2f1; border:1px solid #80cbc4; border-radius:12px; padding:16px 18px 14px; margin-bottom:12px;'>
     <h4 style='margin:0 0 12px; font-size:.95rem; color:#1b5e20; font-weight:600;'>Superfície Aletada</h4>
     
     <div style='margin-bottom:16px;'>
       <label style='font-size:.65rem; font-weight:600; margin-bottom:8px; display:block;'>Tipo de Aleta</label>
       <div style='display:flex; gap:12px;'>
         <label style='display:flex; align-items:center; gap:6px; font-size:.65rem;'>
           <input type='radio' name='fin-type-selection' value='rectangular' ${isRectangular?'checked':''} data-prop='fin_type'> Retangular (Placa)
         </label>
         <label style='display:flex; align-items:center; gap:6px; font-size:.65rem;'>
           <input type='radio' name='fin-type-selection' value='cylindrical' ${!isRectangular?'checked':''} data-prop='fin_type'> Cilíndrica (Pino)
         </label>
       </div>
     </div>
     
     <div style='display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; margin-bottom:16px;'>
       <div><label style='font-size:.63rem;font-weight:600;'>Número de aletas N</label><input id='fin-N' type='number' step='1' min='1' value='${N}' style='width:100%;'></div>
       <div><label style='font-size:.63rem;font-weight:600;'>Comprimento L (m)</label><input id='fin-length' type='number' step='0.001' value='${L}' style='width:100%;'></div>
       <div><label style='font-size:.63rem;font-weight:600;'>h (W/m²·K)</label><input id='fin-h' type='number' step='0.1' value='${h}' style='width:100%;'></div>
       <div><label style='font-size:.63rem;font-weight:600;'>k (W/m·K)</label><input id='fin-k' type='number' step='0.1' value='${k}' style='width:100%;'></div>
       <div><label style='font-size:.63rem;font-weight:600;'>Área base (m²)</label><input id='fin-base-area' type='number' step='0.001' value='${A_base}' style='width:100%;'></div>
     </div>
     
     <div id='fin-specific-params'>${specificParams}</div>
     
     <div id='fin-metrics' style='background:#e8f5e8; border:1px solid #c8e6c9; padding:12px; border-radius:10px; font-family:monospace; font-size:.7rem; line-height:1.4;'>
       <strong>Etapa 1: Aleta ${isRectangular ? 'Retangular (Placa)' : 'Cilíndrica (Pino)'}</strong><br>
       ${geometryCalcs}<br>
       ${parameterCalcs}<br><br>
       <strong>Etapa 2: Superfície Aletada (Conjunto)</strong><br>
       Calculando...
     </div>
   </div>`;
 }
 function positionSmart(pop, evt){
  const vw=innerWidth, vh=innerHeight; const rect=(evt?.target?.getBoundingClientRect?.())||{left:vw/2, top:vh/2, bottom:vh/2};
  const pw=Math.min(640, vw-40); pop.style.maxWidth=pw+'px';
  requestAnimationFrame(()=>{
    const ph=Math.min(pop.offsetHeight||560, vh-40);
    let left=rect.left+20; if(left+pw>vw-20) left=vw-pw-20; if(left<20) left=20;
    let top=rect.bottom+12; if(top+ph>vh-20) top=rect.top-ph-12; if(top<20) top=20;
    pop.style.left=left+'px'; pop.style.top=top+'px';
  });
 }
 function badge(txt,color){ return `<span style="background:${color}; color:#fff; padding:2px 6px; border-radius:12px; font-size:.65rem; font-weight:600;">${txt}</span>`; }
 function header(layer, idx, customText){
  const isFluid=/Fluido/.test(layer.type||''); const isFinned=/SuperficieAletada/.test(layer.type||''); const isCyl=/Cilindrica/.test(layer.type||'');
  const isParallel=Array.isArray(layer.branches) && layer.branches.length > 0;
  const icon=isFinned?'🌊':(isFluid?'💨':(isCyl?'🌀':(isParallel?'∷':'🧊')));
  const mark=isFluid? badge('CONV','#0288d1'): (isFinned? badge('FIN','#00695c'): (isCyl? badge('CYL','#6a1b9a'): (isParallel? badge('PAR','#9c27b0'): badge('COND','#ef6c00'))));
  const subtitle = customText || `Camada ${idx+1}`;
  return `<div style="display:flex; gap:14px; align-items:center; margin:0 0 14px; padding:0 0 12px; border-bottom:2px solid #e3f2fd;">
   <div style="background:#1976d2; color:#fff; width:54px; height:54px; border-radius:16px; display:flex; align-items:center; justify-content:center; font-size:1.65rem; box-shadow:0 6px 18px -2px rgba(25,118,210,.4);">${icon}</div>
   <div style="flex:1; min-width:0;">
     <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
       <span style="font-weight:600; font-size:1.05rem; color:#0d47a1;">${layer.type||'Camada'}</span>${mark}
     </div>
     <div style="color:#607d8b; font-size:.7rem; letter-spacing:.5px;">${subtitle}</div>
   </div>
   <div style="display:flex; flex-direction:column; gap:6px;">
     ${idx !== -1 ? `<button id="btn-dup" title="Duplicar" style="background:#8d6e63; color:#fff; border:none; width:34px; height:34px; border-radius:10px; cursor:pointer; font-weight:600;">⧉</button>` : ''}
     <button id="pop-close-x" title="Fechar" style="background:#eceff1; border:none; width:34px; height:34px; border-radius:10px; cursor:pointer; font-weight:600; color:#455a64;">×</button>
   </div>
  </div>`;
 }
 function metricsContainers(layer){
  const isFluid=/Fluido/.test(layer.type||''); const isFinned=/SuperficieAletada/.test(layer.type||''); const isCyl=/Cilindrica/.test(layer.type||'');
  if(isFinned) return ''; if(isFluid) return `<div id="conv-metrics" style="background:#e3f2fd; border:1px solid #bbdefb; padding:10px 12px; border-radius:10px; font-family:monospace; font-size:.72rem; line-height:1.35; margin-top:10px;">—</div>`; if(isCyl) return `<div id="cyl-metrics" style="background:#ede7f6; border:1px solid #d1c4e9; padding:10px 12px; border-radius:10px; font-family:monospace; font-size:.72rem; line-height:1.35; margin-top:10px;">—</div>`; return `<div id="cond-metrics" style="background:#fff3e0; border:1px solid #ffe0b2; padding:10px 12px; border-radius:10px; font-family:monospace; font-size:.72rem; line-height:1.35; margin-top:10px;">—</div>`; }
function actionsBar(){
 const autoSaved = (()=>{ try{return JSON.parse(localStorage.getItem('thermalAutoUpdate')||'true');}catch{return true;}})();
 return `<div style="display:flex; justify-content:flex-start; align-items:center; gap:12px; margin-top:12px; flex-wrap:wrap;">
  <label style="display:flex; gap:6px; align-items:center; font-size:.7rem;"> <input id="chk-auto" type="checkbox" ${autoSaved?'checked':''} style="transform:scale(1.15);"> Atualização simultânea</label>
 </div>`;
}
function footerButtons(){ return `<div style="display:flex; gap:10px; justify-content:flex-end; margin-top:16px; flex-wrap:wrap;">
   <button class="btn-pop" data-act="return" style="background:#eceff1; color:#455a64;">Voltar</button>
   <button class="btn-pop" data-act="save" style="background:#388e3c; color:#fff;">Salvar</button>
 </div>`; }
 function buildPlanarMetrics(layer){ const A=(selectedGeometry==='planar'?(planarParams?.A||1):(layer.A||1))||1; const L=parseFloat(layer.thickness||layer.L||0); const k=parseFloat(layer.conductivity||layer.k||0); const Rc=parseFloat(layer.contact_resistance||0)||0; let Rm=(k>0&&A>0)? L/(k*A):NaN; let Rtot=isFinite(Rm)? Rm+(Rc>0?Rc:0):NaN; return {A,L,k,Rm,Rtot,Rc}; }
 function buildConvMetrics(layer){ 
   const A=(selectedGeometry==='planar'?(planarParams?.A||1):(layer.A||1))||1; 
   const h=parseFloat(layer.convection||0); 
   const eps=parseFloat(layer.emissivity||0); 
   const useRad=!!(layer.include_radiation&&eps>0); 
   const sigma=5.670374419e-8; 
   const TsurfK=(parseFloat(layer.temperature||0)+273.15); 
   const TvizK=(parseFloat(layer.T_viz||20)+273.15); 
   const h_rad=useRad ? eps*sigma*(TsurfK+TvizK)*(TsurfK*TsurfK+TvizK*TvizK) : 0; 
   const heff=h+h_rad; 
   const Rconv=(heff>0&&A>0)?1/(heff*A):NaN; 
   const Rbase=(h>0&&A>0)?1/(h*A):NaN; 
   const Rrad=useRad?(h_rad>0&&A>0?1/(h_rad*A):NaN):NaN; 
   return {A,h,eps,h_rad,heff,Rconv,Rbase,Rrad,useRad,TsurfK,TvizK}; 
 }
 function buildCylMetrics(layer){
  let r_int=parseFloat(layer.r_int||0); let r_ext=parseFloat(layer.r_ext||0);
  if(layer.use_r_override && isFinite(layer.r1_override) && isFinite(layer.r2_override) && layer.r2_override>layer.r1_override){
    r_int=parseFloat(layer.r1_override); r_ext=parseFloat(layer.r2_override);
  }
  const k=parseFloat(layer.k||layer.conductivity||0); const L=parseFloat(layer.L||1); const Rc=parseFloat(layer.contact_resistance||0)||0;
  let R_mat=(r_int>0&&r_ext>r_int&&k>0&&L>0)? Math.log(r_ext/r_int)/(2*Math.PI*k*L):NaN;
  let R_total=isFinite(R_mat)? R_mat + Rc:NaN;
  const A_int=(r_int>0&&L>0)?2*Math.PI*r_int*L:NaN; const A_ext=(r_ext>0&&L>0)?2*Math.PI*r_ext*L:NaN; const A_mid=(isFinite(r_int)&&isFinite(r_ext)&&L>0)? 2*Math.PI*((r_int+r_ext)/2)*L:NaN;
  return {r_int,r_ext,k,L,R_mat,R_total,Rc,A_int,A_ext,A_mid};
 }
 function renderMetrics(pop, layer){
  if(/SuperficieAletada/.test(layer.type||'')) return;
  if(/Fluido/.test(layer.type||'')){
    const m=buildConvMetrics(layer); const box=pop.querySelector('#conv-metrics'); if(!box) return;
    const f=n=> isFinite(n)?(Math.abs(n)<1e-3||Math.abs(n)>1e4?n.toExponential(3):n.toFixed(4)):'—';
    const fe=n=> isFinite(n)?n.toExponential(3):'—';
    if(m.useRad){
      box.innerHTML=`<strong>Convecção:</strong> R_conv = 1/(h·A) = 1/(${f(m.h)}·${f(m.A)}) = ${f(m.Rbase)} K/W<br><strong>Radiação:</strong> h_r = εσ(T_s+T_viz)(T_s²+T_viz²) = ${f(m.eps)}×${fe(5.670374419e-8)}×(${f(m.TsurfK-273.15)}+${f(m.TvizK-273.15)})×(...) = ${f(m.h_rad)} W/m²·K<br>R_rad = 1/(h_r·A) = ${f(m.Rrad)} K/W<br><strong>Combinadas:</strong> h_total = h + h_r = ${f(m.h)} + ${f(m.h_rad)} = ${f(m.heff)} W/m²·K<br><strong>R_total = 1/(h_total·A) = ${f(m.Rconv)} K/W</strong>`;
    } else {
      box.innerHTML=`R_conv = 1/(h·A) = 1/(${f(m.h)}·${f(m.A)}) = ${f(m.Rbase)} K/W<br><strong>R_total = ${f(m.Rbase)} K/W</strong>`;
    }
    return;
  }
  if(/Cilindrica/.test(layer.type||'')){
    const m=buildCylMetrics(layer); const box=pop.querySelector('#cyl-metrics'); if(!box) return;
    const f=n=> isFinite(n)?(Math.abs(n)<1e-4||Math.abs(n)>1e5?n.toExponential(3):n.toFixed(2)):'—';
    const fe=n=> isFinite(n)?n.toExponential(3):'—';
    const calculation = `R = ln(r₂/r₁)/(2πkL) + R_cont = ln(${f(m.r_ext)}/${f(m.r_int)})/(2π·${f(m.k)}·${f(m.L)}) + ${m.Rc||0} = ${fe(m.R_total)} K/W`;
    box.innerHTML=calculation;
    return;
  }
  const m=buildPlanarMetrics(layer); const box=pop.querySelector('#cond-metrics'); if(!box) return; const f=n=> isFinite(n)?(Math.abs(n)<1e-3||Math.abs(n)>1e4?n.toExponential(3):n.toFixed(5)):'—'; box.innerHTML=`R_m = L/(k·A) = ${f(m.L)}/(${f(m.k)}·${f(m.A)}) = ${f(m.Rm)} K/W<br>${m.Rc>0? `R_total = R_m + R_cont = ${f(m.Rm)} + ${f(m.Rc)} = <strong>${f(m.Rtot)}</strong> K/W`:`R_total = <strong>${f(m.Rtot)}</strong> K/W`}`;
 }

 // ===== BLOCO PARALELO (NOVO EDIÇÃO INLINE) =====
 // Agora usamos summarizeParallelBlock global para consistência
 function computeBranchResistance(branch){
   if(!Array.isArray(branch)) return NaN;
   
   let totalR = 0;
   // Cada camada no ramo contribui em série
   for(const layer of branch) {
     let layerR = 0;
     
     if(Array.isArray(layer.branches) && layer.branches.length > 0) {
       // Bloco paralelo aninhado: R_eq = 1 / (1/R1 + 1/R2 + ... + 1/RN)
       let parallelSum = 0;
       for(const subBranch of layer.branches) {
         const subBranchR = computeBranchResistance(subBranch);
         if(isFinite(subBranchR) && subBranchR > 0) {
           parallelSum += 1 / subBranchR;
         }
       }
       layerR = parallelSum > 0 ? 1 / parallelSum : Infinity;
       
     } else {
       // Camada simples - usar função global se disponível
       const tempBlock = { branches: [ [layer] ] };
       const sub = (typeof summarizeParallelBlock==='function')? summarizeParallelBlock(tempBlock): null;
       layerR = sub && sub.branches && sub.branches[0] ? sub.branches[0].R_branch : NaN;
     }
     
     if(isFinite(layerR) && layerR > 0) {
       totalR += layerR; // Resistências em série se somam
     }
   }
   
   return totalR > 0 ? totalR : NaN;
 }
 function computeParallelEquivalent(branches){
   if(typeof summarizeParallelBlock!=='function') return NaN;
   const temp = { branches: branches.slice() };
   const s = summarizeParallelBlock(temp);
   return s && isFinite(s.Req)? s.Req : NaN;
 }
 function fmtVal(v){ return isFinite(v)? (Math.abs(v)<1e-3||Math.abs(v)>1e4? v.toExponential(3): v.toFixed(5)) : 'N/A'; }
function subLayerForm(parIdx, bIdx, slIdx, sl){
  const isCylGlobal = (typeof selectedGeometry!=='undefined' && selectedGeometry==='cylindrical');
  const baseStyle="display:grid; grid-template-columns:repeat(auto-fit,minmax(110px,1fr)); gap:8px;";
  const wrap = (inner)=>`<div class='sublayer-editor' data-par='${parIdx}' data-branch='${bIdx}' data-layer='${slIdx}' style='background:#fafafa; border:1px solid #e0e0e0; border-radius:10px; padding:10px 12px; margin-bottom:8px; position:relative;'>${inner}</div>`;
   const header = ()=>{ const icon=/Fluido/.test(sl.type||'')?'💨':(/SuperficieAletada/.test(sl.type||'')?'🌊':(/Paralelo/.test(sl.type||'')?'∷':'🧊')); return `<div style='display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;'>`+
     `<div style='font-size:.75rem; font-weight:600; color:#37474f; display:flex; gap:6px; align-items:center;'>${icon} ${(sl.type||'').replace(/\s+\d+$/,'')}</div>`+
     `<div style='display:flex; gap:6px;'>`+
       `${!Array.isArray(sl.branches)? `<button data-act='edit-sublayer' data-par='${parIdx}' data-branch='${bIdx}' data-layer='${slIdx}' style='background:#6a1b9a; color:#fff; border:none; border-radius:6px; padding:4px 8px; font-size:.6rem; cursor:pointer;'>Editar</button>`:''}`+
       `<button title='Remover' data-act='del-sublayer' data-par='${parIdx}' data-branch='${bIdx}' data-layer='${slIdx}' style='background:#ef5350; color:#fff; border:none; border-radius:6px; padding:4px 8px; font-size:.65rem; cursor:pointer;'>×</button>`+
     `</div>`+
   `</div>`; };
   if(/Fluido/.test(sl.type||'')){
     const useRad = sl.include_radiation || false;
     const tviz = sl.T_viz || 20;
     return wrap(header()+`<div style='${baseStyle}'>
        <div style='display:flex; flex-direction:column; gap:3px;'><label style='font-size:.6rem;font-weight:600;'>h (W/m²·K)</label><input data-prop='convection' type='number' step='0.01' value='${sl.convection||''}'></div>
        <div style='display:flex; flex-direction:column; gap:3px;'><label style='font-size:.6rem;font-weight:600;'>T (°C)</label><input data-prop='temperature' type='number' step='0.1' value='${sl.temperature||''}'></div>
        <div style='display:flex; flex-direction:column; gap:3px;'><label style='font-size:.6rem;font-weight:600;'>ε (0–1)</label><input data-prop='emissivity' type='number' step='0.01' min='0' max='1' value='${sl.emissivity||0}'></div>
        <div style='display:flex; flex-direction:column; gap:3px;'><label style='font-size:.6rem;font-weight:600;'>A (m²)</label><input data-prop='A_layer' type='number' step='0.0001' value='${sl.A_layer||''}' placeholder='global'></div>
     </div>
     <label style='display:flex; align-items:center; gap:6px; margin-top:6px; font-size:.6rem; font-weight:600;'><input data-prop='include_radiation' class='sublayer-rad-toggle' type='checkbox' ${useRad?'checked':''} style='transform:scale(1.1);'> Incluir radiação</label>
     <div class='sublayer-rad-fields' style='display:${useRad?'block':'none'}; background:#f3e5f5; border:1px dashed #ce93d8; border-radius:8px; padding:6px 8px; margin-top:6px;'>
       <div style='display:flex; flex-direction:column; gap:3px;'><label style='font-size:.55rem;font-weight:600;'>T_viz (°C)</label><input data-prop='T_viz' type='number' step='0.1' value='${tviz}'></div>
     </div>`);
   } else if(/Paralelo/.test(sl.type||'')){
     const nBranches = Array.isArray(sl.branches) ? sl.branches.length : 0;
     // Auto-expandir o bloco paralelo aninhado
     const expandedContent = buildParallelContent(sl, -1);
     return wrap(header()+`<div style='font-size:.65rem; color:#555; margin-bottom:8px;'>Bloco paralelo aninhado (${nBranches} ${nBranches===1?'ramo':'ramos'}):</div>
     <div class='nested-parallel-content' style='margin-top:8px; padding:10px; background:#f8f4ff; border:1px solid #ce93d8; border-radius:8px;'>${expandedContent}</div>`);
  } else { // sólido / condução
    if(isCylGlobal){
      const r1 = sl.r_int || sl.r1_override || 0.05;
      const thick = sl.thickness || ( (sl.r2_override && sl.r1_override)? (sl.r2_override - sl.r1_override): 0.01);
      const useOvr = sl.use_r_override;
      return wrap(header()+`<div style='${baseStyle}'>
         <div style='display:flex; flex-direction:column; gap:3px;'><label style='font-size:.6rem;font-weight:600;'>r₁ (m)</label><input data-prop='r_int' class='cyl-r1' type='number' step='0.0001' value='${r1}' ${useOvr? 'disabled':''}></div>
         <div style='display:flex; flex-direction:column; gap:3px;'><label style='font-size:.6rem;font-weight:600;'>Espessura (m)</label><input data-prop='thickness' class='cyl-dr' type='number' step='0.0001' value='${thick}' ${useOvr? 'disabled':''}></div>
         <div style='display:flex; flex-direction:column; gap:3px;'><label style='font-size:.6rem;font-weight:600;'>k (W/m·K)</label><input data-prop='conductivity' type='number' step='0.01' value='${sl.conductivity||sl.k||''}'></div>
         <div style='display:flex; flex-direction:column; gap:3px;'><label style='font-size:.6rem;font-weight:600;'>R_cont (K/W)</label><input data-prop='contact_resistance' type='number' step='0.0001' value='${isFinite(sl.contact_resistance)?sl.contact_resistance:''}'></div>
         <div style='display:flex; flex-direction:column; gap:3px; grid-column:1/-1; background:#f3e5f5; padding:6px 8px; border:1px dashed #ce93d8; border-radius:8px;'>
           <label style='font-size:.6rem; font-weight:600; display:flex; gap:6px; align-items:center;'><input type='checkbox' class='sublayer-ovr-toggle' ${useOvr? 'checked':''}> Definir por raios</label>
           <div style='display:grid; grid-template-columns:repeat(auto-fit,minmax(90px,1fr)); gap:8px;'>
             <div style='display:flex; flex-direction:column; gap:3px;'><label style='font-size:.55rem;font-weight:600;'>r₁ ov (m)</label><input class='ovr-r1' data-prop='r1_override' type='number' step='0.0001' value='${sl.r1_override||''}' ${useOvr? '' : 'disabled'}></div>
             <div style='display:flex; flex-direction:column; gap:3px;'><label style='font-size:.55rem;font-weight:600;'>r₂ ov (m)</label><input class='ovr-r2' data-prop='r2_override' type='number' step='0.0001' value='${sl.r2_override||''}' ${useOvr? '' : 'disabled'}></div>
             <div class='ovr-warn' style='grid-column:1/-1; font-size:.5rem; color:#b71c1c; display:none;'>r₂ deve ser > r₁ e ambos > 0.</div>
           </div>
         </div>
      </div>`);
    } else {
      return wrap(header()+`<div style='${baseStyle}'>
         <div style='display:flex; flex-direction:column; gap:3px;'><label style='font-size:.6rem;font-weight:600;'>L (m)</label><input data-prop='thickness' type='number' step='0.0001' value='${sl.thickness||sl.L||''}'></div>
         <div style='display:flex; flex-direction:column; gap:3px;'><label style='font-size:.6rem;font-weight:600;'>k (W/m·K)</label><input data-prop='conductivity' type='number' step='0.01' value='${sl.conductivity||sl.k||''}'></div>
         <div style='display:flex; flex-direction:column; gap:3px;'><label style='font-size:.6rem;font-weight:600;'>R_cont (K/W)</label><input data-prop='contact_resistance' type='number' step='0.0001' value='${isFinite(sl.contact_resistance)?sl.contact_resistance:''}'></div>
         <div style='display:flex; flex-direction:column; gap:3px;'><label style='font-size:.6rem;font-weight:600;'>A (m²)</label><input data-prop='A_layer' type='number' step='0.0001' value='${sl.A_layer||''}' placeholder='global'></div>
      </div>`);
    }
  }
 }
 function buildParallelContent(layer, idx){
  const parIdx=idx; const branches=Array.isArray(layer.branches)?layer.branches:[]; const nBranches=branches.length;
  const branchR=branches.map(b=>computeBranchResistance(b)); const Req=computeParallelEquivalent(branches);
  const isNested = (parIdx === -1); // nested paralelo dentro de ramo
  let html = `<div style='background:${isNested?'#faf5ff':'#f5f9ff'}; border:1px solid ${isNested?'#ce93d8':'#bbdefb'}; padding:14px 16px; border-radius:14px; margin-bottom:12px;'>
    <h4 style='margin:0 0 10px; font-size:.85rem; color:${isNested?'#6a1b9a':'#0d47a1'}; font-weight:600;'>${isNested? 'Paralelo Aninhado' : 'Paralelo'} (${nBranches} ${nBranches===1?'ramo':'ramos'})</h4>
    <div id='parallel-metrics' ${isNested?"data-nested='1'":''} style='font-family:monospace; font-size:.7rem; line-height:1.4; background:#fff; border:1px solid ${isNested?'#e1bee7':'#e3f2fd'}; padding:10px 12px; border-radius:10px;'>${parallelMetricsHTML(branchR, Req, isNested)}</div>
    <div style='display:flex; flex-wrap:wrap; gap:10px; margin-top:12px;'>
      <button data-act='add-branch' data-par='${parIdx}' style='background:${isNested?'#f8e1ff':'#e0f2f1'}; color:${isNested?'#4a148c':'#1b5e20'}; border:1px solid ${isNested?'#ce93d8':'#80cbc4'}; padding:6px 10px; border-radius:8px; font-size:.7rem; cursor:pointer; font-weight:600;'>+ Ramo</button>
    </div>
  </div>`;
   branches.forEach((branch,bIdx)=>{
     html += `<div class='parallel-branch' data-par='${parIdx}' data-branch='${bIdx}' style='background:#fff; border:1px solid #e0e0e0; border-radius:12px; padding:12px 14px; margin-bottom:14px;'>
        <div style='display:flex; align-items:center; justify-content:space-between; margin:0 0 8px;'>
       <div style='display:flex; align-items:center; gap:10px;'>
         <button data-act='del-branch' data-par='${parIdx}' data-branch='${bIdx}' title='Remover ramo' style='background:#ffebee; color:#c62828; border:1px solid #ef9a9a; padding:4px 8px; border-radius:6px; font-size:.65rem; cursor:pointer; font-weight:700;'>×</button>
         <span style='font-weight:600; color:#37474f; font-size:.8rem;'>Ramo ${bIdx+1}</span>
       </div>
       <div style='display:flex; gap:6px;'>
         <button data-act='add-layer-kind' data-kind='Fluido' data-par='${parIdx}' data-branch='${bIdx}' style='background:#e3f2fd; color:#0d47a1; border:1px solid #90caf9; padding:4px 8px; border-radius:6px; font-size:.6rem; cursor:pointer; font-weight:600;'>+ Fluido</button>
         <button data-act='add-layer-kind' data-kind='Sólido' data-par='${parIdx}' data-branch='${bIdx}' style='background:#fff3e0; color:#e65100; border:1px solid #ffcc80; padding:4px 8px; border-radius:6px; font-size:.6rem; cursor:pointer; font-weight:600;'>+ Sólido</button>
       </div>
        </div>`;
     if(!branch.length){ html += `<div style='font-size:.65rem; font-style:italic; color:#607d8b;'>(vazio)</div>`; }
     branch.forEach((sl,slIdx)=>{ html += subLayerForm(parIdx,bIdx,slIdx,sl); });
     html += `</div>`;
   });
   return html;
 }
 function parallelMetricsHTML(branchR, Req, isNested=false){
   if(isNested){
     // Versão simplificada sem etapas detalhadas
     const ReqStr = fmtVal(Req);
     return `<div style='font-size:.65rem; color:#5e35b1;'>Resumo: ${branchR.length} ramos • R_eq = ${ReqStr}</div>`;
   }
   let out = `<strong>Etapa 1 – Resistência de cada ramo</strong><br>`;
   branchR.forEach((R,i)=>{ out += `<div style='margin:3px 0 1px; color:#4527a0;'>R_ramo${i+1}</div><div style='margin-left:8px;'>Soma = ${fmtVal(R)} K/W</div>`; });
   out += `<div style='margin-top:8px; font-weight:600;'>Etapa 2 – Associação em paralelo</div>`+
          `<div style='margin-left:8px;'>1/R_eq = Σ (1/R_ramo_i)</div>`+
          `<div style='margin-left:8px;'>R_eq = ${fmtVal(Req)}</div>`;
   return out;
 }
 function reRenderParallel(pop, layer, idx){
   const body=pop.querySelector('.parallel-body'); if(!body) return; body.innerHTML=buildParallelContent(layer, idx);
 }
 function updateParallelMetrics(pop, layer){
   const box=pop.querySelector('#parallel-metrics');
   if(!box) return;
   const isNested = box.dataset && box.dataset.nested === '1';
   let branchR, Req;
   if(typeof summarizeParallelBlock==='function'){
     const summary = summarizeParallelBlock(layer);
     branchR = (summary.branches||[]).map(b=>b.R_branch);
     Req = summary && isFinite(summary.Req)? summary.Req : NaN;
   } else {
     const branches = layer.branches||[];
     branchR = branches.map(b=>computeBranchResistance(b));
     Req = computeParallelEquivalent(branches);
   }
   box.innerHTML = parallelMetricsHTML(branchR, Req, isNested);
 }
 function serializeLayers(){ return JSON.stringify(layers,null,2); }
 function showExport(pop){ let modal=pop.querySelector('#export-area'); if(!modal){ const div=document.createElement('div'); div.id='export-area'; div.style.cssText='margin-top:14px;'; div.innerHTML=`<textarea style="width:100%; height:180px; font-family:monospace; font-size:.7rem; border:1px solid #90a4ae; border-radius:6px; padding:8px;">${serializeLayers()}</textarea>`; pop.appendChild(div);} else { modal.querySelector('textarea').value=serializeLayers(); } }
 function showImport(pop){ let modal=pop.querySelector('#import-area'); if(!modal){ const div=document.createElement('div'); div.id='import-area'; div.style.cssText='margin-top:14px;'; div.innerHTML=`<textarea id="import-json" placeholder="Cole JSON das camadas aqui" style="width:100%; height:140px; font-family:monospace; font-size:.7rem; border:1px solid #90a4ae; border-radius:6px; padding:8px;"></textarea>\n<div style='display:flex; justify-content:flex-end; margin-top:6px;'><button id='btn-do-import' style='background:#00796b; color:#fff; border:none; padding:6px 12px; border-radius:5px; font-size:.7rem; cursor:pointer;'>Aplicar Importação</button></div>`; pop.appendChild(div);} }
 function extractEdits(pop, layer){
   const isFluid=/Fluido/.test(layer.type||'');
   const isFinned=/SuperficieAletada/.test(layer.type||'');
   const isCyl=/Cilindrica/.test(layer.type||'');
   if(isFinned){
     renderFinnedMetrics(pop, layer);
   }
  if(isFinned){
    layer.N_fins=parseInt(pop.querySelector('#fin-N')?.value)||layer.N_fins;
    const LfinVal = parseFloat(pop.querySelector('#fin-length')?.value);
    if(isFinite(LfinVal) && LfinVal>0){ layer.fin_length = LfinVal; layer.L_fin = LfinVal; }
     layer.convection=parseFloat(pop.querySelector('#fin-h')?.value)||layer.convection;
     layer.conductivity=parseFloat(pop.querySelector('#fin-k')?.value)||layer.conductivity;
     layer.A_base=parseFloat(pop.querySelector('#fin-base-area')?.value)||layer.A_base;
     layer.use_tip_correction=pop.querySelector('#fin-tip-correction')?.checked||false;
     
     // Extrair parâmetros específicos por tipo
     const finType = pop.querySelector('input[name="fin-type-selection"]:checked')?.value || 'rectangular';
     layer.fin_type = finType;
     
     if(finType === 'rectangular') {
       layer.fin_width=parseFloat(pop.querySelector('#fin-width')?.value)||layer.fin_width;
       layer.fin_thickness=parseFloat(pop.querySelector('#fin-thickness')?.value)||layer.fin_thickness;
     } else {
       layer.fin_diameter=parseFloat(pop.querySelector('#fin-diameter')?.value)||layer.fin_diameter;
     }
  // manter compatibilidade com nomenclatura antiga
  layer.k_fin=parseFloat(pop.querySelector('#fin-k')?.value)||layer.k_fin;
  layer.h_base=parseFloat(pop.querySelector('#fin-h')?.value)||layer.h_base;
     const autoA=pop.querySelector('#fin-autoA')?.checked||false;
     if(!autoA){
       const Aval=parseFloat(pop.querySelector('#fin-A-base')?.value);
       if(isFinite(Aval)&&Aval>0) layer.A_base_total=Aval; else delete layer.A_base_total;
     } else delete layer.A_base_total;
   } else if(isFluid){
     layer.convection=parseFloat(pop.querySelector('#fluid-h')?.value)||0;
     layer.temperature=parseFloat(pop.querySelector('#fluid-temp')?.value)||0;
     layer.emissivity=parseFloat(pop.querySelector('#fluid-eps')?.value)||0;
     layer.T_viz=parseFloat(pop.querySelector('#fluid-tviz')?.value)||20;
     layer.include_radiation=pop.querySelector('#fluid-radiation')?.checked||false;
   } else if(isCyl){
     // UI cilíndrica: r1 + espessura ou overrides r1/r2
     const r1=parseFloat(pop.querySelector('#cyl-rint')?.value);
     const dr=parseFloat(pop.querySelector('#cyl-dr')?.value);
     const useOvr=pop.querySelector('#cyl-use-ovr')?.checked||false;
     const r1ov=parseFloat(pop.querySelector('#cyl-r1-ovr')?.value);
     const r2ov=parseFloat(pop.querySelector('#cyl-r2-ovr')?.value);
     const L=parseFloat(pop.querySelector('#cyl-L')?.value);
     const k=parseFloat(pop.querySelector('#cyl-k')?.value);
     const Rc=parseFloat(pop.querySelector('#cyl-Rc')?.value);
     
     layer.use_r_override=useOvr;
     if(useOvr && isFinite(r1ov) && isFinite(r2ov) && r2ov>r1ov){
       layer.r1_override=r1ov;
       layer.r2_override=r2ov;
       layer.r_int=r1ov;
       layer.r_ext=r2ov;
       layer.thickness=r2ov-r1ov;
     } else {
       delete layer.r1_override; delete layer.r2_override;
       if(isFinite(r1)) layer.r_int=r1; 
       if(isFinite(r1) && isFinite(dr) && dr>0) {
         layer.r_ext=r1+dr; // Sim, espessura altera r2 = r1 + espessura
         layer.thickness=dr;
       }
     }
     if(isFinite(L)) layer.L=L; 
     if(isFinite(k)) { layer.k=k; layer.conductivity=k; }
     layer.contact_resistance=(isFinite(Rc)&&Rc>0)?Rc:null;
   } else {
     layer.thickness=parseFloat(pop.querySelector('#solid-thickness')?.value)||layer.thickness||0;
     layer.conductivity=parseFloat(pop.querySelector('#solid-k')?.value)||layer.conductivity||0;
     const Rc=parseFloat(pop.querySelector('#solid-contact')?.value);
     layer.contact_resistance=(isFinite(Rc)&&Rc>0)?Rc:null;
   }
 }
 function duplicateLayer(idx){ try{ const base=layers[idx]; if(!base) return; const copy=JSON.parse(JSON.stringify(base)); const name=base.type.replace(/(\d+)?$/,'').trim(); const count=layers.filter(l=> (l.type||'').startsWith(name)).length+1; copy.type=name+' '+count; layers.splice(idx+1,0,copy); updateLayersList(); updateCircuitDisplay(); }catch(e){ console.warn('Falha duplicar',e);} }
window.openPropertyPopover=function(event, idx, nestedLayer){ try{ 
  let layer;
  if(nestedLayer && idx === -1) {
    // Caso especial: bloco paralelo aninhado
    layer = nestedLayer;
  } else if(!Array.isArray(layers)||!layers[idx]){ 
    console.warn('Camada inválida', idx); return; 
  } else {
    layer = layers[idx];
  } destroyCurrent(); const pop=document.createElement('div'); window.currentPopover=pop; pop.className='prop-popover'; pop.style.cssText='position:fixed; background:#fff; border:2px solid #1976d2; border-radius:20px; padding:22px 26px 24px; max-width:760px; max-height:84vh; overflow:auto; z-index:30000; font:14px \'Segoe UI\',Arial; box-shadow:0 22px 60px -10px rgba(0,0,0,.4);'; const isParallel=Array.isArray(layer.branches) && layer.branches.length > 0; const isFluid=/Fluido/.test(layer.type||''); const isFinned=/SuperficieAletada/.test(layer.type||''); const isCyl=/Cilindrica/.test(layer.type||''); let content=''; if(isParallel){ content = `<div class="parallel-body">${buildParallelContent(layer, idx)}</div>`; } else if(isFinned){ content=(typeof createFinnedContent==='function'? createFinnedContent(layer):'<div>Conteúdo aletado indisponível.</div>'); } else if(isFluid){ 
     const h=layer.convection||10; 
     const T=layer.temperature||25; 
     const eps=layer.emissivity||0.8; 
     const Tviz=layer.T_viz||20; 
     const useRad=layer.include_radiation||false; 
     content=`<div style='background:#e3f2fd; border:1px solid #bbdefb; border-radius:12px; padding:16px 18px 14px; margin-bottom:12px;'>
<h4 style='margin:0 0 12px; font-size:.95rem; color:#0d47a1; font-weight:600;'>Fluido (Convecção)</h4>
<div style='display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:14px; margin-bottom:16px;'>
 <div><label style='font-size:.63rem;font-weight:600;'>h (W/m²·K)</label><input id='fluid-h' type='number' step='0.01' value='${h}' style='width:100%;'></div>
 <div><label style='font-size:.63rem;font-weight:600;'>T (°C)</label><input id='fluid-temp' type='number' step='0.1' value='${T}' style='width:100%;'></div>
 <div><label style='font-size:.63rem;font-weight:600;'>ε (0–1)</label><input id='fluid-eps' type='number' step='0.01' min='0' max='1' value='${eps}' style='width:100%;'></div>
</div>
<label style='display:flex; align-items:center; gap:6px; margin-bottom:12px; font-size:.65rem; font-weight:600;'><input id='fluid-radiation' type='checkbox' ${useRad?'checked':''} style='transform:scale(1.1);'> Incluir radiação</label>
<div id='radiation-fields' style='display:${useRad?'block':'none'}; background:#f3e5f5; border:1px dashed #ce93d8; border-radius:10px; padding:10px 12px; margin-bottom:12px;'>
 <div><label style='font-size:.63rem;font-weight:600;'>Temperatura de vizinhança T_viz (°C)</label><input id='fluid-tviz' type='number' step='0.1' value='${Tviz}' style='width:100%;'></div>
</div>
</div>`; } else if(isCyl){ 
     let r1=layer.r_int||0.05, r2=layer.r_ext||(r1+(layer.thickness||0.01)); 
     if(!(r2>r1)) r2=r1+0.01; 
     const dr=parseFloat((r2-r1).toFixed(4)); 
     const k=layer.k||layer.conductivity||50; 
     const L=layer.L||1.0; 
     const Rc=layer.contact_resistance||''; 
     const useOvr=layer.use_r_override; 
     const r1ovr=layer.r1_override ? parseFloat(layer.r1_override).toFixed(4) : ''; 
     const r2ovr=layer.r2_override ? parseFloat(layer.r2_override).toFixed(4) : ''; 
     content=`<div style='background:#f3e5f5; border:1px solid #e1bee7; border-radius:12px; padding:16px 18px 14px; margin-bottom:12px;'>
<h4 style='margin:0 0 12px; font-size:.95rem; color:#6a1b9a; font-weight:600;'>Sólido (Condução Cilíndrica)</h4>
<div style='display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:14px; margin-bottom:16px;'>
 <div><label style='font-size:.63rem;font-weight:600;'>Comprimento L (m)</label><input id='cyl-L' type='number' step='0.001' value='${L}' style='width:100%;'></div>
 <div><label style='font-size:.63rem;font-weight:600;'>Raio interno r₁ (m)</label><input id='cyl-rint' type='number' step='0.0001' value='${r1}' ${useOvr? 'disabled':''} style='width:100%;'></div>
 <div><label style='font-size:.63rem;font-weight:600;'>Espessura (m)</label><input id='cyl-dr' type='number' step='0.0001' value='${dr}' ${useOvr? 'disabled':''} style='width:100%;'></div>
</div>
<div style='display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:14px; margin-bottom:16px;'>
 <div><label style='font-size:.63rem;font-weight:600;'>Condutividade Térmica (W/m·K)</label><input id='cyl-k' type='number' step='0.01' value='${k}' style='width:100%;'></div>
 <div><label style='font-size:.63rem;font-weight:600;'>R_contato (K/W, opcional)</label><input id='cyl-Rc' type='number' step='0.0001' value='${Rc}' style='width:100%;' placeholder='0'></div>
</div>
<div style='background:#ede7f6; border:1px dashed #b39ddb; border-radius:10px; padding:10px 12px; margin-bottom:12px;'>
 <label style='display:flex; gap:8px; align-items:center; font-size:.65rem; font-weight:600; margin-bottom:8px;'><input id='cyl-use-ovr' type='checkbox' ${useOvr?'checked':''}> Definir por raios (opcional)</label>
 <div style='display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px;'>
  <div><label style='font-size:.6rem;font-weight:600;'>r₁ (m)</label><input id='cyl-r1-ovr' type='number' step='0.0001' value='${r1ovr}' ${useOvr?'' :'disabled'} style='width:100%;'></div>
  <div><label style='font-size:.6rem;font-weight:600;'>r₂ (m)</label><input id='cyl-r2-ovr' type='number' step='0.0001' value='${r2ovr}' ${useOvr?'' :'disabled'} style='width:100%;'></div>
 </div>
</div>
<div id='cyl-metrics' style='background:#ede7f6; border:1px solid #d1c4e9; padding:10px 12px; border-radius:10px; font-family:monospace; font-size:.7rem; line-height:1.35;'>—</div>
</div>`; } else { content=(typeof createNormalContent==='function'? createNormalContent(layer,false):'<div>Condução plana básica.</div>'); }
const headerText = (idx === -1) ? 'Bloco Paralelo Aninhado' : `Camada ${idx+1}`;
 pop.innerHTML=header(layer,idx,headerText)+(isParallel? '' : actionsBar())+content+(isParallel? '' : (metricsContainers(layer)+footerButtons()))+(isParallel? footerButtons(): '');
 document.body.appendChild(pop);
 positionSmart(pop,event);
 // Abrir painel lateral com imagem (se função auxiliar estiver disponível)
 try {
   if (typeof window.openSideImagePopoverFor === 'function') {
     window.openSideImagePopoverFor(pop);
   } else {
     console.warn('[PopoverAvancado] openSideImagePopoverFor ausente, usando fallback simples');
     try {
       const side = document.createElement('div');
       side.id = 'side-image-popover';
  side.style.cssText = 'position:fixed; background:#ffffff; border:2px solid #90caf9; border-radius:12px; padding:10px; box-shadow:0 12px 40px rgba(0,0,0,0.25); z-index:100000; max-height:84vh; overflow:auto;';
       const geom = (typeof selectedGeometry!=='undefined' ? selectedGeometry : 'planar');
       const imgSrc = geom==='cylindrical' ? '/static/formulas/cilindro.png' : '/static/formulas/parede.png';
       const title = geom==='cylindrical' ? 'Esquema (cilindro)' : 'Esquema (parede plana)';
       side.innerHTML = "<div id='side-pop-head' style='display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:6px; cursor:move;'>"
         +   "<div style='font-weight:700;color:#1565c0;'>"+title+"</div>"
         +   "<div style='display:flex; gap:6px;'>"
         +     "<button type='button' id='side-pop-reset' class='btn-sm' title='Reposicionar ao lado do popover' style='background:#bbdefb;color:#0d47a1;'>Reset</button>"
         +     "<button type='button' id='side-pop-close' class='btn-sm' style='background:#e3f2fd;color:#0d47a1;'>Fechar</button>"
         +   "</div>"
         + "</div>"
         + "<div style='border:1px solid #e3f2fd;border-radius:8px;padding:6px;background:#fafcff;'>"
         +   "<img id='side-pop-img' src='"+imgSrc+"' alt='"+title+"' style='display:block;max-width:100%;height:auto;border-radius:6px;'>"
         + "</div>";
  document.body.appendChild(side);
  // Aumentar largura para planar; manter para cilíndrica
  try { side.style.maxWidth = (geom==='cylindrical') ? '380px' : '560px'; } catch{}
       const vw = window.innerWidth, vh = window.innerHeight;
       const ALIGN_OFFSET = -8;
       let userMoved=false;
       function positionSide(){
         try{
           const rect = pop.getBoundingClientRect();
           const styleTop = (pop && pop.style && /px$/.test(pop.style.top||'')) ? parseFloat(pop.style.top) : rect.top;
           const styleLeft = (pop && pop.style && /px$/.test(pop.style.left||'')) ? parseFloat(pop.style.left) : rect.left;
           const popW = pop.offsetWidth || rect.width;
           let left = styleLeft + popW + 12;
           if (left + side.offsetWidth + 20 > vw) left = Math.max(20, styleLeft - side.offsetWidth - 12);
           let top = styleTop + ALIGN_OFFSET;
           if (top < 20) top = 20;
           if (top + side.offsetHeight > vh - 20) top = Math.max(20, vh - side.offsetHeight - 20);
           side.style.left = left + 'px';
           side.style.top = Math.max(20, top) + 'px';
         } catch{}
       }
       positionSide();
       // estabilizar após repaints
       (function rAFStabilize(){ let i=0; function tick(){ if(userMoved) return; positionSide(); if(++i<10) requestAnimationFrame(tick);} requestAnimationFrame(tick); })();
       // reposicionar em load da imagem
       try { side.querySelector('#side-pop-img')?.addEventListener('load', ()=>{ if(!userMoved) positionSide(); }, { once:true }); } catch{}
       // resize/scroll
       function maybeAuto(){ if(!userMoved) positionSide(); }
       window.addEventListener('resize', maybeAuto, { passive:true });
       window.addEventListener('scroll', maybeAuto, { passive:true });
       // observar mudanças de tamanho
       try { const ro=new ResizeObserver(()=>{ if(!userMoved) positionSide(); }); ro.observe(pop); ro.observe(side); side.__ro=ro; }catch{}
       // drag
       (function enableDrag(){ const head=side.querySelector('#side-pop-head'); if(!head) return; let dragging=false,sx=0,sy=0,sl=0,st=0; function mv(ev){ if(!dragging) return; const dx=(ev.clientX||0)-sx, dy=(ev.clientY||0)-sy; side.style.left=(sl+dx)+'px'; side.style.top=(st+dy)+'px'; userMoved=true; } function up(){ dragging=false; document.removeEventListener('mousemove',mv); document.removeEventListener('mouseup',up); document.body.style.userSelect=''; } head.addEventListener('mousedown', (ev)=>{ ev.preventDefault?.(); dragging=true; const r=side.getBoundingClientRect(); sx=ev.clientX||0; sy=ev.clientY||0; sl=r.left; st=r.top; document.addEventListener('mousemove',mv); document.addEventListener('mouseup',up); document.body.style.userSelect='none'; }); })();
       // reset
       side.querySelector('#side-pop-reset')?.addEventListener('click', ()=>{ userMoved=false; positionSide(); });
       // close
       side.querySelector('#side-pop-close')?.addEventListener('click', ()=>{ try{ side.__ro && side.__ro.disconnect && side.__ro.disconnect(); side.remove(); }catch{} });
     } catch (e2) { console.warn('[PopoverAvancado] Fallback lateral falhou', e2); }
   }
 } catch (e) { console.warn('[PopoverAvancado] Falha ao abrir painel lateral', e); }
 if(!isParallel){ renderMetrics(pop,layer); }
// Event listeners para interface simplificada
if(!isParallel){
 // Interface simplificada sem botões de formatação
}
const autoBox=pop.querySelector('#chk-auto'); if(autoBox){ autoBox.addEventListener('change',()=>{ try{localStorage.setItem('thermalAutoUpdate', JSON.stringify(autoBox.checked));}catch{} }); }
if(!isParallel){
  // Reação genérica a inputs
  pop.addEventListener('input',ev=>{ if(autoBox && autoBox.checked){ extractEdits(pop,layer); renderMetrics(pop,layer);} });
  pop.addEventListener('change',ev=>{ 
    if(ev.target.id==='fluid-radiation'){
      const radFields=pop.querySelector('#radiation-fields');
      if(radFields) radFields.style.display = ev.target.checked ? 'block' : 'none';
      if(autoBox && autoBox.checked){ extractEdits(pop,layer); renderMetrics(pop,layer);}
    }
    // Handler para mudança de tipo de aleta
    else if(ev.target.name === 'fin-type-selection'){
      const newFinType = ev.target.value;
      layer.fin_type = newFinType;
      // Recriar conteúdo específico
      const specificParams = pop.querySelector('#fin-specific-params');
      if(specificParams) {
        const isRectangular = newFinType === 'rectangular';
        if(isRectangular) {
          const w = layer.fin_width || 0.02;
          const t = layer.fin_thickness || 0.002;
          const useTip = layer.use_tip_correction || false;
          specificParams.innerHTML = `
            <div style='display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; margin-bottom:16px;'>
              <div><label style='font-size:.63rem;font-weight:600;'>Largura w (m)</label><input id='fin-width' type='number' step='0.001' value='${w}' style='width:100%;'></div>
              <div><label style='font-size:.63rem;font-weight:600;'>Espessura t (m)</label><input id='fin-thickness' type='number' step='0.0001' value='${t}' style='width:100%;'></div>
            </div>
            <label style='display:flex; align-items:center; gap:6px; margin-bottom:12px; font-size:.65rem; font-weight:600;'>
              <input id='fin-tip-correction' type='checkbox' ${useTip?'checked':''} style='transform:scale(1.1);'> Usar correção de ponta (L_c)
            </label>`;
        } else {
          const D = layer.fin_diameter || 0.005;
          const useTip = layer.use_tip_correction || false;
          specificParams.innerHTML = `
            <div style='display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; margin-bottom:16px;'>
              <div><label style='font-size:.63rem;font-weight:600;'>Diâmetro D (m)</label><input id='fin-diameter' type='number' step='0.0001' value='${D}' style='width:100%;'></div>
            </div>
            <label style='display:flex; align-items:center; gap:6px; margin-bottom:12px; font-size:.65rem; font-weight:600;'>
              <input id='fin-tip-correction' type='checkbox' ${useTip?'checked':''} style='transform:scale(1.1);'> Usar correção de ponta (L_c)
            </label>`;
        }
      }
      if(autoBox && autoBox.checked){ extractEdits(pop,layer); renderMetrics(pop,layer);}
    }
  });
  pop.querySelector('#btn-dup')?.addEventListener('click',()=>{ duplicateLayer(idx); destroyCurrent(); });
  // Ajustes específicos para modo cilíndrico (toggle override)
  if(isCyl){
     const chk=pop.querySelector('#cyl-use-ovr');
     const r1o=pop.querySelector('#cyl-r1-ovr');
     const r2o=pop.querySelector('#cyl-r2-ovr');
     const baseR=pop.querySelector('#cyl-rint');
     const baseDr=pop.querySelector('#cyl-dr');
     function sync(){ 
       const on=chk?.checked; 
       if(r1o) r1o.disabled=!on; 
       if(r2o) r2o.disabled=!on; 
       if(baseR) baseR.disabled=on;
       if(baseDr) baseDr.disabled=on;
     }
     chk?.addEventListener('change',()=>{ sync(); if(autoBox && autoBox.checked){ extractEdits(pop,layer); renderMetrics(pop,layer);} });
     sync();
  }
} else {
  // Eventos de clique estruturais
  pop.addEventListener('click',function(e){ const btn=e.target.closest('button'); if(!btn) return; const act=btn.getAttribute('data-act'); if(act==='add-branch'){ 
   // Se idx === -1 significa bloco paralelo aninhado dentro de um ramo (não é layer principal em 'layers')
   if(idx === -1){
     if(Array.isArray(layer.branches)){
       layer.branches.push([]);
       try{ pushHistory && pushHistory('add nested branch (popover)'); }catch{}
       updateLayersList(); updateCircuitDisplay(); reRenderParallel(pop, layer, idx); updateParallelMetrics(pop, layer);
     }
   } else {
     if(typeof addBranch==='function'){
       addBranch(idx);
       updateLayersList(); updateCircuitDisplay(); reRenderParallel(pop, layer, idx); updateParallelMetrics(pop, layer);
     }
   }
  }
    else if(act==='add-nested-parallel'){ return; }
  else if(act==='add-layer-kind'){ const kind=btn.getAttribute('data-kind'); const b=parseInt(btn.getAttribute('data-branch')); 
      // Criar nova camada com propriedades padrão
  let newLayer = { type: kind };
      if(kind==='Fluido') {
        newLayer = { ...newLayer, convection: 10, temperature: 25, emissivity: 0.8, include_radiation: false, T_viz: 20 };
      } else if(kind==='Sólido') {
        newLayer = { ...newLayer, thickness: 0.01, conductivity: 50 };
      }
      if(!layer.branches[b]) layer.branches[b] = [];
      layer.branches[b].push(newLayer);
      updateLayersList(); updateCircuitDisplay(); reRenderParallel(pop, layer, idx); updateParallelMetrics(pop, layer);
    }
  else if(act==='del-sublayer'){ const b=parseInt(btn.getAttribute('data-branch')); const l=parseInt(btn.getAttribute('data-layer')); if(typeof removeBranchLayer==='function'){ removeBranchLayer(idx,b,l); updateLayersList(); updateCircuitDisplay(); reRenderParallel(pop, layer, idx); updateParallelMetrics(pop, layer);} }
  else if(act==='del-branch'){ 
    const b=parseInt(btn.getAttribute('data-branch'));
    if(idx === -1){ // paralelo aninhado (layer é o próprio bloco em edição)
      if(Array.isArray(layer.branches) && layer.branches[b]){
        layer.branches.splice(b,1);
        try{ pushHistory && pushHistory('remove nested branch (popover)'); }catch{}
        updateLayersList(); updateCircuitDisplay(); reRenderParallel(pop, layer, idx); updateParallelMetrics(pop, layer);
      }
    } else if(typeof removeBranch==='function') {
      removeBranch(idx,b); updateLayersList(); updateCircuitDisplay(); reRenderParallel(pop, layer, idx); updateParallelMetrics(pop, layer);
    }
   }
    else if(act==='edit-sublayer'){ 
      const b=parseInt(btn.getAttribute('data-branch')); 
      const l=parseInt(btn.getAttribute('data-layer')); 
      const sublayer = layer.branches[b][l];
      
      console.log('DEBUG edit-sublayer:', { b, l, sublayer, hasBranches: Array.isArray(sublayer?.branches) });
      
      // Blocos paralelos agora são sempre expandidos, só editar camadas simples
      if(typeof openBranchLayerPopover==='function'){ 
        console.log('Abrindo camada simples');
        openBranchLayerPopover(idx,b,l,e); 
      } else {
        console.log('Nenhuma ação disponível para esta sublayer');
      }
    }
  });
  // Edição inline
  pop.addEventListener('input', function(e){ const inp=e.target; if(!inp.closest('.sublayer-editor')) return; const ed=inp.closest('.sublayer-editor'); const b=parseInt(ed.getAttribute('data-branch')); const l=parseInt(ed.getAttribute('data-layer')); if(!layer.branches[b]||!layer.branches[b][l]) return; const sub=layer.branches[b][l]; const prop=inp.getAttribute('data-prop'); if(prop){ let raw=inp.value.trim().replace(',','.'); const num=parseFloat(raw); if(inp.type==='checkbox'){ sub[prop]=inp.checked; } else { if(!isNaN(num)) sub[prop]=num; else if(raw==='') delete sub[prop]; }
    // Regras cilíndricas
    if(selectedGeometry==='cylindrical' && !/Fluido/.test(sub.type||'')){
      if(sub.use_r_override){ if(isFinite(sub.r1_override)&&isFinite(sub.r2_override)&&sub.r2_override>sub.r1_override){ sub.r_int=sub.r1_override; sub.r_ext=sub.r2_override; sub.thickness=sub.r_ext-sub.r_int; } }
      else { if(prop==='r_int'||prop==='thickness'){ if(isFinite(sub.r_int)&&isFinite(sub.thickness)&&sub.thickness>0){ sub.r_ext=sub.r_int+sub.thickness; } } }
    }
  }
    updateParallelMetrics(pop, layer); });
  // Toggle override e radiação
  pop.addEventListener('change', function(e){ 
    // Toggle override cilíndrico
    const chk=e.target.closest('.sublayer-ovr-toggle'); 
    if(chk) {
      const ed=chk.closest('.sublayer-editor'); const b=parseInt(ed.getAttribute('data-branch')); const l=parseInt(ed.getAttribute('data-layer')); const sub=layer.branches[b][l]; sub.use_r_override=chk.checked; const r1o=ed.querySelector('.ovr-r1'); const r2o=ed.querySelector('.ovr-r2'); const baseR=ed.querySelector('.cyl-r1'); const baseDr=ed.querySelector('.cyl-dr'); if(chk.checked){ if(r1o) r1o.disabled=false; if(r2o) r2o.disabled=false; if(baseR) baseR.disabled=true; if(baseDr) baseDr.disabled=true; } else { if(r1o) r1o.disabled=true; if(r2o) r2o.disabled=true; if(baseR) baseR.disabled=false; if(baseDr) baseDr.disabled=false; } if(sub.use_r_override){ if(isFinite(sub.r1_override)&&isFinite(sub.r2_override)&&sub.r2_override>sub.r1_override){ sub.r_int=sub.r1_override; sub.r_ext=sub.r2_override; sub.thickness=sub.r_ext-sub.r_int; }} updateParallelMetrics(pop, layer); return;
    }
    // Toggle radiação
    const radChk=e.target.closest('.sublayer-rad-toggle');
    if(radChk) {
      const ed=radChk.closest('.sublayer-editor'); const radFields=ed.querySelector('.sublayer-rad-fields'); if(radFields) radFields.style.display = radChk.checked ? 'block' : 'none'; const b=parseInt(ed.getAttribute('data-branch')); const l=parseInt(ed.getAttribute('data-layer')); const sub=layer.branches[b][l]; sub.include_radiation=radChk.checked; updateParallelMetrics(pop, layer); return;
    }
  });
  // Validação visual override
  pop.addEventListener('input', function(e){ const ed=e.target.closest('.sublayer-editor'); if(!ed) return; if(selectedGeometry!=='cylindrical') return; const chk=ed.querySelector('.sublayer-ovr-toggle'); if(!chk||!chk.checked) return; const r1o=ed.querySelector('.ovr-r1'); const r2o=ed.querySelector('.ovr-r2'); const warn=ed.querySelector('.ovr-warn'); const v1=parseFloat(r1o?.value); const v2=parseFloat(r2o?.value); const bad=!(isFinite(v1)&&isFinite(v2)&&v2>v1&&v1>0); if(warn) warn.style.display=bad?'block':'none'; [r1o,r2o].forEach(el=>{ if(!el)return; el.style.borderColor=bad?'#d32f2f':'#90a4ae'; el.style.background=bad?'#ffebee':'#fff'; }); });
 }
 pop.addEventListener('click',e=>{ const actBtn=e.target.closest('.btn-pop'); if(!actBtn) return; const act=actBtn.getAttribute('data-act');
   if(act==='return'){ destroyCurrent(); return; }
   if(act==='save'){ if(!isParallel){ extractEdits(pop,layer); } updateLayersList(); updateCircuitDisplay(); destroyCurrent(); return; }
 });
 pop.querySelector('#pop-close-x').addEventListener('click',destroyCurrent);
 setTimeout(()=>{
   document.addEventListener('mousedown', function onDoc(ev){
     if(!currentPopover) return document.removeEventListener('mousedown', onDoc);
     if(!currentPopover.contains(ev.target)){
       destroyCurrent();
       document.removeEventListener('mousedown', onDoc);
     }
   });
 },30);
 console.log(installingLogPrefix,'Popover avançado aberto camada', idx, isParallel?'(PARALELO)':'');
 }catch(err){ console.error(installingLogPrefix,'Falha openPropertyPopover avançado:', err); } };
 console.log(installingLogPrefix,'Implementação avançada de openPropertyPopover instalada.');
})();
