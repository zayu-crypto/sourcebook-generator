#!/usr/bin/env python3
import os
import json
import re
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Google Generative AI
API_KEY = os.getenv('GOOGLE_GEMINI_API_KEY')
if not API_KEY:
    print("⚠️  Warning: GOOGLE_GEMINI_API_KEY is not set")
else:
    genai.configure(api_key=API_KEY)

def search_wikimedia_image(query, max_retries=3):
    """Wikimedia Commons에서 이미지 검색 (재시도 로직 포함)"""
    for attempt in range(max_retries):
        try:
            print(f"🔍 Searching Wikimedia for: {query} (attempt {attempt+1}/{max_retries})")
            
            url = "https://commons.wikimedia.org/w/api.php"
            headers = {
                'User-Agent': 'SourcebookGenerator/1.0 (Educational tool; +http://localhost:8000)'
            }
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': query,
                'srnamespace': 6,
                'format': 'json',
                'srlimit': 30
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"  ⚠️  HTTP {response.status_code}, retrying...")
                continue
                
            results = response.json()
            search_results = results.get('query', {}).get('search', [])
            
            if not search_results:
                # 검색 실패 시 더 간단한 키워드로 재시도
                if len(query) > 10:
                    simpler_query = query.split()[0]
                    print(f"  ⚠️  No results, trying simpler query: {simpler_query}")
                    return search_wikimedia_image(simpler_query, max_retries=1)
                continue
            
            print(f"  📋 Found {len(search_results)} results, finding valid image...")
            
            # 검색 결과 중에서 유효한 이미지 찾기
            for idx, result in enumerate(search_results[:15]):
                title = result.get('title', '')
                if title.startswith('File:'):
                    title = title[5:]
                
                info_params = {
                    'action': 'query',
                    'titles': f'File:{title}',
                    'prop': 'imageinfo',
                    'iiprop': 'url|mime',
                    'format': 'json'
                }
                
                try:
                    info_response = requests.get(url, params=info_params, headers=headers, timeout=10)
                    info_results = info_response.json()
                    pages = info_results.get('query', {}).get('pages', {})
                    
                    for page_id, page_data in pages.items():
                        if page_id == '-1' or 'imageinfo' not in page_data:
                            continue
                        
                        image_info = page_data['imageinfo'][0]
                        image_url = image_info.get('url', '')
                        mime_type = image_info.get('mime', '')
                        
                        if not image_url or not mime_type.startswith('image/'):
                            continue
                        
                        # URL이 실제로 작동하는지 빠르게 확인
                        try:
                            head_response = requests.head(image_url, headers=headers, timeout=3)
                            if head_response.status_code == 200:
                                print(f"  ✅ Found valid image: {title}")
                                return image_url, title
                        except:
                            # URL 검증 실패해도 일단 반환 (많은 이미지가 HEAD 요청 거절)
                            print(f"  ✅ Found image (unverified): {title}")
                            return image_url, title
                except Exception as e:
                    continue
            
            print(f"  ⚠️  No valid images in results, retrying...")
            
        except Exception as e:
            print(f"  ⚠️  Error: {e}, retrying...")
            continue
    
    print(f"❌ Failed to find image after {max_retries} attempts")
    return None, None

