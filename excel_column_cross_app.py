import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Excel Column Cross (Single List)", layout="wide")
st.title("Excel Column Cross Product (Single List)")
st.markdown(
    "Upload two Excel files. This app creates a **single list** of all pairs between "
    "values in selected columns from File 1 and selected columns from File 2."
)

# File uploaders
file1 = st.file_uploader("Upload first Excel file (File 1)", type=["xlsx", "xls"])
file2 = st.file_uploader("Upload second Excel file (File 2)", type=["xlsx", "xls"])

if file1 and file2:
    try:
        # Read Excel files (first sheet by default)
        df1 = pd.read_excel(file1)
        df2 = pd.read_excel(file2)

        st.success("Files loaded successfully!")
        st.write(f"**File 1:** {df1.shape[0]} rows × {df1.shape[1]} columns")
        st.write(f"**File 2:** {df2.shape[0]} rows × {df2.shape[1]} columns")

        with st.expander("Preview File 1"):
            st.dataframe(df1.head())
        with st.expander("Preview File 2"):
            st.dataframe(df2.head())

        # Column selection
        st.subheader("Select columns to cross")

        cols1 = df1.columns.tolist()
        cols2 = df2.columns.tolist()

        mode = st.radio(
            "Cross mode",
            ["All columns from File 1 × All columns from File 2",
             "Select specific columns from each file"],
            index=0
        )

        if mode == "All columns from File 1 × All columns from File 2":
            selected_cols1 = cols1
            selected_cols2 = cols2
        else:
            selected_cols1 = st.multiselect(
                "Columns from File 1",
                cols1,
                default=cols1[:1] if cols1 else []
            )
            selected_cols2 = st.multiselect(
                "Columns from File 2",
                cols2,
                default=cols2[:1] if cols2 else []
            )

        if not selected_cols1 or not selected_cols2:
            st.warning("Please select at least one column from each file.")
        else:
            st.write(
                f"Will cross: {selected_cols1} (File 1) with {selected_cols2} (File 2) "
                "into a single list."
            )

            # Build cross product as a SINGLE list
            result_parts = []

            for c1 in selected_cols1:
                for c2 in selected_cols2:
                    vals1 = df1[c1].dropna().tolist()
                    vals2 = df2[c2].dropna().tolist()

                    if len(vals1) == 0 or len(vals2) == 0:
                        continue

                    # Create DataFrame of all pairs for this column pair
                    pairs = pd.DataFrame({
                        "value_file1": vals1 * len(vals2),  # repeat each val1 for all val2
                        "value_file2": [v for v in vals2 for _ in vals1],  # cycle val2
                        "source_col_file1": c1,
                        "source_col_file2": c2,
                    })

                    result_parts.append(pairs)

            if not result_parts:
                st.error("No valid data to cross after dropping missing values.")
            else:
                # Stack all pairs into one single table
                cross_df = pd.concat(result_parts, ignore_index=True)

                st.write(f"**Result (single list):** {cross_df.shape[0]} rows × {cross_df.shape[1]} columns")

                with st.expander("Preview Result (single list)"):
                    st.dataframe(cross_df.head())

                # Download options
                st.subheader("Download")

                # Excel
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

                # CSV
                csv_data = cross_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Download as CSV (text format)",
                    data=csv_data,
                    file_name="column_cross_single_list.csv",
                    mime="text/csv",
                )

                # TSV
                tsv_data = cross_df.to_csv(index=False, sep="\t").encode("utf-8")
                st.download_button(
                    label="Download as TSV (tab-separated text)",
                    data=tsv_data,
                    file_name="column_cross_single_list.tsv",
                    mime="text/plain",
                )

    except Exception as e:
        st.error(f"Error processing files: {e}")
else:
    st.info("Please upload both Excel files to generate the column cross product.")

st.markdown("---")
st.markdown(
    "Logic: For each selected column in File 1 and each selected column in File 2, "
    "every value in the File 1 column is paired with every value in the File 2 column. "
    "All such pairs are stacked into a **single list**."
