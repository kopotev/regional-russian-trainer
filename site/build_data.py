from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
template=(ROOT/'site/template.html').read_text()
data=json.loads((ROOT/'data/Kazakhstan_final.json').read_text())
payload={'release':data,'original':{'packs':[{'cards':data.get('legacy_cards',[])}]}}
safe=json.dumps(payload,ensure_ascii=False).replace('</','<\\/')
html=template.replace('@@DATA@@',safe)
(ROOT/'site/dist').mkdir(parents=True,exist_ok=True)
(ROOT/'site/dist/index.html').write_text(html)
(ROOT/'site/dist/Kazakhstan_lexicon_trainer.html').write_text(html)
(ROOT/'site/standalone').mkdir(parents=True,exist_ok=True)
(ROOT/'site/standalone/index.html').write_text(html)
(ROOT/'site/standalone/Kazakhstan_lexicon_trainer.html').write_text(html)
print(len(data.get('words',[])), 'words embedded')
