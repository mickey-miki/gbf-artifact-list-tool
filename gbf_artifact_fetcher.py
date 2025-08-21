#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class GBFArtifactFetcher:
    def __init__(self, uid, debug_port=9222):
        self.uid = uid  
        self.debug_port = debug_port
        self.driver = None
        self.session = requests.Session()
        self.base_url = "https://game.granbluefantasy.jp"


    def connect_to_chrome(self):
        try:
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.debug_port}")
            chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ 既存のChromeブラウザに接続しました")
            current_url = self.driver.current_url
            if "granbluefantasy.jp" not in current_url:
                print("⚠️ GBFのページではありません。GBFにログインしてください。")
                return False
            self.extract_cookies()
            print(f"✅ UIDを設定: {self.uid}")
            return True
        except Exception as e:
            print(f"❌ Chromeブラウザへの接続に失敗しました: {e}")
            return False

    def extract_cookies(self):
        try:
            cookies = self.driver.get_cookies()
            for cookie in cookies:
                if cookie['domain'] in ['.granbluefantasy.jp', 'game.granbluefantasy.jp']:
                    self.session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
            print(f"✅ {len([c for c in cookies if 'granbluefantasy.jp' in c['domain']])} 個のCookieを取得しました")
        except Exception as e:
            print(f"❌ Cookie取得エラー: {e}")

    def get_attribute_name(self, attribute_id):
        attribute_map = {'1': '火', '2': '水', '3': '土', '4': '風', '5': '光', '6': '闇'}
        return attribute_map.get(str(attribute_id), f'属性{attribute_id}')

    def save_artifacts_to_file(self, artifacts, filename="gbf_artifacts_raw.json"):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(artifacts, f, ensure_ascii=False, indent=2)
            print(f"✅ アーティファクト情報を {filename} に保存しました")
            return True
        except Exception as e:
            print(f"❌ ファイル保存エラー: {e}")
            return False

    def format_artifact_data(self, artifacts):
        formatted_artifacts = []
        for i, artifact in enumerate(artifacts, 1):
            formatted = {
                'index': i,
                'id': artifact.get('id'),
                'artifact_id': artifact.get('artifact_id'),
                'name': artifact.get('name', '不明'),
                'level': artifact.get('level', '不明'),
                'rarity': artifact.get('rarity', '不明'),
                'attribute': self.get_attribute_name(artifact.get('attribute')),
                'is_locked': artifact.get('is_locked', False),
                'skills': []
            }
            for skill_key in ['skill1_info', 'skill2_info', 'skill3_info', 'skill4_info']:
                skill_info = artifact.get(skill_key)
                if skill_info:
                    skill = {
                        'skill_id': skill_info.get('skill_id'),
                        'name': skill_info.get('name', '不明'),
                        'level': skill_info.get('level', 1),
                        'quality': skill_info.get('skill_quality', 1),
                        'is_max_quality': skill_info.get('is_max_quality', False),
                        'effect_value': skill_info.get('effect_value', '不明'),
                        'icon_image': skill_info.get('icon_image', '')
                    }
                    formatted['skills'].append(skill)
            equip_info = artifact.get('equip_npc_info', [])
            formatted['equipped_to'] = len(equip_info) > 0
            formatted['equip_details'] = equip_info
            formatted_artifacts.append(formatted)
        return formatted_artifacts

    def print_artifact_summary(self, artifacts):
        if not artifacts:
            print("❌ アーティファクトデータがありません")
            return
        print(f"\n📋 アーティファクト概要:")
        print("=" * 60)
        rarity_count = {}
        attribute_count = {}
        for artifact in artifacts:
            rarity = artifact.get('rarity', '不明')
            attribute = self.get_attribute_name(artifact.get('attribute'))
            rarity_count[rarity] = rarity_count.get(rarity, 0) + 1
            attribute_count[attribute] = attribute_count.get(attribute, 0) + 1
        print(f"📊 総数: {len(artifacts)} 個")
        print(f"🌟 レアリティ別: {dict(sorted(rarity_count.items()))}")
        print(f"⚡ 属性別: {dict(sorted(attribute_count.items()))}")
        locked_artifacts = [a for a in artifacts if a.get('is_locked')]
        if locked_artifacts:
            print(f"🔒 ロック済み: {len(locked_artifacts)} 個")

    def close(self):
        if self.driver:
            self.driver.quit()
            print("✅ ブラウザ接続を閉じました")

    def fetch_artifact_data_from_network(self, page=1):
        self.driver.execute_cdp_cmd("Network.enable", {})
        print(f"\n🔎 {page}ページ目のアーティファクト一覧を表示したらEnterキーを押してください。APIレスポンスを取得します。ページ遷移を終了したい場合は 'q' を入力してEnterを押してください。")
        user_input = input()
        if user_input.strip().lower() == 'q':
            return None
        logs = self.driver.get_log("performance")
        artifact_data = None
        # Network.responseReceived と Network.loadingFinished のペアを探す
        request_ids = set()
        for log in reversed(logs):
            message = log["message"]
            if "/rest/artifact/list/" in message and f"uid={self.uid}" in message:
                import json as _json
                msg_json = _json.loads(message)
                method = msg_json.get("message", {}).get("method", "")
                if method == "Network.responseReceived":
                    params = msg_json["message"]["params"]
                    request_id = params.get("requestId")
                    if request_id:
                        request_ids.add(request_id)
    # Network.loadingFinishedがあるrequestIdのみ取得
        for log in reversed(logs):
            message = log["message"]
            import json as _json
            msg_json = _json.loads(message)
            method = msg_json.get("message", {}).get("method", "")
            if method == "Network.loadingFinished":
                params = msg_json["message"]["params"]
                request_id = params.get("requestId")
                if request_id in request_ids:
                    try:
                        body = self.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
                        artifact_data = body.get("body")
                        break
                    except Exception as e:
                        print(f"⚠️ Network.getResponseBody取得失敗: {e}")
                        continue
        if artifact_data:
            print("✅ APIレスポンスを取得しました")
            try:
                return json.loads(artifact_data)
            except Exception:
                return artifact_data
        else:
            print("❌ APIレスポンスが取得できませんでした")
            print("（デバッグ用: performanceログの一部を表示）")
            print("※ページ表示後すぐにEnterキーを押してください。取得タイミングが重要です。")
            for log in logs[:10]:
                print(log["message"][:200])
            return None

    def process_artifact_page(self, page, artifacts_all):
        artifact_data = self.fetch_artifact_data_from_network(page=page)
        if not artifact_data or 'list' not in artifact_data or not artifact_data['list']:
            return False
        artifacts = artifact_data['list']
        artifacts_all.extend(artifacts)
        self.print_artifact_summary(artifacts)
        print(f"→ {len(artifacts)}件を追加。現在合計: {len(artifacts_all)}件")
        return True

    def save_all_artifacts(self, artifacts_all):
        print(f"\n💾 全ページ分のファイル保存中...（合計{len(artifacts_all)}件）")
        self.save_artifacts_to_file(artifacts_all, "gbf_artifacts_raw.json")
        print(f"\n📋 アーティファクトサンプル (最初の3個):")
        print("-" * 60)
        formatted = self.format_artifact_data(artifacts_all[:3])
        for artifact in formatted:
            print(f"🔸 {artifact['index']}. {artifact['name']} (Lv.{artifact['level']})")
            print(f"   属性: {artifact['attribute']} | レアリティ: {artifact['rarity']}")
            print(f"   スキル数: {len(artifact['skills'])} 個")
            for i, skill in enumerate(artifact['skills'], 1):
                print(f"     スキル{i}: {skill['name']} (品質:{skill['quality']}, 効果:{skill['effect_value']})")
            print()
        print(f"✅ 処理完了! 詳細は保存されたJSONファイルを確認してください。")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="GBF Artifact Fetcher")
    parser.add_argument('--uid', type=str, required=True, help='GBFのUID（必須）')
    args = parser.parse_args()

    print("🎮 グランブルーファンタジー アーティファクト取得ツール")
    print("=" * 60)
    fetcher = GBFArtifactFetcher(uid=args.uid)
    try:
        if not fetcher.connect_to_chrome():
            print("❌ Chromeブラウザへの接続に失敗しました。GBFのページにアクセスし、ログインしてください。")
            return
        artifacts_all = []
        page = 1
        while True:
            success = fetcher.process_artifact_page(page, artifacts_all)
            if not success:
                print("✅ すべてのページの取得が完了しました")
                break
            page += 1
        fetcher.save_all_artifacts(artifacts_all)
    except KeyboardInterrupt:
        print("\n⏹️ ユーザーによって中断されました")
    except Exception as e:
        print(f"❌ 予期しないエラーが発生しました: {e}")
    finally:
        fetcher.close()

if __name__ == "__main__":
    main()
