// Count-up animation for the hero stat
const el = document.getElementById("kcal");
const target = 2150;
const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

if (reduce) {
  el.textContent = target.toLocaleString();
} else {
  const duration = 1800;
  const start = performance.now() + 700; // starts after the headline rises
  function tick(now) {
    const t = Math.min(Math.max((now - start) / duration, 0), 1);
    const eased = 1 - Math.pow(1 - t, 3);
    el.textContent = Math.round(target * eased).toLocaleString();
    if (t < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}