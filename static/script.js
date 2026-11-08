// ===== Theme Toggle =====
const themeToggle = document.getElementById('themeToggle');
const html = document.documentElement;

const savedTheme = localStorage.getItem('theme');
const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

if (savedTheme) {
  html.setAttribute('data-theme', savedTheme);
} else if (systemDark) {
  html.setAttribute('data-theme', 'dark');
}

themeToggle.addEventListener('click', () => {
  const current = html.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
});

// ===== Custom Cursor =====
const cursor = document.getElementById('cursor');
const follower = document.getElementById('cursorFollower');

let mouseX = 0, mouseY = 0;
let followerX = 0, followerY = 0;

document.addEventListener('mousemove', (e) => {
  mouseX = e.clientX;
  mouseY = e.clientY;
  cursor.style.left = mouseX + 'px';
  cursor.style.top = mouseY + 'px';
});

function animateFollower() {
  followerX += (mouseX - followerX) * 0.12;
  followerY += (mouseY - followerY) * 0.12;
  follower.style.left = followerX + 'px';
  follower.style.top = followerY + 'px';
  requestAnimationFrame(animateFollower);
}
animateFollower();

function setupCursorHover() {
  document.querySelectorAll('a, button, .project, input, select').forEach(el => {
    el.addEventListener('mouseenter', () => {
      cursor.style.width = '12px';
      cursor.style.height = '12px';
      follower.style.width = '48px';
      follower.style.height = '48px';
    });
    el.addEventListener('mouseleave', () => {
      cursor.style.width = '8px';
      cursor.style.height = '8px';
      follower.style.width = '36px';
      follower.style.height = '36px';
    });
  });
}
setupCursorHover();

// ===== Navbar scroll =====
const nav = document.querySelector('.nav');
window.addEventListener('scroll', () => {
  nav.classList.toggle('scrolled', window.scrollY > 40);
});

// ===== Scroll reveal =====
const revealElements = document.querySelectorAll('.project, .about-content, .contact');
revealElements.forEach(el => el.classList.add('reveal'));

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) entry.target.classList.add('visible');
  });
}, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });

revealElements.forEach(el => observer.observe(el));

// ===== Smooth anchors =====
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    const targetId = this.getAttribute('href');
    if (targetId === '#' || targetId === '#cabinet') return;
    e.preventDefault();
    const target = document.querySelector(targetId);
    if (target) {
      const top = target.getBoundingClientRect().top + window.scrollY - 80;
      window.scrollTo({ top, behavior: 'smooth' });
    }
  });
});

// ===== API helpers =====
async function api(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    credentials: 'same-origin',
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.error || 'Ошибка сервера');
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

// ===== UI Elements =====
const loginBtn = document.getElementById('loginBtn');
const userMenu = document.getElementById('userMenu');
const userBtn = document.getElementById('userBtn');
const userAvatar = document.getElementById('userAvatar');
const userName = document.getElementById('userName');
const logoutBtn = document.getElementById('logoutBtn');
const cabinetLink = document.getElementById('cabinetLink');

const authModal = document.getElementById('authModal');
const modalClose = document.getElementById('modalClose');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const showRegister = document.getElementById('showRegister');
const showLogin = document.getElementById('showLogin');

const loginFormEl = document.getElementById('loginFormEl');
const registerFormEl = document.getElementById('registerFormEl');
const loginError = document.getElementById('loginError');
const registerError = document.getElementById('registerError');

const mainContent = document.getElementById('mainContent');
const cabinet = document.getElementById('cabinet');
const siteFooter = document.getElementById('siteFooter');
const backToSite = document.getElementById('backToSite');
const logoLink = document.getElementById('logoLink');

const cabinetName = document.getElementById('cabinetName');
const profileName = document.getElementById('profileName');
const profileEmail = document.getElementById('profileEmail');
const profileRole = document.getElementById('profileRole');
const profileDate = document.getElementById('profileDate');
const editName = document.getElementById('editName');
const profileForm = document.getElementById('profileForm');
const profileMessage = document.getElementById('profileMessage');
const activityList = document.getElementById('activityList');
const usersPanel = document.getElementById('usersPanel');
const usersTableBody = document.getElementById('usersTableBody');
const usersMessage = document.getElementById('usersMessage');

