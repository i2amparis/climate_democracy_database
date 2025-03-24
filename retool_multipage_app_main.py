import streamlit as st
import pandas as pd

#Datafiles path definition
data_path = "input_data/202409_climate_democracy_data_clean.xlsx"
metadata_path = "input_data/climate_democracy_metadata_new.xlsx"

#Central page aesthetics
st.set_page_config(page_title="Climate Democracy Data",
                   page_icon="media/logo_cropped.svg")
st.logo("media/logo.svg", size='large', link=None, icon_image=None)
st.header('''Climate Democracy in Europe''')

st.sidebar.header('''Introduction''')
st.sidebar.markdown('''
RETOOL is an EU Horizon Europe project that aims to advance
our understanding of how to address the twin challenges of responding
to the climate imperative while strengthening and reinvigorating
democratic governance.

This page is an interactive interface to the RETOOL climate democracy
dataset. The dataset provides information about climate democracy on
all EU member states and UK since 1990. There are over 100 variables
about various topics related to climate action, energy policy, and
democratic practices.

You can explore the dataset through the different visualisations
available below.''')

st.sidebar.header('''Select a visualisation''')

@st.cache_resource(show_spinner="Fetching data from the database...")
def load_data_file(path):
    df = pd.read_excel(path, engine='openpyxl')
    return df

@st.cache_resource
def load_metadata_file(path):
    df_meta = pd.read_excel(path,
                            sheet_name='Variables', index_col='Variable', engine='openpyxl')
    return df_meta


#df = load_data_file(data_path)
#df_meta = load_metadata_file(metadata_path)

def import_data_file():
    key = "import_data"
    if key not in st.session_state:
        st.session_state[key] = load_data_file(data_path)
    return st.session_state[key]

def import_metadata_file():
    key = "import_metadata"
    if key not in st.session_state:
        st.session_state[key] = load_metadata_file(metadata_path)
    return st.session_state[key]

timeseries_page = st.Page("retool_multipage_timeseries2.py")
                          #,
                          #title="Time Series Visualisation",
                          #icon="📈")
map_page = st.Page("retool_multipage_map2.py")
                   #,
                   #title="Interactive Map Infographic",
                   #icon="🌍")

#df = import_data_file()
#df_meta = import_metadata_file()

st.sidebar.page_link(map_page,
             label="Interactive Map Infographic", icon="🌍")

st.sidebar.page_link(timeseries_page,
             label="Time Series Visualisation",
             icon="📈")

st.sidebar.header("Download the full dataset")

with open(data_path, 'rb') as f:
    st.sidebar.download_button("Full dataset", f, file_name='retool_climate_democracy_data.xlsx')
with open(metadata_path, 'rb') as m:
    st.sidebar.download_button("Metadata file", m, file_name='retool_climate_democracy_metadata.xlsx')

st.sidebar.header("Find more about RETOOL")
st.sidebar.markdown(f"[https://retoolproject.eu/](https://retoolproject.eu/)")

import_data_file()
import_metadata_file()

multipage = st.navigation([map_page, timeseries_page],
                          position="hidden")

multipage.run()
