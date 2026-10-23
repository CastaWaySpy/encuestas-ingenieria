(() => {
  const form = document.getElementById("strategyForm");
  const button = document.getElementById("generateBtn");
  const notice = document.getElementById("loadingNotice");
  if (!form) return;
  form.addEventListener("submit", () => {
    if (button) { button.disabled = true; button.textContent = "Generando estrategia…"; }
    if (notice) notice.classList.remove("d-none");
  });
})();
