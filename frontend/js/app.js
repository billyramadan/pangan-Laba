const $=id=>document.getElementById(id);
const money=n=>{const v=Number(n||0);return (v<0?'-Rp':'Rp')+Math.abs(v).toLocaleString('id-ID',{maximumFractionDigits:0})};
const pct=n=>Number(n||0).toLocaleString('id-ID',{maximumFractionDigits:2})+'%';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function readCookie(name){const m=document.cookie.match(new RegExp('(?:^|; )'+name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'=([^;]*)'));return m?decodeURIComponent(m[1]):''}

// Sisipkan token CSRF (double-submit) pada semua request mutating.
(function(){const orig=window.fetch.bind(window);window.fetch=(url,opts={})=>{const m=String(opts.method||'GET').toUpperCase();const t=readCookie('pangan_csrf');if(t&&m!=='GET'&&m!=='HEAD'){opts={...opts,headers:{...(opts.headers||{}),'X-CSRF-Token':t}}}return orig(url,opts)}})();

// Delegasi klik: gantikan atribut onclick inline (aman untuk CSP script-src 'self').
document.addEventListener('DOMContentLoaded',()=>{
  document.body.addEventListener('click',e=>{
    const el=e.target.closest('[data-action]');
    if(!el)return;
    if(el.dataset.remove){const target=el.closest(el.dataset.remove);if(target)target.remove();e.preventDefault();return}
    const fn=window[el.dataset.action];
    if(typeof fn!=='function')return;
    let args=[];
    if(el.dataset.args){try{args=JSON.parse(el.dataset.args)}catch{}}
    if(el.dataset.confirm&&!window.confirm(el.dataset.confirm))return;
    e.preventDefault();
    fn.apply(null,args);
  });
});

window.addEventListener('error',e=>{try{toast('Error: '+e.message)}catch{}});
window.addEventListener('unhandledrejection',e=>{try{toast('Error: '+(e.reason&&e.reason.message||e.reason))}catch{}});

function toast(s){$('toast').textContent=s;$('toast').classList.remove('hidden');setTimeout(()=>$('toast').classList.add('hidden'),3600)}

const PLANS=[
 {id:'starter',name:'Starter',price:150000,features:['Komoditas tak terbatas','Dashboard dasar']}];

let authState={auth_ready:false,logged_in:false,local_preview:false,user:null,account:null,billing:{}};
let state={commodity:'',variant:'GRU — harga + cuaca + kalender + siklus tanggal',restock:7,lastProfit:null,lastSim:null,history:[],currentQuotes:{}};

function parseVariant(v){const i=v.indexOf(' — ');return {model:v.slice(0,i),features:v.slice(i+3)}}

// ===== Landing =====
function renderLandingPlans(){$('landingPlans').innerHTML=PLANS.map(p=>`<div class="card" style="display:flex;flex-direction:column">${p.id==='pro'?'<span class="pill" style="background:var(--primary);color:#fff;align-self:flex-start;margin-bottom:8px">Paling populer</span>':''}<div style="color:#b94b35;font-size:.72rem;font-weight:800;letter-spacing:.1em">${esc(p.name)}</div><div style="font-size:2rem;font-weight:850;color:var(--primary-dark);letter-spacing:-.02em;margin:6px 0">Rp${p.price.toLocaleString('id-ID')}<span style="font-size:.9rem;font-weight:600;color:var(--muted)">/bulan</span></div><div style="color:var(--muted);font-size:.9rem">${esc(p.features.join(' · '))}</div><button class="btn primary" style="margin-top:14px;width:100%" data-action="landChoosePlan" data-args='["${p.id}"]'>Pilih paket</button></div>`).join('')}

function enterDemo(){
  if(!authState.logged_in||authState.local_preview){startSignup();return}
  if(!authState.access_allowed){showExpiredAccess();return}
  $('accountNotice').classList.add('hidden');$('landing').classList.add('hidden');$('app').classList.remove('hidden');initApp()
}
function startSignup(){
  if(authState.logged_in&&!authState.local_preview){
    if(authState.access_allowed){enterDemo();return}
    showExpiredAccess();document.getElementById('harga').scrollIntoView({behavior:'smooth'});return
  }
  if(authState.auth_ready){location.assign('/auth/login');return}
  toast(authState.oauth_error||'Login Google belum siap. Periksa callback OAuth pada konfigurasi server.')
}
function logoutAccount(){location.assign('/auth/logout')}
function expiredAccessLabel(){return authState.account?.expired_reason==='subscription'?'Langganan berakhir':'Trial berakhir'}
function showExpiredAccess(){
  const notice=$('accountNotice');if(!notice)return
  const label=expiredAccessLabel();
  notice.innerHTML=`<strong>${label}.</strong> Akses dashboard dijeda sampai paket dipilih dan pembayaran dikonfirmasi. Lihat paket di bawah, atau <button class="btn small" type="button" data-action="logoutAccount">Keluar akun</button><div id="accountPaymentStatus" class="status" role="status" aria-live="polite"></div>`;
  notice.classList.remove('hidden');$('landing').classList.remove('hidden');$('app').classList.add('hidden')
}
function updateAccountBadge(){
  const account=authState.account||{};
  const badge=$('accountBadge'),summary=$('accountSummaryText'),actions=$('accountActions');
  if(authState.logged_in&&!authState.local_preview){
    const status=account.status||'trial';
    const label=status==='active'?'Langganan aktif':status==='expired'?expiredAccessLabel():`Trial · ${Number(account.days_remaining||0)} hari tersisa`;
    if(badge)badge.textContent=label;
    if(summary)summary.textContent=`Masuk sebagai ${authState.user?.name||authState.user?.email||'pengguna'}`;
    if(actions)actions.classList.remove('hidden');
  }else{
    if(badge)badge.textContent=authState.local_preview?'Preview lokal':'Belum masuk';
    if(summary)summary.textContent=authState.auth_ready?'Masuk dengan Google untuk membuat akun trial 7 hari.':'Login Google belum dikonfigurasi untuk alamat ini.';
    if(actions)actions.classList.add('hidden');
  }
  fillSideUser();
}
function fillSideUser(){
  const user=authState.user||{};const account=authState.account||{};
  const name=user.name||user.email||'Tamu';
  const letter=name.replace(/[^a-zA-Z0-9]/g,'').charAt(0)||'?';
  const su=$('suName'),sp=$('suPlan'),av=$('avatarLetter');
  if(su)su.textContent=name;
  const status=account.status||(authState.logged_in?'trial':'guest');
  const plan=status==='active'?'Langganan aktif':status==='expired'?'Trial berakhir':authState.logged_in?`Trial · ${Number(account.days_remaining||0)} hari tersisa`:'Belum masuk';
  if(sp)sp.textContent=plan;
  if(av)av.textContent=letter;
}
async function loadAccountState(){
  try{const response=await fetch('/api/bootstrap',{cache:'no-store'});if(!response.ok)return;authState=await response.json();updateAccountBadge();fillOverview();
    const authError=new URLSearchParams(location.search).get('auth_error');
    if(authError){const messages={config:'Login Google belum siap. Periksa URL callback di Google Cloud dan secrets.toml.',cancelled:'Login Google dibatalkan.',state:'Sesi login kedaluwarsa atau tidak cocok. Coba masuk lagi.',email:'Google tidak mengonfirmasi alamat email akun ini.',provider:'Google tidak dapat menyelesaikan login. Coba lagi.'};toast(messages[authError]||messages.provider);history.replaceState({},'',location.pathname)}
    if(authState.logged_in&&!authState.local_preview){
      if(authState.access_allowed||authState.is_admin)enterDemo();else showExpiredAccess();
    }else $('accountNotice').classList.add('hidden');
  }catch{}
}
function fillOverview(){
  const d=authState.data||{};
  const fmt=n=>Number(n||0).toLocaleString('id-ID');
  const set=(id,v)=>{const e=$(id);if(e)e.textContent=v};
  set('ovComm',fmt(d.price_commodities));
  set('ovObs',fmt(d.metric_rows));
  const r=d.date_range||[];set('ovPeriod',r.length>1?r[0].slice(0,4)+'–'+r[1].slice(0,4):'—');
  set('ovSource',`Sumber harga: PIHPS · Wilayah: ${d.region||'Kota Depok'}${r.length>1?' · data '+r[0]+' s.d. '+r[1]:''}.`);
  const user=authState.user||{};
  const first=user.name?user.name.split(' ')[0]:'';
  set('greet',first?`Halo, ${first} — selamat datang`:'Selamat datang');
  set('greetDash',first?`Halo, ${first}`:'Selamat datang');
  if(!d.price_commodities){set('readyLabel','Data harga belum tersedia');set('readyDetail','Admin perlu mengimpor data PIHPS Kota Depok.')}
  else if(Number(d.price_age_days)>7){set('readyLabel','Harga PIHPS perlu diperbarui');set('readyDetail',`Data terakhir berusia ${fmt(d.price_age_days)} hari. Prediksi dan saran beli/tunda akan ditahan sampai data harga terbaru tersedia.`)}
  else if(d.ready){set('readyLabel','Data harga dan model tersedia');set('readyDetail',`${fmt(d.price_commodities)} komoditas · ${fmt(d.metric_rows)} baris evaluasi · ${(authState.models||[]).length} jenis model.`)}
  else{set('readyLabel','Model belum siap');set('readyDetail','Data harga ada. Admin perlu melatih model terlebih dahulu.')}
}
function backToLanding(){$('landing').classList.remove('hidden');$('app').classList.add('hidden')}
function priceBadge(ch){ch=Number(ch)||0;const up=ch>=5,down=ch<=-5;const cls=up?'up':down?'down':'flat';const lab=up?'▲ Naik':down?'▼ Turun':'Stabil';return `<span class="trend-pill ${cls}">${lab} ${ch>=0?'+':''}${ch.toFixed(1)}%</span>`}
function recommendationLabel(value){return typeof value==='string'?value:(value&&typeof value==='object'&&typeof value.recommendation==='string'?value.recommendation:'Beli sesuai kebutuhan')}
function renderHealth(){
  const el=$('healthStrip');if(!el)return;
  const h=state.fullHistory||state.history||[];
  if(!h.length){el.innerHTML=`<div class="card" style="grid-column:1/-1"><p style="color:var(--muted);margin:0">Catatan laba belum ada. Hitung &amp; simpan penjualan menu dulu — ringkasan usaha muncul di sini.</p></div>`;return}
  const rev=h.reduce((a,p)=>a+Number(p.revenue),0);
  const net=h.reduce((a,p)=>a+Number(p.net),0);
  const avg=h.reduce((a,p)=>a+Number(p.margin),0)/h.length;
  const best=[...h].sort((a,b)=>(Number(b.net)-Number(a.net)))[0];
  el.innerHTML=
    `<div class="metric"><div class="l">Total omzet tercatat</div><div class="v">${money(rev)}</div></div>`+
    `<div class="metric"><div class="l">Laba bersih</div><div class="v">${money(net)}</div><div class="d">${net>=0?'untung':'rugi'} · margin ${avg.toFixed(1)}%</div></div>`+
    `<div class="metric"><div class="l">Menu paling untung</div><div class="v" style="font-size:1.05rem">${esc(best.menu)}</div><div class="d">${money(best.net)}</div></div>`+
    `<div class="metric"><div class="l">Total catatan</div><div class="v">${h.length}</div><div class="d">tiap menu dihitung</div></div>`;
}
function downloadAnalysis(){
  const h=state.fullHistory||state.history||[];
  if(!h.length){toast('Belum ada data untuk diunduh');return}
  const cols=['menu','period','portions','revenue','net','margin'];
  const q=v=>'"'+String(v??'').replaceAll('"','""')+'"';
  const text='﻿'+[cols.join(','),...h.map(r=>cols.map(c=>q(r[c])).join(','))].join('\r\n');
  const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type:'text/csv;charset=utf-8'}));a.download='rekap_analisis_menu.csv';a.click();URL.revokeObjectURL(a.href);
}
function goFeature(tab,id){if($('landing')&&!$('landing').classList.contains('hidden')){if(!authState.access_allowed){startSignup();return}enterDemo()}if(tab)showTab(tab);if(id)setTimeout(()=>{const el=$(id);el&&el.scrollIntoView({behavior:'smooth'})},80)}

