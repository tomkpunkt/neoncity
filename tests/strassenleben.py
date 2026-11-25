"""Regressionstest für Richtungswechsel, Vorrang und Fußwege nach einem Umbau."""
import pathlib
import tempfile

from playwright.sync_api import sync_playwright
import pruefung


def main():
    # Testzugriff nur in der temporären HTML-Kopie, ohne Eingriff in das Spiel-API.
    html = (pruefung.ROOT / 'index.html').read_text()
    probe = """
window.checkTraffic=()=>{
  G=emptyGrid();
  const middle=ix(10,10),before=ix(9,10),after=ix(11,10);
  for(let x=7;x<=13;x++)G[ix(x,10)].g=1;
  G[ix(10,9)].g=2;
  G[ix(10,11)].m=1;
  rebuild();
  const gate=crossings.get(middle);
  if(!gate)throw Error('Überweg am Park fehlt');
  const source=middle*4+3,target=middle*4;
  const edge=walkGraph.get(source).links.find(e=>e.to===target&&e.gate===gate);
  if(!edge)throw Error('Markierung und Fußweg stimmen nicht überein');
  let visited=new Set([target]),front=[target];
  for(const id of front)for(const e of walkGraph.get(id).links){
    if(!visited.has(e.to)){visited.add(e.to);front.push(e.to)}
  }
  if(!front.some(id=>(id>>2)===ix(10,9)))throw Error('Park nicht erreichbar');
  const pedestrian={node:source,t:0,speed:.4,rest:0,route:[edge],edge:null};
  const companion={...pedestrian,speed:.31,route:[edge]};
  const car=(cell,t)=>({cell,t,entry:0,exit:0,cruise:.9,speed:.8});
  const lead=car(middle,.94),following=car(before,.40),tail=car(ix(8,10),.89);
  gcars.splice(0,gcars.length,lead,following,tail);
  gate.time=3;advancePed(pedestrian,.02);
  let crossed=false,group=false,braked=false,released=false;
  for(let i=0;i<650;i++){
    stepTraffic(.02);
    if(pedestrian.node!==target)advancePed(pedestrian,.02);
    if(companion.node!==target)advancePed(companion,.02);
    if(gate.active===2)group=true;
    if(pedestrian.edge||companion.edge){
      crossed=true;
      if(gcars.some(c=>c.cell===middle))throw Error('Auto auf besetztem Überweg');
    }
    if(following.cell===before&&following.speed<.16)braked=true;
    if(crossed&&following.cell===after)released=true;
    if(tail.cell===following.cell&&tail.entry===following.entry&&following.t-tail.t<.34)
      throw Error('Auffahrender Wagen');
  }
  if(!crossed||!group||!braked||!released)throw Error('Übergang ohne vollständigen Wechsel');
  const exiting=car(middle,1);exiting.exit=1;
  const entering=car(ix(10,11),0);entering.entry=1;entering.exit=2;
  const p=carPose(exiting),q=carPose(entering);
  if(Math.hypot(p[0]-q[0],p[1]-q[1],p[2]-q[2])>1e-6)throw Error('Sprung im Abbiegebogen');
  G[middle].g=0;rebuild();
  if(crossings.has(middle)||walkGraph.has(source)||gcars.some(c=>c.cell===middle))
    throw Error('Entfernte Straße noch belegt');
  for(let i=0;i<120;i++){stepTraffic(.02);for(const person of peds)advancePed(person,.02)}
  // Der hintere Wagen steht in der Liste zuerst. Er darf die Einmündung
  // nicht vor dem Wagen an der Haltelinie reservieren.
  G=emptyGrid();
  for(let x=6;x<=14;x++)G[ix(x,10)].g=1;
  for(let z=6;z<=14;z++)G[ix(10,z)].g=1;
  rebuild();
  gcars.splice(0,gcars.length,car(before,.35),car(before,.76));
  const [rear,frontCar]=gcars;
  let frontEntered=false,rearEntered=false;
  for(let i=0;i<350;i++){
    stepTraffic(.02);
    frontEntered ||= frontCar.cell===middle;
    rearEntered ||= rear.cell===middle;
  }
  if(!frontEntered||!rearEntered)throw Error('Hinterer Wagen blockiert die Einmündung');

  G=emptyGrid();
  for(let x=6;x<=14;x++)G[ix(x,10)].g=1;
  G[ix(10,9)].g=2;G[ix(11,9)].g=2;
  rebuild();
  const gates=[crossings.get(middle),crossings.get(after)];
  if(gates.some(gate=>!gate))throw Error('Benachbarte Überwege fehlen');
  gcars.splice(0,gcars.length,car(middle,.5),{...car(after,.5),entry:2,exit:2});
  for(const gate of gates){gate.wait=true;gate.time=3}
  stepTraffic(.02);
  if(gates.filter(gate=>gate.phase==='drain').length!==1)
    throw Error('Benachbarte Überwege sperren sich gleichzeitig');

  let seed=27;
  const random=Math.random;
  Math.random=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296);
  try{
    gcars.length=0;peds.length=0;
    generate(7);rebuild();
    let lastMove=0,crossed=0;
    for(let i=0;i<15000;i++){
      const occupiedCells=gcars.map(car=>car.cell);
      stepTraffic(.02);
      if(gcars.some((car,j)=>car.cell!==occupiedCells[j]))lastMove=i;
      for(const person of peds){
        const previous=person.edge?.gate;
        advancePed(person,.02);
        if(previous&&person.edge===null)crossed++;
      }
      for(const gate of crossings.values()){
        if(gate.active&&gcars.some(car=>car.cell===gate.cell))
          throw Error('Auto auf besetztem Überweg im Langzeittest');
      }
      if(i-lastMove>500)throw Error('Zehn Sekunden ohne Fahrzeugbewegung im Startviertel');
    }
    if(!crossed)throw Error('Keine Fußgängerquerung im Startviertel');
  }finally{Math.random=random}
  return true;
};
"""
    pruefung.libs_holen()
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as playwright:
        pruefung.ROOT = pathlib.Path(tmp)
        (pruefung.ROOT / 'index.html').write_text(html.replace('window.NEON={', probe+'window.NEON={'))
        browser, page, errors = pruefung.seite(playwright, 640, 400)
        try:
            assert page.evaluate('checkTraffic()')
            assert not errors, errors
        finally:
            browser.close()
    print('Parkzugang, Gruppenfreigabe, Abbiegen, Abriss und fünf Minuten Verkehrsfluss geprüft.')


if __name__ == '__main__':
    main()
