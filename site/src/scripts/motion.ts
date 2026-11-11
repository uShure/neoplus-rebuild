import { animate, inView, stagger } from "motion";

/**
 * Анимации сайта (motion.dev / WAAPI).
 * Отключаются при prefers-reduced-motion; запускаются после load+idle,
 * чтобы не попадать в окно TBT при загрузке. Пред-скрытие — через CSS
 * (html.anim), а не из JS.
 */
const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const EASE: [number, number, number, number] = [0.22, 1, 0.36, 1];

function cleanup(el: HTMLElement) {
  el.style.opacity = "";
  el.style.transform = "";
}

function init() {
  // живой градиент hero — включаем после idle
  document.querySelector(".hero-pan")?.classList.add("hero-pan-run");

  const belowFold = (el: HTMLElement) =>
    el.getBoundingClientRect().top > window.innerHeight * 0.9;

  // 1) Секции кроме первой (hero остаётся мгновенным): fade-up по скроллу.
  const sections = Array.from(
    document.querySelectorAll<HTMLElement>("main > section:not(:first-child)")
  );
  if (sections.length) {
    const scrollSections: HTMLElement[] = [];
    for (const el of sections) {
      if (belowFold(el)) scrollSections.push(el);
      else el.classList.add("is-revealed");
    }
    if (scrollSections.length) {
      inView(
        scrollSections,
        (el) => {
          el.classList.add("is-revealed");
          const a = animate(
            el,
            { opacity: [0, 1], transform: ["translateY(14px)", "translateY(0px)"] },
            { duration: 0.5, ease: EASE }
          );
          a.finished.then(() => cleanup(el));
        },
        { margin: "0px 0px -8% 0px" }
      );
    }
  }

  // 2) Поэлементный reveal с вариантами: data-reveal="up" (по умолч.) | "scale" | "left" | "right"
  const VARIANTS: Record<string, { opacity: number[]; transform: string[] }> = {
    up: { opacity: [0, 1], transform: ["translateY(14px)", "translateY(0px)"] },
    scale: { opacity: [0, 1], transform: ["scale(0.94)", "scale(1)"] },
    left: { opacity: [0, 1], transform: ["translateX(-18px)", "translateX(0px)"] },
    right: { opacity: [0, 1], transform: ["translateX(18px)", "translateX(0px)"] },
  };
  const revealEls = Array.from(document.querySelectorAll<HTMLElement>("[data-reveal]"));
  if (revealEls.length) {
    const scrollReveal: HTMLElement[] = [];
    for (const el of revealEls) {
      if (belowFold(el)) scrollReveal.push(el);
      else el.classList.add("is-revealed");
    }
    if (scrollReveal.length) {
      inView(
        scrollReveal,
        (el) => {
          const v = VARIANTS[el.dataset.reveal || "up"] || VARIANTS.up;
          el.classList.add("is-revealed");
          const a = animate(el, v, { duration: 0.45, ease: EASE });
          a.finished.then(() => cleanup(el));
        },
        { margin: "0px 0px -6% 0px" }
      );
    }
  }

  // 3) Каскад для сеток/групп: data-stagger на контейнере
  const groups = Array.from(document.querySelectorAll<HTMLElement>("[data-stagger]"));
  if (groups.length) {
    const scrollGroups: HTMLElement[] = [];
    for (const g of groups) {
      if (g.closest("main > section:first-child")) continue; // hero анимируется CSS-ом
      const kids = Array.from(g.children) as HTMLElement[];
      if (!belowFold(g)) {
        for (const k of kids) cleanup(k);
        continue;
      }
      for (const k of kids) k.style.opacity = "0";
      scrollGroups.push(g);
    }
    if (scrollGroups.length) {
      inView(
        scrollGroups,
        (g) => {
          const kids = Array.from(g.children) as HTMLElement[];
          const a = animate(
            kids,
            { opacity: [0, 1], transform: ["translateY(12px)", "translateY(0px)"] },
            { delay: stagger(0.06), duration: 0.45, ease: EASE }
          );
          a.finished.then(() => kids.forEach(cleanup));
        },
        { margin: "0px 0px -8% 0px" }
      );
    }
  }

  // 4) Счётчики цифр: data-count-to / data-count-suffix
  const counters = Array.from(document.querySelectorAll<HTMLElement>("[data-count-to]"));
  if (counters.length) {
    inView(
      counters,
      (el) => {
        const to = parseFloat(el.dataset.countTo || "0");
        const suffix = el.dataset.countSuffix ?? "";
        const a = animate(0, to, {
          duration: 1.2,
          ease: EASE,
          onUpdate: (v) => {
            el.textContent = String(Math.round(v)) + suffix;
          },
        });
        a.finished.then(() => {
          el.textContent = String(to) + suffix;
        });
      },
      { amount: 0.5 }
    );
  }

  // 5) Карусели: data-carousel (scroll-snap) + стрелки
  for (const root of Array.from(document.querySelectorAll<HTMLElement>("[data-carousel]"))) {
    const track = root.querySelector<HTMLElement>("[data-carousel-track]");
    const prev = root.querySelector<HTMLElement>("[data-carousel-prev]");
    const next = root.querySelector<HTMLElement>("[data-carousel-next]");
    if (!track) continue;
    const step = () => {
      const card = track.querySelector<HTMLElement>(":scope > *");
      return card ? card.getBoundingClientRect().width + 16 : 260;
    };
    prev?.addEventListener("click", () => track.scrollBy({ left: -step(), behavior: "smooth" }));
    next?.addEventListener("click", () => track.scrollBy({ left: step(), behavior: "smooth" }));
    const sync = () => {
      if (!prev || !next) return;
      const max = track.scrollWidth - track.clientWidth - 4;
      prev.style.opacity = track.scrollLeft <= 4 ? "0.35" : "1";
      next.style.opacity = track.scrollLeft >= max ? "0.35" : "1";
    };
    track.addEventListener("scroll", sync, { passive: true });
    sync();
  }
}

if (!reduced) {
  if (document.readyState === "complete") {
    setTimeout(init, 600);
  } else {
    window.addEventListener(
      "load",
      () => setTimeout(init, 600),
      { once: true }
    );
  }
}
