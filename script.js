// 实时更新时间
function updateDateTime() {
    const now = new Date();
    const formatted = now.toISOString().slice(0, 19).replace('T', ' ');
    document.querySelector('.datetime-info').textContent = formatted;
}

// 初始化并每秒更新
updateDateTime();
setInterval(updateDateTime, 1000);

// 时间筛选切换
const filterBtns = document.querySelectorAll('.filter-btn');
filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    });
});

// 自动定位功能
document.querySelector('.btn-auto-location').addEventListener('click', () => {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude.toFixed(4);
                const lng = position.coords.longitude.toFixed(4);
                document.querySelectorAll('.input-field input')[0].value = lng;
                document.querySelectorAll('.input-field input')[1].value = lat;
            },
            (error) => {
                alert('无法获取位置: ' + error.message);
            }
        );
    } else {
        alert('您的浏览器不支持地理位置服务');
    }
});

// 天体对象交互
const celestialObjects = document.querySelectorAll('.celestial-object');
celestialObjects.forEach(obj => {
    obj.addEventListener('click', () => {
        alert('点击了天体对象! 这里可以显示详细信息');
    });
});

// 缩放控制
let zoomLevel = 1;
document.querySelectorAll('.btn-zoom').forEach(btn => {
    btn.addEventListener('click', (e) => {
        if (e.target.textContent === '放大') {
            zoomLevel = Math.min(zoomLevel + 0.2, 2);
        } else {
            zoomLevel = Math.max(zoomLevel - 0.2, 0.5);
        }
        document.querySelector('.chart-canvas').style.transform = `scale(${zoomLevel})`;
    });
});

// 全屏切换
document.querySelector('.btn-primary').addEventListener('click', () => {
    const chart = document.querySelector('.sky-chart');
    if (document.fullscreenElement) {
        document.exitFullscreen();
    } else {
        chart.requestFullscreen();
    }
});

// 时间轴交互
const timelineBar = document.querySelector('.timeline-bar');
timelineBar.addEventListener('click', (e) => {
    const rect = timelineBar.getBoundingClientRect();
    const percent = ((e.clientX - rect.left) / rect.width) * 100;
    document.querySelector('.timeline-progress').style.width = percent + '%';
});

// 目标卡片高亮
const targetCards = document.querySelectorAll('.target-card');
targetCards.forEach(card => {
    card.addEventListener('mouseenter', () => {
        card.style.borderColor = '#2563EB';
        card.style.border = '1px solid #2563EB';
    });
    card.addEventListener('mouseleave', () => {
        card.style.borderColor = 'transparent';
        card.style.border = 'none';
    });
});

console.log('AI Skywatcher Demo loaded successfully!');
