const editorState = {
  acts: [],
  templates: [],
  isNew: false,
  currentFilename: "",
  fields: [],
  templateVariables: [],
  projectFields: {},
  projectNumberPrefix: "",
  lastGeneratedFile: null,
  isDirty: false,
};
// Temporarily disable explicit "reference" type in UI.
const ENABLE_REFERENCE_TYPE = false;

const DATE_FORMAT_SUGGESTIONS = [
  "dd.MM.yyyy",
  "d.M.yyyy",
  "yyyy-MM-dd",
  "dd/MM/yyyy",
  "d MMMM yyyy",
  "d MMMM yyyy г.",
  "d MMMMG yyyy г.",
  "dd MMM yyyy",
  "dd.MM.yy",
];

const MONTHS_NOM = [
  "январь",
  "февраль",
  "март",
  "апрель",
  "май",
  "июнь",
  "июль",
  "август",
  "сентябрь",
  "октябрь",
  "ноябрь",
  "декабрь",
];

const MONTHS_GEN = [
  "января",
  "февраля",
  "марта",
  "апреля",
  "мая",
  "июня",
  "июля",
  "августа",
  "сентября",
  "октября",
  "ноября",
  "декабря",
];

const MONTHS_SHORT = [
  "янв",
  "фев",
  "мар",
  "апр",
  "май",
  "июн",
  "июл",
  "авг",
  "сен",
  "окт",
  "ноя",
  "дек",
];

function editorWorkspace() {
  return typeof ws === "function" ? ws() : "";
}

function editorLog(message, kind = "info") {
  if (typeof log === "function") log(message);
  if (typeof showToast === "function") showToast(message.replace(/^\[[A-Z]+\]\s*/, ""), kind);
}

function editorNormalizeFilename(raw) {
  const value = (raw || "").trim();
  if (!value) return "";
  return value.endsWith(".md") ? value : `${value}.md`;
}

function editorCurrentTemplate() {
  return (document.getElementById("editorTemplate").value || "").trim();
}

function editorIsFormVisible() {
  const card = document.getElementById("editorCard");
  return Boolean(card && card.style.display !== "none");
}

function editorSetDirty(value) {
  editorState.isDirty = Boolean(value);
  const base = editorState.currentFilename || "новый акт";
  const suffix = editorState.isDirty ? " *" : "";
  document.getElementById("editorTitle").textContent = `Редактирование: ${base}${suffix}`;
}

function editorMarkDirty() {
  editorSetDirty(true);
}

function editorConfirmDiscardIfDirty(actionLabel = "продолжить") {
  if (!editorState.isDirty || !editorIsFormVisible()) return true;
  return window.confirm(
    `Есть несохраненные изменения. Сохраните акт перед тем, как ${actionLabel}. Продолжить без сохранения?`
  );
}

function editorToDateInputValue(value) {
  const raw = String(value || "").trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) return raw;
  const ddmmyyyy = raw.match(/^(\d{2})\.(\d{2})\.(\d{4})$/);
  if (!ddmmyyyy) return "";
  return `${ddmmyyyy[3]}-${ddmmyyyy[2]}-${ddmmyyyy[1]}`;
}

function editorFromDateInputValue(value) {
  const raw = String(value || "").trim();
  if (!/^\d{4}-\d{2}-\d{2}$/.test(raw)) return raw;
  const [year, month, day] = raw.split("-");
  return `${day}.${month}.${year}`;
}

function editorNormalizeFieldType(rawType) {
  const known = new Set(["text", "multiline", "date", "reference", "number"]);
  const base = known.has(rawType) ? rawType : "text";
  if (!ENABLE_REFERENCE_TYPE && base === "reference") return "text";
  return base;
}

function editorResetForm() {
  editorState.isNew = false;
  editorState.currentFilename = "";
  editorState.fields = [];
  editorState.templateVariables = [];
  editorState.lastGeneratedFile = null;
  editorSetDirty(false);
  document.getElementById("editorCard").style.display = "none";
}

