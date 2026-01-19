export const UI = {
    $chatBox: $("#ai-chat-box"),
    $input: $("#ai-input-text"),
    $sendBtn: $("#ai-run-btn"),
    $typingIndicator: null,

    addBubble(role, text) {
        let html = (role === "user") ? `<div style="white-space:pre-wrap;">${text}</div>` : text;
        this.addRawBubble(role, html);
    },

    addRawBubble(role, htmlContent) {
        const bubbleClass = role === "user" ? "ai-user" : "ai-assistant";
        const $el = $(`<div class="ai-bubble ${bubbleClass}"></div>`).html(htmlContent).hide();
        this.$chatBox.append($el);
        $el.fadeIn(300);
        document.getElementById("ai-chat-container").scrollTop = 99999;
        return $el;
    },

    setLoading(isLoading) {
        this.$sendBtn.prop("disabled", isLoading);
        if (isLoading) this.showTyping();
        else {
            if (this.$typingIndicator) {
                this.$typingIndicator.remove();
                this.$typingIndicator = null;
            }
            this.$input.focus();
        }
    },

    showTyping() {
        const tmpl = `<div class="d-flex align-items-center gap-1" style="height:24px;">
          <span class="typing-dot" style="animation-delay:0s">●</span>
          <span class="typing-dot" style="animation-delay:0.2s">●</span>
          <span class="typing-dot" style="animation-delay:0.4s">●</span>
        </div>`;
        this.$typingIndicator = this.addRawBubble("assistant", tmpl);
    },

    toggleSidebar() {
        $("#ai-sidebar").toggleClass("open");
        $("#ai-sidebar-overlay").toggleClass("show");
    },

    closeSidebar() {
        $("#ai-sidebar").removeClass("open");
        $("#ai-sidebar-overlay").removeClass("show");
    }
};
