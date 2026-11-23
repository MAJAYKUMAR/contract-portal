// Data (JOBS, EXPIRED) lives in data/roles.json and is injected by
// scripts/build.py — see data/README.md for the rules for adding roles.
var STORAGE_KEY = 'contract-portal-applied-v1';
var STARRED_KEY = 'contract-portal-starred-v1';
function loadMarks(key){
  try{
    var raw = window.localStorage.getItem(key);
    if(!raw) return {};
    var parsed = JSON.parse(raw);
    if(!parsed || typeof parsed !== 'object') return {};
    var out = {};
    for(var k in parsed){ if(parsed[k]) out[k] = true; }
    return out;
  }catch(e){ return {}; }
}
function loadApplied(){ return loadMarks(STORAGE_KEY); }
function saveApplied(){
  try{ window.localStorage.setItem(STORAGE_KEY, JSON.stringify(applied)); }catch(e){}
}
function loadStarred(){ return loadMarks(STARRED_KEY); }
function saveStarred(){
  try{ window.localStorage.setItem(STARRED_KEY, JSON.stringify(starred)); }catch(e){}
}
var applied = loadApplied();
var starred = loadStarred();

/* ---- Cross-device sync via the Realtime Database REST API ----
   No SDK and no API key: marks are read and written with plain HTTPS
   requests against the database REST endpoints only. /applied.json and
   /starred.json are polled every few seconds so marks made on other
   devices show up here, and marking or un-marking a role writes with a
   PUT (mark) or DELETE (un-mark) request to those same endpoints,
   keyed by job ID. localStorage stays as the on-device cache/fallback:
   it is written on every change and read first on load, and any marks
   saved locally before the cloud connection existed are migrated up to
   the cloud on the first successful poll. */
var DB_BASE = 'https://contract-portal-9ea01-default-rtdb.firebaseio.com';
var SYNC_POLL_MS = 4000;
var syncEverOk = false;
var syncFail = { applied: false, starred: false };
var pendingApplied = {};
var pendingStarred = {};
function refreshSyncStatus(){
  if(syncFail.applied && syncFail.starred){
    setSyncStatus('Sync unavailable — marks save on this device only.', false);
  } else if(syncFail.applied || syncFail.starred){
    setSyncStatus('Sync unavailable for ' + (syncFail.applied ? 'applied' : 'starred') + ' marks — saving on this device only.', false);
  } else if(syncEverOk){
    setSyncStatus('Sync: live — Applied and Starred marks update on every device within a few seconds.', true);
  }
}
function noteSyncResult(kind, ok){
  syncFail[kind] = !ok;
  if(ok) syncEverOk = true;
  refreshSyncStatus();
}
function setSyncStatus(text, live){
  var wrap = document.getElementById('syncStatus');
  var label = document.getElementById('syncStatusText');
  if(label) label.textContent = text;
  if(wrap) wrap.classList.toggle('live', !!live);
}
function cloudSet(kind, id, on){
  var pending = (kind === 'applied') ? pendingApplied : pendingStarred;
  pending[String(id)] = !!on;
  var url = DB_BASE + '/' + kind + '/' + encodeURIComponent(String(id)) + '.json';
  var opts = on
    ? { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: 'true' }
    : { method: 'DELETE' };
  try{
    fetch(url, opts).then(function(r){
      noteSyncResult(kind, !!r.ok);
    }).catch(function(){ noteSyncResult(kind, false); });
  }catch(e){ noteSyncResult(kind, false); }
}
function applyCloud(kind, val){
  // kind is 'applied' or 'starred'; val is the parsed JSON from that
  // node's REST endpoint (an object keyed by job ID, or null).
  var cloud = {};
  if(val && typeof val === 'object'){
    for(var k in val){ if(val[k]) cloud[k] = true; }
  }
  // Migrate marks saved only on this device up to the cloud, once.
  var migKey = 'contract-portal-cloud-migrated-' + kind + '-v1';
  var done = false;
  try{ done = window.localStorage.getItem(migKey) === '1'; }catch(e){}
  if(!done){
    var local = (kind === 'applied') ? applied : starred;
    for(var lk in local){
      if(local[lk] && !cloud[lk]){ cloud[lk] = true; cloudSet(kind, lk, true); }
    }
    try{ window.localStorage.setItem(migKey, '1'); }catch(e){}
  }
  // Writes made on this device that the cloud has not caught up with yet
  // win over a stale poll response, so a fresh mark never flickers off.
  var pending = (kind === 'applied') ? pendingApplied : pendingStarred;
  for(var pk in pending){
    var want = pending[pk];
    if(!!cloud[pk] === want){ delete pending[pk]; }
    else if(want){ cloud[pk] = true; }
    else { delete cloud[pk]; }
  }
  if(kind === 'applied'){ applied = cloud; saveApplied(); }
  else { starred = cloud; saveStarred(); }
  render();
}
function pollKind(kind){
  try{
    fetch(DB_BASE + '/' + kind + '.json', { cache: 'no-store' }).then(function(r){
      if(!r.ok) throw new Error('read failed');
      return r.json();
    }).then(function(val){
      noteSyncResult(kind, true);
      applyCloud(kind, val);
    }).catch(function(){ noteSyncResult(kind, false); });
  }catch(e){ noteSyncResult(kind, false); }
}
function pollSync(){ pollKind('applied'); pollKind('starred'); }
function initSync(){
  if(typeof fetch === 'undefined'){
    setSyncStatus('Sync unavailable — marks save on this device only.', false);
    return;
  }
  pollSync();
  window.setInterval(pollSync, SYNC_POLL_MS);
  document.addEventListener('visibilitychange', function(){
    if(!document.hidden) pollSync();
  });
}
var activeFilter = 'all';
var activeDate = 'all';
/* Posted-date filter, against each role's normalised postedISO date.
   Windows are computed relative to the visitor's actual current local
   date (YYYY-MM-DD), so roles age naturally as real days pass and
   future roles are placed correctly when their posting date arrives.
   ISO date strings compare correctly with plain string comparison. */
