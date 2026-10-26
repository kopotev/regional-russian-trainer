import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const site=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
execFileSync('python3',['build_data.py'],{cwd:site,stdio:'inherit'});
const html=await readFile(path.join(site,'dist/index.html'),'utf8');
await mkdir(path.join(site,'standalone'),{recursive:true});
await writeFile(path.join(site,'standalone/index.html'),html);
await writeFile(path.join(site,'standalone/Kazakhstan_lexicon_trainer.html'),html);
const data=JSON.parse(await readFile(path.join(site,'../data/Kazakhstan_final.json'),'utf8'));
const candidates=JSON.parse(execFileSync('python3',['-c',"import csv,json,sys; print(json.dumps(list(csv.DictReader(open(sys.argv[1],encoding='utf-8-sig'))),ensure_ascii=False))",path.join(site,'../backend/resources/candidates.csv')],{encoding:'utf8',maxBuffer:8*1024*1024}));
const runtime=(await readFile(path.join(site,'worker/runtime.mjs'),'utf8')).replace(/\nexport default createRuntime;?\s*$/, '\n');
const payload={html,words:data.words,candidates};
const source=runtime+'\nconst BUNDLED_INPUT='+JSON.stringify(payload)+';\nexport default createRuntime(BUNDLED_INPUT);\n';
await mkdir(path.join(site,'worker'),{recursive:true});
await writeFile(path.join(site,'worker/index.js'),source);
console.log('Bundled '+data.words.length+' teaching targets and '+candidates.length+' frozen candidates.');
