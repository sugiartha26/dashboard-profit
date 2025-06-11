import streamlit as st
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(layout="wide")
st.title("📊 Dashboard Profit Penjualan Handphone")

# ==============================
# UPLOAD FILE EXCEL
# ==============================
uploaded_file = st.file_uploader("Unggah file Excel", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    # Cek apakah kolom yang dibutuhkan ada
    required_columns = {'Nama_Kota', 'Handphone', 'Tanggal', 'Profit'}
    if not required_columns.issubset(df.columns):
        st.error(f"File harus memiliki kolom: {', '.join(required_columns)}")
    else:
        # ==============================
        # PREPROCESSING
        # ==============================
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
        df['Tahun'] = df['Tanggal'].dt.year
        df['Bulan'] = df['Tanggal'].dt.strftime('%B')
        df['Bulan_Num'] = df['Tanggal'].dt.month

        # ==============================
        # FILTERS
        # ==============================
        st.sidebar.header("🔍 Filter Data")

        selected_years = st.sidebar.multiselect(
            "Pilih Tahun",
            options=sorted(df['Tahun'].dropna().unique()),
            default=sorted(df['Tahun'].dropna().unique())
        )

        selected_cities = st.sidebar.multiselect(
            "Pilih Nama Kota",
            options=sorted(df['Nama_Kota'].unique()),
            default=sorted(df['Nama_Kota'].unique())
        )

        selected_phones = st.sidebar.multiselect(
            "Pilih Handphone",
            options=sorted(df['Handphone'].unique()),
            default=sorted(df['Handphone'].unique())
        )

        # ==============================
        # FILTERED DATA
        # ==============================
        filtered_df = df[
            (df['Tahun'].isin(selected_years)) &
            (df['Nama_Kota'].isin(selected_cities)) &
            (df['Handphone'].isin(selected_phones))
        ]

        tab1, tab2 = st.tabs(["📈 Visualisasi", "🧠 Data Understanding"])

        # ==============================
        # TAB VISUALISASI
        # ==============================
        with tab1:
            st.subheader("📱 Profit per Handphone")
            profit_per_hp = filtered_df.groupby('Handphone')['Profit'].sum().sort_values(ascending=False).reset_index()
            st.dataframe(profit_per_hp.style.format({"Profit": "Rp {:,.0f}"}), use_container_width=True)

            st.subheader("📈 Profit Bulanan")
            profit_per_month = (
                filtered_df.groupby(['Bulan_Num', 'Bulan'])['Profit'].sum().reset_index().sort_values('Bulan_Num')
            )
            line_chart = alt.Chart(profit_per_month).mark_line(point=True).encode(
                x=alt.X('Bulan', sort=list(profit_per_month['Bulan'])),
                y='Profit',
                tooltip=['Bulan', 'Profit']
            ).properties(width=700, height=400)
            st.altair_chart(line_chart, use_container_width=True)

            st.subheader("🥧 Profit per Kota")
            profit_per_kota = filtered_df.groupby('Nama_Kota')['Profit'].sum()
            fig, ax = plt.subplots()
            ax.pie(profit_per_kota, labels=profit_per_kota.index, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            st.pyplot(fig)

            st.subheader("📊 Profit per Tahun")
            profit_per_tahun = filtered_df.groupby('Tahun')['Profit'].sum().reset_index()
            bar_chart = alt.Chart(profit_per_tahun).mark_bar().encode(
                x='Tahun:O',
                y='Profit:Q',
                tooltip=['Tahun', 'Profit']
            ).properties(width=500, height=400)
            st.altair_chart(bar_chart, use_container_width=True)

        # ==============================
        # TAB DATA UNDERSTANDING
        # ==============================
        with tab2:
            st.subheader("📌 Tipe Data")
            st.dataframe(df.dtypes.rename("Tipe Data"))

            st.subheader("📊 Statistik Deskriptif")
            st.dataframe(df.describe(include='all'))

            st.subheader("🧩 Missing Values")
            missing = df.isnull().sum()
            missing_cols = missing[missing > 0]
            st.dataframe(missing_cols.rename("Jumlah Missing"))

            if not missing_cols.empty:
                st.write("🔍 **Baris dengan Missing Values:**")
                st.dataframe(df[df.isnull().any(axis=1)])

            st.subheader("📑 Duplikasi Data")
            duplikat_count = df.duplicated().sum()
            st.write(f"Jumlah baris duplikat: **{duplikat_count}**")

            if duplikat_count > 0:
                st.write("🔍 **Baris Duplikat:**")
                st.dataframe(df[df.duplicated(keep=False)])

            st.subheader("📈 Korelasi (Numerik)")
            numeric_df = df.select_dtypes(include=['int64', 'float64'])
            if not numeric_df.empty:
                corr = numeric_df.corr()
                fig, ax = plt.subplots()
                sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
                st.pyplot(fig)
            else:
                st.info("Tidak ada kolom numerik untuk dihitung korelasi.")

            st.subheader("🚨 Outlier Deteksi (menggunakan IQR)")

            outlier_report = []
            all_outliers = pd.DataFrame()

            for col in numeric_df.columns:
                Q1 = numeric_df[col].quantile(0.25)
                Q3 = numeric_df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                outliers = df[(numeric_df[col] < lower) | (numeric_df[col] > upper)]
                if not outliers.empty:
                    outliers['Outlier_Col'] = col  # untuk pelabelan
                    all_outliers = pd.concat([all_outliers, outliers])
                outlier_report.append({
                    'Kolom': col,
                    'Jumlah Outlier': len(outliers),
                    'Persentase (%)': round(100 * len(outliers) / len(df), 2)
                })

            outlier_df = pd.DataFrame(outlier_report)
            st.dataframe(outlier_df)

            if not all_outliers.empty:
                st.write("🔍 **Baris yang mengandung Outlier:**")
                st.dataframe(all_outliers.drop_duplicates())

                st.write("📦 **Visualisasi Boxplot untuk Kolom yang Memiliki Outlier:**")
                for col in outlier_df[outlier_df['Jumlah Outlier'] > 0]['Kolom']:
                    fig, ax = plt.subplots()
                    sns.boxplot(x=df[col], ax=ax)
                    ax.set_title(f'Boxplot - {col}')
                    st.pyplot(fig)

else:
    st.info("Silakan unggah file Excel untuk memulai visualisasi dan analisis.")
