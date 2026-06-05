// N-Assist Core Interactions Manager

document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initMobileSidebar();
    initAIChatDrawer();
    
    // Auto-create lucide icons on load
    if (window.lucide) {
        lucide.createIcons();
    }
});

/* ==========================================================================
   THEME MANAGER
   ========================================================================== */

function initTheme() {
    const themeBtn = document.getElementById("themeToggleBtn");
    if (!themeBtn) return;
    
    const body = document.body;
    const cachedTheme = localStorage.getItem("theme") || "dark";
    
    // Set initial theme state
    if (cachedTheme === "light") {
        body.classList.add("light-theme");
        body.classList.remove("dark-theme");
    } else {
        body.classList.add("dark-theme");
        body.classList.remove("light-theme");
    }
    
    themeBtn.addEventListener("click", () => {
        if (body.classList.contains("light-theme")) {
            body.classList.remove("light-theme");
            body.classList.add("dark-theme");
            localStorage.setItem("theme", "dark");
        } else {
            body.classList.remove("dark-theme");
            body.classList.add("light-theme");
            localStorage.setItem("theme", "light");
        }
        if (window.lucide) {
            lucide.createIcons();
        }
    });
}

/* ==========================================================================
   MOBILE SIDEBAR TOGGLER
   ========================================================================== */

function initMobileSidebar() {
    const toggleBtn = document.getElementById("menuToggleBtn");
    const closeBtn = document.getElementById("closeSidebarBtn");
    const sidebar = document.getElementById("sidebar");
    
    if (!sidebar) return;
    
    if (toggleBtn) {
        toggleBtn.addEventListener("click", () => {
            sidebar.classList.add("active");
        });
    }
    
    if (closeBtn) {
        closeBtn.addEventListener("click", () => {
            sidebar.classList.remove("active");
        });
    }
    
    // Close sidebar if clicking main content area while open
    document.addEventListener("click", (e) => {
        if (window.innerWidth <= 768 && sidebar.classList.contains("active")) {
            if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
                sidebar.classList.remove("active");
            }
        }
    });
}

/* ==========================================================================
   TOAST NOTIFICATION ENGINE
   ========================================================================== */

