// Dynamic per-stock report
let chartInstance = null;
let currentPrice = 0;

const stocks = {
    'Reliance': {
        logo: '/static/image/reliance-logo.png',
        name: 'Reliance Industries Ltd',
        recommendation: 'BUY',
        target: '₹ 3,150',
        upside: '+10.5%',
        marketCap: '₹ 19.2 L Cr',
        todayHigh: 2890,
        todayLow: 2810,
        current: 2850,
        week52: 3200,
        overview: "Reliance Industries Limited is India’s largest private sector company with diversified operations across petrochemicals, refining, oil & gas, retail, and digital services (Jio).",
        chart: {
            '1D': { labels: ['09:30','11:00','13:00','15:00','16:00'], data: [2810,2825,2840,2860,2850] },
            '1W': { labels: ['Mon','Tue','Wed','Thu','Fri'], data: [2700,2750,2780,2820,2850] },
            '1M': { labels: ['W1','W2','W3','W4','Now'], data: [2550,2620,2700,2780,2850] },
            '3M': { labels: ['M1','M2','M3','Now',''], data: [2450,2600,2750,2850,2850] },
            '1Y': { labels: ['Jan','Apr','Jul','Oct','Dec'], data: [2200,2450,2700,2850,2850] }
        }
    },
    'Adani Power': {
        logo: '/static/image/adani-logo.png',
        name: 'Adani Power Ltd',
        recommendation: 'HOLD',
        target: '₹ 350',
        upside: '+12.1%',
        marketCap: '₹ 3.4 L Cr',
        todayHigh: 320,
        todayLow: 305,
        current: 312,
        week52: 450,
        overview: 'Adani Power is a leading power generation company in India.',
        risks: ['Commodity price exposure','Regulatory and policy risks','High debt levels'],
        chart: {
            '1D': { labels: ['09:30','11:00','13:00','15:00','16:00'], data: [308,310,315,318,312] },
            '1W': { labels: ['Mon','Tue','Wed','Thu','Fri'], data: [300,305,310,320,312] },
            '1M': { labels: ['W1','W2','W3','W4','Now'], data: [250,280,300,310,312] },
            '3M': { labels: ['M1','M2','M3','Now',''], data: [200,250,290,310,312] },
            '1Y': { labels: ['Jan','Apr','Jul','Oct','Dec'], data: [150,200,260,300,312] }
        }
    },
    'TCS': {
        logo: '/static/image/tcs-logo.jpg',
        name: 'Tata Consultancy Services',
        recommendation: 'BUY',
        target: '₹ 3,600',
        upside: '+7.8%',
        marketCap: '₹ 11.5 L Cr',
        todayHigh: 3360,
        todayLow: 3300,
        current: 3340,
        week52: 3600,
        overview: 'TCS is a leading global IT services and consulting company.',
        risks: ['Currency fluctuations','Client concentration','Tech sector cyclicality'],
        chart: {
            '1D': { labels: ['09:30','11:00','13:00','15:00','16:00'], data: [3310,3325,3335,3350,3340] },
            '1W': { labels: ['Mon','Tue','Wed','Thu','Fri'], data: [3200,3250,3300,3330,3340] },
            '1M': { labels: ['W1','W2','W3','W4','Now'], data: [3000,3100,3200,3300,3340] },
            '3M': { labels: ['M1','M2','M3','Now',''], data: [2800,3000,3200,3340,3340] },
            '1Y': { labels: ['Jan','Apr','Jul','Oct','Dec'], data: [2400,2700,3000,3300,3340] }
        }
    },
    'Yes Bank': {
        logo: '/static/image/yesbank-logo.png',
        name: 'Yes Bank Ltd',
        recommendation: 'SELL',
        target: '₹ 15',
        upside: '-17.6%',
        marketCap: '₹ 0.8 L Cr',
        todayHigh: 19,
        todayLow: 17,
        current: 18,
        week52: 40,
        overview: 'Yes Bank is a private sector bank in India that has undergone restructuring.',
        risks: ['Balance sheet recovery','Regulatory scrutiny','Market liquidity'],
        chart: {
            '1D': { labels: ['09:30','11:00','13:00','15:00','16:00'], data: [18,18.2,18.4,18.1,18] },
            '1W': { labels: ['Mon','Tue','Wed','Thu','Fri'], data: [17,17.5,18,18.2,18] },
            '1M': { labels: ['W1','W2','W3','W4','Now'], data: [12,14,16,17.5,18] },
            '3M': { labels: ['M1','M2','M3','Now',''], data: [8,12,15,18,18] },
            '1Y': { labels: ['Jan','Apr','Jul','Oct','Dec'], data: [5,8,12,15,18] }
        }
    }
};

function getQueryParam(name) {
    const params = new URLSearchParams(window.location.search);
    return params.get(name);
}

