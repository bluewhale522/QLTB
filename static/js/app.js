// Hệ thống Quản lý Thiết bị Trường học (QLTB) - Frontend Logic

let currentTab = 'dashboard';
let categoryChartInstance = null;
let locationChartInstance = null;

let state = {
    devices: [],
    categories: [],
    locations: [],
    users: [],
    borrowRequests: [],
    movements: [],
    floors: [],
    standardDevices: [],
    stats: null,
    currentUser: {
        id: 0,
        username: 'guest',
        fullname: 'Khách vãng lai',
        role: 'guest',
        is_authenticated: false
    }
};

// Khởi chạy khi load trang
document.addEventListener('DOMContentLoaded', async () => {
    lucide.createIcons();
    await loadInitialData();
    await switchTab('dashboard');
    setupFilterEvents();
});

// Setup realtime filter event listeners
function setupFilterEvents() {
    const searchInput = document.getElementById('deviceSearchInput');
    const catFilter = document.getElementById('deviceCategoryFilter');
    const statusFilter = document.getElementById('deviceStatusFilter');
    const floorFilter = document.getElementById('deviceFloorFilter');
    const locFilter = document.getElementById('deviceLocationFilter');

    let debounceTimer;
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => loadDevices(), 300);
        });
    }
    if (catFilter) catFilter.addEventListener('change', () => loadDevices());
    if (statusFilter) statusFilter.addEventListener('change', () => loadDevices());
    if (floorFilter) {
        floorFilter.addEventListener('change', (e) => {
            onFloorFilterChange(e.target.value);
            loadDevices();
        });
    }
    if (locFilter) locFilter.addEventListener('change', () => loadDevices());

    const borrowSearch = document.getElementById('borrowSearchInput');
    const borrowStatus = document.getElementById('borrowStatusFilter');
    if (borrowSearch) {
        borrowSearch.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => loadBorrowRequests(), 300);
        });
    }
    if (borrowStatus) borrowStatus.addEventListener('change', () => loadBorrowRequests());

    const moveSearch = document.getElementById('movementSearchInput');
    if (moveSearch) {
        moveSearch.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => loadMovements(), 300);
        });
    }
}

// Tải danh mục, phòng ban, người dùng, tầng và thiết bị chuẩn 2022 ban đầu
async function loadInitialData() {
    // 1. Tải thông tin phiên đăng nhập người dùng hiện tại
    try {
        const authRes = await fetch('/api/auth/me');
        if (authRes.ok) {
            const authData = await authRes.json();
            if (authData && authData.username) {
                state.currentUser = authData;
            }
        }
    } catch (err) {
        console.warn('Không tải được thông tin phiên đăng nhập:', err);
    }
    updateAuthUI();

    try {
        const [catRes, locRes, userRes] = await Promise.all([
            fetch('/api/categories'),
            fetch('/api/locations'),
            fetch('/api/users')
        ]);
        state.categories = await catRes.json();
        state.locations = await locRes.json();
        state.users = await userRes.json();
        console.log(`[QLTB] Loaded: ${state.categories.length} categories, ${state.locations.length} locations, ${state.users.length} users`);
    } catch (err) {
        console.error('Lỗi khi tải dữ liệu cơ bản:', err);
    }

    // Tải floors + standard devices riêng để không ảnh hưởng data chính
    try {
        const floorRes = await fetch('/api/floors');
        state.floors = await floorRes.json();
        console.log(`[QLTB] Loaded: ${state.floors.length} floors`);
    } catch (err) {
        console.warn('Không tải được danh sách tầng:', err);
        state.floors = [];
    }

    try {
        const stdDevRes = await fetch('/api/standard-devices');
        state.standardDevices = await stdDevRes.json();
        console.log(`[QLTB] Loaded: ${state.standardDevices.length} standard devices`);
    } catch (err) {
        console.warn('Không tải được danh sách thiết bị chuẩn:', err);
        state.standardDevices = [];
    }

    populateDropdowns();
    populateStandardDevicesDatalist();
}

// Điền danh sách gợi ý thiết bị chuẩn 2022
function populateStandardDevicesDatalist() {
    const datalist = document.getElementById('standardDeviceList');
    if (!datalist || !state.standardDevices) return;

    // Lọc danh sách thiết bị duy nhất
    const uniqueMap = new Map();
    state.standardDevices.forEach(d => {
        if (d.name && !uniqueMap.has(d.name)) {
            uniqueMap.set(d.name, d);
        }
    });

    datalist.innerHTML = Array.from(uniqueMap.values()).map(d => `
        <option value="${d.name}">${d.category ? `[${d.category}] ` : ''}${d.model ? `Model: ${d.model}` : ''}</option>
    `).join('');
}

// Điền các select dropdown
function populateDropdowns() {
    // Categories
    const devCatSelect = document.getElementById('deviceCategory');
    const devCatFilter = document.getElementById('deviceCategoryFilter');
    if (devCatSelect) {
        devCatSelect.innerHTML = state.categories.map(c => `<option value="${c.name}">${c.name}</option>`).join('');
        devCatSelect.onchange = () => updateSuggestedCode();
    }
    if (devCatFilter) {
        devCatFilter.innerHTML = '<option value="all">Tất cả danh mục</option>' +
            state.categories.map(c => `<option value="${c.name}">${c.name}</option>`).join('');
    }

    // Locations Filter
    updateLocationFilterByFloor('all');

    // Cập nhật bộ lọc tổ / phòng ban cán bộ
    const userDeptFilter = document.getElementById('userDeptFilter');
    if (userDeptFilter && state.users && state.users.length > 0) {
        const currentDept = userDeptFilter.value || 'all';
        const depts = [...new Set(state.users.map(u => u.department).filter(Boolean))].sort();
        userDeptFilter.innerHTML = '<option value="all">Tất cả tổ / ban</option>' +
            depts.map(d => `<option value="${d}" ${d === currentDept ? 'selected' : ''}>${d}</option>`).join('');
    }
}

// ==================== SEARCHABLE USER COMBOBOX ====================
function openAssignedUserDropdown() {
    const q = document.getElementById('deviceAssignedUserSearch')?.value || '';
    searchAssignedUsers(q);
    document.getElementById('deviceAssignedUserDropdown')?.classList.remove('hidden');
}

function closeAssignedUserDropdown() {
    document.getElementById('deviceAssignedUserDropdown')?.classList.add('hidden');
}

