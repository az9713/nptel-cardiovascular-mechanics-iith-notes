"""Export exact chapter Python listings to explicitly mapped public files."""
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
MAPPING={1:'code/ch01_bed.py',2:'code/ch02_kinematics.py',3:'code/ch03_pump.py',4:'code/ch04_tissue.py',5:'code/ch05_rheology.py',6:'code/ch06_models.py',7:'code/ch07_vessels.py',8:'code/ch08_synthesis.py'}
def main():
 for n,relative in MAPPING.items():
  matches=list(ROOT.glob(f'chapter-{n:02d}-*.html'))
  if not matches:continue
  if len(matches)!=1:raise ValueError('Ambiguous chapter')
  s=BeautifulSoup(matches[0].read_bytes().decode('utf-8'),'html.parser')
  listings=s.select('pre[data-run]')
  if len(listings)!=1:raise ValueError('Expected one explicitly mapped listing per chapter')
  content=listings[0].get_text()
  target=ROOT/relative;target.parent.mkdir(exist_ok=True)
  target.write_bytes(content.encode('utf-8'))
  print(relative)
if __name__=='__main__':main()
