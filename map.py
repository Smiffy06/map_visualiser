import streamlit as st
import pandas as pd
import plotly.express as px
import json
import plotly.graph_objects as go
import geopandas as gpd

st.title("Map Visualization Dashboard")
st.write("---")

# Load JSON
@st.cache_data
def load_json():
    with open("newindia.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    state_districts = {}
    for feature in data["features"]:
        props = feature.get("properties", {})
        state = props.get("st_nm")
        district = props.get("district")

        if state and district:
            state_districts.setdefault(state, set()).add(district)

    sorted_states = sorted(state_districts.keys())
    sorted_districts = {state: sorted(list(districts)) for state, districts in state_districts.items()}

    return sorted_states, sorted_districts

states, districts_data = load_json()

st.header("India State and District Selector")
col1, col2 = st.columns(2)
with col1:
    selected_state = st.selectbox("Choose a State/Union Territory:", states)
with col2:
    district_options = districts_data[selected_state]
    selected_district = st.selectbox("Choose a District:", district_options)

st.write("---")
#-----------------------------------------------------------------------------------------------------------------------

gdf = gpd.read_file("newindia.json")
population_df = pd.read_csv("state_wise_population.csv")

population_df["state"] = population_df["State"].str.strip().str.title()
population_df.drop(columns=["State"], inplace=True)

gdf["st_nm_clean"] = gdf["st_nm"].str.strip().str.title()
gdf = gdf.merge(population_df, left_on="st_nm_clean", right_on="state", how="left")

gdf["hover_text"] = gdf.apply(lambda row: (
        f"<b>{row['st_nm']}</b><br>"
        f"Total: {int(row['total_population']):,}<br>"
        f"Male: {int(row['population_male']):,}<br>"
        f"Female: {int(row['population_female']):,}") 
        if pd.notna(row['total_population']) else row['st_nm'],
    axis=1
)

state_gdf = gdf[gdf["st_nm"] == selected_state]
district_gdf = gdf[(gdf["st_nm"] == selected_state) & (gdf["district"] == selected_district)]

col1, col2 = st.columns(2)
with col1:
    st.subheader("Selected State Map")
    india_states = gdf.dissolve(by="st_nm", as_index=False)
    selected_state_shape = india_states[india_states["st_nm"] == selected_state]
    fig_state = go.Figure()
    fig_state.add_trace(go.Choropleth(
        geojson=india_states.__geo_interface__,
        locations=india_states.index,
        z=[0]*len(india_states),
        colorscale=[[0, "lightgrey"], [1, "lightgrey"]],
        showscale=False,
        marker_line_color="black",
        marker_line_width=0.5,
        hoverinfo="skip"
    ))

    selected_hover = gdf[gdf["st_nm"] == selected_state].iloc[0]["hover_text"]

    fig_state.add_trace(go.Choropleth(
        geojson=selected_state_shape.__geo_interface__,
        locations=selected_state_shape.index,
        z=[1]*len(selected_state_shape),
        colorscale=[[0, "#FFA500"], [1, "#FFA500"]],
        showscale=False,
        marker_line_color="black",
        marker_line_width=2,
        hovertemplate=selected_hover
    ))

    fig_state.update_geos(fitbounds="locations", visible=False)
    fig_state.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig_state)

with col2:
    st.subheader("Selected District Map")
    all_districts_in_state = gdf[gdf["st_nm"] == selected_state]
    fig_district = go.Figure()
    
    fig_district.add_trace(go.Choropleth(
        geojson=all_districts_in_state.__geo_interface__,
        locations=all_districts_in_state.index,
        z=[0]*len(all_districts_in_state),
        colorscale=[[0, "lightgrey"], [1, "lightgrey"]],
        showscale=False,
        marker_line_color="white",
        hoverinfo="skip"
    ))

    fig_district.add_trace(go.Choropleth(
        geojson=district_gdf.__geo_interface__,
        locations=district_gdf.index,
        z=[1]*len(district_gdf),
        colorscale=[[0, "#008080"], [1, "#008080"]],
        showscale=False,
        marker_line_color="black",
        hovertemplate=f"<b>{selected_district}</b><extra></extra>"
    ))  

    fig_district.add_trace(go.Choropleth(
        geojson=state_gdf.__geo_interface__,
        locations=state_gdf.index,
        z=[0]*len(state_gdf),
        colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
        showscale=False,
        marker_line_color="black",
        marker_line_width=2,
        hoverinfo="skip"
    ))

    fig_district.update_geos(fitbounds="locations", visible=False)
    fig_district.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig_district)

st.write("---")
st.subheader("What you selected:")
st.success(selected_state)
st.success(selected_district)

st.write("---")
st.subheader("Population for the Selected State")

pop_row = population_df[population_df["state"] == selected_state.title()].iloc[0]

total=int(population_df[population_df["state"] == selected_state.title()]["total_population"].iloc[0])
male=int(population_df[population_df["state"] == selected_state.title()]["population_male"].iloc[0])
female=int(population_df[population_df["state"] == selected_state.title()]["population_female"].iloc[0])

sunburst_df = pd.DataFrame({
    "labels": [selected_state, "Male", "Female"],
    "parents": ["", selected_state, selected_state],
    "values": [total, male, female]
})

fig_sunburst = px.sunburst(
    sunburst_df,
    names="labels",
    parents="parents",
    values="values",
    color="values",)
st.plotly_chart(fig_sunburst)
st.write("---")
st.write("Select Wide Mode in Streamlit Settings to view the map properly.")