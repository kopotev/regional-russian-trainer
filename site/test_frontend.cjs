// DOM-level functional checks; no corpus or model calls.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/dist/index.html','utf8');
const payload=html.match(/<script id="dataset" type="application\/json">([\s\S]*?)<\/script>/)[1];
const code=html.match(/<script>([\s\S]*?)<\/script>/)[1];
class Node {constructor(){this.children=[];this.value='';this.dataset={};this.classList={toggle(){},add(){}};this.textContent='';this.hidden=false;}append(...n){this.children.push(...n)}replaceChildren(...n){this.children=n;}setAttribute(k,v){this[k]=v;}addEventListener(){} }
const nodes={};const document={getElementById(id){if(!nodes[id])nodes[id]=new Node();return nodes[id]},createElement(){return new Node()},querySelectorAll(){return []},documentElement:{}};
document.getElementById('dataset').textContent=payload;
const mem={};const window={};
const context={document,window,localStorage:{getItem:k=>mem[k]||null,setItem:(k,v)=>mem[k]=v},fetch:async()=>{throw Error('no network in test')},navigator:{},console,setTimeout,clearTimeout,crypto:global.crypto,location:{pathname:'/index.html'}};
vm.runInNewContext(code,context);const app=window.REGIONAL_TRAINER;
assert.equal(app.words.length,94);assert.equal(new Set(app.words.map(w=>w.lemma)).size,94);assert.equal(app.originalCards.length,40);
for (const language of ['ru','en']) {app.setLang(language);for(let i=0;i<app.words.length;i++){app.selectWord(i);app.mode('recognition');assert.equal(nodes.activity.children[1].children.length,4);const w=app.words[i],correct=w.definition[language];const choices=nodes.activity.children[1].children;assert.equal(choices.filter(b=>b.textContent===correct).length,1);choices.find(b=>b.textContent===correct).onclick();assert.equal(nodes.answerbox.hidden,false);assert(nodes.answerbox.innerHTML.includes(w.example.ru));app.mode('recall');const row=nodes.activity.children[2];row.children[0].value=w.lemma;row.children[1].onclick();assert.equal(nodes.answerbox.hidden,false);app.mode('evidence');assert.equal(nodes.activity.children[1].children.length,4);assert(app.groundedPrompt().includes(w.lemma));}}
assert.equal(nodes.wordlist.children.length,94);
console.log('PASS: 94 words × RU/EN × recognition/recall/evidence; prompt grounding and 40 preserved legacy cards.');
