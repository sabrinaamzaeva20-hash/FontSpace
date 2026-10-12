const $ = s => document.querySelector(s);
let favorites = [], listing = [], currentEdit = null;
const types = {serif:'С засечками','sans-serif':'Без засечек',display:'Акцидентный',handwriting:'Рукописный',monospace:'Моноширинный'};
const escapeText = v => String(v).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(path, options={}) {
 const res = await fetch('/api'+path, {...options, headers:{'Content-Type':'application/json'}});
 if (!res.ok) {let detail={}; try {detail=await res.json()} catch{}; throw Error(typeof detail.detail==='string'?detail.detail:'Ошибка '+res.status)}
 return res.status===204?null:res.json();
}
function notice(text){$('#notice').textContent=text;}
function ensureFont(family){
 const id = 'family-'+family.toLowerCase().replace(/[^a-z0-9]/g,'-');
 if(!document.getElementById(id)) {
   const link=document.createElement('link');link.id=id;link.rel='stylesheet';
   link.href='https://fonts.googleapis.com/css2?family='+encodeURIComponent(family).replace(/%20/g,'+')+'&display=swap';
   document.head.appendChild(link);
 }
}
function card(x,saved=false){
 ensureFont(x.family);
 const fav=saved?x:favorites.find(v=>v.family===x.family);
 const name=escapeText(x.family), category=escapeText(types[x.category]||x.category);
 const sample=escapeText($('#preview').value||'Слова обретают форму');
 const action=saved?'<div class="mini-buttons"><button class="edit" data-edit="'+x.id+'">Изменить</button><button class="remove" data-remove="'+x.id+'">Удалить</button></div>':(fav?'<span class="category">♥ В избранном</span>':'<button class="save" data-family="'+name+'">♡ Сохранить</button>');
 return '<article class="font-card"><div class="card-top"><b class="font-name">'+name+'</b><span class="category">'+category+'</span></div><div class="sample" style="font-family:'+"'"+name.replace(/'/g,'')+"', sans-serif"+'">'+sample+'</div><div class="card-bottom"><span>'+(saved?escapeText(x.project_name):('Начертаний: '+x.variants))+'</span>'+action+'</div>'+(saved&&x.notes?'<div class="info">'+escapeText(x.notes)+'</div>':'')+'</article>';
}
function render(){
 $('#font-grid').innerHTML=listing.length?listing.map(x=>card(x)).join(''):'<div class="empty">Шрифты не найдены. Измените запрос.</div>';
 $('#favorites-grid').innerHTML=favorites.length?favorites.map(x=>card(x,true)).join(''):'<div class="empty">Здесь пока пусто. Сохраните шрифт из каталога.</div>';
 $('#fav-counter').textContent=favorites.length;
}
async function fetchFavorites(){favorites=await api('/favorites');render();}
async function search(){
 try{
  notice('');let query=new URLSearchParams({q:$('#search').value,category:$('#category').value});
  let result=await api('/fonts?'+query);listing=result.fonts;
  $('#result-count').textContent=result.total;
  $('#source').textContent=result.source.startsWith('google-fonts-api')?'Источник: Google Fonts API':'Источник: локальный каталог (эмулятор API)';
  render();
 }catch(e){notice(e.message)}
}
function tab(favs){
 $('#catalog-section').hidden=favs;$('#favorites-section').hidden=!favs;
 $('#nav-catalog').classList.toggle('selected',!favs);$('#nav-favorites').classList.toggle('selected',favs);
}
$('#nav-catalog').onclick=()=>tab(false);$('#nav-favorites').onclick=async()=>{tab(true);try{await fetchFavorites()}catch(e){notice(e.message)}};
$('#find').onclick=search;$('#search').addEventListener('keydown',e=>{if(e.key==='Enter')search()});$('#category').onchange=search;
$('#preview').oninput=render;
$('#font-grid').onclick=async e=>{
 let b=e.target.closest('button[data-family]');if(!b)return;
 const family=b.dataset.family;const item=listing.find(x=>x.family===family);if(!item)return;
 try{await api('/favorites',{method:'POST',body:JSON.stringify({family:item.family,category:item.category})});await fetchFavorites();notice('Шрифт добавлен в избранное')}catch(err){notice(err.message)}
};
$('#favorites-grid').onclick=async e=>{
 const remove=e.target.closest('button[data-remove]');const edit=e.target.closest('button[data-edit]');
 if(remove){if(!confirm('Удалить шрифт из избранного?'))return;try{await api('/favorites/'+remove.dataset.remove,{method:'DELETE'});await fetchFavorites();notice('Удалено')}catch(err){notice(err.message)}}
 if(edit){currentEdit=Number(edit.dataset.edit);const x=favorites.find(v=>v.id===currentEdit);if(!x)return;$('#edit-form').elements.project_name.value=x.project_name;$('#edit-form').elements.notes.value=x.notes;$('#edit-dialog').showModal()}
};
$('#cancel').onclick=()=>$('#edit-dialog').close();
$('#edit-form').onsubmit=async e=>{
 e.preventDefault();let form=e.target;
 try{await api('/favorites/'+currentEdit,{method:'PATCH',body:JSON.stringify({project_name:form.elements.project_name.value,notes:form.elements.notes.value})});$('#edit-dialog').close();await fetchFavorites();notice('Информация сохранена')}catch(err){notice(err.message)}
};
Promise.all([fetchFavorites(),search()]).catch(e=>notice(e.message));
