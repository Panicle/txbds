let map;
let markers = {};
let positionHistory = [];
let ws;
let mapInitialized = false;

const config = {
    backendUrl: null
};

function initMap() {
    console.log('初始化本地地图...');
    
    const mapContainer = document.getElementById('map');
    mapContainer.innerHTML = '';
    
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', '100%');
    svg.setAttribute('viewBox', '0 0 800 600');
    svg.style.background = '#e8f4f8';
    
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    
    const gridPattern = document.createElementNS('http://www.w3.org/2000/svg', 'pattern');
    gridPattern.setAttribute('id', 'grid');
    gridPattern.setAttribute('width', '50');
    gridPattern.setAttribute('height', '50');
    gridPattern.setAttribute('patternUnits', 'userSpaceOnUse');
    
    const gridPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    gridPath.setAttribute('d', 'M 50 0 L 0 0 0 50');
    gridPath.setAttribute('fill', 'none');
    gridPath.setAttribute('stroke', '#c0d8e8');
    gridPath.setAttribute('stroke-width', '0.5');
    gridPattern.appendChild(gridPath);
    defs.appendChild(gridPattern);
    
    const bgRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    bgRect.setAttribute('width', '800');
    bgRect.setAttribute('height', '600');
    bgRect.setAttribute('fill', 'url(#grid)');
    svg.appendChild(defs);
    svg.appendChild(bgRect);
    
    for (let i = 0; i <= 16; i++) {
        const x = i * 50;
        const vLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        vLine.setAttribute('x1', x);
        vLine.setAttribute('y1', 0);
        vLine.setAttribute('x2', x);
        vLine.setAttribute('y2', 600);
        vLine.setAttribute('stroke', i % 4 === 0 ? '#9ec6d8' : '#d8e8f0');
        vLine.setAttribute('stroke-width', i % 4 === 0 ? 1 : 0.5);
        svg.appendChild(vLine);
    }
    
    for (let i = 0; i <= 12; i++) {
        const y = i * 50;
        const hLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        hLine.setAttribute('x1', 0);
        hLine.setAttribute('y1', y);
        hLine.setAttribute('x2', 800);
        hLine.setAttribute('y2', y);
        hLine.setAttribute('stroke', i % 3 === 0 ? '#9ec6d8' : '#d8e8f0');
        hLine.setAttribute('stroke-width', i % 3 === 0 ? 1 : 0.5);
        svg.appendChild(hLine);
    }
    
    const centerX = 400;
    const centerY = 300;
    
    const centerCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    centerCircle.setAttribute('cx', centerX);
    centerCircle.setAttribute('cy', centerY);
    centerCircle.setAttribute('r', 15);
    centerCircle.setAttribute('fill', '#3498db');
    centerCircle.setAttribute('stroke', '#fff');
    centerCircle.setAttribute('stroke-width', 3);
    centerCircle.setAttribute('opacity', 0.6);
    svg.appendChild(centerCircle);
    
    const centerLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    centerLabel.setAttribute('x', centerX);
    centerLabel.setAttribute('y', centerY - 25);
    centerLabel.setAttribute('text-anchor', 'middle');
    centerLabel.setAttribute('fill', '#2980b9');
    centerLabel.setAttribute('font-size', '14');
    centerLabel.setAttribute('font-weight', 'bold');
    centerLabel.textContent = '基准位置';
    svg.appendChild(centerLabel);
    
    const coordLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    coordLabel.setAttribute('x', centerX);
    coordLabel.setAttribute('y', centerY + 35);
    coordLabel.setAttribute('text-anchor', 'middle');
    coordLabel.setAttribute('fill', '#7f8c8d');
    coordLabel.setAttribute('font-size', '11');
    coordLabel.textContent = 'N 34.26°, E 108.95°';
    svg.appendChild(coordLabel);
    
    const scaleBar = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    scaleBar.setAttribute('x', '720');
    scaleBar.setAttribute('y', '560');
    scaleBar.setAttribute('width', '60');
    scaleBar.setAttribute('height', '8');
    scaleBar.setAttribute('fill', '#fff');
    scaleBar.setAttribute('stroke', '#34495e');
    scaleBar.setAttribute('stroke-width', '1');
    svg.appendChild(scaleBar);
    
    const scaleLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    scaleLabel.setAttribute('x', '750');
    scaleLabel.setAttribute('y', '578');
    scaleLabel.setAttribute('text-anchor', 'middle');
    scaleLabel.setAttribute('fill', '#34495e');
    scaleLabel.setAttribute('font-size', '10');
    scaleLabel.textContent = '500m';
    svg.appendChild(scaleLabel);
    
    mapContainer.appendChild(svg);
    
    map = {
        svg: svg,
        addOverlay: function(marker) {
            if (marker && marker.element) {
                svg.appendChild(marker.element);
            }
        },
        removeOverlay: function(marker) {
            if (marker && marker.element && marker.element.parentNode) {
                marker.element.parentNode.removeChild(marker.element);
            }
        },
        panTo: function(point) {
            console.log('移动到:', point);
        }
    };
    
    addLegend();
    mapInitialized = true;
    console.log('本地地图初始化成功');
}