function showToast(message, type = "success") {
    let container = document.querySelector(".toast-container");
    if (!container) {
        container = document.createElement("div");
        container.className = "toast-container";
        document.body.appendChild(container);
    }
    
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    
    const iconName = type === "success" ? "check-circle" : "alert-triangle";
    
    toast.innerHTML = `
        <i data-lucide="${iconName}"></i>
        <span>${escapeHTML(message)}</span>
    `;
    
    container.appendChild(toast);
    if (window.lucide) {
        lucide.createIcons();
    }
    
    // Fade out and remove
    setTimeout(() => {
        toast.style.transition = "opacity 0.5s, transform 0.5s";
        toast.style.opacity = "0";
        toast.style.transform = "translateY(10px)";
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

// Global exposure
window.showToast = showToast;

/* ==========================================================================
   UTILITY HELPER FUNCTIONS
   ========================================================================== */

function escapeHTML(str) {
    if (!str) return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

window.escapeHTML = escapeHTML;

/* ==========================================================================
   FLOATING AI ASSISTANT CHATBOT DRAWER
   ========================================================================== */

function initAIChatDrawer() {
    const bubble = document.getElementById("aiToggleBubble");
    const container = document.querySelector(".ai-widget-container");
    const closeBtn = document.querySelector(".bot-close-icon");
    const sendBtn = document.getElementById("aiDrawerSendBtn");
    const input = document.getElementById("aiDrawerInput");
    const messagesContainer = document.getElementById("aiDrawerMessages");
    
    if (!bubble || !container || !messagesContainer) return;
    
    // Toggle active state
    bubble.addEventListener("click", () => {
        container.classList.toggle("active");
        
        // Remove pulse indicator when chatbot is opened once
        const indicator = bubble.querySelector(".pulse-indicator");
        if (indicator) indicator.remove();
        
        // Auto focus input
        if (container.classList.contains("active")) {
            setTimeout(() => input.focus(), 300);
        }
    });

    // Sidebar AI Copilot nav item click
    const sidebarBtn = document.getElementById("aiSidebarNav");
    if (sidebarBtn) {
        sidebarBtn.addEventListener("click", (e) => {
            e.preventDefault();
            bubble.click();
        });
    }

    // Keyboard shortcuts
    document.addEventListener("keydown", (e) => {
        const active = document.activeElement;
        const isTyping = active && (active.tagName === "INPUT" || active.tagName === "TEXTAREA" || active.tagName === "SELECT" || active.contentEditable === "true");
        
        // '/' shortcut to open or focus
        if (e.key === "/" && !isTyping) {
            e.preventDefault();
            if (!container.classList.contains("active")) {
                bubble.click();
            } else {
                input.focus();
            }
        }
        
        // Alt+A shortcut to toggle
        if (e.altKey && e.key.toLowerCase() === "a") {
            e.preventDefault();
            bubble.click();
        }
    });

    // Close when clicking close widget inside header
    if (closeBtn) {
        closeBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            container.classList.remove("active");
        });
    }
    
    // Send action
    const sendMessage = async () => {
        const query = input.value.trim();
        if (!query) return;
        
        // Clear input
        input.value = "";
        
        // Append user bubble
        appendChatBubble(query, "user");
        
        // Add loading placeholder bubble
        const loadingId = "bot-loading-" + Date.now();
        const loadingBubble = document.createElement("div");
        loadingBubble.className = "ai-message bot loading";
        loadingBubble.id = loadingId;
        loadingBubble.innerHTML = `<span class="loading-dots">Thinking...</span>`;
        messagesContainer.appendChild(loadingBubble);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        try {
            const res = await fetch("/api/ai/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: query })
            });
            
            // Remove loading bubble
            const loader = document.getElementById(loadingId);
            if (loader) loader.remove();
            
            if (res.ok) {
                const data = await res.json();
                appendChatBubble(data.response, "bot");
            } else {
                appendChatBubble("Sorry, I encountered an issue connecting to the prioritization database.", "bot");
            }
        } catch (err) {
            console.error("AI chat error:", err);
            const loader = document.getElementById(loadingId);
            if (loader) loader.remove();
            appendChatBubble("Network connection error. Please try again.", "bot");
        }
    };
    
    sendBtn.addEventListener("click", sendMessage);
    input.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            sendMessage();
        }
    });
}

function appendChatBubble(text, sender) {
    const container = document.getElementById("aiDrawerMessages");
    if (!container) return;
    
    const bubble = document.createElement("div");
    bubble.className = `ai-message ${sender}`;
    
    if (sender === "bot") {
        // AI sends formatted custom markdown back. Let's do a simple translation.
        bubble.innerHTML = translateSimpleMarkdown(text);
    } else {
        bubble.innerText = text;
    }
    
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
    if (window.lucide) {
        lucide.createIcons();
    }
}

function translateSimpleMarkdown(text) {
    // Escape HTML first to prevent XSS
    let escaped = escapeHTML(text);
    
    // Parse Headers: ### Header -> <h3>Header</h3>
    escaped = escaped.replace(/### (.*?)\n/g, "<h3>$1</h3>");
    escaped = escaped.replace(/### (.*?)$/g, "<h3>$1</h3>");
    
    // Parse Bold: **text** -> <strong>text</strong>
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    
    // Parse Bullet Lists: - Item -> <li>Item</li> inside a <ul>
    // To make it easy, we replace '- ' with list tag and handle structure
    let lines = escaped.split("\n");
    let inList = false;
    let newLines = [];
    
    lines.forEach(line => {
        let trimmed = line.trim();
        if (trimmed.startsWith("- ")) {
            if (!inList) {
                newLines.push("<ul>");
                inList = true;
            }
            newLines.push(`<li>${trimmed.substring(2)}</li>`);
        } else {
            if (inList) {
                newLines.push("</ul>");
                inList = false;
            }
            newLines.push(line);
        }
    });
    
    if (inList) {
        newLines.push("</ul>");
    }
    
    return newLines.join("<br>").replace(/<\/ul><br>/g, "</ul>").replace(/<br><ul>/g, "<ul>");
}
