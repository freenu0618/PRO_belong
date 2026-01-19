/**
 * API 호출 래퍼
 * 모든 AJAX 호출을 표준화하고 에러 처리를 통일합니다.
 */

const API = {
    /**
     * 기본 API 호출 함수
     * @param {string} url - API 엔드포인트 URL
     * @param {string} method - HTTP 메서드 (GET, POST, etc.)
     * @param {object|null} data - 요청 데이터
     * @param {object} options - 추가 옵션
     * @returns {Promise} jQuery Promise
     */
    call: function (url, method = 'GET', data = null, options = {}) {
        const token = localStorage.getItem('access_token');

        const ajaxConfig = {
            url: url,
            type: method,
            contentType: 'application/json',
            headers: {},
            ...options
        };

        // JWT 토큰 추가
        if (token) {
            ajaxConfig.headers['Authorization'] = `Bearer ${token}`;
        }

        // 데이터 추가 (GET 제외)
        if (data && method !== 'GET') {
            ajaxConfig.data = JSON.stringify(data);
        }

        return $.ajax(ajaxConfig)
            .fail(function (xhr) {
                // 공통 에러 처리
                API.handleError(xhr);
            });
    },

    /**
     * GET 요청
     */
    get: function (url, params = null) {
        let fullUrl = url;
        if (params) {
            const queryString = $.param(params);
            fullUrl += `?${queryString}`;
        }
        return this.call(fullUrl, 'GET');
    },

    /**
     * POST 요청
     */
    post: function (url, data) {
        return this.call(url, 'POST', data);
    },

    /**
     * PUT 요청
     */
    put: function (url, data) {
        return this.call(url, 'PUT', data);
    },

    /**
     * DELETE 요청
     */
    delete: function (url) {
        return this.call(url, 'DELETE');
    },

    /**
     * 파일 업로드 (multipart/form-data)
     */
    upload: function (url, formData) {
        const token = localStorage.getItem('access_token');

        return $.ajax({
            url: url,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        }).fail(function (xhr) {
            API.handleError(xhr);
        });
    },

    /**
     * 공통 에러 처리
     */
    handleError: function (xhr) {
        const response = xhr.responseJSON;

        // 401 Unauthorized - 로그인 페이지로 리다이렉트
        if (xhr.status === 401) {
            localStorage.removeItem('access_token');
            alert('세션이 만료되었습니다. 다시 로그인해주세요.');
            window.location.href = '/login';
            return;
        }

        // 표준 에러 응답 형식
        if (response && response.ok === false) {
            const errorMsg = response.error?.message || '알 수 없는 오류가 발생했습니다';
            console.error('[API Error]', errorMsg, response.error?.details);
        } else {
            console.error('[네트워크 오류]', xhr.status, xhr.statusText);
        }
    },

    /**
     * 성공 응답에서 데이터 추출
     */
    extractData: function (response) {
        if (response.ok === true) {
            return response.data || response;
        }
        throw new Error(response.error?.message || '응답 형식 오류');
    }
};

// 전역으로 사용 가능하도록 설정
window.API = API;
