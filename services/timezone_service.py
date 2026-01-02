from datetime import datetime
import pytz

# Дефолтный часовой пояс для пользователей без установленного часового пояса
DEFAULT_TIMEZONE = 'Asia/Yekaterinburg'  # UTC+5


def get_user_timezone(user_settings):
    """
    Получает объект часового пояса пользователя.
    Если часовой пояс не установлен, возвращает дефолтный (UTC+5).

    Args:
        user_settings: Объект UserSettings или None

    Returns:
        pytz.timezone объект (дефолтный UTC+5, если часовой пояс
        не установлен)
    """
    if not user_settings or not user_settings.timezone:
        return pytz.timezone(DEFAULT_TIMEZONE)

    try:
        return pytz.timezone(user_settings.timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        msg = (f"Неизвестный часовой пояс: {user_settings.timezone}, "
               f"используется дефолтный {DEFAULT_TIMEZONE}")
        print(msg)
        return pytz.timezone(DEFAULT_TIMEZONE)


def get_user_local_time(user_settings) -> datetime:
    """
    Получает текущее локальное время пользователя.
    Если часовой пояс не установлен, используется дефолтный (UTC+5).

    Args:
        user_settings: Объект UserSettings или None

    Returns:
        datetime объект в часовом поясе пользователя (дефолтный UTC+5,
        если не установлен)
    """
    user_tz = get_user_timezone(user_settings)
    return datetime.now(user_tz)


def is_time_for_reminder(user_settings, hour: int) -> bool:
    """
    Проверяет, наступило ли время для напоминания в часовом поясе
    пользователя. Если часовой пояс не установлен, используется
    дефолтный (UTC+5).

    Args:
        user_settings: Объект UserSettings или None
        hour: Час для проверки (например, 9 для 9:00)

    Returns:
        True, если текущее время пользователя соответствует указанному
        часу и минуте (00:00)
    """
    user_time = get_user_local_time(user_settings)
    return user_time.hour == hour and user_time.minute == 0


def detect_timezone_from_time(
    user_time_str: str,
    popular_timezones: list[tuple[str, str]] = None
) -> tuple[str | None, str]:
    """
    Определяет часовой пояс по времени, присланному пользователем.

    Args:
        user_time_str: Время в формате "HH:MM" или "H:MM"
        popular_timezones: Список популярных часовых поясов
            в формате [(tz_name, label), ...]

    Returns:
        Tuple (timezone_name, error_message)
        timezone_name - название часового пояса или None
        error_message - сообщение об ошибке или пустая строка
    """
    try:
        # Парсим время пользователя
        time_parts = user_time_str.strip().split(':')
        if len(time_parts) != 2:
            error_msg = (
                "Неверный формат времени. "
                "Используй формат HH:MM (например, 14:30)"
            )
            return None, error_msg

        user_hour = int(time_parts[0])
        user_minute = int(time_parts[1])

        if not (0 <= user_hour <= 23 and 0 <= user_minute <= 59):
            return None, (
                "Неверное время. Час должен быть от 0 до 23, "
                "минуты от 0 до 59"
            )

        # Получаем текущее UTC время
        utc_now = datetime.now(pytz.UTC)
        utc_hour = utc_now.hour
        utc_minute = utc_now.minute

        # Вычисляем разницу в часах и минутах
        user_total_minutes = user_hour * 60 + user_minute
        utc_total_minutes = utc_hour * 60 + utc_minute

        # Вычисляем смещение (может быть отрицательным)
        diff_minutes = user_total_minutes - utc_total_minutes

        # Учитываем, что разница может быть через полночь
        if diff_minutes > 12 * 60:
            diff_minutes -= 24 * 60
        elif diff_minutes < -12 * 60:
            diff_minutes += 24 * 60

        # Конвертируем в часы (округление)
        offset_hours = round(diff_minutes / 60)

        # Находим подходящий часовой пояс
        # Сначала проверяем популярные, если переданы
        if popular_timezones:
            for tz_name, _ in popular_timezones:
                try:
                    tz = pytz.timezone(tz_name)
                    tz_now = datetime.now(tz)
                    tz_offset = tz_now.utcoffset().total_seconds() / 3600
                    if abs(tz_offset - offset_hours) < 0.5:
                        return tz_name, ""
                except Exception:
                    continue

        # Если не нашли в популярных, ищем во всех доступных
        matching_timezones = []
        for tz_name in pytz.all_timezones:
            try:
                tz = pytz.timezone(tz_name)
                tz_now = datetime.now(tz)
                tz_offset = tz_now.utcoffset().total_seconds() / 3600
                if abs(tz_offset - offset_hours) < 0.5:
                    matching_timezones.append(tz_name)
            except Exception:
                continue

        if matching_timezones:
            # Выбираем первый подходящий
            return matching_timezones[0], ""

        # Если ничего не нашли, возвращаем ошибку
        error_msg = (
            f"Не удалось определить часовой пояс. "
            f"Вычисленное смещение: UTC{offset_hours:+d}. "
            f"Попробуй выбрать часовой пояс вручную."
        )
        return None, error_msg

    except ValueError:
        error_msg = (
            "Неверный формат времени. "
            "Используй формат HH:MM (например, 14:30)"
        )
        return None, error_msg
    except Exception as e:
        return None, f"Ошибка при определении часового пояса: {str(e)}"