function editorFieldNames(excludeIndex = -1) {
  const names = [];
  for (let i = 0; i < editorState.fields.length; i += 1) {
    if (i === excludeIndex) continue;
    const name = String(editorState.fields[i].name || "").trim();
    if (!name || names.includes(name)) continue;
    names.push(name);
  }
  return names;
}

function editorMergedKnownFieldNames(excludeIndex = -1) {
  const own = editorFieldNames(excludeIndex);
  const inherited = Object.keys(editorState.projectFields || {});
  const special = ["number", "number_value", "number_prefix", "номер", "номер_значение", "номер_префикс"];
  return [...new Set(own.concat(inherited, special))];
}

function editorRenderList() {
  const root = document.getElementById("editorList");
  root.innerHTML = "";
  if (!editorState.acts.length) {
    const empty = document.createElement("div");
    empty.className = "muted";
    empty.textContent = "Акты не найдены.";
    root.appendChild(empty);
    return;
  }

  for (const act of editorState.acts) {
    const row = document.createElement("div");
    row.className = "result-item";

    const icon = document.createElement("span");
    icon.className = "result-icon";
    icon.textContent = "📄";

    const meta = document.createElement("div");
    meta.className = "result-meta";
    const title = document.createElement("span");
    title.className = "result-name";
    title.textContent = act;
    const path = document.createElement("span");
    path.className = "result-path";
    path.textContent = "Акт";
    meta.appendChild(title);
    meta.appendChild(path);

    const actions = document.createElement("div");
    actions.className = "actions";

    const editBtn = document.createElement("button");
    editBtn.className = "secondary";
    editBtn.textContent = "Редактировать";
    editBtn.addEventListener("click", () => {
      void withLoading(editBtn, () => editorOpenAct(act));
    });

    const delBtn = document.createElement("button");
    delBtn.className = "secondary";
    delBtn.textContent = "Удалить";
    delBtn.addEventListener("click", () => {
      void withLoading(delBtn, () => editorDeleteFromList(act));
    });

    actions.appendChild(editBtn);
    actions.appendChild(delBtn);

    row.appendChild(icon);
    row.appendChild(meta);
    row.appendChild(actions);
    root.appendChild(row);
  }
}

function editorRenderTemplateOptions(selected = null) {
  const sel = document.getElementById("editorTemplate");
  sel.innerHTML = "";
  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = "Выберите шаблон...";
  sel.appendChild(placeholder);
  for (const name of editorState.templates) {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    sel.appendChild(option);
  }
  if (selected && editorState.templates.includes(selected)) {
    sel.value = selected;
  } else if (editorState.templates.length === 1) {
    sel.value = editorState.templates[0];
  } else {
    sel.value = "";
  }
}

function editorCreateDateFormatOptions(selected) {
  const input = document.createElement("input");
  input.type = "text";
  input.placeholder = "Формат даты (например d MMMM yyyy)";
  input.value = selected || "dd.MM.yyyy";
  input.setAttribute("list", "editor-date-format-suggestions");
  return input;
}

function editorFormatDatePreview(ddmmyyyy, format) {
  const raw = String(ddmmyyyy || "").trim();
  const match = raw.match(/^(\d{2})\.(\d{2})\.(\d{4})$/);
  if (!match) return raw;
  const day = Number(match[1]);
  const month = Number(match[2]);
  const year = Number(match[3]);
  const date = new Date(year, month - 1, day);
  if (Number.isNaN(date.getTime())) return raw;

  let result = String(format || "dd.MM.yyyy");
  result = result.replaceAll("MMMMG", MONTHS_GEN[month - 1]);
  result = result.replaceAll("MMMM", MONTHS_NOM[month - 1]);
  result = result.replaceAll("MMM", MONTHS_SHORT[month - 1]);
  result = result.replaceAll("MM", String(month).padStart(2, "0"));
  result = result.replaceAll("M", String(month));
  result = result.replaceAll("dd", String(day).padStart(2, "0"));
  result = result.replaceAll("d", String(day));
  result = result.replaceAll("yyyy", String(year));
  result = result.replaceAll("yy", String(year % 100).padStart(2, "0"));
  return result;
}

