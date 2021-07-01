# Ubuntu Installation

&nbsp;

# Introduction
This guide will guide you through the installation process for the HIAS Historical Data Interface.

&nbsp;

# Prerequisites
You will need to ensure you have the following prerequisites installed and setup.

## HIAS Core

The HIAS Historical Data Interface is a core component of the [Hospital Intelligent Automation Server](https://github.com/AIIAL/HIAS-Core). Before beginning this tutorial you should complete the HIAS installation guide and the server should be running.

## Operating System
The **HIASCDI** has been tried and tested on the following operating system(s):

- Ubuntu 18.04

&nbsp;

# Installation
You are now ready to install the HIAS Historical Data Interface software.

## Clone the repository

Clone the [HIAS Historical Data Interface](https://github.com/AIIAL/HIASHDI " HIAS Historical Data Interface") repository from the [Asociación de Investigacion en Inteligencia Artificial Para la Leucemia Peter Moss](https://github.com/AIIAL "Asociación de Investigacion en Inteligencia Artificial Para la Leucemia Peter Moss") Github Organization.

To clone the repository and install the project, make sure you have Git installed. Now navigate to your HIAS installation project root and then use the following command.

``` bash
 git clone https://github.com/AIIAL/HIASHDI.git
 mv HIASHDI components/hiashdi
```

This will clone the HIAS Historical Data Interface repository and move the cloned repository to the agents directory in the HIAS project (components/hiashdi/).

``` bash
 cd components/
 ls
```

Using the ls command in your home directory should show you the following.

``` bash
 hiashdi
```

Navigate to the **components/hiashdi/** directory in your HIAS project root, this is your project root directory for this tutorial.

### Developer forks

Developers from the Github community that would like to contribute to the development of this project should first create a fork, and clone that repository. For detailed information please view the [CONTRIBUTING](https://github.com/AIIAL/HIASHDI/blob/main/CONTRIBUTING.md "CONTRIBUTING") guide. You should pull the latest code from the development branch.

``` bash
 git clone -b "1.0.0" https://github.com/AIIAL/HIASHDI.git
```

The **-b "1.0.0"** parameter ensures you get the code from the latest master branch. Before using the below command please check our latest master branch in the button at the top of the project README.

## Installation script

All other software requirements are included in **scripts/install.sh**. You can run this file on your machine from the HIAS project root in terminal. Use the following command from the HIAS project root:

``` bash
 sh components/hiashdi/scripts/install.sh
```

&nbsp;

# Service
You will now create a service that will run your IoT Agent. Making sure you are in the HIAS project root, use the following command:

``` bash
sh components/hiashdi/scripts/service.sh
```

&nbsp;

# Continue
Now you can continue to the [API Usage Guide](../usage/api.md)

&nbsp;

# Contributing
Asociación de Investigacion en Inteligencia Artificial Para la Leucemia Peter Moss encourages and welcomes code contributions, bug fixes and enhancements from the Github community.

## Ways to contribute

The following are ways that you can contribute to this project:

- [Bug Report](https://github.com/AIIAL/HIASHDI/issues/new?assignees=&labels=&template=bug_report.md&title=)
- [Feature Request](https://github.com/AIIAL/HIASHDI/issues/new?assignees=&labels=&template=feature_request.md&title=)
- [Feature Proposal](https://github.com/AIIAL/HIASHDI/issues/new?assignees=&labels=&template=feature-proposal.md&title=)
- [Report Vulnerabillity](https://github.com/AIIAL/HIASHDI/issues/new?assignees=&labels=&template=report-a-vulnerability.md&title=)

Please read the [CONTRIBUTING](https://github.com/AIIAL/HIASHDI/blob/main/CONTRIBUTING.md "CONTRIBUTING") document for a contribution guide.

You can also join in with, or create, a discussion in our [Github Discussions](https://github.com/AIIAL/HIASCDI/discussions) area.

## Contributors

All contributors to this project are listed below.

- [Adam Milton-Barker](https://www.leukemiaairesearch.com/association/volunteers/adam-milton-barker "Adam Milton-Barker") - [Asociación de Investigacion en Inteligencia Artificial Para la Leucemia Peter Moss](https://www.leukemiaresearchassociation.ai "Asociación de Investigacion en Inteligencia Artificial Para la Leucemia Peter Moss") President/Founder & Lead Developer, Sabadell, Spain

&nbsp;

# Versioning
We use [SemVer](https://semver.org/) for versioning.

&nbsp;

# License
This project is licensed under the **MIT License** - see the [LICENSE](https://github.com/AIIAL/HIASHDI/blob/main/LICENSE "LICENSE") file for details.

&nbsp;

# Bugs/Issues

You use the [repo issues](https://github.com/AIIAL/HIASHDI/issues/new/choose "repo issues") to track bugs and general requests related to using this project. See [CONTRIBUTING](https://github.com/AIIAL/HIASHDI/blob/main/CONTRIBUTING.md "CONTRIBUTING") for more info on how to submit bugs, feature requests and proposals.