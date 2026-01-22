import streamlit as st
import pandas as pd
import subprocess
import os
import json

# --- PAGE CONFIG ---
st.set_page_config(page_title="Solarix Datasheet Generator", page_icon="☀️", layout="wide")

st.title("☀️ Solarix PDF Generator")
st.write("Review or modify the data below before generating your professional datasheet.")

# --- 1. DATA INPUT & PERSISTENCE ---
# We use st.session_state so edits aren't lost if the app reruns
if "df" not in st.session_state:
    st.session_state.df = None

# Check for data from VBA URL
query_params = st.query_params
if "data" in query_params and st.session_state.df is None:
    try:
        raw_json = query_params["data"]
        data_dict = json.loads(raw_json)
        st.session_state.df = pd.DataFrame([data_dict])
    except Exception as e:
        st.error(f"Error parsing data from Excel: {e}")

# Fallback: Manual Upload
if st.session_state.df is None:
    uploaded_file = st.file_uploader("No data received. Please upload an Excel file:", type="xlsx")
    if uploaded_file:
        st.session_state.df = pd.read_excel(uploaded_file)

# --- 2. EDITABLE PREVIEW ---
if st.session_state.df is not None:
    st.info("💡 You can click on any cell in the table below to manually correct the data before generating.")
    
    # st.data_editor allows the user to change values directly in the browser
    edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)

    if st.button("🚀 Generate PDF: Solarix_datasheet_" + str(edited_df.iloc[0].get('series', 'Product'))):
        with st.spinner("Compiling LaTeX..."):
            
            # Save the (potentially edited) data to CSV
            edited_df.to_csv("data_heidelberg.csv", index=False)

            # File Setup
            tex_file = "template.tex"
            pdf_file = "template.pdf"
            
            # Use the 'series' value for the filename, fallback to 'Product' if missing
            series_name = str(edited_df.iloc[0].get('series', 'Product')).replace(" ", "_")
            download_name = f"Solarix_datasheet_{series_name}.pdf"

            # Run XeLaTeX
            process = subprocess.run(
                ['xelatex', '-interaction=nonstopmode', tex_file],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            if os.path.exists(pdf_file):
                st.balloons()
                st.success(f"✅ Created: {download_name}")
                with open(pdf_file, "rb") as f:
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=f,
                        file_name=download_name,
                        mime="application/pdf"
                    )
            else:
                st.error("❌ LaTeX Compilation Failed.")
                if os.path.exists("template.log"):
                    with open("template.log", "r") as log:
                        st.code(log.read()[-2000:], language="text")