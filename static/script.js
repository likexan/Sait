// ============================================================
// THEME
// ============================================================

const themeToggle = document.getElementById('themeToggle');
const html = document.documentElement;

const savedTheme = localStorage.getItem('theme');
const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

if (savedTheme) {
    html.setAttribute('data-theme', savedTheme);
} else if (systemDark) {
    html.setAttribute('data-theme', 'dark');
}

themeToggle?.addEventListener('click', () => {
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';

    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
});


// ============================================================
// CUSTOM CURSOR
// ============================================================

const cursor = document.getElementById('cursor');
const follower = document.getElementById('cursorFollower');

let mouseX = 0;
let mouseY = 0;
let followerX = 0;
let followerY = 0;

if (cursor && follower) {
    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;

        cursor.style.left = `${mouseX}px`;
        cursor.style.top = `${mouseY}px`;
    });

    function animateFollower() {
        followerX += (mouseX - followerX) * 0.12;
        followerY += (mouseY - followerY) * 0.12;

        follower.style.left = `${followerX}px`;
        follower.style.top = `${followerY}px`;

        requestAnimationFrame(animateFollower);
    }

    animateFollower();

    function setupCursorHover() {
        document.querySelectorAll(
            'a, button, .project, input, select, textarea'
        ).forEach(el => {
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
}


// ============================================================
// NAVBAR AND SCROLL
// ============================================================

const nav = document.querySelector('.nav');

window.addEventListener('scroll', () => {
    nav?.classList.toggle('scrolled', window.scrollY > 40);
});

const revealElements = document.querySelectorAll(
    '.project, .about-content, .contact'
);

revealElements.forEach(el => el.classList.add('reveal'));

if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, {
        threshold: 0.15,
        rootMargin: '0px 0px -40px 0px'
    });

    revealElements.forEach(el => observer.observe(el));
}


// ============================================================
// API
// ============================================================

async function api(url, options = {}) {
    const res = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        },
        credentials: 'same-origin'
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
        const error = new Error(
            data.error || 'Ошибка сервера'
        );

        error.status = res.status;
        error.data = data;

        throw error;
    }

    return data;
}


// ============================================================
// HELPERS
// ============================================================

function escapeHtml(value) {
    const element = document.createElement('div');
    element.textContent = String(value ?? '');
    return element.innerHTML;
}

function formatDate(iso) {
    if (!iso) return '—';

    try {
        return new Date(iso).toLocaleDateString('ru-RU', {
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        });
    } catch {
        return '—';
    }
}

function formatDateTime(iso) {
    if (!iso) return '—';

    try {
        return new Date(iso).toLocaleString('ru-RU');
    } catch {
        return '—';
    }
}

function setMessage(element, message, type = '') {
    if (!element) return;

    element.textContent = message;
    element.className = 'form-message';

    if (type) {
        element.classList.add(type);
    }
}


// ============================================================
// UI ELEMENTS
// ============================================================

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
    { value: 'admin', label: 'Администратор' }
];


// ============================================================
// AUTH MODAL
// ============================================================

function openModal() {
    authModal.hidden = false;

    requestAnimationFrame(() => {
        authModal.classList.add('active');
    });

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
    if (e.target === authModal) {
        closeModal();
    }
});

showRegister.addEventListener('click', showRegisterForm);
showLogin.addEventListener('click', showLoginForm);

document.addEventListener('keydown', (e) => {
    if (
        e.key === 'Escape' &&
        authModal.classList.contains('active')
    ) {
        closeModal();
    }
});

userBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    userMenu.classList.toggle('open');
});

document.addEventListener('click', () => {
    userMenu.classList.remove('open');
});


// ============================================================
// AUTH UI
// ============================================================

function updateAuthUI() {
    if (currentUser) {
        loginBtn.hidden = true;
        userMenu.hidden = false;

        userName.textContent = currentUser.name;
        userAvatar.textContent = currentUser.name
            .charAt(0)
            .toUpperCase();
    } else {
        loginBtn.hidden = false;
        userMenu.hidden = true;
    }

    updateCTFPermissions();
}