function addLegend() {
    const legend = document.createElement('div');
    legend.className = 'legend';
    legend.innerHTML = `
        <div class="legend-item">
            <div class="legend-color person"></div>
            <span>人员定位</span>
        </div>
        <div class="legend-item">
            <div class="legend-color shoe-e1"></div>
            <span>铁鞋初步定位</span>
        </div>
        <div class="legend-item">
            <div class="legend-color shoe-e2"></div>
            <span>铁鞋改正后</span>
        </div>
        <div class="legend-item">
            <div class="legend-color shoe-e3"></div>
            <span>铁鞋精密定位</span>
        </div>
    `;
    
    const mapContainer = document.getElementById('map');
    mapContainer.appendChild(legend);
}

function connectWebSocket() {
    let wsUrl;
    
    if (config.backendUrl) {
        const protocol = config.backendUrl.startsWith('https') ? 'wss:' : 'ws:';
        const url = new URL(config.backendUrl);
        wsUrl = `${protocol}//${url.host}/ws`;
    } else {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        wsUrl = `${protocol}//${window.location.host}/ws`;
    }
    
    console.log('WebSocket连接:', wsUrl);
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = function() {
        document.getElementById('connection-status').className = 'connected';
        document.getElementById('connection-status').textContent = '已连接';
        console.log('WebSocket连接成功');
    };
    
    ws.onmessage = function(event) {
        console.log('收到消息:', event.data);
        try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'history') {
                console.log('历史数据:', data.data);
                data.data.forEach(pos => {
                    addPosition(pos);
                });
            } else if (data.type === 'position') {
                console.log('位置数据:', data);
                addPosition(data);
            }
        } catch (e) {
            console.error('消息解析错误:', e);
        }
    };
    
    ws.onerror = function(error) {
        console.error('WebSocket错误:', error);
    };
    
    ws.onclose = function(event) {
        document.getElementById('connection-status').className = 'disconnected';
        document.getElementById('connection-status').textContent = '已断开';
        console.log('WebSocket连接关闭，5秒后重连:', event.code, event.reason);
        setTimeout(connectWebSocket, 5000);
    };
}

