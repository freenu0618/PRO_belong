import { helpContent, descriptions } from './constants.js';

export const UI = {
    showHelp(key) {
        // Find main help content
        let content = helpContent[key];

        // If not found in main help, check descriptions (for icons)
        if (!content && descriptions[key]) {
            content = descriptions[key];
        }

        if (!content) content = "설명이 없습니다.";

        $("#tuningHelpBody").html(content);
        new bootstrap.Modal(document.getElementById('tuningHelpModal')).show();
    },

    loadModelsUI(models) {
        const $selects = $("#chat-model-select, #model-a-select, #model-b-select");
        $selects.empty();

        models.forEach(model => {
            let label = model;
            if (model === "base") label = "Llama-3-8B-Base (Original)";
            $selects.append(`<option value="${model}">${label}</option>`);
        });

        if (models.length > 1) {
            $("#model-b-select").val(models[1]);
        }

        // Load Saved Models List
        const $container = $("#saved-models-list");
        $container.empty();
        const protectedModels = ["base", "lora_best_r32"];

        models.forEach(model => {
            const isProtected = protectedModels.includes(model);
            const card = `
                <div class="col-md-4 col-sm-6">
                    <div class="card bg-secondary bg-opacity-25 border-secondary">
                        <div class="card-body p-3 d-flex justify-content-between align-items-center">
                            <div>
                                <span class="text-white">${model}</span>
                                ${isProtected ? '<span class="badge bg-info ms-2">기본</span>' : ''}
                            </div>
                            ${!isProtected ? `
                                <button class="btn btn-outline-danger btn-sm btn-delete-model" 
                                        data-model="${model}" title="삭제">
                                    <i class="bi bi-trash"></i>
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
            $container.append(card);
        });

        if (models.length === 0) {
            $container.html('<div class="text-muted">저장된 모델이 없습니다.</div>');
        }
    },

    showInlineProgress(maxSteps) {
        $("#training-progress-section").slideDown();
        $('html, body').animate({
            scrollTop: $("#training-progress-section").offset().top - 100
        }, 500);

        $("#progress-percentage").text("0%");
        $("#progress-bar").css("width", "0%").attr("aria-valuenow", 0);
        $("#current-step").text(`0/${maxSteps}`);
        $("#elapsed-time").text("00:00:00");
        $("#train-loss").text("-");
        $("#eval-loss").text("-");
        $("#training-logs").html('<div class="text-info">학습을 준비 중입니다...</div>');
    },

    hideInlineProgress() {
        $("#training-progress-section").slideUp();
    },

    updateProgress(data) {
        const pct = data.progress || 0;
        $("#progress-bar").css("width", `${pct}%`).attr("aria-valuenow", pct);
        $("#progress-percentage").text(`${pct}%`);

        if (data.metrics) {
            const m = data.metrics;
            const current = m.current_step || 0;
            const total = m.total_steps || 100;
            $("#current-step").text(`${current} / ${total}`);

            if (m.loss !== undefined) {
                const loss = typeof m.loss === 'number' ? m.loss.toFixed(4) : m.loss;
                $("#train-loss").text(loss);
            }
            if (m.eval_loss !== undefined) {
                const eval_loss = typeof m.eval_loss === 'number' ? m.eval_loss.toFixed(4) : m.eval_loss;
                $("#eval-loss").text(eval_loss);
            }
            if (m.learning_rate !== undefined) {
                const lr = typeof m.learning_rate === 'number' ? m.learning_rate.toExponential(2) : m.learning_rate;
                $("#train-lr").text(lr);
            }
            if (m.eta_seconds !== undefined) {
                $("#train-eta").text(this.formatETA(m.eta_seconds));
            }
            if (m.elapsed_time !== undefined) {
                $("#elapsed-time").text(this.formatTime(m.elapsed_time));
            }
        }

        // Status Text
        if (data.status_text) {
            $("#training-status-text").text(data.status_text);
        } else if (data.status) {
            const statusMap = {
                "pending": "대기 중...",
                "running": "학습 진행 중...",
                "completed": "✅ 학습 완료!",
                "failed": "❌ 학습 실패"
            };
            $("#training-status-text").text(statusMap[data.status] || data.status);
        }
    },

    appendLogs(logs) {
        if (logs && logs.length > 0) {
            const logHtml = logs.map(log => {
                let logClass = "text-light";
                if (log.includes("Error") || log.includes("Failed")) logClass = "text-danger";
                else if (log.includes("Eval") || log.includes("Checkpoint")) logClass = "text-info";
                else if (log.includes("Loss=")) logClass = "text-warning";
                return `<div class="${logClass}">${this.escapeHtml(log)}</div>`;
            }).join("");

            $("#training-logs").append(logHtml);

            // Auto scroll
            const container = document.getElementById("training-logs");
            if (container) container.scrollTop = container.scrollHeight;
        }
    },

    formatETA(seconds) {
        if (!seconds || seconds < 0) return "-";
        const mins = Math.floor(seconds / 60);
        const secs = Math.round(seconds % 60);
        if (mins > 0) return `${mins}분 ${secs}초`;
        return `${secs}초`;
    },

    formatTime(seconds) {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = Math.floor(seconds % 60);
        return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    },

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }
};
