import streamlit as st
import pandas as pd
import altair as alt

# session state variable initialisation
if "disable_country_selection" not in st.session_state:
    st.session_state.disable_country_selection = False

st.markdown('#### Time Series Visualisation')
st.markdown('''
Select a variable of interest to get a line plot of the values over
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
        variable_value = st.selectbox("**Select a Variable:**", df["variable"].unique())

        try:
            var_desc = df_meta.loc[variable_value, 'Interpretation']
            var_source = df_meta.loc[variable_value, 'Source']
            st.markdown(f'**Variable description:** {var_desc}')
            st.markdown(f'**Variable source:** {var_source}')
            st.session_state.disable_country_selection = False #enable country selection
        except KeyError:
            st.warning(f"Sorry, there is no metadata available for the variable: '{variable_value}'.")
            st.session_state.disable_country_selection = True #disable country selection

#with var_widget:
#    with st.container(border=True):
#        variable_value = st.selectbox("**Select a Variable:**",
#                                        df["variable"].unique())
#        var_desc = (df_meta.loc[variable_value, 'Interpretation'])
#        var_source = (df_meta.loc[variable_value, 'Source'])
#        st.markdown(f'**Variable description:** {var_desc}')
#        st.markdown(f'**Variable source:** {var_source}')

with country_widget:
    with st.container(border=True):
        country_values = st.multiselect("**Select Countries:**",
                                            df["countryname"].unique(), 
                                            disabled=st.session_state.disable_country_selection, #disable if needed
                                            )

if country_values and variable_value:
    filtered_df = df[(df["countryname"].isin(country_values)) &
                    (df["variable"] == variable_value)]

    if not filtered_df.empty:
        # Altair chart creation
        chart = alt.Chart(filtered_df).mark_line(point=True).encode(
            x=alt.X('observation_year:O', title="Years", axis=alt.Axis(labelAngle=0, values=list(range(filtered_df['observation_year'].min(), filtered_df['observation_year'].max() + 1, 5)))),  # Ordinal for year
            y=alt.Y('value:Q', title=variable_value),  # Quantitative for value
            color=alt.Color('countryname:N', title="Country"),  # Nominal for country
            tooltip=['countryname:N', 'observation_year:O', 'value:Q']  # Tooltip on hover
        ).properties(
            width=600,  
            height=400  
        )

        hover = alt.selection_single(
            fields=["observation_year"],
            nearest=True,
            on="mouseover",
            empty="none",
            name="hover" 
        )

        points = chart.mark_circle(size=65, color='red').add_selection(hover).transform_filter(hover) # selection to points application

        st.altair_chart(chart + points, use_container_width=True) # chart and annotations combination

        st.write(filtered_df.iloc[:, 1:])

    else:
        st.warning('No data available for the selected choices.')
else:
    st.warning('Please select at least one option for each category.')
