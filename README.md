# GBF Artifact List Tool

## 概要
グランブルーファンタジー（GBF）のアーティファクト情報をChromeのデバッグセッション経由で取得し、JSON/CSV形式で保存するツールです。

## 前提
本ツールはWindows環境での動作を想定しています。  
GBFの画面操作（ログイン・ページ遷移など）は手動で行う必要があります。

## 主な機能
- Chromeのデバッグセッションに接続し、GBFのアーティファクトAPIレスポンスを取得
- 全ページ分のアーティファクトデータを `gbf_artifacts_raw.json` に保存
- CSV変換（`json_to_csv.py`）

## セットアップ
### 1. Pythonのインストール
公式サイト（https://www.python.org/downloads/）からPython 3.xをダウンロード・インストールしてください。
インストール時に「Add Python to PATH」にチェックを入れてください。

### 2. pipのインストール・確認
コマンドプロンプトまたはPowerShellで以下を実行し、pipが使えるか確認します。
```
python --version
pip --version
```
pipが見つからない場合は、以下でインストールできます。
```
python -m ensurepip --upgrade
```

### 3. 必要パッケージのインストール
コマンドラインで以下を実行してください。
```
pip install selenium requests
```

## 使い方
### 1. Chromeの起動
コマンドラインで以下のようにChromeを起動してください。  
インストール先が異なる場合は適宜変更してください。
```
cd "C:\Program Files (x86)\Google\Chrome\Application"
.\chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrome_debug"
```
GBFにログインし、アーティファクト一覧画面を表示してください。

### 2. アーティファクトデータの取得
コマンドプロンプトやPowerShellで本ツールのフォルダ（例：`c:\develop\python\gbf_artifact_list`）に移動してから、以下を実行してください。
```
python gbf_artifact_fetcher.py --uid <あなたのGBF UID>
```
- UIDは必須です。自分のGBF UIDを指定してください。
- 1ページ目表示後、EnterキーでAPI取得
- 2ページ目以降はページ遷移後にEnterキーでAPI取得
- すべてのページ取得後、`gbf_artifacts_raw.json` に保存されます
- 途中で終了したい場合は「q」を入力してEnterキーを押してください

### 3. JSON→CSV変換
```
python json_to_csv.py
```
- `gbf_artifacts_raw.json` から `gbf_artifacts_raw.csv` を生成
- csvはgoogleスプレッドシートやExcelにインポート可能です。

## ファイル構成
- gbf_artifact_fetcher.py : データ取得メインスクリプト
- json_to_csv.py : JSON→CSV変換スクリプト
- gbf_artifacts_raw.json : 取得した生データ
- gbf_artifacts_raw.csv : CSV変換結果

## 注意事項
- GBFの仕様変更等で動作しなくなる場合があります

## ライセンス
MIT License

## 免責事項・利用規約について
本ツールはグランブルーファンタジー（GBF）の非公式ツールです。GBFの利用規約やスクレイピング規約等に違反しない範囲でご利用ください。  
本ツールの利用によって生じたいかなる損害・トラブルについても、作者は一切の責任を負いません。利用は自己責任でお願いします。