let currentUser = null;

const ROLE_OPTIONS = [
  { value: 'member', label: 'Участник' },
  { value: 'moderator', label: 'Модератор' },
  { value: 'admin', label: 'Администратор' },
];

// ===== Auth UI =====
function openModal() {
  authModal.hidden = false;
  requestAnimationFrame(() => authModal.classList.add('active'));
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  authModal.classList.remove('active');
  setTimeout(() => {
    authModal.hidden = true;
    document.body.style.overflow = '';
    loginError.textContent = '';
    registerError.textContent = '';
    loginFormEl.reset();
    registerFormEl.reset();
  }, 250);
}

function showLoginForm() {
  loginForm.hidden = false;
  registerForm.hidden = true;
  loginError.textContent = '';
  registerError.textContent = '';
}

function showRegisterForm() {
  loginForm.hidden = true;
  registerForm.hidden = false;
  loginError.textContent = '';
  registerError.textContent = '';
}

loginBtn.addEventListener('click', () => {
  showLoginForm();
  openModal();
});

modalClose.addEventListener('click', closeModal);
authModal.addEventListener('click', (e) => {
  if (e.target === authModal) closeModal();
});

showRegister.addEventListener('click', showRegisterForm);
showLogin.addEventListener('click', showLoginForm);

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && authModal.classList.contains('active')) closeModal();
});

userBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  userMenu.classList.toggle('open');
});

document.addEventListener('click', () => userMenu.classList.remove('open'));

