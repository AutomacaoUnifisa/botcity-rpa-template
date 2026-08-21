from typing import Dict, Optional, Tuple

from botcity.maestro import BotMaestroSDK

from botcity_aux.core.config import settings
from src.main import main


class MaestroCredentialsMixin:
    """
    Single source of truth for every credential the bot reads from BotMaestro.

    Both runners (`BotRunnerLocal` and `BotRunnerMaestro`) fetch the exact same
    credentials, the only difference being *which* SDK instance answers the call:

        - `BotRunnerLocal` **is** a `BotMaestroSDK` (it inherits from it).
        - `BotRunnerMaestro` **holds** a `BotMaestroSDK` in `self.maestro`.

    Each runner exposes that object through the `maestro_sdk` property, so the
    credential code below is written once and works in both environments.

    Attributes:
        TASK_CREDENTIALS (Dict[str, Tuple[str, str]]):
            Declarative map of the credentials required by `src.main.main`, in the
            form `{"NAME_USED_BY_MAIN": (maestro_label, maestro_key)}`. Declare each
            credential here **once** and both environments will resolve it.

    Example:
        >>> class BotRunner(MaestroCredentialsMixin, BotMaestroSDK):
        ...     TASK_CREDENTIALS = {
        ...         "SYSTEM_USER": (
        ...             settings.MAESTRO_AUTOMATION_LABEL,
        ...             settings.MAESTRO_AUTOMATION_USER,
        ...         ),
        ...         "SYSTEM_PASSWORD": (
        ...             settings.MAESTRO_AUTOMATION_LABEL,
        ...             settings.MAESTRO_AUTOMATION_PASSWORD,
        ...         ),
        ...     }
    """

    TASK_CREDENTIALS: Dict[str, Tuple[str, str]] = {
        # Declare the credentials used by the automation here, e.g.:
        # "SYSTEM_USER": (
        #     settings.MAESTRO_AUTOMATION_LABEL,
        #     settings.MAESTRO_AUTOMATION_USER,
        # ),
        # "SYSTEM_PASSWORD": (
        #     settings.MAESTRO_AUTOMATION_LABEL,
        #     settings.MAESTRO_AUTOMATION_PASSWORD,
        # ),
    }

    @property
    def maestro_sdk(self) -> BotMaestroSDK:
        """
        SDK instance used to read credentials from BotMaestro.

        Returns:
            BotMaestroSDK: The connected SDK instance.

        Raises:
            NotImplementedError: If the runner does not provide the SDK instance.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must expose the BotMaestroSDK instance "
            "through the 'maestro_sdk' property."
        )

    def get_maestro_credential(self, label: str, key: str) -> str:
        """
        Reads a single credential from BotMaestro.

        Args:
            label (str): Credential label registered in BotMaestro.
            key (str): Credential key registered under the given label.

        Returns:
            str: The credential value.
        """
        return self.maestro_sdk.get_credential(label=label, key=key)

    def _get_task_credentials(self) -> Dict[str, str]:
        """
        Resolves every credential declared in `TASK_CREDENTIALS`.

        Returns:
            Dict[str, str]: Mapping of credential name to its value, ready to be
                forwarded to `src.main.main`.
        """
        return {
            name: self.get_maestro_credential(label=label, key=key)
            for name, (label, key) in self.TASK_CREDENTIALS.items()
        }

    def _get_credentials_sharepoint(self) -> Dict[str, str]:
        """
        Retrieves the SharePoint credentials from BotMaestro.

        Returns:
            Dict[str, str]: SharePoint site URL, tenant, client ID and thumbprint.
        """
        credentials = {
            "site_url": self.get_maestro_credential(
                label=settings.MAESTRO_SHAREPOINT_LABEL,
                key=settings.MAESTRO_SHAREPOINT_SITE_URL,
            ),
            "tenant": self.get_maestro_credential(
                label=settings.MAESTRO_SHAREPOINT_LABEL,
                key=settings.MAESTRO_SHAREPOINT_TENANT,
            ),
            "client_id": self.get_maestro_credential(
                label=settings.MAESTRO_SHAREPOINT_LABEL,
                key=settings.MAESTRO_SHAREPOINT_CLIENT_ID,
            ),
            "thumbprint": self.get_maestro_credential(
                label=settings.MAESTRO_SHAREPOINT_LABEL,
                key=settings.MAESTRO_SHAREPOINT_THUMBPRINT,
            ),
        }

        return credentials

    def _execute_bot_task(self) -> Optional[int]:
        """
        Executes the bot task and returns the number of processed items.

        This method prepares the credentials, calls the `main` function to execute
        the bot's main workflow, and returns the number of processed items. If the
        task fails or produces no result, `None` can be returned.

        Override it in a specific runner when one environment needs to call `main`
        differently from the other.

        Returns:
            Optional[int]:
                The number of items processed if successful, otherwise `None`.

        Example:
            >>> result = self._execute_bot_task()
            >>> if result:
            ...     print(f"Processed {result} items")
            ... else:
            ...     print("No items processed.")
        """
        credentials = self._get_task_credentials()

        items_processed = main(credentials)
        return items_processed
