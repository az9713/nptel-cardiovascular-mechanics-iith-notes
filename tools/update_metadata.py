"""Recompute public chapter counts and aggregate existing review attestations.

This tool does not invent review rounds or grant scientific acceptance. Independent
review records must already exist in each chapter sidecar at its exact body digest.
"""
from pathlib import Path
import hashlib,json
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def main():
 rows=[]
 for path in sorted(ROOT.glob('chapter-??-*.html')):
  document=path.read_bytes().decode('utf-8');body=document.split('<!-- BOOK-CONTENT-START -->',1)[1].split('<!-- BOOK-CONTENT-END -->',1)[0];sha=hashlib.sha256(body.encode()).hexdigest();s=BeautifulSoup(body,'html.parser');meta_path=path.with_suffix('.meta.json');m=json.loads(meta_path.read_text(encoding='utf-8'));assert m['authored_body_sha256']==sha
  acceptance=m.get('acceptance');accepted=isinstance(acceptance,dict) and acceptance.get('status')=='accepted' and acceptance.get('accepted_body_sha256')==sha
  m.update(article_words_including_math_code=len(s.get_text(' ',strip=True).split()),counting_method='Whitespace tokens of exact authored article text including math/code; reader chrome excluded',worked_solutions=len(s.select('details')),executable_listings=len(s.select('pre[data-run]')))
  meta_path.write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
  rows.append({'chapter':m['chapter'],'file':path.name,'authored_body_sha256':sha,'accepted':accepted,'review_rounds':m.get('review_rounds',[]),'worked_solutions':m['worked_solutions'],'words_including_math_code':m['article_words_including_math_code']})
 report={'accepted':len(rows)==8 and all(x['accepted'] for x in rows),'chapter_count':len(rows),'independent_rounds_required':2,'chapters':rows,'scope':'Public attestations summarize separately performed scientific reviews at exact authored-body digests. They are not generated proof verification; code, source integrity, browser and publication checks remain separate.','limits':['No clinical calibration or personal medical inference','No complete audiovisual/board audit','Primary sources used only at the inspection scope recorded in chapter sidecars']}
 (ROOT/'editorial-review-summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print('Existing scientific attestations:',sum(x['accepted'] for x in rows),'of',len(rows),'chapters accepted')
if __name__=='__main__':main()
