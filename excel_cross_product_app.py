import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Excel Cross Product", layout="wide")
st.title("Excel Cross Product Generator")
st.markdown("Upload two Excel files. This app creates a cross product (Cartesian product) of **all columns** from File 1 with **all columns** from File 2.")

# File uploaders
file1 = st.file_uploader("Upload first Excel file (File 1)", type=["xlsx", "xls"])
file2 = st.file_uploader("Upload second Excel file (File 2)", type=["xlsx", "xls"])

if file1 and file2:
    try:
        # Read Excel files
        df1 = pd.read_excel(file1)
        df2 = pd.read_excel(file2)

        st.success("Files loaded successfully!")
        st.write(f"**File 1:** {df1.shape[0]} rows × {df1.shape[1]} columns")
        st.write(f"**File 2:** {df2.shape[0]} rows × {df2.shape[1]} columns")

        # Show previews
        with st.expander("Preview File 1"):
            st.dataframe(df1.head())
        with st.expander("Preview File 2"):
            st.dataframe(df2.head())

        # Create cross product
        # Add a temporary key to each dataframe to enable merge
        df1["_key"] = 1
        df2["_key"] = 1

        cross_df = pd.merge(df1, df2, on="_key", how="outer")
        cross_df = cross_df.drop(columns=["_key"])

        st.write(f"**Cross product result:** {cross_df.shape[0]} rows × {cross_df.shape[1]} columns")

        with st.expander("Preview Cross Product"):
            st.dataframe(cross_df)

        # Download options
        st.subheader("Download")

        # Excel download
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            cross_df.to_excel(writer, index=False, sheet_name="CrossProduct")
        excel_bytes = excel_buffer.getvalue()

        st.download_button(
            label="Download as Excel (.xlsx)",
            data=excel_bytes,
            file_name="cross_product.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        # Text (CSV) download
        csv_data = cross_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download as CSV (text format)",
            data=csv_data,
            file_name="cross_product.csv",
            mime="text/csv",
        )

        # Plain text (tab-separated) download
        txt_data = cross_df.to_csv(index=False, sep="\t").encode("utf-8")
        st.download_button(
            label="Download as TSV (tab-separated text)",
            data=txt_data,
            file_name="cross_product.tsv",
            mime="text/plain",
        )

    except Exception as e:
        st.error(f"Error processing files: {e}")
else:
    st.info("Please upload both Excel files to generate the cross product.")

st.markdown("---")
st.markdown("**Note:** A cross product pairs every row from File 1 with every row from File 2. If File 1 has *m* rows and File 2 has *n* rows, the result will have *m × n* rows.")
