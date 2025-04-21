from selenium import webdriver
import urllib.request
import requests
import pandas as pd
from bs4 import BeautifulSoup
import os
from io import StringIO



def generate_customs_urls(year, month, nu_range):
    urls = []
    print(1)
    for No in nu_range:
        # 77類は存在しないのでスキップ
        if No == 77:
            continue
        if year>=2022:
            url = f'https://www.customs.go.jp/yusyutu/{year:04d}_{month:02d}_01/data/print_j_{No:02d}.htm'
        elif year>=2020:
            if month==4:
                url = f'https://www.customs.go.jp/yusyutu/{year:04d}_{month:1d}/data/print_j_{No:02d}.htm'
            else:
                url = f'https://www.customs.go.jp/yusyutu/{year:04d}_1/data/print_j_{No:02d}.htm'
        elif year>=2017:
            if month==4:
                url = f'https://www.customs.go.jp/yusyutu/{year:04d}_{month:1d}/data/print_j_{No:02d}.htm'
            else:
                url = f'https://www.customs.go.jp/yusyutu/{year:04d}/data/print_j_{No:02d}.htm'
        elif year>=2016:
                url = f'https://www.customs.go.jp/yusyutu/{year:04d}/data/print_j_{No:02d}.htm'
        elif year>=2010:
                url = f'https://www.customs.go.jp/yusyutu/{year:04d}/data/print_e{year:04d}01j_{No:02d}.htm'
        else:
            raise ValueError('2010年度未満は未対応です')
            break
        urls.append(url)
    return urls


def scrape_and_process_data(url):
    # リクエストを送信
    response = requests.get(url)
    # エンコーディングをcp932に指定してパース
    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='cp932')
    # テーブル内の各セルのデータを抽出
    rows = soup.find_all('tr')
    data = []
    for row in rows:
        cols = row.find_all(['td'])
        cols = [col.text.strip() for col in cols]
        data.append(cols)
    # データをDataFrameに変換
    df = pd.DataFrame([row[:5] for row in data[5:]], columns=['HSコード_大', 'HSコード_小', '品名', '単位1', '単位2'])
    burui_master = pd.read_csv('s3://project-opendata/01_貿易統計/01_import/HScode/HSコードマスタ_部類.csv')
    burui_master['番号']=burui_master['類数'].str.replace(r'^第(\d+)類$', lambda x: '{:02d}'.format(int(x.group(1))), regex=True)
    temp = burui_master[burui_master['番号'] == url[-6:][:2]].reset_index(drop=True)
    df['部数'], df['部名'] = temp['部数'][0], temp['部名'][0]
    df['類数'], df['類名'] = temp['類数'][0], temp['類名'][0]
    # 特定の条件に基づいて行を除外
    condition_to_exclude = ~((df['HSコード_大'] == '') & (df['HSコード_小'] == '') & (df['品名'].str.startswith('第')))
    df = df[condition_to_exclude].reset_index(drop=True)
    return df


