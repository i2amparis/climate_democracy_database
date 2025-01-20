import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

@st.cache_resource
def basic_structure():
    st.title('Climate democracy in Europe')

    st.markdown('''
    The following dataset provides information about climate democracy 
    on all EU member states and UK since 1990. There are over 100 variables 
    about various topics related to climate action, energy policy, and democratic practices.
    ''')

@st.cache_resource
def timeseries_structure():
    st.header('Time Series Visualisation')
    st.markdown('''
                Select the countries and a desired variable to get the plot of the values over the years, for each 
                selected country.
                ''')

@st.cache_resource(show_spinner="Fetching data from the database...")
def load_data_file():
    df = pd.read_excel("input_data/202409_climate_democracy_data_clean.xlsx", engine='openpyxl')
    return df


@st.cache_resource
def load_metadata_file():
    df_meta = pd.read_excel("input_data/climate_democracy_metadata_new.xlsx",
                            sheet_name='Variables', index_col='Variable', engine='openpyxl')
    return df_meta

@st.cache_data
def timeseries_plot(country_values, variable_value):
    if country_values and variable_value:
        filtered_df = df[(df["countryname"].isin(country_values)) &
                         (df["variable"] == variable_value)]
        var_desc = (df_meta.loc[variable_value, 'Interpretation'])
        var_source = (df_meta.loc[variable_value, 'Source'])
        st.sidebar.markdown(f'**Variable description:** {var_desc}')
        st.sidebar.markdown(f'**Variable source:** {var_source}')

        if not filtered_df.empty:
            plt.figure(figsize=(10, 6))

            for country in country_values:
                subset = filtered_df[(filtered_df["countryname"] == country)]
                if not subset.empty:
                    label = f'{country}'
                    plt.plot(subset.observation_year, subset.value, marker='o', linestyle='-', label=label)

            plt.xlabel("Years")
            plt.ylabel("")
            plt.grid(True)
            plt.legend()
            st.pyplot(plt)

        else:
            st.warning('No data available for the selected choices.')
        st.write(filtered_df.iloc[:, 1:])
    else:
        st.warning('Please select at least one option for each category.')


st.logo("media/logo.svg", size='large', link=None, icon_image=None)
basic_structure()
df = load_data_file()
df_meta = load_metadata_file()

# df = df.applymap(lambda x: x.lower() if isinstance(x, str) else x)
st.header('Time Series Visualisation')
st.markdown('''
                Select the countries and a variable of interest from the sidebar to get the plot of the values over the
                years, for each selected country.
                ''')

st.sidebar.header(''' Select variable and countries of interest for timeseries visualisation''')
country_values = st.sidebar.multiselect("Select Country:", df["countryname"].unique())
# scenario_values = st.multiselect("Select Scenarios:", df["Scenario"].unique())
# region_values = st.multiselect("Select Regions:", df["Region"].unique())
variable_value = st.sidebar.selectbox("Select a Variable:", df["variable"].unique())

timeseries_plot(country_values,variable_value)


# ------------ Map Feature Code -------------

import plotly.graph_objects as go
import plotly.express as px
import geopandas as gpd

# Streamlit Map interface
@st.cache_resource
def map_structure():  # Streamlit Map interface
    st.header("Interactive Map: Country-Level Data Over Time")
    st.markdown('''
                This is a map infographic to present country level data. Select a desired variable from the sidebar and
                slide the bar through the years to observe the values for each European country in the dataset.
                ''')

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


map_structure()
pivoted_data = transform_data_for_map()
world_df = countries_dataset()

st.sidebar.header(''' Select a variable and year of interest for map infographic''')
# Map Streamlit controls
variable_map = st.sidebar.selectbox(
    "Select Variable",
    pivoted_data.columns[2:]  # Skip 'countryname' and 'observation_year'
)


var_desc_map, var_source_map = map_metadata(variable_map)
st.sidebar.markdown(f'**Variable description:** {var_desc_map}')
st.sidebar.markdown(f'**Variable source:** {var_source_map}')


year_of_interest = st.sidebar.slider(
    "Select Year",
    int(pivoted_data['observation_year'].min()),
    int(pivoted_data['observation_year'].max())
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
