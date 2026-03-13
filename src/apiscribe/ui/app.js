// Функция для скачивания OpenAPI спецификации
async function downloadOpenAPI() {
    const button = document.getElementById("downloadOpenAPI");
    try {
        button.disabled = true;
        button.innerHTML = `
            <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Loading...
        `;

        const response = await fetch("/openapi");
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `openapi_${new Date().toISOString().slice(0,10)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error("Failed to download OpenAPI:", error);
        alert("Error downloading OpenAPI: " + error.message);
    } finally {
        button.disabled = false;
        button.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            OpenAPI
        `;
    }
}

// Функция для получения и отображения статуса
async function loadStatus() {
    const data = await api("/api/status");
    const statusEl = document.getElementById("status");
    if (data.running) {
        statusEl.textContent = `Running → ${data.target}`;
        statusEl.classList.remove("bg-gray-500", "bg-red-500");
        statusEl.classList.add("bg-green-500");
    } else {
        statusEl.textContent = "Stopped";
        statusEl.classList.remove("bg-green-500", "bg-red-500");
        statusEl.classList.add("bg-gray-500");
    }
}

// Запуск прокси
async function startProxy() {
    const target = document.getElementById("target").value;
    try {
        await api("/api/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ target_url: target })
        });
        loadStatus();
    } catch (error) {
        console.error("Start error:", error);
    }
}

// Остановка прокси
async function stopProxy() {
    try {
        await api("/api/stop", { method: "POST" });
        loadStatus();
    } catch (error) {
        console.error("Stop error:", error);
    }
}

// Загрузка статистики
async function loadStats() {
    const data = await api("/api/stats");
    document.getElementById("totalRequests").textContent = data.total_requests;
    document.getElementById("endpointCount").textContent = data.endpoint_count;
    renderMethods(data.methods);
}

// Отображение методов в виде цветных бейджей
function renderMethods(methods) {
    const container = document.getElementById("methodsStats");
    container.innerHTML = "";
    if (!methods || Object.keys(methods).length === 0) {
        container.textContent = "No data";
        return;
    }
    const methodColors = {
        GET: "bg-blue-100 text-blue-800",
        POST: "bg-green-100 text-green-800",
        PUT: "bg-yellow-100 text-yellow-800",
        PATCH: "bg-purple-100 text-purple-800",
        DELETE: "bg-red-100 text-red-800"
    };
    for (const [method, count] of Object.entries(methods)) {
        const badge = document.createElement("span");
        badge.className = `px-2 py-1 rounded-full text-xs font-semibold ${methodColors[method] || "bg-gray-100 text-gray-800"}`;
        badge.textContent = `${method} ${count}`;
        container.appendChild(badge);
    }
}

// Загрузка списка эндпоинтов
async function loadEndpoints() {
    const endpoints = await api("/api/endpoints");
    const table = document.getElementById("endpointTable");
    table.innerHTML = "";
    endpoints.forEach(ep => {
        const row = document.createElement("tr");
        row.className = "border-b hover:bg-gray-50";
        let methodColor = "text-gray-800";
        if (ep.method === "GET") methodColor = "text-blue-600 font-bold";
        else if (ep.method === "POST") methodColor = "text-green-600 font-bold";
        else if (ep.method === "PUT") methodColor = "text-yellow-600 font-bold";
        else if (ep.method === "PATCH") methodColor = "text-purple-600 font-bold";
        else if (ep.method === "DELETE") methodColor = "text-red-600 font-bold";
        row.innerHTML = `
            <td class="p-2"><span class="${methodColor}">${ep.method}</span></td>
            <td class="p-2 font-mono">${ep.path}</td>
            <td class="p-2 text-right">${ep.count}</td>
        `;
        table.appendChild(row);
    });
}

// Подключение к WebSocket для логов с обработкой ошибок
function connectLogs() {
    const ws = new WebSocket("ws://localhost:9001/ws/logs");
    ws.onopen = () => console.log("WebSocket connected");
    ws.onerror = (err) => console.error("WebSocket error:", err);
    ws.onclose = () => {
        console.log("WebSocket closed, reconnecting in 3 seconds...");
        setTimeout(connectLogs, 3000);
    };
    ws.onmessage = e => {
        try {
            const log = JSON.parse(e.data);
            const logsDiv = document.getElementById("logs");
            const el = document.createElement("div");
            // Добавляем временную метку и цвет статуса
            const statusClass = log.status >= 500 ? 'text-red-400' :
                               log.status >= 400 ? 'text-yellow-400' :
                               'text-green-400';
            el.innerHTML = `${new Date().toLocaleTimeString()} ${log.method} ${log.path} → <span class="${statusClass}">${log.status}</span>`;
            logsDiv.prepend(el);
            // Ограничиваем количество логов до 100
            if (logsDiv.children.length > 100) {
                logsDiv.removeChild(logsDiv.lastChild);
            }
        } catch (err) {
            console.error("Error processing log:", err);
        }
    };
}

// Обновление всех данных
function refresh() {
    loadStats();
    loadEndpoints();
    loadStatus();
}

// Привязка событий после загрузки страницы
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("downloadOpenAPI").addEventListener("click", downloadOpenAPI);
    connectLogs();
    refresh();
    setInterval(refresh, 2000);
});