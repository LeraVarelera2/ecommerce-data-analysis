
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# =====================================================
# 1. KONFIGURASI HALAMAN
# =====================================================

st.set_page_config(
    page_title="E-Commerce Data Analysis",
    page_icon="",
    layout="wide"
)

DATA_DIR = Path(__file__).parent / "data"


# =====================================================
# 2. MEMUAT DATA
# =====================================================

@st.cache_data
def load_data():
    sales_detail = pd.read_csv(DATA_DIR / "sales_detail.csv")
    delivery_detail = pd.read_csv(DATA_DIR / "delivery_detail.csv")

    sales_detail["order_purchase_timestamp"] = pd.to_datetime(
        sales_detail["order_purchase_timestamp"]
    )

    delivery_detail["order_purchase_timestamp"] = pd.to_datetime(
        delivery_detail["order_purchase_timestamp"]
    )

    # Memastikan status keterlambatan berbentuk boolean
    if delivery_detail["is_late"].dtype != bool:
        delivery_detail["is_late"] = (
            delivery_detail["is_late"]
            .astype(str)
            .str.lower()
            .map({"true": True, "false": False})
        )

    return sales_detail, delivery_detail


sales_detail, delivery_detail = load_data()


# =====================================================
# 3. FILTER RENTANG TANGGAL
# =====================================================

st.title("E-Commerce Data Analysis Dashboard")

st.caption(
    "Analisis penjualan produk, ketepatan pengiriman, "
    "dan segmentasi pelanggan"
)

st.divider()

st.sidebar.title("Filter Dashboard")

all_dates = pd.concat([
    sales_detail["order_purchase_timestamp"],
    delivery_detail["order_purchase_timestamp"]
])

min_date = all_dates.min().date()
max_date = all_dates.max().date()