function searchAssignedUsers(query) {
    const dropdown = document.getElementById('deviceAssignedUserDropdown');
    if (!dropdown) return;
    dropdown.classList.remove('hidden');

    const q = (query || '').trim().toLowerCase();
    const clearBtn = document.getElementById('deviceAssignedUserClear');
    if (clearBtn) {
        clearBtn.classList.toggle('hidden', !q);
    }

    // Option Chưa bàn giao ở đầu
    let html = `
        <div onclick="selectAssignedUser('', '-- Chưa bàn giao / Dùng chung phòng học --')" 
             class="px-3 py-2 text-xs font-semibold text-slate-500 hover:bg-slate-100 cursor-pointer flex items-center transition">
            <span class="w-6 h-6 rounded-full bg-slate-200 text-slate-600 flex items-center justify-center font-bold text-[10px] mr-2">--</span>
            <span>-- Chưa bàn giao / Dùng chung phòng học --</span>
        </div>
    `;

    const filtered = (state.users || []).filter(u => {
        if (!q) return true;
        const nameMatch = (u.fullname || '').toLowerCase().includes(q);
        const codeMatch = (u.code || '').toLowerCase().includes(q);
        const deptMatch = (u.department || '').toLowerCase().includes(q);
        const phoneMatch = (u.phone || '').includes(q);
        return nameMatch || codeMatch || deptMatch || phoneMatch;
    });

    if (filtered.length === 0) {
        html += `<div class="p-3 text-center text-xs text-slate-400">Không tìm thấy giáo viên nào khớp với "${query}"</div>`;
    } else {
        html += filtered.map(u => {
            const initials = u.fullname.split(' ').map(w => w[0]).slice(-2).join('').toUpperCase();
            const displayText = `[${u.code}] ${u.fullname} - ${u.department}${u.phone ? ` (${u.phone})` : ''}`;
            const escapedName = u.fullname.replace(/'/g, "\\'");
            const escapedDisplay = displayText.replace(/'/g, "\\'");

            return `
                <div onclick="selectAssignedUser('${escapedName}', '${escapedDisplay}')" 
                     class="px-3 py-2 hover:bg-blue-50 cursor-pointer flex items-center justify-between text-xs transition">
                    <div class="flex items-center space-x-2.5">
                        <div class="w-7 h-7 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center text-[10px] shrink-0">
                            ${initials}
                        </div>
                        <div>
                            <div class="flex items-center space-x-1.5">
                                <span class="font-bold text-slate-900">${u.fullname}</span>
                                <span class="px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-slate-100 text-blue-700 border border-slate-200">${u.code}</span>
                            </div>
                            <p class="text-[11px] text-slate-500">${u.department} ${u.phone ? `&bull; 📞 ${u.phone}` : ''}</p>
                        </div>
                    </div>
                    <span class="text-[10px] text-blue-600 font-semibold">Chọn</span>
                </div>
            `;
        }).join('');
    }

    dropdown.innerHTML = html;
}

function selectAssignedUser(fullname, displayText) {
    const hidden = document.getElementById('deviceAssignedUser');
    const search = document.getElementById('deviceAssignedUserSearch');
    const clearBtn = document.getElementById('deviceAssignedUserClear');

    if (hidden) hidden.value = fullname || '';
    if (search) search.value = fullname ? displayText : '';
    if (clearBtn) clearBtn.classList.toggle('hidden', !fullname);
    closeAssignedUserDropdown();
}

function clearAssignedUserCombobox() {
    selectAssignedUser('', '');
    const search = document.getElementById('deviceAssignedUserSearch');
    if (search) search.focus();
}

function setAssignedUserCombobox(fullname) {
    if (!fullname) {
        selectAssignedUser('', '');
        return;
    }
    const u = (state.users || []).find(x => x.fullname === fullname);
    if (u) {
        selectAssignedUser(u.fullname, `[${u.code}] ${u.fullname} - ${u.department}${u.phone ? ` (${u.phone})` : ''}`);
    } else {
        selectAssignedUser(fullname, fullname);
    }
}

// Searchable Combobox for Borrow User
function openBorrowUserDropdown() {
    const q = document.getElementById('borrowUserCodeSearch')?.value || '';
    searchBorrowUsers(q);
    document.getElementById('borrowUserCodeDropdown')?.classList.remove('hidden');
}

function closeBorrowUserDropdown() {
    document.getElementById('borrowUserCodeDropdown')?.classList.add('hidden');
}

function searchBorrowUsers(query) {
    const dropdown = document.getElementById('borrowUserCodeDropdown');
    if (!dropdown) return;
    dropdown.classList.remove('hidden');

    const q = (query || '').trim().toLowerCase();
    const clearBtn = document.getElementById('borrowUserCodeClear');
    if (clearBtn) {
        clearBtn.classList.toggle('hidden', !q);
    }

    const filtered = (state.users || []).filter(u => {
        if (!q) return true;
        const nameMatch = (u.fullname || '').toLowerCase().includes(q);
        const codeMatch = (u.code || '').toLowerCase().includes(q);
        const deptMatch = (u.department || '').toLowerCase().includes(q);
        const phoneMatch = (u.phone || '').includes(q);
        return nameMatch || codeMatch || deptMatch || phoneMatch;
    });

    let html = '';
    if (filtered.length === 0) {
        html = `<div class="p-3 text-center text-xs text-slate-400">Không tìm thấy giáo viên nào khớp với "${query}"</div>`;
    } else {
        html = filtered.map(u => {
            const initials = u.fullname.split(' ').map(w => w[0]).slice(-2).join('').toUpperCase();
            const displayText = `[${u.code}] ${u.fullname} - ${u.department}${u.phone ? ` (${u.phone})` : ''}`;
            const escapedCode = u.code.replace(/'/g, "\\'");
            const escapedDisplay = displayText.replace(/'/g, "\\'");

            return `
                <div onclick="selectBorrowUser('${escapedCode}', '${escapedDisplay}')" 
                     class="px-3 py-2 hover:bg-emerald-50 cursor-pointer flex items-center justify-between text-xs transition">
                    <div class="flex items-center space-x-2.5">
                        <div class="w-7 h-7 rounded-full bg-emerald-100 text-emerald-800 font-bold flex items-center justify-center text-[10px] shrink-0">
                            ${initials}
                        </div>
                        <div>
                            <div class="flex items-center space-x-1.5">
                                <span class="font-bold text-slate-900">${u.fullname}</span>
                                <span class="px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">${u.code}</span>
                            </div>
                            <p class="text-[11px] text-slate-500">${u.department} ${u.phone ? `&bull; 📞 ${u.phone}` : ''}</p>
                        </div>
                    </div>
                    <span class="text-[10px] text-emerald-700 font-semibold">Chọn</span>
                </div>
            `;
        }).join('');
    }

    dropdown.innerHTML = html;
}

function selectBorrowUser(userCode, displayText) {
    const hidden = document.getElementById('borrowUserCode');
    const search = document.getElementById('borrowUserCodeSearch');
    const clearBtn = document.getElementById('borrowUserCodeClear');

    if (hidden) hidden.value = userCode || '';
    if (search) search.value = userCode ? displayText : '';
    if (clearBtn) clearBtn.classList.toggle('hidden', !userCode);
    closeBorrowUserDropdown();
}

function clearBorrowUserCombobox() {
    selectBorrowUser('', '');
    const search = document.getElementById('borrowUserCodeSearch');
    if (search) search.focus();
}

function setBorrowUserCombobox(userCode) {
    if (!userCode) {
        selectBorrowUser('', '');
        return;
    }
    const u = (state.users || []).find(x => x.code === userCode);
    if (u) {
        selectBorrowUser(u.code, `[${u.code}] ${u.fullname} - ${u.department}${u.phone ? ` (${u.phone})` : ''}`);
    } else {
        selectBorrowUser(userCode, userCode);
    }
}

// Đóng dropdown khi click ra ngoài
document.addEventListener('click', (e) => {
    if (!e.target.closest('#deviceAssignedUserSearch') && !e.target.closest('#deviceAssignedUserDropdown')) {
        closeAssignedUserDropdown();
    }
    if (!e.target.closest('#borrowUserCodeSearch') && !e.target.closest('#borrowUserCodeDropdown')) {
        closeBorrowUserDropdown();
    }
});

// Khi người dùng đổi Tầng trong bộ lọc bảng thiết bị
function onFloorFilterChange(floor) {
    updateLocationFilterByFloor(floor);
}

// Hàm render các options phòng học có phân nhóm theo loại phòng / tầng
function renderLocationOptions(locations, groupByFloor = false) {
    if (!locations || locations.length === 0) {
        return '<option value="" disabled>Không tìm thấy phòng nào</option>';
    }

    if (groupByFloor) {
        const floors = ['Tầng 1', 'Tầng 2', 'Tầng 3', 'Tầng 4', 'Tầng 5', 'Tầng 6'];
        let html = '';
        floors.forEach(f => {
            const locsInFloor = locations.filter(l => l.floor === f);
            if (locsInFloor.length > 0) {
                html += `<optgroup label="🏢 ${f} (${locsInFloor.length} phòng / vị trí)">`;
                locsInFloor.forEach(l => {
                    html += `<option value="${l.name}">${l.name}</option>`;
                });
                html += `</optgroup>`;
            }
        });
        return html;
    }

    // Phân nhóm theo Loại vị trí (Lớp học, Phòng chức năng, Văn phòng, Kho/Kỹ thuật, Sân bãi...)
    const typeOrder = [
        'Phòng học & Lớp học',
        'Phòng chức năng & Bộ môn',
        'Văn phòng & Khối làm việc',
        'Kho & Kỹ thuật',
        'Khuôn viên, Sân bãi & Tiện ích',
        'Tiện ích & Phụ trợ'
    ];
    const typeLabels = {
        'Phòng học & Lớp học': '🏫 Lớp học & Phòng học văn hóa',
        'Phòng chức năng & Bộ môn': '🔬 Phòng chức năng & Bộ môn chuyên đề',
        'Văn phòng & Khối làm việc': '🏢 Văn phòng & Khối làm việc BGH / HĐQT',
        'Kho & Kỹ thuật': '📦 Kho thiết bị & Hạ tầng kỹ thuật',
        'Khuôn viên, Sân bãi & Tiện ích': '🌳 Khuôn viên, Sân bãi & Thể thao',
        'Tiện ích & Phụ trợ': '🚪 Tiện ích, Sảnh, Hành lang & Vệ sinh'
    };

    const grouped = {};
    locations.forEach(l => {
        const t = l.type || 'Tiện ích & Phụ trợ';
        if (!grouped[t]) grouped[t] = [];
        grouped[t].push(l);
    });

    let html = '';
    typeOrder.forEach(t => {
        if (grouped[t] && grouped[t].length > 0) {
            const label = typeLabels[t] || t;
            html += `<optgroup label="${label} (${grouped[t].length})">`;
            grouped[t].forEach(l => {
                html += `<option value="${l.name}">${l.name}</option>`;
            });
            html += `</optgroup>`;
        }
    });

    Object.keys(grouped).forEach(t => {
        if (!typeOrder.includes(t) && grouped[t].length > 0) {
            html += `<optgroup label="Khác - ${t} (${grouped[t].length})">`;
            grouped[t].forEach(l => {
                html += `<option value="${l.name}">${l.name}</option>`;
            });
            html += `</optgroup>`;
        }
    });

    return html;
}

// Quy chuẩn tiền tố theo danh mục thiết bị Sigma
function getCategoryPrefix(categoryName) {
    if (!categoryName) return 'TB';
    const c = categoryName.toLowerCase();
    if (c.includes('màn hình')) return 'M';
    if (c.includes('máy tính bàn') || c.includes('case')) return 'PC';
    if (c.includes('mạng') || c.includes('router') || c.includes('switch')) return 'ROUTER';
    if (c.includes('unifi') || c.includes('wifi')) return 'WF';
    if (c.includes('laptop')) return 'LT';
    if (c.includes('in') || c.includes('photo')) return 'PRN';
    if (c.includes('chiếu')) return 'MC';
    if (c.includes('camera')) return 'CAM';
    if (c.includes('âm thanh')) return 'AT';
    if (c.includes('chấm công') || c.includes('thẻ')) return 'CC';
    if (c.includes('server') || c.includes('máy chủ')) return 'SRV';
    if (c.includes('suất ăn')) return 'SA';
    return 'TB';
}

// Cập nhật gợi ý mã thiết bị theo định dạng Sigma-[LOẠI]-[SEQ:03d]
async function updateSuggestedCode() {
    const deviceId = document.getElementById('deviceId')?.value;
    if (deviceId) return; // Nếu đang chỉnh sửa thiết bị thì giữ nguyên mã

    const catSelect = document.getElementById('deviceCategory');
    const category = catSelect ? catSelect.value : '';
    const prefix = getCategoryPrefix(category);

    try {
        const res = await fetch(`/api/devices/suggest-code?category=${encodeURIComponent(category)}`);
        if (res.ok) {
            const data = await res.json();
            const devCodeInput = document.getElementById('deviceCode');
            if (devCodeInput && data.suggested_code) {
                devCodeInput.value = data.suggested_code;
                return;
            }
        }
    } catch (err) {
        console.warn('Lỗi gọi API suggest-code, tự động tính fallback:', err);
    }

    // Fallback nếu API không khả dụng
    let maxNum = 0;
    const regex = new RegExp(`^Sigma-${prefix}-(\\d+)$`, 'i');
    (state.devices || []).forEach(d => {
        if (d.code) {
            const m = d.code.match(regex);
            if (m) {
                const n = parseInt(m[1], 10);
                if (n > maxNum) maxNum = n;
            }
        }
    });
    const devCodeInput = document.getElementById('deviceCode');
    if (devCodeInput) {
        devCodeInput.value = `Sigma-${prefix}-${String(maxNum + 1).padStart(3, '0')}`;
    }
}

function updateLocationFilterByFloor(floor) {
    const devLocFilter = document.getElementById('deviceLocationFilter');
    if (!devLocFilter) return;

    let filtered = state.locations || [];
    if (floor && floor !== 'all') {
        filtered = filtered.filter(l => l.floor === floor);
    }

    // Sắp xếp theo code cho dễ tìm
    filtered = [...filtered].sort((a, b) => (a.code || '').localeCompare(b.code || '', 'vi'));

    devLocFilter.innerHTML = '<option value="all">Tất cả vị trí / phòng</option>' +
        renderLocationOptions(filtered, floor === 'all');
}

// Khi người dùng chọn Tầng trong modal Thêm/Sửa hoặc Di chuyển
function onModalFloorChange(floor, targetSelectId, selectedValue = '') {
    const targetSelect = document.getElementById(targetSelectId);
    if (!targetSelect) return;

    let filtered = state.locations || [];
    if (floor && floor !== 'all') {
        filtered = filtered.filter(l => l.floor === floor);
    }

    // Sắp xếp theo code cho dễ tìm
    filtered = [...filtered].sort((a, b) => (a.code || '').localeCompare(b.code || '', 'vi'));

    targetSelect.innerHTML = '<option value="">-- Chọn phòng học / vị trí cụ thể --</option>' +
        renderLocationOptions(filtered, floor === 'all');

    if (selectedValue) {
        targetSelect.value = selectedValue;
    }

    // Nếu là modal Thêm thiết bị mới, tự động cập nhật gợi ý mã thiết bị theo tầng
    if (targetSelectId === 'deviceLocation') {
        updateSuggestedCode();
    }
}

// Khi người dùng chọn thiết bị từ danh sách gợi ý 2022
function handleStandardDeviceSelect(devName) {
    if (!devName || !state.standardDevices) return;
    const found = state.standardDevices.find(d => d.name === devName);
    if (found) {
        const catSelect = document.getElementById('deviceCategory');
        if (catSelect && found.category) {
            // Find best matching category
            const match = state.categories.find(c => c.name.toLowerCase().includes(found.category.toLowerCase()));
            if (match) {
                catSelect.value = match.name;
                updateSuggestedCode();
            }
        }

        const specInput = document.getElementById('deviceSpec');
        if (specInput && (found.model || found.spec || found.mfg)) {
            let specStr = [];
            if (found.model) specStr.push(`Model: ${found.model}`);
            if (found.spec) specStr.push(`Cấu hình: ${found.spec}`);
            if (found.mfg) specStr.push(`Hãng: ${found.mfg}`);
            specInput.value = specStr.join(' | ');
        }

        const supplierInput = document.getElementById('deviceSupplier');
        if (supplierInput && found.mfg) {
            supplierInput.value = found.mfg;
        }
    }
}

// Chuyển đổi tab
async function switchTab(tabName) {
    currentTab = tabName;
    document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active', 'text-blue-600', 'bg-blue-50/80');
            btn.classList.remove('text-slate-600', 'hover:bg-slate-100');
        } else {
            btn.classList.remove('active', 'text-blue-600', 'bg-blue-50/80');
            btn.classList.add('text-slate-600', 'hover:bg-slate-100');
        }
    });

    document.querySelectorAll('.tab-content').forEach(sec => sec.classList.add('hidden'));
    const targetSection = document.getElementById(`tab-${tabName}`);
    if (targetSection) targetSection.classList.remove('hidden');

    if (tabName === 'dashboard') await loadDashboard();
    else if (tabName === 'devices') await loadDevices();
    else if (tabName === 'movements') {
        await loadMovements();
        populateMovementDeviceSelect();
    }
    else if (tabName === 'borrow') await loadBorrowRequests();
    else if (tabName === 'users_rooms') {
        await loadUsers();
        await loadLocations();
    }
    else if (tabName === 'reports') await loadReports();
    else if (tabName === 'settings') await loadLogs();

    lucide.createIcons();
}

// Cập nhật giao diện theo trạng thái người dùng (Admin vs Guest)
function updateAuthUI() {
    const isGuest = state.currentUser.role === 'guest';
    const isAdmin = state.currentUser.role === 'admin';

    // Cập nhật thông tin Header
    const nameEl = document.getElementById('currentUserName');
    if (nameEl) nameEl.innerText = state.currentUser.fullname || state.currentUser.username;

    const descEl = document.getElementById('currentUserRoleDesc');
    if (descEl) descEl.innerText = isAdmin ? 'Toàn quyền hệ thống' : 'Khách vãng lai (Chỉ xem)';

    const badgeEl = document.getElementById('currentUserBadge');
    if (badgeEl) {
        if (isAdmin) {
            badgeEl.innerText = 'ADMIN';
            badgeEl.className = 'text-[10px] px-1.5 py-0.5 rounded-full font-bold bg-indigo-100 text-indigo-800 border border-indigo-200';
        } else {
            badgeEl.innerText = 'GUEST';
            badgeEl.className = 'text-[10px] px-1.5 py-0.5 rounded-full font-bold bg-amber-100 text-amber-800 border border-amber-200';
        }
    }

    const avatarEl = document.getElementById('userAvatar');
    if (avatarEl) {
        if (isAdmin) {
            avatarEl.innerText = 'AD';
            avatarEl.className = 'w-8 h-8 rounded-full bg-indigo-700 text-white flex items-center justify-center font-bold text-xs shadow-sm';
        } else {
            avatarEl.innerText = 'GS';
            avatarEl.className = 'w-8 h-8 rounded-full bg-amber-600 text-white flex items-center justify-center font-bold text-xs shadow-sm';
        }
    }

    const btnAuthText = document.getElementById('btnAuthText');
    if (btnAuthText) {
        btnAuthText.innerText = isAdmin ? 'Đổi TK' : 'Đăng nhập';
    }

    const btnAuthSwitch = document.getElementById('btnAuthSwitch');
    if (btnAuthSwitch) {
        if (isAdmin) {
            btnAuthSwitch.className = 'px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition flex items-center';
            btnAuthSwitch.title = 'Đổi tài khoản đăng nhập';
        } else {
            btnAuthSwitch.className = 'px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition flex items-center';
            btnAuthSwitch.title = 'Đăng nhập với tư cách Quản trị viên';
        }
    }

    const btnLogout = document.getElementById('btnLogout');
    if (btnLogout) {
        if (isAdmin) {
            btnLogout.classList.remove('hidden');
        } else {
            btnLogout.classList.add('hidden');
        }
    }

    // Hiển thị / ẩn banner thông báo chế độ Khách
    const guestBanner = document.getElementById('guestRoleBanner');
    if (guestBanner) {
        if (isGuest) {
            guestBanner.classList.remove('hidden');
        } else {
            guestBanner.classList.add('hidden');
        }
    }

    // Ẩn / hiện các nút thao tác Admin
    document.querySelectorAll('.admin-action, .admin-only').forEach(el => {
        if (isGuest) {
            el.classList.add('hidden');
        } else {
            el.classList.remove('hidden');
        }
    });

    // Disable nút di chuyển thiết bị nếu là guest
    const moveSubmitBtn = document.querySelector('#moveDeviceForm button[type="submit"]');
    if (moveSubmitBtn) {
        if (isGuest) {
            moveSubmitBtn.disabled = true;
            moveSubmitBtn.classList.add('opacity-50', 'cursor-not-allowed');
            moveSubmitBtn.title = 'Chỉ Admin mới có quyền điều chuyển thiết bị';
        } else {
            moveSubmitBtn.disabled = false;
            moveSubmitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            moveSubmitBtn.title = '';
        }
    }

    // Cập nhật người di chuyển mặc định
    const movedByInput = document.getElementById('movedByInput');
    if (movedByInput) {
        movedByInput.value = state.currentUser.fullname || 'Quản trị viên';
    }

    lucide.createIcons();
}

function openAuthModal(tab = 'login') {
    switchAuthTab(tab);
    openModal('authModal');
}

function switchAuthTab(tab) {
    const btnLogin = document.getElementById('tabBtnLogin');
    const btnRegister = document.getElementById('tabBtnRegister');
    const formLogin = document.getElementById('loginForm');
    const formRegister = document.getElementById('registerForm');

    if (tab === 'login') {
        if (btnLogin) btnLogin.className = 'px-3.5 py-1.5 text-xs font-bold rounded-lg bg-blue-600 text-white shadow-sm transition';
        if (btnRegister) btnRegister.className = 'px-3.5 py-1.5 text-xs font-bold rounded-lg text-slate-600 hover:text-slate-900 transition';
        if (formLogin) formLogin.classList.remove('hidden');
        if (formRegister) formRegister.classList.add('hidden');
    } else {
        if (btnRegister) btnRegister.className = 'px-3.5 py-1.5 text-xs font-bold rounded-lg bg-emerald-600 text-white shadow-sm transition';
        if (btnLogin) btnLogin.className = 'px-3.5 py-1.5 text-xs font-bold rounded-lg text-slate-600 hover:text-slate-900 transition';
        if (formRegister) formRegister.classList.remove('hidden');
        if (formLogin) formLogin.classList.add('hidden');
    }
    lucide.createIcons();
}

function togglePasswordVisibility(inputId, iconId) {
    const input = document.getElementById(inputId);
    const icon = document.getElementById(iconId);
    if (!input) return;
    if (input.type === 'password') {
        input.type = 'text';
        if (icon) icon.setAttribute('data-lucide', 'eye-off');
    } else {
        input.type = 'password';
        if (icon) icon.setAttribute('data-lucide', 'eye');
    }
    lucide.createIcons();
}

async function handleAuthLogin(event) {
    event.preventDefault();
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;

    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (!res.ok) {
            Swal.fire({ icon: 'error', title: 'Đăng nhập thất bại', text: data.error });
            return;
        }

        state.currentUser = data.account;
        closeModal('authModal');
        updateAuthUI();

        Swal.fire({
            icon: 'success',
            title: `Xin chào, ${data.account.fullname}!`,
            text: `Bạn đã đăng nhập với vai trò: ${data.account.role.toUpperCase()}`,
            timer: 2000,
            showConfirmButton: false
        });

        // Tải lại các bảng để cập nhật các nút thao tác tương ứng quyền
        await loadDevices();
        if (currentTab === 'users_rooms') {
            await loadLocations();
            await loadUsers();
        } else if (currentTab === 'borrow') {
            await loadBorrowRequests();
        }
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Lỗi kết nối', text: err.message });
    }
}

