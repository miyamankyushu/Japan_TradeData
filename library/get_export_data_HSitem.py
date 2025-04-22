import os
import re
import pandas as pd
import requests
from datetime import datetime
from io import StringIO
import json



with open('reference_master/e-stat/month.json', 'r', encoding='utf-8') as f:
    cat02_by_month = json.load(f)

class TradeDataPipeline:
    def __init__(self, hs_counter_df, trade_counter_df, nation_df, month, api_key):
        self.hs_counter_df = hs_counter_df
        self.trade_counter_df = trade_counter_df
        self.nation_df = nation_df
        self.month = month
        self.api_key = api_key
        self.cat02_by_month = cat02_by_month  # ← ここで渡す
        self.start_time = datetime.now()
        print("✅ 初期化完了: 取得開始")

    def get_cat02_by_month(self, month):
        return self.cat02_by_month.get(month.zfill(2))

    def get_data(self, statdataID, startPosition, month, year):
        url = 'http://api.e-stat.go.jp/rest/3.0/app/getSimpleStatsData'
        cat02 = self.get_cat02_by_month(month)
        params = {
            'appId': self.api_key,
            'lang': 'J',
            'statsDataId': statdataID,
            'metaGetFlg': 'N',
            'cntGetFlg': 'N',
            'explanationGetFlg': 'N',
            'annotationGetFlg': 'N',
            'sectionHeaderFlg': '1',
            'replaceSpChars': '0',
            'limit': '100000',
            'startPosition': str(startPosition),
            'cdCat02': cat02,
            'cdTime': str(year) + '000000'
        }
        response = requests.get(url, params=params).text
        i_NEXT_KEY = response.find('"NEXT_KEY"')
        if i_NEXT_KEY >= 0:
            next_startPosition = response[response.find('"NEXT_KEY"'):].split('\n')[0].split(',')[-1][1:-1]
        else:
            next_startPosition = 1
        df = pd.read_csv(StringIO(response[response.find('"VALUE"') + len('"VALUE"'):]), dtype=str)
        return df, next_startPosition

    def fetch_all_data(self, statdataID, year):
        all_dfs = []
        startPosition = 1
        df, next_startPosition = self.get_data(statdataID, startPosition, self.month, year)
        if df.columns[0] == 'RESULT':
            print(' - - 結果なし')
            return pd.DataFrame()
        all_dfs.append(df)
        while int(next_startPosition) > 1:
            df, next_startPosition = self.get_data(statdataID, next_startPosition, self.month, year)
            all_dfs.append(df)
        return pd.concat(all_dfs, ignore_index=True)

    def process_dataframe(self, df):
        df['国'] = df['国'].str.split('_').str[1]
        df['数量・金額'] = df['統計品目表の数量・金額'].str.split('_').str[1]
        df['月'] = df['統計品目表の数量・金額'].str.split('_').str[0]

        q_cols = ['時間軸(年次)', 'cat01_code', '月', '税関', '国', '数量・金額', 'value']
        m_cols = ['時間軸(年次)', 'cat01_code', '月', '税関', '国', 'unit', '数量・金額', 'value']

        df_q = df[df['数量・金額'] == '数量2'][q_cols].rename(columns={'value': '数量'})
        df_m = df[df['数量・金額'] == '金額'][m_cols].rename(columns={'value': '金額'})

        df_final = pd.merge(
            df_m, df_q,
            on=['cat01_code', '月', '税関', '国', '時間軸(年次)'],
            how='inner'
        )
        return df_final

    def merge_with_master(self, df, year):
        hs_path = f'reference_master/HS_master/HSコードマスタ_{year}.csv'
        hs_master = pd.read_csv(hs_path, dtype=str)
        df = df[df['cat01_code'].astype(str).str.len() == 9]
        df = pd.merge(df, hs_master, left_on='cat01_code', right_on='HSコード', how='left')
        df = pd.merge(df, self.nation_df, on='国', how='left')

        df = df[[
            '地域', '国', '時間軸(年次)', '月', '税関', '部数', '部名',
            '類数', '類名', 'cat01_code', '大項目', '中項目', '小項目', '細項目', '微細項目', '項目',
            '金額', 'unit', '数量', '単位2'
        ]]
        return df.rename(columns={
            '時間軸(年次)': '年',
            '単位2': '数量単位',
            'unit': '金額単位',
            'cat01_code': 'HSコード',
        })

    def save_csv(self, df, year):
        date = datetime.now().strftime('%Y%m%d')
        path = f'./Output/HS_item/{year}_{self.month}_税関別_{date}.csv'
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_csv(path, index=False, encoding='utf-8')
        print(f'📁 保存完了: {path}')

    def run(self):
        for i in range(len(self.hs_counter_df)):
            print(f"▶️ 分類：{self.hs_counter_df['分類'][i]} {self.hs_counter_df['year'][i]}年 {self.month}月")
            statdataID = self.trade_counter_df['statdataID'][i]
            year = self.trade_counter_df['year'][i]

            raw_df = self.fetch_all_data(statdataID, year)
            if raw_df.empty:
                continue
            processed_df = self.process_dataframe(raw_df)
            merged_df = self.merge_with_master(processed_df, year)
            self.save_csv(merged_df, year)

        elapsed = datetime.now() - self.start_time
        minutes, seconds = divmod(int(elapsed.total_seconds()), 60)
        print(f"⏱️ 実行完了: {minutes}分 {seconds}秒")
