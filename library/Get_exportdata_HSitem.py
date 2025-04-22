import requests
import os
import re
import pandas as pd
from datetime import datetime
from io import StringIO



def get_data(statdataID, startPosition, cat02,year,api_key):
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




def run_trade_data_pipeline(hs_counter_df, trade_counter_df, nation_df,m_q_list,api_key):
    # セルの実行開始時刻を記録
    start_time = datetime.now()
    print('取得開始')

 
    for l in range(len(hs_counter_df)): # start_year ~ end_yearのstatdataI
        all_dfs=[]
        statdataID=trade_counter_df['statdataID'][l]
        year=trade_counter_df['year'][l]
        cat02_list=m_q_list
        print('分類：',hs_counter_df['分類'][l],', 年度：',hs_counter_df['year'][l],', StatdataID：',hs_counter_df['statdataID'][l])
        syutoku_data=0
        startPosition = 1  # init
        # 10万件未満⇒next_startPosition = 1
        # 10万件以上⇒next_startPosition > 1
        df, next_startPosition = get_data(statdataID, startPosition,cat02_list,year,api_key)
        if df.columns[0]=='RESULT':
            syutoku_data+=len(df)
            print(' - - 取得完了:',syutoku_data,'行')
            break
        all_dfs.append(df)

        # 1回のAPI呼び出しあたり10万件未満(next_startPosition=1)になるまで取得し続ける.
        """""
        while int(next_startPosition) > 1:
            syutoku_data+=len(df)
            print(' - - 取得完了:',syutoku_data,'行')
            df, next_startPosition = get_data(statdataID, next_startPosition,cat02_list,year,api_key)
            all_dfs.append(df)
        syutoku_data+=len(df)
        print(' - - 取得完了:',syutoku_data,'行')
        """


        final_df = pd.concat(all_dfs, ignore_index=True)
        del all_dfs
        # '国' 列のデータから '_' より右の国名だけを取得
        final_df['国'] = final_df['国'].str.split('_').str[1]
        # '統計品目表の数量・金額' 列のデータから '_' より右のフラグだけを取得
        final_df['数量・金額'] = final_df['統計品目表の数量・金額'].str.split('_').str[1]
        # '統計品目表の数量・金額' 列のデータから '_' より左の月だけを取得
        final_df['統計品目表の数量・金額'] = final_df['統計品目表の数量・金額'].str.split('_').str[0]
        selected_columns = ['時間軸(年次)','cat01_code', '統計品目表の数量・金額', '税関', '国','数量・金額','value']
        final_df_q = final_df[final_df['数量・金額'] == '数量2'][selected_columns]
        final_df_q.rename(columns={'value': '数量'}, inplace=True)


        selected_columns = ['時間軸(年次)','cat01_code', '統計品目表の数量・金額', '税関', '国','unit','数量・金額','value']
        final_df_m=final_df[final_df['数量・金額'] == '金額'][selected_columns]

        # カラムの名前を変更
        final_df_m.rename(columns={'value': '金額'}, inplace=True)
        del final_df
        # df1とdf2を指定の列で結合
        print(len(final_df_m),len(final_df_q))
        print(final_df_m.columns)
        print(final_df_q.columns)
        final_df = pd.merge(final_df_m, final_df_q, on=['cat01_code', '統計品目表の数量・金額', '税関', '国','時間軸(年次)'], how='inner')
        print(len(final_df),len(final_df_q))
        del final_df_q,final_df_m

        HS_master=pd.read_csv(f'reference_master/HS_master/HSコードマスタ_{year}.csv')
        merged_df = pd.merge(final_df, HS_master, left_on='cat01_code', right_on='HSコード', how='left')
        print(len(merged_df))
        merged_df=pd.merge(merged_df, nation_df, left_on='国', right_on='国', how='left')
        del final_df

        merged_df=merged_df[['地域','国','時間軸(年次)','統計品目表の数量・金額','税関','部数','部名', '類数', '類名', 'HSコード', '大項目', '中項目', '小項目', '細項目', '微細項目', '項目', '金額','unit','数量','単位2']]
        column_mapping = {'時間軸(年次)':'年','統計品目表の数量・金額':'月','単位2': '数量単位','unit':'金額単位'}
        merged_df = merged_df.copy()  
        merged_df.rename(columns=column_mapping, inplace=True)  
        # データ取得日の日付を取得（例として今日の日付を使用）
        data_acquisition_date = datetime.now().strftime('%Y%m%d')
        csv_filename = f'{year}_月次_税関別_{data_acquisition_date}.csv'
        csv_path = f'./Output/HS_item/{csv_filename}'
        merged_df.to_csv(csv_path, index=False, encoding='utf-8-sig')

        end_time = datetime.now()
        execution_time = end_time - start_time
        total_seconds = execution_time.total_seconds()
        minutes, seconds = divmod(int(total_seconds), 60)
        print(f"セルの実行時間: {minutes}分 {seconds}秒")
        print('')
    print('取得終了')
    return merged_df