function editorEnsureDateFormatDatalist() {
  if (document.getElementById("editor-date-format-suggestions")) return;
  const list = document.createElement("datalist");
  list.id = "editor-date-format-suggestions";
  for (const format of DATE_FORMAT_SUGGESTIONS) {
    const option = document.createElement("option");
    option.value = format;
    list.appendChild(option);
  }
  document.body.appendChild(list);
}

function editorBuildLabeledControl(labelText, controlElement) {
  const block = document.createElement("div");
  block.className = "editor-control-block";
  const label = document.createElement("div");
  label.className = "editor-control-label";
  label.textContent = labelText;
  block.appendChild(label);
  block.appendChild(controlElement);
  return block;
}

function editorBuildValueInput(field, index) {
  const wrapper = document.createElement("div");
  const normalizedType = editorNormalizeFieldType(field.type || "text");
  wrapper.className = `editor-value-wrap editor-value-wrap-${normalizedType}`;

  if (normalizedType === "multiline") {
    const input = document.createElement("textarea");
    input.style.minHeight = "90px";
    input.value = String(field.value ?? "");
    input.addEventListener("input", () => {
      editorState.fields[index].value = input.value;
      editorMarkDirty();
    });
    wrapper.appendChild(editorBuildLabeledControl("Значение", input));
    return wrapper;
  }

  if (normalizedType === "reference") {
    const controls = document.createElement("div");
    controls.className = "editor-reference-controls";

    const referenceSelect = document.createElement("select");
    const empty = document.createElement("option");
    empty.value = "";
    empty.textContent = "Ссылка на поле...";
    referenceSelect.appendChild(empty);
    for (const name of editorMergedKnownFieldNames(index)) {
      const option = document.createElement("option");
      option.value = name;
      option.textContent = name;
      referenceSelect.appendChild(option);
    }

    const tokenInput = document.createElement("input");
    tokenInput.type = "text";
    tokenInput.placeholder = "[[имя_поля]]";
    tokenInput.value = String(field.value ?? "");
    tokenInput.addEventListener("input", () => {
      editorState.fields[index].value = tokenInput.value;
      editorMarkDirty();
    });

    const currentRef = String(field.value || "").match(/^\[\[([^\]]+)\]\]$/);
    if (currentRef) {
      referenceSelect.value = currentRef[1];
    }
    referenceSelect.addEventListener("change", () => {
      if (!referenceSelect.value) return;
      const token = `[[${referenceSelect.value}]]`;
      editorState.fields[index].value = token;
      tokenInput.value = token;
      editorMarkDirty();
    });

    controls.appendChild(editorBuildLabeledControl("Источник ссылки", referenceSelect));
    controls.appendChild(editorBuildLabeledControl("Токен", tokenInput));
    wrapper.appendChild(controls);
    return wrapper;
  }

  if (normalizedType === "date") {
    editorEnsureDateFormatDatalist();

    const controls = document.createElement("div");
    controls.className = "editor-date-controls";

    const dateInput = document.createElement("input");
    dateInput.type = "date";
    dateInput.value = editorToDateInputValue(field.value);

    const formatSelect = editorCreateDateFormatOptions(field.format || "dd.MM.yyyy");
    const preview = document.createElement("div");
    preview.className = "editor-inline-preview";
    const initialValue = String(field.value || "");
    preview.textContent = initialValue
      ? "Превью: " + editorFormatDatePreview(initialValue, formatSelect.value)
      : "Превью появится после выбора даты";

    dateInput.addEventListener("input", () => {
      editorState.fields[index].value = editorFromDateInputValue(dateInput.value);
      editorMarkDirty();
      const next = String(editorState.fields[index].value || "");
      preview.textContent = next
        ? "Превью: " + editorFormatDatePreview(next, formatSelect.value)
        : "Превью появится после выбора даты";
    });
    formatSelect.addEventListener("input", () => {
      editorState.fields[index].format = formatSelect.value;
      editorMarkDirty();
      const next = String(editorState.fields[index].value || "");
      preview.textContent = next
        ? "Превью: " + editorFormatDatePreview(next, formatSelect.value)
        : "Превью появится после выбора даты";
    });

    controls.appendChild(editorBuildLabeledControl("Дата", dateInput));
    controls.appendChild(editorBuildLabeledControl("Формат даты", formatSelect));
    wrapper.appendChild(controls);
    wrapper.appendChild(preview);
    return wrapper;
  }

  const input = document.createElement("input");
  input.type = normalizedType === "number" ? "number" : "text";
  input.value = String(field.value ?? "");
  input.addEventListener("input", () => {
    if (normalizedType === "number") {
      editorState.fields[index].value = input.value === "" ? "" : Number(input.value);
      editorMarkDirty();
      return;
    }
    editorState.fields[index].value = input.value;
    editorMarkDirty();
  });
  wrapper.appendChild(editorBuildLabeledControl("Значение", input));
  return wrapper;
}

