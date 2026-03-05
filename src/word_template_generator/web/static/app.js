const RECENT_KEY = "word_template_generator.recent_workspaces.v1";
const RECENT_MAX = 8;
const EMPTY_SELECT_VALUE = "__none__";
const DEFAULT_OUTPUT_DIR = "generated";

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

function showToast(message, kind = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;
  const el = document.createElement("div");
  el.className = `toast toast-${kind}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => {
    el.style.opacity = "0";
    el.style.transform = "translateY(-8px)";
  }, 3200);
  setTimeout(() => {
    el.remove();
  }, 3400);
}

async function withLoading(buttonOrEvent, asyncFn) {
  const btn =
    buttonOrEvent instanceof Event ? buttonOrEvent.currentTarget : buttonOrEvent;
  if (!btn || typeof asyncFn !== "function") return;
  if (btn.classList.contains("loading")) return;

  const originalMinWidth = btn.style.minWidth;
  btn.style.minWidth = `${btn.offsetWidth}px`;
  btn.disabled = true;
  btn.classList.add("loading");

  try {
    await asyncFn();
  } finally {
    btn.disabled = false;
    btn.classList.remove("loading");
    btn.style.minWidth = originalMinWidth;
  }
}

async function fetchJson(url, options, networkErrorMessage, silent = false) {
  let response;
  try {
    response = await fetch(url, options);
  } catch {
    log("[ERR] " + networkErrorMessage);
    if (!silent) showToast(networkErrorMessage, "error");
    return null;
  }

  let data = {};
  try {
    data = await response.json();
  } catch {
    data = {};
  }

  return { response, data };
}

function clearLog() {
  document.getElementById("log").value = "";
  showToast("Лог очищен", "info");
}

function ws() {
  const el = document.getElementById("workspace");
  const normalized = normalizeWorkspacePath(el.value);
  el.value = normalized;
  return normalized;
}

function selectedTemplate() {
  const value = (document.getElementById("templateSelect").value || "").trim();
  return value && value !== EMPTY_SELECT_VALUE ? value : null;
}

function outputDir() {
  return (document.getElementById("outputDir").value || "").trim();
}

function generationSettings() {
  return {
    template: selectedTemplate(),
    outputDir: outputDir() || DEFAULT_OUTPUT_DIR,
  };
}

function normalizeRecentItem(item) {
  if (typeof item === "string") {
    return { path: item, lastUsed: Date.now(), template: null, outputDir: DEFAULT_OUTPUT_DIR };
  }
  if (!item || typeof item.path !== "string") return null;
  return {
    path: item.path,
    lastUsed: Number(item.lastUsed || Date.now()),
    template: typeof item.template === "string" && item.template ? item.template : null,
    outputDir: typeof item.outputDir === "string" && item.outputDir ? item.outputDir : DEFAULT_OUTPUT_DIR,
  };
}

function readRecent() {
  try {
    const raw = localStorage.getItem(RECENT_KEY);
    if (!raw) return [];
    const data = JSON.parse(raw);
    if (!Array.isArray(data)) return [];
    return data.map(normalizeRecentItem).filter(Boolean);
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
    const details = [];
    if (item.template) details.push("шаблон: " + item.template);
    if (item.outputDir) details.push("папка: " + item.outputDir);
    opt.title = [item.path].concat(details).join("\n");
    sel.appendChild(opt);
  }
}

function rememberWorkspace(pathValue, settings) {
  const path = (pathValue || "").trim();
  if (!path) return;
  const now = Date.now();
  const template = settings && settings.template ? settings.template : null;
  const outputDir = settings && settings.outputDir ? settings.outputDir : DEFAULT_OUTPUT_DIR;
  const items = readRecent().filter((item) => item.path !== path);
  items.unshift({ path, lastUsed: now, template, outputDir });
  writeRecent(items);
  renderRecent();
}

function findRecent(path) {
  return readRecent().find((item) => item.path === path) || null;
}

function setTemplateOptions(templates, selected) {
  const sel = document.getElementById("templateSelect");
  sel.innerHTML = "";
  if (!templates || !templates.length) {
    const opt = document.createElement("option");
    opt.value = EMPTY_SELECT_VALUE;
    opt.textContent = "Шаблоны .docx/.docm не найдены";
    sel.appendChild(opt);
    sel.value = EMPTY_SELECT_VALUE;
    return;
  }

  const placeholder = document.createElement("option");
  placeholder.value = EMPTY_SELECT_VALUE;
  placeholder.textContent = "Выберите шаблон...";
  sel.appendChild(placeholder);

  for (const name of templates) {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    sel.appendChild(opt);
  }

  if (selected && templates.includes(selected)) {
    sel.value = selected;
  } else if (templates.length === 1) {
    sel.value = templates[0];
  } else {
    sel.value = EMPTY_SELECT_VALUE;
  }
}

function setOutputOptions(dirs, selected) {
  const sel = document.getElementById("outputDirSelect");
  sel.innerHTML = "";
  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = "Папки проекта";
  sel.appendChild(placeholder);

  for (const name of dirs || []) {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    sel.appendChild(opt);
  }
  sel.value = selected || "";
}

function setActsOptions(acts) {
  const sel = document.getElementById("acts");
  sel.innerHTML = "";

  const placeholder = document.createElement("option");
  placeholder.value = EMPTY_SELECT_VALUE;
  placeholder.textContent = "Выберите акт...";
  sel.appendChild(placeholder);
  sel.value = EMPTY_SELECT_VALUE;

  for (const name of acts || []) {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    sel.appendChild(opt);
  }
}

function useRecent() {
  const selected = document.getElementById("recent").value;
  if (!selected) {
    log("[ERR] Выберите проект из списка.");
    return;
  }
  document.getElementById("workspace").value = selected;
  const item = findRecent(selected);
  if (item) {
    document.getElementById("outputDir").value = item.outputDir || DEFAULT_OUTPUT_DIR;
  }
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

async function hydrateFromStorage() {
  renderRecent();
  const items = readRecent();
  if (!items.length) return;
  const last = items[0];
  document.getElementById("workspace").value = last.path;
  document.getElementById("outputDir").value = last.outputDir || DEFAULT_OUTPUT_DIR;
  log("[OK] Восстановлен последний workspace: " + last.path);
  await loadActs({ silent: true });
}

async function pickFolder() {
  const result = await fetchJson(
    "/api/pick-workspace",
    { method: "POST" },
    "Сервер не отвечает: не удалось выбрать папку"
  );
  if (!result) return;
  const { response, data } = result;
  if (!response.ok) {
    const msg = data.detail || "Не удалось выбрать папку";
    log("[ERR] " + msg);
    showToast(msg, "error");
    return;
  }
  if (!data.workspace) {
    log("[ERR] Папка не была выбрана.");
    showToast("Папка не была выбрана", "error");
    return;
  }
  document.getElementById("workspace").value = data.workspace;
  rememberWorkspace(data.workspace, generationSettings());
  log("[OK] Папка выбрана: " + data.workspace);
  showToast("Папка проекта выбрана", "success");
  await loadActs();
}

async function loadActs(options = {}) {
  const silent = Boolean(options.silent);
  const workspace = ws();
  if (!workspace) {
    log("[ERR] Укажите путь к workspace.");
    if (!silent) showToast("Укажите путь к workspace", "error");
    return;
  }
  const url = "/api/acts?workspace=" + encodeURIComponent(workspace);
  const result = await fetchJson(
    url,
    undefined,
    "Сервер не отвечает: не удалось загрузить акты",
    silent
  );
  if (!result) return;
  const { response, data } = result;
  if (!response.ok) {
    const msg = data.detail || "Не удалось загрузить акты";
    log("[ERR] " + msg);
    if (!silent) showToast(msg, "error");
    return;
  }

  setActsOptions(data.acts || []);

  const recent = findRecent(workspace);
  const selectedTemplate = recent && recent.template ? recent.template : data.selected_template;
  setTemplateOptions(data.templates || [], selectedTemplate || null);

  const selectedOutputDir =
    (recent && recent.outputDir) || data.selected_output_dir || DEFAULT_OUTPUT_DIR;
  setOutputOptions(data.output_dirs || [], selectedOutputDir);
  document.getElementById("outputDir").value = selectedOutputDir;

  if (selectedTemplate && selectedTemplate !== EMPTY_SELECT_VALUE) {
    log("[OK] Шаблон: " + selectedTemplate);
  }
  log("[OK] Загружено актов: " + (data.acts || []).length);
  if (!silent) showToast(`Загружено актов: ${(data.acts || []).length}`, "success");
  rememberWorkspace(workspace, generationSettings());
}

async function validateWs() {
  const workspace = ws();
  if (!workspace) {
    log("[ERR] Укажите путь к workspace.");
    showToast("Укажите путь к workspace", "error");
    return;
  }
  const result = await fetchJson(
    "/api/validate",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        workspace,
        template: selectedTemplate(),
        output_dir: outputDir(),
      }),
    },
    "Сервер не отвечает: проверка не выполнена"
  );
  if (!result) return;
  const { response, data } = result;
  if (!response.ok) {
    const msg = data.detail || "Проверка завершилась с ошибкой";
    log("[ERR] " + msg);
    showToast(msg, "error");
    return;
  }
  rememberWorkspace(workspace, generationSettings());
  for (const line of data.log) log(line);
  showToast("Проверка успешно завершена", "success");
}

async function buildAll() {
  const workspace = ws();
  if (!workspace) {
    log("[ERR] Укажите путь к workspace.");
    showToast("Укажите путь к workspace", "error");
    return;
  }
  const result = await fetchJson(
    "/api/build-all",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        workspace,
        template: selectedTemplate(),
        output_dir: outputDir(),
      }),
    },
    "Сервер не отвечает: генерация не выполнена"
  );
  if (!result) return;
  const { response, data } = result;
  if (!response.ok) {
    const msg = data.detail || "Генерация завершилась с ошибкой";
    log("[ERR] " + msg);
    showToast(msg, "error");
    return;
  }
  rememberWorkspace(workspace, generationSettings());
  for (const line of data.log) log(line);
  showToast("Все акты успешно сгенерированы", "success");
}

async function buildOne() {
  const workspace = ws();
  const act = document.getElementById("acts").value;
  if (!workspace) {
    log("[ERR] Укажите путь к workspace.");
    showToast("Укажите путь к workspace", "error");
    return;
  }
  if (!act) {
    log("[ERR] Выберите акт из списка.");
    showToast("Выберите акт из списка", "error");
    return;
  }
  if (act === EMPTY_SELECT_VALUE) {
    log("[ERR] Сначала выберите конкретный акт.");
    showToast("Сначала выберите конкретный акт", "error");
    return;
  }
  const result = await fetchJson(
    "/api/build-one",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        workspace,
        act,
        template: selectedTemplate(),
        output_dir: outputDir(),
      }),
    },
    "Сервер не отвечает: генерация не выполнена"
  );
  if (!result) return;
  const { response, data } = result;
  if (!response.ok) {
    const msg = data.detail || "Генерация завершилась с ошибкой";
    log("[ERR] " + msg);
    showToast(msg, "error");
    return;
  }
  rememberWorkspace(workspace, generationSettings());
  for (const line of data.log) log(line);
  showToast("Выбранный акт успешно сгенерирован", "success");
}

document.getElementById("outputDirSelect").addEventListener("change", () => {
  const value = document.getElementById("outputDirSelect").value;
  if (!value) return;
  document.getElementById("outputDir").value = value;
});

setActsOptions([]);
setTemplateOptions([], null);
setOutputOptions([], DEFAULT_OUTPUT_DIR);
document.getElementById("outputDir").value = DEFAULT_OUTPUT_DIR;
void hydrateFromStorage();

