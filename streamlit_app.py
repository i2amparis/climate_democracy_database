import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

uploaded_file = st.file_uploader("Upload a file", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    file_extension = uploaded_file.name.split(".")[-1].lower()
    #Check for csv 
    if file_extension == "csv":
            df = pd.read_csv(uploaded_file)
    #Check for xlsx or xls
    else:
            df = pd.read_excel(uploaded_file)
    #lower case
    df = df.applymap(lambda x: x.lower() if isinstance(x, str) else x)
    country_values = st.multiselect("Select Country:", df["countryname"].unique())
    # scenario_values = st.multiselect("Select Scenarios:", df["Scenario"].unique())
    # region_values = st.multiselect("Select Regions:", df["Region"].unique())
    variable_value = st.selectbox("Select a Variable:", df["variable"].unique())

    if country_values and variable_value:
        filtered_df = df[(df["countryname"].isin(country_values)) & 
                        (df["variable"]== variable_value)]

        if not filtered_df.empty:
            plt.figure(figsize=(10, 6))

            for country in country_values:
                subset = filtered_df[(filtered_df["countryname"] == country)]
                if not subset.empty:
                    label = f"{country}"
                    plt.plot(subset.observation_year, subset.value, marker='o', linestyle='-', label=label)
                            

            plt.title(f"Line Plot for {variable_value}")
            plt.xlabel("Years")
            plt.ylabel("")  
            plt.grid(True)
            plt.legend()
            st.pyplot(plt)
        else:
            st.warning('No data available for the selected choices.')
        st.write(filtered_df)
    else:
        st.warning('Please select at least one option for each category.')
