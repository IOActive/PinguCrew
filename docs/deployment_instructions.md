# Requeriments

## Docker Service

At the moment the default configuration when the [run_server butler command](butler.md#run-pingucrew-backend-server) uses docker containers to run the MongoDB, rabbit-mq and minio services. It is mandatory to have docker service installed in case the the fault configuration is used. To install docker you can refer to the official installtion instructions [Install Docker Engine](https://docs.docker.com/engine/install/):

## Python

To run the backend server and the Pingu bot it is necessary to have latest [python](https://docs.python.org/3/using/index.html) version installed in your system.

## Node.js

By the fault in order to execute the Pingu Frontend the framework uses [NodeJS](https://nodejs.org/en/learn/getting-started/how-to-install-nodejs).

# Deployment steps

1. **Sync Submodules**: First of all as the project is fragmented in multiple git submodules once the PinguCrew project is cloned it will be necessary to run the following git command to sync the rest of git submodules.

```bash
git submodule update --init
```

2. **Install Dependencies**: Instead of manually installing all the dependency manually use the [butler boostrap command](butler.md#bootstrap-all-pingucrew-components).
3. **Setup configuration file parameters**: You can find and modify the project configuration by editting the file located in **configs/test/project.yaml.** The following parameters need to be configured before jumping to the following deployment step:

   * **MINIO_ROOT_USER & MINIO_ROOT_PASSWORD**: admin credentials to access the Mino Dashboards.
   * **SECRET_KEY**:  This ensures that sensitive information, like connection strings, API credentials, and user data, are encrypted and protected from unauthorized access in the Django Backend.
   * **MINIO_STORAGE_PATH**: local folder path where the Minio bucket DB will be stored.
   * **MONGO_DB_PATH:** local path where the MongoDB will be stored.
   * **BACKEND_SUPERUSER**: Django dashboard admin username. The admin password will be requested during when [run_server butler command line](butler.md#run-pingucrew-backend-server) is executed if the boostrap flag (-b) is set.
4. **Run backend server**: The easiest way to run the backend service is using the [run_server butler command line](butler.md#run-pingucrew-backend-server) boostrap command. The butler assitant will make sure to initialize all the backend components for you including MongoDb, rabbit-mq and minio.
5. **Generate access tokens for the bots**: The Pingu bots need access tokens to comunicate with the backend API and the minio buckets API. Therefore, before execution any bot it is necesary to manually generate these token using the [Django Admin dashboard](http://127.0.0.1:8086/admin) or using the [API directly](http://127.0.0.1:8086/api/swagger/) and the [minio dashboard](http://127.0.0.1:9001/buckets).

   **Note:** At this point you will notice that the **configs/** folder has been linked to all the subprojects.

   **Note**: every time the butler command line is use the source folder will be sync with their copies.

   There are few key values inside the project.yaml file that you will need to modify in order to run the Pingu bot succesfully:

   1. **MINIO_ACCESS_KEY & MINIO_SECRET_KEY**: To get this keys it is necesary to generate them using the minio dashboard.
   2. **API_HOST && API_KEY:** API host and API token used by the bots to interact with the backend. At the moment all the bots share the same access token but in the future this configuration variable will be moved to the "*src/pingubot/bot_working_directory/env.yaml*" configuration file that way each bot will have its own access token.
6. **Run forntend server**: The easyest way to run the frontend dashboard is by using the [run_web butler command](butler.md#Run-Pingu-Frontend). At this point it is posible to create a dashboard user by using the [Django Admin dashboard](http://127.0.0.1:8086/admin) or directly using the registration form in the login page.
