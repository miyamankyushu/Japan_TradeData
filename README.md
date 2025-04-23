# 日本貿易統計データ自動取得パイプライン 🌏

このプロジェクトは、日本の政府統計（e-Stat API）および税関ウェブサイトを活用し、HSコード別の貿易統計データを自動で収集・加工・保存するためのPythonスクリプト群です。



---

## 🔍 主な特徴

- **HSコード（品目分類）の階層マスタ自動生成**（スクレイピング）
- **e-Stat API からの月次貿易統計データ取得**（指定された月・年・分類で）
- **部類/類/項目レベルでのマスタ統合**
- **国別・税関別に分類された取引データをCSVで出力**
- **品質検査（欠損値、構造欠落、桁数チェック）付き**

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