def HS_code_master(url):
    df=scrape_and_process_data(url)
    num=len(df)-1
    for i in range(len(df)):

        leading_hyphens_count = len(df.at[i, '品名']) - len(df.at[i, '品名'].lstrip('－'))
        #print(leading_hyphens_count)
        if df.at[i, 'HSコード_大'] != '' and df.at[i, '品名']=='':
             df.at[i, '品名'] = df.at[i + 1, '品名']
        if df.at[i, 'HSコード_大'] == '' and leading_hyphens_count == 1:
            if i!=num:
                if len(df.at[i+1, '品名']) - len(df.at[i+1, '品名'].lstrip('－'))>=2:
                    df.at[i, 'HSコード_大'] = df.at[i + 1, 'HSコード_大']
                elif len(df.at[i+1, '品名']) - len(df.at[i+1, '品名'].lstrip('－'))<=1:
                    df.at[i, 'HSコード_大'] = df.at[i - 1, 'HSコード_大']
            elif i==num:
                df.at[i, 'HSコード_大'] = df.at[i - 1, 'HSコード_大']
        elif df.at[i, 'HSコード_大'] == '' and leading_hyphens_count == 2:
            df.at[i, 'HSコード_大'] = df.at[i - 1, 'HSコード_大']
        elif df.at[i, 'HSコード_大'] == '' and leading_hyphens_count >= 3:
            df.at[i, 'HSコード_大'] = df.at[i - 1, 'HSコード_大']
    for i in range(len(df)):
        leading_hyphens_count = len(df.at[i, '品名']) - len(df.at[i, '品名'].lstrip('－'))
        if df.at[i, 'HSコード_小'] == '' and leading_hyphens_count == 4:
            df.at[i, 'HSコード_小'] = df.at[i + 1, 'HSコード_小']
    for i in range(len(df)):
        leading_hyphens_count = len(df.at[i, '品名']) - len(df.at[i, '品名'].lstrip('－'))
        if df.at[i, 'HSコード_小'] == '' and leading_hyphens_count == 3:
            df.at[i, 'HSコード_小'] = df.at[i + 1, 'HSコード_小']
    for i in range(len(df)):
        leading_hyphens_count = len(df.at[i, '品名']) - len(df.at[i, '品名'].lstrip('－'))
        if df.at[i, 'HSコード_小'] == '' and leading_hyphens_count == 2:
            df.at[i, 'HSコード_小'] = df.at[i + 1, 'HSコード_小']

    # 条件に基づいて単位2がある行とない行を分ける
    df_with_unit2 = df[df['単位2'] != ''].copy()
    df_without_unit2 = df[df['単位2'] == ''].copy()
    # 関数の仕様
    df_without_unit2=add_flg(df_without_unit2)
    df_with_unit2=add_flg(df_with_unit2)

    df_master=df_with_unit2[['部数','部名','類数','類名','HSコード','大項目','中項目','小項目','細項目','微細項目','項目','単位2']]
    df_master = df_master.copy()

    df_without_unit2_very_detail = df_without_unit2[df_without_unit2['微細項目'].notna()][['HSコード','微細項目']]
    df_without_unit2_very_detail['HSコード'] = df_without_unit2_very_detail['HSコード'].astype(str).str[:8]
    # df_without_unit2_smallからのマッピング
    df_master.loc[df_master['微細項目'].isna(), '微細項目'] = df_master.loc[df_master['微細項目'].isna(), 'HSコード'].str[:8].map(df_without_unit2_very_detail.set_index('HSコード')['微細項目'])

    df_without_unit2_detail = df_without_unit2[df_without_unit2['細項目'].notna()][['HSコード','細項目']]
    df_without_unit2_detail['HSコード'] = df_without_unit2_detail['HSコード'].astype(str).str[:7]
    if len(df_without_unit2_detail[df_without_unit2_detail.duplicated(subset='HSコード', keep=False)])>0:
        df_without_unit2_detail,df_without_unit2_detail_sp=detail_sp(df_without_unit2_detail,df_without_unit2)
        # df_without_unit2_detailからのマッピング
        df_master.loc[df_master['細項目'].isna(), '細項目'] = df_master.loc[df_master['細項目'].isna(), 'HSコード'].str[:7].map(df_without_unit2_detail.set_index('HSコード')['細項目'])
        df_master.loc[df_master['細項目'].isna(), '細項目'] = df_master.loc[df_master['細項目'].isna(), 'HSコード'].str[:8].map(df_without_unit2_detail_sp.set_index('HSコード_new')['細項目'])
    else:
        df_master.loc[df_master['細項目'].isna(), '細項目'] = df_master.loc[df_master['細項目'].isna(), 'HSコード'].str[:7].map(df_without_unit2_detail.set_index('HSコード')['細項目'])

    df_without_unit2_small = df_without_unit2[df_without_unit2['小項目'].notna()][['HSコード','小項目']]
    df_without_unit2_small['HSコード'] = df_without_unit2_small['HSコード'].astype(str).str[:6]
    if len(df_without_unit2_small[df_without_unit2_small.duplicated(subset='HSコード', keep=False)])>0:
        df_without_unit2_small,df_without_unit2_small_sp=small_sp(df_without_unit2_small,df_without_unit2)
        # df_without_unit2_smallからのマッピング
        df_master.loc[df_master['小項目'].isna(), '小項目'] = df_master.loc[df_master['小項目'].isna(), 'HSコード'].str[:6].map(df_without_unit2_small.set_index('HSコード')['小項目'])
        df_master.loc[df_master['小項目'].isna(), '小項目'] = df_master.loc[df_master['小項目'].isna(), 'HSコード'].str[:7].map(df_without_unit2_small_sp.set_index('HSコード_new')['小項目'])
    else:
        df_master.loc[df_master['小項目'].isna(), '小項目'] = df_master.loc[df_master['小項目'].isna(), 'HSコード'].str[:6].map(df_without_unit2_small.set_index('HSコード')['小項目'])

    df_without_unit2_med = df_without_unit2[df_without_unit2['中項目'].notna()][['HSコード','中項目']]
    df_without_unit2_med['HSコード'] = df_without_unit2_med['HSコード'].astype(str).str[:5]
    if len(df_without_unit2_med[df_without_unit2_med.duplicated(subset='HSコード', keep=False)])>0:
        df_without_unit2_med,df_without_unit2_med_sp=med_sp(df_without_unit2_med,df_without_unit2)
        # df_without_unit2_medからのマッピング
        df_master.loc[df_master['中項目'].isna(), '中項目'] = df_master.loc[df_master['中項目'].isna(), 'HSコード'].str[:5].map(df_without_unit2_med.set_index('HSコード')['中項目'])
        #df_master.loc[df_master['中項目'].isna(), '中項目'] = df_master.loc[df_master['中項目'].isna(), 'HSコード'].str[:6].map(df_without_unit2_med_sp.set_index('HSコード_new')['中項目'])
    else:
        df_master.loc[df_master['中項目'].isna(), '中項目'] = df_master.loc[df_master['中項目'].isna(), 'HSコード'].str[:5].map(df_without_unit2_med.set_index('HSコード')['中項目'])

    df_without_unit2_big = df_without_unit2[df_without_unit2['大項目'].notna()][['HSコード','大項目']]
    # df_without_unit2_bigからのマッピング
    df_master.loc[df_master['大項目'].isna(), '大項目'] = df_master.loc[df_master['大項目'].isna(), 'HSコード'].str[:4].map(df_without_unit2_big.set_index('HSコード')['大項目'])
    return df_master


