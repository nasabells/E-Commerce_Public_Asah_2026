from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="E-Commerce Dashboard", page_icon="🛍️", layout="wide")

DATA_PATH = Path(__file__).parent / "main_data.csv"
AKHIR_Q2 = pd.Timestamp("2018-08-31 23:59:59")  # data bulanan lengkap sampai Agustus 2018


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["order_purchase_timestamp"])
    df["bulan"] = df["order_purchase_timestamp"].dt.to_period("M").astype(str)
    return df


df = load_data()

# ---------- Sidebar ----------
st.sidebar.header("Filter")
tgl_min = df["order_purchase_timestamp"].min().date()
tgl_max = df["order_purchase_timestamp"].max().date()
rentang = st.sidebar.date_input("Rentang tanggal order", (tgl_min, tgl_max),
                                min_value=tgl_min, max_value=tgl_max)

if len(rentang) != 2:
    st.info("Pilih tanggal mulai dan tanggal akhir pada filter di sebelah kiri.")
    st.stop()

mulai, akhir = pd.Timestamp(rentang[0]), pd.Timestamp(rentang[1]) + pd.Timedelta(days=1)
data = df[(df["order_purchase_timestamp"] >= mulai) & (df["order_purchase_timestamp"] < akhir)]

if data.empty:
    st.warning("Tidak ada data pada rentang tanggal tersebut.")
    st.stop()

orders = data.drop_duplicates("order_id")  # satu baris per order

# ---------- Header & ringkasan ----------
st.title("🛍️ E-Commerce Public Dataset Dashboard")
st.caption("Order berstatus delivered, 2017-2018. Revenue dihitung dari harga item (tanpa ongkir), dalam R$.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Order", f"{orders['order_id'].nunique():,}")
c2.metric("Total Revenue", f"R$ {data['price'].sum():,.0f}")
c3.metric("Pelanggan Unik", f"{data['customer_unique_id'].nunique():,}")
c4.metric("Order Terlambat", f"{orders['terlambat'].mean() * 100:.2f}%")

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Kategori Produk", "2. Tren Bulanan", "3. Keterlambatan & Review", "4. Pelanggan per State"
])

# ---------- Pertanyaan 1 ----------
with tab1:
    st.subheader("Top 10 kategori berdasarkan revenue dan jumlah item terjual")
    kategori = (data.groupby("product_category_name_english")
                .agg(revenue=("price", "sum"), items_sold=("price", "count"))
                .reset_index()
                .rename(columns={"product_category_name_english": "kategori"}))
    top_rev = kategori.nlargest(10, "revenue")
    top_qty = kategori.nlargest(10, "items_sold")
    keduanya = set(top_rev["kategori"]) & set(top_qty["kategori"])

    label = lambda d: d.assign(
        posisi=d["kategori"].map(lambda k: "Top 10 di kedua metrik" if k in keduanya else "Hanya di satu metrik"))
    warna = {"Top 10 di kedua metrik": "#1f77b4", "Hanya di satu metrik": "#ff7f0e"}

    kiri, kanan = st.columns(2)
    with kiri:
        fig = px.bar(label(top_rev), x="revenue", y="kategori", color="posisi", orientation="h",
                     color_discrete_map=warna, title="Top 10 berdasarkan total revenue (R$)",
                     labels={"revenue": "Total revenue (R$)", "kategori": ""})
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, legend_title_text="")
        st.plotly_chart(fig, width="stretch")
    with kanan:
        fig = px.bar(label(top_qty), x="items_sold", y="kategori", color="posisi", orientation="h",
                     color_discrete_map=warna, title="Top 10 berdasarkan jumlah item terjual",
                     labels={"items_sold": "Jumlah item terjual", "kategori": ""})
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, legend_title_text="")
        st.plotly_chart(fig, width="stretch")

    st.write(f"**{len(keduanya)} kategori** masuk top 10 di kedua metrik. "
             f"Hanya di revenue: {', '.join(sorted(set(top_rev['kategori']) - keduanya)) or '-'}. "
             f"Hanya di jumlah item: {', '.join(sorted(set(top_qty['kategori']) - keduanya)) or '-'}.")