// ===== Data aktif dari PIHPS dan model tersimpan =====
let live={forecast:null,summary:null,eval:null,error:'',loading:false};
function handleAccessDenied(payload){
  if(!payload||!payload.access_required)return false;
  authState.access_allowed=false;
  authState.account={...(authState.account||{}),status:'expired',access_allowed:false,days_remaining:0,
    expired_reason:payload.expired_reason||authState.account?.expired_reason||'trial'};
  updateAccountBadge();showExpiredAccess();
  return true;
}
async function fetchJSON(url){
  try{const r=await fetch(url,{cache:'no-store'});const j=await r.json().catch(()=>null);if(r.status===402)handleAccessDenied(j);if(!r.ok)return null;return j}catch{return null}
}
async function postJSON(url,data){
  try{const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const j=await r.json().catch(()=>null);if(r.status===402)handleAccessDenied(j);return {ok:r.ok,status:r.status,json:j}}catch{return {ok:false,status:0,json:null}}
}
async function loadLive(){
  const p=parseVariant(state.variant);
  if(!state.commodity){renderSummary();return}
  const q=new URLSearchParams({commodity:state.commodity,model:p.model,features:p.features,restock_days:state.restock});
  live.loading=true;
  try{
    const response=await fetch('/api/forecasts/current?'+q,{cache:'no-store'});
    const d=await response.json().catch(()=>null);
    if(!response.ok){
      live.forecast=null;
      live.error=response.status===404
        ?'Endpoint prediksi tidak ditemukan. Hosting harus menjalankan backend Python PanganLaba.'
        :(d?.error||`Server prediksi merespons HTTP ${response.status}.`);
      state.currentQuotes={};live.summary=null;
    }else if(!d||typeof d!=='object'){
      live.forecast=null;live.error='Server prediksi mengirim respons yang tidak dapat dibaca.';
      state.currentQuotes={};live.summary=null;
    }else{
      live.forecast=d;live.error='';state.currentQuotes=d.quotes||{};
      const selected=d.selected||null;
      live.summary=selected&&selected.current_price?selected:null;
      if(authState.is_admin){
        const ev=await fetchJSON('/api/evaluation?commodity='+encodeURIComponent(state.commodity));
        live.eval=(ev&&ev.details)?ev:null;
      }
    }
  }catch(error){
    live.forecast=null;state.currentQuotes={};live.summary=null;
    live.error='Tidak bisa terhubung ke server prediksi. Pastikan backend PanganLaba berjalan.';
  }finally{
    live.loading=false;
    updateMarginSuggest();
    renderSummary();renderResearch();
  }
}

// ===== App init =====
function fill(sel,vals){const s=$(sel);if(!s)return;s.innerHTML=vals.map(v=>`<option value="${esc(v)}">${esc(v)}</option>`).join('')}
function syncSelects(ids,value){ids.forEach(id=>{const el=$(id);if(el)el.value=value})}
function buildChoices(){
  const dataCommodities=authState.commodities||[];
  const models=authState.models?.length?authState.models:['LSTM','GRU'];
  const features=authState.features?.length?authState.features:['harga saja','harga + cuaca + kalender + siklus tanggal'];
  const fc=(authState.forecast_choices)||[];
  const comms=dataCommodities.length?dataCommodities:[...new Set(fc.map(x=>x.commodity))].filter(Boolean).sort();
  const vpairs=[...new Set(models.flatMap(m=>features.map(f=>`${m} — ${f}`)))];
  fill('commodity',comms);fill('commodityMobile',comms);
  fill('variant',vpairs);fill('variantMobile',vpairs);
  state.commodity=comms[0]||'';
  if(!vpairs.includes(state.variant))state.variant=vpairs[0]||'';
  syncSelects(['commodity','commodityMobile'],state.commodity);
  syncSelects(['variant','variantMobile'],state.variant);
  syncSelects(['restock','restockMobile'],String(state.restock));
  $('researchTab')?.classList.toggle('hidden',!authState.is_admin);
  $('researchSide')?.classList.toggle('hidden',!authState.is_admin);
  $('adminTools')?.classList.toggle('hidden',!authState.is_admin);
  if(authState.is_admin)loadAdminPayments();
}
function initApp(){
  buildChoices();
  ['commodity','commodityMobile'].forEach(id=>$(id).onchange=e=>{
    state.commodity=e.target.value;syncSelects(['commodity','commodityMobile'],state.commodity);loadLive()
  });
  ['variant','variantMobile'].forEach(id=>$(id).onchange=e=>{
    state.variant=e.target.value;syncSelects(['variant','variantMobile'],state.variant);loadLive()
  });
  ['restock','restockMobile'].forEach(id=>$(id).onchange=e=>{
    state.restock=Number(e.target.value);syncSelects(['restock','restockMobile'],String(state.restock));loadLive()
  });
  $('marginSlider').addEventListener('input',updateMarginSuggest);updateMarginSuggest();
  $('tanyaInput').addEventListener('keydown',e=>{if(e.key==='Enter')askPanganLaba()});
  addRecipeRow();
  loadLive();
  loadHistory();
  renderLandingPlans();
  renderHealth();
  fillOverview();
}

