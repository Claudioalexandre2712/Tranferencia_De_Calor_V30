            // ========== UTILITÁRIOS ==========
            const fmt = (v,d=4)=> (isFinite(v)? Number(v).toFixed(d):'—');
            const fmtExp = (v,d=3)=> (isFinite(v)? Number(v).toExponential(d):'—');
            
            // ========== DADOS PRINCIPAIS ==========
            const Rtot = result.R_total;
            const hasQ = (result.q!=null && isFinite(result.q));
            const qv = hasQ? result.q: (auxiliaryInputs.qKnown||null);
            const deltaT = (isFinite(result.deltaT)? result.deltaT : (hasQ? (result.q*Rtot): null));
            const Tin = boundaryTemps.T_in;
            const Tout = boundaryTemps.T_out;
            const Aplan = (selectedGeometry==='planar')? (planarParams.A||1): null;
            const U = (selectedGeometry==='planar' && isFinite(Rtot) && Aplan>0)? (1/(Rtot*Aplan)) : null;
            const UA = isFinite(Rtot)? (1/Rtot) : null;
            
            // Filtros de camadas
            const allLayers = result.layers||[];
            const finned = allLayers.filter(l=> l && l.kind==='finned' && l.details);
            const solidLayers = allLayers.filter(l=> l && (l.kind==='solid' || l.kind==='conduction'));
            const fluidLayers = allLayers.filter(l=> l && (l.kind==='fluid' || l.kind==='convection'));
            
            // Percentual de contribuição
            const perc = (Lr)=> (isFinite(Lr.R)&&isFinite(Rtot)&&Rtot>0? (Lr.R/Rtot*100): null);
            
            // ========== HTML PRINCIPAL ==========
            let h = '';
            h += `<div style='font-family:system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif; background:#f8f9fa; padding:20px; border-radius:12px; max-width:1200px; margin:16px auto; line-height:1.4;'>`;
            
            // ═══════════════════════════════════════════════════════════
            // 📊 CABEÇALHO - Resultados do Cálculo Térmico
            // ═══════════════════════════════════════════════════════════
            h += `<div style='text-align:center; margin-bottom:24px;'>`+
                 `<h1 style='margin:0 0 8px; font-size:1.8rem; font-weight:700; color:#1976d2;'>📊 Resultados do Cálculo Térmico</h1>`+
                 `<p style='margin:0 0 12px; font-size:1rem; color:#666;'>Análise completa das resistências térmicas e transferência de calor</p>`+
                 `<div style='background:#e3f2fd; display:inline-block; padding:8px 16px; border-radius:20px; font-size:0.9rem; color:#1976d2; font-weight:600;'>`+
                 `<strong>Geometria:</strong> ${selectedGeometry==='planar'?'Planar':'Cilíndrica'}${Aplan?' (A = '+fmt(Aplan,2)+' m²)':''}`+
                 `</div></div>`;
            
            // ═══════════════════════════════════════════════════════════
            // CARDS DE MÉTRICAS PRINCIPAIS
            // ═══════════════════════════════════════════════════════════
            h += `<div style='display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:16px; margin-bottom:24px;'>`;
            
            // 🔥 Card: Resistência Total
            h += `<div style='background:#fff; border-radius:12px; padding:18px; box-shadow:0 2px 8px rgba(0,0,0,0.1); border-left:4px solid #f44336;'>`+
                 `<div style='display:flex; align-items:center; gap:12px; margin-bottom:10px;'>`+
                 `<div style='background:#ffebee; color:#f44336; width:40px; height:40px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:1.2rem;'>🔥</div>`+
                 `<div style='font-size:0.75rem; text-transform:uppercase; letter-spacing:0.5px; color:#999; font-weight:600;'>Resistência Térmica Total</div>`+
                 `</div>`+
                 `<div style='font-size:1.6rem; font-weight:700; color:#f44336; margin-bottom:4px;'>R<sub>total</sub> = ${fmt(Rtot,4)} K/W</div>`+
                 `<div style='font-size:0.8rem; color:#666;'>Oposição total ao fluxo de calor</div>`+
                 `</div>`;
            
            // ⚡ Card: Taxa de Transferência
            if(hasQ && qv!=null){
                h += `<div style='background:#fff; border-radius:12px; padding:18px; box-shadow:0 2px 8px rgba(0,0,0,0.1); border-left:4px solid #ff9800;'>`+
                     `<div style='display:flex; align-items:center; gap:12px; margin-bottom:10px;'>`+
                     `<div style='background:#fff3e0; color:#ff9800; width:40px; height:40px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:1.2rem;'>⚡</div>`+
                     `<div style='font-size:0.75rem; text-transform:uppercase; letter-spacing:0.5px; color:#999; font-weight:600;'>Taxa de Transferência</div>`+
                     `</div>`+
                     `<div style='font-size:1.6rem; font-weight:700; color:#ff9800; margin-bottom:4px;'>q = ${fmt(qv,2)} W</div>`+
                     `<div style='font-size:0.8rem; color:#666;'>ΔT = ${deltaT!=null?fmt(deltaT,2):'—'} °C</div>`+
                     `</div>`;
            }
            
            // 📐 Card: Coeficiente Global U
            if(selectedGeometry==='planar' && U!=null){
                h += `<div style='background:#fff; border-radius:12px; padding:18px; box-shadow:0 2px 8px rgba(0,0,0,0.1); border-left:4px solid #2196f3;'>`+
                     `<div style='display:flex; align-items:center; gap:12px; margin-bottom:10px;'>`+
                     `<div style='background:#e3f2fd; color:#2196f3; width:40px; height:40px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:1.2rem;'>📐</div>`+
                     `<div style='font-size:0.75rem; text-transform:uppercase; letter-spacing:0.5px; color:#999; font-weight:600;'>Coeficiente Global</div>`+
                     `</div>`+
                     `<div style='font-size:1.6rem; font-weight:700; color:#2196f3; margin-bottom:4px;'>U = ${fmt(U,2)} W/(m²·K)</div>`+
                     `<div style='font-size:0.8rem; color:#666;'>Transferência por unidade de área</div>`+
                     `</div>`;
            }
            
            // 🔧 Card: Condutância Térmica UA
            if(UA!=null){
                h += `<div style='background:#fff; border-radius:12px; padding:18px; box-shadow:0 2px 8px rgba(0,0,0,0.1); border-left:4px solid #9c27b0;'>`+
                     `<div style='display:flex; align-items:center; gap:12px; margin-bottom:10px;'>`+
                     `<div style='background:#f3e5f5; color:#9c27b0; width:40px; height:40px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:1.2rem;'>🔧</div>`+
                     `<div style='font-size:0.75rem; text-transform:uppercase; letter-spacing:0.5px; color:#999; font-weight:600;'>Condutância Térmica</div>`+
                     `</div>`+
                     `<div style='font-size:1.6rem; font-weight:700; color:#9c27b0; margin-bottom:4px;'>UA = ${fmt(UA,2)} W/K</div>`+
                     `<div style='font-size:0.8rem; color:#666;'>Capacidade de condução global</div>`+
                     `</div>`;
            }
            
            h += `</div>`; // Fecha grid de cards
            
            // ═══════════════════════════════════════════════════════════
            // FÓRMULAS DOS COEFICIENTES
            // ═══════════════════════════════════════════════════════════
            if(U!=null || UA!=null){
                h += `<div style='background:#fff; border-radius:10px; padding:16px 20px; margin-bottom:20px; box-shadow:0 2px 8px rgba(0,0,0,0.1);'>`+
                     `<div style='font-size:0.9rem; color:#555; line-height:1.6; font-family:ui-monospace,Consolas,monospace;'>`;
                if(U!=null){
                    h += `<div style='margin-bottom:10px; padding:10px; background:#f5f5f5; border-radius:6px;'><strong style='color:#2196f3;'>📐 Fórmula de U</strong><br>`+
                         `U = 1/(R<sub>total</sub>·A) = 1/(${fmt(Rtot,4)}·${fmt(Aplan,4)}) = ${fmt(U,4)} W/m²·K</div>`;
                }
                if(UA!=null){
                    h += `<div style='padding:10px; background:#f5f5f5; border-radius:6px;'><strong style='color:#9c27b0;'>🔧 Fórmula de UA</strong><br>`+
                         `UA = 1/R<sub>total</sub> = 1/(${fmt(Rtot,4)}) = ${fmt(UA,4)} W/K</div>`;
                }
                h += `</div></div>`;
            }
            
            // ═══════════════════════════════════════════════════════════
            // 🧊 SUPERFÍCIES ALETADAS (se houver)
            // ═══════════════════════════════════════════════════════════
            if(finned.length > 0) {
                h += `<div style='background:#fff; border-radius:10px; padding:20px; margin-bottom:20px; box-shadow:0 2px 8px rgba(0,0,0,0.1); border-left:4px solid #4caf50;'>`+
                     `<h3 style='margin:0 0 16px; color:#2e7d32; font-size:1.3rem; display:flex; align-items:center; gap:8px;'>`+
                     `🧊 Superfícies Aletadas – Parâmetros Geométricos & Desempenho</h3>`+
                     `<p style='margin:0 0 16px; color:#666; font-size:0.9rem;'>Derivações completas para cada grupo de aletas e grandezas globais equivalentes</p>`;
                
                finned.forEach((fl,idx)=>{
                    const d = fl.details||{};
                    const isPin = !!d.is_pin;
                    const label = fl.label || `Grupo de Aletas (Camada Série ${idx+1})`;
                    
                    h += `<div style='background:#f8f9fa; border:1px solid #e0e0e0; border-radius:8px; padding:16px; margin-bottom:16px;'>`+
                         `<div style='margin-bottom:12px;'><strong style='color:#2e7d32; font-size:1.1rem;'>${label}</strong><br>`+
                         `<span style='color:#666; font-size:0.9rem;'>R = ${fmt(fl.R,4)} K/W</span></div>`;
                    
                    // Parâmetros Básicos
                    h += `<div style='margin-bottom:12px;'><strong style='color:#2e7d32;'>Parâmetros Básicos</strong><br>`+
                         `<div style='font-family:monospace; font-size:0.85rem; color:#555; line-height:1.4;'>`;
                    if(isPin) {
                        h += `D = ${fmt(d.t||d.t_fin,4)} m; L = ${fmt(d.L||d.L_fin,4)} m<br>`+
                             `A_tr = π·D²/4 = ${fmtExp(d.A_c||d.A_tr,3)} m²<br>`+
                             `P = π·D = ${fmt(d.P,5)} m`;
                    } else {
                        h += `L = ${fmt(d.L||d.L_fin,4)} m; W = ${fmt(d.w||d.w_fin,4)} m; t = ${fmt(d.t||d.t_fin,4)} m<br>`+
                             `A_tr = W·t = ${fmtExp(d.A_c||d.A_tr,3)} m²<br>`+
                             `P = 2(W+t) = ${fmt(d.P,5)} m`;
                    }
                    h += `</div></div>`;
                    
                    // Uma Aleta
                    h += `<div style='margin-bottom:12px;'><strong style='color:#2e7d32;'>Uma Aleta</strong><br>`+
                         `<div style='font-family:monospace; font-size:0.85rem; color:#555; line-height:1.4;'>`+
                         `A_aleta = P·L = ${fmtExp(d.A_f/(d.N||1),3)} m²<br>`+
                         `m = sqrt(h·P/(k·A_tr)) = √(${fmt(d.h||45,1)}·${fmt(d.P,4)}/(${fmt(d.k||237,1)}·${fmtExp(d.A_c||d.A_tr,3)})) = ${fmt(d.m,4)}<br>`+
                         `mL = ${fmt(d.mL||d.m*(d.L||d.L_fin),4)}<br>`+
                         `η_a = tanh(mL)/(mL) = ${fmt(d.eta_f,4)}`+
                         `</div></div>`;
                    
                    // Superfície Completa
                    h += `<div style='margin-bottom:12px;'><strong style='color:#2e7d32;'>Superfície Completa</strong><br>`+
                         `<div style='font-family:monospace; font-size:0.85rem; color:#555; line-height:1.4;'>`+
                         `N = ${d.N||'—'}<br>`+
                         `A_a = N·A_aleta = ${fmtExp(d.A_f,3)} m²<br>`+
                         `A_b = A_base_total - N·A_tr ≈ ${fmtExp(d.A_b,3)} m²<br>`+
                         `A_t = A_a + A_b = ${fmtExp(d.A_t||d.A_total,3)} m²<br>`+
                         `η_0 = 1 - (A_a/A_t)(1-η_a) = ${fmt(d.eta_0||d.eta_o,4)}`+
                         `</div></div>`;
                    
                    // Desempenho / Calor
                    if(hasQ) {
                        const Tb = d.T_b || (Tin || 40);
                        const Tinf = d.T_inf || (Tout || 25);
                        h += `<div style='margin-bottom:8px;'><strong style='color:#2e7d32;'>Desempenho / Calor</strong><br>`+
                             `<div style='font-family:monospace; font-size:0.85rem; color:#555; line-height:1.4;'>`+
                             `T_b ≈ ${fmt(Tb,2)}°C<br>`+
                             `T_∞ ≈ ${fmt(Tinf,2)}°C<br>`+
                             `q_t = η_0·h·A_t·(T_b - T_∞) = ${fmt(qv,4)} W<br>`+
                             `q (série) = ${fmt(qv,4)} W<br>`+
                             `q_a (por aleta) ≈ ${d.N? fmt(qv/(d.N),4):'—'}<br>`+
                             `R_{t,o} = 1/(η_0·h·A_t) = ${fmt(fl.R,4)} K/W`+
                             `</div></div>`;
                    }
                    
                    h += `<div style='font-size:0.8rem; color:#666; font-style:italic;'>Notas: A_aleta baseada em P·L (modelo pedido).</div>`;
                    h += `</div>`;
                });
                
                h += `</div>`;
            }
            
            // ═══════════════════════════════════════════════════════════
            // 🧮 ANÁLISE POR CAMADA INDIVIDUAL
            // ═══════════════════════════════════════════════════════════
            h += `<div style='background:#fff; border-radius:10px; padding:20px; margin-bottom:20px; box-shadow:0 2px 8px rgba(0,0,0,0.1); border-left:4px solid #5e35b1;'>`+
                 `<h3 style='margin:0 0 16px; color:#4527a0; font-size:1.3rem; display:flex; align-items:center; gap:8px;'>`+
                 `🧮 Análise por Camada Individual</h3>`+
                 `<p style='margin:0 0 16px; color:#666; font-size:0.9rem;'>Resistências térmicas detalhadas e substituições numéricas</p>`;
            
            // Lista de camadas com detalhes
            allLayers.forEach((Lr,i)=>{
                const p = perc(Lr);
                const layerIcon = Lr.kind==='finned'?'❄️':Lr.kind==='fluid'?'💧':'🧱';
                const layerType = Lr.kind==='finned'?'Superfícies Aletadas':Lr.kind==='fluid'?'Fluido':'Sólido';
                const layerNum = i+1;
                
                h += `<div style='background:#f8f9fa; border:1px solid #e0e0e0; border-radius:8px; padding:12px; margin-bottom:12px;'>`+
                     `<div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;'>`+
                     `<div><strong style='color:#4527a0; font-size:1rem;'>${layerIcon} ${layerType} (${layerNum})</strong><br>`+
                     `<span style='color:#666; font-size:0.85rem;'>${Lr.label||('Camada '+layerNum)}</span></div>`+
                     `<div style='text-align:right;'><div style='color:#4527a0; font-weight:700; font-size:1.1rem;'>R= ${fmt(Lr.R,4)} K/W</div>`+
                     `<div style='color:#666; font-size:0.8rem;'>Contrib.= ${p?fmt(p,2):'—'} %</div></div>`+
                     `</div>`;
                
                // Detalhes específicos por tipo
                if(Lr.kind==='finned' && Lr.details) {
                    const d = Lr.details;
                    h += `<div style='font-size:0.85rem; color:#555; line-height:1.4; margin-bottom:8px;'>`+
                         `w=${fmt(d.w||d.w_fin,4)} m | t=${fmt(d.t||d.t_fin,4)} m | L=${fmt(d.L||d.L_fin,3)} m<br>`+
                         `η_f=${fmt(d.eta_f,3)} | η₀=${fmt(d.eta_0||d.eta_o,3)}<br>`+
                         `A_t=${fmt(d.A_t||d.A_total,3)} m² (A_f=${fmt(d.A_f,3)} m²)<br>`+
                         `m=${fmt(d.m,3)} (mL=${fmt(d.mL||d.m*(d.L||d.L_fin),3)})`+
                         `</div>`;
                } else if(Lr.kind==='solid' && Lr.details) {
                    const d = Lr.details;
                    h += `<div style='font-size:0.85rem; color:#555; line-height:1.4; margin-bottom:8px;'>`+
                         `L=${fmt(d.L||Lr.thickness,4)} m | k=${fmt(d.k||Lr.conductivity,2)} W/m·K | A=${fmt(Aplan,4)} m²`+
                         `</div>`;
                } else if(Lr.kind==='fluid' && Lr.details) {
                    const d = Lr.details;
                    h += `<div style='font-size:0.85rem; color:#555; line-height:1.4; margin-bottom:8px;'>`+
                         `h=${fmt(d.h||Lr.h,2)} W/m²·K | A=${fmt(Aplan,4)} m²`+
                         `</div>`;
                }
                
                // Fórmula da resistência
                const formula = Lr.kind==='finned'? 'R = 1/(η₀·h·A_t), P=2(w+t), A_c=w·t, m=√(hP/(kA_c))' :
                              Lr.kind==='fluid'? 'R = 1/(h·A)' : 'R = L/(k·A) + R_cont';
                const substitution = Lr.subst || Lr.formula || `R = ${fmt(Lr.R,4)} K/W`;
                
                h += `<div style='font-size:0.8rem; color:#666; font-family:monospace; background:#f0f0f0; padding:6px 8px; border-radius:4px;'>`+
                     `${formula}<br>${substitution}</div>`;
                
                h += `</div>`;
            });
            
            // Tabela resumo
            h += `<div style='margin-top:16px;'><strong style='color:#4527a0; font-size:1rem;'>📋 Tabela Resumo:</strong></div>`+
                 `<div style='overflow-x:auto; margin-top:8px;'>`+
                 `<table style='width:100%; border-collapse:collapse; font-size:0.85rem; background:#fff;'>`+
                 `<thead><tr style='background:#5e35b1; color:#fff;'>`+
                 `<th style='text-align:left; padding:8px 10px; font-weight:600;'>🏷️ Camada</th>`+
                 `<th style='text-align:left; padding:8px 10px; font-weight:600;'>📐 Fórmula</th>`+
                 `<th style='text-align:left; padding:8px 10px; font-weight:600;'>🔢 Substituição</th>`+
                 `<th style='text-align:right; padding:8px 10px; font-weight:600;'>⚡ R (K/W)</th>`+
                 `<th style='text-align:right; padding:8px 10px; font-weight:600;'>%</th>`+
                 `</tr></thead><tbody>`;
            
            allLayers.forEach((Lr,i)=>{
                const p = perc(Lr);
                const bg = i%2? '#fff':'#f9f9f9';
                const isBottleneck = p!=null && p >= 30;
                const layerIcon = Lr.kind==='finned'?'🛠️':Lr.kind==='fluid'?'💧':'🧱';
                const layerLabel = Lr.label||('Camada '+(i+1));
                const formula = Lr.kind==='finned'? 'R = 1/(η₀·h·A_t)' :
                              Lr.kind==='fluid'? 'R = 1/(h·A)' : 'R = L/(k·A) + R_cont';
                const substitution = Lr.subst || `${fmt(Lr.R,4)}`;
                
                h += `<tr style='background:${bg}; ${isBottleneck?"border-left:3px solid #ff5722;":""}'>` +
                     `<td style='padding:6px 10px;'>${layerIcon}<br>${layerLabel}</td>`+
                     `<td style='padding:6px 10px; font-family:monospace; font-size:0.8rem;'>${formula}</td>`+
                     `<td style='padding:6px 10px; font-family:monospace; font-size:0.8rem;'>${substitution}</td>`+
                     `<td style='padding:6px 10px; text-align:right; font-family:monospace; font-weight:600;'>${fmt(Lr.R,4)}</td>`+
                     `<td style='padding:6px 10px; text-align:right; font-weight:${isBottleneck?"700":"400"}; color:${isBottleneck?"#ff5722":"#555"};'>${p?fmt(p,2):'—'}</td>`+
                     `</tr>`;
            });
            
            h += `</tbody></table></div>`;
            h += `</div>`;
            
            // ═══════════════════════════════════════════════════════════
            // 🧾 EXPLICAÇÃO DIDÁTICA PASSO A PASSO
            // ═══════════════════════════════════════════════════════════
            h += `<div style='background:#fff; border-radius:10px; padding:20px; margin-bottom:20px; box-shadow:0 2px 8px rgba(0,0,0,0.1); border-left:4px solid #ff5722;'>`+
                 `<h3 style='margin:0 0 16px; color:#d84315; font-size:1.3rem; display:flex; align-items:center; gap:8px;'>`+
                 `🧾 Explicação Didática Passo a Passo</h3>`;
            
            // Etapa 1 - Condução nas Camadas Sólidas
            if(solidLayers.length > 0) {
                h += `<div style='background:#fff3e0; border:1px solid #ffb74d; border-radius:8px; padding:12px; margin-bottom:12px;'>`+
                     `<div style='font-weight:700; color:#e65100; margin-bottom:8px;'>Etapa 1 – Condução nas Camadas Sólidas</div>`;
                
                solidLayers.forEach((sl,i)=>{
                    const det = sl.details||{};
                    const L = det.L || sl.thickness;
                    const k = det.k || sl.conductivity;
                    h += `<div style='font-family:monospace; font-size:0.85rem; color:#bf360c; margin-bottom:4px;'>`+
                         `R_${String.fromCharCode(65+i)} = L_${String.fromCharCode(65+i)}/(k_${String.fromCharCode(65+i)}·A) ≈ ${fmt(L,4)}/(${fmt(k,3)}·${fmt(Aplan,4)}) = ${fmt(sl.R,4)} K/W</div>`;
                });
                h += `</div>`;
            }
            
            // Etapa 2 - Superfície Aletada
            if(finned.length > 0) {
                h += `<div style='background:#e8f5e9; border:1px solid #81c784; border-radius:8px; padding:12px; margin-bottom:12px;'>`+
                     `<div style='font-weight:700; color:#2e7d32; margin-bottom:8px;'>Etapa 2 – Superfície Aletada (Aletas ${finned[0].details&&finned[0].details.is_pin?'Cilíndricas':'Retangulares'})</div>`+
                     `<div style='font-family:monospace; font-size:0.85rem; color:#1b5e20; line-height:1.4;'>`;
                
                const d = finned[0]?.details||{};
                if(d.is_pin) {
                    h += `A_tr = π·D²/4 → P = π·D<br>`;
                } else {
                    h += `A_tr = w·t → P = 2(w+t)<br>`;
                }
                h += `m = √(h·P/(k·A_c)) = ${fmt(d.m,4)}<br>`+
                     `η_f = tanh(mL)/(mL) = ${fmt(d.eta_f,4)} (mL=${fmt(d.mL||d.m*(d.L||d.L_fin),4)})<br>`+
                     `A_f = N·A_aleta, A_b = A_base − N·A_tr → A_t = A_b + A_f = ${fmt(d.A_b,4)} + ${fmt(d.A_f,4)} = ${fmt(d.A_t||d.A_total,4)}<br>`+
                     `η₀ = 1 − (A_f/A_t)(1 − η_f) = ${fmt(d.eta_0||d.eta_o,4)}<br>`+
                     `R_{t,o} = 1/(η₀·h·A_t) = 1/(${fmt(d.eta_0||d.eta_o,4)}·${fmt(d.h||45,1)}·${fmt(d.A_t||d.A_total,4)}) = ${fmt(finned[0].R,4)} K/W`;
                h += `</div></div>`;
            }
            
            // Etapa 3 - Soma das Resistências
            h += `<div style='background:#e1f5fe; border:1px solid #4fc3f7; border-radius:8px; padding:12px; margin-bottom:12px;'>`+
                 `<div style='font-weight:700; color:#0277bd; margin-bottom:8px;'>Etapa 3 – Soma das Resistências</div>`+
                 `<div style='font-family:monospace; font-size:0.85rem; color:#01579b;'>`+
                 `R_total = ${allLayers.map((l,i)=>`R_${String.fromCharCode(65+i)}`).join(' + ')}<br>`+
                 `${allLayers.map(l=>fmt(l.R,4)).join(' + ')} = ${fmt(Rtot,4)} K/W`+
                 `</div></div>`;
            
            // Etapa 4 - Taxa de Transferência
            if(hasQ) {
                h += `<div style='background:#fce4ec; border:1px solid #f48fb1; border-radius:8px; padding:12px; margin-bottom:8px;'>`+
                     `<div style='font-weight:700; color:#c2185b; margin-bottom:8px;'>Etapa 4 – Taxa de Transferência de Calor</div>`+
                     `<div style='font-family:monospace; font-size:0.85rem; color:#ad1457;'>`+
                     `q = ΔT / R_total = ${fmt(deltaT,4)} / ${fmt(Rtot,4)} = ${fmt(qv,4)} W`+
                     `</div></div>`;
            }
            
            h += `<div style='font-size:0.8rem; color:#666; font-style:italic; margin-top:12px;'>`+
                 `Assumido regime permanente, 1D, propriedades constantes e ponta de aleta desprezada (L_c≈L). `+
                 `Ajuste conforme condições reais (contato, radiação adicional, ponta corrigida etc.).</div>`;
            
            h += `</div>`;
            
            // ═══════════════════════════════════════════════════════════
            // 📐 EQUAÇÕES FUNDAMENTAIS
            // ═══════════════════════════════════════════════════════════
            h += `<div style='background:#fff; border-radius:10px; padding:20px; margin-bottom:20px; box-shadow:0 2px 8px rgba(0,0,0,0.1); border-left:4px solid #607d8b;'>`+
                 `<h3 style='margin:0 0 16px; color:#37474f; font-size:1.3rem; display:flex; align-items:center; gap:8px;'>`+
                 `📐 Equações Fundamentais</h3>`+
                 `<p style='margin:0 0 16px; color:#666; font-size:0.9rem;'>Relações matemáticas governantes e validação dos cálculos</p>`;
            
            // Soma de resistências
            h += `<div style='background:#f5f5f5; border:1px solid #bdbdbd; border-radius:6px; padding:12px; margin-bottom:12px; font-family:monospace; font-size:0.9rem;'>`+
                 `<strong style='color:#37474f;'>🔗 [Eq. G1] Soma de resistências:</strong><br>`+
                 `R_total = ${allLayers.map(l=>fmt(l.R,4)).join(' + ')} = ${fmt(Rtot,4)} K/W`+
                 `</div>`;
            
            // Quedas por camada (se houver q)
            if(hasQ) {
                h += `<div style='background:#f5f5f5; border:1px solid #bdbdbd; border-radius:6px; padding:12px; margin-bottom:12px; font-family:monospace; font-size:0.9rem;'>`+
                     `<strong style='color:#37474f;'>📊 [Eq. G3] Quedas por camada:</strong><br>`+
                     `ΔT_i = q·R_i<br>`;
                
                allLayers.forEach((Lr,i)=>{
                    const dTi = result.q * Lr.R;
                    h += `ΔT_${i+1} = ${fmt(result.q,2)}·${fmt(Lr.R,4)} = ${fmt(dTi,2)}°C<br>`;
                });
                h += `</div>`;
            }
            
            h += `</div>`;
            
            // ═══════════════════════════════════════════════════════════
            // 🌡️ QUEDAS DE TEMPERATURA POR CAMADA
            // ═══════════════════════════════════════════════════════════
            if(hasQ) {
                h += `<div style='background:#fff; border-radius:10px; padding:20px; margin-bottom:20px; box-shadow:0 2px 8px rgba(0,0,0,0.1); border-left:4px solid #ff7043;'>`+
                     `<h3 style='margin:0 0 16px; color:#d84315; font-size:1.3rem; display:flex; align-items:center; gap:8px;'>`+
                     `🌡️ Quedas de Temperatura por Camada</h3>`+
                     `<p style='margin:0 0 16px; color:#666; font-size:0.9rem;'>Distribuição das quedas de temperatura ΔT_i através do sistema</p>`;
                
                // Tabela de quedas
                h += `<div style='overflow-x:auto;'>`+
                     `<table style='width:100%; border-collapse:collapse; font-size:0.85rem; background:#fff;'>`+
                     `<thead><tr style='background:#ff7043; color:#fff;'>`+
                     `<th style='text-align:left; padding:8px 10px; font-weight:600;'>🏷️ Camada</th>`+
                     `<th style='text-align:left; padding:8px 10px; font-weight:600;'>📐 Fórmula</th>`+
                     `<th style='text-align:left; padding:8px 10px; font-weight:600;'>🔢 Substituição</th>`+
                     `<th style='text-align:right; padding:8px 10px; font-weight:600;'>🌡️ ΔT_i (°C)</th>`+
                     `</tr></thead><tbody>`;
                
                let maxDeltaT = 0;
                let maxDeltaTLayer = '';
                
                allLayers.forEach((Lr,i)=>{
                    const dTi = result.q * Lr.R;
                    const bg = i%2? '#fff':'#fff3e0';
                    const layerIcon = Lr.kind==='finned'?'🛠️':Lr.kind==='fluid'?'💧':'🧱';
                    const layerLabel = Lr.label||('Camada '+(i+1));
                    
                    if(dTi > maxDeltaT) {
                        maxDeltaT = dTi;
                        maxDeltaTLayer = layerLabel;
                    }
                    
                    h += `<tr style='background:${bg};'>` +
                         `<td style='padding:6px 10px;'>${layerIcon}<br>${layerLabel}</td>`+
                         `<td style='padding:6px 10px; font-family:monospace; font-size:0.8rem;'>ΔT_${i+1} = q·R_${i+1}</td>`+
                         `<td style='padding:6px 10px; font-family:monospace; font-size:0.8rem;'>${fmt(result.q,2)} · ${fmt(Lr.R,4)} = ${fmt(dTi,2)} °C</td>`+
                         `<td style='padding:6px 10px; text-align:right; font-family:monospace; font-weight:600;'>${fmt(dTi,2)}</td>`+
                         `</tr>`;
                });
                
                h += `</tbody></table></div>`;
                
                // Análise das quedas
                h += `<div style='background:#fff3e0; border:1px solid #ffb74d; border-radius:8px; padding:12px; margin-top:16px;'>`+
                     `<div style='font-weight:700; color:#e65100; margin-bottom:8px;'>📊 Análise das Quedas de Temperatura</div>`+
                     `<div style='font-size:0.9rem; color:#bf360c; line-height:1.5;'>`+
                     `Esta análise ajuda a identificar onde a maior parte do ΔT acontece, quais resistências mais impactam o sistema e onde atuar para reduzir R_total ou equilibrar o gradiente de temperatura.<br><br>`+
                     `<strong>🔥 Maior Queda</strong><br>${maxDeltaTLayer}<br>ΔT = ${fmt(maxDeltaT,2)}°C<br>${fmt((maxDeltaT/deltaT)*100,1)}% do total<br>`+
                     `<em>Indica onde ocorre a maior parcela da queda de temperatura. Geralmente é a região com maior resistência.</em><br><br>`+
                     `<strong>⚡ Resistência Dominante</strong><br>${maxDeltaTLayer}<br>${fmt((maxDeltaT/deltaT)*100,1)}%<br>Controla o sistema<br>`+
                     `<em>A camada que concentra >50% da queda de temperatura. Melhorar esta camada tende a reduzir significativamente R_total.</em><br><br>`+
                     `<strong>💡 Recomendações:</strong><br>`+
                     `• Revisar parâmetros da superfície aletada: aumentar N, L ou otimizar t/w para elevar A_f<br>`+
                     `• Aumentar h externo (melhorar fluxo / turbulência) ou usar material de aleta com maior k`+
                     `</div></div>`;
                
                h += `</div>`;
            }
            
            // ═══════════════════════════════════════════════════════════
            // ⚖️ BALANÇO TÉRMICO GLOBAL
            // ═══════════════════════════════════════════════════════════
            h += `<div style='background:#fff; border-radius:10px; padding:20px; margin-bottom:20px; box-shadow:0 2px 8px rgba(0,0,0,0.1); border-left:4px solid #3f51b5;'>`+
                 `<h3 style='margin:0 0 16px; color:#283593; font-size:1.3rem; display:flex; align-items:center; gap:8px;'>`+
                 `⚖️ Balanço Térmico Global</h3>`;
            
            if(hasQ) {
                h += `<div style='background:#e8eaf6; border:1px solid #9fa8da; border-radius:8px; padding:16px; margin-bottom:16px; text-align:center;'>`+
                     `<div style='font-size:1.2rem; font-weight:700; color:#283593; margin-bottom:8px;'>`+
                     `q = ΔT_total / R_total = ${fmt(qv,4)} W</div>`+
                     `<div style='font-size:0.9rem; color:#3f51b5;'>`+
                     `ΔT_total = ${fmt(deltaT,2)} °C • R_total = ${fmt(Rtot,4)} K/W</div>`+
                     `</div>`;
            }
            
            // Temperaturas nas interfaces (se disponível)
            if(Array.isArray(result.interfaces) && result.interfaces.length > 0) {
                h += `<div style='margin-bottom:16px;'><strong style='color:#283593; font-size:1rem;'>Temperaturas nas Interfaces</strong><br>`+
                     `<div style='display:flex; flex-wrap:wrap; gap:8px; margin-top:8px;'>`;
                
                result.interfaces.forEach((T,idx)=>{
                    const label = `T${idx+1}`;
                    const colorTemp = isFinite(T)? (T>=50?'#f44336': T>=30?'#ff9800':'#2196f3') : '#9e9e9e';
                    h += `<div style='background:${colorTemp}; color:#fff; padding:6px 12px; border-radius:16px; font-size:0.8rem; font-weight:600;'>`+
                         `${label}: ${isFinite(T)?fmt(T,2):'—'} °C</div>`;
                });
                
                h += `</div></div>`;
            }
             
            h += `<div style='font-size:0.8rem; color:#666; font-style:italic;'>(resultados são exemplos baseados nos cálculos fornecidos)</div>`;
            h += `</div>`;
            
            // FIM DO RELATÓRIO
            h += `</div>`;
            return h;