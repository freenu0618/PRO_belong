import { API } from './api.js';
import { Formatter } from './formatter.js';
import { UI } from './ui.js';

$(document).ready(function () {
    let currentMode = "translate";

    const modeLabels = {
        translate: "AI 번역",
        summary: "텍스트 요약",
        rerank: "문서 재순위 (Reranker)",
        "text-gen": "AI 텍스트 생성",
        qa: "질의 응답",
        agent: "AI Agent (RAG)",
        comparison: "모델 비교 (Base vs Tuned)",
        guide: "사용 가이드"
    };

    // 0. Initial Load
    const urlParams = new URLSearchParams(window.location.search);
    const initialMode = urlParams.get('mode');

    // AI 허브는 정해진 유틸리티 모델만 사용 (파인튜닝 모델 X)
    // 번역, 요약 등은 model_loader.py의 UTILITY_MODELS 사용
    // 모델 선택 로직 제거 (각 기능별로 고정 모델 사용)

    if (initialMode && modeLabels[initialMode]) {
        setTimeout(() => $(`.ai-nav-btn[data-mode="${initialMode}"]`).click(), 50);
    }

    // 1. Mode Switching
    $(".ai-nav-btn[data-mode]").on("click", function () {
        const mode = $(this).data("mode");
        if (mode === "guide") {
            runGuide();
            return;
        }

        $(".ai-nav-btn").removeClass("active");
        $(this).addClass("active");

        currentMode = mode;
        $("#current-mode-label").text(modeLabels[currentMode]);

        // UI toggles
        $("#opt-translate, #opt-qa, #opt-rag, #opt-model-select").hide();

        if (currentMode === "translate") $("#opt-translate").show();

        // Show Model Select for Agent (Chat) and QA
        if (currentMode === "agent" || currentMode === "qa") { // Chat related modes
            $("#opt-model-select").show();
        }

        if (currentMode === "qa") {
            $("#opt-qa").show();
            $("#opt-rag").show();
        }


        $("#ai-chat-box").removeClass("d-none");
        $("#ai-compare-box").addClass("d-none");
        $("#ai-welcome").hide();
        UI.$input.focus();
    });

    // 2. Event Listeners
    $("#ai-run-btn").on("click", runAI);
    $("#ai-input-text").on("keydown", function (e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            runAI();
        }
    });

    // Auto-grow textarea
    $("#ai-input-text").on("input", function () {
        this.style.height = "auto";
        this.style.height = (this.scrollHeight) + "px";
        if (this.value === "") this.style.height = "auto";
    });

    // Copy Button Logic
    $(document).on("click", ".btn-copy", function () {
        const $btn = $(this);
        const rawCode = $btn.closest(".ai-code-block").find(".raw-code").text();
        navigator.clipboard.writeText(rawCode).then(() => {
            const orig = $btn.text();
            $btn.text("Copied!");
            setTimeout(() => $btn.text(orig), 2000);
        });
    });

    // Sidebar Logic
    $("#btn-toggle-sidebar").on("click", (e) => {
        e.stopPropagation();
        UI.toggleSidebar();
    });
    $("#ai-sidebar-overlay").on("click", UI.closeSidebar);

    // ✅ Options Menu Toggle (번역 방향 등 설정 표시/숨김)
    $("#btn-toggle-options").on("click", function (e) {
        e.stopPropagation();
        const $menu = $("#ai-options-menu");
        $menu.toggleClass("show");
    });

    // Options 메뉴 외부 클릭 시 닫기
    $(document).on("click", function (e) {
        const $menu = $("#ai-options-menu");
        const $btn = $("#btn-toggle-options");
        if (!$menu.is(e.target) && $menu.has(e.target).length === 0 &&
            !$btn.is(e.target) && $btn.has(e.target).length === 0) {
            $menu.removeClass("show");
        }
    });

    // 3. Main Action
    function runAI() {
        const text = UI.$input.val().trim();
        if (!text) return;

        UI.$input.val("").css("height", "auto");
        UI.addBubble("user", UI.escapeHtml ? UI.escapeHtml(text) : text);
        // escapeHtml is not in UI object but simple jquery can handle it or add it to UI
        // Actually UI.addBubble handles html content if role is user by wrapping in div with pre-wrap

        UI.setLoading(true);

        const token = API.getToken();
        if (!token) {
            UI.addBubble("assistant", "로그인이 필요합니다.");
            UI.setLoading(false);
            return;
        }

        const payload = { text: text, options: {} };
        const selectedModel = $("#ai-model-select").val() || "base";

        if (currentMode === "agent") {
            payload.model = selectedModel;
            payload.options.use_rag = true;
        } else if (currentMode === "qa") {
            payload.model = selectedModel; // QA도 모델 선택 가능하게 지원
            payload.options.context = $("#opt-qa-context").val();
            payload.options.use_rag = $("#opt-use-rag").is(":checked");
        } else if (currentMode === "translate") {
            payload.options.direction = $("#opt-trans-direction").val();
        } else if (currentMode === "rerank") {
            delete payload.text;
            payload.query = text;
            payload.documents = text.split("\n").filter(line => line.trim().length > 10);
            if (payload.documents.length === 0) payload.documents = [text];
        } else if (currentMode === "text-gen") {
            delete payload.text;
            payload.prompt = text;
        }

        API.runAI(currentMode, payload).then(resp => {
            let content = "결과를 가져올 수 없습니다.";
            if (resp.result) {
                content = Formatter.humanizeResponse(currentMode, resp.result);
            } else if (resp.message) {
                content = resp.message;
            }
            UI.addBubble("assistant", content);
        }).catch(() => {
            UI.addBubble("assistant", "오류가 발생했습니다. (서버 연결 실패)");
        }).always(() => {
            UI.setLoading(false);
        });
    }

    function runGuide() {
        $("#ai-welcome").hide();
        const guideText = `
**[AI 사용 가이드]**

1. **AI 번역**: 한영/영한 번역을 해줍니다.
2. **감정 분석**: 문장에 담긴 감정(긍정/부정)을 분석해줍니다.
3. **개체 분석**: 문장에서 인물, 장소 등 키워드를 찾습니다.
4. **텍스트 요약**: 긴 글을 요약합니다.
5. **질의 응답**: Context 입력창에 글을 넣고 질문하면 답해줍니다.

왼쪽 메뉴에서 기능을 선택하고 대화를 시작해 보세요!
        `;
        UI.addBubble("assistant", Formatter.formatMarkdown(guideText));
    }
});
