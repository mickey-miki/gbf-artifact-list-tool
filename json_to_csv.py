import json
import csv

# 入力・出力ファイル名
json_file = 'gbf_artifacts_raw.json'
csv_file = 'gbf_artifacts_raw.csv'

# JSON読み込み
with open(json_file, 'r', encoding='utf-8') as f:
    artifacts = json.load(f)

def get_attribute_name(attribute_id):
    attribute_map = {
        '1': '火',
        '2': '水',
        '3': '土',
        '4': '風',
        '5': '光',
        '6': '闇'
    }
    return attribute_map.get(str(attribute_id), f'属性{attribute_id}')

def get_kind_name(kind_id):
    kind_map = {
        '1': '剣',
        '2': '短剣',
        '3': '槍',
        '4': '斧',
        '5': '杖',
        '6': '銃',
        '7': '格闘',
        '8': '弓',
        '9': '楽器',
        '10': '刀'
    }
    return kind_map.get(str(kind_id), f'種別{kind_id}')

# CSV書き込み
with open(csv_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    # ヘッダー
    header = [
        'id', 'artifact_id', 'name', 'level', 'rarity', 'attribute', 'kind',
        'is_locked', 'is_unnecessary',
        'skill1_name', 'skill1_quality', 'skill1_effect', 'skill1_level', 'skill1_is_max_quality',
        'skill2_name', 'skill2_quality', 'skill2_effect', 'skill2_level', 'skill2_is_max_quality',
        'skill3_name', 'skill3_quality', 'skill3_effect', 'skill3_level', 'skill3_is_max_quality',
        'skill4_name', 'skill4_quality', 'skill4_effect', 'skill4_level', 'skill4_is_max_quality'
    ]
    writer.writerow(header)
    for artifact in artifacts:
        def skill_info(key):
            info = artifact.get(key, {})
            return [
                info.get('name', ''),
                info.get('skill_quality', ''),
                info.get('effect_value', ''),
                info.get('level', ''),
                info.get('is_max_quality', '')
            ]
        row = [
            artifact.get('id'),
            artifact.get('artifact_id'),
            artifact.get('name'),
            artifact.get('level'),
            artifact.get('rarity'),
            get_attribute_name(artifact.get('attribute')),
            get_kind_name(artifact.get('kind')),
            artifact.get('is_locked', ''),
            artifact.get('is_unnecessary', ''),
            *skill_info('skill1_info'),
            *skill_info('skill2_info'),
            *skill_info('skill3_info'),
            *skill_info('skill4_info')
        ]
        writer.writerow(row)
print(f'✅ CSVファイルを出力しました: {csv_file}')
