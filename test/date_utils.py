from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


class DateUtils:
  def __init__(self, date_str):
    self.date = datetime.strptime(date_str, "%Y-%m-%d")

  def future(self, days: int) -> str:
    return (self.date + timedelta(days=days)).strftime("%Y-%m-%d")