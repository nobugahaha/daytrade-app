import streamlit as st
import pandas as pd

# ページの設定（画面を広く使う）
st.set_page_config(page_title="デイトレ分析アプリ", layout="wide")

st.title("📈 デイトレード分析ダッシュボード")
st.write("毎日の取引データ（CSV）をアップロードしてください。複数のファイルをまとめて入れると、日別の表が自動で作成されます！")

# 1. ファイルのアップロード機能
uploaded_files = st.file_uploader("CSVデータをドラッグ＆ドロップ", type="csv", accept_multiple_files=True)

if uploaded_files:
    df_list = []
    for file in uploaded_files:
        try:
            file.seek(0) # エラー対策：ファイルの先頭に戻す
            temp_df = pd.read_csv(file, encoding="shift_jis")
        except:
            file.seek(0) # エラー対策：ファイルの先頭に戻す
            temp_df = pd.read_csv(file, encoding="utf-8")
        df_list.append(temp_df)
    
    # 複数ファイルのデータを合体させる
    df = pd.concat(df_list, ignore_index=True)
    
    # 金額のカンマや＋記号を消して数値に変換
    df['実現損益(円)'] = df['実現損益(円)'].astype(str).str.replace(',', '').str.replace('+', '').astype(float)
    df['約定日'] = pd.to_datetime(df['約定日'])
    
    # --- 2. 日ごとの集計処理 ---
    daily_stats = []
    cum_pnl = 0
    max_cum_pnl = 0

    # 日付の古い順に並び替えて、日ごとにグループ化して計算
    for date, group in df.sort_values('約定日').groupby(df['約定日'].dt.date):
        trades = group['実現損益(円)']
        win_trades = trades[trades > 0]
        lose_trades = trades[trades <= 0]
        
        # 1日のトータル損益
        total_pnl = trades.sum()
        
        # 累計損益と最大ドローダウンの計算
        cum_pnl += total_pnl
        max_cum_pnl = max(max_cum_pnl, cum_pnl)
        drawdown = max_cum_pnl - cum_pnl
        
        avg_profit = win_trades.mean() if len(win_trades) > 0 else 0
        avg_loss = lose_trades.mean() if len(lose_trades) > 0 else 0
        
        # 画像と同じ順番で列を作成
        daily_stats.append({
            '日付': date.strftime('%Y/%m/%d'),
            '取引回数': len(trades),
            'トータル損益': int(total_pnl),
            '勝率': f"{len(win_trades) / len(trades) * 100:.1f}%" if len(trades) > 0 else "0.0%",
            '平均利益': int(avg_profit),
            '平均損失': int(avg_loss),
            '最大利益': int(trades.max()) if len(trades) > 0 else 0,
            '最大損失': int(trades.min()) if len(trades) > 0 else 0,
            'リスクリワード': round(abs(avg_profit / avg_loss), 2) if avg_loss != 0 else 0.0,
            '累計損益': int(cum_pnl),
            '最大ドローダウン': int(drawdown),
            'プロフィットファクター': round(win_trades.sum() / abs(lose_trades.sum()), 2) if lose_trades.sum() != 0 else 0.0
        })

    # 集計したデータを表（データフレーム）に変換
    summary_df = pd.DataFrame(daily_stats)

    # --- 3. アプリ画面への表示 ---
    st.subheader("📋 デイトレード結果まとめ表")
    
    # 表を表示（行番号を隠し、画面幅いっぱいに表示）
    st.dataframe(summary_df, hide_index=True, use_container_width=True)

    st.divider()

    st.subheader("📈 累計損益グラフ")
    # グラフ描画用に日付データをセットして折れ線グラフを表示
    chart_data = summary_df.set_index('日付')[['累計損益']]
    st.line_chart(chart_data)