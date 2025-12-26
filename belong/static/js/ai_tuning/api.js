export const API = {
    getToken() {
        return localStorage.getItem("access_token");
    },

    getModels() {
        return $.ajax({
            url: "/api/tuning/models",
            method: "GET"
        });
    },

    deleteModel(modelName) {
        const token = this.getToken();
        return $.ajax({
            url: `/api/tuning/models/${modelName}`,
            method: "DELETE",
            headers: { "Authorization": "Bearer " + token }
        });
    },

    startTraining(formData) {
        const token = this.getToken();
        return $.ajax({
            url: "/api/tuning/start",
            type: "POST",
            contentType: "application/json",
            headers: { "Authorization": "Bearer " + token },
            data: JSON.stringify(formData)
        });
    },

    getTrainingStatus(jobId) {
        const token = this.getToken();
        return $.ajax({
            url: `/api/tuning/status/${jobId}`,
            method: "GET",
            headers: { "Authorization": "Bearer " + token }
        });
    },

    chat(msg, model, options) {
        const token = this.getToken();
        const payload = {
            text: msg,
            model: model,
            options: options
        };
        return $.ajax({
            url: "/api/tuning/chat",
            type: "POST",
            contentType: "application/json",
            headers: { "Authorization": "Bearer " + token },
            data: JSON.stringify(payload)
        });
    },

    compare(msg, model, options) {
        const token = this.getToken();
        const payload = {
            text: msg,
            model: model,
            options: options
        };
        return $.ajax({
            url: "/api/tuning/compare",
            type: "POST",
            contentType: "application/json",
            headers: { "Authorization": "Bearer " + token },
            data: JSON.stringify(payload)
        });
    }
};