function editorRenderFields() {
  const root = document.getElementById("editorFields");
  root.innerHTML = "";

  if (!editorState.fields.length) {
    const empty = document.createElement("div");
    empty.className = "muted";
    empty.textContent = "Поля не добавлены.";
    root.appendChild(empty);
    return;
  }

  for (let index = 0; index < editorState.fields.length; index += 1) {
    const field = editorState.fields[index];
    const row = document.createElement("div");
    row.className = "editor-field-row";

    const nameInput = document.createElement("input");
    nameInput.className = "editor-field-name";
    nameInput.placeholder = "название_поля";
    nameInput.value = field.name;
    nameInput.addEventListener("input", () => {
      editorState.fields[index].name = nameInput.value;
      editorMarkDirty();
      editorRenderProjectFields();
      editorRenderTemplateVariables();
    });

    const typeSelect = document.createElement("select");
    const typeOptions = ENABLE_REFERENCE_TYPE
      ? ["text", "multiline", "date", "reference", "number"]
      : ["text", "multiline", "date", "number"];
    for (const type of typeOptions) {
      const option = document.createElement("option");
      option.value = type;
      option.textContent = type;
      typeSelect.appendChild(option);
    }
    typeSelect.value = editorNormalizeFieldType(field.type || "text");
    typeSelect.addEventListener("change", () => {
      const previousType = editorNormalizeFieldType(editorState.fields[index].type || "text");
      editorState.fields[index].type = typeSelect.value;
      editorMarkDirty();
      if (previousType !== "date" && typeSelect.value === "date") {
        // Do not keep old text as fake date preview.
        editorState.fields[index].value = "";
      }
      if (typeSelect.value === "date" && !editorState.fields[index].format) {
        editorState.fields[index].format = "dd.MM.yyyy";
      }
      editorRenderFields();
      editorRenderTemplateVariables();
    });

    const removeBtn = document.createElement("button");
    removeBtn.className = "secondary";
    removeBtn.textContent = "Удалить поле";
    removeBtn.addEventListener("click", () => {
      editorState.fields.splice(index, 1);
      editorMarkDirty();
      editorRenderFields();
      editorRenderProjectFields();
      editorRenderTemplateVariables();
    });

    const controls = document.createElement("div");
    controls.className = "editor-field-controls";
    controls.appendChild(editorBuildValueInput(field, index));

    const actions = document.createElement("div");
    actions.className = "editor-field-actions";
    typeSelect.classList.add("editor-type-select");
    actions.appendChild(editorBuildLabeledControl("Тип поля", typeSelect));
    actions.appendChild(removeBtn);

    row.appendChild(editorBuildLabeledControl("Название поля", nameInput));
    row.appendChild(controls);
    row.appendChild(actions);
    root.appendChild(row);
  }
}

