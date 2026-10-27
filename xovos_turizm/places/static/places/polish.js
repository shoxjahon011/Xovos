// Preloader, ripple va sarlavha animatsiyasi
(function () {
  const pre = document.getElementById('pre');
  const hide = () => pre && setTimeout(() => pre.classList.add('done'), 350);
  window.addEventListener('load', hide);
  setTimeout(hide, 3000); // internet sekin bo'lsa ham yopiladi

  document.addEventListener('pointerdown', e => {
    const el = e.target.closest('button,.btn,.tile,.tr-btns a');
    if (!el) return;
    const r = el.getBoundingClientRect(), s = Math.max(r.width, r.height);
    const d = document.createElement('span');
    d.className = 'ripple';
    d.style.cssText = `width:${s}px;height:${s}px;left:${e.clientX - r.left - s / 2}px;top:${e.clientY - r.top - s / 2}px`;
    el.appendChild(d);
    setTimeout(() => d.remove(), 650);
  });

  const top = document.querySelector('.top');
  addEventListener('scroll', () => top && top.classList.toggle('small', scrollY > 30), {passive: true});
})();