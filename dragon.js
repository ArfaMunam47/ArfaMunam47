import * as THREE from 'three';

const host = document.querySelector('#dragon-stage');
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(32, 1, 0.1, 100);
camera.position.set(0, 0.15, 8.4);

const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
host.appendChild(renderer.domElement);

scene.add(new THREE.HemisphereLight(0xffe8f2, 0x503044, 2.0));
const key = new THREE.DirectionalLight(0xffd5e5, 3.2); key.position.set(-3, 5, 6); scene.add(key);
const rim = new THREE.PointLight(0xf16ca6, 22, 12); rim.position.set(3, 1, -2); scene.add(rim);
const fill = new THREE.PointLight(0xffb7d2, 8, 10); fill.position.set(-4, -2, 4); scene.add(fill);

const mat = (color, roughness=.48, metalness=0) => new THREE.MeshStandardMaterial({ color, roughness, metalness });
const pink = mat('#e98db5');
const lightPink = mat('#ffc0d9');
const bellyMat = mat('#ffd4e5');
const darkPink = mat('#a94e79');
const hornMat = mat('#ffe5ee', .32);
const eyeWhite = mat('#fff8fc', .18);
const irisMat = mat('#8b456b', .2);
const pupilMat = mat('#241923', .12);
const shineMat = new THREE.MeshBasicMaterial({ color: '#ffffff' });
const nostrilMat = mat('#783b59');

const dragon = new THREE.Group(); scene.add(dragon);
const torso = new THREE.Group(); dragon.add(torso);

function sphere(parent, name, scale, position, material, segments=32) {
  const mesh = new THREE.Mesh(new THREE.SphereGeometry(1, segments, segments), material);
  mesh.name = name; mesh.scale.set(...scale); mesh.position.set(...position); mesh.castShadow = true; mesh.receiveShadow = true; parent.add(mesh); return mesh;
}
function tube(parent, points, radius, material, tubular=32) {
  const curve = new THREE.CatmullRomCurve3(points.map(p => new THREE.Vector3(...p)));
  const mesh = new THREE.Mesh(new THREE.TubeGeometry(curve, tubular, radius, 8, false), material);
  mesh.castShadow = true; parent.add(mesh); return mesh;
}

// Pear-shaped body and soft belly
sphere(torso, 'body', [0.83, 1.0, .62], [0, -.35, 0], pink);
sphere(torso, 'belly', [.59, .77, .18], [0, -.42, .51], bellyMat);
for (let i=0;i<3;i++) sphere(torso, 'belly-scale-'+i, [.42-i*.035,.018,.025], [0,-.1-i*.23,.68], lightPink, 20);

// Head, cheeks and muzzle
const head = new THREE.Group(); head.position.set(0, .72, .18); torso.add(head);
sphere(head, 'head', [.88,.77,.7], [0,0,0], pink, 40);
sphere(head, 'muzzle', [.43,.29,.43], [0,-.27,.58], lightPink);
sphere(head, 'cheek-left', [.22,.14,.13], [-.57,-.23,.49], lightPink);
sphere(head, 'cheek-right', [.22,.14,.13], [.57,-.23,.49], lightPink);

// Eyes: independent pupils follow pointer and blink as a pair.
const eyes=[];
for (const side of [-1,1]) {
  const eye = new THREE.Group(); eye.position.set(side*.36,.08,.58); head.add(eye);
  sphere(eye,'eye-socket',[.255,.32,.12],[0,0,0],darkPink);
  sphere(eye,'eyeball',[.215,.275,.13],[0,0,.035],eyeWhite);
  const iris = sphere(eye,'iris',[.125,.17,.075],[0,-.015,.15],irisMat);
  const pupil = sphere(eye,'pupil',[.075,.12,.045],[0,-.005,.205],pupilMat);
  sphere(eye,'eye-glint',[.037,.05,.018],[-.035,.065,.25],shineMat,20);
  sphere(eye,'eye-glint-small',[.017,.022,.012],[.045,-.055,.25],shineMat,16);
  // Upper eyelid is a skin-coloured curved cap, scaled down briefly for a blink.
  const lid = sphere(eye,'upper-lid',[.235,.03,.145],[0,.285,.035],pink);
  eyes.push({eye, iris, pupil, lid, side});
}
// Tiny nostrils and smile
for (const x of [-.105,.105]) sphere(head,'nostril',[.026,.035,.018],[x,-.22,.968],nostrilMat,16);
tube(head,[[-.18,-.39,.91],[-.08,-.44,.96],[0,-.45,.97],[.08,-.44,.96],[.18,-.39,.91]],.014,darkPink,24);

