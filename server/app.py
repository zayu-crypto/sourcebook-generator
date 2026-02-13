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

        prompt = """당신은 Observable Outcome 설계에 정통한 교육 설계 전문가입니다.
사용자가 작성한 Learning Outcome 초안을 분석하고, 더 좋은 Sourcebook 카드를 생성할 수 있도록 구체화해주세요.

## 사용자의 초안:
{0}

## Outcome 작성 5대 원칙

초안을 아래 5가지 원칙에 따라 개선하세요:

### 1. Observable (관찰 가능)
- "~를 이해한다", "~를 안다"처럼 머릿속에만 있는 표현을 피하세요.
- 관찰 가능한 행동 동사로 표현하세요:
  - "~의 차이를 비교하여 설명할 수 있다"
  - "~상황에서 ~를 적용한 대안을 제시할 수 있다"
  - "~의 사례를 분석하여 ~원리를 도출할 수 있다"

### 2. Single Focus (단일 초점)
- 하나의 Outcome 문장에 하나의 핵심 행동만 담으세요.
- "A를 하고, B도 하고, C도 한다"처럼 여러 행동을 나열하지 마세요.
- 만약 초안에 여러 행동이 섞여 있다면, 가장 핵심적인 것을 중심으로 통합하거나 2-3개의 독립 문장으로 분리하세요.
  - 나쁜 예: "UI를 설계하고, 사용자 테스트를 수행하고, 결과를 분석한다"
  - 좋은 예: "사용자 테스트 결과를 바탕으로 UI 개선점을 도출할 수 있다"

### 3. Context & Condition (맥락과 조건)
- "어떤 상황/조건에서" 수행하는지를 명시하세요.
- 맥락이 빠지면 범위가 무한히 넓어집니다.
  - 나쁜 예: "데이터를 분석할 수 있다"
  - 좋은 예: "주어진 사용자 행동 로그 데이터에서 이탈 패턴을 분석할 수 있다"

### 4. Scope Boundary (범위 한정)
- 초안에서 암시된 하위 주제, 핵심 키워드, 관찰 대상을 명시적으로 나열하세요.
- 너무 넓은 주제는 핵심 영역 2-3개로 좁히세요.
  - 나쁜 예: "인터랙션 디자인을 할 수 있다"
  - 좋은 예: "모바일 환경에서 제스처 기반 인터랙션과 음성 인터랙션의 장단점을 비교할 수 있다"

### 5. Cognitive Level (인지 수준 적정성)
- Bloom's Taxonomy를 참고하여 적절한 인지 수준의 동사를 사용하세요.
  - 기초: 나열하다, 식별하다, 설명하다
  - 중급: 비교하다, 분류하다, 적용하다
  - 고급: 분석하다, 평가하다, 설계하다
- 수업 수준에 맞지 않게 너무 높거나 낮은 동사를 쓰지 마세요.
- 초안의 맥락에서 적절한 인지 수준을 판단하세요.

## 규칙
- 초안의 원래 의도를 벗어나지 마세요. 관련 없는 새 주제를 추가하지 마세요.
- 초안이 이미 충분히 구체적이면 크게 바꾸지 마세요.
- 한국어로 작성하세요.
- Impact(장기적 영향)는 포함하지 마세요. Outcome만 다듬으세요.

## 응답 형식
반드시 아래 JSON 형식으로만 응답하세요:
{{"refined": "개선된 Outcome 텍스트 (2-4문장, 위 5대 원칙이 반영된 관찰 가능한 학습 성과)", "changes": "무엇을 보강했는지 한 줄 설명 (적용된 원칙 번호 포함, 예: [1,3,4] Observable + 맥락 + 범위 구체화)"}}""".format(draft)

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
