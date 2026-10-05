import "./icons.css";
import "./styles.css";

document.documentElement.classList.add("js");

const menuButton = document.querySelector("[data-menu-toggle]");
const sidebar = document.querySelector("[data-sidebar]");
const overlay = document.querySelector("[data-sidebar-overlay]");

function setMenu(open) {
  if (!menuButton || !sidebar || !overlay) return;

  menuButton.setAttribute("aria-expanded", String(open));
  menuButton.setAttribute("aria-label", open ? "Cerrar menú" : "Abrir menú");
  sidebar.dataset.open = String(open);
  overlay.hidden = !open;
  document.body.classList.toggle("menu-open", open);
}

menuButton?.addEventListener("click", () => {
  setMenu(menuButton.getAttribute("aria-expanded") !== "true");
});

overlay?.addEventListener("click", () => setMenu(false));

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && menuButton?.getAttribute("aria-expanded") === "true") {
    setMenu(false);
    menuButton.focus();
  }
});

const desktopMedia = window.matchMedia("(min-width: 48.001rem)");
desktopMedia.addEventListener("change", (event) => {
  if (event.matches) setMenu(false);
});

for (const alert of document.querySelectorAll(".alert")) {
  const closeButton = alert.querySelector("[data-alert-close]");
  closeButton?.addEventListener("click", () => {
    alert.classList.add("is-leaving");
    alert.addEventListener("animationend", () => alert.remove(), { once: true });
  });
}

for (const toggle of document.querySelectorAll("[data-password-toggle]")) {
  const input = document.getElementById(toggle.dataset.passwordToggle);
  if (!input) continue;

  toggle.addEventListener("click", () => {
    const showing = input.type === "text";
    input.type = showing ? "password" : "text";
    toggle.setAttribute("aria-pressed", String(!showing));
    toggle.setAttribute("aria-label", showing ? "Mostrar contraseña" : "Ocultar contraseña");
    const icon = toggle.querySelector("i");
    icon?.classList.toggle("ph-eye", showing);
    icon?.classList.toggle("ph-eye-slash", !showing);
  });
}

const maintenanceStatus = document.querySelector("[data-maintenance-status]");
const scheduledAt = document.getElementById("fecha_programada");
const startedAt = document.getElementById("fecha_inicio");
const finishedAt = document.getElementById("fecha_fin");

function updateMaintenanceRequirements() {
  if (!maintenanceStatus || !scheduledAt || !startedAt || !finishedAt) return;
  const status = maintenanceStatus.value;
  scheduledAt.required = status === "PROGRAMADO";
  startedAt.required = status === "EN_PROCESO" || status === "COMPLETADO";
  finishedAt.required = status === "COMPLETADO";
}

maintenanceStatus?.addEventListener("change", updateMaintenanceRequirements);
startedAt?.addEventListener("change", () => {
  if (finishedAt) finishedAt.min = startedAt.value;
});
updateMaintenanceRequirements();
if (startedAt?.value && finishedAt) finishedAt.min = startedAt.value;

const svgNamespace = "http://www.w3.org/2000/svg";

function svgElement(name, attributes = {}, textContent = "") {
  const element = document.createElementNS(svgNamespace, name);
  for (const [key, value] of Object.entries(attributes)) {
    element.setAttribute(key, String(value));
  }
  if (textContent) element.textContent = textContent;
  return element;
}

function chartData(selector) {
  const source = document.querySelector(selector);
  if (!source) return [];
  try {
    return JSON.parse(source.textContent);
  } catch {
    return [];
  }
}