// ===== Register =====
registerFormEl.addEventListener('submit', async (e) => {
  e.preventDefault();
  registerError.textContent = '';

  const name = document.getElementById('regName').value.trim();
  const email = document.getElementById('regEmail').value.trim().toLowerCase();
  const password = document.getElementById('regPassword').value;
  const password2 = document.getElementById('regPassword2').value;

  if (password !== password2) {
    registerError.textContent = 'Пароли не совпадают';
    return;
  }

  try {
    const data = await api('/api/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    });
    currentUser = data.user;
    closeModal();
    updateAuthUI();
    showCabinet();
  } catch (err) {
    registerError.textContent = err.message;
  }
});

// ===== Login =====
loginFormEl.addEventListener('submit', async (e) => {
  e.preventDefault();
  loginError.textContent = '';

  const email = document.getElementById('loginEmail').value.trim().toLowerCase();
  const password = document.getElementById('loginPassword').value;

  try {
    const data = await api('/api/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    currentUser = data.user;
    closeModal();
    updateAuthUI();
  } catch (err) {
    loginError.textContent = err.message;
  }
});

// ===== Logout =====
logoutBtn.addEventListener('click', async () => {
  try {
    await api('/api/logout', { method: 'POST' });
  } catch (_) { /* ignore */ }
  currentUser = null;
  updateAuthUI();
  showMain();
  userMenu.classList.remove('open');
});

// ===== Auth UI State =====
function updateAuthUI() {
  if (currentUser) {
    loginBtn.hidden = true;
    userMenu.hidden = false;
    userName.textContent = currentUser.name;
    userAvatar.textContent = currentUser.name.charAt(0).toUpperCase();
  } else {
    loginBtn.hidden = false;
    userMenu.hidden = true;
  }
}

function setRoleBadge(el, user) {
  el.textContent = user.role_label || user.role;
  el.className = 'role-badge role-' + (user.role || 'member');
}

// ===== Cabinet =====
async function showCabinet() {
  if (!currentUser) return;

  mainContent.hidden = true;
  siteFooter.hidden = true;
  cabinet.hidden = false;

  cabinetName.textContent = currentUser.name;
  profileName.textContent = currentUser.name;
  profileEmail.textContent = currentUser.email;
  setRoleBadge(profileRole, currentUser);
  profileDate.textContent = formatDate(currentUser.created_at);
  editName.value = currentUser.name;

  activityList.innerHTML = '<li>Загрузка…</li>';
  try {
    const data = await api('/api/activities');
    if (data.activities.length === 0) {
      activityList.innerHTML = '<li>Пока нет активности</li>';
    } else {
      activityList.innerHTML = data.activities
        .map(a => `<li>${a.text} — ${formatDate(a.date)}</li>`)
        .join('');
    }
  } catch {
    activityList.innerHTML = '<li>Не удалось загрузить</li>';
  }

  const canManage = currentUser.role === 'admin' || currentUser.role === 'moderator';
  usersPanel.hidden = !canManage;
  if (canManage) {
    await loadUsers();
  }

  window.scrollTo({ top: 0 });
}

async function loadUsers() {
  usersMessage.textContent = '';
  usersTableBody.innerHTML = '<tr><td colspan="4">Загрузка…</td></tr>';
  try {
    const data = await api('/api/users');
    if (!data.users.length) {
      usersTableBody.innerHTML = '<tr><td colspan="4">Нет пользователей</td></tr>';
      return;
    }
    const isAdmin = currentUser.role === 'admin';
    usersTableBody.innerHTML = data.users.map(u => {
      const roleSelect = isAdmin
        ? `<select data-user-id="${u.id}" class="role-select">
            ${ROLE_OPTIONS.map(o =>
              `<option value="${o.value}" ${u.role === o.value ? 'selected' : ''}>${o.label}</option>`
            ).join('')}
          </select>`
        : `<span class="role-badge role-${u.role}">${u.role_label}</span>`;

      return `<tr>
        <td>${escapeHtml(u.name)}</td>
        <td>${escapeHtml(u.email)}</td>
        <td>${roleSelect}</td>
        <td></td>
      </tr>`;
    }).join('');

    if (isAdmin) {
      usersTableBody.querySelectorAll('.role-select').forEach(sel => {
        sel.addEventListener('change', async () => {
          const userId = sel.dataset.userId;
          const role = sel.value;
          usersMessage.textContent = '';
          usersMessage.className = 'form-message';
          try {
            await api(`/api/users/${userId}/role`, {
              method: 'PUT',
              body: JSON.stringify({ role }),
            });
            usersMessage.textContent = 'Роль обновлена';
            usersMessage.classList.add('success');
            if (Number(userId) === currentUser.id) {
              const me = await api('/api/me');
              currentUser = me.user;
              updateAuthUI();
              setRoleBadge(profileRole, currentUser);
            }
            setTimeout(() => {
              usersMessage.textContent = '';
              usersMessage.className = 'form-message';
            }, 2000);
          } catch (err) {
            usersMessage.textContent = err.message;
            usersMessage.classList.add('error');
            await loadUsers();
          }
        });
      });
    }
  } catch (err) {
    usersTableBody.innerHTML = `<tr><td colspan="4">${escapeHtml(err.message)}</td></tr>`;
  }
}

function escapeHtml(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

function showMain() {
  cabinet.hidden = true;
  mainContent.hidden = false;
  siteFooter.hidden = false;
  window.scrollTo({ top: 0 });
}

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });
  } catch {
    return '—';
  }
}

cabinetLink.addEventListener('click', (e) => {
  e.preventDefault();
  userMenu.classList.remove('open');
  showCabinet();
});

backToSite.addEventListener('click', showMain);
logoLink.addEventListener('click', (e) => {
  e.preventDefault();
  showMain();
});

// ===== Profile edit =====
profileForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  profileMessage.textContent = '';
  profileMessage.className = 'form-message';

  const name = editName.value.trim();
  if (name.length < 2) {
    profileMessage.textContent = 'Имя слишком короткое';
    profileMessage.classList.add('error');
    return;
  }

  try {
    const data = await api('/api/profile', {
      method: 'PUT',
      body: JSON.stringify({ name }),
    });
    currentUser = data.user;
    updateAuthUI();
    cabinetName.textContent = currentUser.name;
    profileName.textContent = currentUser.name;

    profileMessage.textContent = 'Сохранено';
    profileMessage.classList.add('success');
    setTimeout(() => {
      profileMessage.textContent = '';
      profileMessage.className = 'form-message';
    }, 2500);
  } catch (err) {
    profileMessage.textContent = err.message;
    profileMessage.classList.add('error');
  }
});

