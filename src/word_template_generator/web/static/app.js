const RECENT_KEY = "word_template_generator.recent_workspaces.v1";
const RECENT_MAX = 8;

function normalizeWorkspacePath(rawValue) {
  let value = (rawValue || "").trim();
  if (!value) return "";

  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    value = value.slice(1, -1).trim();
  }

  if (/^[A-Za-z]:[\\/]/.test(value)) {
    value = value.replaceAll("/", "\\");
  }
  return value;
}

function log(line) {
  const el = document.getElementById("log");
  el.value += line + "\n";
  el.scrollTop = el.scrollHeight;
}

function ws() {
  const el = document.getElementById("workspace");
  const normalized = normalizeWorkspacePath(el.value);
  el.value = normalized;
  return normalized;
}

function readRecent() {
  try {
    const raw = localStorage.getItem(RECENT_KEY);
    if (!raw) return [];
    const data = JSON.parse(raw);
    if (!Array.isArray(data)) return [];
    return data.filter((item) => item && typeof item.path === "string");
  } catch {
    return [];
  }
}

function writeRecent(items) {
  localStorage.setItem(RECENT_KEY, JSON.stringify(items.slice(0, RECENT_MAX)));
}

function renderRecent() {
  const sel = document.getElementById("recent");
  const items = readRecent();
  sel.innerHTML = "";
  if (!items.length) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "Недавних проектов пока нет";
    sel.appendChild(opt);
    return;
  }
  for (const item of items) {
    const opt = document.createElement("option");
    opt.value = item.path;
    const time = item.lastUsed ? " [" + new Date(item.lastUsed).toLocaleString() + "]" : "";
    const displayPath = item.path.length > 56 ? "..." + item.path.slice(-53) : item.path;
    opt.textContent = displayPath + time;
    opt.title = item.path;
    sel.appendChild(opt);
  }
}

function rememberWorkspace(pathValue) {
  const path = (pathValue || "").trim();
  if (!path) return;
  const now = Date.now();
  const items = readRecent().filter((item) => item.path !== path);
  items.unshift({ path, lastUsed: now });
  writeRecent(items);
  renderRecent();
}

function useRecent() {
  const selected = document.getElementById("recent").value;
  if (!selected) {
    log("[ERR] Выберите проект из списка.");
    return;
  }
  document.getElementById("workspace").value = selected;
  log("[OK] Выбран проект: " + selected);
  loadActs();
}

function removeRecent() {
  const selected = document.getElementById("recent").value;
  if (!selected) {
    log("[ERR] Нечего удалять.");
    return;
  }
  const items = readRecent().filter((item) => item.path !== selected);
  writeRecent(items);
  renderRecent();
  log("[OK] Проект удален из недавних: " + selected);
}

function clearRecent() {
  localStorage.removeItem(RECENT_KEY);
  renderRecent();
  log("[OK] Список недавних проектов очищен.");
}

function hydrateFromStorage() {
  renderRecent();
  const items = readRecent();
  if (!items.length) return;
  const last = items[0].path;
  document.getElementById("workspace").value = last;
  log("[OK] Восстановлен последний workspace: " + last);
}

async function pickFolder() {
  const res = await fetch("/api/pick-workspace", { method: "POST" });
  const data = await res.json();
  if (!res.ok) {
    log("[ERR] " + (data.detail || "Не удалось выбрать папку"));
    return;
  }
  if (!data.workspace) {
    log("[ERR] Папка не была выбрана.");
    return;
  }
  document.getElementById("workspace").value = data.workspace;
  rememberWorkspace(data.workspace);
  log("[OK] Папка выбрана: " + data.workspace);
  await loadActs();
}

async function loadActs() {
  const workspace = ws();
  if (!workspace) {
    log("[ERR] Укажите путь к workspace.");
    return;
  }
  const url = "/api/acts?workspace=" + encodeURIComponent(workspace);
  const res = await fetch(url);
  const data = await res.json();
  if (!res.ok) {
    log("[ERR] " + (data.detail || "Не удалось загрузить акты"));
    return;
  }

  const sel = document.getElementById("acts");
  sel.innerHTML = "";
  for (const name of data.acts) {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    sel.appendChild(opt);
  }
  rememberWorkspace(workspace);
  log("[OK] Загружено актов: " + data.acts.length);
}

async function validateWs() {
  const workspace = ws();
  if (!workspace) {
    log("[ERR] Укажите путь к workspace.");
    return;
  }
  const res = await fetch("/api/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workspace }),
  });
  const data = await res.json();
  if (!res.ok) {
    log("[ERR] " + (data.detail || "Проверка завершилась с ошибкой"));
    return;
  }
  rememberWorkspace(workspace);
  for (const line of data.log) log(line);
}

async function buildAll() {
  const workspace = ws();
  if (!workspace) {
    log("[ERR] Укажите путь к workspace.");
    return;
  }
  const res = await fetch("/api/build-all", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workspace }),
  });
  const data = await res.json();
  if (!res.ok) {
    log("[ERR] " + (data.detail || "Генерация завершилась с ошибкой"));
    return;
  }
  rememberWorkspace(workspace);
  for (const line of data.log) log(line);
  await loadActs();
}

async function buildOne() {
  const workspace = ws();
  const act = document.getElementById("acts").value;
  if (!workspace) {
    log("[ERR] Укажите путь к workspace.");
    return;
  }
  if (!act) {
    log("[ERR] Выберите акт из списка.");
    return;
  }
  const res = await fetch("/api/build-one", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workspace, act }),
  });
  const data = await res.json();
  if (!res.ok) {
    log("[ERR] " + (data.detail || "Генерация завершилась с ошибкой"));
    return;
  }
  rememberWorkspace(workspace);
  for (const line of data.log) log(line);
}

hydrateFromStorage();