async function handleAuthRegister(event) {
    event.preventDefault();
    const fullname = document.getElementById('regFullname').value.trim();
    const username = document.getElementById('regUsername').value.trim();
    const password = document.getElementById('regPassword').value;
    const confirm = document.getElementById('regPasswordConfirm').value;
    const email = document.getElementById('regEmail').value.trim();
    const phone = document.getElementById('regPhone').value.trim();

    if (password !== confirm) {
        Swal.fire({ icon: 'warning', title: 'Mật khẩu không khớp', text: 'Vui lòng kiểm tra lại mật khẩu xác nhận!' });
        return;
    }

    try {
        const res = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fullname, username, password, email, phone })
        });
        const data = await res.json();
        if (!res.ok) {
            Swal.fire({ icon: 'error', title: 'Đăng ký thất bại', text: data.error });
            return;
        }

        state.currentUser = data.account;
        closeModal('authModal');
        updateAuthUI();

        Swal.fire({
            icon: 'success',
            title: 'Đăng ký thành công!',
            text: 'Tài khoản của bạn đã được tạo với vai trò Khách (Guest - Chỉ xem).',
            timer: 3000,
            showConfirmButton: false
        });

        await loadDevices();
        if (currentTab === 'users_rooms') {
            await loadLocations();
            await loadUsers();
        }
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Lỗi', text: err.message });
    }
}

async function handleLogout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
        state.currentUser = {
            id: 0,
            username: 'guest',
            fullname: 'Khách vãng lai',
            role: 'guest',
            is_authenticated: false
        };
        updateAuthUI();
        Swal.fire({
            toast: true,
            position: 'top-end',
            icon: 'info',
            title: 'Đã chuyển về quyền Khách (Chỉ xem)',
            showConfirmButton: false,
            timer: 2000
        });
        await loadDevices();
        if (currentTab === 'users_rooms') {
            await loadLocations();
            await loadUsers();
        } else if (currentTab === 'borrow') {
            await loadBorrowRequests();
        }
    } catch (err) {
        console.error('Lỗi đăng xuất:', err);
    }
}

// ==================== DASHBOARD ====================
async function loadDashboard() {
    try {
        const res = await fetch('/api/stats');
        const stats = await res.json();
        state.stats = stats;

        // KPI
        document.getElementById('statTotalDevices').innerText = stats.total_devices;
        document.getElementById('statTotalValue').innerText = 'Tổng giá trị: ' + formatCurrency(stats.total_value);
        document.getElementById('statReadyDevices').innerText = stats.status_counts.ready;
        document.getElementById('statBorrowedDevices').innerText = stats.status_counts.borrowed;
        document.getElementById('statBrokenDevices').innerText = stats.status_counts.broken + stats.status_counts.maintenance;
        document.getElementById('statOverdueCount').innerText = `${stats.overdue_count} phiếu quá hạn`;

        // Borrow badge
        const badge = document.getElementById('borrowBadge');
        if (stats.overdue_count > 0) {
            badge.innerText = `${stats.overdue_count} quá hạn`;
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }

        // Overdue Alert Banner
        const banner = document.getElementById('overdueAlertBanner');
        if (stats.overdue_count > 0) {
            banner.classList.remove('hidden');
            document.getElementById('overdueAlertText').innerText = `Cảnh báo: Có ${stats.overdue_count} thiết bị đang mượn đã QUÁ HẠN hoàn trả!`;
        } else {
            banner.classList.add('hidden');
        }

        // Overdue Table in Dashboard
        const overdueTable = document.getElementById('overdueSummaryTable');
        if (stats.overdue_list && stats.overdue_list.length > 0) {
            overdueTable.innerHTML = stats.overdue_list.map(b => `
                <tr class="hover:bg-red-50/50">
                    <td class="py-2.5 font-medium text-slate-800">${b.user_name} <span class="text-slate-400">(${b.department})</span></td>
                    <td class="py-2.5 font-bold text-slate-900">${b.device_code} - ${b.device_name}</td>
                    <td class="py-2.5 text-slate-600">${formatDate(b.expected_return_date)}</td>
                    <td class="py-2.5 text-right font-bold text-red-600">Quá ${b.overdue_days} ngày</td>
                </tr>
            `).join('');
        } else {
            overdueTable.innerHTML = '<tr><td colspan="4" class="py-4 text-center text-slate-400">Không có phiếu mượn nào quá hạn 🎉</td></tr>';
        }

        // Top Devices Table
        const topTable = document.getElementById('topDevicesTable');
        if (stats.top_devices && stats.top_devices.length > 0) {
            topTable.innerHTML = stats.top_devices.map(d => `
                <tr class="hover:bg-slate-50">
                    <td class="py-2.5 font-semibold text-blue-600">${d.device_code}</td>
                    <td class="py-2.5 text-slate-800">${d.device_name}</td>
                    <td class="py-2.5 text-right font-bold text-slate-900">${d.borrow_count} lần</td>
                </tr>
            `).join('');
        } else {
            topTable.innerHTML = '<tr><td colspan="3" class="py-4 text-center text-slate-400">Chưa có dữ liệu mượn</td></tr>';
        }

        // Render Charts
        renderCategoryChart(stats.category_counts);
        renderLocationChart(stats.location_counts);

    } catch (err) {
        console.error('Lỗi tải Dashboard:', err);
    }
}

function renderCategoryChart(data) {
    const ctx = document.getElementById('categoryChart').getContext('2d');
    if (categoryChartInstance) categoryChartInstance.destroy();

    const labels = data.map(d => d.category);
    const counts = data.map(d => d.count);
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#64748b'];

    categoryChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { boxWidth: 10, font: { size: 11 } }
                }
            },
            cutout: '65%'
        }
    });
}