// ===== Init =====
async function init() {
  try {
    const data = await api('/api/me');
    currentUser = data.user;
  } catch {
    currentUser = null;
  }
  updateAuthUI();
}

init();
// ============================================================
// CTF FRONTEND
// ============================================================

const ctfNavLink = document.getElementById('ctfNavLink');
const ctfModNavLink = document.getElementById('ctfModNavLink');

const ctfPage = document.getElementById('ctfPage');
const ctfModPage = document.getElementById('ctfModPage');

const ctfCreatePanel = document.getElementById('ctfCreatePanel');
const ctfCreateForm = document.getElementById('ctfCreateForm');

const ctfList = document.getElementById('ctfList');
const ctfWorkspaceEmpty = document.querySelector('.ctf-workspace-empty');
const ctfActiveWorkspace = document.getElementById('ctfActiveWorkspace');

const ctfMessages = document.getElementById('ctfMessages');
const ctfMessageForm = document.getElementById('ctfMessageForm');

let activeChallengeId = null;
let activeSubmission = null;

let activeModSubmissionId = null;
let activeModMaxPoints = 100;


// ============================================================
// NAVIGATION
// ============================================================

function hideAllPages() {
    mainContent.hidden = true;
    cabinet.hidden = true;
    ctfPage.hidden = true;
    ctfModPage.hidden = true;
    siteFooter.hidden = true;
}

function showMain() {
    hideAllPages();

    mainContent.hidden = false;
    siteFooter.hidden = false;

    window.scrollTo({ top: 0 });
}

async function showCTF() {
    if (!currentUser) {
        showLoginForm();
        openModal();
        return;
    }

    hideAllPages();
    ctfPage.hidden = false;

    ctfCreatePanel.hidden = !['admin', 'moderator'].includes(
        currentUser.role
    );

    window.scrollTo({ top: 0 });

    await loadCTFChallenges();
}

async function showCTFMod() {
    if (!currentUser ||
        !['admin', 'moderator'].includes(currentUser.role)) {
        return;
    }

    hideAllPages();
    ctfModPage.hidden = false;

    window.scrollTo({ top: 0 });

    await loadCTFModerationQueue();
}

ctfNavLink.addEventListener('click', (e) => {
    e.preventDefault();
    showCTF();
});

ctfModNavLink.addEventListener('click', (e) => {
    e.preventDefault();
    showCTFMod();
});

document.getElementById('ctfBackBtn').addEventListener(
    'click',
    showMain
);

document.getElementById('ctfModBackBtn').addEventListener(
    'click',
    showCTF
);

document.getElementById('ctfRefreshBtn').addEventListener(
    'click',
    loadCTFChallenges
);


// ============================================================
// NAVIGATION ROLE VISIBILITY
// ============================================================

// Переопределяем отображение ссылок после авторизации.

const originalUpdateAuthUI = updateAuthUI;

updateAuthUI = function () {
    originalUpdateAuthUI();

    ctfNavLink.hidden = false;

    ctfModNavLink.hidden = !(
        currentUser &&
        ['admin', 'moderator'].includes(currentUser.role)
    );
};


// ============================================================
// CTF CHALLENGES
// ============================================================

