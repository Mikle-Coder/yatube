import datetime as dt


def year(request):
    """
    Добавляет переменную с текущим годом.
    """
    cur_year = dt.datetime.now().year
    return {'year' : cur_year}