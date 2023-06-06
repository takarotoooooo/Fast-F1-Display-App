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


def drivers(year):
    pkl_file = f"/app/data/{year}/drivers.zip"

    if os.path.isfile(pkl_file):
        return pd.read_pickle(pkl_file)

    column_names = [
        'DriverNumber',
        'Abbreviation',
        'FullName',
        'CountryCode']

    drivers_pd = results(year) \
        .groupby(column_names) \
        .nunique().reset_index()[column_names + ['EventName']] \
        .rename(columns={'EventName': 'RaceCount'})

    os.makedirs(f"/app/data/{year}", exist_ok=True)
    drivers_pd.to_pickle(pkl_file)

    return drivers_pd


def teams(year):
    pkl_file = f"/app/data/{year}/teams.zip"

    if os.path.isfile(pkl_file):
        return pd.read_pickle(pkl_file)

    column_names = ['TeamName', 'TeamColor']

    teams_pd = results(year) \
        .groupby(column_names) \
        .nunique().reset_index()[column_names + ['EventName']] \
        .rename(columns={'EventName': 'RaceCount'})

    os.makedirs(f"/app/data/{year}", exist_ok=True)
    teams_pd.to_pickle(pkl_file)

    return teams_pd


def team_drivers(year):
    pkl_file = f"/app/data/{year}/team_drivers.zip"

    if os.path.isfile(pkl_file):
        return pd.read_pickle(pkl_file)

    column_names = ['TeamName', 'DriverNumber', 'Abbreviation']

    team_drivers_pd = results(year) \
        .groupby(column_names) \
        .nunique().reset_index()[column_names + ['EventName']] \
        .rename(columns={'EventName': 'RaceCount'})

    os.makedirs(f"/app/data/{year}", exist_ok=True)
    team_drivers_pd.to_pickle(pkl_file)

    return team_drivers_pd


def races(year):
    event_schedule = fastf1.get_event_schedule(year)
    events = {
        'RoundNumber': [],
        'OfficialEventName': [],
        'Country': [],
        'Location': [],
        'Date': []
    }
    for record in event_schedule.to_dict('records'):
        try:
            event = event_schedule.get_event_by_round(record['RoundNumber'])
        except ValueError:
            continue

        race_session = event.get_race()
        events['RoundNumber'].append(record['RoundNumber'])
        events['OfficialEventName'].append(record['OfficialEventName'])
        events['Country'].append(record['Country'])
        events['Location'].append(record['Location'])
        events['Date'].append(race_session.date)

    return pd.DataFrame(events)
