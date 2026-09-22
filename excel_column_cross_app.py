import streamlit as st
import pandas as pd
import io
import os

st.set_page_config(page_title="Excel Column Cross (From Repo)", layout="wide")
st.title("Excel Column Cross Product (From Repo)")
st.markdown(
    "This app reads Excel files **from the same Git repository** as the code. "
    "Select two sheets (from any of the Excel files in the repo) and generate a cross product."
)

# ----------------------------
# CONFIG: folder where Excel files are stored (relative to this script)
# ----------------------------
# Change this if your Excel files are in a different folder.
EXCEL_FOLDER = "."  # current directory; or e.g. "data"

# ----------------------------
# Discover Excel files in repo
# ----------------------------
@st.cache_data
def list_excel_files(folder: str):
    excel_files = []
    if not os.path.isdir(folder):
        return excel_files
    for fname in os.listdir(folder):
        if fname.lower().endswith((".xlsx", ".xls")) and not fname.startswith("~"):
            excel_files.append(fname)
    return sorted(excel_files)

excel_files = list_excel_files(EXCEL_FOLDER)

if not excel_files:
    st.error(
        f"No Excel files found in folder '{EXCEL_FOLDER}'. "
        "Please add .xlsx/.xls files to this folder in the repo."
    )
    st.stop()

st.write(f"Found Excel files in '{EXCEL_FOLDER}':")
st.json(excel_files)

# ----------------------------
# Helper: get sheet names for a file
# ----------------------------
@st.cache_data
def get_sheet_names(filename: str):
    path = os.path.join(EXCEL_FOLDER, filename)
    xls = pd.ExcelFile(path)
    return xls.sheet_names

# ----------------------------
# UI: select two sheets (from possibly different files)
# ----------------------------
st.subheader("Select two sheets to cross")

# File + sheet selection for first sheet
file1 = st.selectbox("Select Excel file for Sheet 1", excel_files, index=0 if excel_files else None)
sheet_names1 = get_sheet_names(file1) if file1 else []
sheet1 = st.selectbox("Select Sheet 1", sheet_names1, index=0 if sheet_names1 else None)

# File + sheet selection for second sheet
file2 = st.selectbox("Select Excel file for Sheet 2", excel_files, index=min(1, len(excel_files)-1) if excel_files else None)
sheet_names2 = get_sheet_names(file2) if file2 else []
sheet2 = st.selectbox("Select Sheet 2", sheet_names2, index=0 if sheet_names2 else None)

if not file1 or not sheet1 or not file2 or not sheet2:
    st.warning("Please select both files and sheets.")
    st.stop()

# ----------------------------
# Load selected sheets
# ----------------------------
path1 = os.path.join(EXCEL_FOLDER, file1)
path2 = os.path.join(EXCEL_FOLDER, file2)

df1 = pd.read_excel(path1, sheet_name=sheet1)
df2 = pd.read_excel(path2, sheet_name=sheet2)

st.success("Sheets loaded successfully!")
st.write(f"**Sheet 1** (`{file1}` → `{sheet1}`): {df1.shape[0]} rows × {df1.shape[1]} columns")
st.write(f"**Sheet 2** (`{file2}` → `{sheet2}`): {df2.shape[0]} rows × {df2.shape[1]} columns")

with st.expander("Preview Sheet 1"):
    st.dataframe(df1)
with st.expander("Preview Sheet 2"):
    st.dataframe(df2)

# ----------------------------
# Column selection
# ----------------------------
st.subheader("Select columns to cross")

cols1 = df1.columns.tolist()
cols2 = df2.columns.tolist()

mode = st.radio(
    "Cross mode",
    ["All columns from Sheet 1 × All columns from Sheet 2",
     "Select specific columns from each sheet"],
    index=0
)

if mode == "All columns from Sheet 1 × All columns from Sheet 2":
    selected_cols1 = cols1
    selected_cols2 = cols2
else:
    selected_cols1 = st.multiselect(
        "Columns from Sheet 1",
        cols1,
        default=cols1[:1] if cols1 else []
    )
    selected_cols2 = st.multiselect(
        "Columns from Sheet 2",
        cols2,
        default=cols2[:1] if cols2 else []
    )

if not selected_cols1 or not selected_cols2:
    st.warning("Please select at least one column from each sheet.")
    st.stop()

st.write(
    f"Will cross: {selected_cols1} (Sheet 1) with {selected_cols2} (Sheet 2) "
    "into a single list."
)

# ----------------------------
# Build cross product as a SINGLE list
# ----------------------------
result_parts = []

for c1 in selected_cols1:
    for c2 in selected_cols2:
        vals1 = df1[c1].dropna().tolist()
        vals2 = df2[c2].dropna().tolist()

        if len(vals1) == 0 or len(vals2) == 0:
            continue

        pairs = pd.DataFrame({
            "value_sheet1": vals1 * len(vals2),
            "value_sheet2": [v for v in vals2 for _ in vals1],
            "source_col_sheet1": c1,
            "source_col_sheet2": c2,
            "source_file_sheet1": file1,
            "source_file_sheet2": file2,
            "source_sheet1": sheet1,
            "source_sheet2": sheet2,
        })

        result_parts.append(pairs)

if not result_parts:
    st.error("No valid data to cross after dropping missing values.")
    st.stop()

cross_df = pd.concat(result_parts, ignore_index=True)

st.write(f"**Result (single list):** {cross_df.shape[0]} rows × {cross_df.shape[1]} columns")

# Show full result on screen (all data visible)
st.subheader("Result (full data visible)")
st.dataframe(cross_df, use_container_width=True)

# ----------------------------
# Download (Excel only, at bottom)
# ----------------------------
st.subheader("Download")

excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
    cross_df.to_excel(writer, index=False, sheet_name="ColumnCross")
excel_bytes = excel_buffer.getvalue()

st.download_button(
    label="Download as Excel (.xlsx)",
    data=excel_bytes,
    file_name="column_cross_single_list.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.markdown("---")
st.markdown(
    "Logic: For each selected column in Sheet 1 and each selected column in Sheet 2, "
    "every value in the Sheet 1 column is paired with every value in the Sheet 2 column. "
    "All such pairs are stacked into a **single list**."
)
