# Conference Room Booking System

Система бронирования конференц-залов Головного офиса.

Подготовлены Django-проект `config`, приложения `accounts`, `rooms`, `bookings`,
`audit`, модели Room, Equipment, Booking, AuditLog и их миграции.
Интерфейс, авторизация пользователей и маршруты приложений пока не реализованы.

## Стек

- Python 3.12
- Django 5.2 LTS
- PostgreSQL (в Docker Compose — версия 17)
- Django Templates
- HTMX — предусмотрен стеком; подключение будет при разработке интерфейса
- Git и GitHub
- Docker / Docker Compose
- pytest / pytest-django
- ruff
- `requirements.txt` для зависимостей
- `.env` и python-dotenv для конфигурации

Прямые зависимости зафиксированы в `requirements.txt`. Обновления выполняйте
осознанно, с повторным запуском проверок; Django остаётся в ветке 5.2 LTS.

## Настройка окружения

Команды ниже выполняются из корня проекта в PowerShell.
Нужны Python 3.12 и Docker с Compose либо отдельно установленный PostgreSQL.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Копируйте `.env.example` только при первом запуске: не перезаписывайте уже
заполненный `.env`. Активация виртуального окружения не обязательна.

Откройте `.env` и заполните `SECRET_KEY` и `DB_PASSWORD` своими значениями.
Готовых секретов в репозитории нет. Для генерации ключа локально:

```powershell
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Вставьте сгенерированный ключ в `.env` в одинарных кавычках. Пароль также
заключите в одинарные кавычки, если в нём есть специальные символы.
Не отправляйте `.env` в GitHub. Переменные окружения процесса имеют приоритет
над `.env`. Без `SECRET_KEY` Django выдаёт понятную ошибку конфигурации.

`DEBUG` принимает `True`, `False`, `1`, `0`; без переменной используется `False`.
`ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS` — списки через запятую.
Для локального запуска оставьте значения из примера. Часовой пояс по умолчанию
`UTC`; нужное значение задаётся через `TIME_ZONE`.

## Первый запуск с PostgreSQL в Docker

После заполнения `.env`:

```powershell
docker compose up -d db
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('PostgreSQL connection OK')"
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Откройте <http://127.0.0.1:8000/>. При `DEBUG=True` и пустом списке маршрутов
Django показывает стандартную страницу успешной установки. Это не интерфейс
системы. При `DEBUG=False` пустые маршруты возвращают 404.

Если PostgreSQL уже установлен отдельно, создайте пустую БД и пользователя
с правами на неё, укажите параметры `DB_*` в `.env` и пропустите команду Docker.
Миграции уже созданы: выполните `migrate` для их применения. Миграция
`bookings/0001_btree_gist.py` активирует расширение `btree_gist` до создания
ограничения пересечений. PostgreSQL должен поддерживать это расширение,
а пользователь БД — иметь право его установить (или оно уже установлено).

## Запуск всего проекта в Docker

Python на компьютере для этого варианта не нужен. Скопируйте `.env.example`
в `.env` и самостоятельно задайте ключ и пароль. Затем:

```powershell
docker compose up --build
```

В другом терминале примените миграции:

```powershell
docker compose exec web python manage.py migrate
```

Веб-сервис дождётся готовности PostgreSQL. В контейнере адрес БД автоматически
меняется на `db:5432`. Приложение доступно по <http://127.0.0.1:8000/>.

```powershell
docker compose down
```

Эта команда сохраняет данные PostgreSQL в именованном томе. Начальные параметры
БД применяются образом PostgreSQL только при создании пустого тома: изменение
пароля в `.env` не меняет пароль уже созданного пользователя БД.
Dockerfile и Compose предназначены для разработки и используют `runserver`.
Конфигурация промышленного развёртывания в этот этап не входит.

## Проверки

После заполнения `.env`:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

По умолчанию выполняются тесты конфигурации, HTTP-ответа и модельной валидации
без БД. Интеграционные тесты помечены `postgres` и явно пропускаются.
Полный набор запускается только с работающим PostgreSQL:

```powershell
.\.venv\Scripts\python.exe -m pytest --postgres -ra
```

pytest-django создаёт отдельную тестовую БД и применяет к ней миграции.
Пользователю нужны права создания тестовой БД и установки `btree_gist`.
При `--postgres` ошибки подключения не скрываются и тесты не пропускаются.
`manage.py check` сам по себе также не подтверждает подключение к БД:
для этого используйте отдельную команду `connection.ensure_connection()` выше.

## Модели и ограничения

Room содержит этаж и вместимость, Equipment связан с залом через `room.equipment`.
Удаление зала каскадно удаляет оборудование, но запрещено при наличии броней
(`Booking.room` использует `PROTECT`). AuditLog допускает системные события без
пользователя; удаление пользователя сохраняет журнал через `SET_NULL`.

`Booking.clean()` проверяет время, активность зала и число участников.
Как обычно в Django, `save()` не вызывает `full_clean()` автоматически:
перед сохранением из будущего кода нужно явно выполнять `full_clean()`.
Проверки активности и вместимости находятся на уровне модели.

БД независимо проверяет положительную вместимость/число участников и
`end_at > start_at`. `booking_no_active_overlap` — PostgreSQL ExclusionConstraint:
одинаковый зал, пересекающийся `TSTZRANGE(start_at, end_at, '[)')`, статус `active`.
Брони встык разрешены, отменённые брони не блокируют интервал. Проверка в Python
не подменяет ограничение БД. Регистрация моделей в admin базовая, URL admin пока
не подключён; кастомного User и автоматической записи AuditLog нет.

## Git workflow

- `main` — стабильная версия.
- `develop` — основная ветка разработки.
- `feature/название-задачи` — отдельная ветка для новой задачи, создаётся от `develop`.

Схема изменений: `feature/... → develop → main`.
Задачи объединяются с `develop` через Pull Request. Готовые изменения из
`develop` попадают в `main` через Pull Request после успешного CI.
Пример начала задачи:

```powershell
git switch develop
git pull --ff-only
git switch -c feature/task-name
```

После первой публикации настройте на GitHub защиту `main`: обязательный Pull
Request и успешная проверка `Python checks` перед слиянием. Сам workflow не
запрещает прямой push — это обеспечивается правилами защиты ветки в GitHub.

### Первый коммит и подключение GitHub

Локальная ветка уже переименована из `master` в `main`. Коммитов пока нет,
remote не задан; публикация не выполнялась. Создайте первый коммит:

```powershell
git add .github/workflows/ci.yml .gitignore .dockerignore .env.example README.md requirements.txt manage.py config accounts rooms bookings audit tests conftest.py pytest.ini ruff.toml Dockerfile compose.yaml
git diff --cached
git commit -m "Initialize Django project foundation"
```

Создайте пустой репозиторий GitHub без автоматически добавленных README и
`.gitignore`, затем вставьте его URL вместо `<URL_ВАШЕГО_РЕПОЗИТОРИЯ>`:

```powershell
git remote add origin "<URL_ВАШЕГО_РЕПОЗИТОРИЯ>"
git push -u origin main
git switch -c develop
git push -u origin develop
```

Существующий документ с вопросами заказчику сохранён. Он не входит в приведённый
список файлов для первого коммита. Новые этапы разработки добавляются отдельно.

## CI в GitHub Actions

Workflow `.github/workflows/ci.yml` запускается для Pull Request в `main` и
`develop`, а также при push в `develop`. На Python 3.12 устанавливаются
зависимости из `requirements.txt`, затем выполняются:

```text
ruff check .
ruff format --check .
pytest
python manage.py check
```

CI использует открытые тестовые переменные из workflow, без настоящих секретов
и без файла `.env`. Текущий workflow выполняет только проверки без БД;
интеграционные тесты PostgreSQL пропускаются. Их автоматический запуск потребует
отдельного добавления PostgreSQL service и флага `--postgres` в CI.
В шаге 1.6 workflow не изменялся. Первый push в `main` этот workflow не запускает;
первый push в `develop` запустит проверки.