function setRoleBadge(element, user) {
    element.textContent = user.role_label || user.role;

    element.className =
        'role-badge role-' + (user.role || 'member');
}


// ============================================================
// REGISTER
// ============================================================

registerFormEl.addEventListener('submit', async (e) => {
    e.preventDefault();

    registerError.textContent = '';

    const name = document.getElementById('regName').value.trim();

    const email = document.getElementById('regEmail')
        .value.trim().toLowerCase();

    const password = document.getElementById('regPassword').value;
    const password2 = document.getElementById('regPassword2').value;

    if (password !== password2) {
        registerError.textContent = 'Пароли не совпадают';
        return;
    }

    try {
        const data = await api('/api/register', {
            method: 'POST',
            body: JSON.stringify({
                name,
                email,
                password
            })
        });

        currentUser = data.user;

        closeModal();
        updateAuthUI();

        await showCabinet();

    } catch (err) {
        registerError.textContent = err.message;
    }
});


// ============================================================
// LOGIN
// ============================================================

loginFormEl.addEventListener('submit', async (e) => {
    e.preventDefault();

    loginError.textContent = '';

    const email = document.getElementById('loginEmail')
        .value.trim().toLowerCase();

    const password = document.getElementById('loginPassword').value;

    try {
        const data = await api('/api/login', {
            method: 'POST',
            body: JSON.stringify({
                email,
                password
            })
        });

        currentUser = data.user;

        closeModal();
        updateAuthUI();

        showMain();

    } catch (err) {
        loginError.textContent = err.message;
    }
});


// ============================================================
// LOGOUT
// ============================================================

logoutBtn.addEventListener('click', async () => {
    try {
        await api('/api/logout', {
            method: 'POST'
        });
    } catch (_) {
        // Локально сбрасываем состояние авторизации.
    }

    currentUser = null;

    updateAuthUI();
    showMain();

    userMenu.classList.remove('open');
});


// ============================================================
// NAVIGATION
// ============================================================

function hideAllPages() {
    mainContent.hidden = true;
    cabinet.hidden = true;
    ctfPage.hidden = true;
    ctfModPage.hidden = true;
    ctfLeaderboardPage.hidden = true;
    siteFooter.hidden = true;
}

