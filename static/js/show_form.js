const menuButtons = document.querySelectorAll(".menu-button");

function closeAllMenus() {
  const allMenus = document.querySelectorAll(".menu");
  allMenus.forEach((menu) => {
    menu.classList.remove("show");
  });
  const allButtons = document.querySelectorAll(".menu-button");
  allButtons.forEach((button) => {
    button.classList.remove("active");
  });
}

// Añadir evento click a los botones del menú
menuButtons.forEach((button) => {
  button.addEventListener("click", function (event) {
    event.stopPropagation();
    const menuId = this.getAttribute("data-menu-id");
    const menu = document.getElementById(menuId);
    const otherMenus = document.querySelectorAll(".menu:not(#" + menuId + ")");

    otherMenus.forEach((otherMenu) => {
      otherMenu.classList.remove("show");
    });

    if (menu.classList.contains("show")) {
      menu.classList.remove("show");
      this.classList.remove("active");
    } else {
      menu.classList.add("show");
      this.classList.add("active");
    }
  });
});

// Añadir evento submit a los formularios dentro de los menús
const forms = document.querySelectorAll(".menu form");

forms.forEach((form) => {
  form.addEventListener("submit", function (event) {
    setTimeout(() => {
      form.reset();

      const menu = form.closest(".menu");
      if (menu) {
        menu.classList.remove("show");
      }

      const relatedButton = document.querySelector(
        '.menu-button[data-menu-id="' + menu.id + '"]'
      );
      if (relatedButton) {
        relatedButton.classList.remove("active");
      }
    }, 500);
  });
});

// Cerrar el menú al hacer clic fuera de él
document.addEventListener("click", function (event) {
  const isClickInsideMenu =
    event.target.closest(".menu") || event.target.closest(".menu-button");
  if (!isClickInsideMenu) {
    closeAllMenus();
  }
});
