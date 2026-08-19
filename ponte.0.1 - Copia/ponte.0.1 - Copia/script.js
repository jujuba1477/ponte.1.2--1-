const header = document.querySelector("[data-header]");
const menuToggle = document.querySelector("[data-menu-toggle]");
const mobileNav = document.querySelector("[data-mobile-nav]");
const menuIcon = menuToggle?.querySelector(".menu-icon");
const navLinks = document.querySelectorAll('a[href^="#"]');
const sections = document.querySelectorAll("[data-route]");
const form = document.querySelector("[data-contact-form]");
const formStatus = document.querySelector("[data-form-status]");
const amountButtons = document.querySelectorAll(".amount-button");
const openModalButtons = document.querySelectorAll("[data-open-modal]");
const closeModalButtons = document.querySelectorAll("[data-close-modal]");
const modalBackdrop = document.querySelector("[data-modal-backdrop]");
const modals = document.querySelectorAll("[data-modal]");
const itemChoices = document.querySelectorAll("[data-item-choice]");
const itemDonationForm = document.querySelector("[data-item-donation-form]");
const itemDonationStatus = document.querySelector("[data-item-donation-status]");
const volunteerForm = document.querySelector("[data-volunteer-form]");
const volunteerStatus = document.querySelector("[data-volunteer-status]");

const sectionIds = new Set([...sections].map((section) => section.id));
const API_BASE_URLS = (() => {
  const { protocol, hostname, port } = window.location;
  const isHttp = protocol === "http:" || protocol === "https:";
  const isLocalHost = hostname === "localhost" || hostname === "127.0.0.1";
  const urls = [];

  if (isHttp) {
    urls.push("");
  }

  if (!isHttp || isLocalHost) {
    urls.push("http://127.0.0.1:3000");
  }

  return [...new Set(urls)];
})();
let activeModal = null;
let lastFocusedElement = null;

class ApiResponseError extends Error {
  constructor(message) {
    super(message);
    this.name = "ApiResponseError";
  }
}

const getFormPayload = (formElement) => {
  return Object.fromEntries(new FormData(formElement).entries());
};

const saveLocally = (collection, payload) => {
  const storageKey = `ponte-esperanca:${collection}`;
  const currentItems = JSON.parse(localStorage.getItem(storageKey) || "[]");
  const record = {
    ...payload,
    id: crypto.randomUUID?.() || String(Date.now()),
    createdAt: new Date().toISOString(),
    savedBy: "localStorage",
  };

  currentItems.push(record);
  localStorage.setItem(storageKey, JSON.stringify(currentItems));
  return record;
};

const readApiErrorMessage = async (response) => {
  try {
    const data = await response.json();

    if (data?.error) {
      return data.error;
    }
  } catch (error) {
    console.warn("Nao foi possivel ler a resposta de erro da API.", error);
  }

  return `API respondeu com status ${response.status}.`;
};

