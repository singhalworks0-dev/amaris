/* Keep the original drawer UI, with browser-local cart state for the preview. */
const cartKey = 'amaris-preview-cart';
const readCart = () => { try { return JSON.parse(localStorage.getItem(cartKey) || '[]'); } catch { return []; } };
const money = value => '₹ ' + new Intl.NumberFormat('en-IN').format(value / 100);
function saveCart(items) {
  localStorage.setItem(cartKey, JSON.stringify(items));
  document.querySelectorAll('[data-cart-count]').forEach(el => { el.textContent = items.reduce((n, item) => n + item.quantity, 0); });
}
function showCart() {
  const drawer = document.querySelector('cart-element');
  if (!drawer || !drawer.openCartDrawer) return;
  drawer.renderCartDrawer(false);
  const items = readCart();
  const holder = drawer.querySelector('[data-items-holder]');
  if (!holder) return;
  holder.replaceChildren();
  holder.classList.toggle('hidden', !items.length);
  for (const item of items) {
    const row = document.createElement('div');
    row.style.cssText = 'display:flex;gap:18px;padding:20px 0;border-bottom:1px solid #eee;align-items:start';
    const image = document.createElement('img'); image.src = item.image; image.alt = item.title;
    image.style.cssText = 'width:90px;height:115px;object-fit:contain';
    const info = document.createElement('div'); info.style.flex = '1';
    const title = document.createElement('a'); title.href = item.url; title.textContent = item.title;
    const price = document.createElement('p'); price.textContent = money(item.price); price.style.margin = '8px 0';
    const quantity = document.createElement('input'); quantity.type = 'number'; quantity.min = '1'; quantity.max = '99';
    quantity.value = item.quantity; quantity.setAttribute('aria-label', 'Quantity for ' + item.title);
    quantity.style.cssText = 'width:65px;padding:6px;border:1px solid #ddd;margin-right:16px';
    quantity.addEventListener('change', () => {
      const cart = readCart(); const current = cart.find(x => x.id === item.id);
      current.quantity = Math.min(99, Math.max(1, Number(quantity.value) || 1)); saveCart(cart); showCart();
    });
    const remove = document.createElement('button'); remove.type = 'button'; remove.textContent = 'Remove';
    remove.style.cssText = 'text-decoration:underline;font:inherit';
    remove.addEventListener('click', () => { saveCart(readCart().filter(x => x.id !== item.id)); showCart(); });
    info.append(title, price, quantity, remove); row.append(image, info); holder.append(row);
  }
  drawer.querySelectorAll('[data-empty-message], [data-empty-message-bottom]').forEach(el => el.classList.toggle('hidden', !!items.length));
  drawer.querySelector('[data-cart-form]')?.classList.toggle('hidden', !items.length);
  const total = items.reduce((n, item) => n + item.price * item.quantity, 0);
  drawer.querySelectorAll('[data-cart-total-price]').forEach(el => { el.textContent = money(total); });
  const count = drawer.querySelector('[data-cart-items-qty]');
  if (count) { count.classList.toggle('hidden', !items.length); count.textContent = items.reduce((n, item) => n + item.quantity, 0) + ' items'; }
  drawer.openCartDrawer();
}
document.addEventListener('click', event => {
  const add = event.target.closest('[data-add-to-cart]');
  if (add && document.querySelector('[data-product-json]')) {
    const form = add.closest('form');
    if (form) {
      event.preventDefault(); event.stopImmediatePropagation();
      form.dispatchEvent(new Event('submit', {bubbles:true, cancelable:true}));
      return;
    }
  }
  const toggle = event.target.closest('[data-cart-drawer-toggle]');
  if (!toggle) return;
  event.preventDefault(); event.stopImmediatePropagation();
  const drawer = document.querySelector('cart-element');
  if (toggle.closest('cart-element')) drawer?.closeCartDrawer(); else showCart();
}, true);
document.addEventListener('submit', function (event) {
  const form = event.target;
  const action = form.getAttribute('action') || '';
  if (/\/search(?:\?|$)/.test(action)) return;
  if (/\/cart\/add/.test(action)) {
    event.preventDefault(); event.stopImmediatePropagation();
    const productJson = document.querySelector('[data-product-json]');
    if (productJson) {
      const product = JSON.parse(productJson.textContent);
      const fields = new FormData(form);
      const variant = product.variants.find(x => String(x.id) === String(fields.get('id'))) || product.variants[0];
      const items = readCart(); const existing = items.find(x => x.id === variant.id);
      const quantity = Math.min(99, Math.max(1, Number(fields.get('quantity')) || 1));
      if (existing) existing.quantity = Math.min(99, existing.quantity + quantity);
      else items.push({id:variant.id, title:product.title, price:variant.price, image:product.featured_image || product.images[0], url:'/products/' + product.handle, quantity});
      saveCart(items); showCart(); return;
    }
  }
  if (/\/cart|\/account|\/contact|\/localization|subscribe|klaviyo|checkout/.test(action)) {
    event.preventDefault();
    event.stopImmediatePropagation();
    let message = form.querySelector('[data-replica-message]');
    if (!message) {
      message = document.createElement('p');
      message.dataset.replicaMessage = '';
      message.setAttribute('role', 'status');
      message.style.cssText = 'padding:12px 0;font:inherit;line-height:1.5';
      form.append(message);
    }
    message.textContent = 'This is a storefront preview. Checkout, accounts and form submissions require a connected store.';
  }
}, true);
