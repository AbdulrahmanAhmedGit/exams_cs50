# Online Exam Platform

## Overview

The Online Exam Platform is a web-based application that allows administrators to create, manage, and conduct online exams. Students can take exams, and their results are evaluated automatically. The platform is designed to simplify the examination process, reduce paperwork, and ensure a seamless experience for both students and administrators.

## Features

* User authentication (Admin and Student roles).
* Admin can create, update, and delete exams.
* Admin can add, update, and delete questions.
* Students can register, log in, and take exams.
* Automatic evaluation of answers and result generation.
* Secure session management.

## Technologies Used

* **Backend:** Flask (Python)
* **Frontend:** HTML, CSS, JavaScript
* **Database:** SQLite
* **Other Tools:** Git, CS50 Library for SQL

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/AbdulrahmanAhmedGit/exams_cs50.git
   cd project
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Initialize the database:

   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

4. Run the application:

   ```bash
   flask run
   ```

5. Open your browser and navigate to:

   ```
   http://127.0.0.1:5000
   ```

## Usage

* **Admin**:

  * Create and manage exams and questions.
  * Monitor student progress and results.
* **Student**:

  * Register or log in to the platform.
  * Attempt available exams and view results.

## Folder Structure

```
project/
│
├── static/            # CSS, JS, images
├── templates/         # HTML templates
├── app.py             # Main application
├── models.py          # Database models
├── requirements.txt   # Python dependencies
└── README.md          # Documentation
```

## Contribution

Contributions are welcome! If you’d like to improve the project, feel free to fork the repository, create a branch, and submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
