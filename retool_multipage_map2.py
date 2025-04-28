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
def map_filtered_data_per_year(year,_world_dataframe):
    # Filter data for the selected year
    filtered_data = pivoted_data[pivoted_data['observation_year'] == year]
    # Create a dataframe with the country left-joining the world dataset with our dataset
    merged_datasets = _world_dataframe.merge(
        filtered_data,
        left_on="NAME",
        right_on="countryname",
        how="left"
    )
    return merged_datasets

@st.cache_data
def get_global_min_max(data):
    global_min_max = data.groupby('variable')['value'].agg(['min', 'max']).to_dict('index')
    return global_min_max

pivoted_data = transform_data_for_map()
world_df = countries_dataset()
global_variable_ranges = get_global_min_max(df)

def start_animation():
    st.session_state.animation_trigger = True
    st.session_state.playing = True

def stop_animation():
    st.session_state.animation_trigger = False
    st.session_state.playing = False

def update_slider(year):
    #if not st.session_state.playing:
    st.session_state.animation_year = year

def animate_map(map_placeholder, year_placeholder, variable_map, slider_placeholder):
    max_year = int(pivoted_data['observation_year'].max())
    min_year = int(pivoted_data['observation_year'].min())
    for year in range(st.session_state.animation_year + 1, max_year + 1):
        if not st.session_state.get("animation_trigger", False):
            break
        st.session_state.animation_year = year
        #year_placeholder.markdown(f"Year: {year}")
        update_map_content(map_placeholder, year, variable_map) #map update.
        # Update the slider
        slider_placeholder.empty()
        with slider_placeholder.container(border=True):
            st.slider(
                "**Select Year**",
                min_year,
                max_year,
                value=year,
                disabled=True,  # Disable during animation
                key=f'animated_year_slider_{year}' # Unique key for each year
            )
        time.sleep(0.5)

def update_map_content(map_placeholder, year, variable_map):
    world_merged = map_filtered_data_per_year(year, world_df)
    world_merged['has_data'] = world_merged[variable_map].notna()
    world_merged['color_variable'] = world_merged[variable_map].fillna("No Data")

    global_min = global_variable_ranges.get(variable_map, {}).get('min')
    global_max = global_variable_ranges.get(variable_map, {}).get('max')

    fig = px.choropleth(
        world_merged[world_merged['has_data']],
        geojson=world_merged.__geo_interface__,
        locations="NAME",
        featureidkey="properties.NAME",
        color=variable_map,
        #title=f"{variable_map} by Country in {year}",
        color_continuous_scale="YlOrRd",
        range_color=[global_min, global_max] if global_min is not None and global_max is not None else None,
        hover_data={variable_map: ':.0f'},
    )

    # Add countries with "No Data" as a single trace
    no_data_countries = world_merged[~world_merged['has_data']]
    fig.add_trace(
        go.Choropleth(
            geojson=no_data_countries.__geo_interface__,
            locations=no_data_countries["NAME"],
            z=[-1] * len(no_data_countries),
            showscale=False,
            colorscale=[[0, "lightgray"], [1, "lightgray"]],
            featureidkey="properties.NAME",
            name="No Data",
            marker_line_width=0.5,
            hovertemplate="<b>%{location}</b><br>No Data Available<extra></extra>",
            showlegend=False
        )
    )

    fig.update_geos(center={"lat": 54.5260, "lon": 15.2551}, projection_scale=4)
    #fig.update_layout(title_text=f"{variable_map} by Country in {year}",
     #                   legend_title_text="Legend", margin={"r": 0, "t": 50, "l": 0, "b": 0})
    map_placeholder.plotly_chart(fig, use_container_width=True)

def map_generation():
    if 'year' not in st.session_state:
        st.session_state.year = int(pivoted_data['observation_year'].min())
    if 'animation_trigger' not in st.session_state:
        st.session_state.animation_trigger = False
    if 'animation_year' not in st.session_state:
        st.session_state.animation_year = int(pivoted_data['observation_year'].min())
    if 'playing' not in st.session_state:
        st.session_state.playing = False

    var_selectbox, year_slider_col, button_col = st.columns([2, 2, 1])
    desc_source_placeholder = st.empty()

    with var_selectbox:
        with st.container(border=True):
            variable_map = st.selectbox("**Select Variable:**", df["variable"].unique())
            var_desc_map, var_source_map = map_metadata(variable_map)
            st.markdown(f'**Variable description:** {var_desc_map}')
            st.markdown(f'**Variable source:** {var_source_map}')
            #desc_source_placeholder.write(f'**Variable description:** {var_desc_map}')
            #desc_source_placeholder.markdown(f'**Variable source:** {var_source_map}')

    with year_slider_col:
        slider_placeholder = st.empty()
        with slider_placeholder.container(border=True):
            st.slider(
                "**Select Year**",
                int(pivoted_data['observation_year'].min()),
                int(pivoted_data['observation_year'].max()),
                value=st.session_state.animation_year,
                disabled=st.session_state.playing,
                key='year_slider',
                on_change=lambda: update_slider(st.session_state.get("year_slider"))
            )

    with button_col:
        st.markdown('**Animation:**')
        if st.session_state.playing:
            if st.button("❚❚", on_click=stop_animation):
                st.session_state.playing = False
        else:
            if st.button("▶", on_click=start_animation):
                st.session_state.playing = True

    map_placeholder = st.empty()
    year_placeholder = st.empty()
    desc_source_placeholder = st.empty()

    try:
        update_map_content(map_placeholder, st.session_state.animation_year, variable_map)
        #var_desc_map, var_source_map = map_metadata(variable_map)
        #st.markdown(f'**Variable description:** {var_desc_map}')
        #desc_source_placeholder.write(f'**Variable description:** {var_desc_map}')
        #desc_source_placeholder.markdown(f'**Variable source:** {var_source_map}')
    except KeyError:
        st.warning(f"Sorry, there is no data available for the variable: '{variable_map}'.")

    if st.session_state.get("animation_trigger", False):
        animate_map(map_placeholder, year_placeholder, variable_map, slider_placeholder)

map_generation()