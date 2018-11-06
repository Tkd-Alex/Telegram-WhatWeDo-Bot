import locale, calendar, datetime
from pointers import time_pointers, day_transformers

class DayManager():
    calendar.setfirstweekday(calendar.MONDAY)
    locale.setlocale(locale.LC_ALL, 'it_IT.utf8')

    def __init__(self):
        self.week_days = list( calendar.day_name )

    def get_day(self, day=None, index=None):
        if day != None:
            return self.week_days[ (datetime.datetime.now() + datetime.timedelta( days=day_transformers[day] )).weekday() ]
        elif index != None:
            return self.week_days[index]
        return None

    def get_today(self):
        return self.week_days[datetime.datetime.now().weekday()]   

    def day_to_add(self, _datetime, day):
        if _datetime.weekday() == 0:
            return self.week_days.index(day)
        elif _datetime.weekday() == 6:
            return self.week_days.index(day) + 1
        else:
            if self.week_days.index(day) <= _datetime.weekday():
                return 5 + self.week_days.index(day)
            else:
                return self.week_days.index(day) - _datetime.weekday()
    
    def add_day(self, day=1):
        return datetime.datetime.now() + datetime.timedelta( days=day ) 

    def get_close_pool(self, _datetime=datetime.datetime.now(), hour=0, day=0):
        return datetime.datetime( _datetime.year, _datetime.month, _datetime.day, hour )
    
    def is_day(self, word):
        for index in range(0, len(self.week_days)):
            if word.startswith( self.week_days[index][:len(self.week_days)-1] ):
                return index
        return -1
    
