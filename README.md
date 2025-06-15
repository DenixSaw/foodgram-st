1. В корневой папке проекта создать файл .env
   Cо следующим содержимым:

```
#Django
HOSTNAME=
SECRET_KEY=
DEBUG=
ALLOWED_HOSTS=

#DB
DB_ENGINE=
DB_NAME=
POSTGRES_USER=
POSTGRES_PASSWORD=
DB_HOST=
DB_PORT=
```

2. Далее нужно выпонлить команду

```
docker-compose up --build
```

3. В рузльтате будут подняты 4 контейнера:

- db - контейнер с базой данных
- nginx - контейнер для проксирование запросов на бекенд
- backend - контейнер с джангой
- frontend - контейнер необходим, чтобы собрать статику. После сбора статики завершает свою работу