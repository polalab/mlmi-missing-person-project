def format_minutes(minutes):
    days = minutes // (24 * 60)
    hours = (minutes % (24 * 60)) // 60
    mins = minutes % 60
    return f"{int(days)}d {int(hours)}h {int(mins)}m"