function showMain() {
    hideAllPages();

    mainContent.hidden = false;
    siteFooter.hidden = false;

    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

function showLoginRequired() {
    showLoginForm();
    openModal();
}

logoLink.addEventListener('click', (e) => {
    e.preventDefault();
    showMain();
});

backToSite.addEventListener('click', showMain);

cabinetLink.addEventListener('click', (e) => {
    e.preventDefault();

    userMenu.classList.remove('open');
    showCabinet();
});


// ============================================================
// CABINET
// ============================================================

async function showCabinet() {
    if (!currentUser) {
        showLoginRequired();
        return;
    }

    hideAllPages();
    cabinet.hidden = false;

    cabinetName.textContent = currentUser.name;
    profileName.textContent = currentUser.name;
    profileEmail.textContent = currentUser.email;

    setRoleBadge(profileRole, currentUser);

    profileDate.textContent = formatDate(
        currentUser.created_at
    );

    editName.value = currentUser.name;

    activityList.innerHTML = '<li>Загрузка…</li>';

    try {
        const data = await api('/api/activities');

        if (!data.activities.length) {
            activityList.innerHTML =
                '<li>Пока нет активности</li>';
        } else {
            activityList.innerHTML = data.activities.map(item => `
                <li>
                    ${escapeHtml(item.text)}
                    — ${formatDateTime(item.date)}
                </li>
            `).join('');
        }

    } catch (err) {
        activityList.innerHTML = `
            <li>${escapeHtml(err.message)}</li>
        `;
    }

    const canManage =
        currentUser.role === 'admin' ||
        currentUser.role === 'moderator';

    usersPanel.hidden = !canManage;

    if (canManage) {
        await loadUsers();
    }

    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}


// ============================================================
// USERS
// ============================================================

async function loadUsers() {
    usersMessage.textContent = '';

    usersTableBody.innerHTML = `
        <tr>
            <td colspan="4">Загрузка…</td>
        </tr>
    `;

    try {
        const data = await api('/api/users');

        if (!data.users.length) {
            usersTableBody.innerHTML = `
                <tr>
                    <td colspan="4">Нет пользователей</td>
                </tr>
            `;
            return;
        }

        const isAdmin = currentUser.role === 'admin';

        usersTableBody.innerHTML = data.users.map(user => {
            const roleControl = isAdmin
                ? `
                    <select
                        data-user-id="${user.id}"
                        class="role-select"
                    >
                        ${ROLE_OPTIONS.map(option => `
                            <option
                                value="${option.value}"
                                ${user.role === option.value ? 'selected' : ''}
                            >
                                ${option.label}
                            </option>
                        `).join('')}
                    </select>
                `
                : `
                    <span class="role-badge role-${escapeHtml(user.role)}">
                        ${escapeHtml(user.role_label)}
                    </span>
                `;

            return `
                <tr>
                    <td>${escapeHtml(user.name)}</td>
                    <td>${escapeHtml(user.email)}</td>
                    <td>${roleControl}</td>
                    <td></td>
                </tr>
            `;
        }).join('');

        if (isAdmin) {
            usersTableBody.querySelectorAll('.role-select')
                .forEach(select => {
                    select.addEventListener('change', async () => {
                        const userId = Number(select.dataset.userId);
                        const role = select.value;

                        setMessage(usersMessage, '');

                        try {
                            await api(`/api/users/${userId}/role`, {
                                method: 'PUT',
                                body: JSON.stringify({ role })
                            });

                            setMessage(
                                usersMessage,
                                'Роль обновлена',
                                'success'
                            );

                            if (userId === currentUser.id) {
                                const me = await api('/api/me');

                                currentUser = me.user;

                                updateAuthUI();

                                setRoleBadge(
                                    profileRole,
                                    currentUser
                                );
                            }

                        } catch (err) {
                            setMessage(
                                usersMessage,
                                err.message,
                                'error'
                            );

                            await loadUsers();
                        }
                    });
                });
        }

    } catch (err) {
        usersTableBody.innerHTML = `
            <tr>
                <td colspan="4">${escapeHtml(err.message)}</td>
            </tr>
        `;
    }
}


// ============================================================
// PROFILE EDIT
// ============================================================

profileForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    setMessage(profileMessage, '');

    const name = editName.value.trim();

    if (name.length < 2) {
        setMessage(
            profileMessage,
            'Имя слишком короткое',
            'error'
        );
        return;
    }

    try {
        const data = await api('/api/profile', {
            method: 'PUT',
            body: JSON.stringify({ name })
        });

        currentUser = data.user;

        updateAuthUI();

        cabinetName.textContent = currentUser.name;
        profileName.textContent = currentUser.name;

        setMessage(
            profileMessage,
            'Изменения сохранены',
            'success'
        );

    } catch (err) {
        setMessage(
            profileMessage,
            err.message,
            'error'
        );
    }
});


// ============================================================
// CTF ELEMENTS
// ============================================================

const ctfNavLink = document.getElementById('ctfNavLink');
const ctfModNavLink = document.getElementById('ctfModNavLink');

const ctfPage = document.getElementById('ctfPage');
const ctfModPage = document.getElementById('ctfModPage');

// LEADERBOARD ELEMENTS
const ctfLeaderboardNavLink = document.getElementById(
    'ctfLeaderboardNavLink'
);

const ctfLeaderboardPage = document.getElementById(
    'ctfLeaderboardPage'
);

const ctfLeaderboardContent = document.getElementById(
    'ctfLeaderboardContent'
);

const ctfLeaderboardRefreshBtn = document.getElementById(
    'ctfLeaderboardRefreshBtn'
);

const ctfLeaderboardBackBtn = document.getElementById(
    'ctfLeaderboardBackBtn'
);

const ctfAdminActions = document.getElementById('ctfAdminActions');
const ctfCreateToggle = document.getElementById('ctfCreateToggle');
const ctfCreateCard = document.getElementById('ctfCreateCard');
const ctfCreateForm = document.getElementById('ctfCreateForm');

