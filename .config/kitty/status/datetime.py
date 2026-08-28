from datetime import datetime


def status():
    now = datetime.now()
    return {'date': now.strftime('%d %b %Y'), 'time': now.strftime('%H:%M')}
