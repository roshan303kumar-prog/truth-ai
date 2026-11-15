/**
 * TRUTH AI — Dashboard Client Controller
 * Visualizes user verification metrics via Chart.js
 */

document.addEventListener("DOMContentLoaded", async () => {
    const outcomeCanvas = document.getElementById("outcomeChart");
    const modalityCanvas = document.getElementById("modalityChart");

    if (!outcomeCanvas && !modalityCanvas) return;

    try {
        const response = await fetch("/api/dashboard");
        if (!response.ok) return;

        const data = await response.json();
        if (!data.success) return;

        const metrics = data.metrics || {};
        const types = data.type_breakdown || {};

        // 1. Outcome Doughnut Chart
        if (outcomeCanvas) {
            new Chart(outcomeCanvas, {
                type: "doughnut",
                data: {
                    labels: ["Supported", "Contradicted", "Misleading", "Unverified", "Insufficient"],
                    datasets: [{
                        data: [
                            metrics.supported || 0,
                            metrics.contradicted || 0,
                            metrics.misleading || 0,
                            metrics.unverified || 0,
                            metrics.insufficient || 0,
                        ],
                        backgroundColor: [
                            "#10b981", // Supported
                            "#ef4444", // Contradicted
                            "#f59e0b", // Misleading
                            "#00e5ff", // Unverified
                            "#94a3b8", // Insufficient
                        ],
                        borderWidth: 2,
                        borderColor: "#0c1322",
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: "bottom",
                            labels: {
                                color: "#94a3b8",
                                font: { family: "Inter", size: 12 },
                                padding: 15,
                            }
                        }
                    },
                    cutout: "70%",
                }
            });
        }

        // 2. Modality Bar Chart
        if (modalityCanvas) {
            new Chart(modalityCanvas, {
                type: "bar",
                data: {
                    labels: ["News & Claims", "Photographs", "Videos"],
                    datasets: [{
                        label: "Verifications Completed",
                        data: [
                            types.news || 0,
                            types.image || 0,
                            types.video || 0,
                        ],
                        backgroundColor: [
                            "rgba(59, 130, 246, 0.75)",
                            "rgba(0, 229, 255, 0.75)",
                            "rgba(99, 102, 241, 0.75)",
                        ],
                        borderColor: [
                            "#3b82f6",
                            "#00e5ff",
                            "#6366f1",
                        ],
                        borderWidth: 1,
                        borderRadius: 6,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { color: "#94a3b8", font: { family: "Inter" } }
                        },
                        y: {
                            beginAtZero: true,
                            grid: { color: "rgba(255, 255, 255, 0.05)" },
                            ticks: { color: "#94a3b8", precision: 0 }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }
    } catch (err) {
        console.error("Dashboard chart initialization error:", err);
    }
});