function editorFieldHasValue(name) {
  const normalized = String(name || "").trim();
  if (["number", "номер", "number_value", "номер_значение"].includes(normalized)) {
    const numberValue = String(document.getElementById("editorNumberValue")?.value || "").trim();
    return numberValue !== "";
  }
  if (["number_prefix", "номер_префикс"].includes(normalized)) {
    const numberPrefix = String(document.getElementById("editorNumberPrefix")?.value || "").trim();
    return numberPrefix !== "";
  }

  for (const field of editorState.fields) {
    if (String(field.name || "").trim() !== name) continue;
    const value = field.value;
    if (value === null || value === undefined) return false;
    if (typeof value === "number") return true;
    return String(value).trim() !== "";
  }
  return false;
}

function editorGetMissingTemplateVariables() {
  const vars = editorState.templateVariables || [];
  const missing = [];
  for (const name of vars) {
    if (!name || typeof name !== "string") continue;
    const inAct = editorFieldHasValue(name);
    const inherited = editorState.projectFields[name];
    const inProject = inherited !== null && inherited !== undefined && String(inherited).trim() !== "";
    if (!inAct && !inProject) missing.push(name);
  }
  return missing;
}

function editorRenderTemplateVariables() {
  const root = document.getElementById("editorTemplateVars");
  const addBtn = document.getElementById("editorAddMissingBtn");
  root.innerHTML = "";
  const vars = editorState.templateVariables || [];
  if (!vars.length) {
    root.className = "muted";
    root.textContent = "Переменные не загружены или шаблон не выбран.";
    addBtn.disabled = true;
    return;
  }
  root.className = "editor-template-vars";

  const missing = new Set(editorGetMissingTemplateVariables());
  for (const name of vars) {
    const badge = document.createElement("span");
    badge.className = "editor-pill " + (missing.has(name) ? "editor-pill-warn" : "editor-pill-ok");
    badge.textContent = missing.has(name) ? `${name} (пусто)` : `${name} (ok)`;
    root.appendChild(badge);
  }
  addBtn.disabled = missing.size === 0;
}

function editorRenderProjectFields() {
  const root = document.getElementById("editorProjectFields");
  root.innerHTML = "";
  const entries = Object.entries(editorState.projectFields || {});
  if (!entries.length) {
    root.className = "muted";
    root.textContent = "В project.md нет наследуемых полей.";
    return;
  }
  root.className = "";

  for (const [name, value] of entries) {
    const item = document.createElement("div");
    item.className = "editor-inherited-item";

    const n = document.createElement("div");
    n.className = "editor-inherited-name";
    n.textContent = name;
    const v = document.createElement("div");
    v.className = "editor-inherited-value";
    v.textContent = `из project.md: ${String(value ?? "")}`;

    const overridden = editorFieldNames().includes(name);
    const action = document.createElement("button");
    action.className = "secondary";
    action.textContent = overridden ? "Переопределено в акте" : "Переопределить";
    action.disabled = overridden;
    action.addEventListener("click", () => {
      editorState.fields.push({
        name,
        value: value ?? "",
        type: typeof value === "number" ? "number" : "text",
        format: null,
      });
      editorMarkDirty();
      editorRenderFields();
      editorRenderProjectFields();
      editorRenderTemplateVariables();
    });

    item.appendChild(n);
    item.appendChild(v);
    item.appendChild(action);
    root.appendChild(item);
  }
}

