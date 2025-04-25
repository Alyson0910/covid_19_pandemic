import pandas as pd
import sqlite3

class CreateCovid19DB:
    def create_time_series(self):
        confirmed = pd.read_csv("data/time_series_covid19_confirmed_global.csv")
        deaths = pd.read_csv("data/time_series_covid19_deaths_global.csv")
        vaccine = pd.read_csv("data/time_series_covid19_vaccine_global.csv")
        # print(daily_report.columns)
        # print(daily_report.head().dtypes, "\n", confirmed.head().dtypes, "\n", deaths.head().dtypes, "\n", vaccine.head().dtypes)
        id_variable = ["Province/State", "Country/Region", "Lat", "Long"]
        confirmed_melted = pd.melt(confirmed, id_vars=id_variable, var_name="Date", value_name="Confirmed")
        deaths_melted = pd.melt(deaths, id_vars=id_variable, var_name="Date", value_name="Deaths")
        confirmed_melted["Date"] = pd.to_datetime(confirmed_melted["Date"], format="%m/%d/%y")
        deaths_melted["Date"] = pd.to_datetime(deaths_melted["Date"], format="%m/%d/%y")
        # print(confirmed_melted.columns)
        # print(confirmed_melted.head().dtypes,"\n",deaths_melted.head().dtypes)
        vaccine["Province_State"] = vaccine["Province_State"].astype(object)
        vaccine["Date"] = pd.to_datetime(vaccine["Date"])
        vaccine = vaccine.rename(columns={"Province_State":"Province/State", 
                                        "Country_Region":"Country/Region"})
        # print(vaccine.dtypes)
        confirmed_melted = confirmed_melted.drop(labels=["Lat", "Long"], axis=1)
        deaths_melted = deaths_melted.drop(labels=["Lat", "Long"], axis=1)
        vaccine = vaccine.drop(labels=["UID", "People_at_least_one_dose"], axis=1)
        join_keys = ["Province/State", "Country/Region", "Date"]
        time_series = pd.merge(confirmed_melted, deaths_melted, left_on=join_keys, right_on=join_keys, how="left")
        time_series = pd.merge(time_series, vaccine, left_on=join_keys, right_on=join_keys, how="left")
        # print(time_series)
        time_series = time_series.drop(labels="Province/State", axis=1)
        time_series = time_series.groupby(["Country/Region", "Date"])[["Confirmed", "Deaths", "Doses_admin"]].sum().reset_index()
        # print(time_series)
        time_series.columns = ["country", "reported_on", "confirmed", "deaths", "doses_administered"]
        time_series["doses_administered"] = time_series["doses_administered"].astype(int)
        return time_series
    
    def create_daily_report(self):
        daily_report = pd.read_csv("data/03-09-2023.csv")
        daily_report = daily_report[["Country_Region", "Province_State", "Admin2", "Confirmed", "Deaths", "Lat", "Long_"]]
        daily_report.columns = ["country", "province", "county", "confirmed", "deaths", "latitude", "longitude"]
        return daily_report
    
    def create_database(self):
        connection = sqlite3.connect("data/covid_19.db")
        time_series = self.create_time_series()
        time_series["reported_on"] = time_series["reported_on"].map(lambda x : x.strftime("%Y-%m-%d"))
        daily_report = self.create_daily_report()
        d_dict = {
            "time_series":time_series,
            "daily_report":daily_report
            }
        for k, v in d_dict.items():
            v.to_sql(k, con=connection, if_exists="replace", index=False)
        connection.close()

create_covid_19_db = CreateCovid19DB()
create_covid_19_db.create_database()
