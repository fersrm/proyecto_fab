const scrollToTopButton = document.getElementById("scrollToTopButton");

window.addEventListener("scroll", () => {
  if (window.scrollY > 300) {
    scrollToTopButton.classList.add("show");
  } else {
    scrollToTopButton.classList.remove("show");
  }
});

scrollToTopButton.addEventListener("click", () => {
  window.scrollTo({
    top: 0,
    behavior: "smooth",
  });
});

/////////////////////////
document.querySelectorAll(".scroll-link").forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();

    const targetId = this.getAttribute("href").substring(1);
    const targetElement = document.getElementById(targetId);
    const offset = 90; // Ajustar según el margen

    window.scrollTo({
      top: targetElement.offsetTop - offset,
      behavior: "smooth",
    });
  });
});