function populateStock(stockKey) {
    const s = stocks[stockKey] || stocks['Reliance'];
    currentPrice = s.current;

    const logoEl = document.getElementById('companyLogo');
    const nameEl = document.getElementById('companyName');
    if (logoEl) logoEl.src = s.logo;
    if (nameEl) nameEl.textContent = s.name;

    const rec = document.getElementById('recommendation');
    const tgt = document.getElementById('targetPrice');
    const up = document.getElementById('expectedUpside');
    const mc = document.getElementById('marketCap');
    if (rec) rec.textContent = s.recommendation;
    if (tgt) tgt.textContent = s.target;
    if (up) up.textContent = s.upside;
    if (mc) mc.textContent = s.marketCap;

    const todayHigh = document.getElementById('todayHigh');
    const todayLow = document.getElementById('todayLow');
    const curr = document.getElementById('currentPrice');
    const week52 = document.getElementById('week52');
    if (todayHigh) todayHigh.textContent = '₹ ' + s.todayHigh.toLocaleString('en-IN');
    if (todayLow) todayLow.textContent = '₹ ' + s.todayLow.toLocaleString('en-IN');
    if (curr) curr.textContent = '₹ ' + s.current.toLocaleString('en-IN');
    if (week52) week52.textContent = '₹ ' + s.week52.toLocaleString('en-IN');

    const overviewEl = document.getElementById('companyOverview');
    if (overviewEl) overviewEl.textContent = s.overview;

    const risksContainer = document.getElementById('risksList');
    if (risksContainer) {
        risksContainer.innerHTML = '';
        (s.risks || []).forEach(r => {
            const item = document.createElement('div');
            item.className = 'risk-item';
            item.innerHTML = `<span class="risk-icon">⚠️</span><span>${r}</span>`;
            risksContainer.appendChild(item);
        });
    }

    window.selectedStockChart = s.chart;
}

document.addEventListener('DOMContentLoaded', function() {
    const stockParam = getQueryParam('stock') || 'Reliance';
    populateStock(stockParam);
    initializeChart('1D');
    setupEventListeners();
});

function initializeChart(period) {
    const ctx = document.getElementById('priceChart').getContext('2d');
    const sChart = window.selectedStockChart || stocks['Reliance'].chart;
    const data = sChart[period] || { labels: [], data: [] };

    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Price',
                data: data.data,
                borderColor: '#1f3c88',
                backgroundColor: 'rgba(31,60,136,0.08)',
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { ticks: { callback: v => '₹' + v } }, x: { grid: { display: false } } }
        }
    });
}

function changeChart(period) {
    document.querySelectorAll('.chart-btn').forEach(btn => btn.classList.remove('active'));
    const btn = document.querySelector(`.chart-btn[data-period="${period}"]`);
    if (btn) btn.classList.add('active');
    initializeChart(period);
}

function setupEventListeners() {
    const quantityInput = document.getElementById('quantity');
    const exchangeSelect = document.getElementById('exchange');
    if (quantityInput) quantityInput.addEventListener('input', updateCostDisplay);
    if (exchangeSelect) exchangeSelect.addEventListener('change', () => {});
    updateCostDisplay();
}

function updateCostDisplay() {
    const qRaw = document.getElementById('quantity').value;
    let quantity = parseInt(qRaw);
    if (!Number.isFinite(quantity) || quantity < 1) quantity = 1;
    const totalCost = currentPrice * quantity;
    const tc = document.getElementById('totalCost');
    const cb = document.getElementById('costBreakdown');
    if (tc) tc.textContent = totalCost.toLocaleString('en-IN');
    if (cb) cb.textContent = `(${quantity} share${quantity>1? 's':''} × ₹${currentPrice.toLocaleString('en-IN')})`;
}

function buyStock() {
    const exchange = document.getElementById('exchange').value.toUpperCase();
    const quantity = document.getElementById('quantity').value || '1';
    const totalCost = currentPrice * parseInt(quantity || 1);
    alert(`BUY ORDER\n\nExchange: ${exchange}\nQuantity: ${quantity} shares\nPrice: ₹${currentPrice.toLocaleString('en-IN')} per share\nTotal Cost: ₹${totalCost.toLocaleString('en-IN')}`);
    document.getElementById('quantity').value = 1; updateCostDisplay();
}

function sellStock() {
    const exchange = document.getElementById('exchange').value.toUpperCase();
    const quantity = document.getElementById('quantity').value || '1';
    const totalCost = currentPrice * parseInt(quantity || 1);
    alert(`SELL ORDER\n\nExchange: ${exchange}\nQuantity: ${quantity} shares\nPrice: ₹${currentPrice.toLocaleString('en-IN')} per share\nTotal Cost: ₹${totalCost.toLocaleString('en-IN')}`);
    document.getElementById('quantity').value = 1; updateCostDisplay();
}
