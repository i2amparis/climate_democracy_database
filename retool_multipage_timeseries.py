import streamlit as st
import matplotlib.pyplot as plt

st.markdown('#### Time Series Visualisation')
st.markdown('''
Select a varible of interest to get a line plot of the values over
the years for each selected country. You can also save the plot by
right clicking on it and selecting "Save Image As". Similarly, you
can download the respective dataset by hovering over the dataset and
selecting "Download as CSV".
''')

df = st.session_state["import_data"]
df_meta = st.session_state["import_metadata"]

var_widget, country_widget = st.columns(spec=2,
                              gap="medium",
                              vertical_alignment="top")

with var_widget:
    with st.container(border=True):
        variable_value = st.selectbox("**Select a Variable:**",
                                      df["variable"].unique())
        var_desc = (df_meta.loc[variable_value, 'Interpretation'])
        var_source = (df_meta.loc[variable_value, 'Source'])
        st.markdown(f'**Variable description:** {var_desc}')
        st.markdown(f'**Variable source:** {var_source}')
with country_widget:
    with st.container(border=True):
        country_values = st.multiselect("**Select Countries:**",
                                        df["countryname"].unique())

if country_values and variable_value:
    filtered_df = df[(df["countryname"].isin(country_values)) &
                        (df["variable"] == variable_value)]

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

