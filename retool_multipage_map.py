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
        how="left"  # Keep all countries locations from GeoDataFrame
    )
    return merged_datasets

pivoted_data = transform_data_for_map()
world_df = countries_dataset()
@st.fragment()
def map_generation():

    # Initialize session state for animation control
    if 'year' not in st.session_state:
        st.session_state.year = int(pivoted_data['observation_year'].min())  # Initial year
    if 'playing' not in st.session_state:
        st.session_state.playing = False

    #var_selectbox, year_slider = st.columns(2)
    var_selectbox, year_slider, button_col = st.columns([2, 2, 1])

    with var_selectbox:
        with st.container(border=True):
            variable_map = st.selectbox(f"**Select Variable:**",
                                        df["variable"].unique())

    with year_slider:
        with st.container(border=True):
            year_of_interest = st.slider(
                f"**Select Year**",
                int(pivoted_data['observation_year'].min()),
                int(pivoted_data['observation_year'].max()),
                value=st.session_state.year, disabled=st.session_state.playing
            )

    # Play/Stop Button
    with button_col:
        if st.button("Play" if not st.session_state.playing else "Stop"):
            st.session_state.playing = not st.session_state.playing

    # Create a dataframe with the country left-joining the world dataset with our dataset
    world_merged = map_filtered_data_per_year(year_of_interest,world_df)

    # Separate countries with and without data
    world_merged['has_data'] = world_merged[variable_map].notna()
    world_merged['color_variable'] = world_merged[variable_map].fillna("No Data")  # Replace NaN with "No Data"

# Create the main map for numeric data
    fig = px.choropleth(
        world_merged[world_merged['has_data']],  # Only countries with valid numeric data
        geojson=world_merged.__geo_interface__,
        locations="NAME",
        featureidkey="properties.NAME",
        color=variable_map,  # Continuous scale for numeric data
        #hover_name="NAME",
        title=f"{variable_map} by Country in {year_of_interest}",
        color_continuous_scale="YlOrRd",
        hover_data={variable_map: ':.0f'},  # Show only the variable with no decimals
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

# Zoom default map over Europe
    fig.update_geos(
        center={"lat": 54.5260, "lon": 15.2551},  # Approximate center of Europe
        projection_scale=4,  # Zoom level (lower values zoom out, higher values zoom in)
        visible=False
    )

# Control overall layout
    fig.update_layout(
        title_text=f"{variable_map} by Country in {year_of_interest}",
        legend_title_text="Legend",
        margin={"r": 0, "t": 50, "l": 0, "b": 0}
    )

# Display the map
    st.plotly_chart(fig, use_container_width=True)

    var_desc_map, var_source_map = map_metadata(variable_map)
    st.markdown(f'**Variable description:** {var_desc_map}')
    st.markdown(f'**Variable source:** {var_source_map}')

    # Animation loop (only runs when playing)
    if st.session_state.playing:
        current_year = year_of_interest # Start from the current slider position
        max_year = int(pivoted_data['observation_year'].max())  # Define max_year
        while current_year <= max_year and st.session_state.playing:
            current_year += 1
            if current_year > max_year: #added condition to break the loop without error
                break
            st.session_state.year = current_year  # Update slider value
            
            #Force slider update by creating a dummy slider inside the loop
            with year_slider: #year_col is the column where the slider is located
                with st.container(border=True):
                    st.slider(
                        "**Select Year**",
                        int(pivoted_data['observation_year'].min()),
                        int(pivoted_data['observation_year'].max()),
                        value=st.session_state.year,
                        disabled=st.session_state.playing
                    )

             # Create a dataframe with the country left-joining the world dataset with our dataset
            world_merged = map_filtered_data_per_year(year_of_interest,world_df)

            # Separate countries with and without data
            world_merged['has_data'] = world_merged[variable_map].notna()
            world_merged['color_variable'] = world_merged[variable_map].fillna("No Data")  # Replace NaN with "No Data"

            # Create the main map for numeric data
            fig = px.choropleth(
                world_merged[world_merged['has_data']],  # Only countries with valid numeric data
                geojson=world_merged.__geo_interface__,
                locations="NAME",
                featureidkey="properties.NAME",
                color=variable_map,  # Continuous scale for numeric data
                #hover_name="NAME",
                title=f"{variable_map} by Country in {year_of_interest}",
                color_continuous_scale="YlOrRd",
                hover_data={variable_map: ':.0f'},  # Show only the variable with no decimals
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

            # Zoom default map over Europe
            fig.update_geos(
                center={"lat": 54.5260, "lon": 15.2551},  # Approximate center of Europe
                projection_scale=4,  # Zoom level (lower values zoom out, higher values zoom in)
                visible=False
            )

            # Control overall layout
            fig.update_layout(
                title_text=f"{variable_map} by Country in {year_of_interest}",
                legend_title_text="Legend",
                margin={"r": 0, "t": 50, "l": 0, "b": 0}
            )

            # Display the map
            st.plotly_chart(fig, use_container_width=True)

            var_desc_map, var_source_map = map_metadata(variable_map)
            st.markdown(f'**Variable description:** {var_desc_map}')
            st.markdown(f'**Variable source:** {var_source_map}')


            time.sleep(0.5)  # Adjust animation speed (seconds)
            st.experimental_rerun() # Essential to update the Streamlit elements

        st.session_state.playing = False # Stop at the end or when interrupted
        st.experimental_rerun()  # Update the button to "Play"

map_generation()
