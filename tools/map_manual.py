import json,os,re,sys
car=sys.argv[1]; parts=json.load(open(sys.argv[2]))  # list of [assembly, part]
idx=json.load(open(f'ref/manual/{car}/index.json'))
base=f'ref/manual/{car}/'
idx=[e for e in idx if os.path.getsize(base+e['file'])>4000]
SYN={
 'tire':['tire','wheels and tires'],'wheel':['wheel','wheels and tires'],'alloy wheel':['wheel'],'steel wheel':['wheel'],'hub cap':['wheel cover','hub cap'],'center cap':['wheel'],
 'lug nut':['lug nut','wheel'],'brake disc':['brake rotor','rotor','disc'],'brake drum':['brake drum','drum'],'brake caliper':['caliper'],'brake pad':['brake pad','pads'],
 'brake shoe':['brake shoe','shoes'],'wheel cylinder':['wheel cylinder'],'backing plate':['backing plate','drum brake'],'wheel bearing':['wheel bearing','hub'],'hub':['hub','wheel bearing'],
 'steering knuckle':['knuckle','steering knuckle'],'knuckle':['knuckle'],'strut':['strut','shock absorber','suspension strut'],'coil spring':['coil spring','spring'],'shock absorber':['shock absorber','shock'],
 'control arm':['control arm','lower arm'],'ball joint':['ball joint'],'radius rod':['radius rod','radius arm'],'tie rod':['tie rod'],'stabilizer':['stabilizer','sway bar'],
 'cv joint':['cv joint','constant velocity','drive axle','axle shaft'],'half shaft':['drive axle','axle shaft','half shaft'],'cv boot':['cv boot','boot'],'outer cv joint':['cv joint','drive axle'],
 'splash':['splash','dust shield'],'dust seal':['seal','wheel bearing'],'snap ring':['snap ring','wheel bearing'],'spindle':['spindle','axle'],'torsion beam':['rear axle','torsion beam','axle beam'],'trailing arm':['trailing arm'],
 'cylinder block':['engine block','cylinder block','block'],'cylinder head':['cylinder head'],'head gasket':['head gasket'],'camshaft':['camshaft'],'valve cover':['valve cover','cylinder head cover','rocker arm cover'],
 'oil pan':['oil pan'],'crankshaft':['crankshaft'],'piston':['piston'],'connecting rod':['connecting rod'],'spark plug':['spark plug'],'ignition coil':['ignition coil'],'fuel injector':['fuel injector','injector'],
 'timing belt':['timing belt'],'timing chain':['timing chain'],'timing':['timing'],'crank pulley':['crankshaft pulley','pulley'],'water pump':['water pump'],'alternator':['alternator'],
 'intake manifold':['intake manifold'],'carburetor':['carburetor'],'air cleaner':['air cleaner','air filter'],'exhaust manifold':['exhaust manifold'],'distributor':['distributor'],'starter':['starter'],
 'flywheel':['flywheel','drive plate'],'oil filter':['oil filter'],'fuel pump':['fuel pump'],'throttle body':['throttle body'],
 'clutch disc':['clutch disc','clutch'],'pressure plate':['pressure plate','clutch'],'release bearing':['release bearing','clutch'],'clutch fork':['clutch','release fork'],'bellhousing':['transaxle','clutch housing'],
 'transmission case':['transaxle','manual transaxle','transmission'],'mainshaft':['mainshaft','transaxle'],'countershaft':['countershaft','transaxle'],'final drive':['final drive','differential'],'differential':['differential'],'shift rod':['shift','gearshift'],
 'transaxle':['transaxle','hybrid transaxle'],'mg1':['motor generator','mg1','generator'],'mg2':['motor generator','mg2','motor'],'power split':['planetary','power split','transaxle'],'damper':['damper','transaxle'],'counter drive gear':['counter','transaxle'],
 'inverter':['inverter','converter'],'boost converter':['boost converter','inverter'],'dc-dc':['dc/dc','converter'],'coolant pump':['water pump','inverter'],
 'hybrid battery':['hv battery','hybrid battery','battery'],'battery case':['hv battery','battery'],'module':['battery module','hv battery'],'battery ecu':['battery ecu','battery'],'cooling fan':['cooling fan','fan'],'service plug':['service plug'],'high voltage':['high voltage','cable'],
 'radiator':['radiator'],'radiator cap':['radiator cap'],'fan':['cooling fan','fan'],'hose':['hose','radiator'],'thermostat':['thermostat'],'reservoir':['reservoir','coolant'],'heater hose':['heater'],'heat storage':['heat storage','coolant heat'],'condenser':['condenser'],
 'front pipe':['exhaust pipe','front pipe','exhaust'],'catalytic converter':['catalytic converter'],'muffler':['muffler','exhaust'],'tailpipe':['tail pipe','exhaust'],'resonator':['resonator','exhaust'],'pipe':['exhaust pipe','exhaust'],'hanger':['hanger','exhaust'],
 'fuel tank':['fuel tank'],'sending unit':['sending unit','fuel gauge'],'filler neck':['filler','fuel tank'],'fuel line':['fuel line'],'fuel filter':['fuel filter'],'charcoal canister':['canister','evaporative'],'bladder':['fuel tank'],
 'master cylinder':['master cylinder'],'brake booster':['brake booster','booster'],'brake actuator':['brake actuator','actuator'],'proportioning valve':['proportioning valve'],'brake line':['brake line','brake hose'],'brake hose':['brake hose'],'parking brake':['parking brake'],
 'steering rack':['steering gear','rack'],'rack housing':['steering gear','rack'],'pinion':['steering gear','pinion'],'rack boot':['boot','steering gear'],'steering column':['steering column'],'intermediate shaft':['intermediate shaft','steering column'],'steering wheel':['steering wheel'],'eps motor':['power steering','motor'],'airbag':['air bag','airbag'],'horn':['horn'],'ignition switch':['ignition switch'],
 'battery':['battery'],'battery cable':['battery cable','battery'],'fuse box':['fuse','relay box','junction block'],'wiring harness':['wiring','harness'],'headlight':['headlamp','headlight'],'taillight':['tail lamp','rear combination','taillight'],'turn signal':['turn signal'],'fog lamp':['fog'],'wiper':['wiper'],'dome light':['dome','interior light'],'hybrid vehicle ecu':['hybrid','ecu'],
 'windshield':['windshield'],'rear window':['back glass','rear window'],'window glass':['window glass','door glass'],'window regulator':['window regulator','regulator'],'quarter glass':['quarter','glass'],'vent glass':['vent','glass'],
 'hood':['hood'],'hood latch':['hood latch','latch'],'trunk':['trunk','luggage','deck lid'],'hatch':['back door','liftgate','hatch'],'spoiler':['spoiler'],'strut':['strut'],
 'door':['door'],'outer skin':['door'],'inner panel':['door'],'door trim':['trim panel','door trim'],'door latch':['door lock','latch'],'outside handle':['outside handle','door handle'],'hinge':['hinge'],'side mirror':['mirror'],'window crank':['regulator','window'],
 'bumper':['bumper'],'grille':['grille'],'energy absorber':['absorber','bumper'],'reinforcement':['reinforcement','bumper'],
 'seat':['seat'],'dashboard':['instrument panel','dashboard'],'instrument cluster':['instrument cluster','gauge','meter'],'center meter':['combination meter','meter'],'multi display':['display','multi'],'glove box':['glove'],'heater core':['heater core'],'radio':['radio','audio'],'center console':['console'],'shift lever':['shift lever','selector'],'power button':['power switch','start'],'pedal':['pedal'],'clutch pedal':['clutch pedal'],'brake pedal':['brake pedal'],'accelerator':['accelerator'],'carpet':['carpet'],'headliner':['headliner','roof'],'rearview mirror':['mirror'],'sun visor':['visor'],
 'engine mount':['engine mount','mount'],'transaxle mount':['mount','transaxle'],'crossmember':['crossmember','subframe'],'suspension member':['subframe','crossmember','suspension member'],
 'fender':['fender'],'quarter panel':['quarter panel'],'rocker':['rocker'],'pillar':['pillar'],'roof':['roof'],'firewall':['dash panel','firewall'],'floor':['floor'],'core support':['radiator support','core support'],'frame rail':['frame','side member'],'strut tower':['strut','tower'],
 'underbody':['body','frame','dimension'],'body shell':['body','frame','dimension'],
}
STOP={'left','right','front','rear','upper','lower','inner','outer','1','2','3','4','5','6','7','of','the','and','row','driver','passenger','assembly','panel'}
BAD=['precaution','bulletin','specification','testing and inspection','symptom','diagnos','trouble','procedure','vacuum indications','normal ignition','circuit','connector','terminal']
GOOD=['diagram','exploded','component','location','overview','parts','view','removal','installation']
def phrases(name):
    n=name.lower()
    out=[]
    keys=[k for k in SYN if re.search(r'(?<![a-z])'+re.escape(k)+r'(?![a-z])',n)]
    keys=[k for k in keys if not any(k!=o and k in o for o in keys)]
    for k in keys: out+=[(p,2.0) for p in SYN[k]]
    words=[w for w in re.findall(r'[a-z0-9\-/]+',n) if w not in STOP and len(w)>2]
    out+=[(w,1.0) for w in words]
    return out