const ctfCreateMessage = document.getElementById('ctfCreateMessage');
const ctfCreateSubmit = document.getElementById('ctfCreateSubmit');

const ctfList = document.getElementById('ctfChallengesList');
const ctfWorkspace = document.getElementById('ctfWorkspace');

const ctfMessages = document.getElementById('ctfMessages');
const ctfMessageForm = document.getElementById('ctfMessageForm');

let activeChallengeId = null;
let activeSubmission = null;

let activeModSubmissionId = null;
let activeModMaxPoints = 100;


// ============================================================
// CTF PERMISSIONS
// ============================================================

function updateCTFPermissions() {
    const isAdmin = currentUser?.role === 'admin';

    const canModerate =
        currentUser?.role === 'admin' ||
        currentUser?.role === 'moderator';

    ctfAdminActions.hidden = !isAdmin;
    ctfModNavLink.hidden = !canModerate;

    if (!isAdmin) {
        closeCTFCreateForm();
    }
}


// ============================================================
// CTF CREATE FORM TOGGLE
// ============================================================

function openCTFCreateForm() {
    if (!currentUser || currentUser.role !== 'admin') {
        return;
    }

    ctfCreateCard.hidden = false;

    ctfCreateToggle.textContent = '− Закрыть форму';
    ctfCreateToggle.setAttribute('aria-expanded', 'true');

    ctfCreateCard.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest'
    });
}

function closeCTFCreateForm() {
    ctfCreateCard.hidden = true;

    ctfCreateToggle.textContent = '+ Создать задание';
    ctfCreateToggle.setAttribute('aria-expanded', 'false');
}

ctfCreateToggle.addEventListener('click', () => {
    if (ctfCreateCard.hidden) {
        openCTFCreateForm();
    } else {
        closeCTFCreateForm();
    }
});

document.getElementById('ctfCreateCancel')
    .addEventListener('click', () => {
        closeCTFCreateForm();
        setMessage(ctfCreateMessage, '');
    });


// ============================================================
// CTF NAVIGATION
// ============================================================

async function showCTF() {
    if (!currentUser) {
        showLoginRequired();
        return;
    }

    hideAllPages();

    ctfPage.hidden = false;

    updateCTFPermissions();
    closeCTFCreateForm();

    activeChallengeId = null;
    activeSubmission = null;

    ctfWorkspace.hidden = true;

    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });

    await loadCTFChallenges();
}

async function showCTFMod() {
    const canModerate =
        currentUser &&
        ['admin', 'moderator'].includes(currentUser.role);

    if (!canModerate) {
        return;
    }

    hideAllPages();

    ctfModPage.hidden = false;

    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });

    await loadCTFModerationQueue();
}


// ============================================================
// LEADERBOARD NAVIGATION
// ============================================================

async function showCTFLeaderboard() {
    if (!currentUser) {
        showLoginRequired();
        return;
    }

    hideAllPages();

    ctfLeaderboardPage.hidden = false;

    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });

    await loadCTFLeaderboard();
}

ctfNavLink.addEventListener('click', (e) => {
    e.preventDefault();
    showCTF();
});

ctfModNavLink.addEventListener('click', (e) => {
    e.preventDefault();
    showCTFMod();
});

ctfLeaderboardNavLink?.addEventListener('click', (e) => {
    e.preventDefault();
    showCTFLeaderboard();
});

ctfLeaderboardRefreshBtn?.addEventListener('click', () => {
    loadCTFLeaderboard();
});

ctfLeaderboardBackBtn?.addEventListener('click', showMain);

document.getElementById('ctfBackBtn')
    .addEventListener('click', showMain);

document.getElementById('ctfModBackBtn')
    .addEventListener('click', showCTF);

document.getElementById('ctfRefreshBtn')
    .addEventListener('click', loadCTFChallenges);


// ============================================================
// LOAD LEADERBOARD
// ============================================================

