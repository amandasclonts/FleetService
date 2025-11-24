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

# 🔹 Remove exact duplicate service rows so they don't skew totals
    df = df.drop_duplicates(
        subset=[
            "Vehicle Name",
            "Completed At",
            "Meter",
            "Service Tasks",
            "Vendor Name",
            "Total Cost (USD)",
        ]
    )

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
        st.dataframe(vendor_vehicle_miles, use_container_width=True)

    # ---------- SERVICE FREQUENCY TAB ----------
    with tab_freq:
        st.subheader("Service Frequency")

        # Optional filters
        vehicles = ["All"] + sorted(service_freq["Vehicle Name"].unique().tolist())
        services = ["All"] + sorted(service_freq["Service Tasks"].unique().tolist())

        c1, c2 = st.columns(2)
        selected_vehicle = c1.selectbox("Filter by Vehicle", vehicles)
        selected_service = c2.selectbox("Filter by Service Task", services)

        freq_filtered = service_freq.copy()
        if selected_vehicle != "All":
            freq_filtered = freq_filtered[freq_filtered["Vehicle Name"] == selected_vehicle]
        if selected_service != "All":
            freq_filtered = freq_filtered[freq_filtered["Service Tasks"] == selected_service]

        st.dataframe(freq_filtered, use_container_width=True)

        # Chart: service count per vehicle
        st.markdown("### Service Count per Vehicle")
        freq_by_vehicle = (
            service_freq.groupby("Vehicle Name")["Service Count"]
            .sum()
            .reset_index()
            .sort_values("Service Count", ascending=False)
        )
        st.bar_chart(freq_by_vehicle.set_index("Vehicle Name")["Service Count"])

        # Chart: service count per service task
        st.markdown("### Service Count per Service Task")
        freq_by_task = (
            service_freq.groupby("Service Tasks")["Service Count"]
            .sum()
            .reset_index()
            .sort_values("Service Count", ascending=False)
        )
        st.bar_chart(freq_by_task.set_index("Service Tasks")["Service Count"])

    # ---------- RAW DATA TAB ----------
    with tab_raw:
        st.subheader("Full Dataset (with Miles Between Service)")
        st.dataframe(df, use_container_width=True)

