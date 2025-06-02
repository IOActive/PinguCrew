# Requeriments

## Docker Service

At the moment the default configuration when the [run_server butler command](butler.md#run-pingucrew-backend-server) uses docker containers to run the PostgreSQL, RabbitMQ, and Minio services. It is mandatory to have Docker service installed in case the default configuration is used. To install Docker, you can refer to the official installation instructions [Install Docker Engine](https://docs.docker.com/engine/install/):

## Python

To run the backend server and the Pingu bot, it is necessary to have the latest [Python](https://docs.python.org/3/using/index.html) version installed on your system.

## Node.js

By default, in order to execute the Pingu Frontend, the framework uses [NodeJS](https://nodejs.org/en/learn/getting-started/how-to-install-nodejs).

# Deployment steps

1. **Sync Submodules**: First of all, as the project is fragmented into multiple git submodules, once the PinguCrew project is cloned, it will be necessary to run the following git command to sync the rest of the git submodules.

```bash
git submodule update --init
```

2. **Install Dependencies**: Instead of manually installing all the dependencies, use the [butler bootstrap command](butler.md#bootstrap-all-pingucrew-components).
3. **Setup Configuration Files**: The configuration files located in the `configs/` directory are automatically set up during the deployment process. There is no need to manually modify these files unless specific customizations are required.
4. **Run Backend Server**: The easiest way to run the backend service is by using the [run_server butler command line](butler.md#run-pingucrew-backend-server) bootstrap command. The Butler assistant will ensure that all backend components, including PostgreSQL, RabbitMQ, and Minio, are initialized for you.
5. **Bot Tokens**: Bot tokens are now auto-generated when a new bot is created using the dashboard. There is no need to manually generate or configure tokens during deployment.
6. **Run Frontend Server**: The easiest way to run the frontend dashboard is by using the [run_web butler command](butler.md#Run-Pingu-Frontend). At this point, it is possible to create a dashboard user by using the [Django Admin dashboard](http://127.0.0.1:8086/admin) or directly using the registration form on the login page.