function renderLineChart() {
  const container = document.querySelector("[data-line-chart]");
  const svg = container?.querySelector("svg");
  const points = chartData("[data-line-chart-data]");
  if (!container || !svg || !points.length) return;

  const width = 820;
  const height = 300;
  const padding = { top: 24, right: 24, bottom: 46, left: 62 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const values = points.flatMap((point) => [point.value, point.minimum, point.maximum]);
  let minimum = Math.min(...values);
  let maximum = Math.max(...values);
  const span = maximum - minimum || Math.max(Math.abs(maximum), 1);
  minimum -= span * 0.12;
  maximum += span * 0.12;

  const x = (index) => padding.left + (points.length === 1 ? chartWidth / 2 : (index * chartWidth) / (points.length - 1));
  const y = (value) => padding.top + ((maximum - value) * chartHeight) / (maximum - minimum);
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.replaceChildren();

  for (let index = 0; index <= 4; index += 1) {
    const gridY = padding.top + (chartHeight * index) / 4;
    const label = maximum - ((maximum - minimum) * index) / 4;
    svg.append(svgElement("line", { x1: padding.left, y1: gridY, x2: width - padding.right, y2: gridY, class: "chart-grid-line" }));
    svg.append(svgElement("text", { x: padding.left - 10, y: gridY + 4, class: "chart-axis-label", "text-anchor": "end" }, label.toFixed(1)));
  }

  const upper = points.map((point, index) => `${x(index)},${y(point.maximum)}`);
  const lower = points.map((point, index) => `${x(index)},${y(point.minimum)}`).reverse();
  svg.append(svgElement("polygon", { points: [...upper, ...lower].join(" "), class: "chart-range-area" }));
  const linePath = points.map((point, index) => `${index ? "L" : "M"} ${x(index)} ${y(point.value)}`).join(" ");
  svg.append(svgElement("path", { d: linePath, class: "chart-value-line" }));

  points.forEach((point, index) => {
    const circle = svgElement("circle", {
      cx: x(index),
      cy: y(point.value),
      r: point.outOfRange ? 5 : 3.5,
      class: point.outOfRange ? "chart-point chart-point-alert" : "chart-point",
    });
    circle.append(svgElement("title", {}, `${point.value} · ${new Date(point.measuredAt).toLocaleString("es-MX")}`));
    svg.append(circle);
  });

  const labelIndexes = [...new Set([0, Math.floor((points.length - 1) / 2), points.length - 1])];
  labelIndexes.forEach((index) => {
    const date = new Date(points[index].measuredAt);
    svg.append(svgElement("text", { x: x(index), y: height - 16, class: "chart-axis-label", "text-anchor": "middle" }, date.toLocaleDateString("es-MX", { day: "2-digit", month: "short" })));
  });
}

function renderBarChart() {
  const container = document.querySelector("[data-bar-chart]");
  const svg = container?.querySelector("svg");
  const items = chartData("[data-bar-chart-data]");
  if (!container || !svg || !items.length) return;

  const width = 720;
  const height = 290;
  const padding = { top: 28, right: 20, bottom: 44, left: 58 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const maximumCost = Math.max(...items.map((item) => item.cost));
  const hasCosts = maximumCost > 0;
  const maximum = hasCosts ? maximumCost : 1;
  const slot = chartWidth / items.length;
  const barWidth = Math.min(slot * 0.52, 54);
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.replaceChildren();

  const defs = svgElement("defs");
  const gradient = svgElement("linearGradient", {
    id: "cost-bar-gradient",
    x1: "0%",
    y1: "100%",
    x2: "0%",
    y2: "0%",
  });
  gradient.append(
    svgElement("stop", { offset: "0%", "stop-color": "#4d5fd1" }),
    svgElement("stop", { offset: "100%", "stop-color": "#aeb8f6" }),
  );
  defs.append(gradient);
  svg.append(defs);

  for (let index = 0; index <= 4; index += 1) {
    const gridY = padding.top + (chartHeight * index) / 4;
    const label = hasCosts ? maximum - (maximum * index) / 4 : 0;
    svg.append(svgElement("line", { x1: padding.left, y1: gridY, x2: width - padding.right, y2: gridY, class: "chart-grid-line" }));
    svg.append(svgElement("text", { x: padding.left - 9, y: gridY + 4, class: "chart-axis-label", "text-anchor": "end" }, `$${Math.round(label).toLocaleString("es-MX")}`));
  }

  items.forEach((item, index) => {
    const center = padding.left + slot * index + slot / 2;
    const barHeight = (item.cost * chartHeight) / maximum;
    const barY = padding.top + chartHeight - barHeight;
    svg.append(svgElement("rect", {
      x: center - barWidth / 2,
      y: padding.top,
      width: barWidth,
      height: chartHeight,
      rx: 8,
      class: "chart-bar-track",
    }));
    const bar = svgElement("rect", {
      x: center - barWidth / 2,
      y: barY,
      width: barWidth,
      height: Math.max(barHeight, 2),
      rx: 8,
      class: "chart-bar",
    });
    bar.append(svgElement("title", {}, `${item.label}: $${item.cost.toLocaleString("es-MX")} · ${item.correctives} correctivos`));
    svg.append(bar);
    svg.append(svgElement("text", { x: center, y: height - 16, class: "chart-axis-label", "text-anchor": "middle" }, item.label));
    svg.append(svgElement("text", { x: center, y: Math.max(barY - 8, 16), class: "chart-bar-label", "text-anchor": "middle" }, `${item.correctives} corr.`));
  });
}

renderLineChart();
renderBarChart();
