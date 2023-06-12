import fastf1
import pandas as pd
import os


def available_years():
    return (
        2023,
        2022,
        2021,
        2020,
        2019
    )


def results(year, use_cache=True):
    pkl_file = f"/app/data/{year}/results.zip"
    if os.path.isfile(pkl_file) and use_cache:
        return pd.read_pickle(pkl_file)

    event_schedule = fastf1.get_event_schedule(year)
    max_round_number = event_schedule['RoundNumber'].max()
    results_pd = None
    for round_number in range(max_round_number):
        event = event_schedule.get_event_by_round(round_number + 1)
        race_session = event.get_race()
        try:
            race_session.load(
                laps=False,
                telemetry=False,
                weather=False,
                messages=False)
        except fastf1.core.DataNotLoadedError:
            continue

        p = pd.DataFrame(race_session.results).query('Abbreviation != "nan"')
        p['RoundNumber'] = event['RoundNumber']
        p['EventName'] = event['EventName']
        if results_pd is None:
            results_pd = p
        else:
            results_pd = pd.concat([results_pd, p])
    os.makedirs(f"/app/data/{year}", exist_ok=True)
    results_pd.to_pickle(f"/app/data/{year}/results.zip")

    return results_pd


def drivers(year, use_cache=True):
    pkl_file = f"/app/data/{year}/drivers.zip"

    if os.path.isfile(pkl_file) and use_cache:
        return pd.read_pickle(pkl_file)

    driver_columns = [
        'DriverNumber',
        'Abbreviation',
        'FullName',
        'CountryCode']

    drivers_pd = results(year).groupby(driver_columns).agg({
        'HeadshotUrl': 'max',
        'TeamName': pd.Series.unique,
        'EventName': pd.Series.nunique,
        'Points': 'sum'
    }).reset_index().rename(columns={
        'TeamName': 'Teams',
        'EventName': 'RaceCount',
        'Points': 'TotalPoint'
    })

    os.makedirs(f"/app/data/{year}", exist_ok=True)
    drivers_pd.to_pickle(pkl_file)

    return drivers_pd


def teams(year, use_cache=True):
    pkl_file = f"/app/data/{year}/teams.zip"

    if os.path.isfile(pkl_file) and use_cache:
        return pd.read_pickle(pkl_file)

    team_columns = ['TeamName', 'TeamColor']
    teams_pd = results(year).groupby(team_columns).agg({
        'Abbreviation': pd.Series.unique,
        'EventName': pd.Series.nunique,
        'Points': 'sum'
    }).reset_index().rename(columns={
        'Abbreviation': 'Drivers',
        'EventName': 'RaceCount',
        'Points': 'TotalPoint'
    })

    os.makedirs(f"/app/data/{year}", exist_ok=True)
    teams_pd.to_pickle(pkl_file)

    return teams_pd


def team_drivers(year, use_cache=True):
    pkl_file = f"/app/data/{year}/team_drivers.zip"

    if os.path.isfile(pkl_file) and use_cache:
        return pd.read_pickle(pkl_file)

    team_driver_columns = [
        'DriverNumber',
        'Abbreviation',
        'FullName',
        'CountryCode',
        'TeamName',
        'TeamColor']

    team_drivers_pd = results(year).groupby(team_driver_columns).agg({
        'HeadshotUrl': 'max',
        'EventName': pd.Series.nunique,
        'Points': 'sum'
    }).reset_index().rename(columns={
        'EventName': 'RaceCount',
        'Points': 'TotalPoint'
    })

    os.makedirs(f"/app/data/{year}", exist_ok=True)
    team_drivers_pd.to_pickle(pkl_file)

    return team_drivers_pd


def races(year, use_cache=True):
    pkl_file = f"/app/data/{year}/races.zip"

    if os.path.isfile(pkl_file) and use_cache:
        return pd.read_pickle(pkl_file)

    event_schedule = fastf1.get_event_schedule(year)
    events = {
        'RoundNumber': [],
        'OfficialEventName': [],
        'EventName': [],
        'Country': [],
        'Location': [],
        'RaceDate': []
    }
    for record in event_schedule.to_dict('records'):
        try:
            event = event_schedule.get_event_by_round(record['RoundNumber'])
        except ValueError:
            continue

        race_session = event.get_race()
        events['RoundNumber'].append(record['RoundNumber'])
        events['OfficialEventName'].append(event['OfficialEventName'])
        events['EventName'].append(event[('EventName')])
        events['Country'].append(record['Country'])
        events['Location'].append(record['Location'])
        events['RaceDate'].append(race_session.date)

    races_pd = pd.DataFrame(events)
    os.makedirs(f"/app/data/{year}", exist_ok=True)
    races_pd.to_pickle(pkl_file)

    return races_pd
