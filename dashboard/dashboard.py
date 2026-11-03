
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# Konfigurasi halaman
st.set_page_config(
    page_title="E-Commerce Data Analysis",
    page_icon="",
    layout="wide"
)

# Lokasi data
DATA_DIR = Path(__file__).parent / "data"

# Memuat dataset
@st.cache_data
def load_data():
    monthly_sales = pd.read_csv(DATA_DIR / "monthly_sales.csv")
    category_sales = pd.read_csv(DATA_DIR / "category_sales.csv")
    monthly_delivery = pd.read_csv(DATA_DIR / "monthly_delivery.csv")
    segment_summary = pd.read_csv(DATA_DIR / "segment_summary.csv")

    monthly_sales["order_month"] = pd.to_datetime(monthly_sales["order_month"])
    monthly_delivery["order_month"] = pd.to_datetime(monthly_delivery["order_month"])

    return monthly_sales, category_sales, monthly_delivery, segment_summary


monthly_sales, category_sales, monthly_delivery, segment_summary = load_data()

# Judul dashboard
st.title("E-Commerce Data Analysis Dashboard")
st.caption("Analisis penjualan produk, ketepatan pengiriman, dan segmentasi pelanggan")
st.divider()

# Sidebar
st.sidebar.title("Filter Dashboard")

categories = sorted(
    monthly_sales["product_category_name_english"].dropna().unique()
)


selected_category = st.sidebar.selectbox(
    "Pilih Kategori Produk",
    ["Semua Kategori"] + categories,
    format_func=lambda x: x.replace("_", " ").title()
)

st.sidebar.caption(
    "Filter kategori memengaruhi nilai penjualan dan grafik tren. "
    "Analisis pengiriman, 10 kategori teratas, dan RFM menggunakan keseluruhan data."
)


# Filter penjualan
if selected_category == "Semua Kategori":
    filtered_sales = monthly_sales.copy()
else:
    filtered_sales = monthly_sales[
        monthly_sales["product_category_name_english"] == selected_category
    ]


# KPI
total_sales = filtered_sales["price"].sum()
total_orders = monthly_delivery["total_orders"].sum()
average_late = monthly_delivery["late_percentage"].mean()


col1, col2, col3 = st.columns(3)

col1.metric(
    "Total Nilai Penjualan",
    f"R$ {total_sales:,.2f}"
)

col2.metric(
    "Pesanan Dianalisis",
    f"{total_orders:,.0f}"
)

col3.metric(
    "Rata-rata Keterlambatan Bulanan",
    f"{average_late:.2f}%"
)

st.divider()


# Analisis Penjualan
st.header("1. Analisis Penjualan Produk")

if selected_category == "Semua Kategori":
    top5_categories = category_sales.nlargest(
        5, "price"
    )["product_category_name_english"].tolist()

    chart_data = filtered_sales[
        filtered_sales["product_category_name_english"].isin(top5_categories)
    ]
else:
    chart_data = filtered_sales

if not chart_data.empty:
    sales_chart = px.line(
        chart_data,
        x="order_month",
        y="price",
        color="product_category_name_english",
        markers=True,
        title=(
            "Tren Nilai Penjualan 5 Kategori Teratas"
            if selected_category == "Semua Kategori"
            else f"Tren Nilai Penjualan Kategori {selected_category.replace('_', ' ').title()}"
        ),
        
        labels={
            "order_month": "Bulan Pembelian",
            "price": "Nilai Penjualan (R$)",
            "product_category_name_english": "Kategori Produk"
        }
    )

    sales_chart.update_layout(
        legend_title_text="Kategori Produk",
        hovermode="x unified",
        template="plotly_white",
        height=480
    )

    st.plotly_chart(sales_chart, use_container_width=True)
else:
    st.info("Tidak ada data penjualan untuk kategori ini.")



# Top 10 kategori
top_categories = category_sales.nlargest(10, "price").sort_values("price").copy()

top_categories["category_label"] = (
    top_categories["product_category_name_english"]
    .str.replace("_", " ", regex=False)
    .str.title()
)

category_chart = px.bar(
    top_categories,
    x="price",
    y="category_label",
    orientation="h",
    title="10 Kategori Teratas (Keseluruhan Data)",
    labels={
        "price": "Nilai Penjualan (R$)",
        "category_label": "Kategori Produk"
    },
    text="price"
)

category_chart.update_traces(
    texttemplate="R$ %{x:,.0f}",
    textposition="outside"
)

category_chart.update_layout(
    template="plotly_white",
    height=500,
    xaxis_title="Nilai Penjualan (R$)",
    yaxis_title="Kategori Produk",
    xaxis_range=[0, top_categories["price"].max() * 1.15]
)

st.plotly_chart(category_chart, use_container_width=True)


st.divider()


# Analisis Pengiriman
st.header("2. Analisis Keterlambatan Pengiriman")

delivery_chart = px.line(
    monthly_delivery,
    x="order_month",
    y="late_percentage",
    markers=True,
    title="Tren Persentase Keterlambatan Pengiriman",
    labels={
        "order_month": "Bulan Pembelian",
        "late_percentage": "Keterlambatan (%)"
    },
    hover_data={
        "total_orders": True,
        "late_orders": True
    }
)

delivery_chart.update_traces(
    line=dict(width=3),
    marker=dict(size=8),
    hovertemplate=(
        "Bulan: %{x|%B %Y}<br>"
        "Keterlambatan: %{y:.2f}%<br>"
        "Total Pesanan: %{customdata[0]:,.0f}<br>"
        "Pesanan Terlambat: %{customdata[1]:,.0f}"
        "<extra></extra>"
    )
)

delivery_chart.update_layout(
    template="plotly_white",
    height=450,
    hovermode="x unified",
    yaxis_title="Keterlambatan (%)",
    xaxis_title="Bulan Pembelian",
    yaxis_ticksuffix="%",
    showlegend=False
)

st.plotly_chart(delivery_chart, use_container_width=True)


# Analisis RFM
st.divider()
st.header("3. Analisis Segmentasi Pelanggan (RFM)")

rfm_chart = px.bar(
    segment_summary.sort_values("total_customers", ascending=True),
    x="total_customers",
    y="customer_segment",
    orientation="h",
    title="Jumlah Pelanggan Berdasarkan Segmen",
    labels={
        "total_customers": "Jumlah Pelanggan",
        "customer_segment": "Segmen Pelanggan"
    },
    text="total_customers"
)

rfm_chart.update_traces(
    texttemplate="%{x:,.0f}",
    textposition="outside"
)

rfm_chart.update_layout(
    template="plotly_white",
    height=450,
    xaxis_title="Jumlah Pelanggan",
    yaxis_title="Segmen Pelanggan",
    showlegend=False
)

st.plotly_chart(rfm_chart, use_container_width=True)

st.caption(
    "Catatan: Nilai penjualan menggunakan harga produk (price), "
    "tidak termasuk biaya pengiriman. Persentase keterlambatan dihitung "
    "dari pesanan terkirim yang memiliki tanggal aktual dan estimasi pengiriman."
)
