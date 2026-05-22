(function () {
  const cfg = window.CROWDVISE || {};

  document.querySelectorAll('[data-cv-href]').forEach((el) => {
    const key = el.getAttribute('data-cv-href');
    if (cfg[key]) el.setAttribute('href', cfg[key]);
  });

  const cursor = document.getElementById('cursor');
  const ring = document.getElementById('cursorRing');
  const useCustomCursor =
    cursor &&
    ring &&
    window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  if (!useCustomCursor) {
    document.body.style.cursor = '';
    cursor?.remove();
    ring?.remove();
  } else {
    document.body.classList.add('custom-cursor');
    let mx = 0;
    let my = 0;
    let rx = 0;
    let ry = 0;

    document.addEventListener('mousemove', (e) => {
      mx = e.clientX;
      my = e.clientY;
    });

    function animateCursor() {
      cursor.style.left = mx + 'px';
      cursor.style.top = my + 'px';
      rx += (mx - rx) * 0.12;
      ry += (my - ry) * 0.12;
      ring.style.left = rx + 'px';
      ring.style.top = ry + 'px';
      requestAnimationFrame(animateCursor);
    }
    animateCursor();
  }

  const reveals = document.querySelectorAll('.reveal');
  if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add('visible');
            observer.unobserve(e.target);
          }
        });
      },
      { threshold: 0.1 }
    );
    reveals.forEach((r) => observer.observe(r));
  } else {
    reveals.forEach((r) => r.classList.add('visible'));
  }
})();
