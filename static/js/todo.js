// N-Assist To-Do Board Mechanics

document.addEventListener("DOMContentLoaded", () => {
    loadTodoTasks();
});

let todoTasks = [];

async function loadTodoTasks() {
    try {
        const res = await fetch('/api/tasks');
        todoTasks = await res.json();
        renderLanes();
    } catch (err) {
        console.error("Error loading Kanban tasks:", err);
        showToast("Failed to fetch To-Do tasks.", "error");
    }
}

function renderLanes() {
    const cardsToday = document.getElementById("cardsToday");
    const cardsUpcoming = document.getElementById("cardsUpcoming");
    const cardsCompleted = document.getElementById("cardsCompleted");
    
    if (!cardsToday || !cardsUpcoming || !cardsCompleted) return;
    
    // Clear content
    cardsToday.innerHTML = "";
    cardsUpcoming.innerHTML = "";
    cardsCompleted.innerHTML = "";
    
    let countToday = 0;
    let countUpcoming = 0;
    let countCompleted = 0;
    
    const now = new Date();
    
    // Start of tomorrow
    const startOfTomorrow = new Date(now.getFullYear(), now.month || now.getMonth(), now.getDate() + 1, 0, 0, 0);
    
    todoTasks.forEach(task => {
        const isCompleted = task.status === "Completed";
        const deadlineDate = new Date(task.deadline);
        const isOverdueOrToday = deadlineDate < startOfTomorrow;
        
        let targetLane;
        
        if (isCompleted) {
            targetLane = cardsCompleted;
            countCompleted++;
        } else if (isOverdueOrToday) {
            targetLane = cardsToday;
            countToday++;
        } else {
            targetLane = cardsUpcoming;
            countUpcoming++;
        }
        
        const card = createKanbanCard(task);
        targetLane.appendChild(card);
    });
    
    // Set counts
    document.getElementById("countToday").innerText = countToday;
    document.getElementById("countUpcoming").innerText = countUpcoming;
    document.getElementById("countCompleted").innerText = countCompleted;
    
    // Render placeholders if lanes are empty
    checkEmptyLane(cardsToday, "No tasks due today.");
    checkEmptyLane(cardsUpcoming, "No upcoming tasks.");
    checkEmptyLane(cardsCompleted, "No completed tasks yet.");
    
    if (window.lucide) {
        lucide.createIcons();
    }
}

function createKanbanCard(task) {
    const card = document.createElement("div");
    card.className = `kanban-card-item glass-panel border-${task.priority.toLowerCase()}`;
    
    if (task.status === "Completed") {
        card.className = "kanban-card-item glass-panel border-completed";
    }
    
    card.setAttribute("draggable", "true");
    card.setAttribute("id", `task-card-${task.id}`);
    card.addEventListener("dragstart", (e) => drag(e, task.id));
    card.addEventListener("dragend", dragEnd);
    
    const dateObj = new Date(task.deadline);
    const formattedDate = dateObj.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    
    const badgeClass = task.priority === 'High' ? 'badge-high' : task.priority === 'Medium' ? 'badge-med' : 'badge-low';
    const isCompleted = task.status === 'Completed';
    
    card.innerHTML = `
        <div class="kanban-card-title ${isCompleted ? 'line-through' : ''}">
            ${escapeHTML(task.title)}
        </div>
        <div class="kanban-card-meta">
            <span class="task-date"><i data-lucide="calendar"></i> ${formattedDate}</span>
            <span class="priority-badge ${badgeClass}">${task.priority}</span>
        </div>
    `;
    
    return card;
}

function checkEmptyLane(container, text) {
    if (container.children.length === 0) {
        container.innerHTML = `
            <div class="empty-lane-placeholder">
                <p>${text}</p>
            </div>
        `;
    }
}

/* ==========================================================================
   DRAG AND DROP HANDLERS
   ========================================================================== */

function drag(ev, taskId) {
    ev.dataTransfer.setData("text/plain", taskId);
    // Add dragging styling classes
    const card = document.getElementById(`task-card-${taskId}`);
    if (card) {
        setTimeout(() => card.classList.add("dragging"), 0);
    }
}

function dragEnd(ev) {
    ev.currentTarget.classList.remove("dragging");
}

function allowDrop(ev) {
    ev.preventDefault();
}

function dragEnter(ev) {
    ev.preventDefault();
    const column = ev.currentTarget;
    if (column.classList.contains("kanban-column")) {
        column.classList.add("drag-over");
    }
}

function dragLeave(ev) {
    const column = ev.currentTarget;
    if (column.classList.contains("kanban-column")) {
        column.classList.remove("drag-over");
    }
}

async function drop(ev, lane) {
    ev.preventDefault();
    const column = ev.currentTarget;
    if (column.classList.contains("kanban-column")) {
        column.classList.remove("drag-over");
    }
    
    const taskId = ev.dataTransfer.getData("text/plain");
    if (!taskId) return;
    
    const task = todoTasks.find(t => t.id == taskId);
    if (!task) return;
    
    // Construct task modifications based on targets
    let payload = {};
    let isModified = false;
    
    if (lane === "Completed" && task.status !== "Completed") {
        payload.status = "Completed";
        isModified = true;
    } else if (lane === "Today") {
        if (task.status === "Completed") {
            payload.status = "Pending";
        }
        
        // Check if task is already due today. If not, schedule for today at 23:59:59 local
        const todayEnd = new Date();
        todayEnd.setHours(23, 59, 59, 999);
        payload.deadline = todayEnd.toISOString();
        isModified = true;
        
    } else if (lane === "Upcoming") {
        if (task.status === "Completed") {
            payload.status = "Pending";
        }
        
        // If task is due today or overdue, push it to tomorrow at 18:00
        const deadlineDate = new Date(task.deadline);
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        tomorrow.setHours(18, 0, 0, 0);
        
        if (deadlineDate < tomorrow) {
            payload.deadline = tomorrow.toISOString();
        }
        isModified = true;
    }
    
    if (isModified) {
        try {
            const res = await fetch(`/api/tasks/${taskId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            
            if (res.ok) {
                showToast(`Task moved to ${lane}`, "success");
                loadTodoTasks();
            } else {
                showToast("Failed to move task.", "error");
            }
        } catch (err) {
            console.error(err);
            showToast("Connection error.", "error");
        }
    }
}

// Global exposure for HTML inline callbacks
window.allowDrop = allowDrop;
window.dragEnter = dragEnter;
window.dragLeave = dragLeave;
window.drop = drop;