// Horns and little head spikes
function horn(parent, x, y, z, lean=0) {
  const curve = new THREE.QuadraticBezierCurve3(new THREE.Vector3(x,y,z),new THREE.Vector3(x+lean,y+.34,z-.02),new THREE.Vector3(x+lean*1.6,y+.57,z-.08));
  const mesh = new THREE.Mesh(new THREE.TubeGeometry(curve,20,.105,12,false),hornMat); mesh.castShadow=true; parent.add(mesh);
}
horn(head,-.43,.55,-.02,-.08); horn(head,.43,.55,-.02,.08);
for(let i=0;i<3;i++) sphere(head,'crown-spike-'+i,[.11,.2,.12],[(-1+i)*.22,.66-Math.abs(i-1)*.05,-.12],darkPink);

// Wings: custom soft membrane with curved finger-like supports.
const wings=[];
function makeWing(side) {
  const pivot = new THREE.Group(); pivot.position.set(side*.62,.25,-.32); torso.add(pivot);
  const shape = new THREE.Shape();
  shape.moveTo(0,0); shape.quadraticCurveTo(side*.25,.45,side*.82,.66);
  shape.quadraticCurveTo(side*.72,.25,side*1.02,-.13);
  shape.quadraticCurveTo(side*.55,-.02,side*.34,-.22);
  shape.quadraticCurveTo(side*.16,-.25,0,0);
  const geom = new THREE.ShapeGeometry(shape,24);
  const membrane = new THREE.Mesh(geom,new THREE.MeshStandardMaterial({color:'#f5a4c6',roughness:.6,side:THREE.DoubleSide, transparent:true, opacity:.96}));
  membrane.position.z=-.03; pivot.add(membrane);
  tube(pivot,[[0,0,.015],[side*.27,.28,.015],[side*.82,.66,.015]],.025,lightPink,20);
  tube(pivot,[[side*.27,.28,.018],[side*.69,.25,.018],[side*1.02,-.13,.018]],.018,lightPink,20);
  tube(pivot,[[side*.27,.28,.018],[side*.34,-.22,.018]],.018,lightPink,16);
  wings.push({pivot,side});
}
makeWing(-1); makeWing(1);

// Arms and feet
for(const side of [-1,1]) {
  const arm=sphere(torso,'arm',[.19,.34,.2],[side*.61,-.48,.42],pink); arm.rotation.z=side*-.45;
  sphere(torso,'paw',[.2,.16,.2],[side*.69,-.73,.48],lightPink);
  sphere(torso,'leg',[.25,.28,.25],[side*.42,-1.05,.12],pink);
  sphere(torso,'foot',[.27,.13,.28],[side*.43,-1.22,.2],lightPink);
  for(let t=-1;t<=1;t++) sphere(torso,'toe',[.055,.045,.06],[side*.43+t*.105,-1.25,.43],bellyMat,16);
}

