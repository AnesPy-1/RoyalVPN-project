(function () {
  const $ = (sel, ctx = document) => ctx.querySelector(sel);
  const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));

  const setYear = () => {
    const yearNode = $("#year");
    if (yearNode) yearNode.textContent = String(new Date().getFullYear());
  };

  const setupMobileNav = () => {
    const navToggle = $("#navToggle");
    const mobileNav = $("#mobileNav");
    if (!navToggle || !mobileNav) return;

    const setOpen = (open) => {
      mobileNav.classList.toggle("is-open", open);
      navToggle.setAttribute("aria-expanded", String(open));
    };

    navToggle.addEventListener("click", () => {
      setOpen(!mobileNav.classList.contains("is-open"));
    });

    $$(".mobile-nav a", mobileNav).forEach((link) => {
      link.addEventListener("click", () => setOpen(false));
    });
  };

  const setupMessages = () => {
    $$("[data-dismiss-message]").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.currentTarget.closest(".message-item")?.remove();
      });
    });

    $$(".message-item").forEach((item) => {
      window.setTimeout(() => item.remove(), 4500);
    });
  };

  const CART_KEY = "royal_vpn_cart";
  const getCart = () => {
    try {
      return JSON.parse(localStorage.getItem(CART_KEY) || "[]");
    } catch (error) {
      return [];
    }
  };
  const setCart = (items) => {
    localStorage.setItem(CART_KEY, JSON.stringify(items));
    updateCartBadge();
  };
  const updateCartBadge = () => {
    const count = getCart().reduce((sum, item) => sum + (item.qty || 1), 0);
    $$("#cartCount").forEach((badge) => {
      badge.textContent = String(count);
    });
  };

  const setupPricingToggle = () => {
    const toggleButtons = $$("[data-pricing-mode]");
    const cards = $$("[data-plan-price]");
    if (!toggleButtons.length || !cards.length) return;

    const pricingModeKey = "royal_vpn_pricing_mode";
    const updateMode = (mode) => {
      toggleButtons.forEach((button) => {
        const active = button.dataset.pricingMode === mode;
        button.classList.toggle("is-active", active);
        button.setAttribute("aria-pressed", String(active));
      });

      cards.forEach((card) => {
        const base = Number(card.dataset.planPrice || 0);
        const amount = mode === "yearly" ? Math.round(base * 10.2) : base;
        const label = card.querySelector("[data-price-value]");
        const suffix = card.querySelector("[data-price-suffix]");
        if (label) label.textContent = new Intl.NumberFormat().format(amount);
        if (suffix) suffix.textContent = mode === "yearly" ? suffix.dataset.yearlyLabel || suffix.textContent : suffix.dataset.monthlyLabel || suffix.textContent;
      });

      localStorage.setItem(pricingModeKey, mode);
    };

    const savedMode = localStorage.getItem(pricingModeKey) || "monthly";
    updateMode(savedMode);

    toggleButtons.forEach((button) => {
      button.addEventListener("click", () => updateMode(button.dataset.pricingMode));
    });
  };

  const setupCart = () => {
    updateCartBadge();

    $$("[data-plan]").forEach((button) => {
      button.addEventListener("click", () => {
        const plan = JSON.parse(button.getAttribute("data-plan"));
        const cart = getCart();
        const index = cart.findIndex((item) => item.id === plan.id);
        if (index >= 0) {
          cart[index].qty = (cart[index].qty || 1) + 1;
        } else {
          cart.push({ ...plan, qty: 1 });
        }
        setCart(cart);
        const originalLabel = button.textContent;
        button.textContent = button.dataset.addedLabel || "افزوده شد";
        window.setTimeout(() => {
          button.textContent = originalLabel;
        }, 1000);
      });
    });

    const cartItemsEl = $("#cartItems");
    if (cartItemsEl) {
      const render = () => {
        const cart = getCart();
        if (!cart.length) {
          cartItemsEl.innerHTML = `<div class="surface-card">سبد خرید شما خالی است.</div>`;
          ["#subtotal", "#tax", "#total"].forEach((selector) => {
            const node = $(selector);
            if (node) node.textContent = "۰";
          });
          return;
        }

        cartItemsEl.innerHTML = cart
          .map(
            (item, index) => `
              <div class="surface-card">
                <div class="flex items-center justify-between gap-4">
                  <div>
                    <p class="font-semibold">${item.name}</p>
                    <p class="text-slate-400 text-sm">${item.price} تومان / ماه</p>
                  </div>
                  <div class="flex items-center gap-2">
                    <button data-dec="${index}" class="px-2 py-1 rounded-lg bg-white/5 hover:bg-white/10">-</button>
                    <span class="min-w-[2rem] text-center">${item.qty || 1}</span>
                    <button data-inc="${index}" class="px-2 py-1 rounded-lg bg-white/5 hover:bg-white/10">+</button>
                    <button data-rem="${index}" class="ml-2 px-3 py-1 rounded-lg bg-red-500/20 text-red-200 hover:bg-red-500/30">حذف</button>
                  </div>
                </div>
              </div>`
          )
          .join("");

        const subtotal = cart.reduce((sum, item) => sum + item.price * (item.qty || 1), 0);
        const tax = +(subtotal * 0.05).toFixed(2);
        const total = +(subtotal + tax).toFixed(2);
        const subtotalNode = $("#subtotal");
        const taxNode = $("#tax");
        const totalNode = $("#total");
        if (subtotalNode) subtotalNode.textContent = `${subtotal} تومان`;
        if (taxNode) taxNode.textContent = `${tax} تومان`;
        if (totalNode) totalNode.textContent = `${total} تومان`;

        $$("[data-inc]").forEach((button) =>
          button.addEventListener("click", () => {
            const current = getCart();
            current[button.dataset.inc].qty += 1;
            setCart(current);
            render();
          })
        );
        $$("[data-dec]").forEach((button) =>
          button.addEventListener("click", () => {
            const current = getCart();
            const index = Number(button.dataset.dec);
            current[index].qty = Math.max(1, (current[index].qty || 1) - 1);
            setCart(current);
            render();
          })
        );
        $$("[data-rem]").forEach((button) =>
          button.addEventListener("click", () => {
            const current = getCart();
            current.splice(Number(button.dataset.rem), 1);
            setCart(current);
            render();
          })
        );
      };

      render();
    }

    const orderItems = $("#orderItems");
    if (orderItems) {
      const cart = getCart();
      if (!cart.length) {
        orderItems.innerHTML = `<p class="text-slate-300">سبد خرید خالی است.</p>`;
      } else {
        orderItems.innerHTML = cart
          .map((item) => `<div class="flex items-center justify-between text-sm"><span>${item.name} × ${item.qty || 1}</span><span>${item.price * (item.qty || 1)} تومان</span></div>`)
          .join("");
      }

      const total = cart.reduce((sum, item) => sum + item.price * (item.qty || 1), 0) * 1.05;
      const orderTotal = $("#orderTotal");
      if (orderTotal) orderTotal.textContent = `${total.toFixed(2)} تومان`;
    }

    const checkoutForm = $("#checkoutForm");
    if (checkoutForm) {
      checkoutForm.addEventListener("submit", (event) => {
        event.preventDefault();
        $("#checkoutMsg")?.classList.remove("hidden");
        setCart([]);
        window.setTimeout(() => {
          window.location.href = "/";
        }, 1200);
      });
    }
  };

  const setupContactForm = () => {
    const contactForm = $("#contactForm");
    if (!contactForm) return;

    contactForm.addEventListener("submit", (event) => {
      event.preventDefault();
      $("#contactMsg")?.classList.remove("hidden");
      contactForm.reset();
    });
  };

  const setupScrollState = () => {
    const header = $(".site-header");
    if (!header) return;

    const update = () => {
      header.dataset.scrolled = String(window.scrollY > 4);
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
  };

  setYear();
  setupMobileNav();
  setupMessages();
  setupPricingToggle();
  setupCart();
  setupContactForm();
  setupScrollState();
})();