async function loadCTFLeaderboard() {
    if (!ctfLeaderboardContent) return;

    ctfLeaderboardContent.innerHTML = `
        <p class="ctf-empty">Загрузка рейтинга...</p>
    `;

    if (ctfLeaderboardRefreshBtn) {
        ctfLeaderboardRefreshBtn.disabled = true;
    }

    try {
        const data = await api('/api/ctf/leaderboard');

        if (!data.success) {
            throw new Error('Не удалось загрузить рейтинг.');
        }

        const leaderboard = data.leaderboard || [];

        if (!leaderboard.length) {
            ctfLeaderboardContent.innerHTML = `
                <div class="leaderboard-empty">
                    <span class="leaderboard-empty-number">00</span>
                    <h3>Пока нет участников</h3>
                    <p>Здесь появятся исследователи, набравшие первые баллы.</p>
                </div>
            `;
            return;
        }

        const getPoints = user => Number(user.points) || 0;
        const getCompleted = user => Number(user.completed) || 0;
        const isCurrentUser = user =>
            currentUser &&
            user.id !== undefined &&
            Number(user.id) === Number(currentUser.id);

        const topThree = leaderboard.slice(0, 3);
        const remaining = leaderboard.slice(3);

        const podiumOrder = [
            topThree[1],
            topThree[0],
            topThree[2]
        ].filter(Boolean);

        const podium = podiumOrder.map(user => {
            const rank = Number(user.rank) || 0;
            const isFirst = rank === 1;

            return `
                <article class="leaderboard-podium-card rank-${rank}
                    ${isCurrentUser(user) ? 'is-current-user' : ''}">

                    <div class="leaderboard-podium-top">
                        <span class="leaderboard-rank">
                            ${String(rank).padStart(2, '0')}
                        </span>

                        ${isFirst
                            ? '<span class="leaderboard-winner-label">ЛИДЕР</span>'
                            : ''}
                    </div>

                    <div class="leaderboard-podium-user">
                        <div class="leaderboard-avatar">
                            ${escapeHtml(
                                String(user.name || '?')
                                    .charAt(0)
                                    .toUpperCase()
                            )}
                        </div>

                        <h3>${escapeHtml(user.name || 'Неизвестный')}</h3>

                        ${isCurrentUser(user)
                            ? '<span class="leaderboard-you-label">ЭТО ВЫ</span>'
                            : ''}
                    </div>

                    <div class="leaderboard-podium-score">
                        <strong>${getPoints(user).toLocaleString('ru-RU')}</strong>
                        <span>БАЛЛОВ</span>
                    </div>

                    <div class="leaderboard-podium-footer">
                        <span>Решено заданий</span>
                        <strong>${getCompleted(user)}</strong>
                    </div>
                </article>
            `;
        }).join('');

        const rows = remaining.map(user => {
            const rank = Number(user.rank) || '—';

            return `
                <div class="leaderboard-row
                    ${isCurrentUser(user) ? 'is-current-user' : ''}">

                    <div class="leaderboard-row-rank">
                        ${String(rank).padStart(2, '0')}
                    </div>

                    <div class="leaderboard-row-user">
                        <div class="leaderboard-row-avatar">
                            ${escapeHtml(
                                String(user.name || '?')
                                    .charAt(0)
                                    .toUpperCase()
                            )}
                        </div>

                        <div>
                            <strong>${escapeHtml(user.name || 'Неизвестный')}</strong>

                            ${isCurrentUser(user)
                                ? '<span class="leaderboard-you-label">ЭТО ВЫ</span>'
                                : ''}
                        </div>
                    </div>

                    <div class="leaderboard-row-completed">
                        <strong>${getCompleted(user)}</strong>
                        <span>заданий</span>
                    </div>

                    <div class="leaderboard-row-points">
                        <strong>${getPoints(user).toLocaleString('ru-RU')}</strong>
                        <span>баллов</span>
                    </div>
                </div>
            `;
        }).join('');

        ctfLeaderboardContent.innerHTML = `
            <div class="leaderboard-overview">
                <div>
                    <span class="leaderboard-overview-label">
                        ОБЩИЙ РЕЙТИНГ
                    </span>
                    <h2>Исследователи</h2>
                </div>

                <div class="leaderboard-participant-count">
                    <strong>${leaderboard.length}</strong>
                    <span>участников</span>
                </div>
            </div>

            <div class="leaderboard-podium">
                ${podium}
            </div>

            ${remaining.length ? `
                <div class="leaderboard-list">
                    <div class="leaderboard-list-header">
                        <span>ПОЗИЦИЯ / УЧАСТНИК</span>
                        <span>РЕЗУЛЬТАТ</span>
                    </div>

                    <div class="leaderboard-list-content">
                        ${rows}
                    </div>
                </div>
            ` : ''}
        `;

    } catch (err) {
        ctfLeaderboardContent.innerHTML = `
            <p class="ctf-empty">
                ${escapeHtml(err.message)}
            </p>
        `;
    } finally {
        if (ctfLeaderboardRefreshBtn) {
            ctfLeaderboardRefreshBtn.disabled = false;
        }
    }
}


