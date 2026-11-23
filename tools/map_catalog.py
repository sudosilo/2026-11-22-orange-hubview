# Matches dealer catalog part numbers to the parts in the 3D model.
# Usage: python3 tools/map_catalog.py parts-list.json ref/parts/catalog-prius.json ref/parts/prius.json
import json, re, sys
parts = json.load(open(sys.argv[1]))
cat = json.load(open(sys.argv[2]))
out_path = sys.argv[3]
old = json.load(open(out_path))

# (model part regex, assembly regex or None, catalog category prefix, catalog name regex)
RULES = [
 (r'^Brake Disc$', None, 'brakes/front-brakes', r'^Rotor$'),
 (r'^(Inner|Outer) Brake Pad$', None, 'brakes/front-brakes', r'^Brake Pads$'),
 (r'^Brake Caliper$', None, 'brakes/front-brakes', r'^Caliper$'),
 (r'^(Front Hub|Wheel Bearing)$', 'Front', 'brakes/front-brakes', r'^Hub & Bearing$'),
 (r'^Splash Shield$', None, 'brakes/front-brakes', r'^Splash Shield$'),
 (r'Brake Shoe$', None, 'brakes/rear-brakes', r'^Brake Shoes$'),
 (r'^Brake Drum$', None, 'brakes/rear-brakes', r'^Drum$'),
 (r'^Wheel Cylinder$', None, 'brakes/rear-brakes', r'^Wheel Cylinder$'),
 (r'^Backing Plate$', None, 'brakes/rear-brakes', r'^Backing Plate$'),
 (r'^Hub Bearing Unit$', None, 'suspension/rear-axle', r'^Hub & Bearing'),
 (r'^Front Strut$', None, 'suspension/front-suspension-components', r'^Absorber Assy'),
 (r'^Front Coil Spring$', None, 'suspension/front-suspension-components', r'^Coil Spring|Spring,\s+Coil'),
 (r'^Upper Strut Mount$', None, 'suspension/front-suspension-components', r'^Support|Strut Mount'),
 (r'^Lower Control Arm$', None, 'suspension/front-suspension-components', r'^Lower Control Arm$'),
 (r'^Lower Ball Joint$', None, 'suspension/front-suspension-components', r'^Lower Ball Joint$'),
 (r'^Steering Knuckle$', None, 'suspension/front-suspension-components', r'^Knuckle$'),
 (r'^Rear Shock Absorber$', None, 'suspension/rear-axle', r'^Shock Absorber$'),
 (r'^Torsion Beam$', None, 'suspension/rear-axle', r'^Axle Assembly$'),
 (r'Rear Coil Spring$', None, 'suspension/rear-axle', r'^Coil Spring$'),
 (r'Beam Bushing$', None, 'suspension/rear-axle', r'^Bushings$'),
 (r'^Stabilizer Bar$', None, 'suspension/stabilizer-bar-components', r'Stabilizer Bar|^Bar'),
 (r'^Outer CV Joint$', None, 'driveline-axles/front-axle-shafts-joints', r'^Outer Joint Assembly$'),
 (r'Half Shaft$', None, 'driveline-axles/front-axle-shafts-joints', r'^Axle Assembly$'),
 (r'Inner CV Joint$', None, 'driveline-axles/front-axle-shafts-joints', r'^Inner CV Joint$'),
 (r'^Cylinder Head$', None, 'engine/', r'^Cylinder Head$'),
 (r'^Head Gasket$', None, 'engine/', r'^Head Gasket$'),
 (r'Camshaft$', 'Engine', 'engine/', r'^Camshaft$'),
 (r'^Valve Cover$', None, 'engine/', r'^Valve Cover$'),
 (r'^Oil Pan$', None, 'engine/', r'^Oil Pan$'),
 (r'^Crankshaft$', None, 'engine/', r'^Crankshaft$'),
 (r'^Piston \d', None, 'engine/', r'^Piston$'),
 (r'^Connecting Rod', None, 'engine/', r'^Connecting Rod$'),
 (r'^Intake Manifold$', None, 'air-fuel-delivery/', r'^Intake Manifold$|^Manifold'),
 (r'^Water Pump$', None, 'belts-cooling/water-pump', r'Pump'),
 (r'^Oil Filter$', None, 'maintenance-lubrication/filters', r'Oil Filter'),
 (r'^Air Cleaner Box$', None, 'maintenance-lubrication/filters', r'Air Filter|Element'),
 (r'^Spark Plug', None, 'electrical/ignition-system', r'Spark Plug'),
 (r'^Ignition Coil', None, 'electrical/ignition-system', r'Coil'),
 (r'^Fuel Injector', None, 'air-fuel-delivery/fuel-injection', r'Injector$'),
 (r'^Electronic Throttle Body$', None, 'air-fuel-delivery/throttle-body', r'Throttle Body'),
 (r'^Exhaust Manifold$', None, 'emission-control-exhaust/exhaust-manifold', r'Manifold$'),
 (r'^Timing Chain Cover$', None, 'engine/', r'^Timing Chain$'),
 (r'^Transaxle Case$', None, 'transmission/', r'^Transaxle$'),
 (r'^Power Split Device$', None, 'electrical/hybrid-components', r'Planetary Ring'),
 (r'^Transaxle Damper$', None, 'electrical/hybrid-components', r'^Damper$'),
 (r'^Battery ECU$', None, 'charging-starting/battery', r'^Computer Assy'),
 (r'^Battery Cooling Fan$', None, 'charging-starting/battery', r'^Blower Motor$'),
 (r'^12V Auxiliary Battery$', None, 'charging-starting/battery', r'^Battery$'),
 (r'^Radiator$', None, 'belts-cooling/', r'^Radiator Assembly$|^Radiator$'),
 (r'^Radiator Cap$', None, 'belts-cooling/', r'Cap Sub-Assy'),
 (r'^Cooling Fan', None, 'belts-cooling/', r'^Fan Blade$'),
 (r'^Fan Motor$', None, 'belts-cooling/', r'^Fan Motor$'),
 (r'^Lower Radiator Hose$', None, 'belts-cooling/', r'^Lower Hose$'),
 (r'^Upper Radiator Hose$', None, 'belts-cooling/', r'^Upper Hose$'),
 (r'^Front Pipe$', None, 'emission-control-exhaust/exhaust-system', r'^Exhaust Pipe$'),
 (r'^Muffler$', None, 'emission-control-exhaust/exhaust-system', r'^Muffler & Pipe$'),
 (r'^Catalytic Converter$', None, 'emission-control-exhaust/', r'Converter'),
 (r'^Fuel Tank$', None, 'air-fuel-delivery/fuel-supply', r'^Fuel Tank$'),
 (r'^Fuel Pump Module$', None, 'air-fuel-delivery/fuel-supply', r'^Fuel Pump$'),
 (r'^Filler Neck$', None, 'air-fuel-delivery/fuel-supply', r'^Filler Pipe$'),
 (r'^Fuel Cap$', None, 'air-fuel-delivery/fuel-supply', r'^Fuel Cap$'),
 (r'^Charcoal Canister$', None, 'emission-control-exhaust/vapor-canister', r'Canister'),
 (r'^Hood Panel$', None, 'body-hardware/hood-components', r'^Hood$'),
 (r'Hood Hinge$', None, 'body-hardware/hood-components', r'^Hinge$'),
 (r'^Hood Latch$', None, 'body-hardware/hood-components', r'^Lock$'),
 (r'^Hood Support Rod$', None, 'body-hardware/hood-components', r'^Support Rod$'),
 (r'^Hood Inner Frame$', None, 'body-hardware/hood-components', r'^Insulator$'),
 (r'Front Fender$', None, 'body-hardware/fender-components', r'^Fender$'),
 (r'^Windshield$', None, 'body-hardware/glass-windshield', r'^Windshield$'),
 (r'^Rearview Mirror$', None, 'body-hardware/glass-windshield', r'^Mirror Inside$'),
 (r'Headlight$', None, 'headlights-lighting/headlamps', r'^Headlamp Assembly$'),
 (r'Taillight$', None, 'headlights-lighting/combination-lamps', r'Tail|Combination'),
 (r'Fog Lamp$', None, 'headlights-lighting/fog-lamps', r'Fog'),
 (r'^Alloy Wheel$', None, 'suspension/wheels', r'^Wheel, Alloy$'),
 (r'^(Hub Cap|Center Cap)$', None, 'suspension/wheels', r'^Wheel Cover$'),
 (r'^Steering Rack$', None, 'steering/steering-gear-linkage', r'^Gear Assembly$'),
 (r'^Tie Rod End$', None, 'steering/steering-gear-linkage', r'^Outer Tie Rod$'),
 (r'Tie Rod$', 'Steering', 'steering/steering-gear-linkage', r'^Inner Tie Rod$'),
 (r'^Steering Column$', None, 'steering/steering-column', r'Column'),
 (r'^Steering Wheel$', None, 'steering/steering-wheel', r'Steering Wheel|^Wheel'),
 (r'^Master Cylinder$', None, 'brakes/hydraulic-system-brakes', r'Master Cylinder'),
 (r'^Brake Actuator$', None, 'brakes/', r'Actuator'),
 (r'^Window Glass$', 'Front .* Door', 'body-hardware/glass-front-door', r'Glass'),
 (r'^Window Glass$', 'Rear .* Door', 'body-hardware/glass-rear-door', r'Door Glass'),
 (r'^Window Regulator$', 'Front', 'body-hardware/glass-front-door', r'Regulator'),
 (r'^Window Regulator$', 'Rear', 'body-hardware/glass-rear-door', r'Regulator'),
 (r'^Side Mirror$', None, 'body-hardware/outside-mirrors', r'Mirror'),
 (r'^Outside Handle$', 'Front', 'body-hardware/front-door-lock-hardware', r'Outside|Handle'),
 (r'^Outside Handle$', 'Rear', 'body-hardware/rear-door-lock-hardware', r'Outside|Handle'),
 (r'^Door Latch$', 'Front', 'body-hardware/front-door-lock-hardware', r'^Lock|Latch'),
 (r'^Door Latch$', 'Rear', 'body-hardware/rear-door-lock-hardware', r'^Lock|Latch'),
 (r'^Front Bumper Cover$', None, 'body-hardware/bumper-components-front', r'Cover'),
 (r'^Bumper Reinforcement$', None, 'body-hardware/bumper-components-front', r'Reinforcement'),
 (r'^Rear Bumper Cover$', None, 'body-hardware/bumper-components-rear', r'Cover'),
 (r'^Rear Reinforcement$', None, 'body-hardware/bumper-components-rear', r'Reinforcement'),
 (r'^Hatch Upper Glass$', None, 'body-hardware/glass-lift-gate', r'Glass'),
 (r'^Rear Spoiler$', None, 'body-hardware/rear-spoiler', r'Spoiler'),
]
def side_of(a, p):
    t = a + ' ' + p
    return 'L' if 'Left' in t or 'Driver' in t else 'R' if 'Right' in t or 'Passenger' in t else None
