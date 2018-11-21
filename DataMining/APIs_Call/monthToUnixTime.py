# avg out 1st aug 2017 to 1st aug 2018 per month
import math, calendar, time, requests
from datetime import datetime

def genDateTimeTuple():
    return [calendar.timegm(datetime(2017,i,1,0,0,0,0).timetuple()) if i <= 12 else calendar.timegm(datetime(2018,i-12,1,0,0,0,0).timetuple()) for i in range(8,20)]
    
def genSQL():
    sql = "SELECT Count(DISTINCT match)"