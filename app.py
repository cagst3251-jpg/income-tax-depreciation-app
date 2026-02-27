import streamlit as st
import pandas as pd

st.set_page_config(page_title="Income Tax Depreciation Calculator", layout="wide")

st.title("Income Tax Depreciation Calculator (India)")
st.write("For Single Client | As per Income Tax Act Rates")

# Default Depreciation Rates
default_rates = {
    "Plant & Machinery": 15,
    "Office Equipment": 15,
    "Furniture & Fittings": 10,
    "Mobile Equipment": 15,
    "Computer": 40,
    "Building": 10
}

# Editable Rate Table
st.subheader("Depreciation Rate Settings")
rate_df = pd.DataFrame(default_rates.items(), columns=["Category", "Rate (%)"])
edited_rates = st.data_editor(rate_df, num_rows="dynamic")
rate_dict = dict(zip(edited_rates["Category"], edited_rates["Rate (%)"]))

st.markdown("---")

st.subheader("Upload Asset Data (Tally Excel Format)")
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
else:
    st.write("Or Enter Manually")
    df = pd.DataFrame({
        "Asset Name": [],
        "Category": [],
        "Purchase Date": [],
        "Purchase Amount": [],
        "Is New Plant & Machinery? (Yes/No)": []
    })
    df = st.data_editor(df, num_rows="dynamic")

if not df.empty:

    df["Purchase Date"] = pd.to_datetime(df["Purchase Date"], errors='coerce')

    additional_option = st.checkbox("Apply Additional Depreciation (20%) for NEW Plant & Machinery (Manufacturing Only)")

    def calculate_depreciation(row):
        category = row["Category"]
        cost = row["Purchase Amount"]

        if category in rate_dict:
            rate = rate_dict[category]
        else:
            rate = 0

        normal_dep = cost * rate / 100

        additional_dep = 0
        if additional_option:
            if category == "Plant & Machinery" and str(row["Is New Plant & Machinery? (Yes/No)"]).lower() == "yes":
                additional_dep = cost * 20 / 100

        return normal_dep, additional_dep

    df[["Normal Depreciation", "Additional Depreciation"]] = df.apply(
        lambda row: pd.Series(calculate_depreciation(row)), axis=1
    )

    df["Total Depreciation"] = df["Normal Depreciation"] + df["Additional Depreciation"]

    st.subheader("Depreciation Calculation Result")
    st.dataframe(df)

    st.subheader("Summary")
    st.write("Total Normal Depreciation:", df["Normal Depreciation"].sum())
    st.write("Total Additional Depreciation:", df["Additional Depreciation"].sum())
    st.write("Total Depreciation:", df["Total Depreciation"].sum())
