import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
from datetime import datetime
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class AjsmScraper:
    def __init__(self):
        self.base_url = "https://ajsm.club"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Seleniumの設定
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # ヘッドレスモード
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')  # ウィンドウサイズを設定
        options.add_argument(f'user-agent={self.headers["User-Agent"]}')
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)  # 暗黙的な待機を10秒に設定

    def dismiss_ad(self):
        """広告を消す（広告が表示されている場合のみ）"""
        try:
            # 広告のiframeが存在するか確認
            iframes = self.driver.find_elements(By.CSS_SELECTOR, "iframe[title='Advertisement']")
            if not iframes:
                return  # 広告がない場合は何もしない
            
            # 広告のiframeを切り替え
            self.driver.switch_to.frame(iframes[0])
            
            # 広告の閉じるボタンが存在するか確認
            dismiss_buttons = self.driver.find_elements(By.CSS_SELECTOR, "div#dismiss-button")
            if dismiss_buttons:
                dismiss_buttons[0].click()
                time.sleep(1)  # 広告が消えるのを待つ
            
            # メインフレームに戻る
            self.driver.switch_to.default_content()
            
        except Exception as e:
            print(f"広告を消す処理でエラーが発生しました: {str(e)}")
            # エラーが発生してもメインフレームに戻る
            try:
                self.driver.switch_to.default_content()
            except:
                pass

    def get_municipalities(self, prefecture_url):
        """都道府県ページから自治体情報を取得"""
        try:
            # Seleniumでページを開く
            self.driver.get(prefecture_url)
            
            # ページの読み込みを待つ
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)  # 追加の待機時間
            
            # 広告を消す
            self.dismiss_ad()
            
            # ページのHTMLを取得
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # デバッグ情報を出力
            print(f"ページタイトル: {soup.title.string if soup.title else 'タイトルなし'}")
            print(f"ページのURL: {self.driver.current_url}")
            
            # fr クラスを持つ div を取得
            fr_divs = soup.find_all('div', class_='fr')
            print(f"fr divの数: {len(fr_divs)}")
            
            municipalities = []
            
            # 各 fr div を処理
            for div in fr_divs:
                link = div.find('a')
                if not link:
                    continue
                
                href = link.get('href')
                if href and 'Area' in href:  # Area を含むリンクを自治体とみなす
                    municipality_name = link.text.strip()
                    municipality_url = self.base_url + href.replace('./', '/')
                    
                    municipalities.append({
                        'name': municipality_name,
                        'url': municipality_url,
                        'store_count': 0
                    })
            
            print(f"取得した自治体数: {len(municipalities)}")
            return municipalities
            
        except Exception as e:
            print(f"自治体情報の取得中にエラーが発生しました: {str(e)}")
            return []

    def get_stores(self, municipality_url):
        """自治体ページから店舗情報を取得"""
        try:
            # Seleniumでページを開く
            self.driver.get(municipality_url)
            
            # ページの読み込みを待つ
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)  # 追加の待機時間
            
            # 広告を消す
            self.dismiss_ad()
            
            # ページのHTMLを取得
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            stores = []
            # fr クラスを持つ div を取得
            fr_divs = soup.find_all('div', class_='fr')
            
            for div in fr_divs:
                try:
                    # 店舗名とURLを取得
                    link = div.find('a')
                    if not link:
                        continue
                    
                    store_name = link.text.strip()
                    store_url = self.base_url + link['href'].replace('./', '/')
                    
                    # 開店日を取得（隣接する fr div から）
                    next_div = div.find_next_sibling('div', class_='fr')
                    opening_date = next_div.text.strip() if next_div else ''
                    
                    stores.append({
                        'store_name': store_name,
                        'store_url': store_url,
                        'opening_date': opening_date
                    })
                except Exception as e:
                    print(f"店舗情報の解析中にエラーが発生しました: {str(e)}")
                    continue
            
            return stores
        except Exception as e:
            print(f"店舗情報の取得中にエラーが発生しました: {str(e)}")
            return []

    def __del__(self):
        """デストラクタ：ブラウザを閉じる"""
        try:
            self.driver.quit()
        except:
            pass

    def save_store_data(self, data, filename):
        """店舗データをCSVファイルに保存"""
        try:
            # 既存のファイルがある場合は読み込む
            if os.path.exists(filename):
                existing_df = pd.read_csv(filename, encoding='utf-8-sig')
                # 重複を避けるため、既存のデータと結合
                df = pd.concat([existing_df, pd.DataFrame([data])]).drop_duplicates(subset=['store_url'])
            else:
                df = pd.DataFrame([data])
            
            # CSVファイルとして保存
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"データの保存中にエラーが発生しました: {str(e)}")
            return False

    def scrape_prefecture(self, prefecture_url, prefecture_name):
        """都道府県の全データをスクレイピング"""
        # タイムスタンプ付きのファイル名を生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ajsm_data_{prefecture_name}_{timestamp}.csv"
        
        # 自治体情報を取得
        municipalities = self.get_municipalities(prefecture_url)
        total_municipalities = len(municipalities)
        
        for i, municipality in enumerate(municipalities, 1):
            print(f"処理中: {municipality['name']} ({i}/{total_municipalities})")
            
            try:
                # 店舗情報を取得
                stores = self.get_stores(municipality['url'])
                
                # 各店舗のデータを保存
                for store in stores:
                    data = {
                        'prefecture': prefecture_name,
                        'municipality': municipality['name'],
                        'store_name': store['store_name'],
                        'store_url': store['store_url'],
                        'opening_date': store['opening_date']
                    }
                    self.save_store_data(data, filename)
                
                # サーバー負荷軽減のための待機
                time.sleep(2)
            except Exception as e:
                print(f"自治体 {municipality['name']} の処理中にエラーが発生しました: {str(e)}")
                continue
        
        return filename

def scrape_ajsm_by_prefecture(prefecture_name):
    """都道府県名からスクレイピングを実行"""
    scraper = AjsmScraper()
    
    # 都道府県のURLを設定
    prefecture_urls = {
        "埼玉県": "https://ajsm.club/saitama.html",
        "千葉県": "https://ajsm.club/chiba.html",
       # "東京都": "https://ajsm.club/tokyo.html",
       # "神奈川県": "https://ajsm.club/kanagawa.html"
    }
    
    if prefecture_name not in prefecture_urls:
        raise ValueError(f"未対応の都道府県です: {prefecture_name}")
    
    return scraper.scrape_prefecture(prefecture_urls[prefecture_name], prefecture_name)