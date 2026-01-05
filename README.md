Анализирую проект на критические места для рефакторинга по принципам DRY и SOLID. Изучаю структуру и основные файлы.

[4 tools called]

Изучаю обработчики и сервисы:

[9 tools called]

Изучаю репозитории, модели и другие важные файлы:

[9 tools called]

Проверяю еще несколько файлов для полноты анализа:

[4 tools called]

## Критические места для рефакторинга

### 1. Нарушения DRY (Don't Repeat Yourself)

#### 1.1. Дублирование парсинга `callback_data`

Проблема: `callback.data.split(":", 1)[1]` или `callback.data.split(":")[1]` повторяется в 8+ местах.

Места:

- `handlers/journal.py:46, 86, 170`
- `handlers/goals.py:199, 256`
- `handlers/ratings.py:13, 32`
- `handlers/settings.py:149`

Решение: создать утилиту для парсинга:

```python
# utils/callback_parser.py
def parse_callback_data(callback_data: str, prefix: str) -> str:
    """Extract value from callback_data after prefix"""
    if not callback_data.startswith(f"{prefix}:"):
        raise ValueError(f"Invalid callback prefix: {prefix}")
    return callback_data.split(":", 1)[1]
```

#### 1.2. Дублирование логики обработки CallbackQuery и Message

Проблема: в `handlers/journal.py` функции `ask_location`, `ask_company`, `finish_log` дублируют логику для `CallbackQuery` и `Message`.

Места:

- `handlers/journal.py:26-39, 66-79, 104-163`

Решение: создать универсальную функцию-обертку:

```python
# utils/message_utils.py
async def send_or_edit(
    callback_or_message: CallbackQuery | Message,
    text: str,
    reply_markup=None,
    parse_mode=None
):
    """Send message or edit existing based on type"""
    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.message.edit_text(
            text, reply_markup=reply_markup, parse_mode=parse_mode
        )
    else:
        await callback_or_message.answer(
            text, reply_markup=reply_markup, parse_mode=parse_mode
        )
```

#### 1.3. Дублирование паттерна работы с сессиями БД

Проблема: во всех репозиториях повторяется `async with self.session_maker() as session: async with session.begin():`.

Места: все методы в `repositories/*.py`

Решение: создать базовый метод в `BaseRepository`:

```python
# repositories/base.py
async def _execute_in_transaction(self, func):
    """Execute function within database transaction"""
    async with self.session_maker() as session:
        async with session.begin():
            return await func(session)
```

#### 1.4. Дублирование проверки `session_maker`

Проблема: проверка `if not session_maker` есть в сервисах, хотя есть middleware.

Места:

- `services/analysis_service.py:70, 112`
- `services/ai_response_service.py:15`
- `services/scheduler.py:60`

Решение: убрать проверки из сервисов (middleware уже обрабатывает это) или использовать декоратор.

#### 1.5. Дублирование логики отправки уведомлений

Проблема: в `scheduler.py` дублируется логика отправки сообщений.

Места:

- `services/scheduler.py:10-26, 29-46`

Решение: создать единый сервис для уведомлений.

---

### 2. Нарушения SOLID

#### 2.1. Single Responsibility Principle (SRP)

Проблема 1: `analysis.py` — God Object

- Смешивает работу с Mistral API, построение промптов и бизнес-логику
- 297 строк, 4 разные функции с разными ответственностями

Места:

- `analysis.py:11-45` — анализ записей
- `analysis.py:47-79` — генерация вопросов
- `analysis.py:81-117` — брейншторм
- `analysis.py:120-296` — анализ списка целей

Решение: разделить на:

- `services/ai/mistral_client.py` — клиент API
- `services/ai/prompt_builder.py` — построение промптов
- `services/ai/analysis_service.py` — бизнес-логика анализа

Проблема 2: `handlers/journal.py` смешивает UI и бизнес-логику

- Обработка UI (строки 14-185)
- Бизнес-логика (строка 152 — вызов анализа)

Решение: вынести бизнес-логику в сервис:

```python
# services/journal_service.py
class JournalService:
    async def create_entry_and_analyze(self, user_id, emotion, location, company):
        # Создание записи + анализ
```

Проблема 3: `handlers/goals.py` содержит логику парсинга и форматирования

- Парсинг целей (строки 407-430)
- Форматирование ответа (строки 449-495)
- Разбиение длинных сообщений (строки 23-80)

Решение: вынести в отдельные утилиты/сервисы.

#### 2.2. Dependency Inversion Principle (DIP)

Проблема: прямая зависимость от `session_maker` и Mistral API

- Handlers зависят от конкретной реализации БД
- `analysis.py` напрямую использует `Mistral`
- Нет абстракций для работы с AI

Решение: создать интерфейсы:

```python
# interfaces/ai_client.py
class IAIClient(ABC):
    @abstractmethod
    async def analyze(self, text: str) -> str: ...

# interfaces/repositories.py
class IJournalRepository(ABC):
    @abstractmethod
    async def add_entry(self, ...): ...
```

#### 2.3. Open/Closed Principle (OCP)

Проблема 1: клавиатуры жестко закодированы

- `keyboards.py` — статические функции
- Сложно добавлять новые опции без изменения кода

Решение: использовать фабрики или билдеры:

```python
# keyboards/builders.py
class KeyboardBuilder:
    def add_emotion_button(self, emotion: str, callback: str):
        # ...
```

Проблема 2: хардкод часовых поясов

- `handlers/settings.py:12-22` — список захардкожен

Решение: вынести в конфигурацию.

---

### 3. Архитектурные проблемы

#### 3.1. Отсутствие слоя сервисов для бизнес-логики

Проблема: бизнес-логика разбросана по handlers.

Примеры:

- `handlers/journal.py:152-163` — логика анализа после записи
- `handlers/goals.py:42-66` — логика уточнения цели
- `handlers/goals.py:327-374` — логика обработки неудачи

Решение: создать сервисы:

- `services/journal_service.py`
- `services/goal_service.py`

#### 3.2. Отсутствие централизованной обработки ошибок

Проблема: обработка ошибок разбросана.

Места:

- `handlers/ratings.py:21-26, 40-45` — try/except в каждом обработчике
- `handlers/settings.py:131-136, 176-181` — дублирование обработки ошибок
- `analysis.py:44-45, 78-79, 116-117, 288-296` — разные стратегии обработки

Решение: создать middleware для обработки ошибок:

```python
# middleware/error_handler.py
class ErrorHandlerMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        try:
            return await handler(event, data)
        except Exception as e:
            # Единая обработка ошибок
```

#### 3.3. Антипаттерн: `UserSettingsStub`

Проблема: в `repositories/user_repository.py:7-12` используется заглушка вместо нормальной модели.

Решение: использовать `Optional[UserSettings]` или создать дефолтные настройки через фабрику.

#### 3.4. Неэффективный scheduler loop

Проблема: в `scheduler.py:59-116` проверка каждую минуту для всех пользователей.

Решение: использовать APScheduler или динамическое планирование:

```python
# Использовать APScheduler для точного планирования
from apscheduler.schedulers.asyncio import AsyncIOScheduler
```

#### 3.5. Отсутствие валидации данных

Проблема: нет валидации входных данных перед сохранением.

Примеры:

- `handlers/journal.py` — нет проверки длины текста
- `handlers/goals.py` — нет проверки формата цели

Решение: добавить валидацию через Pydantic:

```python
# schemas/journal.py
from pydantic import BaseModel, validator

class JournalEntrySchema(BaseModel):
    emotion: str
    location: str
    company: str

    @validator('emotion')
    def validate_emotion(cls, v):
        if len(v) > 200:
            raise ValueError("Emotion too long")
        return v
```

---

### 4. Приоритеты рефакторинга

Критично (сделать в первую очередь):

1. Разделить `analysis.py` на сервисы (SRP)
2. Создать утилиту для парсинга `callback_data` (DRY)
3. Вынести бизнес-логику из handlers в сервисы (SRP)
4. Убрать `UserSettingsStub`, использовать Optional (архитектура)

Высокий приоритет: 5. Создать универсальную функцию для CallbackQuery/Message (DRY) 6. Рефакторинг паттерна работы с сессиями в BaseRepository (DRY) 7. Добавить централизованную обработку ошибок 8. Оптимизировать scheduler loop (использовать APScheduler)

Средний приоритет: 9. Добавить валидацию данных (Pydantic) 10. Рефакторинг клавиатур (OCP) 11. Вынести конфигурацию часовых поясов 12. Создать интерфейсы для AI и репозиториев (DIP)

---

### Рекомендуемая структура после рефакторинга:

```
project/
├── repositories/          # Слой доступа к данным
│   ├── base.py           # BaseRepository с _execute_in_transaction
│   ├── journal_repository.py
│   └── ...
├── services/              # Бизнес-логика
│   ├── journal_service.py
│   ├── goal_service.py
│   └── ai/
│       ├── mistral_client.py
│       ├── prompt_builder.py
│       └── analysis_service.py
├── handlers/              # Только обработка UI
├── middleware/            # Middleware для проверок и ошибок
├── utils/                 # Утилиты
│   ├── callback_parser.py
│   ├── message_utils.py
│   └── validators.py
├── interfaces/            # Абстракции (опционально)
├── schemas/               # Pydantic схемы для валидации
└── config/                # Конфигурация
```

Готов подготовить конкретные примеры рефакторинга для любого из этих пунктов.