function renderLocationChart(data) {
    const ctx = document.getElementById('locationChart').getContext('2d');
    if (locationChartInstance) locationChartInstance.destroy();

    const labels = data.map(d => d.location);
    const counts = data.map(d => d.count);

    locationChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Số lượng thiết bị',
                data: counts,
                backgroundColor: '#3b82f6',
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 }
                },
                x: {
                    ticks: {
                        font: { size: 10 },
                        maxRotation: 30,
                        minRotation: 15
                    }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

// ==================== DEVICES TAB ====================
function clearDeviceSearch() {
    const s = document.getElementById('deviceSearchInput');
    if (s) s.value = '';
    loadDevices();
}

function resetDeviceFilters() {
    const s = document.getElementById('deviceSearchInput');
    if (s) s.value = '';
    const cat = document.getElementById('deviceCategoryFilter');
    if (cat) cat.value = 'all';
    const st = document.getElementById('deviceStatusFilter');
    if (st) st.value = 'all';
    const fl = document.getElementById('deviceFloorFilter');
    if (fl) fl.value = 'all';
    updateLocationFilterByFloor('all');
    const loc = document.getElementById('deviceLocationFilter');
    if (loc) loc.value = 'all';
    loadDevices();
}

async function loadDevices() {
    try {
        const search = document.getElementById('deviceSearchInput')?.value || '';
        const category = document.getElementById('deviceCategoryFilter')?.value || 'all';
        const status = document.getElementById('deviceStatusFilter')?.value || 'all';
        const floor = document.getElementById('deviceFloorFilter')?.value || 'all';
        const location = document.getElementById('deviceLocationFilter')?.value || 'all';

        const params = new URLSearchParams({ search, category, status, floor, location });
        const res = await fetch(`/api/devices?${params.toString()}`);
        const devices = await res.json();
        state.devices = devices;

        const countSummary = document.getElementById('deviceCountSummary');
        if (countSummary) countSummary.innerText = `${devices.length} thiết bị`;
        const countText = document.getElementById('devicesCountText');
        if (countText) countText.innerText = devices.length;

        const clearBtn = document.getElementById('deviceSearchClear');
        if (clearBtn) clearBtn.classList.toggle('hidden', !search);

        const tbody = document.getElementById('devicesTableBody');

        if (devices.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="py-8 text-center text-slate-400">Không tìm thấy thiết bị nào phù hợp với bộ lọc.</td></tr>`;
            return;
        }

        tbody.innerHTML = devices.map(d => {
            const statusBadgeClass = getStatusBadgeClass(d.status);
            return `
                <tr class="hover:bg-slate-50 transition border-b border-slate-100">
                    <td class="px-4 py-3 font-semibold text-blue-600 whitespace-nowrap">
                        <button onclick="viewDeviceDetail(${d.id})" class="hover:underline flex items-center">
                            ${d.code}
                        </button>
                    </td>
                    <td class="px-4 py-3 font-medium text-slate-900 min-w-[200px]">
                        <div>${d.name}</div>
                        ${d.specification ? `<span class="block text-xs text-slate-400 truncate max-w-xs">${d.specification}</span>` : ''}
                    </td>
                    <td class="px-4 py-3 text-slate-600 text-xs whitespace-nowrap">${d.category}</td>
                    <td class="px-4 py-3 whitespace-nowrap">
                        <span class="inline-flex items-center text-xs font-medium text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-lg border border-indigo-100 whitespace-nowrap">
                            <i data-lucide="map-pin" class="w-3.5 h-3.5 mr-1 text-indigo-500 shrink-0"></i> ${d.current_location}
                        </span>
                    </td>
                    <td class="px-4 py-3 text-xs text-slate-700 whitespace-nowrap">
                        ${d.assigned_user ? `
                            <span class="inline-flex items-center font-medium text-slate-800 bg-slate-100 px-2.5 py-1 rounded-lg whitespace-nowrap">
                                <i data-lucide="user" class="w-3.5 h-3.5 mr-1 text-blue-600 shrink-0"></i> ${d.assigned_user}
                            </span>
                        ` : `<span class="text-slate-400 italic">Dùng chung</span>`}
                    </td>
                    <td class="px-4 py-3 whitespace-nowrap">
                        <span class="text-xs px-2.5 py-1 rounded-full font-medium whitespace-nowrap inline-flex items-center ${statusBadgeClass}">
                            <span class="w-1.5 h-1.5 rounded-full mr-1.5 shrink-0 ${getStatusDotColor(d.status)}"></span>
                            ${d.status}
                        </span>
                    </td>
                    <td class="px-4 py-3 text-right font-medium text-slate-700 whitespace-nowrap">
                        ${formatCurrency(d.price)}
                    </td>
                    <td class="px-4 py-3 text-center whitespace-nowrap">
                        <div class="flex items-center justify-center space-x-1">
                            <button onclick="viewDeviceDetail(${d.id})" title="Xem chi tiết & lịch sử" class="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition">
                                <i data-lucide="eye" class="w-4 h-4"></i>
                            </button>
                            ${state.currentUser.role === 'admin' ? `
                                <button onclick="quickMoveDevice('${d.code}')" title="Di chuyển vị trí phòng" class="p-1.5 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition">
                                    <i data-lucide="truck" class="w-4 h-4"></i>
                                </button>
                                <button onclick="openChangeCategoryModal(${d.id})" title="Di chuyển phân loại thiết bị" class="p-1.5 text-slate-500 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition">
                                    <i data-lucide="tag" class="w-4 h-4"></i>
                                </button>
                                <button onclick="openEditDeviceModal(${d.id})" title="Chỉnh sửa trực tiếp tất cả thông tin" class="p-1.5 text-slate-500 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition">
                                    <i data-lucide="pencil" class="w-4 h-4"></i>
                                </button>
                                <button onclick="handleDeleteDevice(${d.id}, '${d.code}')" title="Xóa thiết bị" class="p-1.5 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition">
                                    <i data-lucide="trash-2" class="w-4 h-4"></i>
                                </button>
                            ` : `
                                <span class="text-[11px] text-slate-400 italic">Chỉ xem</span>
                            `}
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

        lucide.createIcons();
    } catch (err) {
        console.error('Lỗi tải danh sách thiết bị:', err);
    }
}

function getStatusDotColor(status) {
    switch (status) {
        case 'Sẵn sàng': return 'bg-emerald-500';
        case 'Đang sử dụng': return 'bg-sky-500';
        case 'Đang mượn': return 'bg-amber-500';
        case 'Hỏng': return 'bg-red-500';
        case 'Bảo trì': return 'bg-orange-500';
        case 'Chờ duyệt': return 'bg-yellow-500';
        case 'Đã trả': return 'bg-emerald-500';
        default: return 'bg-slate-400';
    }
}

function getStatusBadgeClass(status) {
    switch (status) {
        case 'Sẵn sàng': return 'badge-ready';
        case 'Đang sử dụng': return 'badge-in_use';
        case 'Đang mượn': return 'badge-borrowed';
        case 'Hỏng': return 'badge-broken';
        case 'Bảo trì': return 'badge-maintenance';
        case 'Chờ duyệt': return 'badge-pending';
        case 'Đã trả': return 'badge-ready';
        default: return 'badge-disposed';
    }
}

// Modal Thêm / Sửa Thiết bị
function openAddDeviceModal() {
    document.getElementById('deviceForm').reset();
    document.getElementById('deviceId').value = '';
    document.getElementById('deviceModalTitle').innerText = 'Thêm thiết bị mới (Thủ công)';
    document.getElementById('deviceCode').removeAttribute('readonly');
    document.getElementById('devicePurchaseDate').value = new Date().toISOString().split('T')[0];
    document.getElementById('deviceStatus').value = 'Đang sử dụng';

    // Khởi tạo Tầng 1 và lọc danh sách phòng tương ứng
    const floorSelect = document.getElementById('deviceFloor');
    if (floorSelect) {
        floorSelect.value = 'Tầng 1';
        onModalFloorChange('Tầng 1', 'deviceLocation');
    }

    setAssignedUserCombobox('');

    // Gợi ý mã thiết bị tự động chuẩn Sigma
    updateSuggestedCode();

    openModal('deviceModal');
}

function openEditDeviceModal(id) {
    const d = state.devices.find(item => item.id === id);
    if (!d) return;

    document.getElementById('deviceId').value = d.id;
    document.getElementById('deviceModalTitle').innerText = `Sửa thông tin thiết bị: ${d.code}`;
    document.getElementById('deviceCode').value = d.code;
    document.getElementById('deviceName').value = d.name;
    document.getElementById('deviceCategory').value = d.category;

    // Nhận diện tầng của thiết bị này
    const matchedLoc = state.locations.find(l => l.name === d.current_location);
    const floor = matchedLoc ? matchedLoc.floor : 'all';
    const floorSelect = document.getElementById('deviceFloor');
    if (floorSelect) {
        floorSelect.value = floor;
        onModalFloorChange(floor, 'deviceLocation', d.current_location);
    } else {
        document.getElementById('deviceLocation').value = d.current_location;
    }

    setAssignedUserCombobox(d.assigned_user || '');

    document.getElementById('deviceStatus').value = d.status;
    document.getElementById('devicePrice').value = d.price;
    document.getElementById('devicePurchaseDate').value = d.purchase_date || '';
    document.getElementById('deviceSupplier').value = d.supplier || '';
    document.getElementById('deviceSpec').value = d.specification || '';
    document.getElementById('deviceNotes').value = d.notes || '';

    openModal('deviceModal');
}

async function handleDeviceSubmit(event) {
    event.preventDefault();
    const id = document.getElementById('deviceId').value;
    const payload = {
        code: document.getElementById('deviceCode').value.trim().toUpperCase(),
        name: document.getElementById('deviceName').value.trim(),
        category: document.getElementById('deviceCategory').value,
        current_location: document.getElementById('deviceLocation').value,
        assigned_user: document.getElementById('deviceAssignedUser')?.value.trim() || null,
        status: document.getElementById('deviceStatus').value,
        price: document.getElementById('devicePrice').value,
        purchase_date: document.getElementById('devicePurchaseDate').value,
        supplier: document.getElementById('deviceSupplier').value.trim(),
        specification: document.getElementById('deviceSpec').value.trim(),
        notes: document.getElementById('deviceNotes').value.trim()
    };

    const isEdit = Boolean(id);
    const url = isEdit ? `/api/devices/${id}` : '/api/devices';
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (!res.ok) {
            Swal.fire({
                icon: 'error',
                title: 'Lỗi',
                text: data.error || 'Có lỗi xảy ra khi lưu thiết bị!'
            });
            return;
        }

        closeModal('deviceModal');
        Swal.fire({
            icon: 'success',
            title: 'Thành công',
            text: data.message,
            timer: 1500,
            showConfirmButton: false
        });

        await loadDevices();
        if (currentTab === 'dashboard') await loadDashboard();
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Lỗi hệ thống', text: err.message });
    }
}

async function handleDeleteDevice(id, code) {
    const result = await Swal.fire({
        title: `Xác nhận xóa thiết bị ${code}?`,
        text: 'Hành động này sẽ xóa vĩnh viễn thiết bị khỏi danh mục!',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'Đồng ý xóa',
        cancelButtonText: 'Hủy'
    });

    if (!result.isConfirmed) return;

    try {
        const res = await fetch(`/api/devices/${id}`, { method: 'DELETE' });
        const data = await res.json();

        if (!res.ok) {
            Swal.fire({ icon: 'error', title: 'Không thể xóa', text: data.error });
            return;
        }

        Swal.fire({ icon: 'success', title: 'Đã xóa', text: data.message, timer: 1500, showConfirmButton: false });
        await loadDevices();
        if (currentTab === 'dashboard') await loadDashboard();
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Lỗi', text: err.message });
    }
}

// Xem chi tiết thiết bị & Lịch sử
async function viewDeviceDetail(id) {
    try {
        const res = await fetch(`/api/devices/${id}`);
        const d = await res.json();
        if (!res.ok) return;

        document.getElementById('detailCodeBadge').innerText = d.code;
        document.getElementById('detailNameTitle').innerText = d.name;
        document.getElementById('detailCategory').innerText = d.category;
        document.getElementById('detailLocation').innerText = d.current_location;
        const assignedEl = document.getElementById('detailAssignedUser');
        if (assignedEl) assignedEl.innerText = d.assigned_user || 'Dùng chung (chưa bàn giao)';
        document.getElementById('detailStatus').innerText = d.status;
        document.getElementById('detailPrice').innerText = formatCurrency(d.price);
        document.getElementById('detailDate').innerText = formatDate(d.purchase_date);
        document.getElementById('detailSupplier').innerText = d.supplier || 'Không có';
        document.getElementById('detailSpec').innerText = d.specification || 'Không có thông số';

        // Lịch sử di chuyển
        const moveTbody = document.getElementById('detailMovementsTable');
        if (d.movements && d.movements.length > 0) {
            moveTbody.innerHTML = d.movements.map(m => `
                <tr class="hover:bg-slate-50">
                    <td class="px-3 py-2 text-slate-500">${m.move_date}</td>
                    <td class="px-3 py-2 text-slate-600">${m.from_location}</td>
                    <td class="px-3 py-2 font-semibold text-blue-700">${m.to_location}</td>
                    <td class="px-3 py-2 text-slate-700">${m.moved_by}</td>
                    <td class="px-3 py-2 text-slate-600">${m.reason}</td>
                </tr>
            `).join('');
        } else {
            moveTbody.innerHTML = '<tr><td colspan="5" class="py-3 text-center text-slate-400">Thiết bị chưa từng di chuyển khỏi vị trí ban đầu.</td></tr>';
        }

        // Lịch sử mượn
        const borrowTbody = document.getElementById('detailBorrowsTable');
        if (d.borrows && d.borrows.length > 0) {
            borrowTbody.innerHTML = d.borrows.map(b => `
                <tr class="hover:bg-slate-50">
                    <td class="px-3 py-2 font-semibold text-blue-600">${b.request_code}</td>
                    <td class="px-3 py-2">${b.user_name} (${b.department})</td>
                    <td class="px-3 py-2 text-slate-600">${formatDate(b.borrow_date)}</td>
                    <td class="px-3 py-2 text-slate-600">${formatDate(b.expected_return_date)}</td>
                    <td class="px-3 py-2"><span class="px-2 py-0.5 rounded text-[11px] font-medium ${getStatusBadgeClass(b.status)}">${b.status}</span></td>
                </tr>
            `).join('');
        } else {
            borrowTbody.innerHTML = '<tr><td colspan="5" class="py-3 text-center text-slate-400">Chưa có lịch sử mượn trả nào.</td></tr>';
        }

        openModal('deviceDetailModal');
        lucide.createIcons();
    } catch (err) {
        console.error('Lỗi xem chi tiết:', err);
    }
}

// ==================== CSV IMPORT ====================
function openImportModal() {
    document.getElementById('importForm').reset();
    const box = document.getElementById('importResultBox');
    box.classList.add('hidden');
    box.innerHTML = '';
    openModal('importModal');
}

async function handleImportSubmit(event) {
    event.preventDefault();
    const fileInput = document.getElementById('csvFileInput');
    if (!fileInput.files.length) return;

    const btn = document.getElementById('btnDoImport');
    btn.disabled = true;
    btn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 mr-1.5 animate-spin"></i> Đang xử lý...`;
    lucide.createIcons();

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const res = await fetch('/api/devices/import-csv', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        const box = document.getElementById('importResultBox');
        box.classList.remove('hidden');

        if (!res.ok) {
            box.className = 'p-3 rounded-xl text-xs bg-red-50 text-red-700 border border-red-200';
            box.innerText = data.error || 'Có lỗi xảy ra khi nhập file CSV.';
        } else {
            let errorHtml = '';
            if (data.errors && data.errors.length > 0) {
                errorHtml = `
                    <div class="mt-2 max-h-32 overflow-y-auto border-t border-amber-200 pt-1 text-amber-900">
                        <p class="font-bold text-[11px]">Chi tiết các dòng bị bỏ qua:</p>
                        <ul class="list-disc list-inside space-y-0.5 pl-1">
                            ${data.errors.map(e => `<li>${e}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }

            box.className = 'p-3 rounded-xl text-xs bg-emerald-50 text-emerald-800 border border-emerald-200';
            box.innerHTML = `
                <p class="font-bold text-emerald-700">🎉 ${data.message}</p>
                <p>Số thiết bị thêm mới: <strong>${data.success_count}</strong></p>
                ${data.error_count > 0 ? `<p class="text-amber-700">Số dòng bị trùng/lỗi: <strong>${data.error_count}</strong></p>` : ''}
                ${errorHtml}
            `;

            await loadDevices();
            if (currentTab === 'dashboard') await loadDashboard();
        }
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Lỗi upload', text: err.message });
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="upload" class="w-4 h-4 mr-1.5"></i> Bắt đầu nhập dữ liệu`;
        lucide.createIcons();
    }
}

// ==================== DI CHUYỂN VỊ TRÍ (MOVEMENTS) ====================
function populateMovementDeviceSelect() {
    const select = document.getElementById('moveDeviceSelect');
    if (!select) return;

    select.innerHTML = '<option value="">-- Chọn thiết bị cần chuyển --</option>' +
        state.devices.map(d => `<option value="${d.code}">[${d.code}] ${d.name} (${d.current_location})</option>`).join('');

    const moveToFloor = document.getElementById('moveToFloorSelect');
    if (moveToFloor) {
        onModalFloorChange(moveToFloor.value, 'moveToLocationSelect');
    }
}

function quickMoveDevice(code) {
    switchTab('movements').then(() => {
        const select = document.getElementById('moveDeviceSelect');
        if (select) {
            select.value = code;
            handleMoveDeviceSelect(code);
        }
        const moveToFloor = document.getElementById('moveToFloorSelect');
        if (moveToFloor) {
            moveToFloor.value = 'Tầng 1';
            onModalFloorChange('Tầng 1', 'moveToLocationSelect');
        }
    });
}

function handleMoveDeviceSelect(code) {
    const dev = state.devices.find(d => d.code === code);
    const fromText = document.getElementById('moveFromLocationText');
    const fromInput = document.getElementById('moveFromLocationInput');

    if (dev) {
        fromText.innerText = dev.current_location;
        fromInput.value = dev.current_location;
    } else {
        fromText.innerText = 'Chưa chọn thiết bị';
        fromInput.value = '';
    }
}

async function handleMoveDeviceSubmit(event) {
    event.preventDefault();
    const payload = {
        device_code: document.getElementById('moveDeviceSelect').value,
        to_location: document.getElementById('moveToLocationSelect').value,
        moved_by: document.getElementById('movedByInput').value.trim() || state.currentUser.name,
        reason: document.getElementById('moveReasonInput').value.trim()
    };

    if (!payload.device_code || !payload.to_location || !payload.reason) {
        Swal.fire({ icon: 'warning', title: 'Thiếu thông tin', text: 'Vui lòng chọn thiết bị, vị trí mới và lý do di chuyển!' });
        return;
    }

    try {
        const res = await fetch('/api/devices/move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (!res.ok) {
            Swal.fire({ icon: 'error', title: 'Lỗi di chuyển', text: data.error });
            return;
        }

        Swal.fire({
            icon: 'success',
            title: 'Đã di chuyển thành công',
            text: data.message,
            timer: 2000,
            showConfirmButton: false
        });

        document.getElementById('moveReasonInput').value = '';
        await loadMovements();
        await loadDevices();
        populateMovementDeviceSelect();
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Lỗi', text: err.message });
    }
}

async function loadMovements() {
    try {
        const search = document.getElementById('movementSearchInput')?.value || '';
        const params = new URLSearchParams({ search });
        const res = await fetch(`/api/movements?${params.toString()}`);
        const movements = await res.json();
        state.movements = movements;

        const tbody = document.getElementById('movementsTableBody');
        if (movements.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="py-6 text-center text-slate-400">Không có lịch sử di chuyển nào.</td></tr>';
            return;
        }

        tbody.innerHTML = movements.map(m => `
            <tr class="hover:bg-slate-50 transition border-b border-slate-100">
                <td class="px-3 py-2.5 text-slate-500 whitespace-nowrap">${m.move_date}</td>
                <td class="px-3 py-2.5 font-semibold text-slate-900 min-w-[180px]">
                    <span class="text-blue-600 block">${m.device_code}</span>
                    <span class="text-xs text-slate-500 font-normal">${m.device_name}</span>
                </td>
                <td class="px-3 py-2.5 whitespace-nowrap">
                    <span class="inline-flex items-center text-xs text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200 whitespace-nowrap">
                        ${m.from_location}
                    </span>
                </td>
                <td class="px-3 py-2.5 whitespace-nowrap">
                    <span class="inline-flex items-center text-xs font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 whitespace-nowrap">
                        👉 ${m.to_location}
                    </span>
                </td>
                <td class="px-3 py-2.5 text-slate-700 font-medium whitespace-nowrap">${m.moved_by}</td>
                <td class="px-3 py-2.5 text-slate-600 italic min-w-[140px]">${m.reason}</td>
            </tr>
        `).join('');

        lucide.createIcons();
    } catch (err) {
        console.error('Lỗi tải lịch sử di chuyển:', err);
    }
}

// ==================== MƯỢN - TRẢ THIẾT BỊ ====================
async function loadBorrowRequests() {
    try {
        const search = document.getElementById('borrowSearchInput')?.value || '';
        const status = document.getElementById('borrowStatusFilter')?.value || 'all';

        const params = new URLSearchParams({ search, status });
        const res = await fetch(`/api/borrow?${params.toString()}`);
        const requests = await res.json();
        state.borrowRequests = requests;

        const tbody = document.getElementById('borrowTableBody');
        if (requests.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="py-8 text-center text-slate-400">Không có phiếu mượn nào phù hợp.</td></tr>';
            return;
        }

        tbody.innerHTML = requests.map(b => {
            const isOverdue = b.overdue_days > 0 && b.status === 'Đang mượn';
            let statusBadge = `<span class="px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap inline-flex items-center ${getStatusBadgeClass(b.status)}"><span class="w-1.5 h-1.5 rounded-full mr-1.5 shrink-0 ${getStatusDotColor(b.status)}"></span>${b.status}</span>`;
            if (isOverdue) {
                statusBadge += `<span class="ml-1 px-2 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-700 border border-red-200 whitespace-nowrap inline-flex items-center">Quá ${b.overdue_days} ngày</span>`;
            }

            let actions = '';
            if (state.currentUser.role === 'admin') {
                if (b.status === 'Chờ duyệt') {
                    actions = `
                        <button onclick="handleApproveBorrow(${b.id})" class="px-2.5 py-1 text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg shadow-sm transition whitespace-nowrap">Duyệt mượn</button>
                        <button onclick="handleRejectBorrow(${b.id})" class="px-2.5 py-1 text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition ml-1 whitespace-nowrap">Từ chối</button>
                    `;
                } else if (b.status === 'Đang mượn') {
                    actions = `
                        <button onclick="openReturnModal(${b.id})" class="px-3 py-1 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-sm transition flex items-center mx-auto whitespace-nowrap">
                            <i data-lucide="check-circle" class="w-3.5 h-3.5 mr-1"></i> Thu hồi / Trả
                        </button>
                    `;
                } else {
                    actions = `<span class="text-xs text-slate-400 whitespace-nowrap">${b.actual_return_date ? `Đã trả ${formatDate(b.actual_return_date)}` : 'Đã kết thúc'}</span>`;
                }
            } else {
                actions = `<span class="text-xs text-slate-400 italic whitespace-nowrap">Chỉ xem</span>`;
            }

            return `
                <tr class="hover:bg-slate-50 transition border-b border-slate-100 ${isOverdue ? 'bg-red-50/30' : ''}">
                    <td class="px-4 py-3 font-semibold text-blue-600 whitespace-nowrap">${b.request_code}</td>
                    <td class="px-4 py-3 whitespace-nowrap">
                        <strong class="text-slate-900 block">${b.user_name}</strong>
                        <span class="text-xs text-slate-500">${b.user_code} - ${b.department}</span>
                    </td>
                    <td class="px-4 py-3 min-w-[200px]">
                        <strong class="text-slate-800 block">${b.device_code}</strong>
                        <span class="text-xs text-slate-500">${b.device_name}</span>
                    </td>
                    <td class="px-4 py-3 text-slate-600 text-xs whitespace-nowrap">${formatDate(b.borrow_date)}</td>
                    <td class="px-4 py-3 text-xs whitespace-nowrap ${isOverdue ? 'text-red-600 font-bold' : 'text-slate-700'}">
                        ${formatDate(b.expected_return_date)}
                    </td>
                    <td class="px-4 py-3 whitespace-nowrap">${statusBadge}</td>
                    <td class="px-4 py-3 text-center whitespace-nowrap">${actions}</td>
                </tr>
            `;
        }).join('');

        lucide.createIcons();
    } catch (err) {
        console.error('Lỗi tải phiếu mượn:', err);
    }
}

function openBorrowModal() {
    document.getElementById('borrowForm').reset();
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('borrowDate').value = today;

    // Hạn trả mặc định: 3 ngày sau
    const returnDate = new Date();
    returnDate.setDate(returnDate.getDate() + 3);
    document.getElementById('borrowExpectedReturn').value = returnDate.toISOString().split('T')[0];

    // Chỉ hiển thị các thiết bị "Sẵn sàng" trong dropdown
    const devSelect = document.getElementById('borrowDeviceCode');
    const availableDevices = state.devices.filter(d => d.status === 'Sẵn sàng');
    devSelect.innerHTML = '<option value="">-- Chọn thiết bị có sẵn --</option>' +
        availableDevices.map(d => `<option value="${d.code}">[${d.code}] ${d.name} (${d.current_location})</option>`).join('');

    // Pre-select teacher in searchable combobox
    if (state.currentUser.role === 'teacher') {
        setBorrowUserCombobox(state.currentUser.code);
    } else {
        setBorrowUserCombobox('');
    }

    openModal('borrowModal');
}

async function handleBorrowSubmit(event) {
    event.preventDefault();
    const payload = {
        user_code: document.getElementById('borrowUserCode').value,
        device_code: document.getElementById('borrowDeviceCode').value,
        borrow_date: document.getElementById('borrowDate').value,
        expected_return_date: document.getElementById('borrowExpectedReturn').value,
        purpose: document.getElementById('borrowPurpose').value.trim(),
        auto_approve: document.getElementById('borrowAutoApprove').checked
    };

    try {
        const res = await fetch('/api/borrow', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (!res.ok) {
            Swal.fire({ icon: 'error', title: 'Lỗi mượn thiết bị', text: data.error });
            return;
        }

        closeModal('borrowModal');
        Swal.fire({
            icon: 'success',
            title: 'Thành công',
            text: data.message,
            timer: 2000,
            showConfirmButton: false
        });

        await loadBorrowRequests();
        await loadDevices();
        if (currentTab === 'dashboard') await loadDashboard();
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Lỗi', text: err.message });
    }
}

async function handleApproveBorrow(id) {
    try {
        const res = await fetch(`/api/borrow/${id}/approve`, { method: 'PUT' });
        const data = await res.json();
        if (!res.ok) {
            Swal.fire({ icon: 'error', title: 'Lỗi duyệt', text: data.error });
            return;
        }
        Swal.fire({ icon: 'success', title: 'Đã duyệt', text: data.message, timer: 1500, showConfirmButton: false });
        await loadBorrowRequests();
        await loadDevices();
        if (currentTab === 'dashboard') await loadDashboard();
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Lỗi', text: err.message });
    }
}

async function handleRejectBorrow(id) {
    const { value: reason } = await Swal.fire({
        title: 'Từ chối yêu cầu mượn?',
        input: 'text',
        inputLabel: 'Lý do từ chối',
        inputPlaceholder: 'Nhập lý do từ chối...',
        showCancelButton: true,
        confirmButtonText: 'Xác nhận từ chối',
        cancelButtonText: 'Hủy'
    });

    if (reason !== undefined) {
        try {
            const res = await fetch(`/api/borrow/${id}/reject`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reason: reason || 'Không đủ điều kiện' })
            });
            const data = await res.json();
            if (!res.ok) {
                Swal.fire({ icon: 'error', title: 'Lỗi', text: data.error });
                return;
            }
            Swal.fire({ icon: 'success', title: 'Đã từ chối', text: data.message, timer: 1500, showConfirmButton: false });
            await loadBorrowRequests();
        } catch (err) {
            Swal.fire({ icon: 'error', title: 'Lỗi', text: err.message });
        }
    }
}

function openReturnModal(id) {
    const req = state.borrowRequests.find(b => b.id === id);
    if (!req) return;

    document.getElementById('returnBorrowId').value = req.id;
    document.getElementById('returnRequestCode').innerText = req.request_code;
    document.getElementById('returnUserName').innerText = `${req.user_name} (${req.user_code})`;
    document.getElementById('returnDeviceName').innerText = `${req.device_code} - ${req.device_name}`;
    document.getElementById('returnActualDate').value = new Date().toISOString().split('T')[0];
    document.getElementById('returnCondition').value = 'Tốt';
    document.getElementById('returnNotes').value = '';

    openModal('returnModal');
}

async function handleReturnSubmit(event) {
    event.preventDefault();
    const id = document.getElementById('returnBorrowId').value;
    const payload = {
        actual_return_date: document.getElementById('returnActualDate').value,
        return_condition: document.getElementById('returnCondition').value,
        notes: document.getElementById('returnNotes').value.trim()
    };

    try {
        const res = await fetch(`/api/borrow/${id}/return`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (!res.ok) {
            Swal.fire({ icon: 'error', title: 'Lỗi thu hồi', text: data.error });
            return;
        }

        closeModal('returnModal');
        Swal.fire({
            icon: 'success',
            title: 'Hoàn tất thu hồi thiết bị',
            text: data.message,
            timer: 2000,
            showConfirmButton: false
        });

        await loadBorrowRequests();
        await loadDevices();
        if (currentTab === 'dashboard') await loadDashboard();
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Lỗi', text: err.message });
    }
}

// ==================== USERS & ROOMS ====================
async function loadUsers() {
    try {
        const res = await fetch('/api/users');
        const users = await res.json();
        state.users = users;

        // Điền danh sách Tổ / Phòng ban vào bộ lọc
        const userDeptFilter = document.getElementById('userDeptFilter');
        if (userDeptFilter) {
            const currentDept = userDeptFilter.value || 'all';
            const depts = [...new Set(users.map(u => u.department).filter(Boolean))].sort();
            userDeptFilter.innerHTML = '<option value="all">Tất cả tổ / ban</option>' +
                depts.map(d => `<option value="${d}" ${d === currentDept ? 'selected' : ''}>${d}</option>`).join('');
        }

        renderUsers();
        populateDropdowns();
    } catch (err) {
        console.error('Lỗi tải người dùng:', err);
    }
}

function renderUsers() {
    const q = (document.getElementById('userSearchInput')?.value || '').trim().toLowerCase();
    const dept = document.getElementById('userDeptFilter')?.value || 'all';
    const clearBtn = document.getElementById('userSearchClear');
    if (clearBtn) clearBtn.classList.toggle('hidden', !q);

    const filtered = (state.users || []).filter(u => {
        if (dept !== 'all' && u.department !== dept) return false;
        if (!q) return true;
        const nameMatch = (u.fullname || '').toLowerCase().includes(q);
        const codeMatch = (u.code || '').toLowerCase().includes(q);
        const deptMatch = (u.department || '').toLowerCase().includes(q);
        const phoneMatch = (u.phone || '').includes(q);
        return nameMatch || codeMatch || deptMatch || phoneMatch;
    });

    const countBadge = document.getElementById('userCountBadge');
    if (countBadge) {
        countBadge.innerText = `Hiển thị ${filtered.length} / ${(state.users || []).length} cán bộ`;
    }

    const isAdmin = state.currentUser.role === 'admin';
    const tbody = document.getElementById('usersTableBody');
    if (!tbody) return;

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="py-8 text-center text-slate-400">Không tìm thấy cán bộ nào khớp với bộ lọc tìm kiếm.</td></tr>`;
        return;
    }

    tbody.innerHTML = filtered.map(u => {
        const actionButtons = isAdmin ? `
            <div class="flex items-center justify-center space-x-1">
                <button onclick="openEditUserModal(${u.id})" title="Chỉnh sửa thông tin" class="p-1 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded transition">
                    <i data-lucide="pencil" class="w-3.5 h-3.5"></i>
                </button>
                <button onclick="handleDeleteUser(${u.id}, '${u.code}')" title="Xóa người dùng" class="p-1 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded transition">
                    <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                </button>
            </div>
        ` : `
            <span class="text-slate-400 text-[11px] italic">Chỉ xem</span>
        `;

        const roleBadge = u.role === 'admin'
            ? `<span class="role-badge role-badge-admin"><i data-lucide="shield-check" class="w-3.5 h-3.5 mr-1 text-purple-600 shrink-0"></i>Quản trị viên</span>`
            : (u.role === 'technician'
                ? `<span class="role-badge role-badge-technician"><i data-lucide="wrench" class="w-3.5 h-3.5 mr-1 text-amber-600 shrink-0"></i>Kỹ thuật viên</span>`
                : `<span class="role-badge role-badge-teacher"><i data-lucide="graduation-cap" class="w-3.5 h-3.5 mr-1 text-blue-600 shrink-0"></i>Giáo viên</span>`);

        return `
            <tr class="hover:bg-slate-50 border-b border-slate-100 transition">
                <td class="px-3 py-2.5 font-semibold text-blue-600 whitespace-nowrap">${u.code}</td>
                <td class="px-3 py-2.5 font-medium text-slate-900 whitespace-nowrap">
                    <div>${u.fullname}</div>
                    ${u.phone ? `<span class="block text-[11px] text-slate-400">📞 ${u.phone}</span>` : ''}
                </td>
                <td class="px-3 py-2.5 text-slate-600 font-medium whitespace-nowrap">${u.department}</td>
                <td class="px-3 py-2.5 whitespace-nowrap">
                    ${roleBadge}
                </td>
                <td class="px-3 py-2.5 text-center whitespace-nowrap">${actionButtons}</td>
            </tr>
        `;
    }).join('');

    lucide.createIcons();
}

function filterUsersList() {
    renderUsers();
}

function clearUserSearch() {
    const input = document.getElementById('userSearchInput');
    if (input) input.value = '';
    renderUsers();
}

const LOCATION_TYPES = [
    'Phòng học & Lớp học',
    'Phòng chức năng & Bộ môn',
    'Văn phòng & Khối làm việc',
    'Kho & Kỹ thuật',
    'Khuôn viên, Sân bãi & Tiện ích',
    'Hội trường & Phòng sự kiện',
    'Tiện ích & Phụ trợ',
    'Khác'
];

async function loadLocations() {
    try {
        const res = await fetch('/api/locations');
        const locations = await res.json();
        state.locations = locations;

        // Điền danh sách Loại phòng vào bộ lọc
        const locationTypeFilter = document.getElementById('locationTypeFilter');
        if (locationTypeFilter) {
            const currentType = locationTypeFilter.value || 'all';
            locationTypeFilter.innerHTML = '<option value="all">Tất cả loại phòng</option>' +
                LOCATION_TYPES.map(t => `<option value="${t}" ${t === currentType ? 'selected' : ''}>${t}</option>`).join('');
        }

        renderLocations();
        populateDropdowns();
    } catch (err) {
        console.error('Lỗi tải phòng ban:', err);
    }
}

function renderLocations() {
    const q = (document.getElementById('locationSearchInput')?.value || '').trim().toLowerCase();
    const floor = document.getElementById('locationFloorFilter')?.value || 'all';
    const type = document.getElementById('locationTypeFilter')?.value || 'all';
    const clearBtn = document.getElementById('locationSearchClear');
    if (clearBtn) clearBtn.classList.toggle('hidden', !q);

    const filtered = (state.locations || []).filter(l => {
        if (floor !== 'all' && l.floor !== floor) return false;
        if (type !== 'all' && l.type !== type) return false;
        if (!q) return true;
        const nameMatch = (l.name || '').toLowerCase().includes(q);
        const codeMatch = (l.code || '').toLowerCase().includes(q);
        const mgrMatch = (l.manager_name || '').toLowerCase().includes(q);
        return nameMatch || codeMatch || mgrMatch;
    });

    const countBadge = document.getElementById('locationCountBadge');
    if (countBadge) {
        countBadge.innerText = `Hiển thị ${filtered.length} / ${(state.locations || []).length} phòng`;
    }

    const isAdmin = state.currentUser.role === 'admin';
    const tbody = document.getElementById('locationsTableBody');
    if (!tbody) return;

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="py-8 text-center text-slate-400">Không tìm thấy phòng nào khớp với bộ lọc tìm kiếm.</td></tr>`;
        return;
    }

    tbody.innerHTML = filtered.map(l => {
        // Chỉnh sửa trực tiếp Loại phòng ở phần hiển thị chỗ phòng
        const roomTypeCell = isAdmin ? `
            <select onchange="handleInlineRoomTypeChange(${l.id}, this.value)" 
                    title="Click để đổi trực tiếp Loại phòng"
                    class="text-xs border border-slate-200 rounded-lg px-2 py-1 bg-white text-slate-800 font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none cursor-pointer hover:border-blue-400 transition shadow-xs">
                ${LOCATION_TYPES.map(t => `<option value="${t}" ${l.type === t ? 'selected' : ''}>${t}</option>`).join('')}
            </select>
        ` : `
            <span class="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 text-xs font-medium border border-slate-200 whitespace-nowrap">
                ${l.type}
            </span>
        `;

        const actionButtons = isAdmin ? `
            <div class="flex items-center justify-center space-x-1">
                <button onclick="openEditLocationModal(${l.id})" title="Chỉnh sửa chi tiết phòng" class="p-1 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded transition">
                    <i data-lucide="pencil" class="w-3.5 h-3.5"></i>
                </button>
                <button onclick="handleDeleteLocation(${l.id}, '${l.name.replace(/'/g, "\\'")}')" title="Xóa phòng" class="p-1 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded transition">
                    <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                </button>
            </div>
        ` : `
            <span class="text-slate-400 text-[11px] italic">Chỉ xem</span>
        `;

        return `
            <tr class="hover:bg-slate-50 border-b border-slate-100 transition">
                <td class="px-3 py-2.5 whitespace-nowrap">
                    <span class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200 whitespace-nowrap">
                        ${l.floor || 'Tầng 1'}
                    </span>
                </td>
                <td class="px-3 py-2.5 font-semibold text-emerald-600 whitespace-nowrap">${l.code}</td>
                <td class="px-3 py-2.5 font-medium text-slate-900 whitespace-nowrap">${l.name}</td>
                <td class="px-3 py-2.5 whitespace-nowrap">${roomTypeCell}</td>
                <td class="px-3 py-2.5 text-slate-600 whitespace-nowrap">${l.manager_name || '-'}</td>
                <td class="px-3 py-2.5 text-center whitespace-nowrap">${actionButtons}</td>
            </tr>
        `;
    }).join('');

    lucide.createIcons();
}

function filterLocationsList() {
    renderLocations();
}

function clearLocationSearch() {
    const input = document.getElementById('locationSearchInput');
    if (input) input.value = '';
    renderLocations();
}

// Chỉnh sửa nhanh Loại phòng trực tiếp trên bảng
async function handleInlineRoomTypeChange(locId, newType) {
    if (state.currentUser.role !== 'admin') {
        Swal.fire({ icon: 'warning', title: 'Từ chối quyền', text: 'Chỉ Quản trị viên (Admin) mới có quyền chỉnh sửa loại phòng!' });
        await loadLocations();
        return;
    }

    try {
        const res = await fetch(`/api/locations/${locId}/type`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-User-Role': state.currentUser.role
            },
            body: JSON.stringify({ type: newType })
        });
        const data = await res.json();
        if (!res.ok) {
            Swal.fire({ icon: 'error', title: 'Lỗi', text: data.error });
            await loadLocations();
            return;
        }

        const loc = state.locations.find(l => l.id === locId);
        if (loc) loc.type = newType;
        populateDropdowns();

        Swal.fire({
            toast: true,
            position: 'top-end',
            icon: 'success',
            title: `Đã đổi loại phòng thành: ${newType}`,
            showConfirmButton: false,
            timer: 2000
        });
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Lỗi', text: err.message });
        await loadLocations();
    }
}

function openEditLocationModal(id) {
    const loc = state.locations.find(l => l.id === id);
    if (!loc) return;

    document.getElementById('editLocId').value = loc.id;
    document.getElementById('editLocCode').value = loc.code;
    document.getElementById('editLocFloor').value = loc.floor || 'Tầng 1';
    document.getElementById('editLocName').value = loc.name;
    document.getElementById('editLocType').value = loc.type || 'Phòng học & Lớp học';
    document.getElementById('editLocManager').value = loc.manager_name || '';
    document.getElementById('editLocDesc').value = loc.description || '';

    openModal('editLocationModal');
}

async function handleEditLocationSubmit(event) {
    event.preventDefault();
    const id = document.getElementById('editLocId').value;
    const payload = {
        code: document.getElementById('editLocCode').value.trim().toUpperCase(),
        floor: document.getElementById('editLocFloor').value,
        name: document.getElementById('editLocName').value.trim(),
        type: document.getElementById('editLocType').value,
        manager_name: document.getElementById('editLocManager').value.trim(),
        description: document.getElementById('editLocDesc').value.trim()
    };

    try {
        const res = await fetch(`/api/locations/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-User-Role': state.currentUser.role
            },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) {
            Swal.fire({ icon: 'error', title: 'Lỗi', text: data.error });
            return;
        }
        closeModal('editLocationModal');
        Swal.fire({ icon: 'success', title: 'Thành công', text: data.message, timer: 1500, showConfirmButton: false });
        await loadLocations();
        await loadDevices();
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Lỗi', text: err.message });
    }
}