def HS_code_master_72(url):
    df=scrape_and_process_data(url)
    # 72類のみ項目よりももう一段階細かい粒度が存在するが、細かすぎるのでそれは取得しない。
    df = df[df.apply(lambda row: len(row['品名']) - len(row['品名'].lstrip('－')) < 6, axis=1)].reset_index(drop=True)
    num=len(df)-1
    for i in range(len(df)):

        leading_hyphens_count = len(df.at[i, '品名']) - len(df.at[i, '品名'].lstrip('－'))
        #print(leading_hyphens_count)
        if df.at[i, 'HSコード_大'] != '' and df.at[i, '品名']=='':
             df.at[i, '品名'] = df.at[i + 1, '品名']
        if df.at[i, 'HSコード_大'] == '' and leading_hyphens_count == 1:
            if i!=num:
                if len(df.at[i+1, '品名']) - len(df.at[i+1, '品名'].lstrip('－'))>=2:
                    df.at[i, 'HSコード_大'] = df.at[i + 1, 'HSコード_大']
                elif len(df.at[i+1, '品名']) - len(df.at[i+1, '品名'].lstrip('－'))<=1:
                    df.at[i, 'HSコード_大'] = df.at[i - 1, 'HSコード_大']
            elif i==num:
                df.at[i, 'HSコード_大'] = df.at[i - 1, 'HSコード_大']
        elif df.at[i, 'HSコード_大'] == '' and leading_hyphens_count == 2:
            df.at[i, 'HSコード_大'] = df.at[i - 1, 'HSコード_大']
        elif df.at[i, 'HSコード_大'] == '' and leading_hyphens_count >= 3:
            df.at[i, 'HSコード_大'] = df.at[i - 1, 'HSコード_大']
    for i in range(len(df)):
        leading_hyphens_count = len(df.at[i, '品名']) - len(df.at[i, '品名'].lstrip('－'))
        if df.at[i, 'HSコード_小'] == '' and leading_hyphens_count == 4:
            df.at[i, 'HSコード_小'] = df.at[i + 1, 'HSコード_小']
    for i in range(len(df)):
        leading_hyphens_count = len(df.at[i, '品名']) - len(df.at[i, '品名'].lstrip('－'))
        if df.at[i, 'HSコード_小'] == '' and leading_hyphens_count == 3:
            df.at[i, 'HSコード_小'] = df.at[i + 1, 'HSコード_小']
    for i in range(len(df)):
        leading_hyphens_count = len(df.at[i, '品名']) - len(df.at[i, '品名'].lstrip('－'))
        if df.at[i, 'HSコード_小'] == '' and leading_hyphens_count == 2:
            df.at[i, 'HSコード_小'] = df.at[i + 1, 'HSコード_小']

    # 条件に基づいて単位2がある行とない行を分ける
    df_with_unit2 = df[df['単位2'] != ''].copy()
    df_without_unit2 = df[df['単位2'] == ''].copy()
    # 関数の仕様
    df_without_unit2=add_flg(df_without_unit2)
    df_with_unit2=add_flg(df_with_unit2)

    df_master=df_with_unit2[['部数','部名','類数','類名','HSコード','大項目','中項目','小項目','細項目','微細項目','項目','単位2']]
    df_master = df_master.copy()

    df_without_unit2_very_detail = df_without_unit2[df_without_unit2['微細項目'].notna()][['HSコード','微細項目']]
    df_without_unit2_very_detail['HSコード'] = df_without_unit2_very_detail['HSコード'].astype(str).str[:8]
    # df_without_unit2_smallからのマッピング
    df_master.loc[df_master['微細項目'].isna(), '微細項目'] = df_master.loc[df_master['微細項目'].isna(), 'HSコード'].str[:8].map(df_without_unit2_very_detail.set_index('HSコード')['微細項目'])
    # New DataFrame with HSコード in the specified range (as strings)
    new_hs_codes = pd.DataFrame({'HSコード': map(str, range(72149000, 72150001))})
    df_without_unit2_very_detail_sp = pd.merge(new_hs_codes, df_without_unit2_very_detail, on='HSコード', how='left')
    # Fill missing values in '微細項目' with the previous row's value
    for i in range(len(df_without_unit2_very_detail_sp)):
        if pd.isnull(df_without_unit2_very_detail_sp.at[i, '微細項目']) and i >= 1:
            df_without_unit2_very_detail_sp.at[i, '微細項目'] = df_without_unit2_very_detail_sp.at[i - 1, '微細項目']
    df_master.loc[df_master['微細項目'].isna() & ~df_master['項目'].isna(), '微細項目']= df_master.loc[df_master['微細項目'].isna(), 'HSコード'].str[:8].map(df_without_unit2_very_detail_sp.set_index('HSコード')['微細項目'])

    df_without_unit2_detail = df_without_unit2[df_without_unit2['細項目'].notna()][['HSコード','細項目']]
    df_without_unit2_detail['HSコード'] = df_without_unit2_detail['HSコード'].astype(str).str[:7]
    if len(df_without_unit2_detail[df_without_unit2_detail.duplicated(subset='HSコード', keep=False)])>0:
        df_without_unit2_detail,df_without_unit2_detail_sp=detail_sp(df_without_unit2_detail,df_without_unit2)
        # df_without_unit2_smallからのマッピング
        df_master.loc[df_master['細項目'].isna(), '細項目'] = df_master.loc[df_master['細項目'].isna(), 'HSコード'].str[:7].map(df_without_unit2_detail.set_index('HSコード')['細項目'])
        df_master.loc[df_master['細項目'].isna(), '細項目'] = df_master.loc[df_master['細項目'].isna(), 'HSコード'].str[:8].map(df_without_unit2_detail_sp.set_index('HSコード_new')['細項目'])
    else:
        df_master.loc[df_master['細項目'].isna(), '細項目'] = df_master.loc[df_master['細項目'].isna(), 'HSコード'].str[:7].map(df_without_unit2_detail.set_index('HSコード')['細項目'])

    df_without_unit2_small = df_without_unit2[df_without_unit2['小項目'].notna()][['HSコード','小項目']]
    df_without_unit2_small['HSコード'] = df_without_unit2_small['HSコード'].astype(str).str[:6]
    if len(df_without_unit2_small[df_without_unit2_small.duplicated(subset='HSコード', keep=False)])>0:
        df_without_unit2_small,df_without_unit2_small_sp=small_sp(df_without_unit2_small,df_without_unit2)
        # df_without_unit2_smallからのマッピング
        df_master.loc[df_master['小項目'].isna(), '小項目'] = df_master.loc[df_master['小項目'].isna(), 'HSコード'].str[:6].map(df_without_unit2_small.set_index('HSコード')['小項目'])
        df_master.loc[df_master['小項目'].isna(), '小項目'] = df_master.loc[df_master['小項目'].isna(), 'HSコード'].str[:7].map(df_without_unit2_small_sp.set_index('HSコード_new')['小項目'])
    else:
        df_master.loc[df_master['小項目'].isna(), '小項目'] = df_master.loc[df_master['小項目'].isna(), 'HSコード'].str[:6].map(df_without_unit2_small.set_index('HSコード')['小項目'])

    df_without_unit2_med = df_without_unit2[df_without_unit2['中項目'].notna()][['HSコード','中項目']]
    df_without_unit2_med['HSコード'] = df_without_unit2_med['HSコード'].astype(str).str[:5]
    if len(df_without_unit2_med[df_without_unit2_med.duplicated(subset='HSコード', keep=False)])>0:
        df_without_unit2_med,df_without_unit2_med_sp=med_sp(df_without_unit2_med,df_without_unit2)
        # df_without_unit2_smallからのマッピング
        df_master.loc[df_master['中項目'].isna(), '中項目'] = df_master.loc[df_master['中項目'].isna(), 'HSコード'].str[:5].map(df_without_unit2_med.set_index('HSコード')['中項目'])
        df_master.loc[df_master['中項目'].isna(), '中項目'] = df_master.loc[df_master['中項目'].isna(), 'HSコード'].str[:6].map(df_without_unit2_med_sp.set_index('HSコード_new')['中項目'])
    else:
        df_master.loc[df_master['中項目'].isna(), '中項目'] = df_master.loc[df_master['中項目'].isna(), 'HSコード'].str[:5].map(df_without_unit2_med.set_index('HSコード')['中項目'])
    # df_without_unit2_medからのマッピング
    #df_master.loc[df_master['中項目'].isna(), '中項目'] = df_master.loc[df_master['中項目'].isna(), 'HSコード'].str[:5].map(df_without_unit2_med.set_index('HSコード')['中項目'])

    df_without_unit2_big = df_without_unit2[df_without_unit2['大項目'].notna()][['HSコード','大項目']]
    # df_without_unit2_bigからのマッピング
    df_master.loc[df_master['大項目'].isna(), '大項目'] = df_master.loc[df_master['大項目'].isna(), 'HSコード'].str[:4].map(df_without_unit2_big.set_index('HSコード')['大項目'])
    return df_master


