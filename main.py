import pandas as pd
import io
import requests
import plotly.express as px
import plotly.io as pio


pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

response = requests.get('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json')
countries_json = response.json()

confirmed_url = requests.get('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv').content
death_url = requests.get('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv').content

confirmed_cases = pd.read_csv(io.StringIO(confirmed_url.decode('utf-8')))
deaths = pd.read_csv(io.StringIO(death_url.decode('utf-8')))

country_codes = pd.read_csv('https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.csv')[['name', 'alpha-3']]
country_codes = country_codes.rename(columns={'name': 'Country/Region'})
country_codes = country_codes.append(pd.DataFrame(data={'Country/Region':['Kosovo'], 'alpha-3':['CS-KM']}), ignore_index=True)

confirmed_case_columns = confirmed_cases.columns[4:].tolist()
deaths_columns = deaths.columns[4:].tolist()

ISO_3_naming = {'Bolivia': 'Bolivia (Plurinational State of)', 'Brunei': 'Brunei Darussalam',
                'Congo (Brazzaville)': 'Congo', 'Congo (Kinshasa)': 'Congo, Democratic Republic of the',
                'Republic of the Congo': 'Congo', "Cote d'Ivoire": "Côte d'Ivoire",
                'Reunion': 'Réunion', 'Korea, South': 'Korea, Republic of',
                'Moldova': 'Moldova, Republic of', 'Russia': 'Russian Federation',
                'Taiwan*': 'Taiwan, Province of China', 'Tanzania': 'Tanzania, United Republic of',
                'The Bahamas': 'Bahamas', 'Bahamas, The': 'Bahamas', 'US': 'United States of America',
                'United Kingdom': 'United Kingdom of Great Britain and Northern Ireland',
                'Venezuela': 'Venezuela (Bolivarian Republic of)', 'Vietnam': 'Viet Nam',
                'West Bank and Gaza': 'Palestine, State of',
                'Iran': 'Iran (Islamic Republic of)', 'Gambia, The': 'Gambia',
                'The Gambia': 'Gambia', 'Syria': 'Syrian Arab Republic', 'Laos': "Lao People's Democratic Republic",
                }

country_consolidated_cases = confirmed_cases.replace(ISO_3_naming)
country_consolidated_cases = pd.pivot_table(country_consolidated_cases, index=['Country/Region'],values=confirmed_case_columns,aggfunc='sum').reset_index()
country_consolidated_cases = country_consolidated_cases.merge(country_codes, how='left', on='Country/Region')

country_consolidated_deaths = deaths.replace(ISO_3_naming)
country_consolidated_deaths = pd.pivot_table(country_consolidated_deaths, index=['Country/Region'],values=deaths_columns,aggfunc='sum').reset_index()
country_consolidated_deaths = country_consolidated_deaths.merge(country_codes, how='left', on='Country/Region')

def transpose_data(cases, deaths, country_name, iso):
    return_df = cases[cases['Country/Region'] == country_name].transpose().reset_index()
    return_df['Country/Region'] = country_name
    return_df['alpha-3'] = iso
    return_df.drop(return_df.tail(1).index,inplace=True)
    return_df.drop(return_df.head(1).index,inplace=True)
    return_df = return_df.rename(columns={'index':'Date',
                                          cases.index[cases['Country/Region'] == country_name][0]:'Confirmed Cases'})
    return_df = return_df.reset_index(drop=True)
    temp_deaths = deaths[deaths['Country/Region'] == country_name].transpose().iloc[4:].reset_index()
    temp_deaths = temp_deaths.rename(columns={'index': 'Date',
                                              deaths.index[deaths['Country/Region'] == country_name][0]: 'Deaths'})
    return_df = return_df.merge(temp_deaths, how='left', on='Date')
    return_df = return_df[['Date', 'Country/Region', 'alpha-3', 'Confirmed Cases', 'Deaths']]
    return_df['Date'] = pd.to_datetime(return_df['Date'])
    return_df = return_df.sort_values('Date')
    return_df['Date'] = return_df['Date'].dt.strftime('%Y-%m-%d')
    return_df['Case Growth'] = return_df['Confirmed Cases'].diff(periods=1)
    return_df['Death Growth'] = return_df['Deaths'].diff(periods=1)
    return_df = return_df.fillna(0)
    return(return_df)

transposed_df = pd.DataFrame()
for i in range(0, len(country_consolidated_cases)):
    temp_df = transpose_data(country_consolidated_cases,
                             country_consolidated_deaths,
                             country_consolidated_cases['Country/Region'][i],
                             country_consolidated_cases['alpha-3'][i])
    transposed_df = transposed_df.append(temp_df, ignore_index=True)

deaths_to_chart = transposed_df[transposed_df['Date'] != '2020-01-22']
deaths_to_chart = deaths_to_chart[deaths_to_chart['Date'] != '2020-01-23']
deaths_to_chart = deaths_to_chart[deaths_to_chart['Date'] != '2020-01-24']
deaths_to_chart = deaths_to_chart.reset_index(drop=True)
death_growth_to_chart = deaths_to_chart[deaths_to_chart['Date'] != '2020-01-25']
death_growth_to_chart = death_growth_to_chart.reset_index(drop=True)
case_growth_to_chart = transposed_df[transposed_df['Date'] != '2020-01-22']
case_growth_to_chart = case_growth_to_chart.reset_index(drop=True)

fig = px.choropleth_mapbox(transposed_df,
                           geojson=countries_json,
                           locations="alpha-3",
                           color="Confirmed Cases",
                           hover_name="Country/Region",
                           mapbox_style="carto-positron",
                           animation_frame="Date",
                           color_continuous_scale="reds",
                           zoom=3,
                           opacity=0.75,
                           title='COVID-19 Cumulative Cases')

pio.write_html(fig, file='~/COVID-19 projects/chloropleth map/Cumulative Cases COVID19.html', auto_open=True)