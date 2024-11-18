import streamlit as st
import pandas as pd
import pydeck as pdk
import geopandas as gpd
from shapely import wkt
import altair as alt
import scipy.stats as stats

# Title of the analysis
st.title("Gold Mining and Mercury Poisoning: A Spatial Analysis of Selected Environmental Contaminants in the Amazon")
st.markdown("### By Anna Correa, Advised by Jerry Reed")

# File paths
file_path1 = 'illegal_mines.csv'
file_path2 = 'fish_kill.csv'
file_path3 = 'lmines.csv'
file_path4 = 'fk.csv'

# Ensure the files are read properly
try:
    # Load and normalize datasets
    df1 = pd.read_csv(file_path1)
    df1.columns = df1.columns.str.lower()
    
    df2 = pd.read_csv(file_path2)
    df2.columns = df2.columns.str.lower()

    df3 = pd.read_csv(file_path3)
    df3.columns = df3.columns.str.lower()

    # Check if the geometry column exists in df3
    if 'geometry' in df3.columns:
        df3['geometry'] = df3['geometry'].apply(wkt.loads)
        gdf3 = gpd.GeoDataFrame(df3, geometry='geometry')
        gdf3['centroid'] = gdf3['geometry'].centroid
        gdf3['latitude'] = gdf3['centroid'].y
        gdf3['longitude'] = gdf3['centroid'].x
        gdf3 = gdf3[['latitude', 'longitude']]

        # Map visualization
        layer1 = pdk.Layer(
            'ScatterplotLayer', data=df1, get_position='[longitude, latitude]', 
            get_color='[255, 0, 0, 160]', get_radius=10000, pickable=True)
        layer2 = pdk.Layer(
            'ScatterplotLayer', data=df2, get_position='[longitude, latitude]', 
            get_color='[0, 0, 255, 160]', get_radius=20000, pickable=True)
        layer3 = pdk.Layer(
            'ScatterplotLayer', data=gdf3, get_position='[longitude, latitude]', 
            get_color='[0, 255, 0, 160]', get_radius=10000, pickable=True)

        view_state = pdk.ViewState(
            latitude=(df1['latitude'].mean() + df2['latitude'].mean() + gdf3['latitude'].mean()) / 3,
            longitude=(df1['longitude'].mean() + df2['longitude'].mean() + gdf3['longitude'].mean()) / 3,
            zoom=5, pitch=40)

        r = pdk.Deck(layers=[layer1, layer2, layer3], initial_view_state=view_state,
                     tooltip={"text": "Latitude: {latitude}\nLongitude: {longitude}"})
        st.pydeck_chart(r)

        st.markdown("#### Legend:")
        st.markdown('**Illegal Mines: :red[●] Red**')
        st.markdown('**Legal Mines: :green[●] Green**')
        st.markdown('**Fish Poisoning Sites: :blue[●] Blue**')

    # Load the fk dataset
    fk = pd.read_csv(file_path4)
    correlations_by_mine_type = {}
    p_values_by_mine_type = {}

    for mine_type, group in fk.groupby("mine_type"):
        correlations = group[["distance_km", "mean_value", "mean_carnivorous_value", "mean_non_carnivorous_value"]].corr()["distance_km"]
        correlations = correlations.drop("distance_km")
        correlations_by_mine_type[mine_type] = correlations

        p_values = {}
        n = len(group)
        for col in correlations.index:
            r = correlations[col]
            t_stat = r * ((n - 2) ** 0.5) / ((1 - r ** 2) ** 0.5) if r != 1 else float('inf')
            p_value = (1 - stats.t.cdf(abs(t_stat), df=n - 2)) * 2
            p_values[col] = p_value
        p_values_by_mine_type[mine_type] = p_values

    st.write("### Correlations and P-values by Mine Type (rounded to 3 decimals)")

    for mine_type, correlations in correlations_by_mine_type.items():
        st.write(f"#### {mine_type}:")

        # Create a styled DataFrame for better readability
        results_df = pd.DataFrame({
            'Correlation': [f"{correlations[col]:.3f}" for col in correlations.index],
            'P-value': [f"{p_values_by_mine_type[mine_type][col]:.13f}" for col in correlations.index]
        }, index=correlations.index)

        styled_df = results_df.style.set_properties(**{
            'width': '150px',  # Set a fixed width for columns
            'text-align': 'center'
        }).format(precision=13)  # Ensure numbers retain precision

        # Display the styled DataFrame in Streamlit
        st.dataframe(styled_df, use_container_width=True)

