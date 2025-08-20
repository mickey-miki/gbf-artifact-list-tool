#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse, parse_qs
import re

class GBFArtifactFetcher:
    def __init__(self, debug_port=9222):
        """
        GBFのアーティファクト情報をREST APIから取得するクラス
        
        Args:
            debug_port (int): Chromeのデバッグポート（デフォルト: 9222）
        """
        self.debug_port = debug_port
        self.driver = None
        self.session = requests.Session()
        self.base_url = "https://game.granbluefantasy.jp"
        self.uid = None
        
    def connect_to_chrome(self):
        """既存のChromeブラウザに接続してCookie情報を取得"""
        try:
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.debug_port}")
            chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ 既存のChromeブラウザに接続しました")
            
            # GBFのページに移動（必要に応じて）
            current_url = self.driver.current_url
            if "granbluefantasy.jp" not in current_url:
                print("⚠️ GBFのページではありません。GBFにログインしてください。")
                return False
            
            # Cookie情報を取得
            self.extract_cookies()
            
            # UIDを取得
            self.extract_uid()
            
            return True
            
        except Exception as e:
            print(f"❌ Chromeブラウザへの接続に失敗しました: {e}")
            print("\n📝 解決方法:")
            print("1. Chromeを以下のコマンドで起動してください:")
            print(f'   chrome.exe --remote-debugging-port={self.debug_port}')
            print("2. GBFにログインしてください")
            return False
    
    def extract_cookies(self):
        """ChromeからCookie情報を抽出してrequestsセッションに設定"""
        try:
            cookies = self.driver.get_cookies()
            
            for cookie in cookies:
                if cookie['domain'] in ['.granbluefantasy.jp', 'game.granbluefantasy.jp']:
                    self.session.cookies.set(
                        cookie['name'], 
                        cookie['value'], 
                        domain=cookie['domain']
                    )
            
            print(f"✅ {len([c for c in cookies if 'granbluefantasy.jp' in c['domain']])} 個のCookieを取得しました")
            
        except Exception as e:
            print(f"❌ Cookie取得エラー: {e}")
    
    def extract_uid(self):
        """UIDを固定値で設定"""
        self.uid = "8050863"
        print(f"✅ 固定UIDを設定: {self.uid}")
    
    def get_artifact_list(self, page=1, manual_uid=None):
        """アーティファクト一覧をAPIから取得"""
        try:
            # UIDが取得できていない場合は手動入力を促す
            if not self.uid and not manual_uid:
                print("UIDが必要です。ブラウザのURLまたはネットワークタブから確認してください。")
                manual_uid = input("UIDを入力してください: ").strip()
            
            uid = manual_uid or self.uid
            if not uid:
                print("❌ UIDが設定されていません")
                return None
            
            # タイムスタンプを生成
            timestamp = int(time.time() * 1000)
            
            # APIエンドポイントURL
            api_url = f"{self.base_url}/rest/artifact/list/{page}"
            
            # パラメータ
            params = {
                '_': timestamp,
                't': timestamp,
                'uid': uid
            }
            
            # ヘッダー設定
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://game.granbluefantasy.jp/',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            print(f"🔄 アーティファクト一覧を取得中... (ページ {page})")
            print(f"📡 API URL: {api_url}")
            print(f"🆔 UID: {uid}")
            
            # APIリクエスト実行
            response = self.session.get(api_url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ アーティファクト一覧を取得しました")
                print(f"📊 総数: {data.get('count', 0)} 個")
                print(f"📄 現在のページ: {data.get('current', 1)}")
                print(f"📋 このページのアイテム数: {len(data.get('list', []))} 個")
                
                return data
                
            else:
                print(f"❌ APIリクエストが失敗しました: {response.status_code}")
                print(f"レスポンス: {response.text[:500]}")
                return None
                
        except Exception as e:
            print(f"❌ アーティファクト取得エラー: {e}")
            return None
    
    def get_all_artifacts(self, manual_uid=None):
        """1ページのみのアーティファクトを取得（試験運用）"""
        data = self.get_artifact_list(1, manual_uid)
        if data and data.get('list'):
            print(f"📄 ページ 1: {len(data['list'])} 個のアーティファクトを取得")
            print(f"✅ 全 {len(data['list'])} 個のアーティファクトを取得しました")
            return data['list']
        else:
            print("❌ アーティファクトデータを取得できませんでした")
            return []
    
    def decode_unicode_names(self, artifacts):
        """Unicode文字列をデコード"""
        for artifact in artifacts:
            # アーティファクト名をデコード
            if 'name' in artifact:
                artifact['name_decoded'] = artifact['name']
            
            # スキル名をデコード
            for skill_key in ['skill1_info', 'skill2_info', 'skill3_info', 'skill4_info']:
                if skill_key in artifact and artifact[skill_key]:
                    skill_info = artifact[skill_key]
                    if 'name' in skill_info:
                        skill_info['name_decoded'] = skill_info['name']
        
        return artifacts
    
    def format_artifact_data(self, artifacts):
        """アーティファクトデータを見やすい形式に整形"""
        formatted_artifacts = []
        
        for i, artifact in enumerate(artifacts, 1):
            formatted = {
                'index': i,
                'id': artifact.get('id'),
                'artifact_id': artifact.get('artifact_id'),
                'name': artifact.get('name', '不明'),
                'level': artifact.get('level', '不明'),
                'max_level': artifact.get('max_level', '不明'),
                'rarity': artifact.get('rarity', '不明'),
                'attribute': self.get_attribute_name(artifact.get('attribute')),
                'is_locked': artifact.get('is_locked', False),
                'exp_info': {
                    'next_exp': artifact.get('next_exp', 0),
                    'remain_next_exp': artifact.get('remain_next_exp', 0),
                    'exp_width': artifact.get('exp_width', 0)
                },
                'skills': []
            }
            
            # スキル情報を整形
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
            
            # 装備情報
            equip_info = artifact.get('equip_npc_info', [])
            formatted['equipped_to'] = len(equip_info) > 0
            formatted['equip_details'] = equip_info
            
            formatted_artifacts.append(formatted)
        
        return formatted_artifacts
    
    def get_attribute_name(self, attribute_id):
        """属性IDを属性名に変換"""
        attribute_map = {
            '1': '火',
            '2': '水', 
            '3': '土',
            '4': '風',
            '5': '光',
            '6': '闇'
        }
        return attribute_map.get(str(attribute_id), f'属性{attribute_id}')
    
    def save_artifacts_to_file(self, artifacts, filename="gbf_artifacts.json"):
        """アーティファクト情報をJSONファイルに保存"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(artifacts, f, ensure_ascii=False, indent=2)
            print(f"✅ アーティファクト情報を {filename} に保存しました")
            return True
        except Exception as e:
            print(f"❌ ファイル保存エラー: {e}")
            return False
    
    def save_formatted_artifacts(self, artifacts, filename="gbf_artifacts_formatted.json"):
        """整形されたアーティファクト情報を保存"""
        formatted = self.format_artifact_data(artifacts)
        return self.save_artifacts_to_file(formatted, filename)
    
    def print_artifact_summary(self, artifacts):
        """アーティファクトの概要を表示"""
        if not artifacts:
            print("❌ アーティファクトデータがありません")
            return
        
        print(f"\n📋 アーティファクト概要:")
        print("=" * 60)
        
        # レアリティ別集計
        rarity_count = {}
        attribute_count = {}
        level_count = {}
        
        for artifact in artifacts:
            rarity = artifact.get('rarity', '不明')
            attribute = self.get_attribute_name(artifact.get('attribute'))
            level = artifact.get('level', '不明')
            
            rarity_count[rarity] = rarity_count.get(rarity, 0) + 1
            attribute_count[attribute] = attribute_count.get(attribute, 0) + 1
            level_count[level] = level_count.get(level, 0) + 1
        
        print(f"📊 総数: {len(artifacts)} 個")
        print(f"🌟 レアリティ別: {dict(sorted(rarity_count.items()))}")
        print(f"⚡ 属性別: {dict(sorted(attribute_count.items()))}")
        print(f"📈 レベル別: {dict(sorted(level_count.items()))}")
        
        # 最高レベルのアーティファクト
        max_level_artifacts = [a for a in artifacts if a.get('level') == '5']
        if max_level_artifacts:
            print(f"🔥 最大レベル(5)のアーティファクト: {len(max_level_artifacts)} 個")
        
        # ロック済みアーティファクト
        locked_artifacts = [a for a in artifacts if a.get('is_locked')]
        if locked_artifacts:
            print(f"🔒 ロック済み: {len(locked_artifacts)} 個")
    
    def close(self):
        """ブラウザ接続を閉じる"""
        if self.driver:
            self.driver.quit()
            print("✅ ブラウザ接続を閉じました")

    def fetch_artifact_data_from_network(self, page=1):
        """Selenium+CDPでAPIレスポンスを取得（毎回Enterで取得）"""
        self.driver.execute_cdp_cmd("Network.enable", {})
        print(f"\n🔎 {page}ページ目のアーティファクト一覧を表示したらEnterキーを押してください。APIレスポンスを取得します。")
        input()
        logs = self.driver.get_log("performance")
        artifact_data = None
        api_path = f"/rest/artifact/list/{page}"
        for log in logs:
            message = log["message"]
            if "/rest/artifact/list/" in message and f"uid=8050863" in message:
                import json as _json
                msg_json = _json.loads(message)
                method = msg_json.get("message", {}).get("method", "")
                if method == "Network.responseReceived":
                    params = msg_json["message"]["params"]
                    request_id = params.get("requestId")
                    if request_id:
                        body = self.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
                        artifact_data = body.get("body")
                        break
        if artifact_data:
            print("✅ APIレスポンスを取得しました")
            try:
                return json.loads(artifact_data)
            except Exception:
                return artifact_data
        else:
            print("❌ APIレスポンスが取得できませんでした")
            print("（デバッグ用: performanceログの一部を表示）")
            for log in logs[:10]:
                print(log["message"][:200])
            return None

def main():
    """メイン実行関数"""
    print("🎮 グランブルーファンタジー アーティファクト取得ツール (API版)")
    print("=" * 60)
    
    fetcher = GBFArtifactFetcher()
    try:
        if not fetcher.connect_to_chrome():
            print("❌ Chromeブラウザへの接続に失敗しました。GBFのページにアクセスし、ログインしてください。")
            return
        artifacts_all = []
        page = 1
        print(f"\n{page}ページ目のアーティファクト一覧を表示したらEnterキーを押してください。ページ遷移を終了したい場合は 'q' を入力してEnterを押してください。")
        while True:
            user_input = input()
            if user_input.strip().lower() == 'q':
                print("⏹️ ユーザー操作によりページ取得を終了します")
                break
            artifact_data = fetcher.fetch_artifact_data_from_network(page=page)
            if not artifact_data or 'list' not in artifact_data or not artifact_data['list']:
                print("✅ すべてのページの取得が完了しました")
                break
            artifacts = artifact_data['list']
            artifacts = fetcher.decode_unicode_names(artifacts)
            artifacts_all.extend(artifacts)
            fetcher.print_artifact_summary(artifacts)
            print(f"→ {len(artifacts)}件を追加。現在合計: {len(artifacts_all)}件")
            page += 1
        print(f"\n💾 全ページ分のファイル保存中...（合計{len(artifacts_all)}件）")
        fetcher.save_artifacts_to_file(artifacts_all, "gbf_artifacts_raw.json")
        fetcher.save_formatted_artifacts(artifacts_all, "gbf_artifacts_formatted.json")
        print(f"\n📋 アーティファクトサンプル (最初の3個):")
        print("-" * 60)
        formatted = fetcher.format_artifact_data(artifacts_all[:3])
        for artifact in formatted:
            print(f"🔸 {artifact['index']}. {artifact['name']} (Lv.{artifact['level']})")
            print(f"   属性: {artifact['attribute']} | レアリティ: {artifact['rarity']}")
            print(f"   スキル数: {len(artifact['skills'])} 個")
            for i, skill in enumerate(artifact['skills'], 1):
                print(f"     スキル{i}: {skill['name']} (品質:{skill['quality']}, 効果:{skill['effect_value']})")
            print()
        print(f"✅ 処理完了! 詳細は保存されたJSONファイルを確認してください。")
    except KeyboardInterrupt:
        print("\n⏹️ ユーザーによって中断されました")
    except Exception as e:
        print(f"❌ 予期しないエラーが発生しました: {e}")
    finally:
        fetcher.close()

if __name__ == "__main__":
    main()