async function loadAdminPayments(){
  const status=$('paymentAdminStatus'),summary=$('paymentSummary'),tableBox=$('paymentAdminTable');
  if(!status||!tableBox||!authState.is_admin)return;
  status.textContent='Memuat transaksi…';
  try{
    const response=await fetch('/api/admin/payments',{cache:'no-store'});
    const result=await response.json().catch(()=>({}));
    if(!response.ok)throw new Error(result.error||'Daftar pembayaran gagal dimuat.');
    const items=Array.isArray(result.items)?result.items:[];
    const pending=items.filter(x=>x.payment_status==='pending').length;
    const received=items.filter(x=>x.payment_status==='succeeded').reduce((sum,x)=>sum+Number(x.amount_idr||0),0);
    summary.innerHTML=`<div class="metric"><div class="l">Transaksi tercatat</div><div class="v">${items.length}</div></div><div class="metric"><div class="l">Menunggu pembayaran</div><div class="v">${pending}</div></div><div class="metric"><div class="l">Pembayaran berhasil</div><div class="v">${money(received)}</div></div>`;
    if(!items.length){tableBox.innerHTML='<div class="notice" style="margin-top:10px">Belum ada transaksi. Permintaan paket pengguna akan muncul di sini.</div>';status.textContent='Data diperbarui.';return}
    const rows=items.map(item=>{
      const label={pending:'Menunggu',succeeded:'Berhasil',failed:'Gagal',refunded:'Dikembalikan'}[item.payment_status]||item.payment_status||'—';
      const provider={manual:'Transfer manual',xendit:'Xendit',stripe:'Stripe'}[item.provider]||item.provider||'—';
      const stamp=item.completed_at||item.created_at;
      const date=stamp?new Date(stamp).toLocaleString('id-ID',{dateStyle:'medium',timeStyle:'short'}):'—';
      const action=item.payment_status==='pending'&&item.provider==='manual'
        ?`<button class="btn small" type="button" data-action="confirmManualPayment" data-args='[${Number(item.id)}]'>Konfirmasi</button>`
        :item.payment_status==='pending'&&item.provider==='xendit'?'Menunggu webhook Xendit':'—';
      return `<tr><td>${esc(item.display_name||item.email)}</td><td>${esc(item.email)}</td><td>${esc(item.plan_name||item.plan_id||'—')}</td><td>${money(item.amount_idr)}</td><td>${esc(provider)}</td><td>${esc(item.provider_transaction_id||'—')}</td><td><span class="pill">${esc(label)}</span></td><td>${esc(item.subscription_status||'—')}</td><td>${esc(date)}</td><td>${action}</td></tr>`;
    });
    tableBox.innerHTML=`<div class="tablewrap"><table><thead><tr><th>Pengguna</th><th>Email</th><th>Paket</th><th>Nominal</th><th>Metode</th><th>Referensi</th><th>Status pembayaran</th><th>Status paket</th><th>Waktu</th><th>Aksi</th></tr></thead><tbody>${rows.join('')}</tbody></table></div>`;
    status.textContent=`Menampilkan ${items.length} transaksi terbaru.`;
  }catch(error){status.textContent=error.message||'Daftar pembayaran gagal dimuat.';tableBox.innerHTML=''}
}

async function confirmManualPayment(paymentId){
  if(!authState.is_admin||!Number.isInteger(Number(paymentId))||Number(paymentId)<=0)return;
  if(!window.confirm('Pastikan dana sudah masuk ke rekening sebelum mengaktifkan paket. Konfirmasi pembayaran ini?'))return;
  const status=$('paymentAdminStatus');if(status)status.textContent='Mengonfirmasi pembayaran…';
  const result=await postJSON('/api/admin/confirm-payment',{payment_id:Number(paymentId)});
  if(!result.ok){if(status)status.textContent=result.json?.error||'Pembayaran gagal dikonfirmasi.';return}
  if(status)status.textContent='Pembayaran dikonfirmasi dan paket pengguna diaktifkan.';
  await loadAdminPayments();
}

// ===== Ringkasan (Beranda usaha) =====
function renderSummary(){
  const c=state.commodity;
  if(live.summary){
    const s=live.summary,available=s.status==='ready'&&!s.stale;
    $('evalCaption').textContent=`Harga PIHPS ${c} · terakhir ${s.price_date} (${s.age_days} hari lalu)`;
    $('summaryMetrics').innerHTML=
      `<div class="metric"><div class="l">Harga PIHPS terakhir · Rp/kg</div><div class="v">${money(s.current_price)}</div><div class="d">${esc(s.price_date)}</div></div>`+
      (available?`<div class="metric"><div class="l">Rata-rata prediksi ${state.restock} hari · Rp/kg</div><div class="v">${money(s.forecast_mean)}</div><div class="d">${priceBadge(s.expected_change_pct)}</div></div>`:`<div class="metric"><div class="l">Prediksi</div><div class="v" style="font-size:1rem">Belum tersedia</div><div class="d">${s.stale?'Data melewati batas kesegaran. Perbarui PIHPS.':esc(s.error||'Model belum siap.')}</div></div>`)+
      `<div class="metric"><div class="l">Saran pembelian</div><div class="v" style="font-size:1.1rem">${available?esc(recommendationLabel(s.recommendation)):'Tahan rekomendasi'}</div><div class="d">${available?'Berdasarkan model '+esc(s.model):'Saran perlu harga dan prediksi terbaru'}</div></div>`;
    $('simCaption').textContent=available?`Model ${s.model} · ${s.features} · proyeksi sampai ${s.forecast.at(-1)?.target_date||'—'}.`:'Saran belanja ditahan sampai data harga dan model cukup baru.';
    $('homeChartCaption').textContent=`${c} · harga terakhir ${s.price_date}`;
    drawCurrentChart('homeChart',s);
    return;
  }
  $('evalCaption').textContent=live.error||'Pilih komoditas dan model untuk memuat data.';
  $('summaryMetrics').innerHTML=`<div class="notice" style="grid-column:1/-1">${esc(live.error||'Harga atau model belum tersedia. Periksa unggahan PIHPS dan model terlatih.')}</div>`;
  $('simCaption').textContent='Saran pembelian tidak ditampilkan tanpa data harga dan model yang tersedia.';
  $('homeChartCaption').textContent='Data belum tersedia';emptyChart('homeChart','Grafik akan tampil setelah harga dan model tersedia.');
}
function emptyChart(id,message){const canvas=$(id);if(!canvas)return;const c=prepCanvas(id);if(!c||c===false)return;const{ctx,w,h}=c;ctx.fillStyle='#756a60';ctx.font='14px Inter,sans-serif';ctx.textAlign='center';ctx.fillText(message,w/2,h/2)}
function drawCurrentChart(id,payload){
  const c=prepCanvas(id);if(c===null)return;if(c===false)return void requestAnimationFrame(()=>drawCurrentChart(id,payload));
  const{ctx,w,h}=c,history=payload.history||[],forecast=payload.forecast||[],all=[...history,...forecast];
  const vals=all.map(x=>Number(x.price??x.predicted)).filter(x=>x>0);if(!vals.length){emptyChart(id,'Data grafik tidak tersedia.');return}
  const min=Math.min(...vals)*.96,max=Math.max(...vals)*1.04,L=58,R=14,T=30,B=34,pw=w-L-R,ph=h-T-B;
  ctx.font='600 11px Inter,sans-serif';ctx.textAlign='right';
  for(let i=0;i<4;i++){const y=T+ph*i/3;ctx.strokeStyle='#eee4d8';ctx.beginPath();ctx.moveTo(L,y);ctx.lineTo(w-R,y);ctx.stroke();ctx.fillStyle='#86796c';ctx.fillText(money(max-(max-min)*i/3),L-6,y+4)}
  const point=(v,i)=>[L+pw*i/(all.length-1||1),T+ph*(1-(v-min)/(max-min||1))];
  const hp=history.map((x,i)=>point(Number(x.price),i)),fp=forecast.map((x,i)=>point(Number(x.predicted),history.length+i));
  if(hp.length>1)strokeLine(ctx,hp,'#594236',2.5);
  if(fp.length){if(hp.length){ctx.save();ctx.setLineDash([4,4]);ctx.strokeStyle='#c6aa91';ctx.beginPath();ctx.moveTo(...hp.at(-1));ctx.lineTo(...fp[0]);ctx.stroke();ctx.restore()}if(fp.length>1)strokeLine(ctx,fp,'#E4572E',2.5)}
  ctx.fillStyle='#86796c';ctx.textAlign='center';ctx.font='600 10px Inter,sans-serif';
  all.forEach((row,i)=>{if(i%Math.ceil(all.length/6)===0||i===all.length-1){const date=row.date||row.target_date;ctx.fillText(new Date(date+'T00:00:00').toLocaleDateString('id-ID',{day:'2-digit',month:'short'}),L+pw*i/(all.length-1||1),h-8)}});
  legendItems(ctx,[['Harga PIHPS','#594236'],['Prediksi '+payload.model,'#E4572E']],L,15);
}
function drawLiveChart(id,rows){
  const c=prepCanvas(id);if(c===null)return;if(c===false){return void requestAnimationFrame(()=>drawLiveChart(id,rows))}const{ctx,w,h}=c;
  const actual=rows.map(r=>Number(r.actual||0)).filter(v=>v>0);
  const predicted=rows.map(r=>Number(r.predicted||0)).filter(v=>v>0);
  const all=[...actual,...predicted];if(!all.length)return;
  const min=Math.min(...all)*0.96,max=Math.max(...all)*1.04;
  const dates=rows.map(r=>{try{return new Date(String(r.target_date).slice(0,10)).toLocaleDateString('id-ID',{day:'2-digit',month:'short'})}catch{return ''}});
  const L=56,R=14,T=34,B=34,plotW=w-L-R,plotH=h-T-B;
  ctx.font='600 11px "Plus Jakarta Sans",Inter,sans-serif';ctx.textAlign='right';
  for(let i=0;i<4;i++){const gy=T+plotH*i/3;ctx.strokeStyle='#f0e7db';ctx.beginPath();ctx.moveTo(L,gy);ctx.lineTo(w-R,gy);ctx.stroke();ctx.fillStyle='#9b8f84';ctx.fillText(money(max-(max-min)*i/3),L-6,gy+4)}
  const xy=(vals,i)=>[L+plotW*i/(vals.length-1||1),T+plotH*(1-(vals[i]-min)/(max-min||1))];
  if(actual.length>1){const pts=actual.map((_,i)=>xy(actual,i));fillAreaUnder(ctx,pts,T,plotH,'rgba(89,66,54,.10)','rgba(89,66,54,0)');strokeLine(ctx,pts,'#594236',2.5)}
  if(predicted.length>1)strokeLine(ctx,predicted.map((_,i)=>xy(predicted,i)),'#E4572E',2.5);
  ctx.fillStyle='#9b8f84';ctx.textAlign='center';ctx.font='600 11px "Plus Jakarta Sans",Inter,sans-serif';
  dates.forEach((d,i)=>{const x=L+plotW*i/(dates.length-1||1);ctx.fillText(d,Math.min(Math.max(x,L+16),w-R-16),h-9)});
  legendItems(ctx,[['Harga aktual','#594236'],['Prediksi model','#E4572E']],L,16);
}

