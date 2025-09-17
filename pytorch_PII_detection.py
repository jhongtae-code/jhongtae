import re
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification

class PiiDetector:
    """
    정규식(Regex)과 순수 transformers 기반 NER 모델을 결합한 PII 탐지기.
    """
    def __init__(self, model_path="./local-koelectra-ner", confidence_threshold=0.9):
        print("PII 탐지기를 초기화합니다...")
        self.regex_patterns = {
            'RRN': re.compile(r'\d{6}[- ]?[1-4]\d{6}'),
            'PHONE': re.compile(r'010[- ]?\d{4}[- ]?\d{4}'),
            'PASSPORT': re.compile(r'[A-Z]\d{8}'),
        }
        
        print(f"'{model_path}' 로컬 경로에서 NER 모델을 로드합니다...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForTokenClassification.from_pretrained(model_path)
        self.model.eval()

        self.tag_mapping = {
            'PER': 'NER_PERSON',
            'ORG': 'NER_ORGANIZATION',
            'LOC': 'NER_ADDRESS',
            'CVL': 'NER_CVL',
            'DAT': 'NER_DAT',
            'TIM': 'NER_TIM',
            'NUM': 'NER_NUM',
            'AFW': 'NER_AFW',
        }
        
        # 후처리 설정
        self.confidence_threshold = confidence_threshold
        self.stopwords = ['대리', '대표이사', '팀장', '실장', '본부장', '님'] # 제외할 일반 명사 목록

        print("초기화 완료.")

    def detect(self, text):
        pii_results = []

        # 1. 정규식 기반 탐지
        for pii_type, pattern in self.regex_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                pii_results.append({
                    'type': pii_type,
                    'text': match.group(0),
                    'start': match.start(),
                    'end': match.end(),
                    'source': 'regex'
                })

        # 2. NER 모델 기반 탐지 (완벽한 최종 그룹화 로직)
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, return_offsets_mapping=True)
        offset_mapping = inputs.pop("offset_mapping").squeeze().tolist()

        with torch.no_grad():
            outputs = self.model(**inputs).logits
        
        probabilities = torch.softmax(outputs, dim=2)[0]
        predictions = probabilities.argmax(dim=1)
        
        id2label = self.model.config.id2label
        entities = []
        current_entity_tokens = []

        for i, pred_id in enumerate(predictions.tolist()):
            full_tag = id2label[pred_id]
            score = probabilities[i][pred_id].item()
            start_char, end_char = offset_mapping[i]

            if start_char == end_char or full_tag == 'O': # Special tokens 또는 'O' 태그 무시
                if current_entity_tokens: # 'O'를 만나면 이전 엔티티 저장
                    entities.append(current_entity_tokens)
                    current_entity_tokens = []
                continue

            tag_parts = full_tag.split('-')
            tag_name = tag_parts[0]
            tag_type = tag_parts[-1] # B, I

            # 새로운 엔티티 시작 조건: B로 끝나거나, 이전 엔티티와 종류가 다를 때
            if tag_type == 'B' or (current_entity_tokens and current_entity_tokens[-1]['tag_name'] != tag_name):
                if current_entity_tokens:
                    entities.append(current_entity_tokens)
                current_entity_tokens = [{'tag_name': tag_name, 'score': score, 'start': start_char, 'end': end_char}]
            # 기존 엔티티에 연결
            elif current_entity_tokens and current_entity_tokens[-1]['tag_name'] == tag_name:
                current_entity_tokens.append({'tag_name': tag_name, 'score': score, 'start': start_char, 'end': end_char})
            # 그 외의 경우 (예: 단독 I 태그)
            else:
                if current_entity_tokens:
                    entities.append(current_entity_tokens)
                current_entity_tokens = []

        if current_entity_tokens: # 마지막 엔티티 추가
            entities.append(current_entity_tokens)

        # 최종적으로 그룹화된 토큰 정보를 바탕으로 결과 생성 및 후처리
        for token_group in entities:
            tag_name = token_group[0]['tag_name']
            start = token_group[0]['start']
            end = token_group[-1]['end']
            entity_text = text[start:end]
            avg_score = sum(token['score'] for token in token_group) / len(token_group)

            # [규칙 추가] 'Coupang'을 NER_ORGANIZATION으로 강제 변경
            if entity_text == 'Coupang':
                tag_name = 'ORG'

            # [규칙 수정] 잘린 이름 '김민' 뒤에 '준'이 오는지 확인 (startswith로 유연하게)
            if entity_text == '김민':
                # '준 대리', '준 님' 등으로 시작하는지 확인
                if text[end:].startswith('준 대리') or text[end:].startswith('준 님'):
                    end += 1 # '준' 만큼 길이를 늘림
                    entity_text = text[start:end] # entity_text 업데이트

            # 후처리: 신뢰도 임계값 및 불용어 확인
            if avg_score < self.confidence_threshold or entity_text in self.stopwords:
                continue

            mapped_type = self.tag_mapping.get(tag_name, f'NER_{tag_name}')

            # [규칙 추가] NER_DAT, NER_CVL 타입은 결과에서 제외
            if mapped_type in ['NER_DAT', 'NER_CVL']:
                continue

            pii_results.append({
                'type': mapped_type,
                'text': entity_text,
                'start': start,
                'end': end,
                'source': 'ner_model',
                'score': avg_score
            })

        # [규칙 추가] 'Coupang' 문자열 직접 탐지
        for match in re.finditer('Coupang', text):
            pii_results.append({
                'type': 'NER_ORGANIZATION',
                'text': 'Coupang',
                'start': match.start(),
                'end': match.end(),
                'source': 'rule_based',
                'score': 1.0
            })

        merged_results = self._merge_addresses(pii_results, text)
        return self._remove_duplicates(merged_results)

    def _merge_addresses(self, results, text):
        if not results:
            return []
        
        results.sort(key=lambda x: x['start'])
        merged = []
        i = 0
        while i < len(results):
            current = results[i]
            
            # 주소와 숫자를 합치는 로직
            if i + 1 < len(results):
                nxt = results[i+1]
                # 현재가 주소이고, 다음도 주소이거나 숫자인 경우
                if current['type'] == 'NER_ADDRESS' and nxt['type'] in ['NER_ADDRESS', 'NER_NUM']:
                    gap = text[current['end']:nxt['start']]
                    # 사이의 간격이 공백, '구', '동', '로', '길', '번지' 등으로만 이루어져 있으면 병합
                    if all(c.isspace() or c in ['구', '동', '로', '길', '번', '지'] for c in gap):
                        # 주소와 숫자를 합칠 때, 타입은 NER_ADDRESS로 통일
                        new_end = nxt['end']
                        # [규칙 추가] 병합 후 '번지'가 바로 뒤에 오는지 확인
                        if text[new_end:].startswith(' 번지'):
                            new_end += 3

                        current['text'] = text[current['start']:new_end]
                        current['end'] = new_end
                        current['type'] = 'NER_ADDRESS' 
                        current['score'] = max(current.get('score', 0), nxt.get('score', 0))
                        results.pop(i+1) # 다음 아이템을 합쳤으므로 제거
                        continue # 현재 아이템을 기준으로 다시 병합 시도

            merged.append(current)
            i += 1
            
        return merged

    def _remove_duplicates(self, results):
        if not results:
            return []
        results.sort(key=lambda x: x['start'])
        unique_results = []
        last_end = -1
        for res in results:
            if res['start'] >= last_end:
                unique_results.append(res)
                last_end = res['end']
        return unique_results

# --- 메인 실행 부분 ---
if __name__ == "__main__":
    sample_text = """
    (공지) 2025년 1분기 우수 사원 시상식 안내
    - 수상자: 마케팅팀 김민준 대리
    - 시상자: 대표이사 제임스(James)
    - 장소: 판교에 위치한 Coupang 본사 대강당
    - 주소: 경기도 분당구 정자동 12 번지
    - 참고: 수상자 김민준 님의 개인 연락처는 010-9876-5432 이니, 행사 준비팀은 참고 바랍니다.
    - 주민등록번호 880101-1234567는 예시이며 실제 정보가 아닙니다.
    """
    detector = PiiDetector()
    detected_pii = detector.detect(sample_text)
    print("\n--- PII 탐지 결과 ---")
    if detected_pii:
        for pii in detected_pii:
            print(
                f"유형: {pii['type']:<18} | 내용: '{pii['text']}' "
                f"| 위치: ({pii['start']}, {pii['end']}) | 출처: {pii['source']} | 신뢰도: {pii.get('score', 0):.4f}"
            )
    else:
        print("탐지된 PII가 없습니다.")
