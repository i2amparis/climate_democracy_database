import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import geopandas as gpd
import time

# Streamlit Map interface
st.markdown("#### Interactive Map: Country-Level Data Over Time")
st.markdown('''
            This is a map infographic to present country level data. Select a desired variable from the sidebar and
            slide the bar through the years to observe the values for each European country in the dataset.
            ''')

df = st.session_state["import_data"]
df_meta = st.session_state["import_metadata"]

# Transform data for map usage
@st.cache_resource
def transform_data_for_map():
    transformed_data = df.pivot(index=['countryname', 'observation_year'], columns='variable', values='value')
    transformed_data.reset_index(inplace=True)
    return transformed_data

# Load data from Natural Earth Data site
@st.cache_resource
def countries_dataset():
    shapefile_path = 'input_data/ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp'
    world_dataframe = gpd.read_file(shapefile_path)
    return world_dataframe

@st.cache_data
def map_metadata(variable):
    description = df_meta.loc[variable, 'Interpretation']
    source = df_meta.loc[variable, 'Source']
    return description, source

@st.cache_data
def map_filtered_data_per_year(year, _world_dataframe):
    # Filter data for the selected year
    filtered_data = pivoted_data[pivoted_data['observation_year'] == year]
    # Create a dataframe with the country left-joining the world dataset with our dataset
    merged_datasets = _world_dataframe.merge(
        filtered_data,
        left_on="NAME",
        right_on="countryname",
        how="left"  # Keep all countries locations from GeoDataFrame
    )
    return merged_datasets

pivoted_data = transform_data_for_map()
world_df = countries_dataset()

def start_animation():
    st.session_state.playing = True

def stop_animation():
    st.session_state.playing = False

def update_slider():
    year = st.session_state.get("year_slider")
    if not st.session_state.playing:
        st.session_state.animation_year = year

@st.fragment()
def map_generation():
    if 'year' not in st.session_state:
        st.session_state.year = int(pivoted_data['observation_year'].min())
    if 'playing' not in st.session_state:
        st.session_state.playing = False
    if 'animation_year' not in st.session_state:
        st.session_state.animation_year = int(pivoted_data['observation_year'].min())

    var_selectbox, year_slider_col, button_col = st.columns([2, 2, 1])

    with var_selectbox:
        with st.container(border=True):
            variable_map = st.selectbox("**Select Variable:**", df["variable"].unique())

    with year_slider_col:
        with st.container(border=True):
            st.slider(
                "**Select Year**",
                int(pivoted_data['observation_year'].min()),
                int(pivoted_data['observation_year'].max()),
                value=st.session_state.animation_year,
                key='year_slider',
                on_change=update_slider
            )

    with button_col:
        if st.session_state.playing:
            if st.button("Stop", on_click=stop_animation):
                st.session_state.playing = False
        else:
            if st.button("Play", on_click=start_animation):
                st.session_state.playing = True

    map_placeholder = st.empty()
    year_placeholder = st.empty()
    desc_source_placeholder = st.empty()

    def update_map(year):
        world_merged = map_filtered_data_per_year(year, world_df)
        world_merged['has_data'] = world_merged[variable_map].notna()
        world_merged['color_variable'] = world_merged[variable_map].fillna("No Data")

        fig = px.choropleth(
            world_merged[world_merged['has_data']],
            geojson=world_merged.__geo_interface__,
            locations="NAME",
            featureidkey="properties.NAME",
            color=variable_map,
            title=f"{variable_map} by Country in {year}",
            color_continuous_scale="YlOrRd",
            hover_data={variable_map: ':.0f'},
        )

        # Add countries with "No Data" as a single trace
        no_data_countries = world_merged[~world_merged['has_data']]
        fig.add_trace(
            go.Choropleth(
                geojson=no_data_countries.__geo_interface__,
                locations=no_data_countries["NAME"],
                z=[-1] * len(no_data_countries),  # Use -1 as indicator for "No Data"
                showscale=False,  # Disable color scale for "No Data"
                colorscale=[[0, "lightgray"], [1, "lightgray"]],  # Colour fill for "No Data"
                featureidkey="properties.NAME",
                name="No Data",  # Legend label
                marker_line_width=0.5,  # borderline intensity
                hovertemplate="<b>%{location}</b><br>No Data Available<extra></extra>",  # Custom hover text
                showlegend = False  # Suppress "No Data" in the legend
            )
        )

        fig.update_geos(center={"lat": 54.5260, "lon": 15.2551}, projection_scale=4)
        fig.update_layout