function editorRenderGenerationResult() {
  const root = document.getElementById("editorGenerationResult");
  root.innerHTML = "";
  if (!editorState.lastGeneratedFile || !editorState.lastGeneratedFile.path) {
    root.className = "muted";
    root.textContent = "Результат генерации появится здесь.";
    return;
  }
  root.className = "row row-wrap";
  const name = document.createElement("span");
  name.className = "result-name";
  name.textContent = `Сгенерировано: ${editorState.lastGeneratedFile.name || editorState.lastGeneratedFile.path}`;
  const openBtn = document.createElement("button");
  openBtn.className = "secondary";
  openBtn.textContent = "Открыть";
  openBtn.addEventListener("click", () => {
    if (typeof withLoading === "function") {
      void withLoading(openBtn, () => openFile(editorState.lastGeneratedFile.path));
    } else {
      void openFile(editorState.lastGeneratedFile.path);
    }
  });
  root.appendChild(name);
  root.appendChild(openBtn);
}

function editorPopulateForm(data) {
  editorState.currentFilename = data.filename || "";
  const incomingFields = Object.entries(data.fields || {}).map(([name, field]) => ({
    name,
    value: field?.value ?? "",
    type: editorNormalizeFieldType(field?.type || "text"),
    format: field?.format || null,
  }));
  editorState.fields = incomingFields.length
    ? incomingFields
    : [{ name: "", value: "", type: "text", format: null }];

  document.getElementById("editorFilename").value = editorState.currentFilename;
  document.getElementById("editorOutputName").value = data.output_name || "";
  document.getElementById("editorNumberPrefix").value = data.number?.prefix || "";
  document.getElementById("editorNumberValue").value =
    data.number?.value === null || data.number?.value === undefined ? "" : String(data.number.value);
  editorRenderTemplateOptions(data.template || null);
  editorSetDirty(false);
  document.getElementById("editorDeleteBtn").style.display = editorState.isNew ? "none" : "inline-block";
  const editorCard = document.getElementById("editorCard");
  editorCard.style.display = "block";
  editorRenderFields();
  editorRenderTemplateVariables();
  editorRenderProjectFields();
  editorRenderGenerationResult();
  void editorLoadTemplateVariables();

  // Bring the edit form into view after opening.
  editorCard.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function editorLoadTemplateVariables() {
  const workspace = editorWorkspace();
  const template = editorCurrentTemplate();
  editorState.templateVariables = [];
  editorRenderTemplateVariables();
  if (!workspace || !template) return;

  const result = await fetchJson(
    `/api/template-variables?workspace=${encodeURIComponent(workspace)}&template=${encodeURIComponent(template)}`,
    undefined,
    "Сервер не отвечает: переменные шаблона не получены",
    true
  );
  if (!result) return;
  const { response, data } = result;
  if (!response.ok) return;
  editorState.templateVariables = Array.isArray(data.variables) ? data.variables : [];
  editorRenderTemplateVariables();
}

async function editorLoadProjectFields() {
  const workspace = editorWorkspace();
  editorState.projectFields = {};
  editorState.projectNumberPrefix = "";
  editorRenderProjectFields();
  if (!workspace) return;

  const result = await fetchJson(
    `/api/project-fields?workspace=${encodeURIComponent(workspace)}`,
    undefined,
    "Сервер не отвечает: поля проекта не загружены",
    true
  );
  if (!result) return;
  const { response, data } = result;
  if (!response.ok) return;
  editorState.projectFields = data.fields && typeof data.fields === "object" ? data.fields : {};
  editorState.projectNumberPrefix = data.number?.prefix || "";
  if (editorState.isNew && !document.getElementById("editorNumberPrefix").value) {
    document.getElementById("editorNumberPrefix").value = editorState.projectNumberPrefix;
  }
  editorRenderProjectFields();
  editorRenderTemplateVariables();
}

async function editorLoadActs() {
  const workspace = editorWorkspace();
  if (!workspace) {
    editorLog("[ERR] Укажите путь к workspace.", "error");
    return false;
  }
  const result = await fetchJson(
    "/api/acts?workspace=" + encodeURIComponent(workspace),
    undefined,
    "Сервер не отвечает: не удалось загрузить акты"
  );
  if (!result) return false;
  const { response, data } = result;
  if (!response.ok) {
    editorLog("[ERR] " + (data.detail || "Не удалось загрузить акты"), "error");
    return false;
  }
  editorState.acts = data.acts || [];
  editorState.templates = data.templates || [];
  editorRenderList();
  await editorLoadProjectFields();
  return true;
}

async function editorOpenAct(filename) {
  if (!editorConfirmDiscardIfDirty("открыть другой акт")) return;
  const workspace = editorWorkspace();
  const result = await fetchJson(
    `/api/act-data?workspace=${encodeURIComponent(workspace)}&act=${encodeURIComponent(filename)}`,
    undefined,
    "Сервер не отвечает: не удалось загрузить акт"
  );
  if (!result) return;
  const { response, data } = result;
  if (!response.ok) {
    editorLog("[ERR] " + (data.detail || "Не удалось загрузить акт"), "error");
    return;
  }
  editorState.isNew = false;
  editorPopulateForm(data);
}

function editorCreateAct() {
  if (!editorConfirmDiscardIfDirty("создать новый акт")) return;
  editorState.isNew = true;
  editorState.currentFilename = "";
  editorState.fields = [{ name: "", value: "", type: "text", format: null }];
  editorState.lastGeneratedFile = null;
  editorPopulateForm({
    filename: "",
    template: editorState.templates[0] || "",
    output_name: "",
    number: { prefix: editorState.projectNumberPrefix || "", value: null },
    fields: {},
  });
}

function editorBackToList() {
  if (!editorConfirmDiscardIfDirty("вернуться к списку")) return;
  editorResetForm();
}

function editorBuildSavePayload() {
  const filename = editorNormalizeFilename(document.getElementById("editorFilename").value);
  const outputName = (document.getElementById("editorOutputName").value || "").trim();
  const numberPrefix = (document.getElementById("editorNumberPrefix").value || "").trim();
  const numberValueRaw = (document.getElementById("editorNumberValue").value || "").trim();
  const template = editorCurrentTemplate() || null;

  const fields = {};
  const duplicateNames = new Set();
  const seenNames = new Set();
  for (const field of editorState.fields) {
    const name = (field.name || "").trim();
    if (!name) continue;
    if (seenNames.has(name)) duplicateNames.add(name);
    seenNames.add(name);
    fields[name] = {
      value: field.value ?? "",
      type: field.type || "text",
      format: field.format || null,
    };
  }

  return {
    filename,
    duplicateNames,
    payload: {
      workspace: editorWorkspace(),
      filename,
      is_new: editorState.isNew,
      data: {
        template,
        output_name: outputName || null,
        number: {
          prefix: numberPrefix,
          value: numberValueRaw ? Number(numberValueRaw) : null,
        },
        fields,
      },
    },
  };
}

async function editorSaveAct() {
  const { filename, payload, duplicateNames } = editorBuildSavePayload();
  if (!payload.workspace) {
    editorLog("[ERR] Укажите путь к workspace.", "error");
    return false;
  }
  if (!filename) {
    editorLog("[ERR] Укажите имя файла акта.", "error");
    return false;
  }
  if (duplicateNames.size) {
    editorLog("[ERR] Дублируются имена полей: " + Array.from(duplicateNames).join(", "), "error");
    return false;
  }
  if (!payload.data.template) {
    editorLog("[ERR] Выберите шаблон.", "error");
    return false;
  }

  const result = await fetchJson(
    "/api/save-act",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    "Сервер не отвечает: акт не сохранен"
  );
  if (!result) return false;
  const { response, data } = result;
  if (!response.ok) {
    editorLog("[ERR] " + (data.detail || "Не удалось сохранить акт"), "error");
    return false;
  }
  editorState.isNew = false;
  editorState.currentFilename = filename;
  editorSetDirty(false);
  await editorLoadActs();
  editorLog("[OK] Акт сохранен: " + filename, "success");
  return true;
}

async function editorDeleteFromList(filename) {
  if (!window.confirm(`Удалить акт ${filename}?`)) return;
  const result = await fetchJson(
    "/api/delete-act",
    {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ workspace: editorWorkspace(), filename }),
    },
    "Сервер не отвечает: акт не удален"
  );
  if (!result) return;
  const { response, data } = result;
  if (!response.ok) {
    editorLog("[ERR] " + (data.detail || "Не удалось удалить акт"), "error");
    return;
  }
  if (editorState.currentFilename === filename) editorResetForm();
  await editorLoadActs();
  editorLog("[OK] Акт удален: " + filename, "success");
}