// ============================================================
// LOAD CTF CHALLENGES
// ============================================================

async function loadCTFChallenges() {
    ctfList.innerHTML = `
        <p class="ctf-empty">Загрузка заданий...</p>
    `;

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
                    class="ctf-item ${
                        activeChallengeId === challenge.id ? 'active' : ''
                    }"
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
// OPEN CTF CHALLENGE
// ============================================================

async function openCTFChallenge(challengeId) {
    activeChallengeId = challengeId;

    ctfWorkspace.hidden = false;

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

        if (activeChallengeId !== challengeId) return;

        activeSubmission = data.submission;

        document.getElementById('ctfTaskTitle').textContent =
            data.challenge.title;

        document.getElementById('ctfTaskDescription').textContent =
            data.challenge.description;

        document.getElementById('ctfTaskDifficulty').textContent =
            `Сложность: ${data.challenge.difficulty}`;

        document.getElementById('ctfTaskPoints').textContent =
            `Баллы: ${data.challenge.max_points}`;

        const statusLabels = {
            in_progress: 'В процессе',
            pending: 'На проверке',
            graded: 'Проверено'
        };

        const statusElement = document.getElementById('ctfTaskStatus');

        statusElement.textContent =
            statusLabels[activeSubmission.status] || 'Неизвестно';

        statusElement.dataset.status = activeSubmission.status;

        renderCTFMessages(data.messages);

        const locked = ['graded', 'pending'].includes(
            activeSubmission.status
        );

        document.getElementById('ctfMessageInput').disabled = locked;
        document.getElementById('ctfSubmitBtn').disabled = locked;
        document.getElementById('ctfSendMessageBtn').disabled = locked;

        const feedback = document.getElementById('ctfFeedback');

        feedback.hidden = activeSubmission.status !== 'graded';

        if (!feedback.hidden) {
            document.getElementById('ctfFeedbackScore').textContent =
                `${activeSubmission.score} / ${data.challenge.max_points}`;

            document.getElementById('ctfFeedbackText').textContent =
                activeSubmission.feedback ||
                'Комментарий отсутствует.';
        }

    } catch (err) {
        ctfMessages.innerHTML = `
            <p class="ctf-empty">
                ${escapeHtml(err.message)}
            </p>
        `;
    }
}


// ============================================================
// RENDER CTF CHAT
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
        const mine =
            Number(message.sender_id) === currentUser.id;

        return `
            <div class="ctf-message ${mine ? 'mine' : 'other'}">

                <div class="ctf-message-author">
                    ${escapeHtml(message.sender_name)}
                </div>

                <div class="ctf-message-text">
                    ${escapeHtml(message.text)}
                </div>

                <div class="ctf-message-date">
                    ${formatDateTime(message.created_at)}
                </div>

            </div>
        `;
    }).join('');

    ctfMessages.scrollTop = ctfMessages.scrollHeight;
}


// ============================================================
// SEND CTF MESSAGE
// ============================================================

