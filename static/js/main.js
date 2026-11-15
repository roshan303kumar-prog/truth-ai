/**
 * TRUTH AI — Core Client Script
 * Verify. Analyze. Trust.
 */

document.addEventListener("DOMContentLoaded", () => {
    // Auto-dismiss standard alerts after 5 seconds
    const alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach((alert) => {
        setTimeout(() => {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (e) {}
        }, 5000);
    });
});

/**
 * Universal Verdict Badge Class Resolver
 */
function getBadgeClass(verdict) {
    if (!verdict) return "badge-insufficient";
    if (verdict.includes("Supported")) return "badge-supported";
    if (verdict.includes("False")) return "badge-false";
    if (verdict.includes("Misleading")) return "badge-misleading";
    if (verdict.includes("Unverified")) return "badge-unverified";
    return "badge-insufficient";
}

/**
 * Universal Verdict Icon Resolver
 */
function getVerdictIcon(verdict) {
    if (!verdict) return "fa-circle-info";
    if (verdict.includes("Supported")) return "fa-circle-check";
    if (verdict.includes("False")) return "fa-circle-xmark";
    if (verdict.includes("Misleading")) return "fa-triangle-exclamation";
    if (verdict.includes("Unverified")) return "fa-circle-question";
    return "fa-circle-info";
}

/**
 * Safe HTML Escaping Helper
 */
function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

/**
 * Global helper to toggle report bookmark/save status
 */
async function toggleBookmark(reportId, btnElement) {
    try {
        const response = await fetch(`/api/report/${reportId}/bookmark`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
        });

        if (response.status === 401) {
            window.location.href = "/login?next=" + encodeURIComponent(window.location.pathname);
            return;
        }

        const data = await response.json();
        if (data.success) {
            const icon = btnElement.querySelector("i");
            if (data.is_saved) {
                icon.classList.remove("fa-regular");
                icon.classList.add("fa-solid");
                btnElement.classList.add("text-warning");
            } else {
                icon.classList.remove("fa-solid");
                icon.classList.add("fa-regular");
                btnElement.classList.remove("text-warning");
            }
        }
    } catch (err) {
        console.error("Failed to toggle bookmark:", err);
    }
}

/**
 * Global helper to delete a report
 */
async function deleteReport(reportId, redirectAfter = false) {
    if (!confirm("Are you sure you want to delete this verification report?")) {
        return;
    }

    try {
        const response = await fetch(`/api/report/${reportId}`, {
            method: "DELETE",
        });

        if (response.ok) {
            if (redirectAfter) {
                window.location.href = "/history";
            } else {
                const row = document.getElementById(`report-row-${reportId}`);
                if (row) row.remove();
            }
        } else {
            alert("Could not delete report. Please ensure you are logged in as the report owner.");
        }
    } catch (err) {
        console.error("Error deleting report:", err);
    }
}

/**
 * Copy current page URL to clipboard
 */
function copyShareLink(url) {
    const link = url || window.location.href;
    navigator.clipboard.writeText(link).then(() => {
        alert("Verification report link copied to clipboard!");
    }).catch(() => {
        prompt("Copy this report link:", link);
    });
}
