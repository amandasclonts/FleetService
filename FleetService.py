import streamlit as st
import pandas as pd
from io import BytesIO

st.title("🚚 Fleet Service Dashboard")

uploaded = st.file_uploader("Upload Fleetio Excel File", type=["xlsx"])

if uploaded:
    # Read Excel
    df = pd.read_excel(uploaded)

    # Clean column names just in case
    df.columns = df.columns.str.strip()

    # Sort for previous-row calculations
    df = df.sort_values(["Vehicle Name", "Service Tasks", "Completed At"])

    # Miles between same service for same vehicle
    df["Miles Between"] = df.groupby(
        ["Vehicle Name", "Service Tasks"]
    )["Meter"].diff()

    st.subheader("Cleaned Data with Miles Between Services")
    st.dataframe(df, use_container_width=True)

    # Avg miles between by Vendor → Vehicle
    vendor_group = (
        df.groupby(["Vendor Name", "Vehicle Name"])["Miles Between"]
        .mean()
        .reset_index()
        .sort_values(["Vendor Name", "Vehicle Name"])
    )
    st.subheader("Average Miles Between Services by Vendor and Vehicle")
    st.dataframe(vendor_group, use_container_width=True)

    # Service frequency per vehicle/service
    freq_group = (
        df.groupby(["Vehicle Name", "Service Tasks"])
        .size()
        .reset_index(name="Service Count")
    )
    st.subheader("Service Frequency per Vehicle & Service Task")
    st.dataframe(freq_group, use_container_width=True)

    # Total cost per vendor
    cost_group = (
        df.groupby("Vendor Name")["Total Cost (USD)"]
        .sum()
        .reset_index()
        .sort_values("Total Cost (USD)", ascending=False)
    )
    st.subheader("Total Cost per Vendor")
    st.dataframe(cost_group, use_container_width=True)

    # Download cleaned data
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)

    st.download_button(
        label="⬇️ Download Cleaned Excel",
        data=buffer,
        file_name="clean_fleet_service_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
else:
    st.info("Upload your Fleetio Excel file to get started.")