async function sendCTFMessage(submit = false) {
    if (!activeChallengeId || !activeSubmission) {
        return;
    }

    const input = document.getElementById('ctfMessageInput');
    const message = input.value.trim();

    const locked = ['graded', 'pending'].includes(
        activeSubmission.status
    );

    if (locked) return;

    if (!message) {
        alert('Введите сообщение или решение.');
        return;
    }

    const sendButton = document.getElementById('ctfSendMessageBtn');
    const submitButton = document.getElementById('ctfSubmitBtn');

    sendButton.disabled = true;
    submitButton.disabled = true;

    try {
        await api(`/api/ctf/${activeChallengeId}/messages`, {
            method: 'POST',
            body: JSON.stringify({
                text: message,
                submit
            })
        });

        input.value = '';

        await openCTFChallenge(activeChallengeId);
        await loadCTFChallenges();

    } catch (err) {
        alert(err.message);

    } finally {
        sendButton.disabled = false;
        submitButton.disabled = false;
    }
}

ctfMessageForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    await sendCTFMessage(false);
});

document.getElementById('ctfSubmitBtn')
    .addEventListener('click', async () => {
        const confirmed = confirm(
            'Отправить решение модераторам на проверку?'
        );

        if (confirmed) {
            await sendCTFMessage(true);
        }
    });


// ============================================================
// CREATE CTF CHALLENGE
// ============================================================

ctfCreateForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!currentUser || currentUser.role !== 'admin') {
        setMessage(
            ctfCreateMessage,
            'Недостаточно прав для создания задания.',
            'error'
        );
        return;
    }

    const title = document.getElementById('ctfCreateTitle')
        .value.trim();

    const description = document.getElementById('ctfCreateDescription')
        .value.trim();

    const difficulty = document.getElementById('ctfCreateDifficulty')
        .value;

    const maxPoints = Number(
        document.getElementById('ctfCreatePoints').value
    );

    if (!title || !description) {
        setMessage(
            ctfCreateMessage,
            'Заполните название и описание.',
            'error'
        );
        return;
    }

    if (
        !Number.isInteger(maxPoints) ||
        maxPoints < 1 ||
        maxPoints > 100000
    ) {
        setMessage(
            ctfCreateMessage,
            'Количество баллов должно быть от 1 до 100000.',
            'error'
        );
        return;
    }

    ctfCreateSubmit.disabled = true;
    ctfCreateSubmit.textContent = 'Публикация...';

    setMessage(ctfCreateMessage, '');

    try {
        const data = await api('/api/ctf', {
            method: 'POST',
            body: JSON.stringify({
                title,
                description,
                difficulty,
                max_points: maxPoints
            })
        });

        setMessage(
            ctfCreateMessage,
            data.message || 'CTF успешно опубликован.',
            'success'
        );

        ctfCreateForm.reset();

        document.getElementById('ctfCreateDifficulty').value =
            'Средняя';

        document.getElementById('ctfCreatePoints').value = 100;

        await loadCTFChallenges();

        setTimeout(() => {
            closeCTFCreateForm();
            setMessage(ctfCreateMessage, '');
        }, 1500);

    } catch (err) {
        setMessage(
            ctfCreateMessage,
            err.message,
            'error'
        );

    } finally {
        ctfCreateSubmit.disabled = false;
        ctfCreateSubmit.textContent = 'Опубликовать задание';
    }
});


// ============================================================
// MODERATION ELEMENTS
// ============================================================

const ctfModList = document.getElementById('ctfModSubmissions');


// ============================================================
// LOAD MODERATION QUEUE
// ============================================================

