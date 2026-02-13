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

Learning Outcome:
{0}

이를 기반으로 Sourcebook 카드 10개를 생성하세요.

**STRATEGY: Learning Outcome에 맞게 구체적 예제를 선택하되, Wikimedia에 풍부한 자료가 있는 것들만 선택하세요.**

🎯 주제별 추천 자료 (Wikimedia 풍부함):

【그래픽 디자인 & 시각 문화】
- 유명 그래픽 디자이너: Josef Müller-Brockmann (스위스 스타일), Saul Bass (영화 포스터), Toulouse-Lautrec (포스터 미술), Shepard Fairey (포스터 아트)
- 역사적 포스터 무브먼트: Art Deco 포스터, Bauhaus, Swiss Design, Russian Constructivism
- 인쇄술과 타이포그래피 역사: Gutenberg printing, 초기 신문 디자인, 책 표지 진화
- 시각적 아이덴티티: 유명 로고 역사 (IBM logo 1956, Mercedes logo, Apple logo 1977)

【조형 요소 & 시각 원리】
- 점 expressionism: Pointillism (조르주 쇠라), Halftone printing 역사
- 선의 역할: Art Nouveau 선의 흐름, Contour line drawing, Sketch 예제
- 면과 형태: Cubism (피카소, 브라크), 기하학적 추상미술
- 색채 이론: Bauhaus 색채론, 인상주의 색채 사용
- 공간과 구성: 건축 설계도, 인쇄 레이아웃, 신문 편집

【디자인 역사 인물】
- Alexander Hamilton (초기 미국 신문), Benjamin Franklin (인쇄술 개혁)
- Oswald Berthold (타이포그래피), Jan Tschichold (모던 타이포그래피)
- László Moholy-Nagy (Bauhaus, 시각 실험)

【역사적 시각 문화】
- 고대 동전의 초상 디자인 (조형 표현의 역사)
- Medieval manuscript illumination (색과 선의 사용)
- 18-19세기 판화 기술 (woodcut, engraving)
- 영화 포스터 역사 (1920-1960s)
- 신문 레이아웃 진화

【기술과 조형】
- 카메라의 역사 (뷰파인더, 프레이밍)
- 인쇄 기술 발전 (Gutenberg → Linotype → Offset printing)
- 컴퓨터 그래픽 역사 (초기 벡터 그래픽 소프트웨어)

각 카드는 다음 3가지를 포함해야 합니다:

1. 핵심 자료 (Core Material) - Learning Outcome과 관련된 구체적 예제
   - imageSearchKeyword: 위 목록에서 선택한 구체적 역사 주제 (예: "Bauhaus color theory", "Josef Müller-Brockmann Swiss Design", "Saul Bass movie poster", "Toulouse-Lautrec Art Nouveau", "Pointillism Georges Seurat", "Gutenberg printing press")
   - source: Wikimedia Commons
   - caption: 한 줄 설명

2. 핵심질문 (Essential Question)
   - Learning Outcome의 조형/시각 개념과 구체적 예제를 연결
   - 학생이 실제로 "보게 되는" 조형 요소에 초점
   - 추상이 아닌 시각적/물리적 관찰 기반
   
   예시 좋은질문:
   - Toulouse-Lautrec의 포스터에서 "선"이 인물의 특성을 어떻게 표현하는가?
   - Bauhaus 색채 이론이 오늘날의 UI 디자인에 구체적으로 어떻게 적용되는가?
   - 신문 레이아웃에서 "공간(여백)"이 정보의 중요도를 어떻게 표현하는가?
   - Pointillism의 작은 점들이 멀리서 보면 다른 색으로 보이는 것은 왜인가?

3. 탐색큐: 3개의 구체적 검색어

응답은 JSON 배열 형식:
[{{"id": 1, "title": "제목", "coreImage": {{"imageSearchKeyword": "검색어", "source": "Wikimedia Commons", "caption": "설명"}}, "essentialQuestion": "질문", "searchCues": ["큐1", "큐2", "큐3"]}}]

Learning Outcome의 의도를 정확히 반영한 10개 카드를 생성하세요.""".format(outcome)

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
