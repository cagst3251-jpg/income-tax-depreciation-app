import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="CA Depreciation Engine", layout="wide")

st.title("Income Tax Depreciation Engine - CA Version")

# -----------------------------
# LOAD OR CREATE MAPPING FILE
# -----------------------------

if not os.path.exists("mapping_data.csv"):
    pd.DataFrame(columns=["Ledger Name", "Category", "Block"]).to_csv("mapping_data.csv", index=False)

if not os.path.exists("block_data.csv"):
    pd.DataFrame(columns=["Block", "Opening WDV", "Closing WDV"]).to_csv("block_data.csv", index=False)

mapping_df = pd.read_csv("mapping_data.csv")
block_df = pd.read_csv("block_data.csv")

# -----------------------------
# DEPRECIATION RATES
# -----------------------------

default_rates = {
    "Plant & Machinery": 15,
    "Furniture & Fittings": 10,
    "Office Equipment": 15,
    "Computer": 40,
    "Building": 10,
    "Mobile Equipment": 15
}

rate_df = pd.DataFrame(default_rates.items(), columns=["Category", "Rate (%)"])
edited_rates = st.data_editor(rate_df)
rate_dict = dict(zip(edited_rates["Category"], edited_rates["Rate (%)"]))

# -----------------------------
# UPLOAD TALLY FILE
# -----------------------------

uploaded_file = st.file_uploader("Upload Tally Fixed Asset Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    df.rename(columns={
        df.columns[0]: "Ledger Name",
        df.columns[1]: "Date",
        df.columns[2]: "Amount"
    }, inplace=True)

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # -----------------------------
    # AUTO MERGE WITH MAPPING
    # -----------------------------

    df = df.merge(mapping_df, on="Ledger Name", how="left")

    st.subheader("Ledger Mapping (Editable)")
    df = st.data_editor(df)

    # Save Mapping
    if st.button("Save Ledger Mapping"):
        new_mapping = df[["Ledger Name", "Category", "Block"]].drop_duplicates()
        new_mapping.to_csv("mapping_data.csv", index=False)
        st.success("Mapping Saved")

    # -----------------------------
    # HALF YEAR RULE
    # -----------------------------

    fy_end = datetime(datetime.now().year, 3, 31)
    df["Days Used"] = (fy_end - df["Date"]).dt.days

    df["Half Year?"] = df["Days Used"] < 180

    additional_option = st.checkbox("Apply Additional Depreciation (20%) – Manufacturing Only")

    # -----------------------------
    # LEDGER WISE DEPRECIATION
    # -----------------------------

    def calc_dep(row):
        rate = rate_dict.get(row["Category"], 0)

        if row["Half Year?"]:
            normal = row["Amount"] * (rate / 2) / 100
        else:
            normal = row["Amount"] * rate / 100

        additional = 0
        if additional_option:
            if row["Category"] == "Plant & Machinery":
                if row["Half Year?"]:
                    additional = row["Amount"] * 10 / 100
                else:
                    additional = row["Amount"] * 20 / 100

        return pd.Series([normal, additional])

    df[["Normal Depreciation", "Additional Depreciation"]] = df.apply(calc_dep, axis=1)

    df["Total Depreciation"] = df["Normal Depreciation"] + df["Additional Depreciation"]

    st.subheader("Ledger Wise Depreciation")
    st.dataframe(df)

    # -----------------------------
    # BLOCK WISE SUMMARY
    # -----------------------------

    block_summary = df.groupby("Block").agg({
        "Amount": "sum",
        "Normal Depreciation": "sum",
        "Additional Depreciation": "sum"
    }).reset_index()

    block_summary["Total Depreciation"] = (
        block_summary["Normal Depreciation"] + block_summary["Additional Depreciation"]
    )

    st.subheader("Block Wise Summary")
    st.dataframe(block_summary)

    # -----------------------------
    # UPDATE CLOSING WDV
    # -----------------------------

    if st.button("Update Closing WDV for Next Year"):
        updated_blocks = []

        for _, row in block_summary.iterrows():
            opening = row["Amount"]
            depreciation = row["Total Depreciation"]
            closing = opening - depreciation

            updated_blocks.append([row["Block"], opening, closing])

        updated_df = pd.DataFrame(updated_blocks, columns=["Block", "Opening WDV", "Closing WDV"])
        updated_df.to_csv("block_data.csv", index=False)

        st.success("Closing WDV Updated & Saved for Next Year")
