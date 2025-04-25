import sqlite3
import pandas as pd
import gradio as gr
import plotly.graph_objects as go

connnection = sqlite3.connect("data/covid_19.db")
daily_report = pd.read_sql("""SELECT * FROM daily_report;""", con=connnection)
time_series = pd.read_sql("""SELECT * FROM time_series;""", con=connnection)
connnection.close()

total_cases = daily_report["confirmed"].sum()
total_deaths = daily_report["deaths"].sum()
latest_time_series = time_series[time_series["reported_on"] == "2023-03-09"]
total_vaccinated = latest_time_series["doses_administered"].sum()
sum_confirmed_by_country = daily_report.groupby("country")["confirmed"].sum().sort_values(ascending=False)
top_comfirmed = sum_confirmed_by_country.index[:30].to_list()
# print(total_cases, total_deaths, total_vaccinated)


def filter_global_map(country_names):
    filter_daily_report = daily_report[daily_report["country"].isin(country_names)]
    countries = filter_daily_report["country"].values
    provinces = filter_daily_report["province"].values
    counties = filter_daily_report["county"].values
    confirmed = filter_daily_report["confirmed"].values
    deaths = filter_daily_report["deaths"].values
    information_when_hover = []
    for country, province, county, c, d in zip(countries, provinces, counties, confirmed, deaths):
        if county is not None:
            marker_information = [(country, province, county), c, d]
        elif province is not None:
            marker_information = [(country, province), c, d]
        else:
            marker_information = [country, c, d]
        information_when_hover.append(marker_information)
    fig = go.Figure(
        go.Scattermapbox(
            lat = filter_daily_report["latitude"],
            lon = filter_daily_report["longitude"],
            customdata=information_when_hover,
            hoverinfo="text",
            hovertemplate="Location: %{customdata[0]}<br>Confirmed: %{customdata[1]}<br>Deaths: %{customdata[2]}",
            mode = 'markers',
            marker={
                "size":filter_daily_report["confirmed"],
                "color":filter_daily_report["confirmed"],
                "sizemin":2,
                "sizeref":filter_daily_report["confirmed"].max() / 2500,
                "sizemode":"area"
            }
        )
    )
    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox=dict(
            zoom=2,
            center=go.layout.mapbox.Center(
                lat=0,
                lon=0
            )
        )
    )
    return fig

with gr.Blocks() as global_map_tab:
    gr.Markdown("""# Covid 19 Global Map""")
    with gr.Row():
        gr.Label(f"{total_cases:,}", label="Total cases")
        gr.Label(f"{total_deaths:,}", label="Total deaths")
        gr.Label(f"{total_vaccinated:,}", label="Total doses administered")
    with gr.Column():
        countries = gr.Dropdown(choices=daily_report["country"].unique().tolist(),
                                label="Select counties",
                                multiselect=True,
                                value=top_comfirmed)
        btn = gr.Button(value="Update")
        global_map = gr.Plot()
    global_map_tab.load(
        fn=filter_global_map,
        inputs=countries,
        outputs=global_map
        )
    btn.click(
        fn=filter_global_map,
        inputs=countries,
        outputs=global_map
        )
    

time_series["reported_on"] = pd.to_datetime(time_series["reported_on"])

with gr.Blocks() as country_time_series_tab:
    gr.Markdown("""# Covid 19 Country Time Series""")
    with gr.Row():
        country = gr.Dropdown(choices=time_series["country"].unique().tolist(),
                              value="Taiwan*",
                              label="Select a country: ")
    plt_confirmed = gr.LinePlot(time_series.head(), x='reported_on', y='confirmed')
    plt_deaths = gr.LinePlot(time_series.head(), x='reported_on', y='deaths')
    plt_doses = gr.LinePlot(time_series.head(), x='reported_on', y='doses_administered')

    @gr.on(inputs=country, outputs=plt_doses)
    @gr.on(inputs=country, outputs=plt_deaths)
    @gr.on(inputs=country, outputs=plt_confirmed)

    def filter_time_series(country):
        filter_df = time_series[time_series["country"] == country]
        return filter_df
    
    country_time_series_tab.load(
        fn=filter_time_series,
        inputs=country,
        outputs=plt_confirmed)
    
    country_time_series_tab.load(
        fn=filter_time_series,
        inputs=country,
        outputs=plt_deaths)
    
    country_time_series_tab.load(
        fn=filter_time_series,
        inputs=country,
        outputs=plt_doses)


demo = gr.TabbedInterface([global_map_tab, country_time_series_tab], ["Global Map", "Country Time Series"])
demo.launch()