def generate_cards(outcome):
    """Generate sourcebook cards using Google Generative AI"""
    try:
        # 사용 가능한 모델 목록 확인
        try:
            models = genai.list_models()
            available_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
            model_name = available_models[0] if available_models else 'models/gemini-2.0-flash'
            model_name = model_name.replace('models/', '')
        except:
            model_name = 'gemini-2.0-flash'
        
        model = genai.GenerativeModel(model_name)
        
        prompt = """당신은 Understanding by Design 원칙을 따르는 교육 설계 전문가입니다.

## 당신의 임무
주어진 Learning Outcome을 분석하고, 이 학습 목표를 달성하기 위한 Sourcebook 카드 10개를 생성하세요.

## Learning Outcome:
{0}

## 핵심 원칙
1. **모든 카드는 위 Learning Outcome에 직접적으로 연결**되어야 합니다. 관련 없는 주제를 포함하지 마세요.
2. 카드는 '지식'이 아니라 '지식으로 향하는 좌표'입니다 — 학습자가 스스로 탐색하도록 돕는 최소한의 단서를 제공하세요.
3. 각 카드는 Learning Outcome의 서로 다른 측면을 다뤄야 합니다 (중복 금지).

## 카드 설계 프로세스
각 카드를 만들 때 다음 순서를 따르세요:

**Step 1: Learning Outcome에서 핵심 개념 추출**
- 이 Outcome이 요구하는 지식, 기술, 태도를 파악하세요.

**Step 2: 원천 증거 (Primary Evidence) 선택**
- 해당 개념을 증명하는 역사적/실제 사례를 찾으세요.
- Wikimedia Commons에서 검색 가능한 구체적인 인물, 사건, 작품, 도구를 선택하세요.
- imageSearchKeyword는 영어로, 구체적인 고유명사를 포함하세요 (예: "Alexander Graham Bell telephone 1876", "DNA double helix Watson Crick").

**Step 3: 핵심 질문 (Essential Question) 설계**
- 단순 정보 검색이 아닌, 깊은 사고를 유도하는 질문을 만드세요.
- 원천 증거와 Learning Outcome을 연결하는 질문이어야 합니다.
- "왜?", "어떻게?", "만약 ~라면?" 형태가 효과적입니다.

**Step 4: 탐색 큐 (Search Cues) 설계**
- 학습자가 깊이 탐구할 수 있는 구체적 검색어 3개를 제공하세요.
- 핵심 키워드, 관련 이론/논문명, 참고 자료 등을 포함하세요.

## 응답 형식
반드시 아래 JSON 배열 형식으로만 응답하세요. 다른 텍스트를 추가하지 마세요:
[{{"id": 1, "title": "카드 제목", "coreImage": {{"imageSearchKeyword": "English search keyword with specific names", "source": "Wikimedia Commons", "caption": "한 줄 설명"}}, "essentialQuestion": "핵심 질문", "searchCues": ["탐색큐1", "탐색큐2", "탐색큐3"]}}]

10개 카드를 생성하세요.""".format(outcome)

        response = model.generate_content(prompt)
        text = response.text
        
        print(f"📝 Raw response length: {len(text)} characters")
        
        # Extract JSON from response
        json_str = None
        json_match = re.search(r'```json\n([\s\S]*?)\n```', text)
        if json_match:
            json_str = json_match.group(1)
            print("✅ Found JSON in code block")
        else:
            # Try to find JSON without code block markers
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                json_str = json_match.group(0)
                print("✅ Found JSON without code block")
            else:
                print(f"❌ Could not find JSON in response: {text[:200]}")
                raise ValueError("Could not extract JSON from response")
        
        cards_data = json.loads(json_str)
        print(f"📊 Parsed JSON type: {type(cards_data)}")
        
        # Handle both dict and list responses
        if isinstance(cards_data, dict):
            cards_list = cards_data.get('cards', [])
        elif isinstance(cards_data, list):
            cards_list = cards_data
        else:
            raise ValueError(f"Unexpected JSON type: {type(cards_data)}")
        
        print(f"📋 Found {len(cards_list)} cards")
        
        # 각 카드의 이미지 검색 및 업데이트
        for idx, card in enumerate(cards_list):
            print(f"\n[{idx+1}/{len(cards_list)}] Processing card: {card.get('title', 'Unknown')}")
            
            if not isinstance(card, dict):
                print(f"  ⚠️  Card is not a dict: {type(card)}")
                continue
            
            if 'coreImage' in card and isinstance(card['coreImage'], dict):
                if 'imageSearchKeyword' in card['coreImage']:
                    search_keyword = card['coreImage']['imageSearchKeyword']
                    print(f"  🔍 Searching image for: {search_keyword}")
                    
                    image_url, filename = search_wikimedia_image(search_keyword)
                    if image_url:
                        card['coreImage']['url'] = image_url
                        print(f"  ✅ Found: {filename}")
                    else:
                        print(f"  ❌ No image found for: {search_keyword}")
                        card['coreImage']['url'] = ""
                    
                    # imageSearchKeyword 제거 (최종 응답에 불필요)
                    if 'imageSearchKeyword' in card['coreImage']:
                        del card['coreImage']['imageSearchKeyword']
        
        # Return proper format
        return {"cards": cards_list}
        
    except Exception as e:
        print(f"❌ Error generating cards: {e}")
        import traceback
        traceback.print_exc()
        raise Exception(f"카드 생성에 실패했습니다: {str(e)}")

