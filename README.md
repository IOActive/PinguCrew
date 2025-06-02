# PinguCrew

![Logo](pingucrew_logo.png)

# Index

1. [Introduction to PinguCrew](#Introduction-to-PinguCrew): This section provides a high-level overview of what Pingucrew is, what it does, and how it can help security researchers. It should provide a good foundation for understanding the rest of the documentation.
2. [PinguCrew - Frontend Overview](src/frontend/README.md): This section documents the frontend section of the Pingucrew framework. It should provide a detailed description of how the frontend is structured and how to use it, as well as any relevant code snippets that would be helpful to see in action.
3. [PinguCrew - Backend Overview](src/backend/README.md): This section documents the backend section of the Pingucrew framework. It should provide a detailed description of how the backend is structured and how to use it, as well as any relevant code snippets that would be helpful to see in action.
4. [PinguCrew - Worker Bot Overview](src/pingubot/README.md): This section documents the worker bot section of the Pingucrew framework. It should provide a detailed description of how the worker bot is structured and how to use it, as well as any relevant code snippets that would be helpful to see in action.
5. [PinguCrew - Toolset Management Overview](docs/butler.md): This section documents how to manage the tools in the Pingucrew framework. It should provide a detailed description of how to add, remove, or configure tools, as well as any relevant code snippets that would be helpful to see in action.
6. PinguCrew - Test Execution Overview: This section documents how to execute tests in the Pingucrew framework. After having set up a test case, it should describe how to start the test and how to view the results, as well as any relevant code snippets that would be helpful to see in action.
7. PinguCrew - Test Results Overview: This section documents how to view and analyze test results in the Pingucrew framework. It should describe how to access the test report and how to analyze it, as well as any relevant code snippets that would be helpful to see in action.
8. [PinguCrew Architecture components](docs/components.md): This section contains a short description of each software component that composes the PinguCrew platform.
9. [PinguCrew Installation](docs/deployment_instructions.md): This section explains in detail how to deploy the PinguCrew framework to leave it ready to go.
10. [Future Features](#future-features): This section contains some of the features that are planned to be implemented in the near future.

# Introduction to PinguCrew

PinguCrew is a web-based fuzzer platform that allows security researchers to test their software for vulnerabilities in a scalable and efficient manner. The tool is inspired by the [ClusterFuzz](https://google.github.io/clusterfuzz/) tool but aims to remove any cloud service dependencies by running the tests within the user's own network.

Unlike ClusterFuzz, which requires users to use a third-party hosting platform, PinguCrew runs the tests on the user's own machines, giving them full control over the fuzzing process. This allows for more customization and flexibility, as users can set up their own testing environments with their desired configurations and testing parameters.

PinguCrew is designed to be highly modular, enabling users to easily integrate new fuzzer tools or modify existing ones to match their specific needs. The tool is built using a microservices architecture, with a Frontend using ReactJS to handle the user interface, a Backend using Django Python to handle server-side tasks, and a Python worker bot to execute the fuzzer test cases.

PinguCrew also provides users with a [Butler](docs/butler.md) script to automate many of the common tasks involved in running and managing fuzzers, including deployments, executions, and tracking test results. This makes it easier for security researchers to focus on their research, without having to worry about the technical details of running and analyzing fuzzing tests.

## Backend Overview

The backend provides the core services for the PinguCrew platform, including:

- A RESTful API for managing fuzzing tasks, crashes, and test cases.
- Integration with PostgreSQL for data storage.
- Celery workers for asynchronous task execution.
- RabbitMQ for task queuing.
- Bucket storage for temporary data handling.

For more details, refer to the [Backend Documentation](src/backend/README.md).

## Frontend Overview

The frontend is a ReactJS-based web application that provides an intuitive interface for managing bots, jobs, and test cases. It includes:

- A dashboard for monitoring system status.
- Tools for managing fuzzing jobs and results.
- Integration with backend APIs for seamless interaction.

For more details, refer to the [Frontend Documentation](src/frontend/README.md).

## Worker Bot Overview

The worker bot is responsible for executing fuzzing tasks and reporting results back to the backend. Key features include:

- Support for multiple fuzzing strategies.
- Task automation for analyzing, minimizing, and symbolizing test cases.
- Integration with the backend for task management.

For more details, refer to the [Worker Bot Documentation](src/pingubot/README.md).

## Future Features:

The Pingucrew platform is continuously evolving to meet the needs of its users. Here are some of the recently implemented features and planned future features:

### Recently Implemented Features:

1. **Fuzzing Statistics Dashboard**: A new dashboard to visualize and analyze fuzzing statistics, providing insights into fuzzing performance and results.
2. **Coverage Explorer**: A tool to explore code coverage data, helping users identify untested areas of their code.
3. **SDK for Integrated Fuzzers**: A new SDK to simplify the development of integrated fuzzers, making it easier to extend the platform with custom fuzzers.
4. **Modular Storage Provider**: Support for both file system and Minio bucket storage providers, offering flexibility in storage configurations.
5. **Fuzzing Projects**: A feature to organize fuzzing campaigns into projects, enabling better management and separation of fuzzing tasks.
6. **Dockerized Deployment**: All backend components are fully dockerized for easier setup and scalability.

### Planned Features:

1. **gRPC API Server and Client**: Development of a gRPC API server and client to support multiple programming languages, enabling broader integration capabilities.
2. **Project Features**: Enhancements to project management, including import/export functionality for fuzzing projects.
3. **Expanded Platform Support**: Plans to extend platform support to include Windows and Android environments, allowing for a wider range of testing scenarios.
4. **AI-Powered Testing Capabilities**: Incorporation of AI-powered test case generators for more accurate and diverse testing scenarios.
5. **Collaboration and Reporting**: Improvements to collaboration and reporting features, such as enhanced dashboards and customizable reporting options.
6. **Improved Plug-and-Play Fuzzer Compatibility**: Enhancements to the fuzzer plugin system, including templates for easier integration of custom fuzzers.

These features reflect the ongoing commitment to making PinguCrew a powerful and flexible fuzzing platform for security researchers.