async function handleDeleteLocation(id, name) {
    const resConfirm = await Swal.fire({
        title: `Xác nhận xóa phòng "${name}"?`,
        text: 'Chỉ có thể xóa nếu phòng không chứa bất kỳ thiết bị nào.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        confirmButtonText: 'Đồng ý xóa',
        cancelButtonText: 'Hủy'
    });
    if (!resConfirm.isConfirmed) return;

    try {
        const res = await fetch(`/api/locations/${id}`, {
            method: 'DELETE',
            headers: { 'X-User-Role': state.currentUser.role }
        });
        const data = await res.json();
        if (!res.ok) {
            Swal.fire({ icon: 'error', title: 'Lỗi', text: data.error });
            return;
        }
        Swal.fire({ icon: 'success', title: 'Đã xóa', text: data.message, timer: 1500, showConfirmButton: false });
        await loadLocations();
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Lỗi', text: err.message });
    }
}

// Chỉnh sửa thông tin Người dùng / Giáo viên
function openEditUserModal(id) {
    const u = state.users.find(x => x.id === id);
    if (!u) return;

    document.getElementById('editUserId').value = u.id;
    document.getElementById('editUserCode').value = u.code;
    document.getElementById('editUserFullname').value = u.fullname;
    document.getElementById('editUserRole').value = u.role || 'teacher';
    document.getElementById('editUserDept').value = u.department;
    document.getElementById('editUserEmail').value = u.email || '';
    document.getElementById('editUserPhone').value = u.phone || '';

    openModal('editUserModal');
}

