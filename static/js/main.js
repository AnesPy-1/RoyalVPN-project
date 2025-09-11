(function(){
  const $ = (sel, ctx=document) => ctx.querySelector(sel);
  const $$ = (sel, ctx=document) => Array.from(ctx.querySelectorAll(sel));
  const setYear = () => $$("#year").forEach(n => n.textContent = new Date().getFullYear());
  setYear();

  // Mobile nav toggle
  const navToggle = $("#navToggle");
  const mobileNav = $("#mobileNav");
  if (navToggle && mobileNav) navToggle.addEventListener("click", () => mobileNav.classList.toggle("hidden"));

  // Cart storage helpers
  const CART_KEY = "royal_vpn_cart";
  const getCart = () => JSON.parse(localStorage.getItem(CART_KEY) || "[]");
  const setCart = (items) => { localStorage.setItem(CART_KEY, JSON.stringify(items)); updateCartBadge(); };
  const updateCartBadge = () => {
    const count = getCart().reduce((s,i)=>s+(i.qty||1),0);
    $$("#cartCount").forEach(b => b.textContent = String(count));
  };
  updateCartBadge();

  // Add to cart (pricing)
  $$("[data-plan]").forEach(btn => {
    btn.addEventListener("click", () => {
      const plan = JSON.parse(btn.getAttribute("data-plan"));
      const cart = getCart();
      const idx = cart.findIndex(i => i.id === plan.id);
      if (idx >= 0) cart[idx].qty = (cart[idx].qty||1) + 1; else cart.push({...plan, qty: 1});
      setCart(cart);
      btn.textContent = "Added";
      setTimeout(()=>btn.textContent = "Add to Cart", 1000);
    });
  });

  // Render cart
  const cartItemsEl = $("#cartItems");
  if (cartItemsEl) {
    const render = () => {
      const cart = getCart();
      if (!cart.length) {
        cartItemsEl.innerHTML = `<div class="rounded-xl border border-white/10 bg-white/5 p-6 text-slate-300">Your cart is empty. <a class="text-white underline" href="pricing.html">Add a plan</a>.</div>`;
        $("#subtotal").textContent = "$0"; $("#tax").textContent = "$0"; $("#total").textContent = "$0";
        return;
      }
      cartItemsEl.innerHTML = cart.map((item,i)=>`
        <div class="rounded-xl border border-white/10 bg-white/5 p-5 flex items-center justify-between gap-4">
          <div>
            <p class="font-semibold">${item.name} Plan</p>
            <p class="text-slate-400 text-sm">$${item.price}/mo</p>
          </div>
          <div class="flex items-center gap-2">
            <button data-dec="${i}" class="px-2 py-1 rounded-lg bg-white/5 hover:bg-white/10">-</button>
            <span class="min-w-[2rem] text-center">${item.qty||1}</span>
            <button data-inc="${i}" class="px-2 py-1 rounded-lg bg-white/5 hover:bg-white/10">+</button>
            <button data-rem="${i}" class="ml-2 px-3 py-1 rounded-lg bg-red-500/20 text-red-200 hover:bg-red-500/30">Remove</button>
          </div>
        </div>`).join("");
      const subtotal = cart.reduce((s,i)=>s+i.price*(i.qty||1),0);
      const tax = +(subtotal*0.05).toFixed(2);
      const total = +(subtotal+tax).toFixed(2);
      $("#subtotal").textContent = `$${subtotal}`;
      $("#tax").textContent = `$${tax}`;
      $("#total").textContent = `$${total}`;

      $$("[data-inc]").forEach(b=>b.addEventListener("click",()=>{const cart=getCart();cart[b.dataset.inc].qty++;setCart(cart);render();}));
      $$("[data-dec]").forEach(b=>b.addEventListener("click",()=>{const cart=getCart();cart[b.dataset.dec].qty=Math.max(1,(cart[b.dataset.dec].qty||1)-1);setCart(cart);render();}));
      $$("[data-rem]").forEach(b=>b.addEventListener("click",()=>{const cart=getCart();cart.splice(b.dataset.rem,1);setCart(cart);render();}));
    };
    render();
  }

  // Checkout: hydrate summary and fake submit
  const orderItems = $("#orderItems");
  if (orderItems) {
    const cart = getCart();
    if (!cart.length) orderItems.innerHTML = `<p class="text-slate-300">No items. <a class="underline" href="pricing.html">Choose a plan</a>.</p>`;
    else orderItems.innerHTML = cart.map(i=>`<div class="flex items-center justify-between text-sm"><span>${i.name} x ${i.qty||1}</span><span>$${i.price*(i.qty||1)}</span></div>`).join("");
    const total = cart.reduce((s,i)=>s+i.price*(i.qty||1),0)*1.05;
    $("#orderTotal").textContent = `$${+total.toFixed(2)}`;
  }
  const checkoutForm = $("#checkoutForm");
  if (checkoutForm) {
    checkoutForm.addEventListener("submit", (e)=>{
      e.preventDefault();
      $("#checkoutMsg").classList.remove("hidden");
      setCart([]);
      setTimeout(()=>{ window.location.href = "index.html"; }, 1200);
    });
  }

  // Contact form fake submit
  const contactForm = $("#contactForm");
  if (contactForm) {
    contactForm.addEventListener("submit", (e)=>{
      e.preventDefault();
      $("#contactMsg").classList.remove("hidden");
      contactForm.reset();
    });
  }
})();
