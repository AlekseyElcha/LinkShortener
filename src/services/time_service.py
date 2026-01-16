from datetime import datetime
import pytz


def convert_utc_string_to_local(utc_time_str: str, target_timezone: str) -> str:
    try:
        naive_dt = datetime.strptime(utc_time_str, "%Y-%m-%d %H:%M:%S")

        utc_dt = pytz.UTC.localize(naive_dt)
        target_tz = pytz.timezone(target_timezone)
        local_dt = utc_dt.astimezone(target_tz)

        return local_dt.strftime("%Y-%m-%d %H:%M:%S")

    except Exception as e:
        return utc_time_str


