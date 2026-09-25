# Student Placement Management System

A database management project built using **Oracle SQL and PL/SQL** to manage student placement activities, job applications, interviews, and placement records.

## Overview

The Student Placement Management System provides a structured database for maintaining student information, departments, skills, companies, job opportunities, applications, interviews, and placement details.

The project demonstrates relational database design, SQL queries, joins, subqueries, views, stored procedures, functions, triggers, indexes, and transaction control.

## Technologies Used

* Oracle AI Database 26ai Free
* Oracle SQL
* PL/SQL
* Oracle SQL Developer

## Database Schema

The database contains 9 main tables:

| Table            | Purpose                         |
| ---------------- | ------------------------------- |
| `DEPARTMENTS`    | Stores department information   |
| `STUDENTS`       | Stores student details          |
| `SKILLS`         | Stores available skills         |
| `STUDENT_SKILLS` | Maps students to their skills   |
| `COMPANIES`      | Stores company information      |
| `JOBS`           | Stores job opportunities        |
| `APPLICATIONS`   | Tracks student job applications |
| `INTERVIEWS`     | Stores interview details        |
| `PLACEMENTS`     | Stores placement records        |

## Features

* Student and department management
* Student skill tracking
* Company and job management
* Job application tracking
* Interview management
* Placement and package records
* SQL queries using joins, subqueries, aggregate functions, `GROUP BY`, and `HAVING`
* Views for student and placement reports
* Stored procedures and user-defined functions
* Triggers for data validation
* Indexing and transaction control using `COMMIT`, `SAVEPOINT`, and `ROLLBACK`

## Database Objects

| Object       | Count |
| ------------ | ----: |
| Tables       |     9 |
| SQL queries  |    15 |
| Views        |     2 |
| Procedures   |     2 |
| Functions    |     2 |
| Triggers     |     2 |
| Custom index |     1 |

## Sample Data

The database includes sample records for students, departments, skills, companies, jobs, applications, interviews, and placements.

## Project Structure

```text
Student-Placement-Management-System/
├── README.md
├── sql/
│   └── 01_database_export.sql
└── screenshots/
    ├── tables/
    ├── queries/
    ├── views/
    ├── procedures/
    ├── functions/
    ├── triggers/
    └── transactions/
```

## Setup and Usage

1. Install Oracle Database and Oracle SQL Developer.
2. Create or connect to an Oracle schema with the required privileges.
3. Open `sql/01_database_export.sql` in SQL Developer.
4. Review the script before execution. It contains database object definitions and sample data.
5. Execute the script using **Run Script (F5)**.
6. Verify that the tables and other database objects are created successfully.

**Note:** The export script is intended to recreate the project in a suitable schema. Do not run it against a schema that already contains these objects unless you have reviewed the script and understand the effects.

## Screenshots

Screenshots demonstrating the database tables, SQL queries, views, procedures, functions, triggers, index, and transaction operations are available in the `screenshots/` directory.

## Author

**Sanket**

## License

This project is available for educational and learning purposes.