function addPosition(pos) {
    if (!mapInitialized) {
        console.warn('地图未初始化，无法添加位置标记');
        return;
    }
    
    const key = `${pos.device_id}-${pos.position_type}`;
    
    if (markers[key]) {
        if (typeof map.removeOverlay === 'function') {
            map.removeOverlay(markers[key]);
        }
    }
    
    const color = getMarkerColor(pos.position_type);
    
    const x = ((pos.lon - 108.93) / 0.04) * 800;
    const y = ((34.28 - pos.lat) / 0.04) * 600;
    
    const markerGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    
    const shadow = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    shadow.setAttribute('cx', x + 3);
    shadow.setAttribute('cy', y + 3);
    shadow.setAttribute('r', 14);
    shadow.setAttribute('fill', 'rgba(0,0,0,0.2)');
    markerGroup.appendChild(shadow);
    
    const outerCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    outerCircle.setAttribute('cx', x);
    outerCircle.setAttribute('cy', y);
    outerCircle.setAttribute('r', 14);
    outerCircle.setAttribute('fill', color);
    outerCircle.setAttribute('stroke', '#fff');
    outerCircle.setAttribute('stroke-width', 3);
    markerGroup.appendChild(outerCircle);
    
    const innerCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    innerCircle.setAttribute('cx', x);
    innerCircle.setAttribute('cy', y);
    innerCircle.setAttribute('r', 6);
    innerCircle.setAttribute('fill', '#fff');
    markerGroup.appendChild(innerCircle);
    
    markerGroup.setAttribute('style', 'cursor: pointer');
    
    markerGroup.addEventListener('click', function() {
        alert(`${pos.position_type_name}\n设备ID: ${pos.device_id}\n坐标: ${pos.lat.toFixed(6)}, ${pos.lon.toFixed(6)}\n高度: ${pos.alt.toFixed(2)}m`);
    });
    
    markerGroup.addEventListener('mouseenter', function() {
        outerCircle.setAttribute('r', 16);
        shadow.setAttribute('r', 16);
    });
    
    markerGroup.addEventListener('mouseleave', function() {
        outerCircle.setAttribute('r', 14);
        shadow.setAttribute('r', 14);
    });
    
    map.addOverlay({ element: markerGroup });
    markers[key] = { element: markerGroup, x: x, y: y };
    
    positionHistory.unshift({
        device_id: pos.device_id,
        position_type: pos.position_type,
        position_type_name: pos.position_type_name,
        lat: pos.lat,
        lon: pos.lon,
        alt: pos.alt,
        receive_time: new Date().toLocaleString('zh-CN')
    });
    
    if (positionHistory.length > 20) {
        positionHistory.pop();
    }
    
    updatePositionInfo(pos);
    updateHistoryList();
}

function getMarkerColor(positionType) {
    switch(positionType) {
        case 0x00: return '#3498db';
        case 0xE1: return '#e67e22';
        case 0xE2: return '#f39c12';
        case 0xE3: return '#27ae60';
        default: return '#95a5a6';
    }
}

function updatePositionInfo(pos) {
    const infoPanel = document.getElementById('position-info');
    infoPanel.innerHTML = `
        <div class="position-item">
            <div class="type">${pos.position_type_name}</div>
            <div class="coord">纬度: ${pos.lat.toFixed(6)}</div>
            <div class="coord">经度: ${pos.lon.toFixed(6)}</div>
            <div class="coord">高度: ${pos.alt.toFixed(2)}m</div>
            <div class="time">时间: ${new Date().toLocaleString('zh-CN')}</div>
        </div>
    `;
}

function updateHistoryList() {
    const historyPanel = document.getElementById('history-list');
    
    if (positionHistory.length === 0) {
        historyPanel.innerHTML = '<p>暂无记录</p>';
        return;
    }
    
    historyPanel.innerHTML = positionHistory.map((pos, index) => `
        <div class="position-item" style="opacity: ${1 - index * 0.04}">
            <div class="type">${pos.position_type_name}</div>
            <div class="coord">(${pos.lat.toFixed(4)}, ${pos.lon.toFixed(4)})</div>
            <div class="time">${pos.receive_time}</div>
        </div>
    `).join('');
}

function loadConfig() {
    const script = document.querySelector('script[data-backend-url]');
    if (script) {
        config.backendUrl = script.getAttribute('data-backend-url');
    }
}

window.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成');
    loadConfig();
    initMap();
    connectWebSocket();
});

console.log('智能铁鞋定位系统初始化');
