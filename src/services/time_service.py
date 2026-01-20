from datetime import datetime
import pytz


def convert_utc_string_to_local(utc_time_str: str, target_timezone: str) -> str:
    try:
        if '.' in utc_time_str:
            utc_time_str = utc_time_str.split('.')[0]

        naive_dt = datetime.strptime(utc_time_str, "%Y-%m-%d %H:%M:%S")

        utc_dt = pytz.UTC.localize(naive_dt)
        target_tz = pytz.timezone(target_timezone)
        local_dt = utc_dt.astimezone(target_tz)

        return local_dt.strftime("%Y-%m-%d %H:%M:%S")

    except Exception as e:
        print(f"Error: {e}")
        return utc_time_str


def convert_local_str_to_utc(local_time_str: str, local_timezone: str) -> str:
    naive_dt = datetime.strptime(local_time_str, "%Y-%m-%d %H:%M")
    local_tz = pytz.timezone(local_timezone)
    local_dt = local_tz.localize(naive_dt)
    utc_dt = local_dt.astimezone(pytz.UTC)
    return utc_dt.strftime("%Y-%m-%d %H:%M")