async function loadCTFChallenges() {
    ctfList.innerHTML = '<p class="ctf-empty">Загрузка заданий...</p>';

    try {
        const data = await api('/api/ctf');

        if (!data.challenges.length) {
            ctfList.innerHTML = `
                <div class="ctf-empty">
                    Пока нет опубликованных заданий.
                </div>
            `;
            return;
        }

        ctfList.innerHTML = data.challenges.map(challenge => {
            const submission = challenge.submission;

            let status = 'Не начато';

            if (submission) {
                status = {
                    in_progress: 'В процессе',
                    pending: 'На проверке',
                    graded: 'Проверено'
                }[submission.status] || submission.status;
            }

            return `
                <button
                    class="ctf-item ${activeChallengeId === challenge.id ? 'active' : ''}"
                    data-id="${challenge.id}"
                    type="button"
                >
                    <div class="ctf-item-top">
                        <span class="ctf-item-difficulty">
                            ${escapeHtml(challenge.difficulty)}
                        </span>

                        <span class="ctf-item-points">
                            ${challenge.max_points} баллов
                        </span>
                    </div>

                    <h3>${escapeHtml(challenge.title)}</h3>

                    <div class="ctf-item-bottom">
                        <span>${escapeHtml(status)}</span>
                        <span>Открыть →</span>
                    </div>
                </button>
            `;
        }).join('');

        ctfList.querySelectorAll('.ctf-item').forEach(item => {
            item.addEventListener('click', () => {
                openCTFChallenge(Number(item.dataset.id));
            });
        });

    } catch (err) {
        ctfList.innerHTML = `
            <p class="ctf-empty">
                ${escapeHtml(err.message)}
            </p>
        `;
    }
}


// ============================================================
// OPEN CHALLENGE
// ============================================================

async function openCTFChallenge(challengeId) {
    activeChallengeId = challengeId;

    ctfWorkspaceEmpty.hidden = true;
    ctfActiveWorkspace.hidden = false;

    ctfMessages.innerHTML = `
        <p class="ctf-empty">Загрузка переписки...</p>
    `;

    document.querySelectorAll('.ctf-item').forEach(item => {
        item.classList.toggle(
            'active',
            Number(item.dataset.id) === challengeId
        );
    });

    try {
        const data = await api(
            `/api/ctf/${challengeId}/submission`
        );

        activeSubmission = data.submission;

        document.getElementById('ctfActiveTitle').textContent =
            data.challenge.title;

        document.getElementById('ctfActiveDescription').textContent =
            data.challenge.description;

        document.getElementById('ctfActiveDifficulty').textContent =
            data.challenge.difficulty;

        document.getElementById('ctfActivePoints').textContent =
            `${data.challenge.max_points} баллов`;

        const statusLabels = {
            in_progress: 'В процессе',
            pending: 'На проверке',
            graded: 'Проверено'
        };

        const statusElement = document.getElementById(
            'ctfActiveStatus'
        );

        statusElement.textContent =
            statusLabels[activeSubmission.status] || 'Неизвестно';

        statusElement.dataset.status = activeSubmission.status;

        renderCTFMessages(data.messages);

        const locked = activeSubmission.status === 'graded' ||
            activeSubmission.status === 'pending';

        document.getElementById('ctfMessageInput').disabled = locked;
        document.getElementById('ctfSubmitSolutionBtn').disabled = locked;

        document.getElementById('ctfMessageForm')
            .querySelector('button[type="submit"]').disabled = locked;

        const feedback = document.getElementById('ctfFeedback');

        feedback.hidden = activeSubmission.status !== 'graded';

        if (!feedback.hidden) {
            document.getElementById('ctfFeedbackScore').textContent =
                `${activeSubmission.score} баллов`;

            document.getElementById('ctfFeedbackText').textContent =
                activeSubmission.feedback || 'Комментарий отсутствует.';
        }

    } catch (err) {
        ctfMessages.innerHTML = `
            <p class="ctf-empty">${escapeHtml(err.message)}</p>
        `;
    }
}


// ============================================================
// RENDER CHAT
// ============================================================

function renderCTFMessages(messages) {
    if (!messages.length) {
        ctfMessages.innerHTML = `
            <div class="ctf-empty">
                Здесь пока нет сообщений.<br>
                Начните своё расследование.
            </div>
        `;
        return;
    }

    ctfMessages.innerHTML = messages.map(message => {
        const mine = Number(message.sender_id) === currentUser.id;

        return `
            <div class="ctf-message ${mine ? 'mine' : 'other'}">
                <div class="ctf-message-author">
                    ${escapeHtml(message.sender_name)}
                </div>

                <div class="ctf-message-text">
                    ${escapeHtml(message.text)}
                </div>

                <div class="ctf-message-date">
                    ${new Date(message.created_at).toLocaleString('ru-RU')}
                </div>
            </div>
        `;
    }).join('');

    ctfMessages.scrollTop = ctfMessages.scrollHeight;
}