async function loadCTFModerationQueue() {
    const status = document.getElementById(
        'ctfModStatusFilter'
    ).value;

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
                class="ctf-mod-item ${
                    activeModSubmissionId === item.id ? 'active' : ''
                }"
                data-id="${item.id}"
            >
                <span class="ctf-mod-item-status">
                    ${escapeHtml(item.status)}
                </span>

                <strong>
                    ${escapeHtml(item.challenge_title)}
                </strong>

                <span>${escapeHtml(item.username)}</span>

                <small>
                    ${formatDate(item.updated_at)}
                </small>
            </button>
        `).join('');

        ctfModList.querySelectorAll('.ctf-mod-item')
            .forEach(item => {
                item.addEventListener('click', () => {
                    openCTFModeration(Number(item.dataset.id));
                });
            });

    } catch (err) {
        ctfModList.innerHTML = `
            <p class="ctf-empty">
                ${escapeHtml(err.message)}
            </p>
        `;
    }
}

document.getElementById('ctfModStatusFilter')
    .addEventListener('change', loadCTFModerationQueue);


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

    const workspace = document.getElementById('ctfModWorkspace');

    workspace.hidden = false;

    document.getElementById('ctfModMessages').innerHTML = `
        <p class="ctf-empty">Загрузка переписки...</p>
    `;

    try {
        const data = await api(
            `/api/mod/ctf/submissions/${submissionId}`
        );

        if (activeModSubmissionId !== submissionId) return;

        const submission = data.submission;
        const challenge = data.challenge;

        if (!challenge) {
            throw new Error('Задание не найдено.');
        }

        activeModMaxPoints = challenge.max_points;

        document.getElementById('ctfModSubmissionTitle').textContent =
            challenge.title;

        document.getElementById('ctfModUsername').textContent =
            submission.username;

        document.getElementById('ctfModChallengeTitle').textContent =
            challenge.title;

        document.getElementById('ctfModSubmissionDate').textContent =
            formatDateTime(submission.updated_at);

        document.getElementById('ctfModSubmissionStatus').textContent =
            submission.status;

        const scoreInput = document.getElementById('ctfGradeScore');

        scoreInput.max = challenge.max_points;
        scoreInput.value = submission.score;

        document.getElementById('ctfGradeFeedback').value =
            submission.feedback || '';

        renderCTFModerationMessages(data.messages);

    } catch (err) {
        document.getElementById('ctfModMessages').innerHTML = `
            <p class="ctf-empty">
                ${escapeHtml(err.message)}
            </p>
        `;
    }
}


// ============================================================
// RENDER MODERATION CHAT
// ============================================================

function renderCTFModerationMessages(messages) {
    const container = document.getElementById('ctfModMessages');

    if (!messages.length) {
        container.innerHTML = `
            <p class="ctf-empty">Нет сообщений.</p>
        `;
        return;
    }

    container.innerHTML = messages.map(message => {
        const mine =
            Number(message.sender_id) === currentUser.id;

        return `
            <div class="ctf-message ${mine ? 'mine' : 'other'}">

                <div class="ctf-message-author">
                    ${escapeHtml(message.sender_name)}
                </div>

                <div class="ctf-message-text">
                    ${escapeHtml(message.text)}
                </div>

                <div class="ctf-message-date">
                    ${formatDateTime(message.created_at)}
                </div>

            </div>
        `;
    }).join('');

    container.scrollTop = container.scrollHeight;
}


// ============================================================
// MODERATOR SEND MESSAGE
// ============================================================

document.getElementById('ctfModMessageForm')
    .addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!activeModSubmissionId) return;

        const input = document.getElementById(
            'ctfModMessageInput'
        );

        const message = input.value.trim();

        if (!message) return;

        try {
            await api(
                `/api/mod/ctf/submissions/${activeModSubmissionId}/messages`,
                {
                    method: 'POST',
                    body: JSON.stringify({
                        text: message
                    })
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
            setMessage(
                message,
                `Баллы должны быть от 0 до ${activeModMaxPoints}.`,
                'error'
            );
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

            setMessage(
                message,
                'Оценка успешно сохранена.',
                'success'
            );

            await loadCTFModerationQueue();
            await openCTFModeration(activeModSubmissionId);

        } catch (err) {
            setMessage(
                message,
                err.message,
                'error'
            );
        }
    });


// ============================================================
// SMOOTH ANCHORS
// ============================================================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const targetId = this.getAttribute('href');

        if (
            targetId === '#' ||
            targetId === '#cabinet' ||
            targetId === '#ctf'
        ) {
            return;
        }

        const target = document.querySelector(targetId);

        if (target && !target.hidden) {
            e.preventDefault();

            const top =
                target.getBoundingClientRect().top +
                window.scrollY - 80;

            window.scrollTo({
                top,
                behavior: 'smooth'
            });
        }
    });
});


// ============================================================
// INITIALIZATION
// ============================================================

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