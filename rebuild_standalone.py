import re

with open('space-invaders-standalone.html','r',encoding='utf-8') as f:
    content = f.read()

matches = re.findall(r"loadAndProcess\('(data:image/png;base64,[^']+)'\)", content)
K = matches[0]
B = matches[1]

NEW_HTML = """<!DOCTYPE html>
<html lang="he">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
  <title>Space Invaders – Khamenei Edition</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background: #000;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
      overflow: hidden;
      touch-action: none;
      font-family: 'Courier New', monospace;
    }
    canvas { display: block; border: 2px solid rgba(0,255,255,0.6); box-shadow: 0 0 30px rgba(0,255,255,0.2); }
    #touch-controls {
      display: none; position: fixed;
      bottom: 0; left: 0; right: 0; height: 88px;
      background: rgba(0,0,0,0.85);
      border-top: 1px solid rgba(0,255,255,0.2);
      flex-direction: row; align-items: center;
      justify-content: space-between; padding: 0 24px;
    }
    .touch-btn {
      background: rgba(0,255,255,0.1);
      border: 2px solid rgba(0,255,255,0.6);
      border-radius: 14px; color: #0ff;
      display: flex; align-items: center; justify-content: center;
      user-select: none; -webkit-user-select: none;
      transition: background 0.08s;
    }
    .touch-btn.pressed { background: rgba(0,255,255,0.35); }
    #btn-left, #btn-right { width: 88px; height: 68px; font-size: 32px; }
    #btn-fire { width: 140px; height: 68px; font-size: 15px; font-weight: bold; letter-spacing: 1px; }
    #info { color: rgba(0,255,255,0.5); margin-top: 8px; font-size: 13px; letter-spacing: 1px; }
    @media (pointer: coarse) { #info { display: none; } #touch-controls { display: flex; } }
  </style>
</head>
<body>
<canvas id="gameCanvas"></canvas>
<div id="info">&#8592; &#8594; move &nbsp;|&nbsp; SPACE shoot &nbsp;|&nbsp; R restart</div>
<div id="touch-controls">
  <button class="touch-btn" id="btn-left">&#9664;</button>
  <button class="touch-btn" id="btn-fire">&#128293; FIRE</button>
  <button class="touch-btn" id="btn-right">&#9654;</button>
</div>
<script>
const canvas=document.getElementById('gameCanvas');
const ctx=canvas.getContext('2d');
const W=800,H=600,CTRL_H=88;
const isMobile=window.matchMedia('(pointer: coarse)').matches;

function resizeCanvas(){
  const availH=window.innerHeight-(isMobile?CTRL_H:0);
  const scale=Math.min(window.innerWidth/W,availH/H);
  canvas.style.width=Math.floor(W*scale)+'px';
  canvas.style.height=Math.floor(H*scale)+'px';
}
resizeCanvas();
window.addEventListener('resize',resizeCanvas);

const DPR=Math.min(window.devicePixelRatio||1,3);
canvas.width=W*DPR; canvas.height=H*DPR;
ctx.scale(DPR,DPR);
ctx.imageSmoothingEnabled=true;
ctx.imageSmoothingQuality='high';

// Khamenei 348x430 → 0.809 → 82x101
const EW=82,EH=101,ECOLS=5,EROWS=3,EGX=28,EGY=22;
// BIBI 603x414 → 1.456 → 144x99
const PW=144,PH=99;
const BW=5,BH=18;

const STARS=Array.from({length:140},()=>({
  x:Math.random()*W,y:Math.random()*H,
  r:Math.random()*1.4+0.3,alpha:Math.random()*0.6+0.3,
  twinkle:Math.random()*Math.PI*2
}));

const particles=[];
function spawnEx(x,y){
  const c=['#ff0','#f80','#f44','#fff','#fa0'];
  for(let i=0;i<18;i++){
    const a=Math.random()*Math.PI*2,sp=Math.random()*4+1.5;
    particles.push({x,y,vx:Math.cos(a)*sp,vy:Math.sin(a)*sp,
      life:1,decay:Math.random()*0.04+0.025,
      r:Math.random()*4+2,color:c[Math.floor(Math.random()*c.length)]});
  }
}
function tickP(){
  for(let i=particles.length-1;i>=0;i--){
    const p=particles[i];
    p.x+=p.vx;p.y+=p.vy;p.vy+=0.12;p.life-=p.decay;
    if(p.life<=0)particles.splice(i,1);
  }
}
function drawP(){
  particles.forEach(p=>{
    ctx.globalAlpha=p.life;ctx.fillStyle=p.color;
    ctx.beginPath();ctx.arc(p.x,p.y,p.r*p.life,0,Math.PI*2);ctx.fill();
  });
  ctx.globalAlpha=1;
}

function loadImg(src){
  return new Promise(res=>{
    const img=new Image();
    img.onload=()=>{
      const oc=document.createElement('canvas');
      oc.width=img.naturalWidth;oc.height=img.naturalHeight;
      const c=oc.getContext('2d');c.drawImage(img,0,0);
      try{
        const id=c.getImageData(0,0,oc.width,oc.height),d=id.data;
        for(let i=0;i<d.length;i+=4){
          const r=d[i],g=d[i+1],b=d[i+2];
          const br=(r+g+b)/3,sat=Math.max(r,g,b)-Math.min(r,g,b);
          if(br>210&&sat<30)d[i+3]=Math.round(Math.max(0,1-(br-210)/45)*255);
        }
        c.putImageData(id,0,0);
      }catch(e){}
      res(oc);
    };
    img.onerror=()=>res(null);
    img.src=src;
  });
}

class Bullet{
  constructor(x,y,dy,ie){this.x=x;this.y=y;this.dy=dy;this.isEnemy=ie;this.alive=true;}
  update(){this.y+=this.dy;if(this.y<-BH||this.y>H+BH)this.alive=false;}
  draw(){
    const g=ctx.createLinearGradient(this.x,this.y,this.x,this.y+BH);
    this.isEnemy?(g.addColorStop(0,'#ff0'),g.addColorStop(1,'#f00')):(g.addColorStop(0,'#fff'),g.addColorStop(1,'#0ff'));
    ctx.shadowBlur=10;ctx.shadowColor=this.isEnemy?'#f80':'#0ff';
    ctx.fillStyle=g;ctx.fillRect(this.x-BW/2,this.y,BW,BH);ctx.shadowBlur=0;
  }
}

class Player{
  constructor(s){this.sprite=s;this.x=W/2;this.y=H-55;this.speed=5;this.cd=0;this.flash=0;}
  update(keys,bullets){
    if(keys.ArrowLeft&&this.x-PW/2>4)this.x-=this.speed;
    if(keys.ArrowRight&&this.x+PW/2<W-4)this.x+=this.speed;
    if(this.cd>0)this.cd--;
    if(keys.Space&&this.cd===0){bullets.push(new Bullet(this.x,this.y-PH/2-2,-11,false));this.cd=18;}
    if(this.flash>0)this.flash--;
  }
  draw(){
    if(this.flash>0&&this.flash%6<3)ctx.globalAlpha=0.25;
    if(this.sprite)ctx.drawImage(this.sprite,this.x-PW/2,this.y-PH/2,PW,PH);
    else{ctx.fillStyle='#4af';ctx.beginPath();ctx.moveTo(this.x,this.y-PH/2);ctx.lineTo(this.x-PW/2,this.y+PH/2);ctx.lineTo(this.x+PW/2,this.y+PH/2);ctx.closePath();ctx.fill();}
    ctx.globalAlpha=1;
    ctx.shadowBlur=18;ctx.shadowColor='#0ff';ctx.fillStyle='#0ff';
    ctx.fillRect(this.x-5,this.y+PH/2-4,10,7);ctx.shadowBlur=0;
  }
  bounds(){return{x:this.x-PW/2+10,y:this.y-PH/2+10,w:PW-20,h:PH-20};}
}

class Enemy{
  constructor(c,r,s){this.col=c;this.row=r;this.sprite=s;this.x=0;this.y=0;this.alive=true;}
  draw(){
    if(!this.alive)return;
    if(this.sprite)ctx.drawImage(this.sprite,this.x-EW/2,this.y-EH/2,EW,EH);
    else{ctx.fillStyle='#f80';ctx.fillRect(this.x-EW/2,this.y-EH/2,EW,EH);}
  }
  bounds(){return{x:this.x-EW/2+8,y:this.y-EH/2+8,w:EW-16,h:EH-16};}
}

class EnemyGrid{
  constructor(s){this.sprite=s;this.dx=1.1;this.drop=28;this.sc=0.0018;this._build();}
  _build(){
    this.enemies=[];
    const tw=ECOLS*EW+(ECOLS-1)*EGX,sx=(W-tw)/2+EW/2,sy=90;
    for(let r=0;r<EROWS;r++)for(let c=0;c<ECOLS;c++){
      const e=new Enemy(c,r,this.sprite);
      e.x=sx+c*(EW+EGX);e.y=sy+r*(EH+EGY);
      this.enemies.push(e);
    }
  }
  get alive(){return this.enemies.filter(e=>e.alive);}
  update(bullets){
    const lv=this.alive;if(!lv.length)return;
    const ratio=lv.length/(ECOLS*EROWS);
    const spd=this.dx*(1+(1-ratio)*2.8);
    const mnX=Math.min(...lv.map(e=>e.x)),mxX=Math.max(...lv.map(e=>e.x));
    let drop=false;
    if(mxX+EW/2>=W-12){this.dx=-Math.abs(this.dx);drop=true;}
    else if(mnX-EW/2<=12){this.dx=Math.abs(this.dx);drop=true;}
    this.enemies.forEach(e=>{if(!e.alive)return;e.x+=spd;if(drop)e.y+=this.drop;});
    const sm=1+(1-ratio)*3.5;
    lv.forEach(e=>{if(Math.random()<this.sc*sm)bullets.push(new Bullet(e.x,e.y+EH/2,5.5,true));});
  }
  bottom(){return this.alive.some(e=>e.y+EH/2>H-90);}
}

function hit(b,r){return b.x>=r.x&&b.x<=r.x+r.w&&b.y>=r.y&&b.y<=r.y+r.h;}

class Game{
  constructor(es,ps){this.es=es;this.ps=ps;this.keys={};this.state='menu';this._bindKeys();requestAnimationFrame(()=>this._loop());}
  _bindKeys(){
    window.addEventListener('keydown',e=>{
      this.keys[e.code]=true;
      if(e.code==='Space'){e.preventDefault();if(this.state!=='playing')this._start();}
      if(e.code==='KeyR')this._start();
    });
    window.addEventListener('keyup',e=>{this.keys[e.code]=false;});
  }
  _start(){this.state='playing';this.score=0;this.lives=3;this.bullets=[];this.grid=new EnemyGrid(this.es);this.player=new Player(this.ps);}
  update(){
    if(this.state!=='playing')return;
    this.player.update(this.keys,this.bullets);
    this.grid.update(this.bullets);
    this.bullets.forEach(b=>b.update());
    this.bullets=this.bullets.filter(b=>b.alive);
    tickP();
    const lv=this.grid.alive;
    this.bullets.forEach(b=>{
      if(b.isEnemy||!b.alive)return;
      lv.forEach(e=>{if(!e.alive)return;if(hit(b,e.bounds())){b.alive=false;e.alive=false;spawnEx(e.x,e.y);this.score+=10;}});
    });
    const pb=this.player.bounds();
    this.bullets.forEach(b=>{
      if(!b.isEnemy||!b.alive)return;
      if(hit(b,pb)){b.alive=false;this.lives--;this.player.flash=40;spawnEx(this.player.x,this.player.y);if(this.lives<=0)this.state='gameover';}
    });
    if(!this.grid.alive.length)this.state='win';
    if(this.grid.bottom())this.state='gameover';
  }
  draw(){
    ctx.fillStyle='#000';ctx.fillRect(0,0,W,H);
    const t=Date.now()/1200;
    STARS.forEach(s=>{
      const a=s.alpha*(0.6+0.4*Math.sin(t+s.twinkle));
      ctx.beginPath();ctx.arc(s.x,s.y,s.r,0,Math.PI*2);
      ctx.fillStyle='rgba(255,255,255,'+a.toFixed(2)+')';ctx.fill();
    });
    if(this.state==='menu'){this._menu();return;}
    this.grid.enemies.forEach(e=>e.draw());
    drawP();
    this.bullets.forEach(b=>b.draw());
    this.player.draw();
    this._hud();
    if(this.state==='win')this._overlay('YOU WIN!','#0f0',isMobile?'TAP TO PLAY AGAIN':'PRESS SPACE TO PLAY AGAIN');
    if(this.state==='gameover')this._overlay('GAME OVER','#f44',isMobile?'TAP TO TRY AGAIN':'PRESS SPACE TO TRY AGAIN');
  }
  _hud(){
    ctx.textAlign='left';ctx.font='bold 22px Courier New';ctx.fillStyle='#0ff';
    ctx.shadowBlur=6;ctx.shadowColor='#0ff';ctx.fillText('SCORE: '+this.score,18,30);ctx.shadowBlur=0;
    ctx.textAlign='right';ctx.fillStyle=this.lives===1?'#f44':'#0ff';
    ctx.fillText('LIVES: '+'\\u2665 '.repeat(this.lives).trim(),W-18,30);
    ctx.strokeStyle='rgba(0,255,255,0.2)';ctx.lineWidth=1;
    ctx.beginPath();ctx.moveTo(0,38);ctx.lineTo(W,38);ctx.stroke();
  }
  _menu(){
    ctx.textAlign='center';
    ctx.font='bold 54px Courier New';ctx.fillStyle='#0ff';
    ctx.shadowBlur=24;ctx.shadowColor='#0ff';
    ctx.fillText('SPACE INVADERS',W/2,170);ctx.shadowBlur=0;
    ctx.font='bold 26px Courier New';ctx.fillStyle='#ff0';
    ctx.fillText('KHAMENEI  EDITION',W/2,218);
    if(this.es){ctx.save();ctx.shadowBlur=16;ctx.shadowColor='#f80';ctx.drawImage(this.es,W/2-52,250,104,128);ctx.restore();}
    const blink=Math.floor(Date.now()/500)%2===0;
    ctx.fillStyle='#fff';ctx.font='bold 22px Courier New';
    if(blink)ctx.fillText(isMobile?'\\u25b6  TAP TO START  \\u25c0':'PRESS  SPACE  TO  START',W/2,430);
    ctx.fillStyle='rgba(255,255,255,0.4)';ctx.font='15px Courier New';
    ctx.fillText(isMobile?'\\u25c0  MOVE  \\u25b6     \\ud83d\\udd25  FIRE':'\\u2190 \\u2192  move     SPACE  shoot     R  restart',W/2,468);
  }
  _overlay(title,color,sub){
    ctx.fillStyle='rgba(0,0,0,0.65)';ctx.fillRect(0,0,W,H);
    ctx.textAlign='center';ctx.font='bold 62px Courier New';ctx.fillStyle=color;
    ctx.shadowBlur=28;ctx.shadowColor=color;ctx.fillText(title,W/2,H/2-30);ctx.shadowBlur=0;
    ctx.font='bold 28px Courier New';ctx.fillStyle='#ff0';
    ctx.fillText('SCORE: '+this.score,W/2,H/2+30);
    const blink=Math.floor(Date.now()/500)%2===0;
    ctx.fillStyle='#fff';ctx.font='18px Courier New';
    if(blink)ctx.fillText(sub,W/2,H/2+78);
  }
  _loop(){this.update();this.draw();requestAnimationFrame(()=>this._loop());}
}

let game;
Promise.all([loadImg('__K__'),loadImg('__B__')]).then(([es,ps])=>{
  game=new Game(es,ps);
  function bt(id,key){
    const btn=document.getElementById(id);
    btn.addEventListener('touchstart',e=>{e.preventDefault();btn.classList.add('pressed');game.keys[key]=true;},{passive:false});
    btn.addEventListener('touchend',e=>{e.preventDefault();btn.classList.remove('pressed');game.keys[key]=false;},{passive:false});
    btn.addEventListener('touchcancel',()=>{btn.classList.remove('pressed');game.keys[key]=false;});
  }
  bt('btn-left','ArrowLeft');bt('btn-right','ArrowRight');bt('btn-fire','Space');
  canvas.addEventListener('touchend',e=>{e.preventDefault();if(game.state!=='playing')game._start();},{passive:false});
});
</script>
</body>
</html>"""

NEW_HTML = NEW_HTML.replace("'__K__'", f"'{K}'")
NEW_HTML = NEW_HTML.replace("'__B__'", f"'{B}'")

with open('space-invaders-standalone.html','w',encoding='utf-8') as f:
    f.write(NEW_HTML)

import os
print(f'Done! {os.path.getsize("space-invaders-standalone.html")//1024} KB')