def HS_code_master_80(url):
    df=scrape_and_process_data(url)
    for i in range(len(df)):

        leading_hyphens_count = len(df.at[i, '品名']) - len(df.at[i, '品名'].lstrip('－'))
        #print(leading_hyphens_count)
        if df.at[i, 'HSコード_大'] == '' and leading_hyphens_count == 1:
            df.at[i, 'HSコード_大'] = df.at[i - 1, 'HSコード_大']

    # 条件に基づいて単位2がある行とない行を分ける
    df_with_unit2 = df[df['単位2'] != ''].copy()
    df_without_unit2 = df[df['単位2'] == ''].copy()

    df_without_unit2=add_flg(df_without_unit2)
    df_with_unit2=add_flg(df_with_unit2)

    df_master=df_with_unit2[['部数','部名','類数','類名','HSコード','大項目','中項目','小項目','細項目','微細項目','項目','単位2']]
    df_master = df_master.copy()
    df_without_unit2_big = df_without_unit2[df_without_unit2['大項目'].notna()][['HSコード','大項目']]
    df_without_unit2_big['HSコード'] = df_without_unit2_big['HSコード'].astype(str).str[:4]
    df_without_unit2_big = df_without_unit2_big[df_without_unit2_big['大項目'] != '']
    # df_without_unit2_bigからのマッピング
    df_master.loc[df_master['大項目'].isna(), '大項目'] = df_master.loc[df_master['大項目'].isna(), 'HSコード'].str[:4].map(df_without_unit2_big.set_index('HSコード')['大項目'])
    return df_master


