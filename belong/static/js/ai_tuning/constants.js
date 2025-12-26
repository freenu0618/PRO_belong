export const helpContent = {
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

export const descriptions = {
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
