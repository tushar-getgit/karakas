import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Excel Column Cross Product", layout="wide")
st.title("Excel Column Cross Product")
st.markdown(
    "Upload two Excel files. This app creates all pairs between values in selected "
    "columns from File 1 and selected columns from File 2."
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

        # Option: cross all columns vs selected columns
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
            selected_cols1 = st.multiselect("Columns from File 1", cols1, default=cols1[:1] if cols1 else [])
            selected_cols2 = st.multiselect("Columns from File 2", cols2, default=cols2[:1] if cols2 else [])

        if not selected_cols1 or not selected_cols2:
            st.warning("Please select at least one column from each file.")
        else:
            st.write(f"Will cross: {selected_cols1} (File 1) with {selected_cols2} (File 2)")

            # Build cross product
            # For each pair (c1, c2), create all combinations of values
            result_parts = []

            for c1 in selected_cols1:
                for c2 in selected_cols2:
                    vals1 = df1[c1].dropna().tolist()
                    vals2 = df2[c2].dropna().tolist()

                    if len(vals1) == 0 or len(vals2) == 0:
                        continue

                    # Create DataFrame of all pairs
                    pairs = pd.DataFrame(
                        [(v1, v2) for v1 in vals1 for v2 in vals2],
                        columns=[f"{c1}", f"{c2}"]
                    )

                    # Optionally add source info columns
                    pairs["source_col_file1"] = c1
                    pairs["source_col_file2"] = c2

                    result_parts.append(pairs)

            if not result_parts:
                st.error("No valid data to cross after dropping missing values.")
            else:
                cross_df = pd.concat(result_parts, ignore_index=True)

                st.write(f"**Result:** {cross_df.shape[0]} rows × {cross_df.shape[1]} columns")

                with st.expander("Preview Result"):
                    st.dataframe(cross_df)

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
                    file_name="column_cross_product.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

                # CSV
                csv_data = cross_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Download as CSV (text format)",
                    data=csv_data,
                    file_name="column_cross_product.csv",
                    mime="text/csv",
                )

                # TSV
                tsv_data = cross_df.to_csv(index=False, sep="\t").encode("utf-8")
                st.download_button(
                    label="Download as TSV (tab-separated text)",
                    data=tsv_data,
                    file_name="column_cross_product.tsv",
                    mime="text/plain",
                )

    except Exception as e:
        st.error(f"Error processing files: {e}")
else:
    st.info("Please upload both Excel files to generate the column cross product.")

st.markdown("---")
st.markdown(
    "Logic: For each selected column in File 1 and each selected column in File 2, "
    "every value in the File 1 column is paired with every value in the File 2 column."
)