# ---------- Pertanyaan 2 ----------
with tab2:
    st.subheader("Tren order dan revenue per bulan (Januari 2017 - Agustus 2018)")
    bln = data[data["order_purchase_timestamp"] <= AKHIR_Q2]
    bulanan = (bln.groupby("bulan")
               .agg(jumlah_order=("order_id", "nunique"), total_revenue=("price", "sum"))
               .reset_index())

    if bulanan.empty:
        st.warning("Tidak ada data bulanan pada rentang tanggal tersebut.")
    else:
        for kolom, judul, sumbu in [("jumlah_order", "Jumlah order per bulan", "Jumlah order"),
                                    ("total_revenue", "Total revenue per bulan", "Total revenue (R$)")]:
            fig = px.line(bulanan, x="bulan", y=kolom, markers=True, title=judul,
                          labels={"bulan": "Bulan", kolom: sumbu})
            puncak = bulanan.loc[bulanan[kolom].idxmax()]
            fig.add_annotation(x=puncak["bulan"], y=puncak[kolom], text=f"Puncak: {puncak['bulan']}",
                               showarrow=True, arrowhead=2, ay=-40, font={"color": "red"})
            st.plotly_chart(fig, width="stretch")

        p_order = bulanan.loc[bulanan["jumlah_order"].idxmax()]
        p_rev = bulanan.loc[bulanan["total_revenue"].idxmax()]
        st.write(f"Order tertinggi: **{p_order['bulan']}** ({int(p_order['jumlah_order']):,} order). "
                 f"Revenue tertinggi: **{p_rev['bulan']}** (R$ {p_rev['total_revenue']:,.0f}).")

# ---------- Pertanyaan 3 ----------
with tab3:
    st.subheader("Keterlambatan pengiriman dan skor review")
    orders = orders.assign(status_kirim=orders["terlambat"].map({True: "Terlambat", False: "Tepat waktu"}))
    persen = orders["status_kirim"].value_counts(normalize=True).mul(100).reset_index()
    persen.columns = ["status_kirim", "persen"]
    rata = orders.groupby("status_kirim")["review_score"].mean().reset_index()

    kiri, kanan = st.columns(2)
    with kiri:
        fig = px.bar(persen, x="status_kirim", y="persen", color="status_kirim", text="persen",
                     title="Persentase order", labels={"status_kirim": "", "persen": "%"})
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(showlegend=False, yaxis_range=[0, 105])
        st.plotly_chart(fig, width="stretch")
    with kanan:
        fig = px.bar(rata, x="status_kirim", y="review_score", color="status_kirim", text="review_score",
                     title="Rata-rata skor review", labels={"status_kirim": "", "review_score": "Skor (1-5)"})
        fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig.update_layout(showlegend=False, yaxis_range=[0, 5])
        st.plotly_chart(fig, width="stretch")

    skor = rata.set_index("status_kirim")["review_score"]
    if {"Terlambat", "Tepat waktu"} <= set(skor.index):
        st.write(f"Selisih rata-rata skor (tepat waktu - terlambat): **{skor['Tepat waktu'] - skor['Terlambat']:.2f}** poin.")

# ---------- Pertanyaan 4 ----------
with tab4:
    st.subheader("Pelanggan unik per state")
    state = (data.groupby("customer_state")
             .agg(pelanggan_unik=("customer_unique_id", "nunique"), jumlah_order=("order_id", "nunique"))
             .sort_values("pelanggan_unik", ascending=False)
             .reset_index())
    top5 = state.head(5)
    kontribusi = top5["jumlah_order"].sum() / state["jumlah_order"].sum() * 100

    st.metric("Kontribusi 5 state teratas terhadap total order", f"{kontribusi:.2f}%")

    top10 = state.head(10).assign(
        kelompok=["5 teratas"] * min(5, len(state)) + ["Lainnya"] * max(0, min(10, len(state)) - 5))
    fig = px.bar(top10, x="customer_state", y="pelanggan_unik", color="kelompok",
                 color_discrete_map={"5 teratas": "#1f77b4", "Lainnya": "#c7c7c7"},
                 title="Top 10 state berdasarkan pelanggan unik",
                 labels={"customer_state": "State", "pelanggan_unik": "Pelanggan unik"})
    fig.update_layout(legend_title_text="")
    st.plotly_chart(fig, width="stretch")
    st.dataframe(state.head(10), width="stretch", hide_index=True)