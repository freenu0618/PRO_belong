export class LossChart {
    constructor(ctxId, insightId = null) {
        this.ctxId = ctxId;
        this.insightId = insightId;  // 인사이트 메시지 표시 요소 ID
        this.chart = null;
        this.lastAddedStep = -1;
        this.lastEvalStep = -1;
        this.rawTrainingData = [];  // 원본 학습 오차 데이터
        this.rawEvalData = [];      // 원본 시험 오차 데이터
        this.labels = [];           // 스텝 레이블
        this.smoothingFactor = 0.6; // 스무딩 계수 (0 = 원본, 0.99 = 매우 부드러움)
    }

    // ✅ 지수 이동 평균 (EMA) 스무딩
    applySmoothing(data, factor) {
        if (factor === 0 || data.length === 0) return [...data];

        const result = [];
        let prev = null;

        for (const val of data) {
            if (val !== null && val !== undefined) {
                if (prev === null) {
                    prev = val;
                } else {
                    prev = (1 - factor) * val + factor * prev;
                }
                result.push(prev);
            } else {
                result.push(null);
            }
        }
        return result;
    }

    // ✅ Outlier 제외 Y축 범위 계산 (5% 제외)
    calculateYAxisRange(data) {
        const validData = data.filter(v => v !== null && v !== undefined);
        if (validData.length < 5) return { min: undefined, max: undefined };

        const sorted = [...validData].sort((a, b) => a - b);
        const cutoff = Math.floor(sorted.length * 0.05);
        const trimmed = sorted.slice(cutoff, sorted.length - cutoff);

        if (trimmed.length === 0) return { min: undefined, max: undefined };

        const min = Math.min(...trimmed) * 0.95;
        const max = Math.max(...trimmed) * 1.05;
        return { min, max };
    }

    // ✅ 학습 상태 인사이트 분석
    analyzeInsight() {
        const trainData = this.rawTrainingData.filter(v => v !== null);
        const evalData = this.rawEvalData.filter(v => v !== null);

        if (trainData.length < 10) {
            return { status: 'info', message: '⏳ 데이터 수집 중... (10스텝 이상 필요)' };
        }

        // 최근 10개 vs 이전 10개 평균 비교
        const recent = trainData.slice(-10);
        const previous = trainData.slice(-20, -10);

        if (previous.length < 5) {
            return { status: 'info', message: '📊 학습 진행 중...' };
        }

        const recentAvg = recent.reduce((a, b) => a + b, 0) / recent.length;
        const prevAvg = previous.reduce((a, b) => a + b, 0) / previous.length;
        const changeRate = (recentAvg - prevAvg) / prevAvg;

        // 과적합 체크: Eval Loss 증가 + Training Loss 감소
        if (evalData.length >= 2) {
            const lastEval = evalData[evalData.length - 1];
            const prevEval = evalData[evalData.length - 2];
            if (lastEval > prevEval && recentAvg < prevAvg) {
                return {
                    status: 'danger',
                    message: '🔴 과적합 징후 감지! (시험 오차↑, 학습 오차↓) 학습을 조기 종료하거나 데이터를 늘려보세요.'
                };
            }
        }

        if (changeRate < -0.05) {
            return { status: 'success', message: '🟢 학습이 순조롭게 진행 중입니다. (오차 감소 중)' };
        } else if (changeRate > 0.05) {
            return { status: 'warning', message: '🟡 오차가 증가하고 있습니다. 학습률(Learning Rate) 조정을 고려하세요.' };
        } else {
            return { status: 'info', message: '🔵 학습이 안정화 단계에 접어들었습니다.' };
        }
    }

    // ✅ 인사이트 메시지 업데이트
    updateInsight() {
        if (!this.insightId) return;

        const insight = this.analyzeInsight();
        const el = document.getElementById(this.insightId);
        if (!el) return;

        const colorMap = {
            success: 'text-success',
            warning: 'text-warning',
            danger: 'text-danger',
            info: 'text-info'
        };

        el.className = `chart-insight small mb-2 ${colorMap[insight.status] || ''}`;
        el.textContent = insight.message;
    }

    // ✅ 스무딩 계수 변경 (슬라이더 연동)
    setSmoothing(factor) {
        this.smoothingFactor = parseFloat(factor);
        this.refreshChart();
    }

    // ✅ 차트 데이터 갱신 (스무딩 적용)
    refreshChart() {
        if (!this.chart) return;

        const smoothedTrain = this.applySmoothing(this.rawTrainingData, this.smoothingFactor);
        const yRange = this.calculateYAxisRange([...smoothedTrain, ...this.rawEvalData]);

        this.chart.data.datasets[0].data = smoothedTrain;
        this.chart.data.datasets[1].data = this.rawEvalData;  // Eval은 스무딩 안함

        // Y축 범위 최적화
        if (yRange.min !== undefined) {
            this.chart.options.scales.y.suggestedMin = yRange.min;
            this.chart.options.scales.y.suggestedMax = yRange.max;
        }

        this.chart.update('none');
        this.updateInsight();
    }

    init() {
        if (this.chart) {
            this.chart.destroy();
        }

        const ctx = document.getElementById(this.ctxId);
        if (!ctx) return;

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: '📉 학습 오차 (Training Loss)',
                        data: [],
                        borderColor: '#ffc107',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true,
                        spanGaps: false,
                        pointRadius: 0,  // 점 숨김 (스무딩 후 라인만 표시)
                        order: 1  // 뒤에 그리기
                    },
                    {
                        label: '📊 시험 오차 (Eval Loss)',
                        data: [],
                        borderColor: '#00ff88',
                        backgroundColor: 'rgba(0, 255, 136, 0.2)',
                        borderWidth: 3,
                        tension: 0.2,
                        fill: false,
                        spanGaps: true,
                        pointRadius: 8,
                        pointHoverRadius: 12,
                        pointBackgroundColor: '#00ff88',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        order: 0  // 맨 앞에 그리기
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                animation: { duration: 300 },
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: true,
                        labels: { color: '#fff', font: { size: 12 } }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.85)',
                        titleColor: '#fff',
                        bodyColor: '#ccc',
                        padding: 12,
                        callbacks: {
                            label: function (context) {
                                const label = context.dataset.label || '';
                                const value = context.parsed.y?.toFixed(4) || 'N/A';
                                return `${label}: ${value} (↓ 낮을수록 좋음)`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: { display: true, text: '학습 단계 (Step)', color: '#aaa', font: { size: 11 } },
                        ticks: { color: '#aaa', maxTicksLimit: 15 },
                        grid: { color: 'rgba(255,255,255,0.08)' }
                    },
                    y: {
                        title: { display: true, text: '오차 (Loss)', color: '#aaa', font: { size: 11 } },
                        ticks: { color: '#aaa' },
                        grid: { color: 'rgba(255,255,255,0.08)' }
                    }
                }
            }
        });

        // 데이터 초기화
        this.rawTrainingData = [];
        this.rawEvalData = [];
        this.labels = [];
        this.lastAddedStep = -1;
        this.lastEvalStep = -1;

        console.log(`📊 Chart initialized (Enhanced UX: 스무딩, 인사이트, 한글화)`);
    }

    update(step, loss, evalLoss) {
        if (!this.chart) return;

        // Training loss가 없으면 evaluation 중
        if (loss === undefined || loss === null) {
            return;
        }

        // 중복 step 방지
        if (step <= this.lastAddedStep) {
            return;
        }

        // 원본 데이터 저장
        this.labels.push(step);
        this.rawTrainingData.push(loss);

        // Eval Loss: 실제 값이 있을 때만 저장
        if (evalLoss !== undefined && evalLoss !== null && step !== this.lastEvalStep) {
            this.rawEvalData.push(evalLoss);
            this.lastEvalStep = step;
        } else {
            this.rawEvalData.push(null);
        }

        this.lastAddedStep = step;

        // 차트 레이블 업데이트
        this.chart.data.labels = this.labels;

        // 스무딩 적용 후 갱신
        this.refreshChart();
    }

    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
        this.rawTrainingData = [];
        this.rawEvalData = [];
        this.labels = [];
    }
}