function localISODate(dt){
  var m = String(dt.getMonth() + 1);
  if(m.length < 2) m = '0' + m;
  var day = String(dt.getDate());
  if(day.length < 2) day = '0' + day;
  return dt.getFullYear() + '-' + m + '-' + day;
}
function isoDaysAgo(base, n){
  var dt = new Date(base.getTime());
  dt.setDate(dt.getDate() - n);
  return localISODate(dt);
}
function dateOk(j){
  if(activeDate==='all') return true;
  var d=j.postedISO||'';
  if(!d) return false;
  var now = new Date();
  var today = localISODate(now);
  if(activeDate==='today') return d===today;
  if(activeDate==='last2') return d>=isoDaysAgo(now, 1) && d<=today;
  if(activeDate==='last7') return d>=isoDaysAgo(now, 6) && d<=today;
  if(activeDate==='older') return d<isoDaysAgo(now, 6);
  return true;
}
var dateOrd = {"Nov 23, 2026":136,"Nov 22, 2026":135,"Nov 21, 2026":134,"Nov 20, 2026":133,"Nov 19, 2026":132,"Nov 18, 2026":131,"Nov 17, 2026":130,"Nov 9, 2026":122,"Nov 16, 2026":129,"Nov 4, 2026":94,"Nov 14, 2026":127,"Nov 13, 2026":126,"Nov 12, 2026":125,"Nov 11, 2026":124,"Nov 10, 2026":123,"Nov 9, 2026":122,"Nov 7, 2026":115,"Nov 6, 2026":114,"Nov 5, 2026":113,"Nov 3, 2026":112,"Nov 9 — 30 min ago":111,"Nov 9 — 1 hr ago":110,"Updated Nov 9 — 1 hr ago":110,"Nov 9 — 4 hrs ago":109,"Nov 9 — 6 hrs ago":108,"Nov 9 — 7 hrs ago":107,"Nov 9 — 8 hrs ago":106,"Nov 9":99,"Reposted ~Nov 8":98,"~Nov 8":98,"Reposted ~Nov 7":97,"~Nov 7":97,"~Nov 6":96,"~Nov 5":95,"~Nov 4":94,"~Nov 3":93,"~Nov 2":92,"~Oct 29":89,"~Oct 27":87,"Oct 30, 2026":90,"Oct 29, 2026":89,"Oct 28, 2026":88,"Oct 27, 2026":87};
function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;');}
function matches(j){
  if(!dateOk(j)) return false;
  var isApplied=!!applied[j.id];
  var isExp=!!EXPIRED[j.id];
  if(activeFilter==='expired'){
    if(!isExp) return false;
  } else if(activeFilter==='applied'){
    if(!isApplied || isExp) return false;
  } else {
    // All Jobs view (and every other filter) only shows live,
    // not-yet-applied roles. Marked roles live in the Applied tab
    // and dead postings live in the Expired tab instead.
    if(isApplied || isExp) return false;
    if(activeFilter==='c2c' && j.type!=='c2c') return false;
    if(activeFilter==='w2' && j.type!=='w2') return false;
    if(activeFilter==='unsure' && j.type!=='unsure') return false;
    if(activeFilter==='1099' && !j.is1099) return false;
    if(activeFilter==='h1b' && !j.h1b) return false;
    if(activeFilter==='remote' && !/remote/i.test(j.loc)) return false;
    if(activeFilter==='texas' && !/TX|Texas|Austin|Houston|Dallas|Irving|Plano|Richardson|Texas City/.test(j.loc)) return false;
    if(activeFilter==='starred' && !starred[j.id]) return false;
  }
  var q=document.getElementById('q').value.trim().toLowerCase();
  if(q){ var hay=(j.title+' '+j.company+' '+j.loc+' '+j.desc+' '+(j.flag||'')).toLowerCase(); if(hay.indexOf(q)===-1) return false; }
  return true;
}
function render(){
  var sort=document.getElementById('sort').value;
  var list=JOBS.filter(matches);
  if(sort==='pay') list.sort(function(a,b){return b.payNum-a.payNum;});
  else if(sort==='new') list.sort(function(a,b){return (dateOrd[b.posted]||0)-(dateOrd[a.posted]||0);});
  else list.sort(function(a,b){return (a.priority||2)-(b.priority||2) || b.payNum-a.payNum;});
  var html='';
  list.forEach(function(j){
    var isExp=!!EXPIRED[j.id];
    var isTop=j.priority===1 && !isExp;
    var isStarred=!!starred[j.id];
    html+='<article class="job'+(isTop?' top':'')+(isStarred?' starred':'')+(isExp?' expired':'')+'">'
      +(isTop?'<div class="priority-label">★ Start here — priority roles</div>':'')
      +'<div class="job-head"><div><h3><a href="'+j.url+'" target="_blank" rel="noopener noreferrer">'+esc(j.title)+'</a></h3><div class="company">'+esc(j.company)+' · via '+j.src+'</div></div>'
      +'<div class="pay">'+esc(j.pay)+'<small>'+esc(j.loc)+'</small></div></div>'
      +'<div class="meta"><span class="tag '+(j.type==='c2c'?'c2c':j.type==='w2'?'w2':'')+'">'+esc(j.typeLabel)+'</span>'
      +(isExp?'<span class="tag expired-badge">Expired</span>':'')
      +(j.h1b?'<span class="tag h1b">H-1B listed</span>':'')
      +(isStarred?'<span class="tag priority">★ Priority</span>':'')
      +'<span class="tag">Posted '+esc(j.posted)+'</span><span class="tag">'+esc(j.exp)+'</span><span class="tag">'+esc(j.dur)+'</span></div>'
      +'<p class="desc">'+esc(j.desc)+'</p>'
      +(j.flag?'<p class="flag">⚠ '+esc(j.flag)+'</p>':'')
      +(isExp?'<p class="expired-note">Expired '+esc(String(EXPIRED[j.id]))+' — posting removed.</p>':'')
      +'<div class="actions"><a class="btn btn-primary" href="'+j.url+'" target="_blank" rel="noopener noreferrer">View job ↗</a>'
      +'<button class="btn btn-applied'+(applied[j.id]?' on':'')+'" data-applied="'+j.id+'">'+(applied[j.id]?'✓ Applied':'Mark as applied')+'</button>'
      +'<button class="btn btn-star'+(isStarred?' on':'')+'" data-starred="'+j.id+'" aria-pressed="'+isStarred+'" aria-label="'+(isStarred?'Remove star from ':'Star as priority: ')+esc(j.title)+'"><span class="star-glyph" aria-hidden="true">'+(isStarred?'★':'☆')+'</span>'+(isStarred?'Starred':'Star')+'</button></div></article>';
  });
  document.getElementById('list').innerHTML=html;
  var emptyEl=document.getElementById('empty');
  emptyEl.hidden=list.length>0;
  if(list.length===0){
    if(activeFilter==='applied'){
      emptyEl.textContent='No applied roles yet. Mark a role as applied from the All Jobs list and it will appear here.';
    } else if(activeFilter==='expired'){
      emptyEl.textContent='No expired roles match those filters.';
    } else {
      emptyEl.textContent='No roles match those filters. Try clearing the search or picking “All types.”';
    }
  }
  var nStarred=Object.keys(starred).filter(function(k){return starred[k];}).length;
  var n=Object.keys(applied).filter(function(k){return applied[k];}).length;
  var inAppliedView=activeFilter==='applied';
  var inExpiredView=activeFilter==='expired';
  var liveCount=JOBS.filter(function(j){return !EXPIRED[j.id];}).length;
  document.getElementById('countLine').textContent=inExpiredView
    ? 'Showing '+list.length+' expired role'+(list.length===1?'':'s')+' — postings removed · ★ '+nStarred+' starred'
    : inAppliedView
    ? 'Showing '+list.length+' applied role'+(list.length===1?'':'s')+' of '+liveCount+' live roles · ★ '+nStarred+' starred'
    : 'Showing '+list.length+' of '+liveCount+' live roles · ★ '+nStarred+' starred';
  document.getElementById('statApplied').textContent=n;
  document.getElementById('statStarred').textContent=nStarred;
  var nAppliedLive=Object.keys(applied).filter(function(k){return applied[k] && !EXPIRED[k];}).length;
  var nExpired=JOBS.filter(function(j){return EXPIRED[j.id];}).length;
  var tabAll=document.getElementById('tabAll');
  var tabApplied=document.getElementById('tabApplied');
  var tabExpired=document.getElementById('tabExpired');
  if(tabAll && tabApplied){
    document.getElementById('tabAllCount').textContent=(liveCount-nAppliedLive);
    document.getElementById('tabAppliedCount').textContent=nAppliedLive;
    if(tabExpired) document.getElementById('tabExpiredCount').textContent=nExpired;
    tabAll.setAttribute('aria-selected', (inAppliedView||inExpiredView) ? 'false' : 'true');
    tabApplied.setAttribute('aria-selected', inAppliedView ? 'true' : 'false');
    if(tabExpired) tabExpired.setAttribute('aria-selected', inExpiredView ? 'true' : 'false');
  }
  // Tabs and pills share one state, so they stay in sync in render():
  // the Applied tab is selected exactly when the "Applied only" pill is.
  var btns=document.querySelectorAll('[data-applied]');
  for(var i=0;i<btns.length;i++){ btns[i].addEventListener('click',function(){ var id=this.getAttribute('data-applied'); if(applied[id]){ delete applied[id]; } else { applied[id]=true; } saveApplied(); cloudSet('applied', id, !!applied[id]); render(); }); }
  var starBtns=document.querySelectorAll('[data-starred]');
  for(var s=0;s<starBtns.length;s++){ starBtns[s].addEventListener('click',function(){ var id=this.getAttribute('data-starred'); if(starred[id]){ delete starred[id]; } else { starred[id]=true; } saveStarred(); cloudSet('starred', id, !!starred[id]); render(); }); }
}
function setFilter(f){
  activeFilter=f;
  document.querySelectorAll('.pill[data-f]').forEach(function(x){
    x.setAttribute('aria-pressed', x.getAttribute('data-f')===f ? 'true' : 'false');
  });
  render();
}
function setDateFilter(d){
  activeDate=d;
  document.querySelectorAll('.pill[data-d]').forEach(function(x){
    x.setAttribute('aria-pressed', x.getAttribute('data-d')===d ? 'true' : 'false');
  });
  render();
}
document.querySelectorAll('.pill[data-f]').forEach(function(p){
  p.addEventListener('click',function(){
    var f=p.getAttribute('data-f');
    // Every filter pill is a toggle: clicking the already-active pill
    // again turns that filter off and returns to the unfiltered
    // "All types" view.
    if(activeFilter===f){ setFilter('all'); }
    else { setFilter(f); }
  });
});
document.querySelectorAll('.pill[data-d]').forEach(function(p){
  p.addEventListener('click',function(){
    var d=p.getAttribute('data-d');
    // Same toggle behaviour for the Posted group: clicking the
    // already-active pill again returns to "All dates".
    if(activeDate===d){ setDateFilter('all'); }
    else { setDateFilter(d); }
  });
});
document.querySelectorAll('.view-tab').forEach(function(t){
  t.addEventListener('click',function(){
    // Applied tab and the "Applied only" pill are the same view.
    // All Jobs tab returns to the All types (not-yet-applied) list.
    var v=t.getAttribute('data-view');
    if(v==='applied'){ setFilter('applied'); }
    else if(v==='expired'){ setFilter('expired'); }
    else { setFilter('all'); }
  });
});
document.getElementById('q').addEventListener('input',render);
document.getElementById('sort').addEventListener('change',render);
initSync();
render();
