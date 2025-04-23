# 日本貿易統計データ自動取得パイプライン（HScode） 🌏
このプロジェクトは、日本の政府統計（[e-Stat API](https://www.e-stat.go.jp/stat-search/files?page=1&toukei=00350300&tstat=000001013143)）および税関の輸出統計品目表([HP](https://www.customs.go.jp/yusyutu/index.htm))
を活用し、HSコード別の貿易統計データを自動で収集・加工・保存するためのPythonスクリプト群です。]



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
│   ├── hscode_scrape.py              # HSコード取得ロジック
├── reference_master/                 # マスタデータ類
│   ├── area/nation.xlsx              # 国・地域マスタ
│   ├── counter/貿易統計_対応表.xlsx   # API情報対応表
│   ├── HS_master/                    # HSコードマスタとログ
│   └── e-stat/month.json             # 月別コード定義
├── Output/                           # 出力されたCSVファイル
├── .gitignore
├── README.md
├── MIT License
├── requirment
└── HSCode_scraping.ipynb             # ノートブック実行インターフェース
```

---
## 🛠 使用方法

### 1. HSコードマスタの生成（`HScode_scrape.py`）
```python
from library.hscode_scrape import (generate_customs_urls,fetch_and_concat_data,validate_and_log_hs_dataframe)
#年・月・部類番号の指定
year, month = 2010, 1    # 年・月（※範囲指定）
num_range = range(1, 98) # 部類番号（※範囲指定）
# HSコードのスクレイピング実行
urls = generate_customs_urls(year, month, num_range)
df = fetch_and_concat_data(urls)
log_df = validate_and_log_hs_dataframe(df, year) #バリデーションlogファイル作成
# CSVで保存
df.to_csv(f'./reference_master/HS_master/HSコードマスタ_{year:04d}.csv', encoding='utf-8', index=False)
```

### 2. 貿易統計データの取得（get_export_data_HSitem.py）
注意事項： APIキーが必要です
e-Stat API(https://www.e-stat.go.jp/api)の利用申請を行い、ご自身の`YOUR_API_KEY`を取得してください。
```python
from library.get_export_data_HSitem import TradeDataPipeline
import pandas as pd
#年・月・部類番号の指定
syurui = 'HS'  # HS品目別
year, month = 2024, '01' # 年・月（※単一指定）
api_key = "***************" #ご自身で取得してください

# 貿易統計マスタと対象データの抽出
trade_counter_df = pd.read_excel('./reference_master/counter/貿易統計_対応表.xlsx', dtype=str)
hs_counter_df = trade_counter_df[(trade_counter_df['分類'] == syurui) & (trade_counter_df['year'].astype(int) == year)].reset_index(drop=True)

# パイプライン実行
pipeline = TradeDataPipeline(hs_counter_df, trade_counter_df, nation_df, month, api_key)
pipeline.run()
```
---
## 💾 出力結果
出力フォルダ：./Output/HS_item/

出力ファイル名例：
2024_01_税関別_20250423.csv

カラム例：
```bash
['地域', '国', '年', '月', '税関', '部数', '部名', '類数', '類名', 'HSコード',
 '大項目', '中項目', '小項目', '細項目', '微細項目', '項目', '金額', '金額単位', '数量', '数量単位']
```
---
## ⚠️ 注意事項

- APIキーが必要です：e-Stat API（https://www.e-stat.go.jp/api）の利用申請を行い、`YOUR_API_KEY`を取得してください。
- reference_master/ 以下のCSVが必要です：分類、マスタ、国名変換などはローカルに格納されたCSVを前提としていますが、これらは私が作成しているものです。適宜ご変更ください。
- 年・月・分類によっては対応していない可能性があります（税関のHTML構造変化やAPI仕様による）。



---
## 📝 作成者
Hiroki Watari（渡利 広希）
データサイエンティスト / データエンジニア

このプロジェクトは個人・企業問わず自由にカスタマイズ可能です。
ForkやIssue歓迎します！


# Japan Trade Statistics Auto-Collection Pipeline 🌏
This project is a set of Python scripts for automatically collecting, processing, and saving Japan’s trade statistics data by HS code. It utilizes the **e-Stat API** (provided by the Japanese government) and **web scraping of Japan Customs pages**.



---

## 🔍 Key Features

- Automatically generates a hierarchical master of HS codes (via web scraping)
- Retrieves monthly trade statistics from the e-Stat API (by year/month/category)
- Merges and enriches data with HS classification hierarchy
- Outputs transaction data classified by country and customs office in CSV format
- Includes data validation features (missing values, structure gaps, digit checks)

---

## 📊 Project Structure

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
## 🛠 How to Use

### 1. Generate the HS Code Master (`HScode_scrape.py`)
```python
from library.HScode_scrape import generate_customs_urls, fetch_and_concat_data, validate_and_log_hs_dataframe

urls = generate_customs_urls(2024, 1, range(1, 98))  Specify year, month, and section range
df = fetch_and_concat_data(urls)
validate_and_log_hs_dataframe(df, 2024)
df.to_csv('./reference_master/HS_master/HSコードマスタ_2024.csv', index=False, encoding='utf-8')
```

### 2. Retrieve Trade Statistics Data (get_export_data_HSitem.py)
```python
from library.get_export_data_HSitem import TradeDataPipeline
import pandas as pd

# Load master files
hs_df = pd.read_csv('...')  # HS classification settings
stat_df = pd.read_csv('...')  # e-Stat statID mapping
nation_df = pd.read_csv('...')  # Country name mapping

pipeline = TradeDataPipeline(hs_df, stat_df, nation_df, '01', 'YOUR_API_KEY')
pipeline.run()
```
---
## 💾 Output
Output folder: ./Output/HS_item/

Example output filename: 2024_01_by_customs_20250423.csv

Sample columns:
```bash
['Region', 'Country', 'Year', 'Month', 'Customs', 'Section No', 'Section Name',
 'Category No', 'Category Name', 'HS Code', 'Main Item', 'Sub Item 1', 'Sub Item 2',
 'Sub Item 3', 'Sub Item 4', 'Item', 'Amount', 'Amount Unit', 'Quantity', 'Quantity Unit']

```
---
## ⚠️ Notes

API key is required
You must apply for and obtain an API key from the e-Stat API.

You need CSV files under reference_master/
These include classification definitions, statID mappings, and country mappings.
These are custom-created and may need to be adjusted for your use.

Some years or classifications may not be supported
This is due to changes in HTML structure of customs pages or limitations of the e-Stat API.



---
## 📝 Author
Hiroki Watari
Data Scientist / Data Engineer

This project is open for customization and free to use for both personal and business purposes.
Forks, Issues, and Pull Requests are very welcome!
