(() => {
  const form = document.getElementById("surveyForm");
  if (!form) return;
  const comments = document.getElementById("comments");
  const count = document.getElementById("charCount");
  const age = document.getElementById("age");
  const updateCount = () => { if (comments && count) count.textContent = comments.value.length; };
  comments?.addEventListener("input", updateCount);
  form.addEventListener("reset", () => setTimeout(updateCount, 0));
  updateCount();
  form.addEventListener("submit", (event) => {
    if (age?.value && (Number(age.value) < 15 || Number(age.value) > 100)) age.setCustomValidity("La edad debe estar entre 15 y 100.");
    else age?.setCustomValidity("");
    if (!form.checkValidity()) {
      event.preventDefault();
      event.stopPropagation();
      form.classList.add("was-validated");
    }
  });
})();
