# BotCity RPA Automation Template

This repository provides a robust template for creating Robotic Process Automation (RPA) bots using the BotCity framework. The template includes integration with **BotMaestroSDK**, detailed logging, and resource tracking for efficient and scalable automation tasks.

## Features

- **Environment-Specific Execution:** Easily switch between Maestro (``--environment maestro``) and local (``--environment local``) execution modes.

- **BotMaestroSDK Integration:** Leverage BotCity Maestro for task management and artifact handling.

- **Detailed Resource Usage Logging:** Tracks CPU, RAM, and GPU usage during bot execution.

- **Flexible Configuration:** Customize bot settings such as server credentials and log directories

## Getting Started

### Prerequisites

Before running the bot, ensure you have the following installed:

- **Python 3.8**+
- **Poetry** (for dependency management)
- **BotCity SDK** (BotCity Maestro)

### Installation

1. Clone this repository:

    ```bash
    git clone https://github.com/vinicinhus/botcity-rpa-template.git

    cd botcity-rpa-template 
    ```

2. Install dependencies. You can choose one of the following methods:

    - **Using Poetry:**

        If you are using Poetry for dependency management, run:

        ```bash
        poetry install
        ```

    - **Using ``requirements.txt``**:

        Alternatively, if you prefer to use pip and a requirements.txt file, you can install the dependencies as follows:

        ```bash
        pip install -r requirements.txt
        ```

3. Set up your environment variables in a ``.env`` file:

    ```plaintext
    SERVER_MAESTRO="your_maestro_server_url"
    LOGIN_MAESTRO="your_maestro_login"  
    KEY_MAESTRO="your_maestro_key"  
    ```

4. Modify ``bot.py`` or ``src/main.py`` to include your automation logic.

### Usage

To run the bot, specify the desired environment:

- **Maestro Execution (default):**

    ```bash
    poetry run python bot.py --environment maestro
    # Or
    python bot.py --environment maestro  
    ```

- **Local Execution:**

    ```bash
    poetry run python bot.py --environment local
    # Or
    python bot.py --environment local  
    ```

### Configuration

- **Environment Selection:** Use the ``--environment`` flag to specify the execution environment (``maestro`` or ``local``).
- **Bot Details:** Set the bot name and server credentials in ``botcity_aux/core/config.py`` or via environment variables.
- **Logs Directory:** Logs are stored in the ``logs`` folder by default but can be customized.

### How It Works

1. **Execution Modes:**

    - **Maestro Mode**: Uses the BotMaestroSDK to execute tasks and interact with the BotCity platform.
    - **Local Mode:** Runs tasks locally while still providing logs.

2. **Resource Tracking:**

    - Logs CPU, RAM, and GPU usage during execution for analysis and debugging.

3. **Error Handling:**

    - Retries the bot task ``MAX_RETRIES`` times after a failure, so the default
      ``MAX_RETRIES = 0`` runs the automation a single time. Only raise it when
      re-running the process from the start is safe.
    - The task is finished in BotCity Maestro only **once**, after the retries are
      over: while it is still retrying, the task keeps showing as running instead of
      being reported as failed.
    - On the final failure, sends the error message and uploads the log to BotCity
      Maestro, then re-raises the exception.

4. **Credentials:**

    - Declared a single time in ``botcity_aux/core/credentials.py`` (``TASK_CREDENTIALS``) and
      resolved for both environments through the ``maestro_sdk`` property, which
      points to ``self`` in local mode and to ``self.maestro`` in maestro mode.

### Logs and Artifacts

**Logs:**

- Generated for each execution and saved in the ``logs`` directory.
- Includes execution time, resource usage, and errors.

**Artifacts:**

- Automatically uploaded to BotCity Maestro under the associated task.

### Extending the Template

To extend or modify the bot’s functionality:

1. Implement your custom automation logic in ``src/main.py``.

2. Declare the credentials your automation needs in ``TASK_CREDENTIALS``
   (``botcity_aux/core/credentials.py``), mapping the name used by ``main`` to the
   BotMaestro ``(label, key)`` pair. They are fetched once and work in both the
   local and the maestro runner.

3. Add or modify utility classes such as ``BotRunnerLocal`` or ``BotRunnerMaestro``.

4. Override the ``_execute_bot_task`` method in a runner only when one environment
   needs to call ``main`` differently from the other (a desktop automation that
   needs a different image set, for instance); the shared implementation lives in
   ``MaestroCredentialsMixin``.

## Contributing

1. Fork this repository.
2. Create a feature branch.
3. Make your changes.
4. Commit and push your changes.
5. Open a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/vinicinhus/botcity-rpa-template/blob/main/LICENSE) file for details.

## Acknowledgments

- [BotCity](https://documentation.botcity.dev/) for providing the powerful framework for automation.
- [Poetry](https://python-poetry.org/) for managing project dependencies.
