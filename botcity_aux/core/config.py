from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from botcity_aux.enums.department import DepartmentFolderNumber, DepartmentName
from botcity_aux.enums.recurrence import Recurrence


class Settings(BaseSettings):
    """
    Centralized application configuration settings.

    This class aggregates all configuration areas (bot, maestro, cli, database,
    sharepoint, simplesclique) into a single BaseSettings object. It keeps the
    environment variables flat (no nested __ required) while remaining modular
    and organized with prefixes.
    """

    # =============================
    # Bot settings
    # =============================
    BOT_NAME: str = "Bot Name"
    # Recurrence this automation runs on (see enums/recurrence.py). Typed as the
    # enum so pydantic rejects an unknown value at startup.
    RECURRENCE: Recurrence = Recurrence.DIARIA
    DEVELOPER: str = "Developer Name"
    STAKEHOLDER: str = "Stakeholder"
    # Single source for the department: SECTOR and SHAREPOINT_DEPARTMENT_LOG_FOLDER
    # are derived from it. Use the enum member name (see enums/department.py).
    DEPARTMENT: str = "ADM_GRUPOS"
    # Number of *additional* attempts after a failure, so 0 means the automation
    # runs a single time and is not repeated when it fails. Only raise it when
    # re-running the process from the start is safe (no duplicated work).
    MAX_RETRIES: int = 0

    # =============================
    # Maestro settings
    # =============================
    SERVER_MAESTRO: Optional[str] = None
    LOGIN_MAESTRO: Optional[str] = None
    KEY_MAESTRO: Optional[str] = None

    # =============================
    # CLI settings
    # =============================
    DESCRIPTION: str = "Bot Runner Settings"
    HELP_MESSAGE: str = (
        "Define the execution environment: 'maestro' or 'local' (default: 'maestro')"
    )
    CHOICE_MAESTRO: str = "maestro"
    CHOICE_LOCAL: str = "local"

    # =============================
    # Database production settings
    # =============================
    USE_DATABASE: bool = True
    USE_DATABASE_LOCAL: bool = True
    SQL_QUERY_PATH: str = r"botcity_aux\query\insert_log.sql"
    MAESTRO_SQL_LABEL: str = "Your Maestro SQL Label Credential"
    MAESTRO_SQL_SERVER: str = "Your Maestro SQL Server Credential"
    MAESTRO_SQL_DATABASE_INTERNAL: str = "Your Maestro SQL Database Internal Credential"
    MAESTRO_SQL_USERNAME: str = "Your Maestro SQL Username Credential"
    MAESTRO_SQL_PASSWORD: str = "Your Maestro SQL Password Credential"

    # =============================
    # Database homologation settings
    # =============================
    MAESTRO_SQL_LABEL_HOMOL: str = "Your Maestro SQL Label Homol Credential"
    MAESTRO_SQL_SERVER_HOMOL: str = "Your Maestro SQL Server Homol Credential"
    MAESTRO_SQL_DATABASE_INTERNAL_HOMOL: str = (
        "Your Maestro SQL Database Internal Homol Credential"
    )

    # =============================
    # SharePoint settings
    # =============================
    USE_SHAREPOINT: bool = True
    USE_SHAREPOINT_LOCAL: bool = False
    MAESTRO_SHAREPOINT_LABEL: str = "Your Maestro Sharepoint Label Credential"
    MAESTRO_SHAREPOINT_SITE_URL: str = "Your Maestro Sharepoint Site URL Credential"
    MAESTRO_SHAREPOINT_TENANT: str = "Your Maestro Sharepoint Tenant Credential"
    MAESTRO_SHAREPOINT_CLIENT_ID: str = "Your Maestro Sharepoint Client ID Credential"
    MAESTRO_SHAREPOINT_THUMBPRINT: str = "Your Maestro Sharepoint Thumbprint Credential"
    CERTIFICATE_FILE_PATH: str = r"botcity_aux\cert\cert.pem"

    MAESTRO_SHAREPOINT_SITE_URL_SUFFIX: str = "DesenvolvimentoIA"
    SHAREPOINT_ROOT_LOG_FOLDER: str = r"Documentos Compartilhados/Automações/Logs"

    # =============================
    # Pydantic Settings
    # =============================
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, env_file_encoding="utf-8"
    )

    # =============================
    # Automation credentials settings
    # =============================
    # Credentials the automation itself needs (the system it logs into, an e-mail
    # account, an API key...). Declare them in `TASK_CREDENTIALS`
    # (core/credentials.py) and add one setting per label/key as needed.
    MAESTRO_AUTOMATION_LABEL: str = "Your Maestro Automation Label Credential"
    MAESTRO_AUTOMATION_USER: str = "Your Maestro Automation User Credential"
    MAESTRO_AUTOMATION_PASSWORD: str = "Your Maestro Automation Password Credential"

    # =============================
    # Derived department settings
    # =============================
    @field_validator("DEPARTMENT")
    @classmethod
    def _validate_department(cls, value: str) -> str:
        """
        Normalizes `DEPARTMENT` and fails at startup when it is unknown.

        Args:
            value (str): The configured department, as an enum member name.

        Returns:
            str: The department name, upper-cased.

        Raises:
            ValueError: If the department is missing from either department enum.
        """
        key = value.strip().upper()

        if key not in DepartmentName.__members__:
            valid = ", ".join(sorted(DepartmentName.__members__))
            raise ValueError(
                f"Unknown DEPARTMENT '{value}'. Valid options are: {valid}"
            )

        if key not in DepartmentFolderNumber.__members__:
            raise ValueError(
                f"Department '{key}' has no folder number in DepartmentFolderNumber. "
                "Add it to enums/department.py."
            )

        return key

    @property
    def SECTOR(self) -> str:
        """Department name recorded in the database, e.g. 'Cobrança'."""
        return DepartmentName[self.DEPARTMENT].value

    @property
    def SHAREPOINT_DEPARTMENT_LOG_FOLDER(self) -> str:
        """Prefix of the department's SharePoint log folder, e.g. '04'."""
        return DepartmentFolderNumber[self.DEPARTMENT].value


# Global settings instance
settings = Settings()