SIDE_BY_NUM = {'43201': 'R', '43202': 'L', '48068': 'R', '48069': 'L', '48510': 'R', '48520': 'L', '45046': 'R', '45047': 'L'}
BOTH_SIDES = ('48530',)
def entry_side(e):
    pre = e['number'][:5]
    if pre in SIDE_BY_NUM: return SIDE_BY_NUM[pre]
    if pre in BOTH_SIDES: return None
    t = e['name'] + ' ' + e['desc']
    if re.search(r'\bLH\b|Left|Driver', t): return 'L'
    if re.search(r'\bRH\b|Right|Passenger', t): return 'R'
    return None
out = {k: v for k, v in old.items() if k.startswith('*/Tire')}
hits = 0
for a, p in parts:
    for prx, arx, cp, nrx in RULES:
        if not re.search(prx, p) or (arx and not re.search(arx, a)):
            continue
        es = [e for e in cat if e['category'].startswith(cp) and (re.search(nrx, e['name']) or re.search(nrx, e['desc']))]
        HW = r'(Bolt|Nut|Washer|Clip|Cushion|Screw|Stud|Rivet|Clamp|Pin|Snap|Pad|Cover|O-Ring|Gasket|Seal|Bracket|Holder|Bushing|Grommet)\b'
        es = [e for e in es if not (re.search(r'\b' + HW, e['name']) or re.match(HW, e['desc']))]
        seen, uniq = set(), []
        for e in es:
            if e['number'] not in seen:
                seen.add(e['number']); uniq.append(e)
        sd = side_of(a, p)
        if sd:
            m = [e for e in uniq if entry_side(e) == sd]
            other = [e for e in uniq if entry_side(e) not in (None, sd)]
            uniq = m if m else ([] if other and len(other) == len(uniq) else [e for e in uniq if entry_side(e) is None])
        if uniq:
            def lab(e):
                t = e['desc'] if e['desc'] and e['desc'] != 'Multiple' else e['name']
                if e['number'][:5] in BOTH_SIDES: t = re.sub(r',? ?(Rear )?(Right|Left) Hand', '', t) + ', Rear (fits both sides)'
                return ('Toyota OEM ' + t).strip()[:60]
            out[a + '/' + p] = [[lab(e), e['number']] for e in uniq[:4]]
            hits += 1
        break
json.dump(out, open(out_path, 'w'), indent=1)
print('matched', hits, 'of', len(parts))
