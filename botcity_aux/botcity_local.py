import time
import warnings
from typing import Optional, Tuple

import GPUtil
import psutil
from botcity.maestro import BotMaestroSDK
from loguru import logger
from urllib3.exceptions import InsecureRequestWarning

from botcity_aux.core.config import settings
from botcity_aux.core.credentials import MaestroCredentialsMixin
from botcity_aux.core.logger import LoggerConfig
from botcity_aux.services.sharepoint import SharePointApi
from botcity_aux.services.sql_connector import SQLDatabaseConnectorDict


class BotRunnerLocal(MaestroCredentialsMixin, BotMaestroSDK):
    """
    Runs the bot on a developer machine, authenticating against BotMaestro only to
    read credentials.

    Credentials are declared once in `MaestroCredentialsMixin.TASK_CREDENTIALS` and
    resolved through `self.maestro_sdk`, shared with `BotRunnerMaestro`.
    """

    def __init__(
        self,
        server: str,
        login: str,
        key: str,
        log_dir: str = "logs",
    ) -> None:
        """
        Initializes the BotRunnerLocal instance with the specified configuration.

        Args:
            server (str): BotMaestro server URL.
            login (str): BotMaestro login credential.
            key (str): BotMaestro authentication key.
            log_dir (str, optional): Directory for log files (default: 'logs').

        """
        # BotMaestroSDK config
        super().__init__(server, login, key)
        super().login()
        warnings.filterwarnings("ignore", category=InsecureRequestWarning)

        # initial config
        self.logger: LoggerConfig = LoggerConfig(log_dir)

        if settings.USE_SHAREPOINT:
            # Sharepoint credentials
            self.sharepoint_credentials = self._get_credentials_sharepoint()

            self.sharepoint = SharePointApi(
                self.sharepoint_credentials.get("site_url", "")
                + settings.MAESTRO_SHAREPOINT_SITE_URL_SUFFIX,
                self.sharepoint_credentials.get("tenant", ""),
                self.sharepoint_credentials.get("client_id", ""),
                self.sharepoint_credentials.get("thumbprint", ""),
                settings.CERTIFICATE_FILE_PATH,
                settings.SHAREPOINT_DEPARTMENT_LOG_FOLDER,
            )

        # maestro config
        self.RAISE_NOT_CONNECTED: bool = False
        self.VERIFY_SSL_CERT = False

        # time config
        self.start_time: Optional[float] = None

    @property
    def maestro_sdk(self) -> BotMaestroSDK:
        """
        SDK instance used to read credentials from BotMaestro.

        Returns:
            BotMaestroSDK: This runner, which is itself a connected SDK instance.
        """
        return self

    def _get_execution_time(self) -> str:
        """
        Computes the execution duration since the bot's start time.

        Returns:
            str: Execution time formatted as 'DD:HH:MM:SS'.
        """
        if self.start_time is None:
            return "Execution time not available"

        end_time = time.time()
        elapsed_seconds = int(end_time - self.start_time)

        days, remainder = divmod(elapsed_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        execution_time = f"{days:02}:{hours:02}:{minutes:02}:{seconds:02}"
        return execution_time

    def _get_resource_usage(self) -> str:
        """
        Retrieves current resource usage (CPU, RAM, and GPU).

        Returns:
            str: Formatted string with CPU, RAM, and GPU usage.
        """
        # CPU and RAM usage
        cpu_percent = psutil.cpu_percent(interval=1)
        ram_usage = psutil.virtual_memory()
        ram_percent = ram_usage.percent
        ram_used_mb = ram_usage.used / (1024 * 1024)

        # GPU usage (if GPU is available)
        gpu_stats = []
        gpus = GPUtil.getGPUs()
        if gpus:
            for gpu in gpus:
                gpu_stats.append(
                    f"GPU {gpu.id}: {gpu.name}, Load: {gpu.load * 100:.1f}%, "
                    f"Memory: {gpu.memoryUsed}MB/{gpu.memoryTotal}MB"
                )
            gpu_usage_str = "; ".join(gpu_stats)
        else:
            gpu_usage_str = "No GPU found."

        # Format the usage information
        usage_info = f"CPU Usage: {cpu_percent}%, RAM Usage: {ram_percent}% ({ram_used_mb:.1f} MB), GPU Usage: {gpu_usage_str}"
        return usage_info

    def _get_database_credentials(self) -> dict:
        """
        Retrieves the database credentials from BotMaestro.

        Returns:
            dict: A dictionary containing the database credentials.
        """
        credentials_database = {
            "server": self.get_maestro_credential(
                label=settings.MAESTRO_SQL_LABEL_HOMOL,
                key=settings.MAESTRO_SQL_SERVER_HOMOL,
            ),
            "database": self.get_maestro_credential(
                label=settings.MAESTRO_SQL_LABEL_HOMOL,
                key=settings.MAESTRO_SQL_DATABASE_HOMOL,
            ),
        }

        return credentials_database

    def _insert_database_log_execution(self, items_processed: int):
        """
        Inserts an execution log entry into the automation logs database.

        This function retrieves the necessary SQL credentials from BotMaestro, establishes a
        connection with the production SQL database, and inserts a log record with information
        about the bot execution (such as bot name, developer, sector, stakeholder, recurrence, and execution time).

        Raises:
            Exception: If there is an error connecting to the database or executing the query.
        """
        execution_time = self._get_execution_time()

        credentials = self._get_database_credentials()

        params = [
            settings.BOT_NAME,
            settings.DEVELOPER,
            settings.SECTOR,
            settings.STAKEHOLDER,
            settings.RECURRENCE,
            execution_time,
            items_processed,
        ]

        with SQLDatabaseConnectorDict(
            server=credentials.get("server", ""),
            database=credentials.get("database", ""),
            use_windows_auth=True,
            username=credentials.get("username"),
            password=credentials.get("password"),
        ) as sql_connector:
            sql_connector.execute_query_from_file(settings.SQL_QUERY_PATH, params)

    def _run_with_retries(self) -> Tuple[Optional[int], Optional[Exception]]:
        """
        Runs the bot task, retrying it up to `settings.MAX_RETRIES` times.

        Returns:
            Tuple[Optional[int], Optional[Exception]]:
                The number of items processed and `None` when an attempt succeeds,
                or `None` and the last exception raised when all attempts fail.
        """
        total_attempts = settings.MAX_RETRIES + 1

        for attempt in range(1, total_attempts + 1):
            try:
                self.start_time = time.time()
                logger.info(
                    f"Bot execution started. Attempt {attempt} of {total_attempts}"
                )

                items_processed = self._execute_bot_task()

                logger.info(
                    f"{settings.BOT_NAME} Bot execution completed on attempt "
                    f"{attempt} of {total_attempts}."
                )
                return items_processed, None

            except Exception as e:
                logger.error(
                    f"An error occurred during bot '{settings.BOT_NAME}' execution "
                    f"on attempt {attempt} of {total_attempts}: {e}"
                )

                if attempt == total_attempts:
                    logger.error(
                        f"Max retries reached ({settings.MAX_RETRIES}). Giving up."
                    )
                    return None, e

                logger.info("Retrying bot execution...")

        return None, None

    def run(self) -> None:
        """
        Starts the bot execution process with retry logic and logs the results.

        The bot task is attempted up to `settings.MAX_RETRIES` times. Logging,
        SharePoint upload and database logging happen once, after the retries are
        done, so a failed attempt that is about to be retried is not reported as a
        finished execution.

        Logs:
            - Execution start and completion per attempt.
            - Execution time and system resource usage.
            - Any errors encountered during execution.

        Raises:
            Exception: If the bot fails to execute successfully after all retry attempts.
        """
        items_processed, error = self._run_with_retries()

        logger.info(f"Execution time: {self._get_execution_time()}")
        logger.info(f"Resource usage at end of execution: {self._get_resource_usage()}")

        if settings.USE_SHAREPOINT:
            if error is None:
                self.sharepoint.list_folders_by_number()
            self.sharepoint.upload_files([rf"{self.logger.log_path}"])

        if error is not None:
            raise error

        if not settings.USE_DATABASE:
            logger.info("Database logging is disabled.")
        elif items_processed is None or items_processed <= 0:
            logger.warning("No items processed or task failed.")
        else:
            logger.info(f"Items processed: {items_processed}")
            self._insert_database_log_execution(items_processed)
