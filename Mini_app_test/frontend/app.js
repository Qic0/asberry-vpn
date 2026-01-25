// ================= TELEGRAM =================
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// ================= STATE =================
const state = {
  user: null,
  activeTab: 'vpn',
  paymentMethod: 'sbp',
  amount: 150
};

// ================= HELPERS =================
const qs = (id) => document.getElementById(id);

// ================= INIT =================
document.addEventListener('DOMContentLoaded', () => {
  initAuth();
  initUI();
});

// ================= AUTH =================
async function initAuth() {
  try {
    const res = await fetch('/auth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ initData: tg.initData })
    });

    if (!res.ok) throw new Error('Auth failed');

    const data = await res.json();
    state.user = data;

    renderUser();
    renderVPN();
  } catch (e) {
    console.error(e);
    tg.showAlert('Ошибка авторизации');
  }
}

// ================= RENDER =================
function renderUser() {
  const tgUser = tg.initDataUnsafe.user;

  qs('username').innerText = tgUser?.first_name || 'User';
  qs('userid').innerText = tgUser?.id || '';
  qs('avatar').src = tgUser?.photo_url || '';

  document.querySelectorAll('.balance span').forEach(el => {
    el.innerText = `${state.user.balance} ₽`;
  });

  const drawerBalance = document.querySelector('.balance-card strong');
  if (drawerBalance) {
    drawerBalance.innerText = `💰 ${state.user.balance} ₽`;
  }
}

function renderVPN() {
  // Пока данные статичны в HTML,
  // позже можно подставлять state.user.subscription_*
}

// ================= UI =================
function initUI() {
  // overlay
  qs('overlay').addEventListener('click', closeDrawer);

  // payment methods
  document.querySelectorAll('.pay-method').forEach((el, idx) => {
    el.dataset.method = idx === 0 ? 'sbp' : 'card';

    el.addEventListener('click', () => {
      document.querySelectorAll('.pay-method').forEach(p => p.classList.remove('active'));
      el.classList.add('active');
      state.paymentMethod = el.dataset.method;
    });
  });

  // amounts
  document.querySelectorAll('.amount').forEach(el => {
    const value = el.querySelector('strong').innerText.replace(/\D/g, '');
    el.dataset.amount = value;

    el.addEventListener('click', () => {
      document.querySelectorAll('.amount').forEach(a => a.classList.remove('active'));
      el.classList.add('active');
      state.amount = Number(value);
    });
  });

  // buttons
  document.querySelector('.primary-btn')?.addEventListener('click', createPayment);
}

// ================= NAVIGATION =================
function openTab(tab) {
  state.activeTab = tab;

  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  qs(tab).classList.add('active');

  document.querySelectorAll('.footer-btn').forEach(b => b.classList.remove('active'));
  if (tab === 'topup') document.querySelectorAll('.footer-btn')[0]?.classList.add('active');
  if (tab === 'help') document.querySelectorAll('.footer-btn')[1]?.classList.add('active');
}

// ================= DRAWER =================
function openDrawer() {
  qs('drawer').classList.add('open');
  qs('overlay').classList.add('open');
}

function closeDrawer() {
  qs('drawer').classList.remove('open');
  qs('overlay').classList.remove('open');
}

// ================= PAYMENTS =================
async function createPayment() {
  try {
    tg.showPopup({
      title: 'Оплата',
      message: `Сумма: ${state.amount} ₽\nСпособ: ${state.paymentMethod === 'sbp' ? 'СБП' : 'Карта'}`,
      buttons: [{ type: 'ok', text: 'Продолжить' }]
    });

    // 🔜 позже:
    // const res = await fetch('/payments/create', { ... })
  } catch (e) {
    tg.showAlert('Ошибка создания платежа');
  }
}

// ================= EXPOSE =================
window.openDrawer = openDrawer;
window.closeDrawer = closeDrawer;
window.openTab = openTab;

