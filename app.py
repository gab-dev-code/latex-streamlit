import streamlit as st # type: ignore
import pandas as pd # type: ignore
import subprocess
import os
import zipfile
import time
import json
from io import BytesIO
from graph_builder import generate_dual_iv_curves # type: ignore
from panel_drawer import draw_panel_sketch # type: ignore

# --- PAGE CONFIG ---
st.set_page_config(page_title="Solarix Datasheet Generator", layout="wide")
st.title("☀️ Solarix Datasheet Generator")

# --- 1. SESSION STATE & DATA INPUT ---
if "df" not in st.session_state:
    st.session_state.df = None

# Handle VBA Data (URL)
query_params = st.query_params
if "data" in query_params and st.session_state.df is None:
    try:
        data_dict = json.loads(query_params["data"])
        st.session_state.df = pd.DataFrame(data_dict)
    except Exception as e:
        st.error(f"Error parsing URL data: {e}")

# Handle Manual Upload
uploaded_file = st.file_uploader("Upload Excel Datasheet", type="xlsx")
if uploaded_file:
    st.session_state.df = pd.read_excel(uploaded_file)
    st.session_state.uploaded_file_object = uploaded_file

# --- 2. THE EDITOR ---
if st.session_state.df is not None:
    edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", width='stretch')

    # --- 3. THE GENERATION BUTTON ---
    if st.button("🚀 Generate Datasheet(s)"):
        generated_files = []
        progress_bar = st.progress(0)
        
        # Ensure image directory exists
        os.makedirs("photos", exist_ok=True)
        
        # Load the base template once
        with open("template.tex", "r", encoding="utf-8") as f:
            base_template = f.read()

        # START THE LOOP
        for index, row in edited_df.iterrows():
            # Clean series name for filenames
            raw_series = str(row.get('series', 'Panel'))
            series_name = raw_series.replace(" ", "_")
            
            # A. Generate the panel sketch
            with st.spinner(f"Creating panel sketch for {series_name}..."):
                output_path = f"photos/{series_name}.png"
                panel_success = draw_panel_sketch(raw_series, output_path=output_path)
                if not panel_success:
                    st.error(f"Failed to save {output_path}")

            # B. Generate the custom IV Graph
            with st.spinner(f"Creating graph for {series_name}..."):
                excel_source = st.session_state.get("uploaded_file_object", "data_test.xlsx")
                
                # Extract values from the current row
                voc_value = row.get('voc', None)
                isc_value = row.get('isc', None)
                pmax_value = row.get('pmax', None)
                
                # Pass the values to the graph generator
                generate_dual_iv_curves(
                    excel_source, 
                    row['series'],
                    voc_input=voc_value,
                    isc_input=isc_value,
                    pmax_input=pmax_value
                )
            
            # C. Prepare the Data and Template
            # Define \seriesname at the top of the file to handle special characters
            # We use \detokenize to prevent underscores from breaking LaTeX
            # 1. Handle the dynamic photo name
            photo_filename = str(row.get('photo', 'default.jpg')) 
            
            # 2. Format the data safely
            formatted_row = row.copy()
            
            # Define column groups
            two_dec = ['voc', 'vmp', 'isc', 'imp']
            one_dec = ['pmax', 'eff', 'weight', 't']

            # Round values (pd.to_numeric handles non-numeric strings safely)
            for col in two_dec:
                if col in formatted_row:
                    formatted_row[col] = round(pd.to_numeric(formatted_row[col], errors='coerce'), 2)
            
            for col in one_dec:
                if col in formatted_row:
                    formatted_row[col] = round(pd.to_numeric(formatted_row[col], errors='coerce'), 1)

            latex_definition = f"\\newcommand{{\\seriesname}}{{\\detokenize{{{series_name}}}}}\n"
            current_tex = latex_definition + base_template
            
            with open("job.tex", "w", encoding="utf-8") as f:
                f.write(current_tex)
            
            pd.DataFrame([formatted_row]).to_csv("data.csv", index=False)

            # D. Run LaTeX
            with st.spinner(f"Compiling PDF for {series_name}..."):
                if os.path.exists("job.pdf"): os.remove("job.pdf")
                
                # Run xelatex twice for references/tables if needed
                process = subprocess.run(
                    ['xelatex', '-interaction=nonstopmode', 'job.tex'],
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True
                )

                if os.path.exists("job.pdf"):
                    new_pdf_name = f"Datasheet_{series_name}.pdf"
                    os.replace("job.pdf", new_pdf_name)
                    generated_files.append(new_pdf_name)
                else:
                    st.error(f"PDF failed for {series_name}. Check LaTeX logs.")
                    # Show error for debugging
                    with st.expander("Show LaTeX Error Log"):
                        st.text(process.stdout[-1000:]) 
            
            progress_bar.progress((index + 1) / len(edited_df))

        # --- 4. DOWNLOAD LOGIC ---
        if generated_files:
            st.success(f"Successfully generated {len(generated_files)} files!")
            if len(generated_files) == 1:
                with open(generated_files[0], "rb") as f:
                    st.download_button("⬇️ Download PDF", f, file_name=generated_files[0])
            else:
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for f in generated_files:
                        zf.write(f)
                        os.remove(f)
                st.download_button("⬇️ Download All (ZIP)", zip_buffer.getvalue(), 
                                   file_name="Solarix_Batch.zip")