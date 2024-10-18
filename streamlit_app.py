import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title('Climate democracy in Europe')
st.logo('media/logo.svg', size='large', link=None, icon_image=None)

st.markdown('''
    The following dataset provides information about climate democracy 
    on all EU member states and UK since 1990. There are over 100 variables 
    about various topics related to climate action, energy policy, and democratic practices.
    ''')

df = pd.read_excel("input_data/202409_climate_democracy_data_clean.xlsx")
df_meta = pd.read_excel("input_data/202409_climate_democracy_metadata.xlsx",
    sheet_name='Variables', index_col='Variable')


# df = df.applymap(lambda x: x.lower() if isinstance(x, str) else x)
country_values = st.multiselect("Select Country:", df["countryname"].unique())
# scenario_values = st.multiselect("Select Scenarios:", df["Scenario"].unique())
# region_values = st.multiselect("Select Regions:", df["Region"].unique())
variable_value = st.selectbox("Select a Variable:", df["variable"].unique())

if country_values and variable_value:
    filtered_df = df[(df["countryname"].isin(country_values)) & 
                    (df["variable"]== variable_value)]

    var_desc = (df_meta.loc[variable_value,'Interpretation'])
    var_source = (df_meta.loc[variable_value,'Source'])

    st.markdown(f'**Variable description:** {var_desc}')
    st.markdown(f'**Variable source:** {var_source}')

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
    st.write(filtered_df.iloc[:,1:])
else:
    st.warning('Please select at least one option for each category.')