def score(e,ph,aph,pname=''):
    path=e['path'].lower(); cap=e['caption'].lower(); segs=path.split('/'); tail='/'.join(segs[1:][-3:]); last2='/'.join(segs[-2:])
    s=0;strong=False
    has=lambda p,t: re.search(r'(?<![a-z])'+re.escape(p)+r'(?![a-z])',t) is not None
    for p,w in ph:
        if w>=2 and has(p,tail): s+=w*len(p.split());strong=True
        elif w>=2 and has(p,cap): s+=0.8*w*len(p.split())
        elif w<2 and len(p)>=6 and has(p,last2): s+=1.5;strong=True
    if not strong: return 0
    for p,w in aph:
        if w>=2 and (p in path or p in cap): s+=0.5
    t=path+' '+cap
    if any(b in t for b in BAD): s-=3
    if 'bulletin' in t: s-=3
    pn=pname.lower()
    if ('air conditioning' in path or 'compressor' in path or 'hvac' in path) and not any(k in pn for k in ['heater','condenser','ac ']): s-=4
    if any(g in cap for g in ['component','exploded']): s+=2.5
    elif any(g in t for g in GOOD): s+=1
    return s
out={}
for a,p in parts:
    ph=phrases(p); aph=phrases(a)
    best=max(idx,key=lambda e:score(e,ph,aph,p)); sc=score(best,ph,aph,p)
    if sc>=4.5: out[a+'/'+p]={'file':best['file'],'path':best['path'],'caption':best['caption'],'score':round(sc,1)}
for a in sorted(set(x[0] for x in parts)):
    ph=phrases(a)
    best=max(idx,key=lambda e:score(e,ph,[],a)); sc=score(best,ph,[],a)
    if sc>=4.5: out[a]={'file':best['file'],'path':best['path'],'caption':best['caption'],'score':round(sc,1)}
json.dump(out,open(sys.argv[3],'w'),indent=0)
print(car,len(out),'of',len(parts)+len(set(x[0] for x in parts)))
