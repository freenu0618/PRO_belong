// static/js/ai_tuning.js

$(document).ready(function () {
    // Explanation Data
    // Explanation Data
    const helpContent = {
        tuning: `
            <h6>🛠️ 파인튜닝 (Fine-Tuning) 가이드</h6>
            <p>RunPod 클라우드의 고성능 GPU를 빌려, AI에게 <b>나만의 데이터</b>를 공부시키는 과정입니다.</p>
            <hr>
            <ul>
                <li><b>Max Steps</b>: 총 공부할 분량입니다. 이 횟수만큼 데이터를 반복 학습합니다.</li>
                <li><b>Warmup Steps</b>: "준비 운동" 단계입니다. 처음부터 무리하지 않고 천천히 학습 속도를 올립니다.</li>
                <li><b>Eval & Save</b>: 중간중간 "모의고사(평가)"를 치르고, "저장(체크포인트)"을 합니다.</li>
            </ul>
            <p class="text-muted small mt-2">※ 설정이 어렵다면, 기본값을 그대로 두고 <b>'학습 시작'</b>을 눌러보세요!</p>
        `,
        chat: `
            <h6>🤖 튜닝된 LLM 사용하기</h6>
            <p>내가 학습시킨('튜닝된') 모델과 대화해볼 수 있는 공간입니다.</p>
            <hr>
            <ul>
                <li><b>모델 선택</b>: 'Base'는 기본 똑똑이, 'Tuned'는 내 데이터를 배운 똑똑이입니다.</li>
                <li><b>고급 설정</b>: AI의 창의력(Temperature)이나 말수(Max Tokens)를 조절할 수 있습니다.</li>
            </ul>
        `,
        compare: `
            <h6>⚖️ LLM 비교하기</h6>
            <p><b>"공부하기 전(Base)과 후(Tuned)가 얼마나 달라졌을까?"</b></p>
            <p>궁금하시죠? 여기서 두 모델을 나란히 두고 같은 질문을 던져보세요.</p>
            <hr>
            <ul>
                <li>왼쪽과 오른쪽에 비교하고 싶은 모델을 각각 선택하세요.</li>
                <li>질문을 입력하고 <b>'비교하기'</b>를 누르면 동시에 대답을 내놓습니다.</li>
            </ul>
        `,
        docs: `
            <h6>📚 지식 베이스 관리 (RAG)</h6>
            <p><b>"AI에게 새로운 지식을 가르쳐주세요."</b></p>
            <p>PDF나 TXT 파일을 업로드하면, AI가 그 내용을 읽고 기억합니다. (Retrieval-Augmented Generation)</p>
            <hr>
            <ul>
                <li><b>파일 업로드</b>: 정책 문서, 매뉴얼, 보고서 등을 업로드하세요.</li>
                <li><b>지식 활용</b>: 업로드 후 '모델 대화'에서 질문하면, 이 내용을 참고(Reference)하여 답변합니다.</li>
            </ul>
        `
    };

    // 0. Dynamic Model Loading
    function loadModels() {
        $.ajax({
            url: "/api/tuning/models",
            method: "GET",
            success: function (res) {
                // Flask success_response는 data로 감싸서 반환
                const data = res.data || res;
                const models = data.models || [];
                if (models.length > 0) {
                    const $selects = $("#chat-model-select, #model-a-select, #model-b-select");
                    $selects.empty();

                    models.forEach(model => {
                        let label = model;
                        if (model === "base") label = "Llama-3-8B-Base (Original)";
                        // Prettify Lora names if needed

                        $selects.append(`<option value="${model}">${label}</option>`);
                    });

                    if (models.length > 1) {
                        $("#model-b-select").val(models[1]);
                    }
                    console.log("✅ Models loaded:", models);

                    // ✅ 저장된 모델 목록 UI 갱신
                    loadSavedModelsUI(models);
                }
            },
            error: function (err) {
                console.error("Failed to load models:", err);
            }
        });
    }
    loadModels();

    // ✅ 저장된 모델 관리 UI
    function loadSavedModelsUI(models) {
        const $container = $("#saved-models-list");
        $container.empty();

        const protected = ["base", "lora_best_r32"];

        models.forEach(model => {
            const isProtected = protected.includes(model);
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
    }

    // ✅ 모델 삭제 버튼 이벤트
    $(document).on("click", ".btn-delete-model", function () {
        const modelName = $(this).data("model");
        if (!confirm(`'${modelName}' 모델을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`)) {
            return;
        }

        const token = localStorage.getItem("access_token");
        const $btn = $(this);
        $btn.prop("disabled", true).html('<i class="bi bi-hourglass-split"></i>');

        $.ajax({
            url: `/api/tuning/models/${modelName}`,
            method: "DELETE",
            headers: { "Authorization": "Bearer " + token },
            success: function (res) {
                const data = res.data || res;
                if (data.ok) {
                    alert(`✅ '${modelName}' 삭제 완료!`);
                    loadModels();  // 목록 새로고침
                } else {
                    alert(`❌ 오류: ${data.error || "삭제 실패"}`);
                }
            },
            error: function (xhr) {
                const err = xhr.responseJSON?.error?.message || "삭제 실패";
                alert(`❌ 오류: ${err}`);
            },
            complete: function () {
                $btn.prop("disabled", false).html('<i class="bi bi-trash"></i>');
            }
        });
    });

    // ✅ 새로고침 버튼
    $("#btn-refresh-models").on("click", function () {
        loadModels();
    });


    // 1. Navigation Logic
    $(".tuning-nav-btn[data-section]").on("click", function () {
        // Active Style
        $(".tuning-nav-btn").removeClass("active");
        $(this).addClass("active");

        // Section Switching
        const target = $(this).data("section");
        $(".tuning-section").removeClass("active");
        $(`#section-${target}`).addClass("active");

        // Auto Open Help Modal
        showHelp(target);
    });

    // 2. Help System
    $("#btn-show-help").on("click", function () {
        // Find current active section
        const activeSectionId = $(".tuning-section.active").attr("id");
        const key = activeSectionId.replace("section-", "");
        showHelp(key);
    });

    $(".help-icon").on("click", function () {
        const key = $(this).data("key");

        const descriptions = {
            max_steps: `
                <strong>Max Steps (최대 학습 단계)</strong><br><br>
                AI가 총 몇 번의 발걸음(Step)을 내디디며 학습할지 정합니다.<br>
                데이터가 많다면 이 숫자를 늘려야 충분히 공부할 수 있습니다.<br>
                (보통 100~500 정도부터 시도해보세요.)
            `,
            warmup_steps: `
                <strong>Warmup Steps (준비 운동)</strong><br><br>
                운동 전에 스트레칭을 하듯이, AI도 처음에는 천천히 학습(Learning Rate를 0에서 목표치까지 서서히 올림)해야 합니다.<br>
                학습 초기에 방향을 잘못 잡는 것을 방지해 줍니다.
            `,
            eval_steps: `
                <strong>Eval Steps (평가 주기)</strong><br><br>
                학습 도중 몇 걸음마다 "중간고사"를 칠지 정합니다.<br>
                자주 평가하면 꼼꼼히 확인하지만 시간이 더 걸릴 수 있습니다.
            `,
            save_steps: `
                <strong>Save Steps (저장 주기)</strong><br><br>
                몇 걸음마다 "게임 세이브"를 할지 정합니다.<br>
                학습 중간중간 모델을 저장해두면, 나중에 가장 똑똑했던 시점의 모델을 골라 쓸 수 있습니다.
            `,
            learning_rate: `
                <strong>Learning Rate (학습률)</strong><br><br>
                AI가 지식을 습득하는 "보폭"입니다.<br>
                너무 크면 세밀한 지점을 지나쳐버리고, 너무 작으면 배우는 데 한세월이 걸립니다.<br>
                기본값 <b>0.0002 (2e-4)</b>가 가장 무난하고 많이 쓰입니다.
            `,
            evaluation_strategy: `
                <strong>Evaluation Strategy (평가 전략)</strong><br><br>
                평가(중간고사)를 언제 할지 기준을 정합니다.<br>
                - <b>Steps</b>: 지정한 횟수(Steps)마다 평가<br>
                - <b>Epoch</b>: 데이터 전체를 한 바퀴 돌 때마다 평가
            `,
            save_strategy: `
                <strong>Save Strategy (저장 전략)</strong><br><br>
                저장(체크포인트)을 언제 할지 기준을 정합니다.<br>
                보통 평가 전략과 동일하게 맞추는 것이 좋습니다.
            `,
            weight_decay: `
                <strong>Weight Decay (가중치 감소)</strong><br><br>
                AI가 특정 지식에만 너무 집착(Overfitting)하지 않도록 규제를 가합니다.<br>
                적절히 설정하면 새로운 문제도 잘 푸는 범용적인 모델이 됩니다. (기본값: 0.01)
            `,
            optim: `
                <strong>Optimizer (최적화 도구)</strong><br><br>
                학습의 효율을 담당하는 수학적 알고리즘입니다.<br>
                <b>adamw_torch</b>가 현재 가장 널리 쓰이는 표준적인 방식입니다.
            `
        };

        const msg = descriptions[key] || "해당 항목에 대한 설명이 준비되지 않았습니다.";
        $("#tuningHelpBody").html(msg); // Removed <p> wrapper to allow HTML inside descriptions
        new bootstrap.Modal(document.getElementById('tuningHelpModal')).show();
    });

    function showHelp(key) {
        const content = helpContent[key] || "설명이 없습니다.";
        $("#tuningHelpBody").html(content);
        new bootstrap.Modal(document.getElementById('tuningHelpModal')).show();
    }

    // Initial Load - Check Hash for Deep Linking
    function checkHash() {
        const hash = window.location.hash.replace("#section-", "");
        if (hash && ["tuning", "chat", "compare", "docs"].includes(hash)) {
            $(`.tuning-nav-btn[data-section="${hash}"]`).click();
        }
    }

    // Run on load
    checkHash();

    // Run on hash change (Navbar link connection)
    $(window).on("hashchange", function () {
        checkHash();
    });

    // 3. Form Handling (Using real endpoint placeholder)
    // 3. Form Handling (Real API)
    $("#tuning-form").on("submit", function (e) {
        e.preventDefault();

        const $btn = $(this).find("button[type='submit']");
        const originalText = $btn.text();
        $btn.prop("disabled", true).text("요청 중...");

        // Serialize to JSON
        const formData = {};
        $(this).serializeArray().forEach(item => {
            // Special handling for model_name - always keep as string
            if (item.name === 'model_name') {
                formData[item.name] = String(item.value);
            }
            // Convert numbers (except model_name)
            else if (!isNaN(item.value) && item.value !== "") {
                formData[item.name] = Number(item.value);
            } else {
                formData[item.name] = item.value;
            }
        });

        // Handle checkboxes separately (they don't appear in serializeArray if unchecked)
        formData.use_double_quant = $('#use_double_quant').is(':checked');

        const token = localStorage.getItem("access_token");

        // ✅ UI Feedback: Show Inline Progress Section with max_steps
        const maxSteps = parseInt(formData.max_steps) || 100;
        showInlineProgress("pending-job-creation", maxSteps);

        $.ajax({
            url: "/api/tuning/start",
            type: "POST",
            contentType: "application/json",
            headers: { "Authorization": "Bearer " + token },
            data: JSON.stringify(formData),
            success: function (res) {
                // Update inline progress with real Job ID and start polling
                updateInlineProgressJobId(res.data.job_id || res.job_id);
            },
            error: function (xhr) {
                const err = xhr.responseJSON?.error?.message || xhr.responseJSON?.message || "학습 시작 실패";
                alert(`❌ 오류: ${err}`);
                hideInlineProgress();
            },
            complete: function () {
                $btn.prop("disabled", false).text(originalText);
            }
        });
    });

    // Polling Logic
    let currentPollingInterval = null;
    let lossChart = null;  // Chart.js instance

    function showInlineProgress(tempJobId, maxSteps = 100) {
        // Show progress section
        $("#training-progress-section").slideDown();

        // Scroll to progress section
        $('html, body').animate({
            scrollTop: $("#training-progress-section").offset().top - 100
        }, 500);

        // Reset UI
        $("#progress-percentage").text("0%");
        $("#progress-bar").css("width", "0%").attr("aria-valuenow", 0);
        $("#current-step").text(`0/${maxSteps}`);
        $("#elapsed-time").text("00:00:00");
        $("#train-loss").text("-");
        $("#eval-loss").text("-");
        $("#training-logs").html('<div class="text-info">학습을 준비 중입니다...</div>');

        // ✅ Initialize Chart.js (반응형)
        initLossChart();
    }

    function hideInlineProgress() {
        $("#training-progress-section").slideUp();
        if (currentPollingInterval) {
            clearInterval(currentPollingInterval);
            currentPollingInterval = null;
        }
        if (lossChart) {
            lossChart.destroy();
            lossChart = null;
        }
    }

    // ✅ 반응형 차트 (동적으로 X축 추가)
    function initLossChart() {
        if (lossChart) {
            lossChart.destroy();
        }

        const ctx = document.getElementById('loss-chart');
        if (!ctx) return;

        lossChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],  // 동적으로 추가
                datasets: [
                    {
                        label: 'Training Loss',
                        data: [],
                        borderColor: '#ffc107',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        tension: 0.4,
                        fill: true,
                        spanGaps: true  // ✅ 끊긴 데이터 연결
                    },
                    {
                        label: 'Eval Loss',
                        data: [],
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        tension: 0.4,
                        fill: true,
                        spanGaps: true  // ✅ Eval Loss 연결 (중요)
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                animation: {
                    duration: 300
                },
                plugins: {
                    legend: {
                        display: true,
                        labels: { color: '#fff' }
                    }
                },
                scales: {
                    x: {
                        title: { display: true, text: 'Step', color: '#aaa' },
                        ticks: { color: '#aaa' },
                        grid: { color: 'rgba(255,255,255,0.1)' }
                    },
                    y: {
                        title: { display: true, text: 'Loss', color: '#aaa' },
                        ticks: { color: '#aaa' },
                        grid: { color: 'rgba(255,255,255,0.1)' }
                    }
                }
            }
        });

        // ✅ 마지막 추가된 step 추적 (중복 방지용)
        lossChart.lastAddedStep = -1;

        console.log(`📊 Chart initialized (reactive mode)`);
    }

    // ✅ 반응형 차트 업데이트 (동적으로 X축 추가, 중복 방지)
    function updateLossChart(step, loss, evalLoss) {
        if (!lossChart) return;

        // ✅ Training loss가 없으면 evaluation 중이므로 업데이트 스킵
        if (loss === undefined || loss === null) {
            console.log(`⏳ Step ${step}: Evaluation in progress, skipping chart update`);
            return;
        }

        // ✅ 중복 step 방지: 이미 추가된 step이면 스킵
        if (step <= lossChart.lastAddedStep) {
            console.log(`⏭️ Step ${step}: Already added, skipping`);
            return;
        }

        // 새 step 추가
        lossChart.data.labels.push(step);
        lossChart.data.datasets[0].data.push(loss);
        lossChart.data.datasets[1].data.push(evalLoss || null);

        // 마지막 추가된 step 업데이트
        lossChart.lastAddedStep = step;

        lossChart.update('none');  // 애니메이션 없이 즉시 업데이트
    }

    function updateInlineProgressJobId(jobId) {
        $("#training-logs").append(`<div class="text-info">✅ 작업 생성 완료! Job ID: ${jobId}</div>`);
        $("#training-logs").append(`<div class="text-muted">학습 로그 수집을 시작합니다...</div>`);

        // Clear any existing poll
        if (currentPollingInterval) clearInterval(currentPollingInterval);

        // Start Polling (3초 간격으로 변경 - UI 렉 방지)
        currentPollingInterval = setInterval(() => {
            pollStatus(jobId, currentPollingInterval);
        }, 3000);  // 1000 → 3000ms

        // Bind Close Button (Unique handler)
        $("#btn-close-training-progress").off("click").on("click", function () {
            hideInlineProgress();
            loadModels(); // Refresh model list after training
        });
    }

    function pollStatus(jobId, intervalId) {
        const token = localStorage.getItem("access_token");
        $.ajax({
            url: `/api/tuning/status/${jobId}`,
            method: "GET",
            headers: { "Authorization": "Bearer " + token },
            success: function (res) {
                // Flask success_response는 data로 감싸서 반환
                const data = res.data || res;
                if (!data.ok && !res.ok) return;

                // Update Progress Bar
                const pct = data.progress || 0;
                $("#progress-bar").css("width", `${pct}%`).attr("aria-valuenow", pct);
                $("#progress-percentage").text(`${pct}%`);

                // Update Step Counter
                if (data.metrics) {
                    const m = data.metrics;
                    const current = m.current_step || 0;
                    const total = m.total_steps || 100;
                    $("#current-step").text(`${current} / ${total}`);

                    // Update Metrics Dashboard
                    if (m.loss !== undefined) {
                        const loss = typeof m.loss === 'number' ? m.loss.toFixed(4) : m.loss;
                        $("#train-loss").text(loss);
                        // ✅ 새 차트 업데이트 함수 사용
                        updateLossChart(current, parseFloat(loss), m.eval_loss);
                    }
                    if (m.eval_loss !== undefined) {
                        const eval_loss = typeof m.eval_loss === 'number' ? m.eval_loss.toFixed(4) : m.eval_loss;
                        $("#eval-loss").text(eval_loss);
                        // ✅ updateLossChart에서 이미 처리됨
                    }

                    if (m.learning_rate !== undefined) {
                        const lr = typeof m.learning_rate === 'number' ? m.learning_rate.toExponential(2) : m.learning_rate;
                        $("#train-lr").text(lr);
                    }
                    if (m.eta_seconds !== undefined) {
                        $("#train-eta").text(formatETA(m.eta_seconds));
                    }
                    if (m.elapsed_time !== undefined) {
                        $("#elapsed-time").text(formatTime(m.elapsed_time));
                    }
                }

                // Update Status Text
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

                // Update Logs
                if (data.logs && Array.isArray(data.logs) && data.logs.length > 0) {
                    const logHtml = data.logs.map(log => {
                        let logClass = "text-light";
                        if (log.includes("Error") || log.includes("Failed")) logClass = "text-danger";
                        else if (log.includes("Eval") || log.includes("Checkpoint")) logClass = "text-info";
                        else if (log.includes("Loss=")) logClass = "text-warning";
                        return `<div class="${logClass}">${escapeHtml(log)}</div>`;
                    }).join("");
                    $("#training-logs").html(logHtml);
                    // Also update legacy console if exists
                    const $console = $("#training-log-console");
                    if ($console.length) $console.html(logHtml);
                    // Auto-scroll to bottom
                    const logContainer = document.getElementById("training-logs") || document.getElementById("training-log-console");
                    if (logContainer) logContainer.scrollTop = logContainer.scrollHeight;
                }

                // Check if Completed or Failed
                const statusText = data.status_text || data.status || "running";
                if (statusText === "completed") {
                    clearInterval(intervalId);
                    $("#training-logs").append('<div class="text-success fw-bold mt-2">✅ 학습이 완료되었습니다!</div>');
                    $("#btn-stop-training").hide();
                    alert("✅ 학습이 완료되었습니다!");
                    loadModels(); // Refresh model list
                } else if (statusText === "failed" || statusText === "error") {
                    clearInterval(intervalId);
                    $("#training-logs").append('<div class="text-danger fw-bold mt-2">❌ 학습이 실패했습니다.</div>');
                    $("#btn-stop-training").hide();
                    alert("❌ 학습이 실패했습니다.");
                }
            },
            error: function (xhr) {
                console.warn("Polling failed:", xhr);
            }
        });
    }

    // ETA 포맷팅 헬퍼
    function formatETA(seconds) {
        if (!seconds || seconds < 0) return "-";
        const mins = Math.floor(seconds / 60);
        const secs = Math.round(seconds % 60);
        if (mins > 0) return `${mins}분 ${secs}초`;
        return `${secs}초`;
    }

    function formatTime(seconds) {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = Math.floor(seconds % 60);
        return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    }

    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }

    // 로그 지우기 버튼
    $("#btn-clear-logs").on("click", function () {
        $("#training-log-console").html('<div class="text-muted">로그가 초기화되었습니다.</div>');
    });

    // 4. Chat & Compare Logic (Real API)
    // Shared Generation Options
    let genOptions = {
        temperature: 0.7,
        max_new_tokens: 200,
        use_cache: true
    };

    // Settings Modal Logic (Shared)
    function openSettingsModal() {
        try {
            // Load current values
            $("#setting-temp").val(genOptions.temperature);
            $("#label-temp-val").text(genOptions.temperature);

            $("#setting-max-tokens").val(genOptions.max_new_tokens);
            $("#label-tokens-val").text(genOptions.max_new_tokens);

            $("#setting-use-cache").prop("checked", genOptions.use_cache);

            // Try Bootstrap 5 modal
            const modalEl = document.getElementById('chatSettingsModal');
            if (modalEl && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                const modal = new bootstrap.Modal(modalEl);
                modal.show();
            } else {
                // Fallback: jQuery method
                $('#chatSettingsModal').modal('show');
            }
        } catch (e) {
            console.error("고급설정 모달 열기 실패:", e);
            alert("고급설정 모달을 열 수 없습니다. 페이지를 새로고침해주세요.");
        }
    }

    $("#btn-chat-settings, #btn-compare-settings").on("click", function (e) {
        e.preventDefault();
        console.log("고급설정 버튼 클릭됨");
        openSettingsModal();
    });

    $("#setting-temp").on("input", function () {
        $("#label-temp-val").text($(this).val());
    });

    $("#setting-max-tokens").on("input", function () {
        $("#label-tokens-val").text($(this).val());
    });

    $("#btn-save-settings").on("click", function () {
        genOptions.temperature = parseFloat($("#setting-temp").val());
        genOptions.max_new_tokens = parseInt($("#setting-max-tokens").val());
        genOptions.use_cache = $("#setting-use-cache").is(":checked");

        // Close modal
        const modalEl = document.getElementById('chatSettingsModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();
    });

    // Keydown handler for Textareas (Shift+Enter for new line, Enter to send)
    $("#chat-single-input, #compare-input").on("keydown", function (e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            const id = $(this).attr("id");
            if (id === "chat-single-input") $("#btn-single-send").click();
            if (id === "compare-input") $("#btn-compare-send").click();
        }
    });

    // RAG Toggle Logic
    $("#toggle-use-rag").on("change", function () {
        if ($(this).is(":checked")) {
            $("#rag-upload-panel").removeClass("d-none");
        } else {
            $("#rag-upload-panel").addClass("d-none");
        }
    });

    $("#btn-close-rag-panel").on("click", function () {
        $("#rag-upload-panel").addClass("d-none");
    });

    // System Message Helper
    function logSystemMessage(msg) {
        const sysMsg = `<div class="text-center my-2"><span class="badge bg-secondary text-wrap" style="font-weight: normal; opacity: 0.8;">ℹ️ ${msg}</span></div>`;
        $("#chat-single-box").append(sysMsg);
        $("#chat-single-box").scrollTop($("#chat-single-box")[0].scrollHeight);
    }

    // Watch for Changes to Log System Messages
    $("#toggle-use-rag").on("change", function () {
        const state = $(this).is(":checked") ? "ON (지식 활용)" : "OFF (일반 대화)";
        logSystemMessage(`RAG 지식 검색 기능이 <b>${state}</b>로 변경되었습니다.`);
    });

    $("#chat-model-select").on("change", function () {
        const modelName = $(this).val();
        logSystemMessage(`대화 모델이 <b>${modelName}</b>(으)로 변경되었습니다.`);
    });

    $("#btn-single-send").on("click", function () {
        const msg = $("#chat-single-input").val().trim(); // Use trim()
        if (!msg) return;

        const model = $("#chat-model-select").val() || "llama3-8b-base-q4"; // Updated ID
        const useRag = $("#toggle-use-rag").is(":checked");

        $("#chat-single-box").append(`<div class="chat-bubble user">${msg.replace(/\n/g, "<br>")}</div>`);
        $("#chat-single-input").val("");
        $("#chat-single-box").scrollTop($("#chat-single-box")[0].scrollHeight);

        // Show typing indicator (animated)
        const loadingId = "loading-" + Date.now();
        const typingIndicator = `
            <div id="${loadingId}" class="chat-bubble bot">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>`;
        $("#chat-single-box").append(typingIndicator);
        $("#chat-single-box").scrollTop($("#chat-single-box")[0].scrollHeight);

        const token = localStorage.getItem("access_token");
        if (!token) {
            alert("로그인 후 이용 가능합니다.");
            window.location.href = "/login";
            return;
        }

        // Merge options with RAG flag
        const finalOptions = { ...genOptions, use_rag: useRag };

        $.ajax({
            url: "/api/tuning/chat",
            type: "POST",
            contentType: "application/json",
            headers: { "Authorization": "Bearer " + token },
            data: JSON.stringify({
                text: msg,
                model: model,
                options: finalOptions
            }),
            success: function (res) {
                // Flask success_response는 data로 감싸서 반환
                const data = res.data || res;
                const formatted = (data.result || "").replace(/\n/g, "<br>");
                // Response with Copy Button and Model Badge
                const responseId = "resp-" + Date.now();
                const responseHTML = `
                    <div class="position-relative">
                        <div id="${responseId}">${formatted}</div>
                        <div class="d-flex justify-content-between align-items-center mt-2 border-top border-secondary pt-1">
                            <small class="text-warning" style="font-size: 0.75rem;">🤖 Model: ${model}</small>
                            <button class="btn btn-sm btn-outline-secondary py-0 px-1 btn-copy-response" data-target="${responseId}" title="복사">
                                📋
                            </button>
                        </div>
                    </div>`;
                $(`#${loadingId}`).html(responseHTML);
            },
            error: function (xhr) {
                const err = xhr.responseJSON?.message || "답변을 가져오지 못했습니다. (모델 상태를 확인해주세요)";
                $(`#${loadingId}`).html(`<span class="text-danger">❌ Error: ${err}</span>`);
            }
        });
    });

    $("#btn-compare-send").on("click", function () {
        const msg = $("#compare-input").val().trim();
        if (!msg) return;

        const modelA = $("#model-a-select").val() || "llama3-8b-base-q4";
        const modelB = $("#model-b-select").val() || "llama3-8b-constant-100-q4";

        $("#compare-box-a").append(`<div class="text-end mb-2 text-muted">${msg.replace(/\n/g, "<br>")}</div>`);
        $("#compare-box-b").append(`<div class="text-end mb-2 text-muted">${msg.replace(/\n/g, "<br>")}</div>`);
        $("#compare-input").val("");

        // Check auth before starting comparison
        const token = localStorage.getItem("access_token");
        if (!token) {
            alert("로그인 후 이용 가능합니다.");
            window.location.href = "/login";
            return;
        }

        // Loading bubbles
        const idA = "comp-a-" + Date.now();
        const idB = "comp-b-" + Date.now();

        $("#compare-box-a").append(`<div id="${idA}" class="p-2 bg-dark border border-secondary rounded mb-2">...</div>`);
        $("#compare-box-b").append(`<div id="${idB}" class="p-2 bg-dark border border-secondary rounded mb-2">...</div>`);

        // Function to call API
        function callCompare(targetId, targetModel) {
            // Use genOptions directly (user-defined limits)
            const token = localStorage.getItem("access_token");
            if (!token) {
                $(`#${targetId}`).html(`<span class="text-danger">로그인 필요</span>`);
                return;
            }

            $.ajax({
                url: "/api/tuning/compare",
                type: "POST",
                contentType: "application/json",
                headers: { "Authorization": "Bearer " + token },
                data: JSON.stringify({
                    text: msg,
                    model: targetModel,
                    options: genOptions
                }),
                success: function (res) {
                    // Flask success_response는 data로 감싸서 반환
                    const data = res.data || res;
                    const formatted = (data.result || "").replace(/\n/g, "<br>");
                    $(`#${targetId}`).html(formatted || "(응답 없음)");
                },
                error: function (xhr) {
                    const err = xhr.responseJSON?.message || "Failed";
                    $(`#${targetId}`).html(`<span class="text-danger">Error: ${err}</span>`);
                }
            });
        }

        callCompare(idA, modelA);
        callCompare(idB, modelB);

    });

    // 6. Doc Upload Logic with Drag & Drop
    const $dropZone = $("#rag-upload-panel");
    const $fileInput = $("#doc-upload-input");
    const $status = $("#doc-upload-status");

    // Drag and Drop Events
    $dropZone.on("dragover", function (e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).addClass("dragover");
    });

    $dropZone.on("dragleave drop", function (e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass("dragover");
    });

    $dropZone.on("drop", function (e) {
        const files = e.originalEvent.dataTransfer.files;
        if (files.length > 0) {
            $fileInput[0].files = files;
            uploadFiles(files);
        }
    });

    // Click Upload Button
    $("#btn-doc-upload").on("click", function () {
        const files = $fileInput[0].files;
        if (files.length === 0) {
            alert("파일을 선택해주세요.");
            return;
        }
        uploadFiles(files);
    });

    // Unified Upload Function
    function uploadFiles(files) {
        $status.html(`
            <div class="d-flex align-items-center gap-2">
                <div class="spinner-border text-primary spinner-border-sm"></div>
                <span>업로드 중... (${files.length}개 파일)</span>
            </div>
            <div class="progress mt-2" style="height: 6px;">
                <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 0%"></div>
            </div>
        `);

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append("files", files[i]);
        }

        const token = localStorage.getItem("access_token");

        $.ajax({
            url: "/api/docs/upload",
            type: "POST",
            data: formData,
            headers: { "Authorization": "Bearer " + token },
            contentType: false,
            processData: false,
            xhr: function () {
                const xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener("progress", function (e) {
                    if (e.lengthComputable) {
                        const pct = Math.round((e.loaded / e.total) * 100);
                        $status.find(".progress-bar").css("width", pct + "%");
                    }
                });
                return xhr;
            },
            success: function (res) {
                const count = res.results ? res.results.length : 1;
                const chunks = res.results ? res.results.reduce((sum, r) => sum + (r.chunks || 0), 0) : 0;
                $status.html(`
                    <div class="text-success">
                        <strong>✅ ${count}개 파일 업로드 완료!</strong>
                        <small class="d-block text-muted">${chunks}개 청크가 지식 베이스에 추가되었습니다.</small>
                    </div>
                `);
                $fileInput.val(""); // Reset
            },
            error: function (xhr) {
                if (xhr.status === 401) {
                    $status.html(`<div class="text-warning">⚠️ 로그인이 필요합니다.</div>`);
                    window.location.href = "/login";
                    return;
                }
                const err = xhr.responseJSON?.message || "업로드 실패";
                $status.html(`<div class="text-danger">❌ 오류: ${err}</div>`);
            }
        });
    }

    // 7. Chat Export Logic
    $("#btn-chat-export").on("click", function () {
        let content = "Belong AI Chat Log\n==================\n\n";

        $("#chat-single-box .chat-bubble").each(function () {
            const isUser = $(this).hasClass("user");
            const sender = isUser ? "USER" : "AI";
            // Replace <br> with newline
            const text = $(this).html().replace(/<br\s*\/?>/gi, "\n");

            content += `[${sender}]\n${text}\n\n`;
        });

        const blob = new Blob([content], { type: "text/plain" });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `chat_log_${new Date().toISOString().slice(0, 10)}.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    });

    // 5. Sidebar Toggle Logic (Mobile)
    const $sidebar = $(".tuning-sidebar");
    const $overlay = $("#tuning-sidebar-overlay");
    const $toggleBtn = $("#btn-toggle-sidebar");

    function toggleSidebar() {
        $sidebar.toggleClass("open");
        $overlay.toggleClass("show");
    }

    function closeSidebar() {
        $sidebar.removeClass("open");
        $overlay.removeClass("show");
    }

    $toggleBtn.on("click", function (e) {
        e.stopPropagation();
        toggleSidebar();
    });

    $overlay.on("click", function () {
        closeSidebar();
    });

    // Close sidebar when clicking a nav item on mobile
    $(".tuning-nav-btn").on("click", function () {
        if ($(window).width() <= 768) {
            closeSidebar();
        }
    });

    // Handle Resize
    $(window).on("resize", function () {
        if ($(window).width() > 768) {
            closeSidebar(); // Reset mobile state when expanding
        }
    });

    // Copy Response Button Handler
    $(document).on("click", ".btn-copy-response", function () {
        const targetId = $(this).data("target");
        const $target = $(`#${targetId}`);

        // Get text content (removing HTML tags)
        const textContent = $target.text();

        // Copy to clipboard
        navigator.clipboard.writeText(textContent).then(() => {
            // Visual feedback
            const $btn = $(this);
            const originalText = $btn.html();
            $btn.html("✅").addClass("text-success");
            setTimeout(() => {
                $btn.html(originalText).removeClass("text-success");
            }, 1500);
        }).catch(err => {
            console.error("복사 실패:", err);
            alert("복사에 실패했습니다.");
        });
    });
});