// ===== Recipe rows =====
function addRecipeRow(item={}){const row=document.createElement('div');row.className='recipe-row';
  const commodities=authState.commodities||[];
  row.innerHTML=`<select aria-label="Nama bahan">${commodities.map(c=>`<option ${item.commodity===c?'selected':''}>${esc(c)}</option>`).join('')}</select>`+
    `<input aria-label="Takaran gram" type="number" min="0" step="10" placeholder="Takaran / porsi (g)" value="${item.grams||''}">`+
    `<input aria-label="Harga beli Rp/kg" type="number" min="0" step="500" placeholder="Harga beli (Rp/kg)" value="${item.price||''}">`+
    `<button class="remove" type="button" data-remove=".recipe-row">×</button>`;
  $('recipeRows').append(row)}
function recipeData(){return [...$('recipeRows').children].map(r=>({commodity:r.children[0].value,grams:Number(r.children[1].value),price:Number(r.children[2].value)})).filter(x=>x.grams>0)}

// ===== Hitung laba =====
async function calculateProfit(){
  const status=$('profitStatus');status.textContent='Menghitung…';
  const menu=$('menuName').value.trim();const selling=Number($('sellingPrice').value);const portions=Number($('portions').value);
  const rows=recipeData();
  if(!menu){status.textContent='Isi nama menu terlebih dahulu.';return}
  if(selling<=0){status.textContent='Harga jual per porsi harus lebih dari Rp0.';return}
  if(portions<=0){status.textContent='Isi jumlah porsi terjual lebih dari 0.';return}
  if(!rows.length){status.textContent='Tambahkan minimal satu bahan dengan takaran lebih dari 0 gram.';return}
  const p=parseVariant(state.variant);
  const res=await postJSON('/api/profit',{menu_name:menu,selling_price:selling,portions_sold:portions,
        recipe:recipeData().map(r=>({commodity:r.commodity,grams_per_portion:r.grams,actual_price_rp_per_kg:r.price||null})),
        model:p.model,features:p.features,
        restock_days:state.restock,other_cost_per_portion:Number($('otherCost').value),fixed_cost:Number($('fixedCost').value),
        sales_period:$('salesPeriod').value,save_history:$('saveHistory').checked});
  if(!res.ok||!res.json?.report){status.textContent=res.json?.error||'Server tidak dapat menghitung. Periksa koneksi dan harga bahan.';return}
  const r=res.json.report,forecastAvailable=Boolean(r.forecast_available);
  state.lastProfit={net:Number(r.net_profit),revenue:Number(r.revenue),margin:Number(r.net_margin_pct),portions,period:$('salesPeriod').value,menu};
  const be=r.break_even_portions===null?'Belum tercapai':Number(r.break_even_portions).toLocaleString('id-ID')+' porsi';
  const forecastCards=forecastAvailable?`<div class="metric"><div class="l">Modal bahan/porsi pada skenario prediksi</div><div class="v">${money(r.predicted_ingredient_cost_per_portion)}</div></div><div class="metric"><div class="l">Laba pada skenario prediksi</div><div class="v">${money(r.predicted_net_profit)}</div><div class="d">${money(r.predicted_net_profit-r.net_profit)} dibanding acuan</div></div>`:'';
  const notice=forecastAvailable?'Prediksi memakai model dan data terbaru.':`Prediksi laba belum ditampilkan karena data harga/model tidak cukup baru. Laba di atas memakai harga pemasok yang dimasukkan atau harga PIHPS terakhir.`;
  $('profitResult').innerHTML=`<div class="grid3"><div class="metric"><div class="l">Modal bahan per porsi</div><div class="v">${money(r.ingredient_cost_per_portion)}</div></div><div class="metric"><div class="l">Omzet periode ini</div><div class="v">${money(r.revenue)}</div></div><div class="metric"><div class="l">Laba bersih estimasi pada harga acuan</div><div class="v">${money(r.net_profit)}</div></div>${forecastCards}<div class="metric"><div class="l">Margin bersih estimasi</div><div class="v">${Number(r.net_margin_pct).toFixed(1)}%</div></div></div><div class="notice" style="margin-top:10px">${esc(notice)}</div><div style="color:var(--muted);font-size:.9rem;margin-top:10px">Titik impas ${be} · ${portions.toLocaleString('id-ID')} porsi · harga acuan ${esc(r.reference_date||'—')}.</div>`;
  status.textContent=res.json.saved?'Hitungan tersimpan di riwayat akun.':'Hitungan selesai; tidak disimpan ke riwayat.';
  if(res.json.saved)await loadHistory();
}
function renderHistory(){renderHistoryTable(state.history||[])}
function renderAnalysis(){
  const el=$('menuAnalysis');if(!el)return;
  const h=state.fullHistory||[];
  if(!h.length){el.innerHTML='<div class="empty">Belum ada data untuk dianalisis. Hitung laba menu dulu.</div>';return}
  const t=Math.max(1,h.length);
  const totalRev=h.reduce((a,p)=>a+Number(p.revenue),0);
  const totalNet=h.reduce((a,p)=>a+Number(p.net),0);
  const avgMargin=h.reduce((a,p)=>a+Number(p.margin),0)/t;
  const best=[...h].sort((a,b)=>(Number(b.net)-Number(a.net)))[0];
  const worst=[...h].sort((a,b)=>(Number(a.net)-Number(b.net)))[0];
  const groups={};h.forEach(p=>{groups[p.menu]=groups[p.menu]||0;groups[p.menu]+=Number(p.revenue)||0});
  const top=Object.entries(groups).sort((a,b)=>b[1]-a[1]).slice(0,4);
  const maxRev=Math.max(...top.map(x=>x[1]),1);
  const share=top.map(([menu,rev])=>`<div class="share-row"><span>${esc(menu)}</span><div class="share-bar"><i style="width:${(rev/maxRev*100).toFixed(1)}%"></i></div><b>${money(rev)}</b></div>`).join('');
  el.innerHTML=`<div class="grid3">
    <div class="metric"><div class="l">Total omzet tercatat</div><div class="v">${money(totalRev)}</div></div>
    <div class="metric"><div class="l">Total laba bersih</div><div class="v">${money(totalNet)}</div><div class="d">margin rata-rata ${avgMargin.toFixed(1)}%</div></div>
    <div class="metric"><div class="l">Menu paling untung</div><div class="v" style="font-size:1.05rem">${esc(best.menu)}</div><div class="d">${money(best.net)}</div></div>
  </div>
  <div style="color:var(--muted);font-size:.85rem;margin-top:10px">Menu dengan laba terendah: <b>${esc(worst.menu)}</b> (${money(worst.net)}). Pertimbangkan meninjau harga jual atau biaya bahannya.</div>
  <div class="section-title" style="font-size:15px;margin:20px 0 8px">Porsi omzet per menu</div>
  <div class="menu-share">${share}</div>
  <div class="row" style="margin-top:14px"><button class="btn small" data-action="downloadAnalysis">Unduh rekap analisis CSV</button></div>`;
}
function renderHistoryTable(h){
  renderAnalysis();renderHealth();
  if(!h.length){$('historyTable').innerHTML='<div class="empty">Belum ada catatan. Hitung dan simpan penjualan menu untuk mulai membuat riwayat.</div>';return}
  $('historyTable').innerHTML=`<div class="tablewrap"><table><thead><tr><th>Menu</th><th>Periode</th><th>Porsi</th><th>Omzet</th><th>Laba bersih</th><th>Margin</th></tr></thead><tbody>`+
    h.map(p=>`<tr><td>${esc(p.menu)}</td><td>${esc(p.period)}</td><td>${Number(p.portions).toLocaleString('id-ID')}</td><td>${money(Number(p.revenue))}</td><td>${money(Number(p.net))}</td><td>${Number(p.margin).toFixed(1)}%</td></tr>`).join('')+
    `</tbody></table></div>`;
}
async function loadHistory(){
  const d=await fetchJSON('/api/history');
  if(d&&d.items&&d.items.length){
    state.fullHistory=d.items.map(it=>({menu:it.menu_name||'',period:it.period_label||'',portions:Number(it.portions_sold||0),revenue:Number(it.revenue||0),net:Number(it.net_profit||0),margin:Number(it.net_margin_pct||0)}));
    renderHistoryTable(state.fullHistory);return;
  }
  renderHistory();
}
async function downloadHistory(){
  try{const r=await fetch('/api/history.csv',{cache:'no-store'});if(r.ok){const b=await r.blob();const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='riwayat_laba_menu.csv';a.click();URL.revokeObjectURL(a.href);return}}catch{}
  const h=state.history||[];if(!h.length){toast('Belum ada riwayat untuk diunduh');return}const cols=['menu','period','portions','revenue','net','margin'];const q=v=>'"'+String(v??'').replaceAll('"','""')+'"';const text='﻿'+[cols.join(','),...h.map(r=>cols.map(c=>q(r[c])).join(','))].join('\r\n');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type:'text/csv;charset=utf-8'}));a.download='riwayat_laba.csv';a.click();URL.revokeObjectURL(a.href)}

