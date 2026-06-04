// N-Assist Interactive Calendar Planner

document.addEventListener("DOMContentLoaded", () => {
    initCalendar();
});

let calendarTasks = [];
let calendarDate = new Date(); // Track currently viewed month/year
let selectedDateKey = null; // Store formatted date key of currently selected cell

async function initCalendar() {
    setupControls();
    await loadCalendarTasks();
}

async function loadCalendarTasks() {
    try {
        const res = await fetch('/api/tasks');
        calendarTasks = await res.json();
        renderCalendar();
    } catch (err) {
        console.error("Error loading calendar events:", err);
        showToast("Failed to fetch calendar tasks.", "error");
    }
}

function setupControls() {
    const prev = document.getElementById("prevMonthBtn");
    const next = document.getElementById("nextMonthBtn");
    
    if (prev && next) {
        prev.addEventListener("click", () => {
            calendarDate.setMonth(calendarDate.getMonth() - 1);
            renderCalendar();
        });
        
        next.addEventListener("click", () => {
            calendarDate.setMonth(calendarDate.getMonth() + 1);
            renderCalendar();
        });
    }
}

function renderCalendar() {
    const grid = document.getElementById("calendarDaysGrid");
    const title = document.getElementById("calendarMonthTitle");
    if (!grid || !title) return;
    
    grid.innerHTML = "";
    
    const year = calendarDate.getFullYear();
    const month = calendarDate.getMonth();
    
    // Set title e.g. "June 2026"
    const monthName = calendarDate.toLocaleString('default', { month: 'long' });
    title.innerText = `${monthName} ${year}`;
    
    // Day logic
    const firstDayIndex = new Date(year, month, 1).getDay();
    const numDays = new Date(year, month + 1, 0).getDate();
    const prevNumDays = new Date(year, month, 0).getDate();
    
    const today = new Date();
    
    // 1. Render padding cells from previous month
    for (let x = firstDayIndex; x > 0; x--) {
        const prevDay = prevNumDays - x + 1;
        const block = document.createElement("div");
        block.className = "calendar-day-block inactive";
        block.innerHTML = `<span class="calendar-day-num">${prevDay}</span>`;
        grid.appendChild(block);
    }
    
    // 2. Render actual month days
    for (let day = 1; day <= numDays; day++) {
        const dateObj = new Date(year, month, day);
        const dateKey = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        
        // Filter tasks due on this calendar date (UTC-based check)
        const dayTasks = calendarTasks.filter(task => {
            const taskDate = new Date(task.deadline);
            return taskDate.getFullYear() === year &&
                   taskDate.getMonth() === month &&
                   taskDate.getDate() === day;
        });
        
        const block = document.createElement("div");
        block.className = "calendar-day-block";
        
        // Is it today?
        const isToday = today.getFullYear() === year &&
                        today.getMonth() === month &&
                        today.getDate() === day;
        if (isToday) {
            block.classList.add("today");
        }
        
        if (selectedDateKey === dateKey) {
            block.classList.add("active-selected");
        }
        
        block.innerHTML = `<span class="calendar-day-num">${day}</span>`;
        
        // Render priority colored dot indicators
        if (dayTasks.length > 0) {
            const indicators = document.createElement("div");
            indicators.className = "day-indicators";
            
            // Map color counts
            let highCount = 0;
            let medCount = 0;
            let lowCount = 0;
            let compCount = 0;
            
            dayTasks.forEach(t => {
                if (t.status === "Completed") compCount++;
                else if (t.priority === "High") highCount++;
                else if (t.priority === "Medium") medCount++;
                else if (t.priority === "Low") lowCount++;
            });
            
            if (highCount > 0) indicators.innerHTML += `<span class="dot-indicator dot-high" title="${highCount} High Priority"></span>`;
            if (medCount > 0) indicators.innerHTML += `<span class="dot-indicator dot-med" title="${medCount} Medium Priority"></span>`;
            if (lowCount > 0) indicators.innerHTML += `<span class="dot-indicator dot-low" title="${lowCount} Low Priority"></span>`;
            if (compCount > 0) indicators.innerHTML += `<span class="dot-indicator dot-completed" title="${compCount} Completed"></span>`;
            
            block.appendChild(indicators);
        }
        
        // Click listener to load sidebar details
        block.addEventListener("click", () => {
            // Remove previous selections
            document.querySelectorAll(".calendar-day-block").forEach(b => b.classList.remove("active-selected"));
            block.classList.add("active-selected");
            selectedDateKey = dateKey;
            
            showDayDetails(dateObj, dayTasks);
        });
        
        grid.appendChild(block);
    }
    
    // Pad remaining space of calendar grid to maintain grid format if necessary
    const totalCells = firstDayIndex + numDays;
    const remaining = 42 - totalCells;
    const nextMonthPadding = remaining >= 7 ? remaining - 7 : remaining; // Keep it clean to 35 or 42 grids
    
    for (let i = 1; i <= nextMonthPadding; i++) {
        const block = document.createElement("div");
        block.className = "calendar-day-block inactive";
        block.innerHTML = `<span class="calendar-day-num">${i}</span>`;
        grid.appendChild(block);
    }
    
    // Auto-load details for current day if present on calendar load
    if (selectedDateKey === null) {
        const todayTasks = calendarTasks.filter(task => {
            const taskDate = new Date(task.deadline);
            return taskDate.getFullYear() === today.getFullYear() &&
                   taskDate.getMonth() === today.getMonth() &&
                   taskDate.getDate() === today.getDate();
        });
        showDayDetails(today, todayTasks);
    } else {
        // Re-render selection tasks based on current loaded index if selected
        const parts = selectedDateKey.split("-");
        const selDate = new Date(parts[0], parts[1] - 1, parts[2]);
        const selTasks = calendarTasks.filter(task => {
            const taskDate = new Date(task.deadline);
            return taskDate.getFullYear() === selDate.getFullYear() &&
                   taskDate.getMonth() === selDate.getMonth() &&
                   taskDate.getDate() === selDate.getDate();
        });
        showDayDetails(selDate, selTasks);
    }
    
    if (window.lucide) {
        lucide.createIcons();
    }
}

function showDayDetails(date, tasks) {
    const badge = document.getElementById("selectedDateBadge");
    const container = document.getElementById("selectedDayTasksList");
    if (!badge || !container) return;
    
    const formattedDate = date.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
    badge.innerText = formattedDate;
    
    if (tasks.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i data-lucide="check-circle" class="success-icon"></i>
                <p>No deadlines scheduled for this day.</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }
    
    container.innerHTML = "";
    tasks.forEach(task => {
        const isCompleted = task.status === "Completed";
        const isOverdue = task.is_overdue;
        
        let borderClass = `border-${task.priority.toLowerCase()}`;
        let statusText = "Pending";
        
        if (isCompleted) {
            borderClass = 'border-completed';
            statusText = "Completed";
        } else if (isOverdue) {
            borderClass = 'border-overdue';
            statusText = "Overdue";
        }
        
        const item = document.createElement("div");
        item.className = `calendar-task-item glass-panel ${borderClass}`;
        
        const dateObj = new Date(task.deadline);
        const timeStr = dateObj.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
        
        item.innerHTML = `
            <h5 class="${isCompleted ? 'line-through' : ''}">${escapeHTML(task.title)}</h5>
            <p><strong>Category:</strong> ${task.category}</p>
            <p><strong>Time:</strong> ${timeStr}</p>
            <p><strong>Priority:</strong> ${task.priority} | <strong>Status:</strong> ${statusText}</p>
        `;
        container.appendChild(item);
    });
    lucide.createIcons();
}