async function handleEditUserSubmit(event) {
    event.preventDefault();
    const id = document.getElementById('editUserId').value;
    const payload = {
        code: document.getElementById('editUserCode').value.trim().toUpperCase(),
        fullname: document.getElementById('editUserFullname').value.trim(),
        role: document.getElementById('editUserRole').value,
        department: document.getElementById('editUserDept').value.trim(),
        email: document.getElementById('editUserEmail').value.trim(),
        phone: document.getElementById('editUserPhone').value.trim()
    };

    try {
        const res = await fetch(`/api/users/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-User-Role': state.currentUser.role
            },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) {
            Swal.fire({ icon: 'error', title: 'Lỗi', text: data.error });
            return;
        }
        closeModal('editUserModal');
        Swal.fire({ icon: 'success', title: 'Thành công', text: data.message, timer: 1500, showConfirmButton: false });
        await loadUsers();
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Lỗi', text: err.message });
    }
}

// ==================== DI CHUYỂN PHÂN LOẠI & QUẢN LÝ DANH MỤC ====================
function openChangeCategoryModal(deviceId) {
    const d = state.devices.find(x => x.id === deviceId);
    if (!d) return;

    document.getElementById('changeCatDeviceId').value = d.id;
    document.getElementById('changeCatDeviceName').innerText = `${d.code} - ${d.name}`;
    document.getElementById('changeCatCurrentCat').innerText = d.category;

    const selectEl = document.getElementById('changeCatNewSelect');
    selectEl.innerHTML = state.categories.map(c => `
        <option value="${c.name}" ${c.name === d.category ? 'selected' : ''}>${c.name}</option>
    `).join('');

    openModal('changeCategoryModal');
}

async function handleChangeCategorySubmit(event) {
    event.preventDefault();
    const deviceId = document.getElementById('changeCatDeviceId').value;
    const newCategory = document.getElementById('changeCatNewSelect').value;

    try {
        const res = await fetch('/api/devices/change-category', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-Role': state.currentUser.role
            },
            body: JSON.stringify({ device_id: deviceId, category: newCategory })
        });
        const data = await res.json();
        if (!res.ok) {
            Swal.fire({ icon: 'error', title: 'Lỗi', text: data.error });
            return;
        }
        closeModal('changeCategoryModal');
        Swal.fire({ icon: 'success', title: 'Thành công', text: data.message, timer: 1500, showConfirmButton: false });
        await loadDevices();
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Lỗi', text: err.message });
    }
}

async function openCategoryManageModal() {
    await renderCategoryManageTable();
    openModal('categoryManageModal');
}

async function renderCategoryManageTable() {
    try {
        const res = await fetch('/api/categories');
        const categories = await res.json();
        state.categories = categories;

        const tbody = document.getElementById('categoryManageTableBody');
        if (!tbody) return;

        const counts = {};
        state.devices.forEach(d => {
            counts[d.category] = (counts[d.category] || 0) + 1;
        });

        tbody.innerHTML = categories.map((c, idx) => `
            <tr class="hover:bg-slate-50 border-b border-slate-100">
                <td class="px-3 py-2 text-slate-400 font-mono">${idx + 1}</td>
                <td class="px-3 py-2 font-semibold text-slate-800">${c.name}</td>
                <td class="px-3 py-2 text-right">
                    <span class="px-2 py-0.5 rounded-full text-xs font-bold bg-purple-50 text-purple-700 border border-purple-100">
                        ${counts[c.name] || 0} TB
                    </span>
                </td>
                <td class="px-3 py-2 text-center whitespace-nowrap">
                    <div class="flex items-center justify-center space-x-1">
                        <button onclick="handleRenameCategory(${c.id}, '${c.name.replace(/'/g, "\\'")}')" title="Đổi tên phân loại" class="p-1 text-slate-500 hover:text-blue-600 rounded">
                            <i data-lucide="edit-2" class="w-3.5 h-3.5"></i>
                        </button>
                        <button onclick="handleDeleteCategory(${c.id}, '${c.name.replace(/'/g, "\\'")}')" title="Xóa phân loại" class="p-1 text-slate-500 hover:text-red-600 rounded">
                            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');

        lucide.createIcons();
    } catch (err) {
        console.error('Lỗi tải danh mục:', err);
    }
}