// ===== Geser margin (HPP) =====
function recipeCostPerPortion(){let c=0;for(const r of recipeData()){const ref=r.price>0?r.price:Number(state.currentQuotes[r.commodity]?.current_price||0);c+=r.grams/1000*ref}return c}
function suggestedPrice(marginPct){const c=recipeCostPerPortion(),m=marginPct/100;return m>=1?0:Math.ceil(c/(1-m))}
function updateMarginSuggest(){const c=recipeCostPerPortion(),sug=suggestedPrice(Number($('marginSlider').value));$('marginSuggest').textContent=c>0?'≈ '+money(sug):'Isi takaran bahan dulu'}
function applyMargin(){const c=recipeCostPerPortion();if(c<=0){toast('Isi takaran bahan dulu');return}const sug=suggestedPrice(Number($('marginSlider').value));$('sellingPrice').value=sug;toast('Harga jual diset ke '+money(sug))}

// ===== Tanya PanganLaba =====
function quoteUnavailableMessage(commodity,quote){
  if(live.loading)return 'Data prediksi sedang dimuat. Tunggu sebentar, lalu kirim pertanyaan lagi.';
  if(live.error)return `Prediksi ${commodity} belum bisa diambil dari server. ${live.error}`;
  if(!quote)return `Server belum mengirim data prediksi untuk ${commodity}. Pastikan komoditas dan modelnya tersedia pada dashboard.`;
  const date=quote.price_date||'tanggal tidak tercatat';
  if(quote.stale||quote.status==='stale')return `Harga PIHPS ${commodity} terakhir tercatat ${date} (${Number(quote.age_days||0)} hari lalu). Rekomendasi ditahan karena data melewati batas kesegaran 7 hari. Admin perlu memperbarui data PIHPS.`;
  if(quote.status!=='ready')return `Harga ${commodity} tersedia sampai ${date}, tetapi model belum menghasilkan prediksi. ${quote.error||'Periksa model dan data fitur pada server.'}`;
  return '';
}

function askPanganLaba(){
  const q=$('tanyaInput').value.trim().toLowerCase(),out=$('tanyaResult');
  if(!q){out.innerHTML='<div class="notice">Tulis pertanyaan dulu, misal "prediksi harga beras?".</div>';return}
  let body='',src='Sumber: data PIHPS dan model yang tersedia di dashboard.';
  const comm=[...(authState.commodities||[])].sort((a,b)=>b.length-a.length).find(c=>q.includes(c.toLowerCase()));
  if((q.includes('laba')||q.includes('untung')||q.includes('omzet'))&&state.lastProfit){
    const p=state.lastProfit;
    body=`Menu <b>${esc(p.menu)}</b>: omzet ${money(p.revenue)} dari ${p.portions.toLocaleString('id-ID')} porsi (${esc(p.period).toLowerCase()}), laba bersih estimasi <b>${money(p.net)}</b>, margin ${p.margin.toFixed(1)}%.`;
    src='Sumber: hitungan terakhir dari kalkulator menu, sesuai isian kamu.';
  }else if(comm){
    const quote=state.currentQuotes[comm];
    const issue=quoteUnavailableMessage(comm,quote);
    if(issue)body=issue;
    else body=`Harga PIHPS terakhir ${quote.price_date}: ${money(quote.current_price)}/kg. Rata-rata prediksi ${state.restock} hari: ${money(quote.forecast_mean)}/kg (${Number(quote.expected_change_pct).toFixed(1)}%). Saran model: ${recommendationLabel(quote.recommendation)}.`;
    src=`Sumber: PIHPS Depok ${esc(quote?.price_date||'belum tersedia')} · model ${esc(state.variant)}.`;
  }else if(q.includes('belanja')||q.includes('saran')){
    const quote=state.currentQuotes[state.commodity];
    const issue=quoteUnavailableMessage(state.commodity,quote);
    body=issue||`Untuk ${state.commodity}, model menyarankan ${recommendationLabel(quote.recommendation)}; perubahan prediksi ${Number(quote.expected_change_pct).toFixed(1)}%. Periksa stok dan kebutuhan usaha sebelum memutuskan.`;
    src=`Sumber: PIHPS ${esc(quote?.price_date||'belum tersedia')} · prediksi ${esc(state.variant)}.`;
  }else if(q.includes('margin')){
    body='Margin jual dipakai untuk menyarankan harga jual: harga jual ≈ modal bahan per porsi ÷ (1 − margin). Di halaman Kalkulator laba menu, geser slider Margin untuk melihat saran harganya berubah.';
  }else{
    body='Saya bisa bantu:\n• "Berapa laba menu saya?" — ringkasan laba terakhir.\n• "Prediksi harga <nama komoditas>?" — harga aktual vs prediksi.\n• "Saran belanja?" — rekomendasi beli/tunda untuk komoditas aktif.\n• "Margin?" — cara pakai geser margin.';
  }
  out.innerHTML=`<div style="border:1px solid var(--line);border-radius:10px;background:#fff9f1;padding:12px 14px"><div style="color:var(--muted);font-size:.8rem;margin-bottom:4px"><b>PanganLaba</b> menjawab:</div><div style="white-space:pre-line;line-height:1.6">${esc(body)}</div><div style="color:var(--muted);font-size:.78rem;margin-top:8px">${esc(src)}</div></div>`;
}