// Long curved tail with a heart/leaf-like tip.
const tailPivot=new THREE.Group(); tailPivot.position.set(0,-.85,-.35); torso.add(tailPivot);
const tailCurve = new THREE.CatmullRomCurve3([
 new THREE.Vector3(0,0,0),new THREE.Vector3(.12,-.28,-.12),new THREE.Vector3(.48,-.48,-.15),new THREE.Vector3(.88,-.34,-.12),new THREE.Vector3(1.13,.02,-.1)
]);
const tail = new THREE.Mesh(new THREE.TubeGeometry(tailCurve,48,.17,16,false),pink); tail.castShadow=true; tailPivot.add(tail);
const tailTip=sphere(tailPivot,'tail-tip',[.2,.12,.16],[1.13,.02,-.1],lightPink); tailTip.rotation.z=.6;

// Soft contact shadow without a visible scene/background.
const shadow = new THREE.Mesh(new THREE.CircleGeometry(1.0,48),new THREE.MeshBasicMaterial({color:'#5b2943',transparent:true,opacity:.14,depthWrite:false}));
shadow.rotation.x=-Math.PI/2; shadow.position.set(0,-1.72,0); shadow.scale.set(1.2,.35,1); scene.add(shadow);

let pointerX=0, pointerY=0, targetX=0, targetY=0;
host.addEventListener('pointermove', e=>{const r=host.getBoundingClientRect(); targetX=((e.clientX-r.left)/r.width-.5)*2; targetY=-((e.clientY-r.top)/r.height-.5)*2;});
host.addEventListener('pointerleave',()=>{targetX=0;targetY=0;});

const clock=new THREE.Clock();
let blinkTimer=2.2, blink=0, blinkPhase=0;
function resize(){const w=host.clientWidth,h=host.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}
new ResizeObserver(resize).observe(host); resize();

function animate(){
  requestAnimationFrame(animate);
  const dt=Math.min(clock.getDelta(),.04);
  const t=clock.elapsedTime;
  pointerX += (targetX-pointerX)*Math.min(1,dt*4);
  pointerY += (targetY-pointerY)*Math.min(1,dt*4);

  // Main hover, gentle roll and head response.
  dragon.position.y=.12+Math.sin(t*1.65)*.13;
  dragon.rotation.y=Math.sin(t*.55)*.12 + pointerX*.12;
  dragon.rotation.z=Math.sin(t*.8)*.035 - pointerX*.035;
  torso.rotation.x=Math.sin(t*1.1)*.025;
  head.rotation.y=pointerX*.19 + Math.sin(t*.7)*.025;
  head.rotation.x=-pointerY*.11 + Math.sin(t*.9)*.018;
  tailPivot.rotation.y=Math.sin(t*1.7)*.32;
  tailPivot.rotation.z=Math.sin(t*1.25)*.13;
  wings.forEach(({pivot,side})=>{pivot.rotation.x=Math.sin(t*7.5+(side===1?0:Math.PI))*.55; pivot.rotation.y=side*(.08+Math.sin(t*7.5)*.08);});

  // Eyes independently track the pointer; eyelids close briefly at irregular intervals.
  blinkTimer-=dt;
  if(blinkTimer<=0 && blinkPhase===0){blinkPhase=1;blink=0;blinkTimer=2.4+Math.random()*2.8;}
  if(blinkPhase===1){blink=Math.min(1,blink+dt*12);if(blink>=1)blinkPhase=2;}
  else if(blinkPhase===2){blink=Math.max(0,blink-dt*10);if(blink<=0)blinkPhase=0;}
  eyes.forEach(({iris,pupil,lid,side})=>{
    const gx=pointerX*.055 + Math.sin(t*.8+side)*.012;
    const gy=pointerY*.045 + Math.sin(t*.55)*.008;
    iris.position.x=gx; iris.position.y=-.015+gy;
    pupil.position.x=gx; pupil.position.y=-.005+gy;
    lid.scale.y=Math.max(.015,1-blink*.98);
    lid.position.y=.285-blink*.03;
  });
  shadow.material.opacity=.10+(.05*(1-(dragon.position.y-.0)));
  renderer.render(scene,camera);
}
animate();
