import streamlit as st
import pandas as pd
import subprocess
import os

st.set_page_config(page_title="Solarix Datasheet Generator")

st.title("☀️ Solarix PDF Generator")
st.write("Upload your Excel file to generate professional datasheets.")

uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write("### Preview Data", df.head())

    if st.button("Generate PDFs"):
        with st.spinner("Compiling LaTeX..."):
            # 1. Save to the CSV format your LaTeX template expects
            df.to_csv("data_heidelberg.csv", index=False)
            
            # 2. Run XeLaTeX
            # Note: Ensure avenir-next-regular.ttf is in the folder
            process = subprocess.run(
                ['xelatex', '-interaction=nonstopmode', 'template.tex'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            if os.path.exists("template.pdf"):
                with open("template.pdf", "rb") as f:
                    st.success("Success!")
                    st.download_button(
                        label="Download Datasheet",
                        data=f,
                        file_name="Solarix_Datasheet.pdf",
                        mime="application/pdf"
                    )
            else:
                st.error("LaTeX Compilation Failed.")
                st.code(process.stdout.decode())