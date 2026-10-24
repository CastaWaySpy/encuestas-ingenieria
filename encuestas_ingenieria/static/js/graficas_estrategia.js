(() => {
  const box = document.getElementById("graficasEstrategia");
  if (!box || typeof Chart === "undefined") return;
  let stats;
  try { stats = JSON.parse(box.dataset.stats); } catch (e) { return; }
  const barras = (id, distribucion) => {
    const items = (distribucion || []).filter(x => x.count > 0);
    if (!items.length) {
      box.querySelector("#" + id).insertAdjacentHTML("afterend", '<p class="field-help mb-0">Sin datos para mostrar.</p>');
      return;
    }
    new Chart(document.getElementById(id), {
      type: "bar",
      data: { labels: items.map(x => x.label), datasets: [{ label: "Respuestas", data: items.map(x => x.count), borderWidth: 1 }] },
      options: { indexAxis: "y", responsive: true, plugins: { legend: { display: false } },
                 scales: { x: { beginAtZero: true, ticks: { precision: 0 } } } }
    });
  };
  barras("gMain", stats.main_distribution);
  barras("gInfluence", stats.influence_distribution);
  barras("gContent", stats.content_distribution);
  barras("gAdditional", stats.additional_distribution);
})();