async function handleAddCategorySubmit(event) {
    event.preventDefault();
    const nameInput = document.getElementById('newCategoryName');
    const name = nameInput.value.trim();
    if (!name) return;

    try {
        const res = await fetch('/api/categories', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-Role': state.currentUser.role
            },
            body: JSON.stringify({ name })
        });
        const data = await res.json();
        if (!res.ok) {
            Swal.fire({ icon: 'error', title: 'Lỗi', text: data.error });
            return;
        }
        nameInput.value = '';
        await renderCategoryManageTable();
        populateDropdowns();
        Swal.fire({ toast: true, position: 'top-end', icon: 'success', title: data.message, showConfirmButton: false, timer: 1500 });
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Lỗi', text: err.message });
    }
}

async function handleRenameCategory(catId, oldName) {
    const { value: newName } = await Swal.fire({
        title: 'Đổi tên phân loại / danh mục',
        input: 'text',
        inputValue: oldName,
        showCancelButton: true,
        confirmButtonText: 'Lưu thay đổi',
        cancelButtonText: 'Hủy',
        inputValidator: (val) => {
            if (!val || !val.trim()) return 'Tên phân loại không được để trống!';
        }
    });

    if (!newName || newName.trim() === oldName) return;

    try {
        const res = await fetch(`/api/categories/${catId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-User-Role': state.currentUser.role
            },
            body: JSON.stringify({ name: newName.trim() })
        });
        const data = await res.json();
        if (!res.ok) {
            Swal.fire({ icon: 'error', title: 'Lỗi', text: data.error });
            return;
        }
        await renderCategoryManageTable();
        await loadDevices();
        populateDropdowns();
        Swal.fire({ toast: true, position: 'top-end', icon: 'success', title: data.message, showConfirmButton: false, timer: 1500 });
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Lỗi', text: err.message });
    }
}

async function handleDeleteCategory(catId, catName) {
    const resConfirm = await Swal.fire({
        title: `Xác nhận xóa phân loại "${catName}"?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        confirmButtonText: 'Xóa phân loại',
        cancelButtonText: 'Hủy'
    });
    if (!resConfirm.isConfirmed) return;

    try {
        const res = await fetch(`/api/categories/${catId}`, {
            method: 'DELETE',
            headers: { 'X-User-Role': state.currentUser.role }
        });
        const data = await res.json();
        if (!res.ok) {
            Swal.fire({ icon: 'error', title: 'Lỗi', text: data.error });
            return;
        }
        await renderCategoryManageTable();
        populateDropdowns();
        Swal.fire({ toast: true, position: 'top-end', icon: 'success', title: data.message, showConfirmButton: false, timer: 1500 });
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Lỗi', text: err.message });
    }
}

