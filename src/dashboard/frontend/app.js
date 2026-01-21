const CONFIG = {
    apiBase: 'http://localhost:8000',
    refreshRate: 5000
};

// Elements
const riskMapCanvas = document.getElementById('riskMap');
const ctx = riskMapCanvas.getContext('2d');
const clockEl = document.getElementById('clock');
const alertList = document.getElementById('alert-list');

// Resize Canvas
function resizeCanvas() {
    const parent = riskMapCanvas.parentElement;
    riskMapCanvas.width = parent.clientWidth;
    riskMapCanvas.height = parent.clientHeight;
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

// Initial Mock Render
function drawMockHeatmap() {
    const w = riskMapCanvas.width;
    const h = riskMapCanvas.height;

    // Clear
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, w, h);

    // Draw Terrain features (lines)
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 1;
    for (let i = 0; i < w; i += 20) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i, h);
        ctx.stroke();
    }

    // Draw Hotspots
    for (let i = 0; i < 5; i++) {
        const x = Math.random() * w;
        const y = Math.random() * h;
        const radius = Math.random() * 50 + 20;

        const grad = ctx.createRadialGradient(x, y, 0, x, y, radius);
        grad.addColorStop(0, 'rgba(255, 42, 109, 0.8)');
        grad.addColorStop(1, 'rgba(255, 42, 109, 0)');

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fill();
    }
}

// Clock
setInterval(() => {
    const now = new Date();
    clockEl.innerText = now.toISOString().split('T')[1].split('.')[0] + " UTC";
}, 1000);

// Polling
async function fetchData() {
    try {
        const res = await fetch(`${CONFIG.apiBase}/status`);
        const data = await res.json();
        console.log("System Status:", data);

        // In real app, we'd fetch /predict result and render grid
    } catch (e) {
        console.warn("Offline Mode / API unreachable");
    }
}

// Start
drawMockHeatmap();
// setInterval(fetchData, CONFIG.refreshRate);
