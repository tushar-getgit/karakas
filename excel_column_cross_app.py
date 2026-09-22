import streamlit as st
import pandas as pd
import io
import os
import random

st.set_page_config(page_title="Excel Column Cross (From Repo)", layout="wide")
st.title("Excel Column Cross Product (From Repo)")
st.markdown(
    "This app reads Excel files **from the same Git repository** as the code. "
    "Select sheets from the Excel files and generate a cross product."
)

# ----------------------------
# CONFIG: folder where Excel files are stored (relative to this script)
# ----------------------------
EXCEL_FOLDER = "."  # e.g. "." or "data" or "files"

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

# ----------------------------
# Helper: get sheet names for a file
# ----------------------------
@st.cache_data
def get_sheet_names(filename: str):
    path = os.path.join(EXCEL_FOLDER, filename)
    xls = pd.ExcelFile(path)
    return xls.sheet_names

# ----------------------------
# UI: select sheets using selectors (one radio per sheet slot)
# ----------------------------
st.subheader("Select sheets to cross")

# We'll support selecting multiple sheets from the same or different files.
# To keep it simple and flexible, we let the user pick:
# - For each "slot" (Sheet A, Sheet B, Sheet C, ...), choose a file and then a sheet from that file.
# The number of slots is fixed to 3 for now (as per your requirement: cross will happen for 3 sheets).

NUM_SHEETS_TO_CROSS = 3

selected_files = []
selected_sheets = []

for i in range(NUM_SHEETS_TO_CROSS):
    st.markdown(f"### Sheet {i+1}")
    
    file_sel = st.selectbox(
        f"Select Excel file for Sheet {i+1}",
        excel_files,
        index=min(i, len(excel_files)-1) if excel_files else None,
        key=f"file_slot_{i}"
    )
    
    if file_sel:
        sheet_names = get_sheet_names(file_sel)
        if not sheet_names:
            st.warning(f"No sheets found in '{file_sel}'.")
            sheet_sel = None
        else:
            # Show one radio option per sheet (number of options = number of sheets in file)
            sheet_sel = st.radio(
                f"Select Sheet {i+1}",
                sheet_names,
                index=0,
                key=f"sheet_slot_{i}_radio"
            )
    else:
        sheet_sel = None
    
    selected_files.append(file_sel)
    selected_sheets.append(sheet_sel)

if None in selected_files or None in selected_sheets:
    st.warning("Please select a file and sheet for all slots.")
    st.stop()

# ----------------------------
# Load selected sheets
# ----------------------------
dfs = []
for path_file, sheet_name in zip(selected_files, selected_sheets):
    path = os.path.join(EXCEL_FOLDER, path_file)
    df = pd.read_excel(path, sheet_name=sheet_name)
    dfs.append(df)

st.success("Sheets loaded successfully!")

for i, (df, file_name, sheet_name) in enumerate(zip(dfs, selected_files, selected_sheets)):
    with st.expander(f"Preview Sheet {i+1}"):
        st.dataframe(df, use_container_width=True)

# ----------------------------
# Column selection
# ----------------------------
st.subheader("Select columns to cross")

all_cols = [df.columns.tolist() for df in dfs]

mode = st.radio(
    "Cross mode",
    ["All columns from all sheets",
     "Select specific columns from each sheet"],
    index=1  # default to "Select specific columns from each sheet"
)

if mode == "All columns from all sheets":
    selected_cols_list = all_cols
else:
    selected_cols_list = []
    for i, cols in enumerate(all_cols):
        sel = st.multiselect(
            f"Columns from Sheet {i+1}",
            cols,
            default=cols[:1] if cols else [],
            key=f"col_select_{i}"
        )
        selected_cols_list.append(sel)

if any(len(sel) == 0 for sel in selected_cols_list):
    st.warning("Please select at least one column from each sheet.")
    st.stop()

# ----------------------------
# Build cross product as a SINGLE list across 3 sheets
# ----------------------------
# For each combination of selected columns (one from each sheet),
# create all value combinations and stack them.

result_parts = []

# Iterate over all combinations of selected columns across the sheets
import itertools

col_combinations = list(itertools.product(*selected_cols_list))

for col_combo in col_combinations:
    # col_combo is a tuple like (col1_from_sheet1, col2_from_sheet2, col3_from_sheet3)
    vals_list = [
        dfs[i][col].dropna().tolist()
        for i, col in enumerate(col_combo)
    ]
    
    # Skip if any column is empty
    if any(len(v) == 0 for v in vals_list):
        continue
    
    # Create all combinations of values across the sheets
    all_value_combos = list(itertools.product(*vals_list))
    
    # Shuffle to show results in random order
    random.shuffle(all_value_combos)
    
    # Build DataFrame
    pairs = pd.DataFrame(
        all_value_combos,
        columns=[f"value_sheet{i+1}" for i in range(NUM_SHEETS_TO_CROSS)]
    )
    
    result_parts.append(pairs)

if not result_parts:
    st.error("No valid data to cross after dropping missing values.")
    st.stop()

cross_df = pd.concat(result_parts, ignore_index=True)

# Shuffle again at the final level for extra randomness (optional)
cross_df = cross_df.sample(frac=1, random_state=42).reset_index(drop=True)

st.write(f"**Result (single list, random order):** {cross_df.shape[0]} rows × {cross_df.shape[1]} columns")

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
    "Logic: For each selected column combination across the 3 sheets, "
    "every value combination is generated and all such rows are stacked into a **single list** in random order."
)
