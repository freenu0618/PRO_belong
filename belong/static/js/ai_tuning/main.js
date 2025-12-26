import { API } from './api.js';
import { UI } from './ui.js';
import { LossChart } from './charts.js';

$(document).ready(function () {
    // ✅ Enhanced Chart with Insight Message
    const lossChart = new LossChart('loss-chart', 'chart-insight');
    let currentPollingInterval = null;

    // ✅ Smoothing Slider Event
    $("#smoothing-slider").on("input", function () {
        const val = parseFloat($(this).val());
        $("#smoothing-value").text(val.toFixed(2));
        lossChart.setSmoothing(val);
    });

    // ✅ Generation Options (for Advanced Settings Modal)
    const genOptions = {
        temperature: 0.7,
        max_new_tokens: 200,
        use_cache: true
    };

    // 1. Initial Load
    function loadModels() {
        API.getModels().then(res => {
            const data = res.data || res;
            const models = data.models || [];
            UI.loadModelsUI(models);
        }).catch(err => console.error("Failed to load models:", err));
    }
    loadModels();

    $("#btn-refresh-models").on("click", loadModels);

    // 2. Navigation
    $(".tuning-nav-btn[data-section]").on("click", function () {
        $(".tuning-nav-btn").removeClass("active");
        $(this).addClass("active");
        const target = $(this).data("section");
        $(".tuning-section").removeClass("active");
        $(`#section-${target}`).addClass("active");
        UI.showHelp(target);
    });

    // Hash Logic
    function checkHash() {
        const hash = window.location.hash.replace("#section-", "");
        if (hash && ["tuning", "chat", "compare", "docs"].includes(hash)) {
            $(`.tuning-nav-btn[data-section="${hash}"]`).click();
        }
    }
    checkHash();
    $(window).on("hashchange", checkHash);

    // 3. Help System
    $("#btn-show-help").on("click", function () {
        const activeSectionId = $(".tuning-section.active").attr("id");
        const key = activeSectionId.replace("section-", "");
        UI.showHelp(key);
    });

    $(".help-icon").on("click", function () {
        UI.showHelp($(this).data("key"));
    });

    // 4. Training Form
    $("#tuning-form").on("submit", function (e) {
        e.preventDefault();
        const $btn = $(this).find("button[type='submit']");
        const originalText = $btn.text();
        $btn.prop("disabled", true).text("요청 중...");

        const formData = {};
        $(this).serializeArray().forEach(item => {
            if (item.name === 'model_name') formData[item.name] = String(item.value);
            else if (!isNaN(item.value) && item.value !== "") formData[item.name] = Number(item.value);
            else formData[item.name] = item.value;
        });
        formData.use_double_quant = $('#use_double_quant').is(':checked');

        const maxSteps = parseInt(formData.max_steps) || 100;
        UI.showInlineProgress(maxSteps);
        lossChart.init();

        API.startTraining(formData).then(res => {
            const jobId = res.data.job_id || res.job_id;
            $("#training-logs").append(`<div class="text-info">✅ 작업 생성 완료! Job ID: ${jobId}</div>`);

            // Start Polling
            if (currentPollingInterval) clearInterval(currentPollingInterval);
            currentPollingInterval = setInterval(() => pollStatus(jobId), 3000);
        }).catch(xhr => {
            const err = xhr.responseJSON?.error?.message || "학습 시작 실패";
            alert(`❌ 오류: ${err}`);
            UI.hideInlineProgress();
        }).always(() => {
            $btn.prop("disabled", false).text(originalText);
        });
    });

    // Polling Function
    function pollStatus(jobId) {
        API.getTrainingStatus(jobId).then(res => {
            const data = res.data || res;
            if (!data.ok && !res.ok) return;

            UI.updateProgress(data);
            UI.appendLogs(data.logs);

            if (data.metrics && data.metrics.loss !== undefined) {
                lossChart.update(data.metrics.current_step, data.metrics.loss, data.metrics.eval_loss);
            }

            const statusText = data.status_text || data.status || "running";
            if (statusText === "completed" || statusText === "failed" || statusText === "error") {
                clearInterval(currentPollingInterval);
                const msg = statusText === "completed"
                    ? "✅ 학습 완료! 새로 학습된 모델을 사용하려면 페이지가 새로고침됩니다."
                    : "❌ 학습 실패";
                alert(msg);

                if (statusText === "completed") {
                    // ✅ 학습 완료 시 페이지 새로고침 (캐시 비우고 모델 재로드)
                    setTimeout(() => {
                        window.location.reload();
                    }, 500);
                }
                $("#btn-stop-training").hide();
            }
        });
    }

    $("#btn-close-training-progress").on("click", function () {
        UI.hideInlineProgress();
        if (currentPollingInterval) {
            clearInterval(currentPollingInterval);
            currentPollingInterval = null;
        }
        lossChart.destroy();
        loadModels();
    });

    // 5. Model Deletion
    $(document).on("click", ".btn-delete-model", function () {
        const modelName = $(this).data("model");
        if (!confirm(`'${modelName}' 모델을 삭제하시겠습니까?`)) return;

        const $btn = $(this);
        $btn.prop("disabled", true).html('<i class="bi bi-hourglass-split"></i>');

        API.deleteModel(modelName).then(res => {
            const data = res.data || res;
            if (data.ok) {
                alert(`✅ 삭제 완료: ${modelName}`);
                loadModels();
            } else {
                alert(`❌ 삭제 실패: ${data.error}`);
            }
        }).catch(xhr => {
            alert(`❌ 오류: ${xhr.responseJSON?.error?.message}`);
        }).always(() => $btn.prop("disabled", false).html('<i class="bi bi-trash"></i>'));
    });

    // 6. Chat Logic
    // ✅ Chat Send Button with Debounce
    let isChatSending = false;  // Prevent duplicate requests

    $("#btn-single-send").on("click", function () {
        if (isChatSending) return;  // ✅ Prevent duplicate clicks

        const msg = $("#chat-single-input").val().trim();
        if (!msg) return;

        const model = $("#chat-model-select").val();
        const useRag = $("#toggle-use-rag").is(":checked");
        // ✅ Use genOptions instead of hardcoded values
        const options = {
            use_rag: useRag,
            max_new_tokens: genOptions.max_new_tokens,
            temperature: genOptions.temperature,
            use_cache: genOptions.use_cache
        };

        // ✅ Disable button during request
        isChatSending = true;
        const $btn = $(this);
        $btn.prop("disabled", true).text("전송 중...");

        $("#chat-single-box").append(`<div class="chat-bubble user">${msg}</div>`);
        $("#chat-single-input").val("");

        const loadingId = "loading-" + Date.now();
        $("#chat-single-box").append(`<div id="${loadingId}" class="chat-bubble bot">...</div>`);

        // Auto-scroll to bottom
        const chatBox = document.getElementById("chat-single-box");
        if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;

        API.chat(msg, model, options).then(res => {
            const data = res.data || res;
            let responseHtml = data.result ? data.result.replace(/\n/g, "<br>") : "응답 없음";

            // ✅ RAG 출처 정보 표시
            if (data.sources && data.sources.length > 0) {
                responseHtml += `<div class="rag-sources mt-2 pt-2 border-top border-secondary">`;
                responseHtml += `<small class="text-muted">📚 참조 출처:</small><ul class="mb-0 ps-3">`;
                data.sources.forEach(s => {
                    const pageInfo = s.page ? ` (p.${s.page})` : "";
                    responseHtml += `<li><small class="text-info">${s.source}${pageInfo}</small></li>`;
                });
                responseHtml += `</ul></div>`;
            }

            $(`#${loadingId}`).html(responseHtml);
        }).catch(xhr => {
            const errMsg = xhr.responseJSON?.error?.message || xhr.responseJSON?.message || "AI 서버 오류";
            $(`#${loadingId}`).html(`<span class="text-danger">Error: ${errMsg}</span>`);
        }).always(() => {
            // ✅ Re-enable button after request completes
            isChatSending = false;
            $btn.prop("disabled", false).text("전송");

            // Auto-scroll after response
            if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
        });
    });

    // RAG Toggle Logic
    $("#toggle-use-rag").on("change", function () {
        if ($(this).is(":checked")) $("#rag-upload-panel").removeClass("d-none");
        else $("#rag-upload-panel").addClass("d-none");
    });
    $("#btn-close-rag-panel").on("click", () => $("#rag-upload-panel").addClass("d-none"));

    // ✅ 7-1. Compare Button Handler
    let isCompareSending = false;

    $("#btn-compare-send").on("click", function () {
        if (isCompareSending) return;

        const msg = $("#compare-input").val().trim();
        if (!msg) {
            alert("비교할 메시지를 입력해주세요.");
            return;
        }

        const modelA = $("#model-a-select").val();
        const modelB = $("#model-b-select").val();
        const useRagB = $("#toggle-rag-model-b").is(":checked");  // ✅ Model B RAG 옵션

        const optionsA = {
            max_new_tokens: genOptions.max_new_tokens,
            temperature: genOptions.temperature,
            use_rag: false  // Model A는 RAG 없이
        };
        const optionsB = {
            max_new_tokens: genOptions.max_new_tokens,
            temperature: genOptions.temperature,
            use_rag: useRagB  // Model B는 RAG 옵션 적용
        };

        isCompareSending = true;
        const $btn = $(this);
        $btn.prop("disabled", true).text("비교 중...");

        // ✅ 사용자 입력 먼저 표시
        const userMsgHtml = `<div class="chat-bubble user">${msg}</div>`;

        // 이전 내용 클리어하고 사용자 입력 + 로딩 표시
        $("#compare-box-a").html(userMsgHtml + '<div class="chat-bubble bot text-warning">⏳ Model A 응답 생성 중...</div>');
        $("#compare-box-b").html(userMsgHtml + '<div class="chat-bubble bot text-warning">⏳ Model B 응답 생성 중...</div>');

        // 입력창 비우기
        $("#compare-input").val("");

        // Call both models in parallel
        const callA = API.chat(msg, modelA, optionsA);
        const callB = API.chat(msg, modelB, optionsB);

        Promise.all([callA, callB]).then(([resA, resB]) => {
            const dataA = resA.data || resA;
            const dataB = resB.data || resB;

            const resultA = dataA.result || "(응답 없음)";
            const resultB = dataB.result || "(응답 없음)";

            // ✅ RAG 출처 정보 표시 (Model B)
            let sourcesHtmlB = "";
            if (dataB.sources && dataB.sources.length > 0) {
                sourcesHtmlB = `<div class="rag-sources mt-2 pt-2 border-top border-secondary">
                    <small class="text-muted">📚 참조 출처:</small><ul class="mb-0 ps-3">`;
                dataB.sources.forEach(s => {
                    const pageInfo = s.page ? ` (p.${s.page})` : "";
                    sourcesHtmlB += `<li><small class="text-info">${s.source}${pageInfo}</small></li>`;
                });
                sourcesHtmlB += `</ul></div>`;
            }

            $("#compare-box-a").html(userMsgHtml + `<div class="chat-bubble bot">${resultA.replace(/\n/g, "<br>")}</div>`);
            $("#compare-box-b").html(userMsgHtml + `<div class="chat-bubble bot">${resultB.replace(/\n/g, "<br>")}${sourcesHtmlB}</div>`);
        }).catch(err => {
            console.error("Compare error:", err);
            $("#compare-box-a").html(userMsgHtml + '<div class="chat-bubble bot text-danger">❌ 오류 발생</div>');
            $("#compare-box-b").html(userMsgHtml + '<div class="chat-bubble bot text-danger">❌ 오류 발생</div>');
        }).finally(() => {
            isCompareSending = false;
            $btn.prop("disabled", false).text("비교하기");
        });
    });

    // ✅ 7. Advanced Settings Modal Logic
    function openSettingsModal() {
        try {
            // Load current values into modal
            $("#setting-temp").val(genOptions.temperature);
            $("#label-temp-val").text(genOptions.temperature);
            $("#setting-max-tokens").val(genOptions.max_new_tokens);
            $("#label-tokens-val").text(genOptions.max_new_tokens);
            $("#setting-use-cache").prop("checked", genOptions.use_cache);

            // Open modal
            const modalEl = document.getElementById('chatSettingsModal');
            if (modalEl && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                const modal = new bootstrap.Modal(modalEl);
                modal.show();
            } else {
                $('#chatSettingsModal').modal('show');
            }
        } catch (e) {
            console.error("고급설정 모달 열기 실패:", e);
            alert("고급설정 모달을 열 수 없습니다. 페이지를 새로고침해주세요.");
        }
    }

    // Settings button click handlers
    $("#btn-chat-settings, #btn-compare-settings").on("click", function (e) {
        e.preventDefault();
        console.log("고급설정 버튼 클릭됨");
        openSettingsModal();
    });

    // Settings sliders real-time update
    $("#setting-temp").on("input", function () {
        $("#label-temp-val").text($(this).val());
    });

    $("#setting-max-tokens").on("input", function () {
        $("#label-tokens-val").text($(this).val());
    });

    // Save settings button
    $("#btn-save-settings").on("click", function () {
        genOptions.temperature = parseFloat($("#setting-temp").val());
        genOptions.max_new_tokens = parseInt($("#setting-max-tokens").val());
        genOptions.use_cache = $("#setting-use-cache").is(":checked");

        console.log("설정 저장됨:", genOptions);

        // Close modal
        const modalEl = document.getElementById('chatSettingsModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();

        alert("✅ 설정이 저장되었습니다.");
    });

    // Enter key to send message
    $("#chat-single-input, #compare-input").on("keydown", function (e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            const id = $(this).attr("id");
            if (id === "chat-single-input") $("#btn-single-send").click();
            if (id === "compare-input") $("#btn-compare-send").click();
        }
    });

    // ✅ 8. Document Upload Handler (RAG)
    $("#btn-doc-upload").on("click", function () {
        const files = $("#doc-upload-input")[0].files;
        if (!files || files.length === 0) {
            alert("📂 업로드할 파일을 선택해주세요.");
            return;
        }

        const $btn = $(this);
        const $status = $("#doc-upload-status");
        $btn.prop("disabled", true).text("업로드 중...");
        $status.html('<span class="text-warning">⏳ 업로드 진행 중...</span>');

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append("files", files[i]);
        }

        const token = localStorage.getItem("access_token");

        $.ajax({
            url: "/api/docs/upload",
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
            headers: { "Authorization": "Bearer " + token },
            success: function (res) {
                const data = res.data || res;
                const count = data.results?.length || 0;
                $status.html(`<span class="text-success">✅ ${count}개 파일 업로드 완료!</span>`);
                $("#doc-upload-input").val("");  // Clear file input
            },
            error: function (xhr) {
                const msg = xhr.responseJSON?.error?.message || "업로드 실패";
                $status.html(`<span class="text-danger">❌ ${msg}</span>`);
            },
            complete: function () {
                $btn.prop("disabled", false).text("업로드 (Upload)");
            }
        });
    });

    // ✅ 9. Chart Responsive Resize
    $(window).on("resize", function () {
        if (lossChart.chart) {
            lossChart.chart.resize();
        }
    });
});
