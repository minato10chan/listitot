from ajsm_scraper import AjsmScraper

def test_scrape_limited_stores():
    scraper = AjsmScraper()
    
    # テスト対象の都道府県
    prefectures = ["埼玉県", "千葉県", "東京都", "神奈川県"]
    
    for prefecture in prefectures:
        print(f"\n=== {prefecture}の店舗情報を取得中 ===")
        
        # 都道府県のURLを設定
        prefecture_urls = {
            "埼玉県": "https://ajsm.club/saitama.html",
            "千葉県": "https://ajsm.club/chiba.html",
          #  "東京都": "https://ajsm.club/tokyo.html",
          #  "神奈川県": "https://ajsm.club/kanagawa.html"
        }
        
        try:
            # 自治体情報を取得
            municipalities = scraper.get_municipalities(prefecture_urls[prefecture])
            print(f"自治体数: {len(municipalities)}")
            
            # 最初の自治体から店舗情報を取得（最大5件）
            if municipalities:
                stores = scraper.get_stores(municipalities[0]['url'])
                print(f"取得した店舗数: {len(stores)}")
                
                # 最初の5件のみ表示
                for i, store in enumerate(stores[:5], 1):
                    print(f"\n店舗 {i}:")
                    print(f"店舗名: {store['store_name']}")
                    print(f"URL: {store['store_url']}")
                    print(f"開店日: {store['opening_date']}")
            
        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")
        
        print("\n" + "="*50)

if __name__ == "__main__":
    test_scrape_limited_stores() 