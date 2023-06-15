import fastf1
import pandas as pd
import os


def available_years():
    """
    利用可能な年を返却する

    Returns
    -------
    list
        利用可能な年の配列
    """
    return (
        2023,
        2022,
        2021,
        2020,
        2019
    )


def events(year: int) -> list[fastf1.events.Event]:
    """
    指定したシーズンのイベントを配列で取得する

    Parameters
    ----------
    year : int
        取得したいシーズン年

    Returns
    -------
    list[fastf1.events.Event]
        イベントの配列
    """
    event_schedule = fastf1.get_event_schedule(year)
    max_round_number = event_schedule['RoundNumber'].max()
    return [
        event_schedule.get_event_by_round(round_number + 1)
        for round_number in range(max_round_number)]


def season_results_df(year: int, use_cache: bool = True) -> pd.DataFrame:
    """
    指定したシーズンのレース結果を取得する

    Parameters
    ----------
    year: int
        取得したいシーズン年
    use_cache: bool
        キャッシュ利用するか。デフォルトはTrue

    Returns
    -------
    results: pandas.DataFrame
        指定した年の全レース全ドライバーのレース結果

        - DriverNumber : object
        - BroadcastName : object
        - Abbreviation : object
        - DriverId : object
        - TeamName : object
        - TeamColor : object
        - TeamId : object
        - FirstName : object
        - LastName : object
        - FullName : object
        - HeadshotUrl : object
        - CountryCode : object
        - Position : float64
        - ClassifiedPosition : object
        - GridPosition : float64
        - Q1 : timedelta64[ns]
        - Q2 : timedelta64[ns]
        - Q3 : timedelta64[ns]
        - Time : timedelta64[ns]
        - Status : object
        - Points : float64
        - RoundNumber : int64
        - OfficialEventName : object
        - EventName : object
        - Country : object
        - Location : object
        - RaceStartDate : datetime64[ns]

    Raises
    -------
    ValueError
        指定したyearが範囲外
    TypeError
        指定したyearの型が不正
    """

    pkl_file = f"/app/data/{year}/season_results.zip"
    if os.path.isfile(pkl_file) and use_cache:
        return pd.read_pickle(pkl_file)

    results_pd = None
    for event in events(year):
        race_session = event.get_race()
        try:
            race_session.load(
                laps=True,
                telemetry=False,
                weather=False,
                messages=False)
        except fastf1.core.DataNotLoadedError:
            continue

        race_results = pd.DataFrame(race_session.results.query('Abbreviation != "nan"'))
        race_results['RoundNumber'] = event['RoundNumber']
        race_results['OfficialEventName'] = event['OfficialEventName']
        race_results['EventName'] = event['EventName']
        race_results['Country'] = event['Country']
        race_results['Location'] = event['Location']
        race_results['RaceStartDate'] = race_session.date
        race_results['TotalLaps'] = race_session.total_laps

        if results_pd is None:
            results_pd = race_results
        else:
            results_pd = pd.concat([results_pd, race_results])

    os.makedirs(f"/app/data/{year}", exist_ok=True)
    results_pd.to_pickle(pkl_file)

    return results_pd[[
        'DriverNumber',
        'BroadcastName',
        'Abbreviation',
        'DriverId',
        'TeamName',
        'TeamColor',
        'TeamId',
        'FirstName',
        'LastName',
        'FullName',
        'HeadshotUrl',
        'CountryCode',
        'Position',
        'ClassifiedPosition',
        'GridPosition',
        'Q1',
        'Q2',
        'Q3',
        'Time',
        'Status',
        'Points',
        'RoundNumber',
        'OfficialEventName',
        'EventName',
        'Country',
        'Location',
        'RaceStartDate'
    ]]


def season_teams_df(year: int, use_cache: bool = True) -> pd.DataFrame:
    """
    指定したシーズンのチームリストを取得する

    Parameters
    ----------
    year: int
        取得したいシーズン年
    use_cache: bool
        キャッシュ利用するか。デフォルトはTrue

    Returns
    -------
    pd.DataFrame
        指定した年の参加チームリスト

        - TeamName | object
        - TeamColor | object
        - Drivers | object
        - RaceCount | int64
        - TotalPoint | float64
    """
    pkl_file = f"/app/data/{year}/season_teams.zip"

    if os.path.isfile(pkl_file) and use_cache:
        return pd.read_pickle(pkl_file)

    team_columns = ['TeamName', 'TeamColor']
    teams_pd = season_results_df(year).groupby(team_columns).agg({
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

    return teams_pd[team_columns + ['Drivers', 'RaceCount', 'TotalPoint']]


def season_drivers_df(year: int, use_cache: bool = True) -> pd.DataFrame:
    """
    指定したシーズンのドライバーリストを取得する

    Parameters
    ----------
    year: int
        取得したいシーズン年
    use_cache: bool
        キャッシュ利用するか。デフォルトはTrue

    Returns
    -------
    pd.DataFrame
        シーズン内のドライバーリスト

        - DriverNumber : object
        - Abbreviation : object
        - FullName : object
        - CountryCode : object
        - Teams : object
        - RaceCount : int64
        - TotalPoint : float64
    """
    pkl_file = f"/app/data/{year}/season_drivers.zip"

    if os.path.isfile(pkl_file) and use_cache:
        return pd.read_pickle(pkl_file)

    driver_columns = [
        'DriverNumber',
        'Abbreviation',
        'FullName',
        'CountryCode']

    drivers_pd = season_results_df(year).groupby(driver_columns).agg({
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

    return drivers_pd[driver_columns + ['Teams', 'RaceCount', 'TotalPoint']]


def season_races_df(year: int, use_cache: bool = True) -> pd.DataFrame:
    """
    指定したシーズンのレースリストを取得する

    Parameters
    ----------
    year: int
        取得したいシーズン年
    use_cache: bool
        キャッシュ利用するか。デフォルトはTrue

    Returns
    -------
    pd.DataFrame
        指定した年のレースリスト

        - RoundNumber : int64
        - OfficialEventName : object
        - EventName : object
        - Country : object
        - Location : object
        - RaceStartDate : datetime64[ns]
        - TotalLaps : int64
        - DriverCount : int64
        - TeamCount : int64
    """
    pkl_file = f"/app/data/{year}/season_races.zip"

    if os.path.isfile(pkl_file) and use_cache:
        return pd.read_pickle(pkl_file)

    race_columns = [
        'RoundNumber',
        'OfficialEventName',
        'EventName',
        'Country',
        'Location',
        'RaceStartDate',
        'TotalLaps']

    races_pd = season_results_df(year).groupby(race_columns).agg({
        'Abbreviation': pd.Series.nunique,
        'TeamName': pd.Series.nunique
    }).reset_index().rename(columns={
        'Abbreviation': 'DriverCount',
        'TeamName': 'TeamCount'
    })

    os.makedirs(f"/app/data/{year}", exist_ok=True)
    races_pd.to_pickle(pkl_file)

    return races_pd[race_columns + ['DriverCount', 'TeamCount']]