const sendToApi = async (endpoint, payload) => {
  let lastConnectionError = null;

  for (const baseUrl of API_BASE_URLS) {
    const response = await fetch(`${baseUrl}${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }).catch((error) => {
      lastConnectionError = error;
      return null;
    });

    if (!response) {
      continue;
    }

    if (!response.ok) {
      const message = await readApiErrorMessage(response);
      const shouldTryDefaultApi =
        baseUrl === "" &&
        response.status === 404 &&
        API_BASE_URLS.length > 1;

      if (shouldTryDefaultApi) {
        lastConnectionError = new Error(message);
        continue;
      }

      throw new ApiResponseError(message);
    }

    return response.json();
  }

  throw lastConnectionError || new Error("API indisponivel.");
};

const submitRecord = async ({ endpoint, collection, payload }) => {
  try {
    const result = await sendToApi(endpoint, payload);
    return { mode: "api", result };
  } catch (error) {
    if (error instanceof ApiResponseError) {
      console.error("A API respondeu com erro.", error);
      return { mode: "error", error };
    }

    console.warn("API indisponível; salvando localmente.", error);
    const result = saveLocally(collection, payload);
    return { mode: "local", result };
  }
};

const getSaveMessage = (mode, successText, error = null) => {
  if (mode === "api") {
    return successText;
  }

  if (mode === "error") {
    return `Não foi possível registrar na API. ${error?.message || "Verifique o backend Python."}`;
  }

  return `${successText} A API não respondeu, então os dados foram salvos neste navegador.`;
};

const normalizeHash = () => {
  const hash = window.location.hash.replace("#", "");

  if (!hash || !sectionIds.has(hash)) {
    return "inicio";
  }

  return hash;
};

const closeMenu = () => {
  if (!menuToggle || !mobileNav) {
    return;
  }

  menuToggle.setAttribute("aria-expanded", "false");
  menuToggle.setAttribute("aria-label", "Abrir navegação");
  mobileNav.classList.remove("is-open");
  document.body.classList.remove("menu-open");

  if (menuIcon) {
    menuIcon.textContent = "☰";
  }
};

const openMenu = () => {
  if (!menuToggle || !mobileNav) {
    return;
  }

  menuToggle.setAttribute("aria-expanded", "true");
  menuToggle.setAttribute("aria-label", "Fechar navegação");
  mobileNav.classList.add("is-open");
  document.body.classList.add("menu-open");

  if (menuIcon) {
    menuIcon.textContent = "×";
  }
};

const getFocusableElements = (container) => {
  return [
    ...container.querySelectorAll(
      'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
    ),
  ].filter((element) => element.offsetParent !== null);
};

const closeModal = () => {
  if (activeModal) {
    activeModal.hidden = true;
    activeModal = null;
  }

  if (modalBackdrop) {
    modalBackdrop.hidden = true;
  }

  document.body.classList.remove("modal-open");
  lastFocusedElement?.focus();
  lastFocusedElement = null;
};

const openModal = (modalId) => {
  const modal = document.getElementById(modalId);

  if (!modal) {
    return;
  }

  closeMenu();

  if (activeModal) {
    activeModal.hidden = true;
  }

  lastFocusedElement = document.activeElement;
  activeModal = modal;
  activeModal.hidden = false;

  if (modalBackdrop) {
    modalBackdrop.hidden = false;
  }

  document.body.classList.add("modal-open");

  activeModal.querySelectorAll(".form-status").forEach((status) => {
    status.textContent = "";
  });

  getFocusableElements(activeModal)[0]?.focus();
};

const trapModalFocus = (event) => {
  if (!activeModal) {
    return;
  }

  const focusableElements = getFocusableElements(activeModal);
  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  if (!firstElement || !lastElement) {
    return;
  }

  if (event.shiftKey && document.activeElement === firstElement) {
    event.preventDefault();
    lastElement.focus();
  } else if (!event.shiftKey && document.activeElement === lastElement) {
    event.preventDefault();
    firstElement.focus();
  }
};

const setActiveRoute = (routeId = normalizeHash()) => {
  navLinks.forEach((link) => {
    const isActive = link.getAttribute("href") === `#${routeId}`;
    link.classList.toggle("is-active", isActive);

    if (isActive) {
      link.setAttribute("aria-current", "page");
    } else {
      link.removeAttribute("aria-current");
    }
  });
};

const updateHeader = () => {
  header?.classList.toggle("is-scrolled", window.scrollY > 8);
};

menuToggle?.addEventListener("click", () => {
  const isOpen = menuToggle.getAttribute("aria-expanded") === "true";

  if (isOpen) {
    closeMenu();
  } else {
    openMenu();
  }
});

mobileNav?.addEventListener("click", (event) => {
  if (event.target.closest("a")) {
    closeMenu();
  }
});

document.addEventListener("click", (event) => {
  if (!mobileNav || !menuToggle) {
    return;
  }

  const isOpen = menuToggle.getAttribute("aria-expanded") === "true";
  const clickedMenu = mobileNav.contains(event.target);
  const clickedToggle = menuToggle.contains(event.target);

  if (isOpen && !clickedMenu && !clickedToggle) {
    closeMenu();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeMenu();
    closeModal();
  }

  if (event.key === "Tab") {
    trapModalFocus(event);
  }
});

window.addEventListener("hashchange", () => {
  setActiveRoute();
  closeMenu();
});

