from os import system, walk, path
from os import walk

dir_path = path.dirname(path.abspath(__file__))
dirs, files = next(walk(dir_path), (None, [], []))[-2:]

assert 'manage.py' in files, 'Файл manage.py не обнаружен'

manage_com = f'python "{path.join(dir_path, 'manage.py')}"'
system('pytest')
commands = ['test', 'makemigrations', 'migrate', 'runserver']
list(map(lambda x: system(manage_com + x), commands))