def detail_sp(df_without_unit2_detail,df_without_unit2):
    # 'HSコード'をキーにして重複を判定し、重複している行を抽出
    duplicated_detail = df_without_unit2_detail[df_without_unit2_detail.duplicated(subset='HSコード', keep=False)]
    # 重複していない行を抽出
    df_without_unit2_detail = df_without_unit2_detail.drop_duplicates(subset='HSコード', keep=False)
    df_without_unit2_detail_sp=df_without_unit2[df_without_unit2['細項目'].notna()][['HSコード','細項目']]
    df_without_unit2_detail_sp.rename(columns={'HSコード': 'HSコード_new'}, inplace=True)
    df_without_unit2_detail_sp['HSコード'] = df_without_unit2_detail_sp['HSコード_new'].astype(str).str[:7]
    df_without_unit2_detail_sp=df_without_unit2_detail_sp.merge(duplicated_detail[['HSコード', '細項目']], on=['HSコード', '細項目'], how='inner')[['HSコード_new','細項目']]
    df_without_unit2_detail_sp['HSコード_new']=df_without_unit2_detail_sp['HSコード_new'].astype(str).str[:8]
    return df_without_unit2_detail,df_without_unit2_detail_sp

def small_sp(df_without_unit2_small,df_without_unit2):
    # 'HSコード'をキーにして重複を判定し、重複している行を抽出
    duplicated_small = df_without_unit2_small[df_without_unit2_small.duplicated(subset='HSコード', keep=False)]
    # 重複していない行を抽出
    df_without_unit2_small = df_without_unit2_small.drop_duplicates(subset='HSコード', keep=False)
    df_without_unit2_small_sp=df_without_unit2[df_without_unit2['小項目'].notna()][['HSコード','小項目']]
    df_without_unit2_small_sp.rename(columns={'HSコード': 'HSコード_new'}, inplace=True)
    df_without_unit2_small_sp['HSコード'] = df_without_unit2_small_sp['HSコード_new'].astype(str).str[:6]
    df_without_unit2_small_sp=df_without_unit2_small_sp.merge(duplicated_small[['HSコード', '小項目']], on=['HSコード', '小項目'], how='inner')[['HSコード_new','小項目']]
    df_without_unit2_small_sp['HSコード_new']=df_without_unit2_small_sp['HSコード_new'].astype(str).str[:7]
    return df_without_unit2_small,df_without_unit2_small_sp

