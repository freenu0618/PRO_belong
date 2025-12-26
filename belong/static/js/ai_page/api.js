export const API = {
    getToken() {
        return localStorage.getItem("access_token") || "";
    },

    getModels() {
        return $.ajax({
            url: "/api/tuning/models",
            method: "GET"
        });
    },

    runAI(mode, payload) {
        const token = this.getToken();
        let endpoint = `/api/ai/${mode}`;

        // Endpoint overrides
        if (mode === "agent") endpoint = "/api/ai/chat";
        if (mode === "rerank") endpoint = "/api/ai/rerank";
        if (mode === "text-gen") endpoint = "/api/ai/text-gen";

        return $.ajax({
            url: endpoint,
            method: "POST",
            contentType: "application/json",
            headers: { "Authorization": "Bearer " + token },
            data: JSON.stringify(payload)
        });
    }
};
