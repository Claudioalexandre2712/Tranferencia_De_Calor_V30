// Conteúdo unificado para o popover avançado
(function(){
  if(window.__POPOVER_CONTENT_READY__) return; // evitar dupla carga
  window.__POPOVER_CONTENT_READY__ = true;
  const logPrefix = '[PopoverContent]';

  function numberInput(id,label,value,step='0.001',extra=''){
    return `<div class="form-group" style="display:flex; flex-direction:column; gap:4px;">
      <label for="${id}" style="font-size:0.65rem; font-weight:600; letter-spacing:.5px; color:#455a64; margin:0;">${label}</label>
      <input id="${id}" type="number" step="${step}" value="${value}" ${extra} style="padding:6px 8px; border:1px solid #90a4ae; border-radius:6px; font-size:0.75rem;" />
    </div>`;
  }

  window.createNormalContent = function(layer,isFluid){
    try {
      if(isFluid){
        return `
          <div style="background:#e3f2fd; border:1px solid #bbdefb; padding:14px 16px; border-radius:14px; margin-bottom:12px;">
            <h5 style="margin:0 0 10px; font-size:.85rem; color:#0d47a1; display:flex; align-items:center; gap:6px; font-weight:600;">💨 Propriedades do Fluido</h5>
            <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px;">
              ${numberInput('fluid-h','h (W/m²·K)', layer.convection||0,'0.1')}
              ${numberInput('fluid-temp','T (°C)', layer.temperature||0,'0.1')}
              ${numberInput('fluid-eps','ε (0–1)', layer.emissivity||0,'0.01','min="0" max="1"')}
              ${numberInput('fluid-tviz','T_viz (°C)', layer.T_viz!=null?layer.T_viz:'','0.1')}
            </div>
            <label style="display:flex; align-items:center; gap:8px; cursor:pointer; font-size:.65rem; font-weight:600; color:#0d47a1; margin-top:10px;">
              <input id="fluid-radiation" type="checkbox" ${layer.include_radiation?'checked':''} style="transform:scale(1.2);"> Incluir radiação linearizada
            </label>
          </div>`;
      } else {
        return `
          <div style="background:#fff3e0; border:1px solid #ffe0b2; padding:14px 16px; border-radius:14px; margin-bottom:12px;">
            <h5 style="margin:0 0 10px; font-size:.85rem; color:#e65100; display:flex; align-items:center; gap:6px; font-weight:600;">🧊 Propriedades do Sólido</h5>
            <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px;">
              ${numberInput('solid-thickness','L (m)', layer.thickness||layer.L||0.01,'0.0001')}
              ${numberInput('solid-k','k (W/m·K)', layer.conductivity||layer.k||10,'0.01')}
              ${numberInput('solid-contact','R_contato (K/W)', layer.contact_resistance!=null?layer.contact_resistance:'','0.0001','min="0"')}
            </div>
          </div>`;
      }
    } catch(e){ console.warn(logPrefix,'Falha createNormalContent:', e); return '<div>Falha conteúdo.</div>'; }
  };

  window.createFinnedContent = function(layer){
    try {
      const metrics = (typeof getFinnedMetrics==='function'? (getFinnedMetrics(layer)||{}):{});
      const autoA = !(isFinite(parseFloat(layer.A_base_total)) && parseFloat(layer.A_base_total)>0);
      const fmt = (v,dp=4)=> isFinite(v)? Number(v).toFixed(dp):'—';
      return `
        <div style="background:#f0f8ff; border:1px solid #1976d2; padding:16px 18px; border-radius:16px; margin-bottom:14px;">
          <h5 style="margin:0 0 12px; font-size:.85rem; color:#1565c0; display:flex; align-items:center; gap:6px; font-weight:600;">🌊 Superfície Aletada</h5>
          <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(110px,1fr)); gap:10px;">
            ${numberInput('fin-N','N (aletas)', layer.N_fins||20,'1','min="1"')}
            ${numberInput('fin-L','L (m)', layer.L_fin||0.02,'0.001')}
            ${numberInput('fin-t', (layer.is_pin?'d (m)':'t (m)'), layer.t_fin||layer.d_fin||0.002,'0.0001')}
            ${numberInput('fin-w','w (m)', layer.w_fin||0.02,'0.001', layer.is_pin? 'disabled style="opacity:.5;"':'')}
            ${numberInput('fin-k','k (W/m·K)', layer.k_fin||200,'1')}
            ${numberInput('fin-h','h (W/m²·K)', layer.h_base||100,'0.1')}
          </div>
          <div style="display:flex; gap:18px; flex-wrap:wrap; margin-top:10px; font-size:.65rem; font-weight:600; color:#1565c0;">
            <label style="display:flex; align-items:center; gap:6px; cursor:pointer;">
              <input id="fin-is-pin" type="checkbox" ${layer.is_pin?'checked':''} style="transform:scale(1.15);"> Aletas cilíndricas (pino)
            </label>
            <label style="display:flex; align-items:center; gap:6px; cursor:pointer;">
              <input id="fin-autoA" type="checkbox" ${autoA?'checked':''} style="transform:scale(1.15);"> Área base automática
            </label>
          </div>
          <div style="margin-top:10px; display:flex; gap:10px; align-items:center;">
            <label for="fin-A-base" style="font-size:.65rem; font-weight:600; color:#1565c0; margin:0;">A_base (m²)</label>
            <input id="fin-A-base" type="number" step="0.0001" value="${autoA? fmt(metrics.A_base_auto||0,4):(layer.A_base_total||metrics.A_base_auto||0)}" ${autoA?'disabled style="opacity:.6;"':''} style="flex:1; padding:6px 8px; border:1px solid #90caf9; border-radius:6px; font-size:0.75rem;">
          </div>
          <div style="background:#e8f5e9; border:1px solid #c5e1a5; padding:10px 12px; border-radius:10px; margin-top:14px;">
            <h6 style="margin:0 0 6px; font-size:.7rem; letter-spacing:.5px; color:#2e7d32; font-weight:700;">📊 Métricas</h6>
            <div id="fin-results" style="font-family:monospace; font-size:.72rem; line-height:1.35; color:#1b5e20;">
              <div>η_f = ${fmt(metrics.eta_f,3)} | η_o = ${fmt(metrics.eta_o,3)}</div>
              <div>R_equiv = ${fmt(metrics.R,4)} K/W</div>
            </div>
          </div>
        </div>`;
    } catch(e){ console.warn(logPrefix,'Falha createFinnedContent:', e); return '<div>Falha conteúdo aletado.</div>'; }
  };

  console.log(logPrefix,'Conteúdo unificado instalado.');
})();
