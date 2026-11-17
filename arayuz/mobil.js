// Lintu FireAtlas · © 2026 Team Lintu · AGPL-3.0 · https://github.com/Lintuteam/lintu-fireatlas
/* Mobil: süzgeç panelini açılır/kapanır yap (dar ekranda varsayılan kapalı). */
(function () {
  const f = document.querySelector(".filters"); if (!f) return;
  const en = () => document.documentElement.lang === "en";
  const b = document.createElement("button"); b.type = "button"; b.className = "ftog"; b.setAttribute("aria-expanded", "false");
  const lbl = () => { const o = !f.classList.contains("mcol"); b.textContent = (en() ? "Filters" : "Süzgeçler") + (o ? " ▴" : " ▾"); b.setAttribute("aria-expanded", String(o)); };
  b.addEventListener("click", () => { f.classList.toggle("mcol"); lbl(); });
  f.insertBefore(b, f.firstChild);
  if (window.matchMedia("(max-width:900px)").matches) f.classList.add("mcol");
  lbl(); new MutationObserver(lbl).observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
})();
