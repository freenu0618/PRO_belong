export const Formatter = {
    humanizeResponse(mode, result) {
        try {
            if (typeof result === "string") return this.formatMarkdown(result);

            // Agent & Chat
            if (mode === "agent" || mode === "chat") {
                return this.formatMarkdown(result.response || JSON.stringify(result));
            }

            // Sentiment
            if (mode === "sentiment") {
                const data = Array.isArray(result) ? result[0] : result;
                if (!data) return this.formatMarkdown(JSON.stringify(result, null, 2));

                const labelMap = { "POSITIVE": "긍정", "NEGATIVE": "부정", "0": "부정", "1": "긍정", "neutral": "중립" };
                let label = labelMap[String(data.label).toUpperCase()] || data.label;
                let score = (data.score * 100).toFixed(1);

                let msg = "";
                if (label === "긍정") msg = `이 문장은 **${score}%**의 확률로 **긍정적**인 내용을 담고 있네요! 😄`;
                else if (label === "부정") msg = `음, 이 문장은 **${score}%**의 확률로 **부정적**인 감정이 느껴집니다. 😟`;
                else msg = `이 문장의 감정은 **${label}** (${score}%)로 분석됩니다.`;

                return this.formatMarkdown(msg);
            }

            // Entities
            if (mode === "entities") {
                let list = result.entities || result;
                if (!Array.isArray(list)) return this.formatMarkdown(JSON.stringify(result, null, 2));
                if (list.length === 0) return "이 문장에서는 특별한 인물이나 장소 같은 개체명을 찾지 못했습니다.";

                let msg = "문장에서 다음과 같은 주요 키워드를 발견했습니다:\n\n";
                list.forEach(item => {
                    let type = item.entity_group || item.entity || "Unknown";
                    msg += `- **${item.text}** (${type})\n`;
                });
                return this.formatMarkdown(msg);
            }

            // Translate
            if (mode === "translate") {
                if (result.translation) return this.formatMarkdown(result.translation);
                if (result.translation_text) return this.formatMarkdown(result.translation_text);
            }

            // Summary
            if (mode === "summary") {
                if (result.summary) return this.formatMarkdown(`**[요약 결과]**\n\n${result.summary}`);
                if (result.summary_text) return this.formatMarkdown(`**[요약 결과]**\n\n${result.summary_text}`);
            }

            // QA
            if (mode === "qa") {
                if (!result.answer) return "질문에 대한 적절한 답변을 찾지 못했습니다. Context를 확인해 주세요.";
                return this.formatMarkdown(`**답변:** ${result.answer}`);
            }

            // Rerank
            if (mode === "rerank") {
                if (!result.ranked_documents || result.ranked_documents.length === 0) return this.formatMarkdown("재순위 결과가 없습니다.");
                let msg = "**📊 문서 재순위 결과:**\n\n";
                result.ranked_documents.forEach((doc, i) => {
                    msg += `${i + 1}. (${(doc.score * 100).toFixed(1)}%) ${doc.text.substring(0, 100)}...\n\n`;
                });
                return this.formatMarkdown(msg);
            }

            // Text Gen
            if (mode === "text-gen") {
                if (result.error) return this.formatMarkdown(`**오류:** ${result.error}`);
                if (result.raw_output) return this.formatMarkdown(`**✨ AI 생성 결과:**\n\n${result.raw_output}`);
                return this.formatMarkdown("생성된 텍스트가 없습니다.");
            }

            return this.formatMarkdown(JSON.stringify(result, null, 2));

        } catch (e) {
            console.error("Humanize Error:", e);
            return this.formatMarkdown("결과를 표시하는 중 오류가 발생했습니다.\n\n" + JSON.stringify(result));
        }
    },

    formatMarkdown(text) {
        if (!text) return "";
        const codeBlocks = [];
        let out = text.replace(/```(\w+)?\n?([\s\S]*?)```/g, function (match, lang, code) {
            codeBlocks.push({ lang: lang || "text", code: code.trim() });
            return `__CODE_BLOCK_${codeBlocks.length - 1}__`;
        });

        out = out.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        out = out.replace(/\n/g, '<br>');

        codeBlocks.forEach((block, i) => {
            const html = `<div class="ai-code-block"><div class="code-header"><span class="lang">${block.lang}</span><button class="btn-copy">Copy</button></div><pre><code>${block.code}</code></pre><div style="display:none;" class="raw-code">${block.code}</div></div>`;
            out = out.replace(`__CODE_BLOCK_${i}__`, html);
        });
        return out;
    }
};
