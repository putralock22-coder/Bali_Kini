(function(){
  const c=document.getElementById('glc');
  if(!c)return;
  const gl=c.getContext('webgl')||c.getContext('experimental-webgl');
  if(!gl)return;
  function sh(type,src){const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);return s;}
  const prog=gl.createProgram();
  gl.attachShader(prog,sh(gl.VERTEX_SHADER,`attribute vec2 p;void main(){gl_Position=vec4(p,0,1);}`));
  gl.attachShader(prog,sh(gl.FRAGMENT_SHADER,`
    precision highp float;
    uniform vec2 r;uniform float t;
    void main(){
      vec2 p=(gl_FragCoord.xy*2.0-r)/min(r.x,r.y);
      float d=length(p)*0.035;
      float rx=p.x*(1.0+d),gx=p.x,bx=p.x*(1.0-d);
      float s=0.9,y=0.38;
      float R=0.032/abs(p.y+sin((rx+t)*s)*y);
      float G=0.032/abs(p.y+sin((gx+t)*s)*y);
      float B=0.032/abs(p.y+sin((bx+t)*s)*y);
      gl_FragColor=vec4(R,G,B,1.0);
    }
  `));
  gl.linkProgram(prog);gl.useProgram(prog);
  const buf=gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER,buf);
  gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,-1,1,1,-1,1]),gl.STATIC_DRAW);
  const loc=gl.getAttribLocation(prog,'p');
  gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc,2,gl.FLOAT,false,0,0);
  const ur=gl.getUniformLocation(prog,'r');
  const ut=gl.getUniformLocation(prog,'t');
  function resize(){c.width=window.innerWidth;c.height=window.innerHeight;gl.viewport(0,0,c.width,c.height);gl.uniform2f(ur,c.width,c.height);}
  window.addEventListener('resize',resize);resize();
  let time=0;
  (function frame(){time+=0.006;gl.uniform1f(ut,time);gl.drawArrays(gl.TRIANGLES,0,6);requestAnimationFrame(frame);})();

  // Scroll reveal
  const io=new IntersectionObserver(entries=>{
    entries.forEach(e=>{if(e.isIntersecting)e.target.classList.add('visible');});
  },{threshold:0.08});
  document.querySelectorAll('.reveal').forEach(el=>io.observe(el));

  // Animate bars
  const barIO=new IntersectionObserver(entries=>{
    entries.forEach(e=>{
      if(e.isIntersecting){
        e.target.querySelectorAll('.bbar').forEach(b=>{b.style.width=b.dataset.w+'%';});
        barIO.unobserve(e.target);
      }
    });
  },{threshold:0.2});
  document.querySelectorAll('.card').forEach(c=>barIO.observe(c));
})();
