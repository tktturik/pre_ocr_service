# RUNBOOK

## Подготовка

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt          # сервис
pip install -r requirements-dev.txt      # тесты и линтеры
cp .env.example .env
```

## Запуск локально

Из корня репозитория:

```bash
python src/main.py
```

Сервис слушает `http://localhost:8000`. Пул воркеров прогревается на старте (до `ANALYSIS_WARMUP_TIMEOUT_S`, по умолчанию 30 с). Готовность: `GET /health` отвечает `204`.

## Запуск в Docker

```bash
docker compose up --build -d
docker compose down
```

Файл `.env` обязателен: compose читает его через `env_file`. Порт `8000` проброшен на хост.

## Проверка работы

Готовность:

```bash
curl -i localhost:8000/health
```

Ожидается `HTTP/1.1 204 No Content`.

Список проверок:

```bash
curl localhost:8000/checks
```

```json
{"checks": ["resolution", "blur", "contrast", "illumination", "noise", "skew"]}
```

Анализ файла. Тело запроса - сырые байты файла, формат определяется по сигнатуре (PNG, JPEG, PDF). Параметр `checks` обязателен, имена через запятую:

```bash
curl -s -X POST "localhost:8000/analyze?checks=resolution,blur,contrast,illumination,noise,skew" \
  --data-binary @<путь к файлу из датасета>
```

Тот же запрос подходит и для изображения, и для PDF; для PDF в `items` по элементу на страницу.

Пример ответа `200` (значения условные):

```json
{
  "suitable_for_ocr": true,
  "quality_score": 0.91,
  "processing_time_ms": 120,
  "items": [
    {
      "index": 0,
      "suitable_for_ocr": true,
      "quality_score": 0.91,
      "checks": {
        "resolution": {"passed": true, "score": 1.0},
        "blur": {"passed": true, "score": 0.9}
      }
    }
  ]
}
```

Поля `passed`, `score` и оценки могут быть `null` — «не определено».

Пример ошибки: неизвестная проверка.

```bash
curl -i -X POST "localhost:8000/analyze?checks=foo" --data-binary @<путь к файлу из датасета>
```

```json
{
  "code": "unknown_checks",
  "request_id": "<id запроса>",
  "details": {"unknown": ["foo"], "available": ["resolution", "blur", "contrast", "illumination", "noise", "skew"]}
}
```

## Тесты

```bash
pytest tests/unit                       # без пула процессов
pytest tests/integrations tests/e2e     # реальный пул процессов
pytest
```

e2e используют файлы из каталога `tests/templates/`.

## Настройки

Переменные читаются из окружения и из `.env`.

| Переменная | По умолчанию | Смысл |
|------------|--------------|-------|
| `ANALYSIS_MAX_FILE_BYTES` | 52428800 (50 МиБ) | максимальный размер тела запроса |
| `ANALYSIS_MAX_RASTER_PIXELS` | 40000000 | максимум пикселей одного изображения |
| `ANALYSIS_MAX_PDF_PAGES` | 100 | максимум страниц PDF |
| `ANALYSIS_PDF_FALLBACK_DPI` | 300 | DPI рендера страницы PDF |
| `ANALYSIS_POOL_SIZE` | число CPU, доступных процессу | число воркеров N |
| `ANALYSIS_QUEUE_SIZE` | равен N | сколько запросов ждёт сверх N занятых воркеров (M) |
| `ANALYSIS_TASK_TIMEOUT_S` | 60 | таймаут одного анализа, по истечении 504 |
| `ANALYSIS_WARMUP_TIMEOUT_S` | 30 | таймаут прогрева пула на старте |
| `ANALYSIS_MAX_TASKS_PER_WORKER` | 200 | число задач, после которого воркер перезапускается |
| `ANALYSIS_START_METHOD` | `spawn` | способ запуска процессов: `spawn` или `forkserver` |
| `LOG_LEVEL` | `DEBUG` | уровень логов |
| `HOST` | `0.0.0.0` | адрес, на котором слушает сервис |
| `PORT` | 8000 | порт сервиса |