except Exception as e:
    st.error(f"Error loading the files: {e}")

# Second Graph

# Create dictionaries to store correlations and p-values
fk = pd.read_csv(file_path4)

st.markdown("## Distance and Mean Concentration of Hg Value")

# Convert 'distance_km' and 'mean_value' to numeric, forcing errors to NaN
fk['distance_km'] = pd.to_numeric(fk['distance_km'], errors='coerce')
fk['mean_value'] = pd.to_numeric(fk['mean_value'], errors='coerce')

# Drop rows with NaN values in the relevant columns
fk = fk.dropna(subset=['distance_km', 'mean_value'])

# Create a scatter plot using Altair
chart = alt.Chart(fk).mark_circle(size=60).encode(
    x='distance_km',
    y='mean_value',
    color=alt.Color('mine_type:N', scale=alt.Scale(scheme='set1')),
    tooltip=['distance_km', 'mean_value', 'mine_type']  # Add tooltips for interaction
).interactive()

# Display the chart in Streamlit
st.altair_chart(chart, use_container_width=True)

st.markdown("## Distance and Mean Concentration of Hg Value in Illegal Mines Only")

# Filter for illegal mines
illegal_mines = fk[fk['mine_type'] == "Illegal"]

# Convert 'distance_km' and 'mean_value' to numeric, forcing errors to NaN
illegal_mines['distance_km'] = pd.to_numeric(illegal_mines['distance_km'], errors='coerce')
illegal_mines['mean_value'] = pd.to_numeric(illegal_mines['mean_value'], errors='coerce')

# Drop rows with NaN values in the relevant columns
illegal_mines = illegal_mines.dropna(subset=['distance_km', 'mean_value'])

# Create a scatter plot using Altair
chart = alt.Chart(illegal_mines).mark_circle(size=60).encode(
    x='distance_km',
    y='mean_value',
    color=alt.Color('mine_type:N', scale=alt.Scale(scheme='set1')),
    tooltip=['distance_km', 'mean_value', 'mine_type']  # Add tooltips for interaction
).interactive()

# Display the chart in Streamlit
st.altair_chart(chart, use_container_width=True)

st.markdown("## Distance and Mean Concentration of Hg Value of Carnivorous Fish in Illegal Mines Only")

# Filter for illegal mines

# Convert 'mean_carnivorous_value' to numeric, forcing errors to NaN
illegal_mines['mean_carnivorous_value'] = pd.to_numeric(illegal_mines['mean_carnivorous_value'], errors='coerce')

# Drop rows with NaN values in the relevant columns
illegal_mines = illegal_mines.dropna(subset=['distance_km', 'mean_carnivorous_value'])

# Create a scatter plot using Altair
chart = alt.Chart(illegal_mines).mark_circle(size=60).encode(
    x='distance_km',
    y='mean_carnivorous_value',
    color=alt.Color('mine_type:N', scale=alt.Scale(scheme='set1')),
    tooltip=['distance_km', 'mean_carnivorous_value', 'mine_type']  # Add tooltips for interaction
).interactive()

# Display the chart in Streamlit
st.altair_chart(chart, use_container_width=True)

st.markdown("## References")
st.write('Basta, Paulo Cesar, et al. "Nota Técnica: maio 2023: Análise regional dos níveis de mercúrio em peixes consumidos pela população da Amazônia brasileira: um alerta em saúde pública e uma ameaça à segurança alimentar." (2023).')
st.write('Earth Genome. “Mining-Detector/Data/Airstrips/Illegal-Airstrips-NYT-Intercept-Public.csv at Main · Earthrise-Media/Mining-Detector.” GitHub, 2024, github.com/earthrise-media/mining-detector/blob/main/data/airstrips/Illegal-Airstrips-NYT-Intercept-Public.csv. Accessed 14 Sept. 2024.')
st.write('“Sistema de Informações Geográficas Da Mineração (SIGMINE).” Dados.gov.br, 1 July 2021, dados.gov.br/dados/conjuntos-dados/sistema-de-informacoes-geograficas-da-mineracao-sigmine. Accessed 24 Oct. 2024.')