function openAddUserModal() {
    document.getElementById('userForm').reset();
    openModal('userModal');
}

async function handleUserSubmit(event) {
    event.preventDefault();
    const payload = {
        code: document.getElementById('userCodeInput').value.trim().toUpperCase(),
        fullname: document.getElementById('userFullnameInput').value.trim(),
        role: document.getElementById('userRoleInput').value,
        department: document.getElementById('userDeptInput').value.trim(),
        email: document.getElementById('userEmailInput').value.trim(),
        phone: document.getElementById('userPhoneInput').value.trim()
    };

    try {
        const res = await fetch('/api/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-Role': state.currentUser.role
            },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) {
            Swal.fire({ icon: 'error', title: 'Lỗi', text: data.error });
            return;
        }
        closeModal('userModal');
        Swal.fire({ icon: 'success', title: 'Thành công', text: data.message, timer: 1500, showConfirmButton: false });
        await loadUsers();
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Lỗi', text: err.message });
    }
}

async function handleDeleteUser(id, code) {
    const resConfirm = await Swal.fire({
        title: `Xác nhận xóa người dùng ${code}?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'Xóa'
    });
    if (!resConfirm.isConfirmed) return;

    try {
        const res = await fetch(`/api/users/${id}`, {
            method: 'DELETE',
            headers: { 'X-User-Role': state.currentUser.role }
        });
        const data = await res.json();
        if (!res.ok) {
            Swal.fire({ icon: 'error', title: 'Lỗi', text: data.error });
            return;
        }
        Swal.fire({ icon: 'success', title: 'Đã xóa', text: data.message, timer: 1500, showConfirmButton: false });
        await loadUsers();
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Lỗi', text: err.message });
    }
}

function openAddLocationModal() {
    document.getElementById('locationForm').reset();
    openModal('locationModal');
}

async function handleLocationSubmit(event) {
    event.preventDefault();
    const payload = {
        code: document.getElementById('locCodeInput').value.trim().toUpperCase(),
        name: document.getElementById('locNameInput').value.trim(),
        floor: document.getElementById('locFloorInput')?.value || 'Tầng 1',
        type: document.getElementById('locTypeInput').value,
        manager_name: document.getElementById('locManagerInput').value.trim(),
        description: document.getElementById('locDescInput').value.trim()
    };

    try {
        const res = await fetch('/api/locations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-Role': state.currentUser.role
            },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) {
            Swal.fire({ icon: 'error', title: 'Lỗi', text: data.error });
            return;
        }
        closeModal('locationModal');
        Swal.fire({ icon: 'success', title: 'Thành công', text: data.message, timer: 1500, showConfirmButton: false });
        await loadLocations();
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Lỗi', text: err.message });
    }
}

// ==================== BÁO CÁO & THỐNG KÊ ====================
async function loadReports() {
    try {
        const res = await fetch('/api/stats');
        const stats = await res.json();

        // Top teachers
        const teacherTbody = document.getElementById('topTeachersReportTable');
        if (stats.top_teachers && stats.top_teachers.length > 0) {
            teacherTbody.innerHTML = stats.top_teachers.map(t => `
                <tr class="hover:bg-slate-50">
                    <td class="py-2.5 font-semibold text-blue-600">${t.user_code}</td>
                    <td class="py-2.5 font-medium text-slate-800">${t.user_name}</td>
                    <td class="py-2.5 text-slate-500">${t.department}</td>
                    <td class="py-2.5 text-right font-bold text-slate-900">${t.borrow_count} lượt</td>
                </tr>
            `).join('');
        } else {
            teacherTbody.innerHTML = '<tr><td colspan="4" class="py-4 text-center text-slate-400">Chưa có dữ liệu</td></tr>';
        }

        // Broken devices
        const brokenDevices = state.devices.filter(d => d.status === 'Hỏng' || d.status === 'Bảo trì');
        const brokenTbody = document.getElementById('brokenDevicesTable');
        if (brokenDevices.length > 0) {
            brokenTbody.innerHTML = brokenDevices.map(d => `
                <tr class="hover:bg-slate-50">
                    <td class="py-2.5 font-semibold text-rose-600">${d.code}</td>
                    <td class="py-2.5 font-medium text-slate-800">${d.name}</td>
                    <td class="py-2.5 text-slate-600">${d.current_location}</td>
                    <td class="py-2.5"><span class="px-2 py-0.5 rounded text-xs font-semibold ${getStatusBadgeClass(d.status)}">${d.status}</span></td>
                </tr>
            `).join('');
        } else {
            brokenTbody.innerHTML = '<tr><td colspan="4" class="py-4 text-center text-slate-400">Không có thiết bị nào bị hỏng 🎉</td></tr>';
        }
    } catch (err) {
        console.error('Lỗi tải báo cáo:', err);
    }
}

// ==================== XUẤT EXCEL (SheetJS) ====================
function exportDevicesExcel() {
    if (!state.devices || state.devices.length === 0) {
        Swal.fire({ icon: 'info', title: 'Thông báo', text: 'Không có dữ liệu thiết bị để xuất!' });
        return;
    }

    const excelData = state.devices.map((d, index) => ({
        'STT': index + 1,
        'Mã thiết bị': d.code,
        'Tên thiết bị': d.name,
        'Danh mục': d.category,
        'Vị trí hiện tại': d.current_location,
        'Trạng thái': d.status,
        'Nguyên giá (VNĐ)': d.price,
        'Ngày nhập': d.purchase_date,
        'Nhà cung cấp': d.supplier,
        'Thông số kỹ thuật': d.specification,
        'Ghi chú': d.notes
    }));

    const ws = XLSX.utils.json_to_sheet(excelData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Danh_muc_thiet_bi");
    XLSX.writeFile(wb, `Danh_muc_thiet_bi_${getFormattedTimestamp()}.xlsx`);
}

function exportBorrowExcel() {
    if (!state.borrowRequests || state.borrowRequests.length === 0) {
        Swal.fire({ icon: 'info', title: 'Thông báo', text: 'Không có dữ liệu mượn trả để xuất!' });
        return;
    }

    const excelData = state.borrowRequests.map((b, index) => ({
        'STT': index + 1,
        'Mã phiếu mượn': b.request_code,
        'Mã giáo viên': b.user_code,
        'Họ tên giáo viên': b.user_name,
        'Phòng ban / Bộ môn': b.department,
        'Mã thiết bị': b.device_code,
        'Tên thiết bị': b.device_name,
        'Ngày mượn': b.borrow_date,
        'Hạn trả dự kiến': b.expected_return_date,
        'Ngày trả thực tế': b.actual_return_date || 'Chưa trả',
        'Trạng thái': b.status,
        'Tình trạng khi trả': b.return_condition,
        'Mục đích sử dụng': b.purpose,
        'Người duyệt': b.approved_by || ''
    }));

    const ws = XLSX.utils.json_to_sheet(excelData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "So_muon_tra");
    XLSX.writeFile(wb, `So_muon_tra_thiet_bi_${getFormattedTimestamp()}.xlsx`);
}

function exportMovementExcel() {
    if (!state.movements || state.movements.length === 0) {
        Swal.fire({ icon: 'info', title: 'Thông báo', text: 'Không có dữ liệu di chuyển để xuất!' });
        return;
    }

    const excelData = state.movements.map((m, index) => ({
        'STT': index + 1,
        'Thời gian di chuyển': m.move_date,
        'Mã thiết bị': m.device_code,
        'Tên thiết bị': m.device_name,
        'Vị trí trước khi chuyển': m.from_location,
        'Vị trí sau khi chuyển': m.to_location,
        'Người thực hiện': m.moved_by,
        'Lý do di chuyển': m.reason
    }));

    const ws = XLSX.utils.json_to_sheet(excelData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Lich_su_di_chuyen");
    XLSX.writeFile(wb, `Lich_su_di_chuyen_thiet_bi_${getFormattedTimestamp()}.xlsx`);
}

// ==================== HỆ THỐNG & NHẬT KÝ ====================
async function loadLogs() {
    try {
        const res = await fetch('/api/logs');
        const logs = await res.json();

        const tbody = document.getElementById('activityLogsTable');
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="py-4 text-center text-slate-400">Chưa có nhật ký hoạt động.</td></tr>';
            return;
        }

        tbody.innerHTML = logs.map(l => `
            <tr class="hover:bg-slate-50 border-b border-slate-100">
                <td class="px-3 py-2 text-slate-400 whitespace-nowrap">${l.created_at}</td>
                <td class="px-3 py-2 font-semibold text-slate-800">${l.user_name || 'Hệ thống'}</td>
                <td class="px-3 py-2">
                    <span class="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700">
                        ${l.action}
                    </span>
                </td>
                <td class="px-3 py-2 text-slate-600">${l.details}</td>
            </tr>
        `).join('');

        lucide.createIcons();
    } catch (err) {
        console.error('Lỗi tải nhật ký:', err);
    }
}

async function handleRestoreDatabase() {
    const fileInput = document.getElementById('restoreFileInput');
    if (!fileInput.files.length) {
        Swal.fire({ icon: 'warning', title: 'Chưa chọn file', text: 'Vui lòng chọn file sao lưu định dạng .json!' });
        return;
    }

    const resConfirm = await Swal.fire({
        title: 'Xác nhận phục hồi cơ sở dữ liệu?',
        text: 'Toàn bộ dữ liệu hiện tại sẽ được thay thế bằng nội dung trong tệp sao lưu!',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3b82f6',
        confirmButtonText: 'Đồng ý phục hồi',
        cancelButtonText: 'Hủy'
    });
    if (!resConfirm.isConfirmed) return;

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const res = await fetch('/api/restore', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (!res.ok) {
            Swal.fire({ icon: 'error', title: 'Lỗi phục hồi', text: data.error });
            return;
        }
        Swal.fire({ icon: 'success', title: 'Thành công', text: data.message });
        await loadInitialData();
        await switchTab('dashboard');
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Lỗi', text: err.message });
    }
}

async function handleResetDemoData() {
    const resConfirm = await Swal.fire({
        title: 'Nạp lại toàn bộ dữ liệu mẫu?',
        text: 'Hệ thống sẽ reset và thiết lập lại các thiết bị, giáo viên, phòng chức năng mô phỏng.',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Đồng ý reset dữ liệu mẫu',
        cancelButtonText: 'Hủy'
    });
    if (!resConfirm.isConfirmed) return;

    try {
        const res = await fetch('/api/reset-demo', { method: 'POST' });
        const data = await res.json();
        if (!res.ok) {
            Swal.fire({ icon: 'error', title: 'Lỗi', text: data.error });
            return;
        }
        Swal.fire({ icon: 'success', title: 'Hoàn tất', text: data.message, timer: 1500, showConfirmButton: false });
        await loadInitialData();
        await switchTab('dashboard');
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Lỗi', text: err.message });
    }
}

// ==================== TIỆN ÍCH CHUNG ====================
function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
        lucide.createIcons();
    }
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    }
}

function formatCurrency(amount) {
    if (!amount) return '0 đ';
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount);
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    try {
        const parts = dateStr.split('-');
        if (parts.length === 3) {
            return `${parts[2]}/${parts[1]}/${parts[0]}`;
        }
    } catch (e) {}
    return dateStr;
}

function getFormattedTimestamp() {
    const now = new Date();
    return `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`;
}