// ============================================================
// SEND USER MESSAGE
// ============================================================

async function sendCTFMessage(submit = false) {
    if (!activeChallengeId) return;

    const input = document.getElementById('ctfMessageInput');
    const message = input.value.trim();

    if (!message) {
        document.getElementById('ctfChatMessage').textContent =
            'Введите сообщение или решение.';
        return;
    }

    const button = document.getElementById('ctfSubmitSolutionBtn');
    button.disabled = true;

    try {
        await api(`/api/ctf/${activeChallengeId}/messages`, {
            method: 'POST',
            body: JSON.stringify({
                text: message,
                submit
            })
        });

        input.value = '';

        document.getElementById('ctfChatMessage').textContent =
            submit
                ? 'Решение отправлено на проверку.'
                : 'Сообщение отправлено.';

        await openCTFChallenge(activeChallengeId);
        await loadCTFChallenges();

    } catch (err) {
        document.getElementById('ctfChatMessage').textContent =
            err.message;
    } finally {
        button.disabled = false;
    }
}

ctfMessageForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    await sendCTFMessage(false);
});

document.getElementById('ctfSubmitSolutionBtn')
    .addEventListener('click', async () => {
        const confirmed = confirm(
            'Отправить решение модераторам на проверку?'
        );

        if (confirmed) {
            await sendCTFMessage(true);
        }
    });


// ============================================================
// CREATE CHALLENGE
// ============================================================

ctfCreateForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const message = document.getElementById(
        'ctfCreateMessage'
    );

    message.textContent = '';

    const payload = {
        title: document.getElementById('ctfTitle').value.trim(),
        description: document.getElementById('ctfDescription').value.trim(),
        difficulty: document.getElementById('ctfDifficulty').value,
        max_points: Number(
            document.getElementById('ctfPoints').value
        )
    };

    try {
        await api('/api/ctf', {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        message.textContent = 'CTF успешно опубликован.';
        message.className = 'form-message success';

        ctfCreateForm.reset();

        await loadCTFChallenges();

    } catch (err) {
        message.textContent = err.message;
        message.className = 'form-message error';
    }
});


// ============================================================
// MODERATION QUEUE
// ============================================================

const ctfModList = document.getElementById('ctfModList');

async function loadCTFModerationQueue() {
    const status = document.getElementById('ctfModFilter').value;

    ctfModList.innerHTML = `
        <p class="ctf-empty">Загрузка...</p>
    `;

    const query = status
        ? `?status=${encodeURIComponent(status)}`
        : '';

    try {
        const data = await api(
            `/api/mod/ctf/submissions${query}`
        );

        if (!data.submissions.length) {
            ctfModList.innerHTML = `
                <p class="ctf-empty">
                    Работ с таким статусом нет.
                </p>
            `;
            return;
        }

        ctfModList.innerHTML = data.submissions.map(item => `
            <button
                type="button"
                class="ctf-mod-item ${activeModSubmissionId === item.id ? 'active' : ''}"
                data-id="${item.id}"
            >
                <span class="ctf-mod-item-status">
                    ${escapeHtml(item.status)}
                </span>

                <strong>${escapeHtml(item.challenge_title)}</strong>

                <span>${escapeHtml(item.username)}</span>

                <small>
                    ${new Date(item.updated_at).toLocaleDateString('ru-RU')}
                </small>
            </button>
        `).join('');

        ctfModList.querySelectorAll('.ctf-mod-item').forEach(item => {
            item.addEventListener('click', () => {
                openCTFModeration(Number(item.dataset.id));
            });
        });

    } catch (err) {
        ctfModList.innerHTML = `
            <p class="ctf-empty">${escapeHtml(err.message)}</p>
        `;
    }
}

document.getElementById('ctfModFilter').addEventListener(
    'change',
    loadCTFModerationQueue
);


// ============================================================
// OPEN MODERATION SUBMISSION
// ============================================================

