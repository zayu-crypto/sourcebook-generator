const { GoogleGenerativeAI } = require("@google/generative-ai");

const genAI = new GoogleGenerativeAI(process.env.GOOGLE_GEMINI_API_KEY);

const generateCards = async (outcome) => {
  const model = genAI.getGenerativeModel({ model: "gemini-pro" });

  const prompt = `당신은 교육 커리큘럼 설계 전문가입니다. 학습자 주도의 토론 기반 이론 수업을 위한 Sourcebook을 만드는 데 도움을 줍니다.

다음 Learning Outcome을 기반으로 Sourcebook용 카드 10개를 생성해주세요.

**Learning Outcome:**
${outcome}

각 카드는 다음 3가지를 포함해야 합니다:
1. **원천증거 (Primary Evidence)**: 이론을 증명하는 날것의 자료 (실제 사례, 역사적 자료, 논문 초록, 제품 설계도 등)
2. **핵심질문 (Essential Question)**: 단순 정보 찾기를 넘어 지속적인 탐구를 유도하는 본질적인 질문
3. **탐색큐 (Search Cues)**: 깊이 있는 탐구를 위한 최소한의 검색어, 논문 제목, 아카이브 위치 (3개 이내)

**응답 형식은 반드시 JSON이어야 합니다:**
\`\`\`json
{
  "cards": [
    {
      "id": 1,
      "title": "카드 제목",
      "primaryEvidence": "원천증거 내용",
      "essentialQuestion": "핵심질문",
      "searchCues": ["큐1", "큐2", "큐3"]
    },
    ...
  ]
}
\`\`\`

**중요 지침:**
- 각 카드는 독립적으로 하나의 학습 주제를 다루어야 합니다
- 원천증거는 구체적이고 실제 사례여야 합니다
- 핵심질문은 학생들이 계속 생각하게 만드는 질문이어야 합니다
- Learning Outcome과 연결성이 있어야 합니다
- 10개 카드가 서로 다른 각도에서 Outcome을 조명해야 합니다

지금 바로 JSON 형식의 10개 카드를 생성해주세요.`;

  try {
    const result = await model.generateContent(prompt);
    const response = await result.response;
    const text = response.text();
    
    // JSON 추출
    const jsonMatch = text.match(/\`\`\`json\n([\s\S]*?)\n\`\`\`/);
    let cards;
    
    if (jsonMatch) {
      cards = JSON.parse(jsonMatch[1]);
    } else {
      // JSON 블록이 없으면 직접 파싱 시도
      cards = JSON.parse(text);
    }
    
    return cards;
  } catch (error) {
    console.error("Error generating cards:", error);
    throw new Error("카드 생성에 실패했습니다: " + error.message);
  }
};

module.exports = { generateCards };
