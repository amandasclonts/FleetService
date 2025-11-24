import streamlit as st
import pandas as pd

st.set_page_config(page_title="Fleet Service Dashboard", layout="wide")
st.title("🚚 Fleet Service Dashboard")

uploaded = st.file_uploader("Upload Fleetio Excel File", type=["xlsx"])

if not uploaded:
    st.info("Upload your Fleetio service history Excel file to begin.")
else:
    # ---- Load & prep data ----
    df = pd.read_excel(uploaded)
    df.columns = df.columns.str.strip()

    # Ensure needed columns exist
    required_cols = [
        "Vehicle Name",
        "Completed At",
        "Meter",
        "Service Tasks",
        "Vendor Name",
        "Total Cost (USD)",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"Missing columns in file: {', '.join(missing)}")
        st.stop()

    # Sort for "previous service" calcs
    df = df.sort_values(["Vehicle Name", "Service Tasks", "Completed At"])

    # Miles between same service for same vehicle
    df["Miles Between Service"] = (
        df.groupby(["Vehicle Name", "Service Tasks"])["Meter"].diff()
    )

    # Basic derived data
    vendor_cost = (
        df.groupby("Vendor Name")["Total Cost (USD)"]
        .sum()
        .reset_index()
        .sort_values("Total Cost (USD)", ascending=False)
    )

    vendor_vehicle_miles = (
        df.groupby(["Vendor Name", "Vehicle Name"])["Miles Between Service"]
        .mean()
        .reset_index()
        .sort_values(["Vendor Name", "Vehicle Name"])
    )

    service_freq = (
        df.groupby(["Vehicle Name", "Service Tasks"])
        .size()
        .reset_index(name="Service Count")
        .sort_values(["Vehicle Name", "Service Count"], ascending=[True, False])
    )

    # High-level KPIs
    total_spend = float(df["Total Cost (USD)"].sum())
    num_vendors = df["Vendor Name"].nunique()
    num_vehicles = df["Vehicle Name"].nunique()
    num_services = len(df)

    # ---- TABS ----
    tab_overview, tab_cost, tab_freq, tab_raw = st.tabs(
        ["📊 Overview", "💰 Total Cost per Vendor", "🔁 Service Frequency", "📄 Raw Data"]
    )

    # ---------- OVERVIEW TAB ----------
    with tab_overview:
        st.subheader("Overall Metrics")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Spend (USD)", f"${total_spend:,.0f}")
        col2.metric("Vendors Used", num_vendors)
        col3.metric("Vehicles Serviced", num_vehicles)
        col4.metric("Service Records", num_services)

        st.markdown("### Average Miles Between Services by Vehicle")

        miles_by_vehicle = (
            df.groupby("Vehicle Name")["Miles Between Service"]
            .mean()
            .reset_index()
            .sort_values("Miles Between Service", ascending=False)
        )

        st.dataframe(miles_by_vehicle, use_container_width=True)

        # Bar chart of average miles between services per vehicle
        chart_data = miles_by_vehicle.set_index("Vehicle Name")["Miles Between Service"]
        st.bar_chart(chart_data)

    # ---------- COST BY VENDOR TAB ----------
    with tab_cost:
        st.subheader("Total Cost per Vendor")

        st.dataframe(vendor_cost, use_container_width=True)

        # Bar chart: vendor cost
        cost_chart = vendor_cost.set_index("Vendor Name")["Total Cost (USD)"]
        st.bar_chart(cost_chart)

        st.markdown("### Average Miles Between Services by Vendor & Vehicle")
        st.da
