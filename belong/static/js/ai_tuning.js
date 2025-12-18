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
        `
    };

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
    const hash = window.location.hash.replace("#section-", "");
    if (hash && ["tuning", "chat", "compare"].includes(hash)) {
        // Trigger click on corresponding nav button
        $(`.tuning-nav-btn[data-section="${hash}"]`).click();
    } else if ($("#section-tuning").hasClass("active")) {
        // Default (Tuning)
        // showHelp('tuning'); // Uncomment if you want it to pop up immediately on page load
    }

    // 3. Form Handling (Using real endpoint placeholder)
    $("#tuning-form").on("submit", function (e) {
        e.preventDefault();
        // Phase 3: RunPod API Integration (Next Step)
        alert("RunPod 파인튜닝 시작! (Backend: /api/tuning/start 연동 예정)\n\n" + $(this).serialize());
    });

    // 4. Chat & Compare Logic (Real API)
    let chatOptions = { temperature: 0.7 };

    // Settings Modal Logic
    $("#btn-chat-settings").on("click", function () {
        // Load current value
        $("#setting-temp").val(chatOptions.temperature);
        $("#label-temp-val").text(chatOptions.temperature);
        new bootstrap.Modal(document.getElementById('chatSettingsModal')).show();
    });

    $("#setting-temp").on("input", function () {
        $("#label-temp-val").text($(this).val());
    });

    $("#btn-save-settings").on("click", function () {
        chatOptions.temperature = parseFloat($("#setting-temp").val());
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

    $("#btn-single-send").on("click", function () {
        const msg = $("#chat-single-input").val().trim(); // Use trim()
        if (!msg) return;

        const model = $("#chat-model-select").val() || "llama3-8b-base-q4"; // Updated ID

        $("#chat-single-box").append(`<div class="chat-bubble user">${msg.replace(/\n/g, "<br>")}</div>`);
        $("#chat-single-input").val("");
        $("#chat-single-box").scrollTop($("#chat-single-box")[0].scrollHeight);

        // Show loading
        const loadingId = "loading-" + Date.now();
        $("#chat-single-box").append(`<div id="${loadingId}" class="chat-bubble bot">...</div>`);
        $("#chat-single-box").scrollTop($("#chat-single-box")[0].scrollHeight);

        const token = localStorage.getItem("access_token");
        if (!token) {
            alert("로그인 후 이용 가능합니다.");
            window.location.href = "/login";
            return;
        }

        $.ajax({
            url: "/api/tuning/chat",
            type: "POST",
            contentType: "application/json",
            headers: { "Authorization": "Bearer " + token },
            data: JSON.stringify({
                text: msg,
                model: model,
                options: chatOptions
            }),
            success: function (res) {
                // Formatting newlines in response
                const formatted = (res.result || "").replace(/\n/g, "<br>");
                $(`#${loadingId}`).html(formatted);
            },
            error: function (xhr) {
                const err = xhr.responseJSON?.message || "답변을 가져오지 못했습니다. (모델 상태를 확인해주세요)";
                $(`#${loadingId}`).html(`<span class="text-danger">Error: ${err}</span>`);
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
            // Compare feature specific limits
            const compareOptions = Object.assign({}, chatOptions, { num_predict: 500 });

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
                    options: compareOptions
                }),
                success: function (res) {
                    const formatted = (res.result || "").replace(/\n/g, "<br>");
                    $(`#${targetId}`).html(formatted);
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
});

