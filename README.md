<a name="readme-top"></a>

<!-- PROJECT SHIELDS -->
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]

<div align="center">
  <h3 align="center">PUP Student Council Online Election System</h3>
  <p align="center">
    For hosting elections in an online setup, linked with Microsoft Webmail.
  </p>
</div>

## About the Project

This project enables the Polytechnic University of the Philippines Student Council
to host elections online, automating most processes instead of physical voting
or Microsoft/Google Forms.

The software is submitted in partial fulfillment of the requirements for the course
**Software Engineering 1** and **Software Engineering 2** under the
*Computer Science* program of the Polytechnic University of the Philippines.

## Features

1. Initiate and manage an election, including the following information:
- Positions to run for
- Candidates
2. Manage Voters
3. Manage Ballots
4. Automatic Counting (with a coin-toss type tiebreaker facility)

## Todo for the Project

- [x] Main Voting Facility
- [x] Link Voters via Microsoft Account (Webmail)
- [ ] Ballot Signing and Validation
- [ ] Revamp User Interface

## Built With

This website is built with the following technologies:

[![Python][Python-shield]][Python-docs]
[![Django][Django-shield]][Django-docs]

## Installation

Install the following beforehand:

1. Python 3.x
1. pipenv - `pip install pipenv`

To run on your development machine, do the following steps:

1. Clone the repo - `git clone https://github.com/QueebSkeleton/taglish-hybrid-integrated-hmm-pos.git`
1. Open the project directory on your terminal.
1. Install dependencies - `pipenv install`
1. Run a shell with the created virtualenv - `pipenv shell`
1. Run database migrations - `python manage.py migrate`
1. Create an admin account for the website - `python manage.py createsuperuser`
then follow the instructions.
1. Run the dev server - `python manage.py runserver`

Then, the instance will now run on your local machine. Endpoints are:

1. `localhost:8000` - the index page of the application.
1. `localhost:8000/admin` - Django admin for initiating and managing elections.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- Markdown Links & Images -->
[stars-shield]: https://img.shields.io/github/stars/QueebSkeleton/pup-sc-online-election-system?style=for-the-badge
[stars-url]: https://github.com/QueebSkeleton/pup-sc-online-election-system/stargazers
[issues-shield]: https://img.shields.io/github/issues/QueebSkeleton/pup-sc-online-election-system?style=for-the-badge
[issues-url]: https://github.com/QueebSkeleton/pup-sc-online-election-system/issues

[Python-shield]: https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54
[Python-docs]: https://www.python.org/
[Django-shield]: https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white
[Django-docs]: https://www.djangoproject.com/
