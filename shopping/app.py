import streamlit as st
import pandas as pd
from ajsm_scraper import AjsmScraper
import time
from datetime import datetime

def main():
    st.title("スーパーマーケット店舗情報検索")
    st.write("都道府県を選択して、店舗情報を表示します。")

    # 都道府県の選択
    prefecture = st.selectbox(
        "都道府県を選択してください",
        ["埼玉県", "千葉県", "東京都", "神奈川県"]
    )

    # 都道府県のURLを設定
    prefecture_urls = {
        "埼玉県": "https://ajsm.club/saitama.html",
        "千葉県": "https://ajsm.club/chiba.html",
        "東京都": "https://ajsm.club/tokyo.html",
        "神奈川県": "https://ajsm.club/kanagawa.html"
    }

    if st.button("店舗情報を取得"):
        with st.spinner("データを取得中..."):
            try:
                # スクレイパーの初期化
                scraper = AjsmScraper()
                
                # 自治体情報を取得
                municipalities = scraper.get_municipalities(prefecture_urls[prefecture])
                
                if not municipalities:
                    st.error("自治体情報の取得に失敗しました。")
                    return
                
                st.success(f"{len(municipalities)}件の自治体を取得しました。")
                
                # 全店舗情報を格納するリスト
                all_stores = []
                
                # プログレスバーの設定
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 各自治体の店舗情報を取得
                for i, municipality in enumerate(municipalities):
                    status_text.text(f"処理中: {municipality['name']} ({i+1}/{len(municipalities)})")
                    
                    try:
                        # 店舗情報を取得
                        stores = scraper.get_stores(municipality['url'])
                        
                        # 店舗情報に自治体情報を追加
                        for store in stores:
                            store['prefecture'] = prefecture
                            store['municipality'] = municipality['name']
                            all_stores.append(store)
                        
                        # プログレスバーを更新
                        progress_bar.progress((i + 1) / len(municipalities))
                        
                        # サーバー負荷軽減のための待機
                        time.sleep(1)
                        
                    except Exception as e:
                        st.warning(f"{municipality['name']}の処理中にエラーが発生しました: {str(e)}")
                        continue
                
                if all_stores:
                    # データフレームの作成
                    df = pd.DataFrame(all_stores)
                    
                    # 表示する列の選択
                    columns_to_show = st.multiselect(
                        "表示する情報を選択してください",
                        ['prefecture', 'municipality', 'store_name', 'store_url', 'opening_date'],
                        default=['prefecture', 'municipality', 'store_name', 'opening_date']
                    )
                    
                    # データフレームの表示
                    st.dataframe(df[columns_to_show])
                    
                    # 統計情報の表示
                    st.subheader("統計情報")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("総店舗数", len(df))
                    with col2:
                        st.metric("自治体数", len(df['municipality'].unique()))
                    with col3:
                        st.metric("平均店舗数/自治体", round(len(df) / len(df['municipality'].unique()), 1))
                    
                    # CSVダウンロードボタン
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    csv = df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        "CSVファイルをダウンロード",
                        csv,
                        f"stores_{prefecture}_{timestamp}.csv",
                        "text/csv"
                    )
                else:
                    st.warning("店舗情報が見つかりませんでした。")
                
            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")
            finally:
                # スクレイパーのクリーンアップ
                try:
                    scraper.driver.quit()
                except:
                    pass

if __name__ == "__main__":
    main() 