"""Loguru-based logging channels driven by `logger_config.json`.

Exposes three channel getters:
    * `get_system_logger()`       - system/startup messages
    * `get_user_logger(user_id)`  - per-user activity, one file per user id
                                    (no retention - kept indefinitely)
    * `get_service_logger()`      - scheduled task output
"""
import json
from pathlib import Path
from threading import Lock

from loguru import logger

_MODULE_DIRECTORY: Path = Path(__file__).resolve().parent
_CONFIG_FILE_PATH: Path = _MODULE_DIRECTORY / "logger_config.json"

with _CONFIG_FILE_PATH.open("r", encoding="utf-8") as config_file:
    _CONFIG_DATA: dict = json.load(config_file)

_LOG_ROOT_DIRECTORY: Path = (_MODULE_DIRECTORY / _CONFIG_DATA["log_root"]).resolve()
_ROTATION_POLICY: str = _CONFIG_DATA["rotation"]
_RETENTION_POLICY: str = _CONFIG_DATA["retention"]
_DEFAULT_LOG_FORMAT: str = _CONFIG_DATA["default_format"]
_USER_LOG_FORMAT: str = _CONFIG_DATA["user_format"]
_CHANNEL_CONFIGS: dict = _CONFIG_DATA["channels"]

_system_sink_id: int | None = None
_service_sink_id: int | None = None
_user_sink_ids_by_user_id: dict[int, int] = {}
_user_sink_registration_lock: Lock = Lock()


def _ensure_directory_exists(directory: Path) -> Path:
    """Create `directory` if missing and return it."""
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _register_channel_sink(
    channel_name: str,
    log_file_path: Path,
    log_format: str,
    log_level: str,
) -> int:
    """Register a sink that only accepts records tagged with `channel_name`."""
    _ensure_directory_exists(log_file_path.parent)
    return logger.add(
        log_file_path,
        level=log_level,
        rotation=_ROTATION_POLICY,
        retention=_RETENTION_POLICY,
        format=log_format,
        filter=lambda record, expected=channel_name: record["extra"].get("log_type") == expected,
        enqueue=True,
        encoding="utf-8",
    )


def get_system_logger():
    """Return a logger bound to the system channel (lazy sink install).

    Returns:
        A `loguru.Logger` bound with `log_type="system"`.
    """
    global _system_sink_id
    if _system_sink_id is None:
        channel_config = _CHANNEL_CONFIGS["system"]
        log_file_path = _LOG_ROOT_DIRECTORY / channel_config["subdir"] / channel_config["filename"]
        _system_sink_id = _register_channel_sink(
            "system", log_file_path, _DEFAULT_LOG_FORMAT, channel_config["level"]
        )
    return logger.bind(log_type="system")


def get_service_logger():
    """Return a logger bound to the service channel (lazy sink install).

    Returns:
        A `loguru.Logger` bound with `log_type="service"`.
    """
    global _service_sink_id
    if _service_sink_id is None:
        channel_config = _CHANNEL_CONFIGS["service"]
        log_file_path = _LOG_ROOT_DIRECTORY / channel_config["subdir"] / channel_config["filename"]
        _service_sink_id = _register_channel_sink(
            "service", log_file_path, _DEFAULT_LOG_FORMAT, channel_config["level"]
        )
    return logger.bind(log_type="service")


def _register_user_sink(user_id: int, log_level: str, log_file_path: Path) -> int:
    """Register a sink that only accepts user-channel records for `user_id`.

    No retention is set - user activity logs are kept indefinitely.
    """
    _ensure_directory_exists(log_file_path.parent)

    def is_record_for_this_user(record, expected_user_id: int = user_id) -> bool:
        extra = record["extra"]
        return extra.get("log_type") == "user" and extra.get("user_id") == expected_user_id

    return logger.add(
        log_file_path,
        level=log_level,
        rotation=_ROTATION_POLICY,
        format=_USER_LOG_FORMAT,
        filter=is_record_for_this_user,
        enqueue=True,
        encoding="utf-8",
    )


def get_user_logger(user_id: int):
    """Return a logger that writes to a dedicated `<user_id>.log` file.

    Args:
        user_id: Integer id of the signed-in user.

    Returns:
        A `loguru.Logger` bound with `log_type="user"` and `user_id=<user_id>`.
    """
    channel_config = _CHANNEL_CONFIGS["user"]
    with _user_sink_registration_lock:
        if user_id not in _user_sink_ids_by_user_id:
            log_file_path = (
                _LOG_ROOT_DIRECTORY
                / channel_config["subdir"]
                / str(user_id)
                / channel_config["filename"]
            )
            _user_sink_ids_by_user_id[user_id] = _register_user_sink(
                user_id, channel_config["level"], log_file_path
            )
    return logger.bind(log_type="user", user_id=user_id)
