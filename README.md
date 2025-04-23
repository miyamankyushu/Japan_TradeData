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
└── execute_HSCode_pipeline.ipynb             # ノートブック実行インターフェース
```

---
## 🛠 使用方法

### 1. HSコードマスタの生成（`HScode_scrape.py`）
HS品目マスタのスクレイピング・データ加工を2010年～2025年まで行うコードです。取得結果はすでに`reference_master\HS_master`に格納済みです。
```python
from library.hscode_scrape import (
    generate_customs_urls,
    fetch_and_concat_data,
    validate_and_log_hs_dataframe
)

# Specify the year, month, and item category number range
year, month = 2010, 1               # Year and month (single month)
category_range = range(1, 98)       # HS category numbers (1–97; 77 skipped internally)

# Run HS code scraping
urls = generate_customs_urls(year, month, category_range)
df = fetch_and_concat_data(urls)

# Run validation and generate log
log_df = validate_and_log_hs_dataframe(df, year)

# Save as CSV
df.to_csv(f'./reference_master/HS_master/HSCode_Master_{year:04d}.csv', encoding='utf-8', index=False)

```

### 2. 貿易統計データの取得（get_export_data_HSitem.py）
税関別・HS品目別・国別に輸出量のデータを取得し、HSマスタと紐づけ等の処理を行い整備したデータを`Output`フォルダに格納します。

注意事項： APIキーが必要です
([e-Stat API](https://www.e-stat.go.jp/api))の利用申請を行い、ご自身の`YOUR_API_KEY`を取得してください。
```python
from library.get_export_data_HSitem import TradeDataPipeline
import pandas as pd

# Specify the type, year, and month
item_type = 'HS'  # HS (Harmonized System) item-based classification
year, month = 2024, '01'  # Year and month (single specification)
api_key = "***************"  # Replace with your own API key

# Load trade statistics master and extract target data
trade_counter_df = pd.read_excel('./reference_master/counter/trade_stat_mapping.xlsx', dtype=str)
hs_counter_df = trade_counter_df[
    (trade_counter_df['分類'] == item_type) & 
    (trade_counter_df['year'].astype(int) == year)
].reset_index(drop=True)

# Load country/region master
nation_df = pd.read_excel('./reference_master/area/nation.xlsx', dtype=str)

# Execute the trade data pipeline
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

- （再掲）APIキーが必要です([e-Stat API](https://www.e-stat.go.jp/api))の利用申請を行い、ご自身の`YOUR_API_KEY`を取得してください。
- reference_master/ 以下に国名、e-stats APIコード、分類などのマスタを格納していますが、これらは私が作成しているものです。適宜ご変更ください。
- 現状ほとんど確認されませんが、年・月・分類によっては対応していない可能性があります（税関のHTML構造変化やAPI仕様による）。



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
├── library/                          # Python modules
│   ├── get_export_data_HSitem.py     # TradeDataPipeline class
│   ├── hscode_scrape.py              # HS code scraping logic
├── reference_master/                 # Master data
│   ├── area/nation.xlsx              # Country/Region master
│   ├── counter/trade_stat_mapping.xlsx  # API info mapping table
│   ├── HS_master/                    # HS code master and logs
│   └── e-stat/month.json             # Monthly code definitions
├── Output/                           # Exported CSV files
├── .gitignore
├── README.md
├── MIT License
├── requirement                       # Required Python libraries
└── execute_HSCode_pipeline.ipynb     # execute
```

---
## 🛠 How to Use

### 1. Generate the HS Code Master (`HScode_scrape.py`)
```python
from library.hscode_scrape import (
    generate_customs_urls,
    fetch_and_concat_data,
    validate_and_log_hs_dataframe
)

# Specify the year, month, and item category number range
year, month = 2010, 1               # Year and month (single month)
category_range = range(1, 98)       # HS category numbers (1–97; 77 skipped internally)

# Run HS code scraping
urls = generate_customs_urls(year, month, category_range)
df = fetch_and_concat_data(urls)

# Run validation and generate log
log_df = validate_and_log_hs_dataframe(df, year)

# Save as CSV
df.to_csv(f'./reference_master/HS_master/HSCode_Master_{year:04d}.csv', encoding='utf-8', index=False)

```

### 2. Retrieve Trade Statistics Data (get_export_data_HSitem.py)
```python
from library.get_export_data_HSitem import TradeDataPipeline
import pandas as pd

# Specify the type, year, and month
item_type = 'HS'  # HS (Harmonized System) item-based classification
year, month = 2024, '01'  # Year and month (single specification)
api_key = "***************"  # Replace with your own API key

# Load trade statistics master and extract target data
trade_counter_df = pd.read_excel('./reference_master/counter/trade_stat_mapping.xlsx', dtype=str)
hs_counter_df = trade_counter_df[
    (trade_counter_df['分類'] == item_type) & 
    (trade_counter_df['year'].astype(int) == year)
].reset_index(drop=True)

# Load country/region master
nation_df = pd.read_excel('./reference_master/area/nation.xlsx', dtype=str)

# Execute the trade data pipeline
pipeline = TradeDataPipeline(hs_counter_df, trade_counter_df, nation_df, month, api_key)
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
