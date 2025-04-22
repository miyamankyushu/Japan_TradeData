import requests
import os
import re
import pandas as pd
from datetime import datetime
from io import StringIO
api_key = "cd892ddafd38c70af31204e5e2927a3573fa942e"


def get_data(statdataID, startPosition, cat02,year):
    url = 'http://api.e-stat.go.jp/rest/3.0/app/getSimpleStatsData'
    params = {
        'appId': api_key,
        'lang': 'J',
        'statsDataId': statdataID,
        'metaGetFlg': 'N',
        'cntGetFlg': 'N',
        'explanationGetFlg': 'N',
        'annotationGetFlg': 'N',
        'sectionHeaderFlg': '1',
        'replaceSpChars': '0',
        'limit':'100000',
        'startPosition': str(startPosition),
        'cdCat02': cat02,
        #'cdArea':'50112',
        'cdTime':str(year)+'000000'
    }
    response = requests.get(url, params=params).text
    i_NEXT_KEY = response.find('"NEXT_KEY"')
    if i_NEXT_KEY >= 0:
        next_startPosition = response[response.find('"NEXT_KEY"'):].split('\n')[0].split(',')[-1][1:-1]  # NEXT_KEYの値部分
    else:
        # 10万件以下の場合はNEXT_KEYタグは存在しない
        next_startPosition = 1  # startPosition=1と同値
    df = pd.read_csv(StringIO(response[response.find('"VALUE"') + len('"VALUE"'):]))  # 実際の貿易統計のデータ部分
    return df, next_startPosition


def run_trade_data_pipeline(hs_counter_df, trade_counter_df, nation_df,m_q_list):
    # セルの実行開始時刻を記録
    start_time = datetime.now()
    print('取得開始')

    for l in range(len(hs_counter_df)):
        all_dfs = []
        statdataID = trade_counter_df['statdataID'][l]
        year = trade_counter_df['year'][l]
        cat02_list = m_q_list

        print('分類：', hs_counter_df['分類'][l], ', 年度：', year, ', StatdataID：', statdataID)

        syutoku_data = 0
        startPosition = 1
        df, next_startPosition = get_data(statdataID, startPosition, cat02_list, year)

        if df.columns[0] == 'RESULT':
            syutoku_data += len(df)
            print(' - - 取得完了:', syutoku_data, '行')
            continue

        all_dfs.append(df)

        while int(next_startPosition) > 1:
            syutoku_data += len(df)
            print(' - - 取得完了:', syutoku_data, '行')
            df, next_startPosition = get_data(statdataID, next_startPosition, cat02_list, year)
            all_dfs.append(df)

        syutoku_data += len(df)
        print(' - - 取得完了:', syutoku_data, '行')

        final_df = pd.concat(all_dfs, ignore_index=True)
        del all_dfs

        final_df['国'] = final_df['国'].str.split('_').str[1]
        final_df['数量・金額'] = final_df['統計品目表の数量・金額'].str.split('_').str[1]
        final_df['統計品目表の数量・金額'] = final_df['統計品目表の数量・金額'].str.split('_').str[0]

        selected_columns_q = ['時間軸(年次)', 'cat01_code', '統計品目表の数量・金額', '税関', '国', '数量・金額', 'value']
        final_df_q = final_df[final_df['数量・金額'] == '数量2'][selected_columns_q].copy()
        final_df_q.rename(columns={'value': '数量'}, inplace=True)

        selected_columns_m = ['時間軸(年次)', 'cat01_code', '統計品目表の数量・金額', '税関', '国', 'unit', '数量・金額', 'value']
        final_df_m = final_df[final_df['数量・金額'] == '金額'][selected_columns_m].copy()
        final_df_m.rename(columns={'value': '金額'}, inplace=True)

        print(len(final_df_m), len(final_df_q))
        final_df = pd.merge(final_df_m, final_df_q, on=['cat01_code', '統計品目表の数量・金額', '税関', '国', '時間軸(年次)'], how='inner')
        print(len(final_df), len(final_df_q))
        del final_df_q, final_df_m

        HS_master = pd.read_csv(f'/content/drive/MyDrive/政府統計/貿易統計/03_import/HScode/HSコードマスタ_{year}.csv')
        merged_df = pd.merge(final_df, HS_master, left_on='cat01_code', right_on='HSコード', how='left')
        merged_df = pd.merge(merged_df, nation_df, on='国', how='left')
        del final_df

        merged_df = merged_df[['地域', '国', '時間軸(年次)', '統計品目表の数量・金額', '税関', '部数', '部名', '類数', '類名', 'HSコード',
                               '大項目', '中項目', '小項目', '細項目', '微細項目', '項目', '金額', 'unit', '数量', '単位2']]
        column_mapping = {'時間軸(年次)': '年', '統計品目表の数量・金額': '月', '単位2': '数量単位', 'unit': '金額単位'}
        merged_df.rename(columns=column_mapping, inplace=True)

        data_acquisition_date = datetime.now().strftime('%Y%m%d')
        csv_filename = f'{year}_月次_税関別_{statdataID}_{data_acquisition_date}.csv'
        csv_path = f'/content/drive/MyDrive/政府統計/貿易統計/04_output/HS item/{csv_filename}'
        # merged_df.to_csv(csv_path, index=False)

        for rui in HS_master['部数'].unique():
            rui_merged_df = merged_df[merged_df['部数'] == rui]
            part_number = int(re.search(r'\d+', rui).group())
            csv_filename = f'Export_{year}_{part_number}_port.csv'
            folder_path = f'/content/drive/MyDrive/政府統計/貿易統計/04_output/HS item/類別/{rui}/'
            os.makedirs(folder_path, exist_ok=True)
            csv_path = os.path.join(folder_path, csv_filename)
            rui_merged_df.to_csv(csv_path, index=False)

        for nation in nation_df['地域'].unique():
            nation_merged_df = merged_df[merged_df['地域'] == nation]
            eng_nation = nation_df[nation_df['地域'] == nation]['地域(英語)'].unique()[0]
            csv_filename = f'Export_{year}_{eng_nation}_port.csv'
            folder_path = f'/content/drive/MyDrive/政府統計/貿易統計/04_output/HS item/地域別/{nation}/'
            os.makedirs(folder_path, exist_ok=True)
            csv_path = os.path.join(folder_path, csv_filename)
            nation_merged_df.to_csv(csv_path, index=False)

        end_time = datetime.now()
        execution_time = end_time - start_time
        minutes, seconds = divmod(int(execution_time.total_seconds()), 60)
        print(f"セルの実行時間: {minutes}分 {seconds}秒\n")

    print('取得終了')
