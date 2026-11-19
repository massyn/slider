// Slide navigation: next/previous reveals each .step in turn, then moves slides.
// Keys: Right/Space/PageDown = next, Left/PageUp = back, Home/End, F = fullscreen.
// Every slide and .step may carry data-voice: the narration for that moment.
// Click the right two thirds to go forward, the left third to go back; swipe on touch.
(() => {
  const slides = [...document.querySelectorAll(".slide")];
  const counter = document.querySelector(".counter");
  const progress = document.querySelector(".progress");
  let index = 0;
  let step = 0;

  const stepsOf = (i) => slides[i].querySelectorAll(".step");

  function show(i, s) {
    index = Math.max(0, Math.min(i, slides.length - 1));
    step = Math.max(0, Math.min(s, stepsOf(index).length));
    slides.forEach((el, n) => {
      el.classList.toggle("past", n < index);
      el.classList.toggle("current", n === index);
      el.toggleAttribute("inert", n !== index);
    });
    stepsOf(index).forEach((el, n) => el.classList.toggle("shown", n < step));
    counter.textContent = `${index + 1} / ${slides.length}`;
    progress.style.width = `${((index + 1) / slides.length) * 100}%`;
    history.replaceState(null, "", `#${index + 1}`);
  }

  function next() {
    if (step < stepsOf(index).length) show(index, step + 1);
    else if (index < slides.length - 1) show(index + 1, 0);
  }

  function prev() {
    if (step > 0) show(index, step - 1);
    else if (index > 0) show(index - 1, stepsOf(index - 1).length);
  }

  // Jumping straight to a slide shows it fully revealed
  const jump = (i) => show(i, stepsOf(Math.max(0, Math.min(i, slides.length - 1))).length);

  document.addEventListener("keydown", (e) => {
    if (e.altKey || e.ctrlKey || e.metaKey) return;
    const actions = {
      ArrowRight: next, ArrowDown: next, PageDown: next, " ": next, Enter: next,
      ArrowLeft: prev, ArrowUp: prev, PageUp: prev, Backspace: prev,
      Home: () => jump(0),
      End: () => jump(slides.length - 1),
      f: () => document.fullscreenElement
        ? document.exitFullscreen()
        : document.documentElement.requestFullscreen(),
    };
    const action = actions[e.key];
    if (action) { e.preventDefault(); action(); }
  });

  document.addEventListener("click", (e) => {
    if (e.target.closest("a")) return;
    (e.clientX < window.innerWidth / 3 ? prev : next)();
  });

  let touchX = null;
  document.addEventListener("touchstart", (e) => { touchX = e.touches[0].clientX; }, { passive: true });
  document.addEventListener("touchend", (e) => {
    if (touchX === null) return;
    const dx = e.changedTouches[0].clientX - touchX;
    touchX = null;
    if (Math.abs(dx) > 40) (dx < 0 ? next : prev)();
  });

  const fromHash = () => parseInt(location.hash.slice(1), 10) - 1;
  window.addEventListener("hashchange", () => {
    const i = fromHash();
    if (!Number.isNaN(i) && i !== index) jump(i);
  });

  // Used by the video builder to step through the deck
  window.slider = { show };

  const start = fromHash();
  if (Number.isNaN(start)) show(0, 0); else jump(start);
})();
