# 日本貿易統計データ自動取得パイプライン 🌏

このプロジェクトは、日本の政府統計（e-Stat API）および税関ウェブサイトを活用し、HSコード別の貿易統計データを自動で収集・加工・保存するためのPythonスクリプト群です。



---

## 🔍 主な特徴

- HSコード（品目分類）の階層マスタ自動生成（スクレイピング）
- e-Stat API からの月次貿易統計データ取得（指定された月・年・分類で）
- 部類/類/項目レベルでのマスタ統合
- 国別・税関別に分類された取引データをCSVで出力
- 品質検査（欠損値、構造欠落、桁数チェック）付き

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

## 🛠 使用方法

### 1. HSコードマスタの生成（`HScode_scrape.py`）
```python
from library.HScode_scrape import generate_customs_urls, fetch_and_concat_data, validate_and_log_hs_dataframe

urls = generate_customs_urls(2024, 1, range(1, 98))  # 年・月・部類番号の範囲
df = fetch_and_concat_data(urls)
validate_and_log_hs_dataframe(df, 2024)
df.to_csv('./reference_master/HS_master/HSコードマスタ_2024.csv', index=False, encoding='utf-8')
```

### 2. 貿易統計データの取得（get_export_data_HSitem.py）
```python
from library.get_export_data_HSitem import TradeDataPipeline
import pandas as pd

# 各種CSVデータを読み込み
hs_df = pd.read_csv('...')  # HS分類指定データ
stat_df = pd.read_csv('...')  # e-StatのID対応データ
nation_df = pd.read_csv('...')  # 国名変換マスタ

pipeline = TradeDataPipeline(hs_df, stat_df, nation_df, '01', 'YOUR_API_KEY')
pipeline.run()
```

## 💾 出力結果
出力フォルダ：./Output/HS_item/

出力ファイル名例：
2024_01_税関別_20250423.csv

カラム例：
```bash
['地域', '国', '年', '月', '税関', '部数', '部名', '類数', '類名', 'HSコード',
 '大項目', '中項目', '小項目', '細項目', '微細項目', '項目', '金額', '金額単位', '数量', '数量単位']
```

## ⚠️ 注意事項

- HAPIキーが必要です：e-Stat API（https://www.e-stat.go.jp/api）の利用申請を行い、`YOUR_API_KEY`を取得してください。
- reference_master/ 以下のCSVが必要です：分類、マスタ、国名変換などはローカルに格納されたCSVを前提としていますが、これらは私が作成しているものです。適宜ご変更ください。
- 年・月・分類によっては対応していない可能性があります（税関のHTML構造変化やAPI仕様による）。


## 📂 .gitignore の活用例
以下を`.gitignore`に追加することで、不要な大容量ファイルのGit追跡を防げます：
```
Output/*.csv
reference_master/HS_master/log/*.csv
debug/*.csv
```

---

## 📝 作成者
Hiroki Watari（渡利 広希）
データサイエンティスト / データエンジニア

このプロジェクトは個人・企業問わず自由にカスタマイズ可能です。
ForkやIssue歓迎します！