@app.route('/api/generate-cards', methods=['POST'])
def api_generate_cards():
    """API endpoint to generate cards"""
    try:
        data = request.get_json()
        outcome = data.get('outcome', '').strip()
        
        if not outcome:
            return jsonify({'error': 'Learning Outcome이 필요합니다'}), 400
        
        print(f"Generating cards for outcome: {outcome[:100]}...")
        cards = generate_cards(outcome)
        
        return jsonify(cards), 200
        
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/refine-outcome', methods=['POST'])
def api_refine_outcome():
    """API endpoint to refine a draft Learning Outcome"""
    try:
        data = request.get_json()
        draft = data.get('draft', '').strip()

        if not draft:
            return jsonify({'error': 'Learning Outcome 초안이 필요합니다'}), 400

        try:
            models = genai.list_models()
            available_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
            model_name = available_models[0] if available_models else 'models/gemini-2.0-flash'
            model_name = model_name.replace('models/', '')
        except:
            model_name = 'gemini-2.0-flash'

        model = genai.GenerativeModel(model_name)

        prompt = """당신은 해당 분야의 전문 지식을 갖춘 교육 설계 전문가입니다.
사용자가 작성한 Learning Outcome 초안의 "빈칸"을 채워서, 수업에 바로 쓸 수 있을 만큼 구체적으로 만들어주세요.

## 사용자의 초안:
{0}

## 당신의 핵심 임무: 빈칸 채우기

초안에는 대부분 모호한 표현이 있습니다. 당신의 역할은 **문장을 예쁘게 다듬는 것이 아니라, 빠져 있는 구체적 내용을 직접 채워넣는 것**입니다.

### 빈칸 채우기 원칙

**1. 고유명사를 넣어라**
- "주요 학파" → 어떤 학파인지 직접 이름을 대라 (예: "피타고라스 학파, 칸트의 판단력 비판, 바우하우스 조형 원리")
- "역사적 사례" → 어떤 시대, 어떤 인물, 어떤 사건인지 특정하라 (예: "고대 그리스의 황금비, 르네상스 원근법, 일본 와비사비")
- "기술/도구" → 구체적 기술명을 넣어라 (예: "React의 가상 DOM, WebSocket 실시간 통신")

**2. 범위를 숫자로 한정하라**
- "다양한 사례" → 몇 개인지 명시 (예: "3개 이상의 시대별 사례")
- "주요 개념" → 핵심 2-4개를 직접 나열

**3. 최종 산출물을 명시하라**
- "지적 지도를 그린다" → 어떤 형태인지 (예: "시대순 비교표로 정리", "관계도로 시각화", "500자 내외의 비교 분석문 작성")
- "이해한다" → 무엇을 할 수 있는지 (예: "차이점 3가지를 근거와 함께 서술할 수 있다")

**4. 맥락/조건을 붙여라**
- "분석할 수 있다" → 어떤 자료를 가지고? 어떤 관점에서?
- 빠진 전제조건을 추가하라

## 좋은 변환 예시

초안: "아름다움의 기준에 대해 역사적으로 다뤄진 사례들을 이해하고 주요 학파들이 어떤 것들이 있었는지 지적 지도를 그리게 된다"

개선: "고대 그리스(플라톤의 이데아론, 피타고라스의 수적 조화), 중세(토마스 아퀴나스의 신학적 미), 근대(칸트의 미적 판단, 헤겔의 예술철학), 현대(단토의 예술 종말론) 등 최소 4개 시대의 미학 사조를 비교하여, 각 학파가 정의한 '아름다움'의 핵심 기준과 시대 간 변화를 계보도 형태로 정리하고 설명할 수 있다."

→ 변환 포인트: "주요 학파"를 구체적 이름 8개로 채움, "지적 지도"를 "계보도"로 구체화, 시대 수를 "최소 4개"로 한정

초안: "데이터를 분석할 수 있다"

개선: "주어진 웹 로그 데이터에서 사용자 이탈률, 체류시간, 전환 퍼널 3가지 지표를 추출하고, 이탈이 집중되는 단계를 식별하여 개선 가설을 제안할 수 있다."

→ 변환 포인트: "데이터"를 "웹 로그"로 특정, 분석 대상을 3가지 지표로 명시, 산출물을 "개선 가설 제안"으로 구체화

## 규칙
- 초안의 주제 영역 안에서 구체화하세요. 완전히 다른 주제를 넣지 마세요.
- 당신이 채워넣는 고유명사와 예시는 해당 분야에서 실제로 중요한 것이어야 합니다. 아무거나 넣지 마세요.
- 한국어로 작성하세요.
- **단순히 문장을 매끄럽게 고치는 것은 금지**합니다. 반드시 새로운 정보(이름, 숫자, 산출물 형태)가 추가되어야 합니다.

## 응답 형식
반드시 아래 JSON 형식으로만 응답하세요:
{{"refined": "구체화된 Outcome (2-4문장. 고유명사, 숫자, 산출물 형태가 반드시 포함되어야 함)", "changes": "어떤 빈칸을 무엇으로 채웠는지 한 줄 설명"}}""".format(draft)

        response = model.generate_content(prompt)
        text = response.text

        json_str = None
        json_match = re.search(r'```json\n([\s\S]*?)\n```', text)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("Could not extract JSON from response")

        result = json.loads(json_str)
        return jsonify(result), 200

    except Exception as e:
        print(f"Refine error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'Server is running'}), 200


# Serve frontend static files when deployed as a single app
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT_DIR = os.path.join(BASE_DIR, 'client')

@app.route('/')
def serve_index():
    return send_from_directory(CLIENT_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    filepath = os.path.join(CLIENT_DIR, filename)
    if os.path.exists(filepath):
        return send_from_directory(CLIENT_DIR, filename)
    return jsonify({'error': 'File not found'}), 404


if __name__ == '__main__':
    print("🚀 Sourcebook Generator Server starting...")

    port = int(os.environ.get('PORT', 5000))
    is_production = os.environ.get('ENVIRONMENT', 'development') == 'production'

    if is_production:
        print(f"📡 Production mode - running on port {port}")
    else:
        print(f"📡 Development mode - running on http://localhost:{port}")
        print("\n다음 단계:")
        print("1. 환경변수 GOOGLE_GEMINI_API_KEY가 설정되어 있는지 확인하세요")
        print("2. 브라우저에서 http://localhost:" + str(port) + "를 열어주세요")
        print("\n종료하려면: Ctrl+C 를 누르세요\n")

    # In deployment environments the platform will provide PORT and listen on 0.0.0.0
    app.run(debug=not is_production, port=port, host='0.0.0.0')