window.addEventListener("scroll", updateHeader, { passive: true });

window.addEventListener("resize", () => {
  if (window.matchMedia("(min-width: 1081px)").matches) {
    closeMenu();
  }
});

amountButtons.forEach((button) => {
  button.addEventListener("click", () => {
    amountButtons.forEach((item) => item.classList.remove("is-selected"));
    button.classList.add("is-selected");
  });
});

openModalButtons.forEach((button) => {
  button.addEventListener("click", () => {
    openModal(button.dataset.openModal);
  });
});

closeModalButtons.forEach((button) => {
  button.addEventListener("click", closeModal);
});

modalBackdrop?.addEventListener("click", closeModal);

modals.forEach((modal) => {
  modal.addEventListener("click", (event) => {
    if (event.target === modal) {
      closeModal();
    }
  });
});

itemChoices.forEach((button) => {
  button.addEventListener("change", () => {
    itemChoices.forEach((item) => {
      item.closest(".item-choice")?.classList.toggle("is-selected", item.checked);
    });
  });
});

form?.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (formStatus) {
    formStatus.textContent = "Enviando mensagem...";
  }

  const payload = getFormPayload(form);
  const { mode, error } = await submitRecord({
    endpoint: "/api/contact",
    collection: "contacts",
    payload,
  });

  if (formStatus) {
    formStatus.textContent = getSaveMessage(mode, "Mensagem registrada com sucesso.", error);
  }

  if (mode === "api") {
    form.reset();
  }
});

itemDonationForm?.addEventListener("submit", async (event) => {
  event.preventDefault();

  const selectedItem = itemDonationForm.querySelector("[data-item-choice]:checked");
  const itemLabel = selectedItem?.dataset.itemLabel || "item";

  if (itemDonationStatus) {
    itemDonationStatus.textContent = "Registrando doação...";
  }

  const payload = {
    ...getFormPayload(itemDonationForm),
    itemType: itemLabel,
  };
  const { mode, error } = await submitRecord({
    endpoint: "/api/item-donations",
    collection: "item-donations",
    payload,
  });

  if (itemDonationStatus) {
    itemDonationStatus.textContent = getSaveMessage(
      mode,
      `Doação de ${itemLabel.toLowerCase()} registrada com sucesso.`,
      error
    );
  }

  if (mode === "api") {
    itemDonationForm.reset();
  }
});

volunteerForm?.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (volunteerStatus) {
    volunteerStatus.textContent = "Confirmando inscrição...";
  }

  const payload = {
    type: "volunteer",
  };
  const { mode, error } = await submitRecord({
    endpoint: "/api/volunteers",
    collection: "volunteers",
    payload,
  });

  if (volunteerStatus) {
    volunteerStatus.textContent = getSaveMessage(
      mode,
      "Inscrição de voluntário confirmada.",
      error
    );
  }
});

if (!window.location.hash || !sectionIds.has(window.location.hash.slice(1))) {
  history.replaceState(null, "", "#inicio");
}

setActiveRoute();
updateHeader();

const themeToggle = document.querySelector("[data-theme-toggle]");
const themeLabel = document.querySelector("[data-theme-label]");
const themeStorageKey = "ponte-esperanca:theme";

const updateThemeControl = () => {
  const isDark = document.body.classList.contains("tema-escuro");

  if (themeToggle) {
    themeToggle.setAttribute("aria-pressed", String(isDark));
    themeToggle.querySelector(".material-symbols-outlined").textContent = isDark ? "light_mode" : "dark_mode";
  }

  if (themeLabel) {
    themeLabel.textContent = isDark ? "Modo claro" : "Modo escuro";
  }
};

const savedTheme = localStorage.getItem(themeStorageKey);
const prefersDarkTheme = window.matchMedia("(prefers-color-scheme: dark)").matches;

if (savedTheme === "dark" || (!savedTheme && prefersDarkTheme)) {
  document.body.classList.add("tema-escuro");
}

updateThemeControl();

themeToggle?.addEventListener("click", () => {
  const isDark = document.body.classList.toggle("tema-escuro");
  localStorage.setItem(themeStorageKey, isDark ? "dark" : "light");
  updateThemeControl();
});