async function editorDeleteAct() {
  const filename = editorNormalizeFilename(document.getElementById("editorFilename").value);
  if (!filename) {
    editorLog("[ERR] Не задано имя файла.", "error");
    return;
  }
  await editorDeleteFromList(filename);
}

async function editorGenerateAct() {
  const saveOk = await editorSaveAct();
  if (!saveOk) return;
  const filename = editorNormalizeFilename(document.getElementById("editorFilename").value);
  const template = editorCurrentTemplate() || null;
  const result = await fetchJson(
    "/api/build-one",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        workspace: editorWorkspace(),
        act: filename,
        template,
        output_dir: outputDir(),
      }),
    },
    "Сервер не отвечает: генерация не выполнена"
  );
  if (!result) return;
  const { response, data } = result;
  if (!response.ok) {
    editorLog("[ERR] " + (data.detail || "Ошибка генерации"), "error");
    return;
  }
  for (const line of data.log || []) {
    if (typeof log === "function") log(line);
  }
  if (typeof upsertResults === "function") upsertResults(data.files || []);
  editorState.lastGeneratedFile = Array.isArray(data.files) && data.files.length ? data.files[0] : null;
  editorRenderGenerationResult();
  editorLog("[OK] Документ сгенерирован", "success");
}

function editorAddField() {
  editorState.fields.push({ name: "", value: "", type: "text", format: null });
  editorMarkDirty();
  editorRenderFields();
  editorRenderProjectFields();
  editorRenderTemplateVariables();
}

