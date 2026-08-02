// app.js

/**
 * Toggle the visibility of the Add Expense form
 */
function toggleExpenseForm() {
    const formWrap = document.getElementById('expense-form-wrap');
    if (!formWrap) return;
    
    if (formWrap.style.display === 'none') {
        formWrap.style.display = 'block';
        // Scroll into view gently
        formWrap.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else {
        formWrap.style.display = 'none';
    }
}

/**
 * Handle custom split selection checkbox area display
 * @param {string} val - Select value ('equal' or 'custom')
 */
function toggleCustomSplit(val) {
    const customSplitDiv = document.getElementById('custom-split');
    if (!customSplitDiv) return;
    
    if (val === 'custom') {
        customSplitDiv.style.display = 'flex';
        // Auto check all checkboxes by default on first switch
        const checkboxes = customSplitDiv.querySelectorAll('input[type="checkbox"]');
        let anyChecked = Array.from(checkboxes).some(cb => cb.checked);
        if (!anyChecked) {
            checkboxes.forEach(cb => cb.checked = true);
        }
    } else {
        customSplitDiv.style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Render balance bars dynamically to satisfy IDE validation and avoid inline styles
    document.querySelectorAll('.balance-bar').forEach(bar => {
        const pct = bar.getAttribute('data-pct');
        if (pct) {
            bar.style.width = pct + '%';
        }
    });

    const codeBadge = document.getElementById('group-code-badge');
    if (codeBadge) {
        codeBadge.addEventListener('click', async () => {
            const codeText = codeBadge.querySelector('span').innerText.trim();
            
            try {
                await navigator.clipboard.writeText(codeText);
                showToast("Copied group code to clipboard!", "success");
            } catch (err) {
                showToast("Could not copy code. Please copy manually.", "error");
            }
        });
    }

    // Auto-fade flash messages after 5 seconds
    const flashContainer = document.getElementById('flash-container');
    if (flashContainer) {
        setTimeout(() => {
            const messages = flashContainer.querySelectorAll('.flash-msg');
            messages.forEach(msg => {
                msg.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
                msg.style.opacity = '0';
                msg.style.transform = 'translateY(-10px)';
                setTimeout(() => msg.remove(), 500);
            });
        }, 5000);
    }
});

/**
 * Dynamic toast generator for visual feedback
 * @param {string} message 
 * @param {'success' | 'error' | 'info'} type 
 */
function showToast(message, type = 'success') {
    let container = document.getElementById('flash-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'flash-container';
        container.className = 'flash-container';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `flash-msg flash-${type}`;
    toast.role = 'alert';
    
    toast.innerHTML = `
        <span>${message}</span>
        <button class="flash-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    
    container.appendChild(toast);
    
    // Auto-remove toast after 4 seconds
    setTimeout(() => {
        toast.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-10px)';
        setTimeout(() => toast.remove(), 500);
    }, 4000);
}