// ===== Simulasi =====
async function runSimulation(){
  const status=$('simStatus');status.textContent='Menghitung simulasi…';
  const qty=Number($('simQty').value),wait=Number($('simWait').value);
  const body={commodity:state.commodity,model:parseVariant(state.variant).model,features:parseVariant(state.variant).features,
              cycle_days:state.restock,max_wait_days:wait,quantity_kg:qty};
  const res=await postJSON('/api/simulation',body);
  if(res.ok&&res.json&&res.json.rows&&res.json.rows.length){
    const s=res.json.summary||{},rows=res.json.rows;
    state.lastSim={rows,baseline:Number(s.baseline_cost_rp||0),policy:Number(s.policy_cost_rp||0),
                   savings:Number(s.savings_rp||0),savingsPct:Number(s.savings_pct||0),
                   deferred:Number(s.deferred||0),cycles:rows.length,qty,wait};
    renderSimResult(state.lastSim);
    status.textContent='Simulasi selesai (data server).';return;
  }
  $('simResult').innerHTML=`<div class="notice">${esc(res.json?.error||'Simulasi belum tersedia. Pastikan data evaluasi model sudah dibuat.')}</div>`;
  status.textContent='';
}
function renderSimResult(s){
  $('simResult').innerHTML=
    `<div class="grid4">`+
    `<div class="metric"><div class="l">Belanja rutin</div><div class="v">${money(s.baseline)}</div></div>`+
    `<div class="metric"><div class="l">Belanja strategi</div><div class="v">${money(s.policy)}</div></div>`+
    `<div class="metric"><div class="l">Selisih simulasi</div><div class="v">${money(s.savings)}</div><div class="d">${s.savingsPct>=0?'+':''}${s.savingsPct.toFixed(2)}% vs rutin</div></div>`+
    `<div class="metric"><div class="l">Transaksi ditunda</div><div class="v" style="font-size:1.1rem">${s.deferred} dari ${s.cycles} siklus</div></div>`+
    `</div>`+
    `<div class="tablewrap"><table><thead><tr><th>Siklus</th><th>Hari ditunda</th><th>Belanja rutin (Rp)</th><th>Belanja strategi (Rp)</th><th>Selisih biaya (Rp)</th></tr></thead><tbody>`+
    s.rows.map(r=>`<tr><td>${r.cycle}</td><td>${r.wait_days}</td><td>${money(r.baseline_cost_rp)}</td><td>${money(r.policy_cost_rp)}</td><td>${money(r.savings_rp)}</td></tr>`).join('')+
    `</tbody></table></div>`+
    `<div class="row" style="margin-top:10px"><button class="btn small" data-action="downloadSim">Unduh rincian simulasi CSV</button></div>`;
}
function downloadSim(){if(!state.lastSim)return;const s=state.lastSim;const cols=['cycle','wait_days','baseline_cost_rp','policy_cost_rp','savings_rp'];const q=v=>'"'+String(v??'').replaceAll('"','""')+'"';const text='﻿'+[cols.join(','),...s.rows.map(r=>cols.map(c=>q(r[c])).join(','))].join('\r\n');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type:'text/csv;charset=utf-8'}));a.download='simulasi_pembelian.csv';a.click();URL.revokeObjectURL(a.href)}

// ===== Tab / Navigasi =====
function showTab(name){if(name==='research'&&!authState.is_admin){name='business';toast('Hasil penelitian hanya tersedia untuk admin.')} $('tab-business').classList.toggle('hidden',name!=='business');$('tab-research').classList.toggle('hidden',name!=='research');document.querySelectorAll('.tabs button').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));if(name==='research')renderResearch()}
function goTab(tab,id){showTab(tab);const el=$(id);if(el)el.scrollIntoView({behavior:'smooth'})}
function hidePlans(){const el=$('plansCard');if(el)el.classList.add('hidden')}
function navGo(tab,id){
  showTab(tab);
  document.querySelectorAll('.side button[data-nav]').forEach(b=>b.classList.toggle('active',b.dataset.nav===(id||tab)));
  if(id){const el=$(id);if(el)el.scrollIntoView({behavior:'smooth',block:'start'})}
}