function editorAddMissingFields() {
  const missing = editorGetMissingTemplateVariables();
  if (!missing.length) return;
  const existing = new Set(editorFieldNames());
  for (const name of missing) {
    if (existing.has(name)) continue;
    editorState.fields.push({ name, value: "", type: "text", format: null });
    existing.add(name);
  }
  editorMarkDirty();
  editorRenderFields();
  editorRenderTemplateVariables();
  editorRenderProjectFields();
}

async function editorOnScreenChange(screen) {
  if (screen !== "editor") return;
  await editorLoadActs();
  if (document.getElementById("editorCard").style.display !== "none") {
    await editorLoadTemplateVariables();
  }
}

window.editorCreateAct = editorCreateAct;
window.editorBackToList = editorBackToList;
window.editorSaveAct = editorSaveAct;
window.editorDeleteAct = editorDeleteAct;
window.editorGenerateAct = editorGenerateAct;
window.editorAddField = editorAddField;
window.editorAddMissingFields = editorAddMissingFields;
window.editorOnScreenChange = editorOnScreenChange;
window.editorCanLeaveScreen = () => editorConfirmDiscardIfDirty("перейти на другой экран");

document.getElementById("editorTemplate").addEventListener("change", () => {
  editorMarkDirty();
  void editorLoadTemplateVariables();
});
document.getElementById("editorFilename").addEventListener("input", editorMarkDirty);
document.getElementById("editorOutputName").addEventListener("input", editorMarkDirty);
document.getElementById("editorNumberPrefix").addEventListener("input", editorMarkDirty);
document.getElementById("editorNumberValue").addEventListener("input", editorMarkDirty);
window.addEventListener("beforeunload", (event) => {
  if (!editorState.isDirty || !editorIsFormVisible()) return;
  event.preventDefault();
  event.returnValue = "";
});
