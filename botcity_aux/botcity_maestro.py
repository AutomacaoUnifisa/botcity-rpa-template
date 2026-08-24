import time
from typing import List, Optional, Tuple

import GPUtil
import psutil
from botcity.maestro import (
    AutomationTaskFinishStatus,
    BotExecution,
    BotMaestroSDK,
    ServerMessage,
)
from loguru import logger

from botcity_aux.core.config import settings
from botcity_aux.core.credentials import MaestroCredentialsMixin
from botcity_aux.core.logger import LoggerConfig
from botcity_aux.services.sharepoint import SharePointApi
from botcity_aux.services.sql_connector import SQLDatabaseConnectorDict


class BotRunnerMaestro(MaestroCredentialsMixin):
    """
    Class to handle execution of a BotCity bot with integration to BotMaestro,
    SharePoint, and optional database logging.

    Responsibilities:
        - Initialize bot, logging, SharePoint, and BotMaestro SDK.
        - Execute main bot task with retries.
        - Capture and log execution time, CPU/RAM/GPU usage.
        - Upload logs to BotMaestro and SharePoint.
        - Insert execution details into SQL database if enabled.

    Credentials are declared once in `MaestroCredentialsMixin.TASK_CREDENTIALS`
    and resolved through `self.maestro_sdk`, shared with `BotRunnerLocal`.
    """

    def __init__(
        self,
        bot_maestro_sdk_raise: bool = False,
    ) -> None:
        """
        Initializes the BotRunnerMaestro with provided configuration.

        Args:
            bot_maestro_sdk_raise (bool, optional): Raise exceptions on BotMaestro connection issues (default False).

        Attributes:
            logger (LoggerConfig): Logger instance for the bot.
            maestro (BotMaestroSDK): Configured BotMaestro SDK instance.
            execution (BotExecution): Current task execution object.
            sharepoint (SharePointApi): SharePoint API instance.
            start_time (Optional[float]): Time when execution starts.
        """
        # initial config
        self.logger: LoggerConfig = LoggerConfig()

        # maestro config
        self.bot_maestro_sdk_raise: bool = bot_maestro_sdk_raise
        self.maestro, self.execution = self._setup_maestro()

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

        # time config
        self.start_time: Optional[float] = None

    def _setup_maestro(self) -> Tuple[BotMaestroSDK, BotExecution]:
        """
        Sets up BotMaestro SDK and retrieves the current task execution.

        Returns:
            Tuple[BotMaestroSDK, BotExecution]: Configured SDK instance and current task execution.

        Raises:
            Exception: If SDK initialization or execution retrieval fails.
        """
        try:
            # Set up the BotMaestroSDK with custom configuration
            if self.bot_maestro_sdk_raise:
                BotMaestroSDK.RAISE_NOT_CONNECTED = True
            maestro = BotMaestroSDK.from_sys_args()
            execution: BotExecution = maestro.get_execution()

            # Log the task details
            logger.info(f"Task ID is: {execution.task_id}")
            logger.info(f"Task Parameters are: {execution.parameters}")

            return maestro, execution
        except Exception as e:
            logger.error(f"Failed to initialize BotMaestroSDK: {e}")
            raise e

    @property
    def maestro_sdk(self) -> BotMaestroSDK:
        """
        SDK instance used to read credentials from BotMaestro.

        Returns:
            BotMaestroSDK: The SDK instance created by `_setup_maestro`.
        """
        return self.maestro

    def _add_log_file_into_maestro(self) -> ServerMessage:
        """
        Uploads the bot's log file to BotMaestro as an artifact.

        Returns:
            ServerMessage: Response from BotMaestro server.

        Raises:
            Exception: If upload fails.
        """
        try:
            response: ServerMessage = self.maestro.post_artifact(
                task_id=int(self.execution.task_id),
                artifact_name=self.logger.log_filename,
                filepath=self.logger.log_path,
            )
            logger.info(
                f"Log file '{self.logger.log_filename}' uploaded successfully to BotCity Maestro."
            )
            return response
        except Exception as e:
            logger.error(
                f"Failed to upload log file '{self.logger.log_filename}' into BotCity Maestro: {e}"
            )
            raise e

    def _get_execution_time(self) -> str:
        """
        Calculates execution duration since bot start.

        Returns:
            str: Execution time formatted as 'DD:HH:MM:SS', or message if start_time is None.
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
        Retrieves current system resource usage.

        Returns:
            str: Formatted CPU, RAM, and GPU usage.
        """
        # CPU and RAM usage
        cpu_percent = psutil.cpu_percent(interval=1)
        ram_usage = psutil.virtual_memory()
        ram_percent = ram_usage.percent
        ram_used_mb = ram_usage.used / (1024 * 1024)

        # GPU usage (if GPU is available)
        gpu_stats = []
        gpus: List = GPUtil.getGPUs()
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
                label=settings.MAESTRO_SQL_LABEL, key=settings.MAESTRO_SQL_SERVER
            ),
            "database": self.get_maestro_credential(
                label=settings.MAESTRO_SQL_LABEL, key=settings.MAESTRO_SQL_DATABASE
            ),
            "username": self.get_maestro_credential(
                label=settings.MAESTRO_SQL_LABEL, key=settings.MAESTRO_SQL_USERNAME
            ),
            "password": self.get_maestro_credential(
                label=settings.MAESTRO_SQL_LABEL, key=settings.MAESTRO_SQL_PASSWORD
            ),
        }

        return credentials_database

    def _insert_database_log_execution(self, items_processed: int):
        """
        Inserts an execution record into the automation logs database.

        Fetches SQL credentials from BotMaestro, connects to the database, and
        inserts a record including bot name, developer, sector, stakeholder,
        recurrence, execution time, and items processed.

        Args:
            items_processed (int): Number of items processed in the bot task.

        Raises:
            Exception: If database connection or query execution fails.
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
            use_windows_auth=False,
            username=credentials.get("username"),
            password=credentials.get("password"),
        ) as sql_connector:
            sql_connector.execute_query_from_file(settings.SQL_QUERY_PATH, params)

    def _run_with_retries(self) -> Tuple[Optional[int], Optional[Exception]]:
        """
        Runs the bot task, retrying it up to `settings.MAX_RETRIES` times.

        Nothing is reported to BotMaestro here: the task is only finished once, by
        `run`, after every attempt has been exhausted. This keeps the task marked as
        running in BotMaestro while it is still retrying.

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

    def _report_outcome_to_maestro(
        self,
        error: Optional[Exception],
        execution_time: str,
        resource_usage: str,
    ) -> None:
        """
        Reports the execution outcome to BotMaestro, exactly once.

        Each call is guarded so a reporting failure neither leaves the task stuck as
        *running* nor replaces the original error.

        Args:
            error (Optional[Exception]): The error that failed the execution, or
                `None` when it succeeded.
            execution_time (str): Execution duration, for the success message.
            resource_usage (str): CPU/RAM/GPU usage, for the success message.
        """
        if error is not None:
            try:
                self.maestro.error(
                    int(self.execution.task_id),
                    error,
                    attachments=[self.logger.log_path],
                )
            except Exception as e:
                logger.error(f"Failed to report the error to BotMaestro: {e}")

        if error is not None:
            status = AutomationTaskFinishStatus.FAILED
            message = f"An error occurred during bot execution: {error}"
        else:
            status = AutomationTaskFinishStatus.SUCCESS
            message = (
                f"Execution time: {execution_time}\n"
                f"Resource usage at end of execution: {resource_usage}"
            )

        try:
            self.maestro.finish_task(self.execution.task_id, status, message)
            logger.info(
                f"Task {self.execution.task_id} finished in BotMaestro as {status.name}."
            )
        except Exception as e:
            logger.error(
                f"Failed to finish task {self.execution.task_id} in BotMaestro: {e}"
            )

        try:
            self._add_log_file_into_maestro()
        except Exception as e:
            logger.error(f"Failed to upload the log file to BotMaestro: {e}")

    def run(self) -> None:
        """
        Executes the bot task with retry logic, logging, and resource monitoring.

        - Attempts the task up to `settings.MAX_RETRIES`.
        - Logs execution time, CPU/RAM/GPU usage, and errors.
        - Uploads logs to SharePoint and BotMaestro.
        - Inserts execution details into SQL database if enabled.
        - Marks the task as SUCCESS or FAILED in BotMaestro **once**, only after all
          retries are done, so a retrying task keeps showing as running in BotMaestro.
        - Always reports, from a `finally` block: a failure while wrapping up marks
          the task FAILED instead of leaving it stuck as running. The first error
          wins, so it never hides the real automation error.

        Raises:
            Exception: If bot execution fails after all retries.
        """
        error: Optional[Exception] = None
        execution_time: str = "Execution time not available"
        resource_usage: str = "Resource usage not available"

        try:
            items_processed, error = self._run_with_retries()

            execution_time = self._get_execution_time()
            resource_usage = self._get_resource_usage()

            logger.info(f"Execution time: {execution_time}")
            logger.info(f"Resource usage at end of execution: {resource_usage}")

            if error is None:
                try:
                    if not settings.USE_DATABASE:
                        logger.info("Database logging is disabled.")
                    elif items_processed is None or items_processed <= 0:
                        logger.warning("No items processed or task failed.")
                    else:
                        logger.info(f"Items processed: {items_processed}")
                        self._insert_database_log_execution(items_processed)
                except Exception as e:
                    error = e
                    logger.error(f"Failed to log the execution into the database: {e}")

            if settings.USE_SHAREPOINT:
                try:
                    self.sharepoint.upload_files([self.logger.log_path])
                except Exception as e:
                    logger.error(f"Failed to upload the log file to SharePoint: {e}")
                    if error is None:
                        error = e

        except Exception as e:
            # Anything unexpected in the bookkeeping above: keep the first error.
            logger.exception("Unexpected failure while wrapping up the bot execution.")
            if error is None:
                error = e

        finally:
            self._report_outcome_to_maestro(error, execution_time, resource_usage)

        if error is not None:
            raise error
