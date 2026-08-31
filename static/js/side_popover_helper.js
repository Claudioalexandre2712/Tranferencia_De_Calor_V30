(function(){
  if (window.openSideImagePopoverFor) return; // evita redefinição
  window.openSideImagePopoverFor = function(anchorEl){
    try {
      if(!anchorEl || !anchorEl.getBoundingClientRect){ console.warn('[SIDE-POPOVER] anchor inválido'); return; }
      const prev = document.getElementById('side-image-popover');
      if (prev) try{ prev.__ro && prev.__ro.disconnect && prev.__ro.disconnect(); prev.remove(); }catch{}

      const side = document.createElement('div');
      side.id = 'side-image-popover';
  side.style.cssText = 'position:fixed; background:#ffffff; border:2px solid #90caf9; border-radius:12px; padding:10px; box-shadow:0 12px 40px rgba(0,0,0,0.25); z-index:100000; max-width:380px; max-height:84vh; overflow:auto;';
      const geom = (window.selectedGeometry||'planar');
      const imgPlanar = '/static/formulas/parede.png';
      const imgCyl = '/static/formulas/cilindro.png';
      const imgSrc = geom==='cylindrical' ? imgCyl : imgPlanar;
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
        + "</div>"
        + "<div style='font-size:11px;color:#546e7a;margin-top:8px;line-height:1.3;'>Notação: h₁/T∞₁ à esquerda, h₂/T∞₂ à direita; sólidos com kᵢ e Lᵢ. Q̇ atravessa todas as camadas.</div>";
  document.body.appendChild(side);
  // Aumenta apenas para geometria planar
  try { side.style.maxWidth = (geom === 'cylindrical') ? '380px' : '560px'; } catch{}

      const vw = window.innerWidth, vh = window.innerHeight;
      const ALIGN_OFFSET = -8; // ajuste fino do topo
      let userMoved = false;

      function positionSide(){
        try {
          const rect = anchorEl.getBoundingClientRect();
          const styleTop = (anchorEl && anchorEl.style && /px$/.test(anchorEl.style.top||'')) ? parseFloat(anchorEl.style.top) : rect.top;
          const styleLeft = (anchorEl && anchorEl.style && /px$/.test(anchorEl.style.left||'')) ? parseFloat(anchorEl.style.left) : rect.left;
          const popW = anchorEl.offsetWidth || rect.width;
          let left = styleLeft + popW + 12;
          if (left + side.offsetWidth + 20 > vw) left = Math.max(20, styleLeft - side.offsetWidth - 12);
          let top = styleTop + ALIGN_OFFSET;
          if (top < 20) top = 20;
          if (top + side.offsetHeight > vh - 20) top = Math.max(20, vh - side.offsetHeight - 20);
          side.style.left = left + 'px';
          side.style.top = Math.max(20, top) + 'px';
        } catch{}
      }

      // primeira posição + estabilização
      positionSide();
      (function rAFStabilize(){ let i=0; function tick(){ if(userMoved) return; positionSide(); if(++i<10) requestAnimationFrame(tick); } requestAnimationFrame(tick); })();

      // load da imagem
      const img = side.querySelector('#side-pop-img');
      if(img){
        img.addEventListener('load', ()=>{ if(!userMoved) positionSide(); }, { once:true });
        img.addEventListener('error', ()=>{ try{ img.src = (geom==='cylindrical'? imgCyl: imgPlanar); }catch{} }, { once:true });
      }

      // resize/scroll
      function maybeAuto(){ if(!userMoved) positionSide(); }
      window.addEventListener('resize', maybeAuto, { passive:true });
      window.addEventListener('scroll', maybeAuto, { passive:true });

      // observar mudanças de tamanho do popover e do painel
      try { const ro=new ResizeObserver(()=>{ if(!userMoved) positionSide(); }); ro.observe(anchorEl); ro.observe(side); side.__ro=ro; } catch{}

      // Drag
      (function enableDrag(){
        const head = side.querySelector('#side-pop-head'); if(!head) return;
        let dragging=false, sx=0, sy=0, sl=0, st=0;
        function mv(ev){ if(!dragging) return; const dx=(ev.clientX||0)-sx, dy=(ev.clientY||0)-sy; side.style.left=(sl+dx)+'px'; side.style.top=(st+dy)+'px'; userMoved=true; }
        function up(){ dragging=false; document.removeEventListener('mousemove',mv); document.removeEventListener('mouseup',up); document.body.style.userSelect=''; }
        head.addEventListener('mousedown', (ev)=>{ ev.preventDefault?.(); dragging=true; const r=side.getBoundingClientRect(); sx=ev.clientX||0; sy=ev.clientY||0; sl=r.left; st=r.top; document.addEventListener('mousemove',mv); document.addEventListener('mouseup',up); document.body.style.userSelect='none'; });
      })();

      // Reset e Close
      side.querySelector('#side-pop-reset')?.addEventListener('click', ()=>{ userMoved=false; positionSide(); });
      side.querySelector('#side-pop-close')?.addEventListener('click', ()=>{ try{ side.__ro && side.__ro.disconnect && side.__ro.disconnect(); side.remove(); }catch{} });

    } catch(e){ console.warn('openSideImagePopoverFor falhou', e); }
  };
})();
