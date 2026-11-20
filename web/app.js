'use strict';
const $=id=>document.getElementById(id);
const date=value=>new Date(value).toLocaleString('zh-CN',{hour12:false});
fetch('versions.json',{cache:'no-store'}).then(response=>{if(!response.ok)throw Error('版本清单尚未发布');return response.json()}).then(data=>{
  const versions=data.versions;
  if(!versions.length){
    $('version').replaceChildren(new Option('暂无开发分支'));
    $('title').textContent='暂无待预览的开发分支';
    $('details').textContent='推送含有新提交的开发分支后，下次刷新会自动收录。';
    $('empty').textContent='可通过右上角的「正式网站」查看已合入的版本。';
    return;
  }
  $('version').replaceChildren(...versions.map(v=>new Option(v.branch,v.id)));
  $('version').disabled=false;
  $('generated').textContent='预览生成于 '+date(data.generated)+' · 约每 30 分钟检查更新';
  function select(id){
    const v=versions.find(v=>v.id===id)||versions[0];
    $('version').value=v.id;
    $('title').textContent=v.title;
    $('details').textContent=`提交 ${v.sha.slice(0,7)} · ${date(v.updated)}`;
    $('pr').hidden=!v.pr;if(v.pr)$('pr').href=v.pr;
    $('open').hidden=false;$('open').href=v.path;
    $('wendao').hidden=!v.wendao;$('wendao').href=v.path+'library/wendao/index.html';
    $('empty').hidden=false;$('empty').textContent='正在打开 '+v.branch+'…';
    $('preview').src=v.path;
    const url=new URL(location.href);url.searchParams.set('version',v.id);history.replaceState(null,'',url);
  }
  $('preview').addEventListener('load',()=>{$('empty').hidden=true});
  $('version').addEventListener('change',()=>select($('version').value));
  select(new URLSearchParams(location.search).get('version'));
}).catch(error=>{$('title').textContent='暂时无法读取预览';$('details').textContent=error.message;$('empty').textContent='请稍后刷新，或通过页脚查看发布进度。'});
