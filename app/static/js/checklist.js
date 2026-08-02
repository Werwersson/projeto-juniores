/* =====================================================
   TeoK!ds. — Checklist com celebração
   ===================================================== */

const COLORS = ['#9b1bcc','#4a6cf7','#00cfff','#00e5a0','#ff6b35','#ff3da0','#fbbf24'];

function criarConfete(qtd = 80) {
  const container = document.createElement('div');
  container.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9999;overflow:hidden;';
  document.body.appendChild(container);

  for (let i = 0; i < qtd; i++) {
    const p = document.createElement('div');
    const cor   = COLORS[Math.floor(Math.random() * COLORS.length)];
    const x     = Math.random() * 100;
    const delay = Math.random() * 0.6;
    const dur   = 1.2 + Math.random() * 1.2;
    const size  = 6 + Math.random() * 8;
    const shape = Math.random() > 0.5 ? '50%' : '2px';
    p.style.cssText = `position:absolute;left:${x}%;top:-20px;width:${size}px;height:${size}px;background:${cor};border-radius:${shape};animation:tkcair ${dur}s ${delay}s ease-in forwards;transform:rotate(${Math.random()*360}deg);`;
    container.appendChild(p);
  }
  setTimeout(() => container.remove(), 2800);
}

function mostrarToast(msg, icone) {
  icone = icone || '🎉';
  const t = document.createElement('div');
  t.innerHTML = '<span style="font-size:1.4rem">' + icone + '</span><span>' + msg + '</span>';
  t.style.cssText = 'position:fixed;bottom:100px;left:50%;transform:translateX(-50%) translateY(20px);background:linear-gradient(135deg,#9b1bcc,#4a6cf7);color:#fff;font-family:Nunito,sans-serif;font-weight:800;font-size:0.95rem;padding:14px 24px;border-radius:40px;box-shadow:0 8px 32px rgba(124,58,237,0.4);z-index:10000;opacity:0;transition:all 0.35s cubic-bezier(0.34,1.56,0.64,1);white-space:nowrap;display:flex;align-items:center;gap:10px;';
  document.body.appendChild(t);
  requestAnimationFrame(function() {
    t.style.opacity = '1';
    t.style.transform = 'translateX(-50%) translateY(0)';
  });
  setTimeout(function() {
    t.style.opacity = '0';
    t.style.transform = 'translateX(-50%) translateY(20px)';
    setTimeout(function() { t.remove(); }, 400);
  }, 2800);
}

function atualizarBarra(done, total) {
  var barra = document.getElementById('tk-progress-fill');
  var texto = document.getElementById('tk-progress-text');
  if (!barra || !total) return;
  barra.style.width = Math.round((done / total) * 100) + '%';
  if (texto) texto.textContent = done + ' / ' + total + ' concluídas';
}

function inicializarChecklist() {
  var forms = document.querySelectorAll('.tk-check-form');
  var total = parseInt(document.getElementById('tk-total-atividades') ? document.getElementById('tk-total-atividades').textContent : forms.length);

  forms.forEach(function(form) {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      var btn    = this.querySelector('button[type="submit"]');
      var doneEl = document.getElementById('tk-done-count');
      var done   = parseInt(doneEl ? doneEl.textContent : '0') + 1;

      // Visual imediato
      btn.disabled = true;
      btn.classList.add('done');
      var circle = btn.querySelector('.tk-check-circle');
      if (circle) {
        circle.innerHTML = '<i class="bi bi-check-lg" style="color:#fff;font-weight:800;"></i>';
        circle.style.background = 'linear-gradient(135deg,#00e5a0,#00bfff)';
        circle.style.borderColor = 'transparent';
      }
      var pts = btn.querySelector('.tk-check-pts');
      if (pts) pts.textContent = '✅ Concluída hoje';
      var arrow = btn.querySelector('.bi-arrow-right');
      if (arrow) arrow.remove();

      if (doneEl) doneEl.textContent = done;
      atualizarBarra(done, total);

      var premiles = btn.dataset.premiles || '10';

      if (done >= total) {
        criarConfete(120);
        mostrarToast('Incrível! Você completou tudo hoje!', '🏆');
        var saldoEl = document.querySelector('.tk-premiles');
        if (saldoEl) {
          var escalas = ['scale(1.3)','scale(1)','scale(1.3)','scale(1)'];
          escalas.forEach(function(s, i) {
            setTimeout(function() { saldoEl.style.transform = s; }, i * 100);
          });
        }
      } else {
        criarConfete(30);
        mostrarToast('+' + premiles + ' Premiles! Continue assim! ⚡');
      }

      var f = form;
      setTimeout(function() { f.submit(); }, 650);
    });
  });
}

// Injeta keyframe via JS
var s = document.createElement('style');
s.textContent = '@keyframes tkcair{0%{transform:translateY(0) rotate(0deg);opacity:1}100%{transform:translateY(105vh) rotate(720deg);opacity:0}}';
document.head.appendChild(s);

document.addEventListener('DOMContentLoaded', inicializarChecklist);
