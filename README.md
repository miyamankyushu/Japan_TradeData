# JAPAN_TRADEDATA 🌏

日本の貿易統計データを取得・検証・保存するためのデータパイプラインです。
e-Stat APIと税関サイトから取得したHSコードマスタを活用して、月次データを自動で収集・出力します。

---

## ✨ 特徴

- 税関データからHSコードマスタを自動スクレイピング
- e-Stat APIを利用した月次の貿易統計データ取得
- データの構造検証とログ出力
- クリーンなCSV形式で自動保存
- 対象年・月・分類を柔軟に指定可能
- `.json` マスタによる設定切り替え対応

---

## 📊 フォルダ構成

```
JAPAN_TRADEDATA/
├── library/                          # Pythonモジュール群
│   ├── get_export_data_HSitem.py     # TradeDataPipelineクラス
│   ├── HScode_scrape.py              # HSコード取得ロジック
├── reference_master/                # マスタデータ類
│   ├── area/nation.xlsx              # 国・地域マスタ
│   ├── counter/貿易統計_対応表.xlsx     # API情報対応表
│   ├── HS_master/                    # HSコードマスタとログ
│   └── cat02_master.json            # 月別コード定義
├── Output/                          # 出力されたCSVファイル
├── debug/                           # 一時的な検証出力
├── .gitignore
├── README.md
└── HSCode_scraping.ipynb            # ノートブック実行インターフェース
```

---

## ⚡ クイックスタート

### 1. 必要なライブラリのインストール
```bash
pip install pandas requests openpyxl
```

### 2. Jupyter Notebookで実行
`HSCode_scraping.ipynb` を開いて順に実行してください：

- HSコードマスタの取得
- バリデーションと保存
- TradeDataPipelineによるデータ取得処理

---

## 🌐 APIキーについて
[e-Stat API](https://www.e-stat.go.jp/)に登録し、以下のようにAPIキーを設定してください：
```python
api_key = "あなたのAPIキー"
```

---

## 📂 .gitignore の活用例
以下を`.gitignore`に追加することで、不要な大容量ファイルのGit追跡を防げます：
```
Output/*.csv
reference_master/HS_master/log/*.csv
debug/*.csv
```

---

## 📝 作成者
開発者：渡利 広希（Hiroki Watari）

このプロジェクトは個人・企業問わず自由にカスタマイズ可能です。
ForkやIssue歓迎します！

---

## 🚀 今後の展望（To Do）
- [ ] コマンドライン対応（CLI）
- [ ] データ可視化ダッシュボードの追加
- [ ] 年度一括バッチ処理の強化