// ===== Penelitian =====
function med(arr){const s=[...arr].sort((a,b)=>a-b);return s.length?(s[(s.length-1)>>1]+s[s.length>>1])/2:0}
function renderResearch(){
  const c=state.commodity;
  const ev=live.eval;
  const details=(ev&&ev.details)||[];
  if(details.length){
    const groups={};
    details.forEach(r=>{const k=String(r.model)+' — '+String(r.features);groups[k]=groups[k]||[];groups[k].push(Number(r.MAE)||0)});
    let bestKey='',bestMAE=Infinity;
    for(const k in groups){const m=groups[k].reduce((a,b)=>a+b)/groups[k].length;if(m<bestMAE){bestMAE=m;bestKey=k}}
    const g=groups[bestKey]||[];
    $('evalMetrics').innerHTML=
      `<div class="metric"><div class="l">Rata-rata MAE terendah</div><div class="v" style="font-size:1.02rem">${esc(bestKey.split(' — ')[0]||'—')} · ${esc(bestKey.split(' — ')[1]||'—')}</div></div>`+
      `<div class="metric"><div class="l">MAE median model ini</div><div class="v">${money(Math.round(med(g)))}/kg</div></div>`+
      `<div class="metric"><div class="l">Komoditas dinilai</div><div class="v">${new Set(details.map(r=>String(r.commodity))).size}</div></div>`+
      `<div class="metric"><div class="l">Baris evaluasi</div><div class="v">${details.length}</div></div>`;
    const rows=details.map(r=>[String(r.commodity),String(r.model),String(r.features),
      money(Math.round(Number(r.MAE)||0)),money(Math.round(Number(r.RMSE)||0)),
      (Number(r.MAPE)||0).toFixed(2).replace('.',',')]);
    $('metricsTable').innerHTML=table(['Komoditas','Model','Fitur','MAE (Rp/kg)','RMSE (Rp/kg)','MAPE (%)'],rows);
    if(ev.summary&&ev.summary.length){
      const rows2=ev.summary.map(s=>[String(s.model),String(s.features),String(s.jumlah_komoditas),
        money(Math.round(Number(s.median_MAE)||0)),money(Math.round(Number(s.median_RMSE)||0)),
        (Number(s.median_MAPE)||0).toFixed(2).replace('.',',')]);
      $('summaryTable').innerHTML=table(['Model','Paket fitur','Jumlah komoditas','Median MAE (Rp/kg)','Median RMSE (Rp/kg)','Median MAPE (%)'],rows2);
    }
    const pairs={};
    details.forEach(r=>{const k=String(r.commodity)+'|'+String(r.model);pairs[k]=pairs[k]||{};pairs[k][String(r.features)]=Number(r.MAE)||0});
    let better=0,count=0;
    for(const k in pairs){const p=pairs[k];const base=p['harga saja'];if(base!==undefined){let improved=false;for(const f in p){if(f!=='harga saja'&&p[f]<base)improved=true}if(improved)better++;count++}}
    $('evalInfo').textContent=count?`Pada data uji, fitur eksternal menurunkan MAE pada ${better} dari ${count} pasangan komoditas–model dibandingkan harga saja. Manfaatnya bergantung komoditas; bandingkan selisih MAE di tabel.`:'Hasil evaluasi tersedia untuk komoditas ini.';
  }else{
    $('evalMetrics').innerHTML='';
    $('evalInfo').textContent=live.error||'Belum ada hasil evaluasi model. Admin perlu melatih model dari data proyek.';
    $('metricsTable').innerHTML='<div class="empty">Hasil evaluasi belum tersedia.</div>';
    $('summaryTable').innerHTML='<div class="empty">Tabel ringkasan akan tampil setelah evaluasi model selesai.</div>';
  }
  $('researchChartCaption').textContent=`${c} · prediksi terkini dari PIHPS dan model tersimpan`;
  drawResearch('researchChart',c,'');
  drawMae('maeChart',c);
}
function table(headers,rows){return `<div class="tablewrap"><table><thead><tr>${headers.map(x=>`<th>${esc(x)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map(x=>`<td>${esc(x)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`}

function prepCanvas(id){
  const canvas=$(id);if(!canvas)return null;
  const ctx=canvas.getContext('2d'),dpr=window.devicePixelRatio||1,w=canvas.clientWidth,h=canvas.clientHeight;
  if(w<10||h<10)return false;
  canvas.width=w*dpr;canvas.height=h*dpr;ctx.scale(dpr,dpr);ctx.clearRect(0,0,w,h);
  return {ctx,w,h};
}
function strokeLine(ctx,pts,color,width){ctx.save();ctx.beginPath();pts.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.strokeStyle=color;ctx.lineWidth=width;ctx.lineJoin='round';ctx.lineCap='round';ctx.stroke();ctx.restore()}
function fillAreaUnder(ctx,pts,T,plotH,start,end){
  if(pts.length<2)return;const base=T+plotH;
  const grad=ctx.createLinearGradient(0,T,0,base);grad.addColorStop(0,start);grad.addColorStop(1,end);
  ctx.save();ctx.beginPath();ctx.moveTo(pts[0][0],base);pts.forEach(([x,y])=>ctx.lineTo(x,y));
  ctx.lineTo(pts[pts.length-1][0],base);ctx.closePath();ctx.fillStyle=grad;ctx.fill();ctx.restore();
}
function roundRectFill(ctx,x,y,w,h,r){if(w<=0)return;ctx.save();ctx.beginPath();ctx.roundRect(x,y,w,h,r);ctx.fill();ctx.restore()}
function legendItems(ctx,items,x,y){
  ctx.save();ctx.font='600 11px "Plus Jakarta Sans",Inter,sans-serif';ctx.textAlign='left';let cx=x;
  items.forEach(([label,color])=>{ctx.fillStyle=color;ctx.beginPath();ctx.roundRect(cx,y+1,10,10,3);ctx.fill();ctx.fillStyle='#756f65';ctx.fillText(label,cx+15,y+10);cx+=ctx.measureText(label).width+20});
  ctx.restore();
}
function drawResearch(id,commodity,origin){
  if(live.forecast?.selected){drawCurrentChart(id,live.forecast.selected);return}
  const c=prepCanvas(id);if(c===null)return;if(c===false){return void requestAnimationFrame(()=>drawResearch(id,commodity,origin))}const{ctx,w,h}=c;
  const fc=(live.forecast&&live.forecast.forecast)||null;
  let actual,predicted,dates;
  if(fc&&fc.length){
    actual=fc.map(r=>Math.max(0,Number(r.actual)||0)).filter(v=>v>0);
    predicted=fc.map(r=>Math.max(0,Number(r.predicted)||0)).filter(v=>v>0);
    dates=fc.map(r=>{try{return new Date(String(r.target_date).slice(0,10)).toLocaleDateString('id-ID',{day:'2-digit',month:'short'})}catch{return ''}});
  }else{emptyChart(id,'Data evaluasi tidak tersedia.');return}
  if(!actual.length||!predicted.length)return;
  const all=[...actual,...predicted];const min=Math.min(...all)*0.96,max=Math.max(...all)*1.04;
  const L=56,R=14,T=34,B=34,plotW=w-L-R,plotH=h-T-B;
  ctx.font='600 11px "Plus Jakarta Sans",Inter,sans-serif';ctx.textAlign='right';
  for(let i=0;i<4;i++){const gy=T+plotH*i/3;ctx.strokeStyle='#f0e7db';ctx.beginPath();ctx.moveTo(L,gy);ctx.lineTo(w-R,gy);ctx.stroke();ctx.fillStyle='#9b8f84';ctx.fillText(money(max-(max-min)*i/3),L-6,gy+4)}
  const xy=(vals,i)=>[L+plotW*i/(vals.length-1||1),T+plotH*(1-(vals[i]-min)/(max-min||1))];
  fillAreaUnder(ctx,actual.map((_,i)=>xy(actual,i)),T,plotH,'rgba(89,66,54,.10)','rgba(89,66,54,0)');
  strokeLine(ctx,actual.map((_,i)=>xy(actual,i)),'#594236',2.5);
  strokeLine(ctx,predicted.map((_,i)=>xy(predicted,i)),'#E4572E',2.5);
  ctx.fillStyle='#9b8f84';ctx.textAlign='center';
  dates.forEach((d,i)=>{const x=L+plotW*i/(dates.length-1);ctx.fillText(d,Math.min(Math.max(x,L+16),w-R-16),h-9)});
  legendItems(ctx,[['Harga aktual','#594236'],['Prediksi model','#E4572E']],L,16);
}
function drawMae(id,commodity){
  const c=prepCanvas(id);if(c===null)return;if(c===false){return void requestAnimationFrame(()=>drawMae(id,commodity))}const{ctx,w,h}=c;
  const det=((live.eval&&live.eval.details)||[]).filter(r=>String(r.commodity)===commodity);
  const price=[],external=[];
  if(det.length){
    ['LSTM','GRU'].forEach(m=>{
      const base=det.find(r=>String(r.model)===m&&String(r.features)==='harga saja');
      const ext=det.filter(r=>String(r.model)===m&&String(r.features)!=='harga saja');
      price.push(base?Number(base.MAE)||0:0);
      external.push(ext.length?med(ext.map(r=>Number(r.MAE)||0)):0);
    });
  }else{ctx.fillStyle='#756a60';ctx.font='14px Inter,sans-serif';ctx.textAlign='center';ctx.fillText('Evaluasi model belum tersedia',w/2,h/2);return}
  const maxError=Math.max(...[...price,...external],1)*1.12;
  const L=64,R=150,T=40,B=18,chartW=w-L-R,row=(h-T-B)/2;
  ctx.font='700 12px "Plus Jakarta Sans",Inter,sans-serif';ctx.textAlign='left';
  ['LSTM','GRU'].forEach((label,i)=>{
    const cy=T+i*row+row/2;const bh=18,gap=6;
    ctx.fillStyle='#5a4d43';ctx.fillText(label,L-58,cy+4);
    const w1=(chartW*0.5)*price[i]/maxError,w2=(chartW*0.5)*external[i]/maxError;
    ctx.fillStyle='#594236';roundRectFill(ctx,L,cy-bh-gap/2,w1,bh,5);
    ctx.fillStyle='#9b8f84';ctx.font='600 11px "Plus Jakarta Sans",Inter,sans-serif';
    ctx.fillText(money(price[i]),L+w1+6,cy-bh-gap/2+13);
    ctx.fillStyle='#E4572E';roundRectFill(ctx,L,cy+gap/2,w2,bh,5);
    ctx.fillStyle='#9b8f84';ctx.fillText(money(external[i]),L+w2+6,cy+gap/2+13);
  });
  legendItems(ctx,[['Harga saja','#594236'],['Harga + fitur eksternal','#E4572E']],L,16);
}

// ===== Feedback form =====
  $('feedbackForm').addEventListener('submit',async e=>{e.preventDefault();const form=e.currentTarget,f=new FormData(form);if(!f.get('consent_anonymous_feedback')){$('feedbackStatus').textContent='Minta persetujuan peserta sebelum menyimpan umpan balik.';return}if(!String(f.get('session_code')||'').trim()){$('feedbackStatus').textContent='Isi kode sesi anonim, bukan nama atau kontak.';return}$('feedbackStatus').textContent='Menyimpan…';const data=Object.fromEntries(f.entries());data.consent_anonymous_feedback=f.get('consent_anonymous_feedback')==='on';const res=await postJSON('/api/feedback',data);$('feedbackStatus').textContent=res.ok?'Umpan balik anonim tersimpan.':(res.json?.error||'Umpan balik gagal disimpan.');if(res.ok)form.reset()});

// ===== Paket saya (mirip render_my_plan) =====
function showMyPlan(){
  const account=authState.account||{};const status=account.status||'preview';const remaining=Number(account.days_remaining||0);
  const statusLabel=status==='active'?'Langganan aktif':status==='expired'?expiredAccessLabel():status==='trial'?'Trial aktif':'Belum masuk';
  const accessLabel=status==='active'?(account.days_remaining===undefined?'Aktif':`${remaining} hari`):status==='trial'?`${remaining} hari`:'Tidak ada akun pelanggan';
  $('plansCard').innerHTML=`<div class="card"><div class="section-label" style="margin-top:0">Paket saya</div><div class="grid2"><div class="metric"><div class="l">Status</div><div class="v" style="font-size:1.1rem">${esc(statusLabel)}</div></div><div class="metric"><div class="l">Sisa akses</div><div class="v" style="font-size:1.1rem">${esc(accessLabel)}</div></div></div><div class="notice">${authState.logged_in?'Status akun ditampilkan dari server.':'Kamu sedang mencoba demo lokal. Masuk dengan Google untuk membuat akun trial dan mengajukan paket.'}</div><div class="row" style="margin-top:10px"><button class="btn primary" data-action="showPlans">Lihat paket &amp; harga</button>${authState.logged_in?'<button class="btn" data-action="logoutAccount">Keluar akun</button>':'<button class="btn" data-action="startSignup">Masuk dengan Google</button>'}<button class="btn" data-action="hidePlans">Tutup</button></div></div>`;
  $('plansCard').classList.remove('hidden');
  $('plansCard').scrollIntoView({behavior:'smooth'});
}

// ===== Paket langganan (mirip render_subscription_offer) =====
function showPlans(){
  const canPay=authState.logged_in&&!authState.local_preview;
  const status=canPay?'Login Google terhubung. Pilih paket untuk membuat permintaan pembayaran.':'Paket berbayar memerlukan akun pelanggan. Masuk dengan Google terlebih dahulu.';
  $('plansCard').innerHTML=`<div class="card"><div class="section-label" style="margin-top:0">Langganan</div><p style="color:var(--muted)">Trial gratis berlaku 7 hari sejak login pertama. ${esc(status)}</p><div class="grid3">${PLANS.map(p=>`<div class="card" style="margin-bottom:0">${p.id==='pro'?'<span class="pill" style="background:var(--primary);color:#fff;display:inline-block;margin-bottom:6px">Terpopuler</span>':''}<div style="color:#b94b35;font-size:.72rem;font-weight:800;letter-spacing:.1em">${esc(p.name)}</div><div style="font-size:1.6rem;font-weight:800;color:var(--primary-dark);margin:6px 0">Rp${p.price.toLocaleString('id-ID')}<span style="font-size:.85rem;font-weight:600;color:var(--muted)">/bulan</span></div><ul style="padding-left:18px;color:var(--muted);font-size:.9rem">${p.features.map(f=>`<li>${esc(f)}</li>`).join('')}</ul><button class="btn primary" style="width:100%" data-action="requestPlan" data-args='["${p.id}"]'>Pilih paket ini</button></div>`).join('')}</div><div id="paymentStatus" class="status" role="status" aria-live="polite"></div><div class="row" style="margin-top:10px"><button class="btn" data-action="hidePlans">Kembali ke dashboard</button></div></div>`;
  $('plansCard').classList.remove('hidden');
  $('plansCard').scrollIntoView({behavior:'smooth'});
}
async function requestPlan(planId,statusId='paymentStatus'){
  if(!authState.logged_in||authState.local_preview){startSignup();return}
  const status=$(statusId);if(status)status.textContent='Membuat permintaan paket…';
  try{
    const response=await fetch('/api/subscription/request',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({plan_id:planId})});
    const result=await response.json();
    if(response.status===401){startSignup();return}
    if(!response.ok)throw new Error(result.error||'Permintaan pembayaran gagal dibuat.');
    if(result.checkout_url){location.assign(result.checkout_url);return}
    const pay=result.payment||{};
    const amount=pay.amount_idr?`Rp${Number(pay.amount_idr).toLocaleString('id-ID')}`:'';
    if(statusId==='accountPaymentStatus'){
      const parts=[result.message||'Permintaan paket tercatat.'];
      if(pay.account_number)parts.push(`Transfer ${amount} ke ${pay.bank_name||'rekening'} ${pay.account_number} a.n. ${pay.account_name||'PanganLaba'}. Akses dibuka setelah pembayaran dikonfirmasi.`);
      else if(result.payment_instructions)parts.push(result.payment_instructions);
      status.textContent=parts.join(' ');return
    }
    const planName=(result.plan&&result.plan.name)||'Paket';
    const support=pay.support_url?`<a class="btn" href="${esc(pay.support_url)}" target="_blank" rel="noopener">${esc(pay.support_label||'Hubungi pengelola')}</a>`:'';
    $('plansCard').innerHTML=`<div class="card"><div class="section-label" style="margin-top:0">Pembayaran · ${esc(planName)}</div>
      <div class="metric" style="margin-bottom:12px"><div class="l">Total tagihan</div><div class="v">${amount}</div><div style="color:var(--muted);font-size:.85rem">Aktivasi setelah pembayaran diverifikasi pengelola.</div></div>
      <div class="notice" style="white-space:pre-line">Transfer ke rekening <strong>${esc(pay.bank_name||'BCA')} ${esc(pay.account_number||'')}</strong> a.n. <strong>${esc(pay.account_name||'PanganLaba')}</strong>.<br>Setelah transfer, kirim bukti ke pengelola. Akses aktif setelah diverifikasi.</div>
      <div class="row" style="margin-top:12px">${support}<button class="btn" data-action="hidePlans">Tutup</button></div></div>`;
  }catch(error){if(status)status.textContent=error.message||'Server tidak dapat dihubungi.'}
}

// ===== Training (offline demo) =====
async function startTraining(statusEl){
  const s=statusEl||$('trainStatus');s.style.color='';s.textContent='Menyiapkan pelatihan…';
  const files=(($('excelFiles')||{}).files)||[];
  const epochs=((document.getElementById('epochs')||{}).value||'15');
  let job;
  if(files.length){
    const inputs=[...document.querySelectorAll('[data-commodity-index]')];
    const metadata=[...files].map((f,i)=>({field:'price_'+i,commodity:(inputs[i]||{}).value||''}));
    if(metadata.some(m=>!m.commodity.trim())){s.textContent='Isi nama komoditas untuk tiap file Excel terlebih dahulu.';return}
    const fd=new FormData();
    [...files].forEach((f,i)=>fd.append('price_'+i,f));
    fd.append('metadata',JSON.stringify(metadata));
    fd.append('epochs',epochs);
    s.textContent='Mengunggah & mulai melatih…';
    try{
      const r=await fetch('/api/train',{method:'POST',body:fd});
      const j=await r.json().catch(()=>null);
      if(!r.ok)throw new Error((j&&j.error)||'Gagal mengirim data.');
      job=j.job_id;
    }catch(err){s.textContent=err.message||'Server tidak dapat dihubungi.';s.style.color='#9d3d2b';return}
  }else{
    const res=await postJSON('/api/train/local',{epochs:Number(epochs)});
    if(!res.ok){s.textContent=(res.json&&res.json.error)||'Gagal mulai pelatihan lokal.';s.style.color='#9d3d2b';return}
    job=res.json.job_id;
  }
  if(!job){s.textContent='Server tak mengembalikan ID pekerjaan.';return}
  s.textContent='Pelatihan berjalan… status diperbarui otomatis.';
  pollTrain(job,s);
}
async function pollTrain(job,s){
  try{
    const st=await fetchJSON('/api/train/status/'+job);
    if(!st){setTimeout(()=>pollTrain(job,s),6000);return}
    if(st.status==='done'){s.textContent=st.message||'Selesai.';setTimeout(()=>loadLive(),800);return}
    if(st.status==='error'){s.textContent=st.message||'Pelatihan gagal.';s.style.color='#9d3d2b';return}
    s.textContent=st.message||'Pelatihan berjalan…';
    setTimeout(()=>pollTrain(job,s),6000);
  }catch{setTimeout(()=>pollTrain(job,s),6000)}
}
function processUploads(){startTraining($('uploadStatus'))}

$('excelFiles').addEventListener('change',e=>{
  $('excelMappings').innerHTML=[...e.target.files].map((f,i)=>
    `<div class="field" style="margin-top:8px"><label>Nama komoditas untuk ${esc(f.name)}</label><input data-commodity-index="${i}" placeholder="Misalnya Beras Medium"></div>`).join('');
});

function landChoosePlan(planId){
  if(authState.logged_in&&!authState.local_preview){
    if(!authState.access_allowed){requestPlan(planId,'accountPaymentStatus');return}
    showPlans();return
  }
  startSignup()
}

(function(){
  // Reveal saat discroll.
  const els=document.querySelectorAll('.reveal');
  if(!('IntersectionObserver' in window)){els.forEach(e=>e.classList.add('in'));return}
  const io=new IntersectionObserver(entries=>{
    entries.forEach(en=>{if(en.isIntersecting){en.target.classList.add('in');io.unobserve(en.target)}});
  },{threshold:.12});
  els.forEach(e=>io.observe(e));
  // Border bawah nav saat scroll.
  const brand=document.querySelector('.brand-row');
  if(brand){
    const onScroll=()=>{brand.classList.toggle('scrolled',window.scrollY>8)};
    window.addEventListener('scroll',onScroll,{passive:true});
    onScroll();
  }
})();

// ===== Kembali dari checkout (strip?paid=...) =====
function handlePaidRedirect(){
  const sp=new URLSearchParams(location.search);
  const paid=sp.get('paid');
  if(!paid)return;
  history.replaceState({},'',location.pathname);
  if(paid==='success'){
    toast('Pembayaran diterima. Memeriksa status langganan…');
    setTimeout(async()=>{
      await loadAccountState();
      toast(authState.account?.status==='active'
        ?'Pembayaran terkonfirmasi. Langganan aktif.'
        :'Pembayaran sedang diverifikasi. Muat ulang status beberapa saat lagi.');
    },1400);
  }else if(paid==='failed'){
    setTimeout(()=>toast('Pembayaran dibatalkan atau gagal. Silakan coba lagi.'),800);
  }
}

// ===== Boot =====
try{renderLandingPlans()}catch(e){}
handlePaidRedirect();
document.getElementById('mobileMenuToggle')?.addEventListener('click',()=>{const nav=$('landingNav'),open=nav.classList.toggle('mobile-open');$('mobileMenuToggle').setAttribute('aria-expanded',String(open))});
loadAccountState();
window.addEventListener('resize',()=>{try{if(!$('app').classList.contains('hidden')){renderSummary();renderResearch()}}catch(e){}});
// Default: landing publik. Daftar/login memakai Google; demo tetap dapat dicoba tanpa akun.
