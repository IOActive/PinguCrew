# Buttler Command line Usage

## Bootstrap all PinguCrew Components
The `bootstrap` command installs all the required dependencies for running all the components and copies the config folder to all the project submodules. To use this command, simply run 

```bash 
python butler.py bootstrap 
```

## Run PinguCrew Backend Server:

The `run_server` command starts the PinguCrew backend server locally, allowing you to run fuzz tests on your own computer. To run the server, follow these steps:

1. Start Docker service and run butler command.
2. Use the `--skip-install-deps` option to skip installation of dependencies (if desired).
3. Use the `--storage-path` option to specify the storage path for the local database.
4. Use the `--log-level` option to specify the logging level for the server.

For example, to start the PinguCrew server with default options, you can run the following command:

```bash
python butler.py run_server --skip-install-deps
```
Alternatively, you can supply additional command-line arguments to specify options such as the bootstrap and clean flags.

For example, to start the PinguCrew server with default options and perform a bootstrap, you can run the following command:

```bash
python butler.py run_server --bootstrap
```
In addition, the `run_server` command has many more options that you can find in the `help` output. Use the `python butler run_server --help` command to see the full list of options.
.

Sure, here is the updated documentation for the `run_bot` command in Butler:

## Run Bot Command


The `run_bot` command runs a local instance of your PinguBot app on the current directory. To run the bot, follow these steps:

1. Run the butler command specifying a bot installation directory.
2. Use the `--config-dir` option to specify the path to the application's config directory.
3. Use the `--name` option to specify the name of the bot to create.
4. Use the `--server-storage-path` option to specify the storage path for the local database.
5. Use the `--android-serial` option to connect to an Android device instead of running normally.
6. Use the `--testing` option to run tests against the bot.

For example, to create a new bot with default options, you can run the following command including the conmfiguration folder path and the folder path which will be the bot working directory:

```bash 
python butler run_bot -c configs/test test-bot
```
In addition, the `run_bot` command has many more options that you can find in the `help` output. Use the `python butler.py run_bot --help` command to see the full list of options.

Sure, here is the updated documentation for the `run_web` command in Butler:

## Run Pingu Frontend

The `run_web` command runs the Pingu frontend server on the current directory. To run the server, follow these steps:

1. Start your Butler instance.
3. Use the `--Skip-Install-Deps` option to skip installation of dependencies (if desired).
4. The server will start and begin listening for requests.

For example, to run the server with default options, you can run the following command:

```bash
python butler.py run_web
```
In addition, the `run_web` command has many more options that you can find in the `help` output. Use the `python butler.py run_web --help` command to see the full list of options.

Sure, here is the updated documentation for the `reproduce` command in Butler:

## Reproduce Command


The `reproduce` command runs the reproduction process for a discovered testcase. To run the process, follow these steps:

1. Start your Butler instance.
2. Navigate to the directory where you want to run the reproduction process.
3. Use the `--testcase` option to specify the URL of the discovered testcase.
4. Use the `--build-dir` option to specify the path to the build directory containing the target app and dependencies.
5. Use the `--iterations` option to specify the number of times to attempt reproduction.
6. Use the `--disable-xvfb` option to disable running the testcase in a virtual frame buffer.
7. Use the `--disable-android-setup` option to skip setting up an Android device for reproduction.
8. Use the `--verbose` option to print additional log messages while running.
9. Use the `--emulator` option to run and attempt to reproduce a crash using the Android emulator.
10. Use the `--application` option to specify the name of the app binary to run.
11. The reproduction process will run and attempt to reproduce the crash in the specified number of iterations.

For example, to run the reproduction process with default options, you can run the following command:

```bash
python butler.py reproduce -t <TESTCASE_URL> -b <BUILD_DIR> -a <APP_NAME>
```
In addition, the `reproduce` command has many more options that you can find in the `help` output. Use the `python butler.py reproduce --help` command to see the full list of options.

## Run command:

The run command works as a wrapper to execute small managment scripts located in "src/local/butler/scripts/". To run a managament command, follow these steps:

1. Start your Butler instance
2. Use the `--non-dry-run` option to run the script enable writes to the actual datastore (eg. buildin fuzzers and templates).

For example to initialize the initial datastore data execute the following command line:
```bash
python butler.py run setup --non-dry-run 
```