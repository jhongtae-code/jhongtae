import re
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification

class PiiDetector:
    """
    정규식(Regex)과 순수 transformers 기반 NER 모델을 결합한 PII 탐지기.
    """
    def __init__(self, model_path="./local-koelectra-ner"):
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
            'LOC': 'NER_ADDRESS'
        }
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

        # 2. NER 모델 기반 탐지 (모든 분기점 추적 디버깅)
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, return_offsets_mapping=True)
        offset_mapping = inputs.pop("offset_mapping").squeeze().tolist()

        with torch.no_grad():
            outputs = self.model(**inputs).logits
        
        predictions = torch.argmax(outputs, dim=2).squeeze().tolist()
        
        id2label = self.model.config.id2label
        entities = []
        current_entity_group = None

        print("\n--- [FINAL DEBUG] Branch-by-Branch Execution Trace ---")
        for i, pred_id in enumerate(predictions):
            full_tag = id2label[pred_id]
            start_char, end_char = offset_mapping[i]
            token_text = self.tokenizer.decode(inputs['input_ids'][0][i])

            print(f"\n[Step {i}] Token: '{token_text}', Tag: '{full_tag}'")

            if start_char == end_char:
                print("  - Branch: Skipping special token.")
                continue

            if full_tag == 'O':
                if current_entity_group:
                    print(f"  - Branch: 'O' tag. Appending previous entity: {current_entity_group}")
                    entities.append(current_entity_group)
                    current_entity_group = None
                else:
                    print("  - Branch: 'O' tag. No active entity.")
                continue

            # 이 블록에 진입했다는 것은 B- 또는 I- 태그라는 의미
            print("  - Branch: Entity tag detected.")
            tag_type = full_tag.split('-')[0]
            tag_name = full_tag.split('-')[1]

            # 새로운 개체 시작 조건
            if tag_type == 'B' or (current_entity_group and tag_name != current_entity_group['tag']):
                if current_entity_group:
                    print(f"  - Branch: New entity type. Appending previous: {current_entity_group}")
                    entities.append(current_entity_group)
                
                print(f"  - Branch: Starting new entity for '{tag_name}'")
                current_entity_group = {'tag': tag_name, 'start': start_char, 'end': end_char}
            
            # 기존 개체 확장 조건
            elif current_entity_group and tag_name == current_entity_group['tag']:
                print(f"  - Branch: Extending entity '{tag_name}'")
                current_entity_group['end'] = end_char
            
            else:
                print("  - Branch: UNHANDLED CASE! This should not happen.")

        print("----------------------------------------------------\n")
        
        if current_entity_group:
            entities.append(current_entity_group)

        # 최종적으로 그룹화된 위치 정보를 바탕으로 결과 생성
        for entity in entities:
            tag_name = entity['tag']
            mapped_type = self.tag_mapping.get(tag_name, f'NER_{tag_name}')
            pii_results.append({
                'type': mapped_type,
                'text': text[entity['start']:entity['end']],
                'start': entity['start'],
                'end': entity['end'],
                'source': 'ner_model'
            })

        return self._remove_duplicates(pii_results)

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
                f"| 위치: ({pii['start']}, {pii['end']}) | 출처: {pii['source']}"
            )
    else:
        print("탐지된 PII가 없습니다.")