selected_dates = st.sidebar.date_input(
    "Pilih Rentang Tanggal Pembelian",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    st.info("Silakan pilih tanggal awal dan tanggal akhir.")
    st.stop()

if start_date > end_date:
    st.warning("Tanggal awal tidak boleh melebihi tanggal akhir.")
    st.stop()

st.sidebar.caption(
    "Rentang tanggal ini memengaruhi seluruh KPI, grafik penjualan, "
    "pengiriman, kategori produk, dan segmentasi pelanggan."
)

start_timestamp = pd.Timestamp(start_date)
end_timestamp = pd.Timestamp(end_date) + pd.Timedelta(days=1)

filtered_sales = sales_detail[
    (sales_detail["order_purchase_timestamp"] >= start_timestamp) &
    (sales_detail["order_purchase_timestamp"] < end_timestamp)
].copy()

filtered_delivery = delivery_detail[
    (delivery_detail["order_purchase_timestamp"] >= start_timestamp) &
    (delivery_detail["order_purchase_timestamp"] < end_timestamp)
].copy()


# =====================================================
# 4. MENGHITUNG DATA PENJUALAN
# =====================================================

filtered_sales["order_month"] = (
    filtered_sales["order_purchase_timestamp"].dt.to_period("M").dt.to_timestamp()
)

monthly_sales = (
    filtered_sales.groupby(
        ["order_month", "product_category_name_english"]
    )["price"]
    .sum()
    .reset_index()
)

category_sales = (
    filtered_sales.groupby("product_category_name_english")["price"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)


# =====================================================
# 5. MENGHITUNG DATA PENGIRIMAN
# =====================================================

filtered_delivery["order_month"] = (
    filtered_delivery["order_purchase_timestamp"].dt.to_period("M").dt.to_timestamp()
)

monthly_delivery = (
    filtered_delivery.groupby("order_month")
    .agg(
        total_orders=("order_id", "nunique"),
        late_orders=("is_late", "sum")
    )
    .reset_index()
)

monthly_delivery["late_percentage"] = (
    monthly_delivery["late_orders"] /
    monthly_delivery["total_orders"] * 100
)


# =====================================================
# 6. MENGHITUNG ANALISIS RFM
# =====================================================

# Menghitung total nilai pembelian setiap pesanan
order_revenue = (
    filtered_sales.groupby("order_id")["price"]
    .sum()
    .reset_index()
    .rename(columns={"price": "monetary"})
)

# Menghubungkan transaksi dengan identitas pelanggan
rfm_data = filtered_delivery[
    [
        "order_id",
        "customer_unique_id",
        "order_purchase_timestamp"
    ]
].merge(
    order_revenue,
    on="order_id",
    how="inner"
)

if not rfm_data.empty:

    # Tanggal acuan mengikuti akhir periode filter
    snapshot_date = pd.Timestamp(end_date) + pd.Timedelta(days=1)

    rfm_df = (
        rfm_data.groupby("customer_unique_id")
        .agg(
            recency=(
                "order_purchase_timestamp",
                lambda x: (snapshot_date - x.max()).days
            ),
            frequency=("order_id", "nunique"),
            monetary=("monetary", "sum")
        )
        .reset_index()
    )

    # Menggunakan metode pemberian skor yang sama dengan notebook
    if len(rfm_df) >= 4:

        rfm_df["R_score"] = pd.qcut(
            rfm_df["recency"].rank(method="first"),
            4,
            labels=[4, 3, 2, 1]
        ).astype(int)

        rfm_df["M_score"] = pd.qcut(
            rfm_df["monetary"].rank(method="first"),
            4,
            labels=[1, 2, 3, 4]
        ).astype(int)

        rfm_df["F_score"] = pd.cut(
            rfm_df["frequency"],
            bins=[0, 1, 2, 3, float("inf")],
            labels=[1, 2, 3, 4]
        ).astype(int)

        # Segmentasi pelanggan mengikuti notebook
        def segment_customer(row):
            if (
                row["R_score"] >= 3
                and row["F_score"] >= 3
                and row["M_score"] >= 3
            ):
                return "Champions"

            elif row["F_score"] >= 3 and row["R_score"] >= 2:
                return "Loyal Customers"

            elif row["R_score"] >= 3 and row["F_score"] <= 2:
                return "Potential Loyalists"

            elif row["R_score"] <= 2:
                return "At Risk"

            else:
                return "Others"

        rfm_df["customer_segment"] = rfm_df.apply(
            segment_customer,
            axis=1
        )

        segment_summary = (
            rfm_df["customer_segment"]
            .value_counts()
            .reset_index()
        )

        segment_summary.columns = [
            "customer_segment",
            "total_customers"
        ]

    else:
        segment_summary = pd.DataFrame(
            columns=["customer_segment", "total_customers"]
        )

else:
    segment_summary = pd.DataFrame(
        columns=["customer_segment", "total_customers"]
    )


# =====================================================
# 7. KPI DASHBOARD
# =====================================================

total_sales = filtered_sales["price"].sum()

total_orders = filtered_delivery["order_id"].nunique()

average_late = (
    monthly_delivery["late_percentage"].mean()
    if not monthly_delivery.empty
    else 0
)

col1, col2, col3 = st.columns(3)

col1.metric(
    "Total Nilai Penjualan",
    f"R$ {total_sales:,.2f}"
)

col2.metric(
    "Pesanan Terkirim Dianalisis",
    f"{total_orders:,.0f}"
)

col3.metric(
    "Rata-rata Keterlambatan Bulanan",
    f"{average_late:.2f}%"
)

st.caption(
    f"Periode analisis: {start_date.strftime('%d %b %Y')} "
    f"- {end_date.strftime('%d %b %Y')}"
)

st.divider()


# =====================================================
# 8. ANALISIS PENJUALAN PRODUK
# =====================================================

st.header("1. Analisis Penjualan Produk")

if not category_sales.empty:

    top5_categories = (
        category_sales.nlargest(5, "price")
        ["product_category_name_english"]
        .tolist()
    )

    chart_data = monthly_sales[
        monthly_sales["product_category_name_english"].isin(
            top5_categories
        )
    ]

    sales_chart = px.line(
        chart_data,
        x="order_month",
        y="price",
        color="product_category_name_english",
        markers=True,
        title="Tren Nilai Penjualan 5 Kategori Teratas",
        labels={
            "order_month": "Bulan Pembelian",
            "price": "Nilai Penjualan (R$)",
            "product_category_name_english": "Kategori Produk"
        }
    )

    sales_chart.update_layout(
        template="plotly_white",
        height=480,
        hovermode="x unified",
        legend_title_text="Kategori Produk"
    )

    st.plotly_chart(
        sales_chart,
        use_container_width=True
    )

    # Top 10 kategori berdasarkan periode terpilih
    top_categories = (
        category_sales.nlargest(10, "price")
        .sort_values("price")
        .copy()
    )

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
        title="10 Kategori Produk dengan Penjualan Tertinggi",
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
        xaxis_range=[
            0,
            top_categories["price"].max() * 1.15
        ]
    )

    st.plotly_chart(
        category_chart,
        use_container_width=True
    )

else:
    st.info("Tidak ada data penjualan pada periode yang dipilih.")


st.divider()


# =====================================================
# 9. ANALISIS KETERLAMBATAN PENGIRIMAN
# =====================================================

st.header("2. Analisis Keterlambatan Pengiriman")

if not monthly_delivery.empty:

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
        marker=dict(size=8)
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

    st.plotly_chart(
        delivery_chart,
        use_container_width=True
    )

else:
    st.info("Tidak ada data pengiriman pada periode yang dipilih.")


# =====================================================
# 10. ANALISIS SEGMENTASI PELANGGAN RFM
# =====================================================

st.divider()

st.header("3. Analisis Segmentasi Pelanggan (RFM)")

if not segment_summary.empty:

    rfm_chart = px.bar(
        segment_summary.sort_values(
            "total_customers",
            ascending=True
        ),
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

    st.plotly_chart(
        rfm_chart,
        use_container_width=True
    )

else:
    st.info(
        "Data pelanggan belum mencukupi untuk perhitungan "
        "segmentasi RFM pada periode ini."
    )


# =====================================================
# 11. CATATAN ANALISIS
# =====================================================

st.divider()

st.caption(
    "Catatan: Nilai penjualan menggunakan harga produk (price), "
    "tidak termasuk biaya pengiriman. Analisis pengiriman menggunakan "
    "pesanan terkirim yang memiliki tanggal aktual dan estimasi pengiriman. "
    "Segmentasi RFM dihitung berdasarkan transaksi pada rentang tanggal "
    "yang dipilih."
)