def med_sp(df_without_unit2_med,df_without_unit2):
    print('med発生')
    # 'HSコード'をキーにして重複を判定し、重複している行を抽出
    duplicated_med = df_without_unit2_med[df_without_unit2_med.duplicated(subset='HSコード', keep=False)]
    # 重複していない行を抽出
    df_without_unit2_med = df_without_unit2_med.drop_duplicates(subset='HSコード', keep=False)
    df_without_unit2_med_sp=df_without_unit2[df_without_unit2['中項目'].notna()][['HSコード','中項目']]
    df_without_unit2_med_sp.rename(columns={'HSコード': 'HSコード_new'}, inplace=True)
    df_without_unit2_med_sp['HSコード'] = df_without_unit2_med_sp['HSコード_new'].astype(str).str[:5]
    df_without_unit2_med_sp=df_without_unit2_med_sp.merge(duplicated_med[['HSコード', '中項目']], on=['HSコード', '中項目'], how='inner')[['HSコード_new','中項目']]
    df_without_unit2_med_sp['HSコード_new']=df_without_unit2_med_sp['HSコード_new'].astype(str).str[:6]
    print(df_without_unit2_med_sp)
    return df_without_unit2_med,df_without_unit2_med_sp

# 関数を定義して項目を追加
def add_flg(df_subset):
    item_column_name='品名'
    df_subset.loc[:, '大項目'] = df_subset.apply(lambda row: row[item_column_name] if len(row[item_column_name]) - len(row[item_column_name].lstrip('－')) == 0 else None, axis=1)
    df_subset.loc[:, '中項目'] = df_subset.apply(lambda row: row[item_column_name] if len(row[item_column_name]) - len(row[item_column_name].lstrip('－')) == 1 else None, axis=1)
    df_subset.loc[:, '小項目'] = df_subset.apply(lambda row: row[item_column_name] if len(row[item_column_name]) - len(row[item_column_name].lstrip('－')) == 2 else None, axis=1)
    df_subset.loc[:, '細項目'] = df_subset.apply(lambda row: row[item_column_name] if len(row[item_column_name]) - len(row[item_column_name].lstrip('－')) == 3 else None, axis=1)
    df_subset.loc[:, '微細項目'] = df_subset.apply(lambda row: row[item_column_name] if len(row[item_column_name]) - len(row[item_column_name].lstrip('－')) == 4 else None, axis=1)
    df_subset.loc[:, '項目'] = df_subset.apply(lambda row: row[item_column_name] if len(row[item_column_name]) - len(row[item_column_name].lstrip('－')) == 5 else None, axis=1)
    df_subset.loc[:, 'HSコード'] = (df_subset['HSコード_大']+df_subset['HSコード_小']).str.replace('.', '')
    return df_subset


def fetch_and_concat_data(urls):
    dfs = []
    for url in urls:
        print(url)
        if url.endswith('80.htm'):
            df = HS_code_master_80(url)
        elif url.endswith('72.htm'):
            df = HS_code_master_72(url)
        else:
            df = HS_code_master(url)
        dfs.append(df)
    
    result_df = pd.concat(dfs, ignore_index=True)
    return result_df

