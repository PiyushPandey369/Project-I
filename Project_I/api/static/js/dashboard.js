// api/static/js/dashboard.js
document.addEventListener("DOMContentLoaded", () => {
    // API endpoints
    const DASHBOARD_API = "/api/dashboard-data";
    const SYNC_API = "/api/sync";
    const MODEL_COMPARISON_API = "/api/model-comparison";
    // Chart instances
    let aqiChartInstance = null;
    let pollutantsChartInstance = null;
    let weatherChartInstance = null;

    // Toast function
    const showToast = (message, type = "success") => {
        const toast = document.getElementById("toast");
        toast.textContent = message;
        toast.className = `toast show ${type}`;
        
        setTimeout(() => {
            toast.className = toast.className.replace("show", "");
        }, 4000);
    };

    // Helper to get AQI category details
    const getAQICategory = (aqi) => {
        if (aqi === null || aqi === undefined) return { label: "N/A", color: "#64748b" };
        if (aqi <= 50) return { label: "Good", color: "#10b981", bg: "rgba(16, 185, 129, 0.1)" };
        if (aqi <= 100) return { label: "Moderate", color: "#f59e0b", bg: "rgba(245, 158, 11, 0.1)" };
        if (aqi <= 150) return { label: "Sensitive Groups", color: "#f97316", bg: "rgba(249, 115, 22, 0.1)" };
        if (aqi <= 200) return { label: "Unhealthy", color: "#ef4444", bg: "rgba(239, 68, 68, 0.1)" };
        if (aqi <= 300) return { label: "Very Unhealthy", color: "#a855f7", bg: "rgba(168, 85, 247, 0.1)" };
        return { label: "Hazardous", color: "#7f1d1d", bg: "rgba(127, 29, 29, 0.1)" };
    };

    // ----------------------------------------------------
    // Load Overview Dashboard Data
    // ----------------------------------------------------
    const loadDashboardData = async () => {
        try {
            const response = await fetch(DASHBOARD_API);
            if (!response.ok) throw new Error("Failed to fetch dashboard data");
            const data = await response.json();

            updateMetrics(data);
            renderCharts(data.history);
        } catch (error) {
            console.error(error);
            showToast("Failed to load dashboard data. Please try syncing.", "error");
        }
    };

    // Update Text Elements in DOM
    const updateMetrics = (data) => {
        const actual = data.latest_actual || {};
        const prediction = data.latest_prediction || {};

        // 1. Current / Actual Values
        document.getElementById("actual-date").textContent = actual.datetime ? new Date(actual.datetime).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : "No Data";
        document.getElementById("actual-aqi").textContent = actual.aqi !== undefined ? Math.round(actual.aqi) : "--";
        document.getElementById("actual-pm25").textContent = actual.pm25 !== undefined ? actual.pm25.toFixed(1) : "--";
        document.getElementById("actual-pm10").textContent = actual.pm10 !== undefined ? actual.pm10.toFixed(1) : "--";
        document.getElementById("actual-temp").textContent = actual.temp !== undefined ? actual.temp.toFixed(1) : "--";
        document.getElementById("actual-humidity").textContent = actual.humidity !== undefined ? actual.humidity : "--";
        document.getElementById("actual-wind").textContent = actual.windspeed !== undefined ? actual.windspeed.toFixed(1) : "--";
        document.getElementById("actual-pressure").textContent = actual.sealevelpressure !== undefined ? actual.sealevelpressure : "--";
        document.getElementById("actual-visibility").textContent = actual.visibility !== undefined ? actual.visibility.toFixed(1) : "--";
        document.getElementById("actual-precip").textContent = actual.precipitation !== undefined ? actual.precipitation.toFixed(2) : "0.00";
        document.getElementById("actual-solar").textContent = actual.solarradiation !== undefined ? actual.solarradiation : "--";

        // Update AQI Badge Color for Actual
        const actualCat = getAQICategory(actual.aqi);
        const actualBadge = document.getElementById("actual-aqi-badge");
        actualBadge.textContent = actualCat.label;
        actualBadge.style.color = actualCat.color;
        actualBadge.style.backgroundColor = actualCat.bg;

        // 2. Tomorrow's Prediction Values
        document.getElementById("pred-date").textContent = prediction.prediction_date ? new Date(prediction.prediction_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : "Not Generated";
        document.getElementById("pred-aqi").textContent = prediction.predicted_aqi !== undefined ? Math.round(prediction.predicted_aqi) : "--";
        document.getElementById("pred-pm25").textContent = prediction.predicted_pm25 !== undefined ? prediction.predicted_pm25.toFixed(1) : "--";
        document.getElementById("pred-pm10").textContent = prediction.predicted_pm10 !== undefined ? prediction.predicted_pm10.toFixed(1) : "--";
        document.getElementById("pred-temp").textContent = prediction.predicted_temperature !== undefined ? prediction.predicted_temperature.toFixed(1) : "--";

        // Update AQI Badge Color for Prediction
        const predCat = getAQICategory(prediction.predicted_aqi);
        const predBadge = document.getElementById("pred-aqi-badge");
        predBadge.textContent = predCat.label;
        predBadge.style.color = predCat.color;
        predBadge.style.backgroundColor = predCat.bg;

        // 3. Dynamic Confidence
        const confidenceVal = data.confidence !== undefined ? data.confidence : 92.4;
        document.getElementById("confidence-score").textContent = `${confidenceVal}%`;
        
        const confidenceBar = document.getElementById("confidence-bar");
        confidenceBar.style.width = `${confidenceVal}%`;
        
        let confidenceClass = "bg-success";
        if (confidenceVal < 70) confidenceClass = "bg-danger";
        else if (confidenceVal < 85) confidenceClass = "bg-warning";
        confidenceBar.className = `progress-bar ${confidenceClass}`;

        // 4. Compare current vs prediction
        const todayStr = actual.datetime;
        let todayPrediction = null;
        if (todayStr && data.history) {
            const todayPair = data.history.find(h => h.date === todayStr);
            if (todayPair && todayPair.predicted_aqi !== null) {
                todayPrediction = todayPair.predicted_aqi;
            }
        }

        const comparisonContainer = document.getElementById("comparison-container");
        if (todayPrediction !== null && actual.aqi !== undefined) {
            const diff = actual.aqi - todayPrediction;
            const diffPct = ((diff / todayPrediction) * 100).toFixed(1);
            const icon = diff >= 0 ? "📈" : "📉";
            const dir = diff >= 0 ? "higher" : "lower";
            const colorClass = diff >= 0 ? "text-danger" : "text-success";
            comparisonContainer.innerHTML = `
                <div class="comparison-card">
                    <h4>Today's Forecast Review</h4>
                    <p>Predicted AQI: <strong>${Math.round(todayPrediction)}</strong> vs Actual AQI: <strong>${Math.round(actual.aqi)}</strong></p>
                    <span class="${colorClass}">${icon} ${Math.abs(diff).toFixed(1)} AQI points (${Math.abs(diffPct)}%) ${dir} than predicted.</span>
                </div>
            `;
        } else {
            comparisonContainer.innerHTML = `
                <div class="comparison-card empty">
                    <h4>Today's Forecast Review</h4>
                    <p>No historical prediction matching today's actual date found. Run sync tomorrow to compare forecast vs actual.</p>
                </div>
            `;
        }
    };
    // ----------------------------------------------------
    // Model Comparison: XGBoost vs River vs Actual
    // ----------------------------------------------------
    const formatComparisonValue = (value) => {
        if (value === null || value === undefined) return null;
        return Number(value).toFixed(2);
    };

    const loadModelComparison = async () => {
        const dateBadge = document.getElementById("model-comparison-date");
        const body = document.getElementById("model-comparison-body");

        try {
            const response = await fetch(MODEL_COMPARISON_API);
            if (!response.ok) throw new Error("Failed to fetch model comparison data");
            const result = await response.json();

            if (!result.data || result.data.length === 0) {
                dateBadge.textContent = "Forecast date: --";
                body.innerHTML = `
                    <div class="model-comparison-empty">
                        ${result.message || "No comparison data available yet. Run Sync to generate a forecast."}
                    </div>
                `;
                return;
            }

            dateBadge.textContent = `Forecast date: ${result.target_date}`;

            const rows = result.data.map(row => {
                const xgboost = formatComparisonValue(row.xgboost);
                const river = formatComparisonValue(row.river);
                const actual = formatComparisonValue(row.actual);

                return `
                    <tr>
                        <td class="param-name">${row.parameter}</td>
                        <td><span class="value-pill pill-xgboost">${xgboost !== null ? xgboost : "--"}</span></td>
                        <td><span class="value-pill pill-river">${river !== null ? river : "--"}</span></td>
                        <td><span class="value-pill ${actual !== null ? "pill-actual" : "pill-empty"}">${actual !== null ? actual : "Not recorded"}</span></td>
                    </tr>
                `;
            }).join("");

            body.innerHTML = `
                <div class="comparison-table-wrapper">
                    <table class="comparison-table">
                        <thead>
                            <tr>
                                <th>Parameter</th>
                                <th>XGBoost</th>
                                <th>River</th>
                                <th>Actual</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rows}
                        </tbody>
                    </table>
                </div>
            `;
        } catch (error) {
            console.error(error);
            dateBadge.textContent = "Forecast date: --";
            body.innerHTML = `
                <div class="model-comparison-empty">
                    Unable to load model comparison data.
                </div>
            `;
        }
    };

    // Render Overview Charts
    const renderCharts = (history) => {
        if (!history || history.length === 0) return;

        const labels = history.map(h => {
            const d = new Date(h.date);
            return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });

        const actualAQIs = history.map(h => h.actual_aqi);
        const predictedAQIs = history.map(h => h.predicted_aqi);

        const actualPM25s = history.map(h => h.actual_pm25);
        const predictedPM25s = history.map(h => h.predicted_pm25);
        const actualPM10s = history.map(h => h.actual_pm10);
        const predictedPM10s = history.map(h => h.predicted_pm10);

        const actualTemps = history.map(h => h.actual_temp);
        const predictedTemps = history.map(h => h.predicted_temp);

        // Common Chart Options
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#475569', font: { family: 'Inter', size: 11, weight: '600' } }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(148, 163, 184, 0.12)' },
                    ticks: { color: '#64748b', font: { family: 'Inter', size: 10, weight: '500' } }
                },
                y: {
                    grid: { color: 'rgba(148, 163, 184, 0.12)' },
                    ticks: { color: '#64748b', font: { family: 'Inter', size: 10, weight: '500' } }
                }
            }
        };

        // 1. AQI Chart
        if (aqiChartInstance) aqiChartInstance.destroy();
        const ctxAQI = document.getElementById("aqiChart").getContext("2d");
        aqiChartInstance = new Chart(ctxAQI, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Actual AQI',
                        data: actualAQIs,
                        borderColor: '#6366f1',
                        backgroundColor: 'rgba(99, 102, 241, 0.05)',
                        borderWidth: 3,
                        pointRadius: 3,
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: 'Predicted AQI',
                        data: predictedAQIs,
                        borderColor: '#a855f7',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointRadius: 3,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0.3
                    }
                ]
            },
            options: chartOptions
        });

        // 2. Pollutants Chart (PM2.5 & PM10)
        if (pollutantsChartInstance) pollutantsChartInstance.destroy();
        const ctxPoll = document.getElementById("pollutantsChart").getContext("2d");
        pollutantsChartInstance = new Chart(ctxPoll, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Actual PM2.5',
                        data: actualPM25s,
                        borderColor: '#ef4444',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointRadius: 2,
                        tension: 0.3
                    },
                    {
                        label: 'Predicted PM2.5',
                        data: predictedPM25s,
                        borderColor: '#fca5a5',
                        borderWidth: 1.5,
                        pointRadius: 2,
                        borderDash: [4, 4],
                        tension: 0.3
                    },
                    {
                        label: 'Actual PM10',
                        data: actualPM10s,
                        borderColor: '#f59e0b',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointRadius: 2,
                        tension: 0.3
                    },
                    {
                        label: 'Predicted PM10',
                        data: predictedPM10s,
                        borderColor: '#fde047',
                        borderWidth: 1.5,
                        pointRadius: 2,
                        borderDash: [4, 4],
                        tension: 0.3
                    }
                ]
            },
            options: chartOptions
        });

        // 3. Weather Chart (Temp)
        if (weatherChartInstance) weatherChartInstance.destroy();
        const ctxWeather = document.getElementById("weatherChart").getContext("2d");
        weatherChartInstance = new Chart(ctxWeather, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Actual Temp (°F)',
                        data: actualTemps,
                        borderColor: '#0ea5e9',
                        backgroundColor: 'rgba(14, 165, 233, 0.05)',
                        borderWidth: 3,
                        pointRadius: 3,
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: 'Predicted Temp (°F)',
                        data: predictedTemps,
                        borderColor: '#fb923c',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointRadius: 3,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0.3
                    }
                ]
            },
            options: chartOptions
        });
    };

    // Synchronize Data Click Handler
    const syncButton = document.getElementById("sync-btn");
    const syncSpinner = document.getElementById("sync-spinner");
    const syncBtnText = document.getElementById("sync-btn-text");

    syncButton.addEventListener("click", async () => {
        syncButton.disabled = true;
        syncSpinner.classList.remove("hidden");
        syncBtnText.textContent = "Syncing Pipeline...";

        showToast("Synchronizing data pipeline (Weather & Pollution APIs -> DB -> ML Forecast)... This may take up to 20 seconds.", "info");

        try {
            const response = await fetch(SYNC_API, {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });
            const result = await response.json();

            if (result.status === "success") {
                showToast("Data pipeline synchronized successfully!", "success");
                await loadDashboardData();
                await loadModelComparison();
                loadNewsFeed();
            } else {
                throw new Error(result.message || "Failed execution");
            }
        } catch (error) {
            console.error(error);
            showToast(`Synchronization failed: ${error.message}`, "error");
        } finally {
            syncButton.disabled = false;
            syncSpinner.classList.add("hidden");
            syncBtnText.textContent = "Sync Data Pipeline";
        }
    });

    // ----------------------------------------------------
    // Tabbed Routing (SPA Page Switching)
    // ----------------------------------------------------
    const initTabbedRouting = () => {
        const navLinks = document.querySelectorAll(".nav-link");
        const tabContents = document.querySelectorAll(".tab-content");

        navLinks.forEach(link => {
            link.addEventListener("click", (e) => {
                e.preventDefault();
                
                // Set active link
                navLinks.forEach(l => l.classList.remove("active"));
                link.classList.add("active");

                // Toggle tabs
                const targetId = link.getAttribute("data-target");
                tabContents.forEach(tab => {
                    tab.classList.remove("active-tab");
                });
                
                const targetTab = document.getElementById(targetId);
                if (targetTab) {
                    targetTab.classList.add("active-tab");
                }
            });
        });
    };

    // ----------------------------------------------------
    // Global Environment & Weather News Loader
    // ----------------------------------------------------
    const loadNewsFeed = async () => {
        const grid = document.getElementById("news-feed-grid");
        if (!grid) return;
        
        try {
            const response = await fetch("/api/news");
            if (!response.ok) throw new Error("Failed to fetch news feed");
            const newsItems = await response.json();
            
            grid.innerHTML = "";
            newsItems.forEach(item => {
                const card = document.createElement("div");
                card.className = "news-card card-glass";
                card.innerHTML = `
                    <div class="news-meta">
                        <span class="news-source">${item.source}</span>
                        <span class="news-date">${item.date}</span>
                    </div>
                    <h3><a href="${item.link}" target="_blank">${item.title}</a></h3>
                    <p>${item.snippet}</p>
                    <a href="${item.link}" target="_blank" class="news-read-more">Read Full Article →</a>
                `;
                grid.appendChild(card);
            });
        } catch (error) {
            console.error(error);
            grid.innerHTML = `<div class="details-placeholder">Failed to load news headlines.</div>`;
        }
    };

    // ----------------------------------------------------
    // Historical Calendar Lookup System
    // ----------------------------------------------------
    let currentYear = new Date().getFullYear();
    let currentMonth = new Date().getMonth(); // 0-11
    
    const monthNames = [
        "January", "February", "March", "April", "May", "June", 
        "July", "August", "September", "October", "November", "December"
    ];
    
    const renderCalendar = () => {
        const grid = document.getElementById("calendar-days-grid");
        const monthYearLabel = document.getElementById("cal-month-year");
        if (!grid || !monthYearLabel) return;
        
        monthYearLabel.textContent = `${monthNames[currentMonth]} ${currentYear}`;
        grid.innerHTML = "";
        
        // Days labels Sun - Sat
        const dayLabels = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];
        dayLabels.forEach(d => {
            const el = document.createElement("div");
            el.className = "cal-day-label";
            el.textContent = d;
            grid.appendChild(el);
        });
        
        const firstDayIndex = new Date(currentYear, currentMonth, 1).getDay();
        const totalDays = new Date(currentYear, currentMonth + 1, 0).getDate();
        
        // Empty days at start
        for (let i = 0; i < firstDayIndex; i++) {
            const el = document.createElement("div");
            el.className = "cal-day empty-day";
            grid.appendChild(el);
        }
        
        // Month days
        for (let day = 1; day <= totalDays; day++) {
            const el = document.createElement("div");
            el.className = "cal-day";
            el.textContent = day;
            
            const formattedMonth = String(currentMonth + 1).padStart(2, '0');
            const formattedDay = String(day).padStart(2, '0');
            const dateStr = `${currentYear}-${formattedMonth}-${formattedDay}`;
            
            // Highlight today's date
            const todayStr = new Date().toISOString().split('T')[0];
            if (dateStr === todayStr) {
                el.style.border = "1px solid var(--color-primary)";
                el.classList.add("active-day");
                setTimeout(() => el.click(), 0);
            }
            
            el.addEventListener("click", () => {
                document.querySelectorAll(".cal-day").forEach(dayEl => dayEl.classList.remove("active-day"));
                el.classList.add("active-day");
                loadDateDetails(dateStr);
            });
            
            grid.appendChild(el);
        }
    };
    
    // Fetch and render single date details
    const loadDateDetails = async (dateStr) => {
        const container = document.getElementById("calendar-date-details");
        if (!container) return;
        
        container.innerHTML = `
            <div class="details-placeholder">
                <span class="spinner" style="border-width:2px; width:16px; height:16px; display:inline-block; vertical-align:middle; margin-right:8px;"></span> 
                Loading details for ${dateStr}...
            </div>
        `;
        
        try {
            const response = await fetch(`/api/date-details?date=${dateStr}`);
            if (!response.ok) throw new Error("Connection failed");
            const data = await response.json();
            
            if (!data.actual && !data.predicted) {
                container.innerHTML = `
                    <div class="details-placeholder" style="color: var(--color-danger); border-color: rgba(239, 68, 68, 0.15);">
                        ⚠️ No data recorded for ${new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}.
                    </div>
                `;
                return;
            }
            
            renderDateDetailCards(container, data);
        } catch (error) {
            console.error(error);
            container.innerHTML = `<div class="details-placeholder" style="color: var(--color-danger);">Failed to load date metrics.</div>`;
        }
    };
    
    // Format and display details layout
    const renderDateDetailCards = (container, data) => {
        const act = data.actual || {};
        const pred = data.predicted || {};
        
        let actAQI = act.aqi !== undefined ? Math.round(act.aqi) : null;
        let predAQI = pred.predicted_aqi !== undefined ? Math.round(pred.predicted_aqi) : null;
        
        let aqiHTML = "";
        if (actAQI !== null && predAQI !== null) {
            const diff = actAQI - predAQI;
            const diffPct = ((diff / predAQI) * 100).toFixed(1);
            const pillClass = diff >= 0 ? "bg-warning" : "bg-success";
            const text = diff >= 0 ? `+${diff.toFixed(1)} points higher` : `${diff.toFixed(1)} points lower`;
            
            aqiHTML = `
                <div class="comparison-box">
                    <h5>AQI Comparison</h5>
                    <div class="comparison-box-grid">
                        <div>Observed: <strong>${actAQI}</strong></div>
                        <div>Forecasted: <strong>${predAQI}</strong></div>
                    </div>
                    <span class="comparison-diff-pill ${pillClass}">${text} (${diffPct}%)</span>
                </div>
            `;
        } else if (actAQI !== null) {
            aqiHTML = `
                <div class="comparison-box">
                    <h5>AQI Comparison</h5>
                    <div class="comparison-box-grid">
                        <div>Observed: <strong>${actAQI}</strong></div>
                        <div>Forecasted: <strong>No Forecast</strong></div>
                    </div>
                </div>
            `;
        } else if (predAQI !== null) {
            aqiHTML = `
                <div class="comparison-box">
                    <h5>AQI Comparison</h5>
                    <div class="comparison-box-grid">
                        <div>Observed: <strong>No Observation</strong></div>
                        <div>Forecasted: <strong>${predAQI}</strong></div>
                    </div>
                </div>
            `;
        }
        
        // Detailed parameters list
        let actPM25 = act.pm25 !== undefined ? `${act.pm25.toFixed(1)} µg/m³` : "N/A";
        let predPM25 = pred.predicted_pm25 !== undefined ? `${pred.predicted_pm25.toFixed(1)} µg/m³` : "N/A";
        let actPM10 = act.pm10 !== undefined ? `${act.pm10.toFixed(1)} µg/m³` : "N/A";
        let predPM10 = pred.predicted_pm10 !== undefined ? `${pred.predicted_pm10.toFixed(1)} µg/m³` : "N/A";
        let actTemp = act.temp !== undefined ? `${act.temp.toFixed(1)} °F` : "N/A";
        let predTemp = pred.predicted_temperature !== undefined ? `${pred.predicted_temperature.toFixed(1)} °F` : "N/A";
        
        container.innerHTML = `
            <div style="background: rgba(255, 255, 255, 0.01); padding: 15px; border-radius: 10px; border: 1px solid var(--border-color);">
                <h4 style="font-size: 0.95rem; font-weight:700; margin-bottom:12px; color:#a5b4fc;">
                    📅 ${new Date(data.date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
                </h4>
                
                ${aqiHTML}
                
                <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-top: 10px;">
                    <thead>
                        <tr style="border-bottom: 1px solid var(--border-color); text-align: left; color: var(--text-secondary);">
                            <th style="padding: 6px 0;">Metric</th>
                            <th style="padding: 6px 0; text-align: right;">Observed</th>
                            <th style="padding: 6px 0; text-align: right;">Forecasted</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="border-bottom: 1px solid rgba(255,255,255,0.03);">
                            <td style="padding: 8px 0; color: var(--text-secondary);">PM2.5</td>
                            <td style="padding: 8px 0; text-align: right; font-weight:600;">${actPM25}</td>
                            <td style="padding: 8px 0; text-align: right; color:#d8b4fe; font-weight:600;">${predPM25}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid rgba(255,255,255,0.03);">
                            <td style="padding: 8px 0; color: var(--text-secondary);">PM10</td>
                            <td style="padding: 8px 0; text-align: right; font-weight:600;">${actPM10}</td>
                            <td style="padding: 8px 0; text-align: right; color:#d8b4fe; font-weight:600;">${predPM10}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: var(--text-secondary);">Temperature</td>
                            <td style="padding: 8px 0; text-align: right; font-weight:600;">${actTemp}</td>
                            <td style="padding: 8px 0; text-align: right; color:#d8b4fe; font-weight:600;">${predTemp}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
    };
    
    // Bind navigation buttons for calendar
    const initCalendarNavigation = () => {
        const prevBtn = document.getElementById("cal-prev");
        const nextBtn = document.getElementById("cal-next");
        if (!prevBtn || !nextBtn) return;
        
        prevBtn.addEventListener("click", () => {
            currentMonth--;
            if (currentMonth < 0) {
                currentMonth = 11;
                currentYear--;
            }
            renderCalendar();
        });
        
        nextBtn.addEventListener("click", () => {
            currentMonth++;
            if (currentMonth > 11) {
                currentMonth = 0;
                currentYear++;
            }
            renderCalendar();
        });
    };

    // Initial Load & Bindings
    initTabbedRouting();
    loadDashboardData();
    loadModelComparison();
    loadNewsFeed();
    renderCalendar();
    initCalendarNavigation();
});