async function openCTFModeration(submissionId) {
    activeModSubmissionId = submissionId;

    document.querySelectorAll('.ctf-mod-item').forEach(item => {
        item.classList.toggle(
            'active',
            Number(item.dataset.id) === submissionId
        );
    });

    document.getElementById('ctfModEmpty').hidden = true;
    document.getElementById('ctfModActive').hidden = false;

    try {
        const data = await api(
            `/api/mod/ctf/submissions/${submissionId}`
        );

        const submission = data.submission;
        const challenge = data.challenge;

        activeModMaxPoints = challenge.max_points;

        document.getElementById('ctfModTitle').textContent =
            challenge.title;

        document.getElementById('ctfModUser').textContent =
            `Участник: ${submission.username}`;

        document.getElementById('ctfModDescription').textContent =
            challenge.description;

        document.getElementById('ctfModStatus').textContent =
            submission.status;

        document.getElementById('ctfGradeScore').max =
            challenge.max_points;

        document.getElementById('ctfGradeScore').value =
            submission.score;

        document.getElementById('ctfGradeMax').textContent =
            `Максимум: ${challenge.max_points}`;

        document.getElementById('ctfGradeFeedback').value =
            submission.feedback || '';

        renderCTFModerationMessages(data.messages);

    } catch (err) {
        alert(err.message);
    }
}


// ============================================================
// MODERATION CHAT
// ============================================================

function renderCTFModerationMessages(messages) {
    const container = document.getElementById(
        'ctfModMessages'
    );

    if (!messages.length) {
        container.innerHTML = `
            <p class="ctf-empty">Нет сообщений.</p>
        `;
        return;
    }

    container.innerHTML = messages.map(message => {
        const mine = Number(message.sender_id) === currentUser.id;

        return `
            <div class="ctf-message ${mine ? 'mine' : 'other'}">
                <div class="ctf-message-author">
                    ${escapeHtml(message.sender_name)}
                </div>

                <div class="ctf-message-text">
                    ${escapeHtml(message.text)}
                </div>

                <div class="ctf-message-date">
                    ${new Date(message.created_at).toLocaleString('ru-RU')}
                </div>
            </div>
        `;
    }).join('');

    container.scrollTop = container.scrollHeight;
}


document.getElementById('ctfModMessageForm')
    .addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!activeModSubmissionId) return;

        const input = document.getElementById(
            'ctfModMessageInput'
        );

        const text = input.value.trim();

        if (!text) return;

        try {
            await api(
                `/api/mod/ctf/submissions/${activeModSubmissionId}/messages`,
                {
                    method: 'POST',
                    body: JSON.stringify({ text })
                }
            );

            input.value = '';

            await openCTFModeration(activeModSubmissionId);

        } catch (err) {
            alert(err.message);
        }
    });


// ============================================================
// GRADE SUBMISSION
// ============================================================

document.getElementById('ctfGradeForm')
    .addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!activeModSubmissionId) return;

        const message = document.getElementById(
            'ctfGradeMessage'
        );

        const score = Number(
            document.getElementById('ctfGradeScore').value
        );

        const feedback = document.getElementById(
            'ctfGradeFeedback'
        ).value.trim();

        if (
            !Number.isInteger(score) ||
            score < 0 ||
            score > activeModMaxPoints
        ) {
            message.textContent = 'Некорректное количество баллов.';
            message.className = 'form-message error';
            return;
        }

        try {
            await api(
                `/api/mod/ctf/submissions/${activeModSubmissionId}/grade`,
                {
                    method: 'POST',
                    body: JSON.stringify({
                        score,
                        feedback
                    })
                }
            );

            message.textContent = 'Оценка успешно сохранена.';
            message.className = 'form-message success';

            await loadCTFModerationQueue();
            await openCTFModeration(activeModSubmissionId);

        } catch (err) {
            message.textContent = err.message;
            message.className = 'form-message error';
        }
    });
const ctfAdminActions = document.getElementById('ctfAdminActions');
const ctfCreateToggle = document.getElementById('ctfCreateToggle');
const ctfCreateCard = document.getElementById('ctfCreateCard');