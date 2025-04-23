# hs_code_scraper.py - Full Version

import os
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime


class HSCodeScraper:
    def __init__(self, year: int, month: int, range_nums: range):
        self.year = year
        self.month = month
        self.range_nums = range_nums
        self.urls = self.generate_urls()
        self.base_dir = os.path.dirname(__file__)
        self.burui_path = os.path.abspath(os.path.join(self.base_dir, '..', 'reference_master', 'HS_master', 'HSコードマスタ_部類.csv'))

    def generate_urls(self):
        urls = []
        for No in self.range_nums:
            if No == 77:
                continue
            if self.year >= 2022:
                url = f'https://www.customs.go.jp/yusyutu/{self.year:04d}_{self.month:02d}_01/data/print_j_{No:02d}.htm'
            elif self.year >= 2020:
                if self.month == 4:
                    url = f'https://www.customs.go.jp/yusyutu/{self.year:04d}_{self.month}/data/print_j_{No:02d}.htm'
                else:
                    url = f'https://www.customs.go.jp/yusyutu/{self.year:04d}_1/data/print_j_{No:02d}.htm'
            elif self.year >= 2017:
                if self.month == 4:
                    url = f'https://www.customs.go.jp/yusyutu/{self.year:04d}_{self.month}/data/print_j_{No:02d}.htm'
                else:
                    url = f'https://www.customs.go.jp/yusyutu/{self.year:04d}/data/print_j_{No:02d}.htm'
            elif self.year >= 2016:
                url = f'https://www.customs.go.jp/yusyutu/{self.year:04d}/data/print_j_{No:02d}.htm'
            elif self.year >= 2010:
                url = f'https://www.customs.go.jp/yusyutu/{self.year:04d}/data/print_e{self.year:04d}01j_{No:02d}.htm'
            else:
                raise ValueError('Years before 2010 are not supported.')
            urls.append(url)
        return urls

    def scrape_and_process_url(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser', from_encoding='cp932')
        rows = soup.find_all('tr')
        data = [[col.text.strip() for col in row.find_all(['td'])] for row in rows]
        df = pd.DataFrame([row[:5] for row in data[5:]], columns=['HSコード_大', 'HSコード_小', '品名', '単位1', '単位2'])

        burui_master = pd.read_csv(self.burui_path)
        burui_master['番号'] = burui_master['類数'].str.replace(r'^第(\d+)類$', lambda x: '{:02d}'.format(int(x.group(1))), regex=True)
        temp = burui_master[burui_master['番号'] == url[-6:][:2]].reset_index(drop=True)

        for col in ['部数', '部名', '類数', '類名']:
            df[col] = temp[col][0]

        condition = ~((df['HSコード_大'] == '') & (df['HSコード_小'] == '') & (df['品名'].str.startswith('第')))
        df = df[condition].reset_index(drop=True)
        return df

    def add_flg(self, df):
        item_column = '品名'
        df['大項目'] = df[item_column].apply(lambda x: x if x.startswith('－') is False else None)
        df['中項目'] = df[item_column].apply(lambda x: x if x.startswith('－') and x.count('－') == 1 else None)
        df['小項目'] = df[item_column].apply(lambda x: x if x.startswith('－－') and x.count('－') == 2 else None)
        df['細項目'] = df[item_column].apply(lambda x: x if x.startswith('－－－') and x.count('－') == 3 else None)
        df['微細項目'] = df[item_column].apply(lambda x: x if x.startswith('－－－－') and x.count('－') == 4 else None)
        df['項目'] = df[item_column].apply(lambda x: x if x.startswith('－－－－－') and x.count('－') == 5 else None)
        df['HSコード'] = (df['HSコード_大'] + df['HSコード_小']).str.replace('.', '')
        return df

    def scrape_all(self):
        dfs = []
        for url in self.urls:
            df = self.scrape_and_process_url(url)
            df = self.add_flg(df)
            dfs.append(df)
        return pd.concat(dfs, ignore_index=True)

    def save_to_csv(self, df, output_dir='./output', prefix='HSコードマスタ'):
        os.makedirs(output_dir, exist_ok=True)
        date = datetime.now().strftime('%Y%m%d')
        path = os.path.join(output_dir, f'{prefix}_{self.year}_{self.month:02d}_{date}.csv')
        df.to_csv(path, index=False, encoding='utf-8')
        print(f'✅ Saved: {path}')


if __name__ == '__main__':
    scraper = HSCodeScraper(year=2024, month=1, range_nums=range(1, 98))
    df = scraper.scrape_all()
    scraper.save_to_csv(df)
