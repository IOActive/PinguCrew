# PinguCrew

# Index

1. [Introduction to PinguCrew](#Introduction-to-PinguCrew): This section provides a high-level overview of what Pingucrew is, what it does, and how it can help security researchers. It should provide a good foundation for understanding the rest of the documentation.
2. [PinguCrew - Frontend Overview](src/frontend/README.md): This section documents the frontend section of the Pingucrew framework. It should provide a detailed description of how the frontend is structured and how to use it, as well as any relevant code snippets that would be helpful to see in action.
3. [PinguCrew - Backend Overview](src/backend/README.md): This section documents the backend section of the Pingucrew framework. It should provide a detailed description of how the backend is structured and how to use it, as well as any relevant code snippets that would be helpful to see in action.
4. PinguCrew - Worker Bot Overview: This section documents the worker bot section of the Pingucrew framework. It should provide a detailed description of how the worker bot is structured and how to use it, as well as any relevant code snippets that would be helpful to see in action.
5. [PinguCrew - Toolset Management Overview](docs/butler.md): This section documents how to manage the tools in the Pingucrew framework. It should provide a detailed description of how to add, remove, or configure tools, as well as any relevant code snippets that would be helpful to see in action.
6. PinguCrew - Test Execution Overview: This section documents how to execute tests in the Pingucrew framework. After having set up a test case, it should describe how to start the test and how to view the results, as well as any relevant code snippets that would be helpful to see in action.
7. PinguCrew - Test Results Overview: This section documents how to view and analyze test results in the Pingucrew framework. It should describe how to access the test report and how to analyze it, as well as any relevant code snippets that would be helpful to see in action.
8. [PinguCrew Architecture components](docs/components.md): this section contatins a short descrition of each software component that composes the PinguCrew platform.
9. [PinguCrew Installation](docs/deployment_instructions.md): This section explain in details how to deploy the PinguCrew framework to leave it ready to go.
10. [Future Features](#future-features): This section contains some of the features that are plan to be implemented in a near future.

# Introduction to PinguCrew

PinguCrew is a web-based fuzzer platform that allows security researchers to test their software for vulnerabilities in a scalable and efficient manner. The tool is inspired by the [ClusterFuzz](https://google.github.io/clusterfuzz/) tool but aims to remove any cloud service dependencies by running the tests within the user's own network.

Unlike ClusterFuzz, which requires users to use a third-party hosting platform, PinguCrew runs the tests on the user's own machines, giving them full control over the fuzzing process. This allows for more customization and flexibility, as users can set up their own testing environments with their desired configurations and testing parameters.

PinguCrew is designed to be highly modular, enabling users to easily integrate new fuzzer tools or modify existing ones to match their specific needs. The tool is built using a microservices architecture, with a Frontend using ReactJS to handle the user interface, a Backend using Django Python to handle server-side tasks and a Python worker bot to execute the fuzzer test cases.

PinguCrew also provides users with a [Butler](docs/butler.md) script to automate many of the common tasks involved in running and managing fuzzers, including deployments, executions, and tracking test results. This makes it easier for security researchers to focus on their research, without having to worry about the technical details of running and analyzing fuzzing tests.

## Future Features:

The Pingucrew platform is continuously evolving to meet the needs of its users. Here are some planned future features that are being developed for the platform:

1. Expanded platform support: The Pingucrew platform currently supports testing in Linux enviroments, but there are plans to expand platform support to include other platforms such as Windows and Android. This would allow users to test a wider range of applications and provide a more comprehensive testing solution.
2. AI-powered testing capabilities: The Pingucrew platform already features advanced testing capabilities, but there are plans to incorporate more AI-powered features such as AI-powered testcases generators. These features would allow for more accurate testing and the ability to handle a wider range of scenarios.
3. Collaboration and reporting: There are plans to enhance the collaboration and reporting features of the Pingucrew platform to provide a more efficient and intuitive testing experience. This could include features such as dashboard improvements, and customizable reporting.
4. Improved scaling: As the Pingucrew platform continues to grow and expand, there are plans to improve its scalability to meet the increasing demands of users. This could include the dockerization of all the software components and the capbility to automatically deploy bots using the dashboard or the butler command line in a larger scale.
5. Improve the plug&play fuzzers compability: In the current state the plaform already support builtin well known fuzzers such as libfuzzer and it is planned to incoporate AFL builtin support. Additionally, the platform also suports blackbox fuzzing were a fuzzer program is uploaded and the bot excutes the fuzzer but in order to improve the collect data and the new custom fuzzers integration it will be nice to have a fuzzer template to create some short of fuzzers plugin system.
6. Code coverage reporting: The platform is already capable to collect code coverage information but the dashboard sectionis not yet implemented.

These are just some of the planned future features for the Pingucrew platform. The platform is constantly evolving and expanding to meet the needs of its users, and these features will help ensure that it remains at the forefront of mobile testing technology.
