from datetime import datetime

def get_current_time_string(format_type):
    now = datetime.now()
    formats = {
        "24h | MM/DD/YYYY": "%H:%M:%S | %m/%d/%Y",
        "24h | Month DD, YY": "%H:%M:%S | %B %d, %y",
        "12h | MM/DD/YYYY": "%I:%M:%S %p | %m/%d/%Y",
        "12h | Month DD, YY": "%I:%M:%S %p | %B %d, %y"
    }
    return now.strftime(formats.get(format_type, formats["24h | MM/DD/YYYY"]))