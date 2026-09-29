import os
from flask import Flask
from dotenv import load_dotenv
from flask import render_template, request, redirect, url_for, flash
from db import get_connection

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")


# ==========================================
# DASHBOARD
# ==========================================
@app.route("/")
def home():
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM STUDENTS),
                    (SELECT COUNT(*) FROM APPLICATIONS),
                    (SELECT COUNT(*) FROM PLACEMENTS),
                    (SELECT COUNT(*) FROM COMPANIES),
                    (SELECT COUNT(*) FROM JOBS),
                    (SELECT COUNT(*) FROM INTERVIEWS),
                    (SELECT NVL(MAX(PACKAGE_LPA), 0) FROM PLACEMENTS)
                FROM DUAL
            """)

            result = cursor.fetchone()

        total_students = result[0]
        total_placements = result[2]

        placement_rate = (
            (total_placements / total_students) * 100
            if total_students > 0 else 0
        )

        stats = {
            "students": total_students,
            "applications": result[1],
            "placements": total_placements,
            "companies": result[3],
            "jobs": result[4],
            "interviews": result[5],
            "placement_rate": placement_rate,
            "highest_package": result[6]
        }

        return render_template("index.html", stats=stats)

    except Exception as e:
        print("Dashboard database error:", e)
        return "Unable to load dashboard data. Check the Flask terminal.", 500

    finally:
        if connection:
            connection.close()


# ==========================================
# VIEW AND SEARCH STUDENTS
# ==========================================
@app.route("/students")
def students():
    connection = None

    try:
        connection = get_connection()
        search = request.args.get("search", "").strip()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    STUDENT_ID,
                    STUDENT_NAME,
                    EMAIL,
                    PHONE,
                    CGPA,
                    DEPARTMENT_ID,
                    GRADUATION_YEAR
                FROM STUDENTS
                WHERE LOWER(STUDENT_NAME) LIKE LOWER(:search)
                   OR TO_CHAR(STUDENT_ID) LIKE :search
                   OR LOWER(EMAIL) LIKE LOWER(:search)
                ORDER BY STUDENT_ID
            """, search=f"%{search}%")

            student_records = cursor.fetchall()

        return render_template(
            "students.html",
            students=student_records,
            search=search
        )

    except Exception as e:
        print("Students page error:", e)
        return "Unable to load student records.", 500

    finally:
        if connection:
            connection.close()


# ==========================================
# ADD STUDENT
# ==========================================
@app.route("/students/add", methods=["GET", "POST"])
def add_student():
    connection = None

    try:
        connection = get_connection()

        if request.method == "POST":
            name = request.form["student_name"].strip()
            email = request.form["email"].strip()
            phone = request.form.get("phone", "").strip() or None
            cgpa = request.form.get("cgpa", "").strip() or None

            department_id = int(request.form["department_id"])

            graduation_year = (
                request.form.get("graduation_year", "").strip() or None
            )

            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO STUDENTS (
                        STUDENT_ID,
                        STUDENT_NAME,
                        EMAIL,
                        PHONE,
                        CGPA,
                        DEPARTMENT_ID,
                        GRADUATION_YEAR
                    )
                    VALUES (
                        STUDENT_ID_SEQ.NEXTVAL,
                        :name,
                        :email,
                        :phone,
                        :cgpa,
                        :department_id,
                        :graduation_year
                    )
                """, {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "cgpa": float(cgpa) if cgpa else None,
                    "department_id": department_id,
                    "graduation_year": (
                        int(graduation_year) if graduation_year else None
                    )
                })

            connection.commit()

            return redirect(url_for("students", added=1))

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT DEPARTMENT_ID, DEPARTMENT_NAME
                FROM DEPARTMENTS
                ORDER BY DEPARTMENT_ID
            """)

            departments = cursor.fetchall()

        return render_template(
            "add_student.html",
            departments=departments
        )

    except Exception as e:
        if connection:
            connection.rollback()

        print("Add student error:", e)
        return "Unable to add student. Check the Flask terminal.", 500

    finally:
        if connection:
            connection.close()


# ==========================================
# EDIT STUDENT
# ==========================================
@app.route("/students/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    connection = None

    try:
        connection = get_connection()

        # ----------------------------------
        # UPDATE STUDENT (POST)
        # ----------------------------------
        if request.method == "POST":

            name = request.form["student_name"].strip()
            email = request.form["email"].strip()
            phone = request.form.get("phone", "").strip() or None
            cgpa = request.form.get("cgpa", "").strip() or None

            department_id = int(request.form["department_id"])

            graduation_year = (
                request.form.get("graduation_year", "").strip() or None
            )

            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE STUDENTS
                    SET
                        STUDENT_NAME = :name,
                        EMAIL = :email,
                        PHONE = :phone,
                        CGPA = :cgpa,
                        DEPARTMENT_ID = :department_id,
                        GRADUATION_YEAR = :graduation_year
                    WHERE STUDENT_ID = :student_id
                """, {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "cgpa": float(cgpa) if cgpa else None,
                    "department_id": department_id,
                    "graduation_year": (
                        int(graduation_year)
                        if graduation_year else None
                    ),
                    "student_id": student_id
                })

                if cursor.rowcount == 0:
                    connection.rollback()
                    return "Student not found.", 404

            connection.commit()

            return redirect(url_for("students", updated=1))

        # ----------------------------------
        # GET EXISTING STUDENT DETAILS
        # ----------------------------------
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    STUDENT_ID,
                    STUDENT_NAME,
                    EMAIL,
                    PHONE,
                    CGPA,
                    DEPARTMENT_ID,
                    GRADUATION_YEAR
                FROM STUDENTS
                WHERE STUDENT_ID = :student_id
            """, student_id=student_id)

            student = cursor.fetchone()

            if student is None:
                return "Student not found.", 404

            cursor.execute("""
                SELECT DEPARTMENT_ID, DEPARTMENT_NAME
                FROM DEPARTMENTS
                ORDER BY DEPARTMENT_ID
            """)

            departments = cursor.fetchall()

        return render_template(
            "edit_student.html",
            student=student,
            departments=departments
        )

    except Exception as e:
        if connection:
            connection.rollback()

        print("Edit student error:", e)
        return "Unable to edit student. Check the Flask terminal.", 500

    finally:
        if connection:
            connection.close()

# ==========================================
# DELETE STUDENT
# ==========================================
@app.route("/students/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM STUDENTS
                WHERE STUDENT_ID = :student_id
            """, {"student_id": student_id})

            if cursor.rowcount == 0:
                connection.rollback()
                return "Student not found.", 404

        connection.commit()

        return redirect(url_for("students", deleted=1))

    except Exception as e:
        if connection:
            connection.rollback()

        print("Delete student error:", e)

        return (
            "Unable to delete this student. "
            "The student may have related records. "
            "Check the Flask terminal for details.",
            500
        )

    finally:
        if connection:
            connection.close()


# ==========================================
# VIEW AND SEARCH COMPANIES
# ==========================================
@app.route("/companies")
def companies():
    connection = None

    try:
        connection = get_connection()
        search = request.args.get("search", "").strip()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COMPANY_ID,
                    COMPANY_NAME,
                    INDUSTRY,
                    LOCATION,
                    HR_EMAIL
                FROM COMPANIES
                WHERE LOWER(COMPANY_NAME) LIKE LOWER(:search)
                   OR TO_CHAR(COMPANY_ID) LIKE :search
                   OR LOWER(INDUSTRY) LIKE LOWER(:search)
                   OR LOWER(LOCATION) LIKE LOWER(:search)
                   OR LOWER(HR_EMAIL) LIKE LOWER(:search)
                ORDER BY COMPANY_ID
            """, search=f"%{search}%")

            company_records = cursor.fetchall()

        return render_template(
            "companies.html",
            companies=company_records,
            search=search
        )

    except Exception as e:
        print("Companies page error:", e)
        return "Unable to load company records.", 500

    finally:
        if connection:
            connection.close()

# ==========================================
# ADD COMPANY
# ==========================================
@app.route("/companies/add", methods=["GET", "POST"])
def add_company():
    connection = None

    try:
        connection = get_connection()

        if request.method == "POST":
            company_name = request.form["company_name"].strip()
            industry = request.form.get("industry", "").strip() or None
            location = request.form.get("location", "").strip() or None
            hr_email = request.form.get("hr_email", "").strip() or None

            if not company_name:
                return "Company name is required.", 400

            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO COMPANIES (
                        COMPANY_ID,
                        COMPANY_NAME,
                        INDUSTRY,
                        LOCATION,
                        HR_EMAIL
                    )
                    VALUES (
                        COMPANY_ID_SEQ.NEXTVAL,
                        :company_name,
                        :industry,
                        :location,
                        :hr_email
                    )
                """, {
                    "company_name": company_name,
                    "industry": industry,
                    "location": location,
                    "hr_email": hr_email
                })

            connection.commit()

            return redirect(url_for("companies", added=1))

        return render_template("add_company.html")

    except Exception as e:
        if connection:
            connection.rollback()

        print("Add company error:", e)
        return "Unable to add company. Check the Flask terminal.", 500

    finally:
        if connection:
            connection.close()
            
@app.route("/companies/edit/<int:company_id>", methods=["GET", "POST"])
def edit_company(company_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if request.method == "POST":
            company_name = request.form["company_name"]
            industry = request.form["industry"]
            location = request.form["location"]
            hr_email = request.form["hr_email"]

            cursor.execute("""
                UPDATE companies
                SET company_name = :company_name,
                    industry = :industry,
                    location = :location,
                    hr_email = :hr_email
                WHERE company_id = :company_id
            """, {
                "company_name": company_name,
                "industry": industry,
                "location": location,
                "hr_email": hr_email,
                "company_id": company_id
            })

            conn.commit()
            flash("Company updated successfully!", "success")
            return redirect(url_for("companies"))

        cursor.execute("""
            SELECT company_id, company_name, industry,
                   location, hr_email
            FROM companies
            WHERE company_id = :company_id
        """, {"company_id": company_id})

        company = cursor.fetchone()

        if company is None:
            flash("Company not found.", "error")
            return redirect(url_for("companies"))

        return render_template("edit_company.html", company=company)

    except Exception as e:
        conn.rollback()
        print("Error editing company:", e)
        flash("Unable to update company. Check the Flask terminal.", "error")
        return redirect(url_for("companies"))

    finally:
        cursor.close()
        conn.close()
        
@app.route("/companies/delete/<int:company_id>", methods=["POST"])
def delete_company(company_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            DELETE FROM companies
            WHERE company_id = :company_id
        """, {"company_id": company_id})

        if cursor.rowcount == 0:
            flash("Company not found.", "error")
        else:
            conn.commit()
            flash("Company deleted successfully!", "success")

    except Exception as e:
        conn.rollback()
        print("Error deleting company:", e)
        flash(
            "Could not delete company. It may be linked to existing job records.",
            "error"
        )

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("companies"))


@app.route("/jobs")
def jobs():
    search = request.args.get("search", "").strip()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = """
            SELECT
                j.job_id,
                j.company_id,
                c.company_name,
                j.job_title,
                j.job_type,
                j.salary,
                j.minimum_cgpa,
                j.job_location
            FROM jobs j
            JOIN companies c
                ON j.company_id = c.company_id
            WHERE
                TO_CHAR(j.job_id) LIKE :search
                OR TO_CHAR(j.company_id) LIKE :search
                OR LOWER(c.company_name) LIKE LOWER(:search)
                OR LOWER(j.job_title) LIKE LOWER(:search)
                OR LOWER(j.job_type) LIKE LOWER(:search)
                OR LOWER(j.job_location) LIKE LOWER(:search)
            ORDER BY j.job_id
        """

        search_value = f"%{search}%"

        cursor.execute(query, {
            "search": search_value
        })

        jobs_list = cursor.fetchall()

        return render_template(
            "jobs.html",
            jobs=jobs_list,
            search=search
        )

    except Exception as e:
        print("Error loading jobs:", e)
        return "Unable to load jobs. Check the Flask terminal.", 500

    finally:
        cursor.close()
        conn.close()

@app.route("/jobs/add", methods=["GET", "POST"])
def add_job():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if request.method == "POST":
            company_id = request.form["company_id"]
            job_title = request.form["job_title"].strip()
            job_type = request.form["job_type"].strip()
            salary = request.form.get("salary") or None
            minimum_cgpa = request.form.get("minimum_cgpa") or None
            job_location = request.form["job_location"].strip()

            cursor.execute("""
                INSERT INTO jobs (
                    job_id,
                    company_id,
                    job_title,
                    job_type,
                    salary,
                    minimum_cgpa,
                    job_location
                )
                VALUES (
                    job_id_seq.NEXTVAL,
                    :company_id,
                    :job_title,
                    :job_type,
                    :salary,
                    :minimum_cgpa,
                    :job_location
                )
            """, {
                "company_id": int(company_id),
                "job_title": job_title,
                "job_type": job_type or None,
                "salary": float(salary) if salary else None,
                "minimum_cgpa": (
                    float(minimum_cgpa) if minimum_cgpa else None
                ),
                "job_location": job_location or None
            })

            conn.commit()
            flash("Job added successfully!", "success")
            return redirect(url_for("jobs"))

        cursor.execute("""
            SELECT company_id, company_name
            FROM companies
            ORDER BY company_name
        """)

        companies_list = cursor.fetchall()

        return render_template(
            "add_job.html",
            companies=companies_list
        )

    except Exception as e:
        conn.rollback()
        print("Error adding job:", e)
        flash("Unable to add job. Check the Flask terminal.", "error")
        return redirect(url_for("jobs"))

    finally:
        cursor.close()
        conn.close()

@app.route("/jobs/edit/<int:job_id>", methods=["GET", "POST"])
def edit_job(job_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if request.method == "POST":
            company_id = request.form["company_id"]
            job_title = request.form["job_title"].strip()
            job_type = request.form.get("job_type") or None
            salary = request.form.get("salary") or None
            minimum_cgpa = request.form.get("minimum_cgpa") or None
            job_location = request.form.get("job_location") or None

            cursor.execute("""
                UPDATE JOBS
                SET COMPANY_ID = :company_id,
                    JOB_TITLE = :job_title,
                    JOB_TYPE = :job_type,
                    SALARY = :salary,
                    MINIMUM_CGPA = :minimum_cgpa,
                    JOB_LOCATION = :job_location
                WHERE JOB_ID = :job_id
            """, {
                "company_id": company_id,
                "job_title": job_title,
                "job_type": job_type,
                "salary": salary,
                "minimum_cgpa": minimum_cgpa,
                "job_location": job_location,
                "job_id": job_id
            })

            conn.commit()
            flash("Job updated successfully!", "success")
            return redirect(url_for("jobs"))

        cursor.execute("""
            SELECT JOB_ID, COMPANY_ID, JOB_TITLE, JOB_TYPE,
                   SALARY, MINIMUM_CGPA, JOB_LOCATION
            FROM JOBS
            WHERE JOB_ID = :job_id
        """, {"job_id": job_id})

        job = cursor.fetchone()

        if not job:
            flash("Job not found.", "error")
            return redirect(url_for("jobs"))

        cursor.execute("""
            SELECT COMPANY_ID, COMPANY_NAME
            FROM COMPANIES
            ORDER BY COMPANY_NAME
        """)
        companies = cursor.fetchall()

        return render_template(
            "edit_job.html",
            job=job,
            companies=companies
        )

    except Exception as e:
        conn.rollback()
        print("Error editing job:", e)
        flash("Could not update job. Check the Flask terminal.", "error")
        return redirect(url_for("jobs"))

    finally:
        cursor.close()
        conn.close()


@app.route("/jobs/delete/<int:job_id>", methods=["POST"])
def delete_job(job_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM JOBS WHERE JOB_ID = :job_id",
            {"job_id": job_id}
        )

        if cursor.rowcount == 0:
            flash("Job not found.", "error")
        else:
            conn.commit()
            flash("Job deleted successfully!", "success")

    except Exception as e:
        conn.rollback()
        print("Error deleting job:", e)
        flash(
            "Could not delete job. It may be linked to applications.",
            "error"
        )

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("jobs"))

# ==============================
# APPLICATIONS
# ==============================

@app.route("/applications")
def applications():
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        search = request.args.get("search", "").strip()

        query = """
            SELECT
                a.APPLICATION_ID,
                a.STUDENT_ID,
                s.STUDENT_NAME,
                a.JOB_ID,
                j.JOB_TITLE,
                c.COMPANY_NAME,
                a.APPLICATION_DATE,
                a.STATUS
            FROM APPLICATIONS a
            JOIN STUDENTS s
                ON a.STUDENT_ID = s.STUDENT_ID
            JOIN JOBS j
                ON a.JOB_ID = j.JOB_ID
            JOIN COMPANIES c
                ON j.COMPANY_ID = c.COMPANY_ID
        """

        params = {}

        if search:
            query += """
                WHERE
                    TO_CHAR(a.APPLICATION_ID) LIKE :search
                    OR TO_CHAR(a.STUDENT_ID) LIKE :search
                    OR LOWER(s.STUDENT_NAME) LIKE LOWER(:search)
                    OR TO_CHAR(a.JOB_ID) LIKE :search
                    OR LOWER(j.JOB_TITLE) LIKE LOWER(:search)
                    OR LOWER(c.COMPANY_NAME) LIKE LOWER(:search)
                    OR LOWER(a.STATUS) LIKE LOWER(:search)
            """

            params["search"] = f"%{search}%"

        query += " ORDER BY a.APPLICATION_ID"

        cursor.execute(query, params)

        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

        applications_list = [
            dict(zip(columns, row))
            for row in rows
        ]

        return render_template(
            "applications.html",
            applications=applications_list,
            search=search
        )

    except Exception as e:
        print("Error loading applications:", e)
        raise

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()
            
# ==============================
# ADD APPLICATION
# ==============================

@app.route("/applications/add", methods=["GET", "POST"])
def add_application():
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        if request.method == "POST":
            student_id = request.form.get("student_id")
            job_id = request.form.get("job_id")
            status = request.form.get("status")

            cursor.execute("""
                INSERT INTO APPLICATIONS (
                    APPLICATION_ID,
                    STUDENT_ID,
                    JOB_ID,
                    APPLICATION_DATE,
                    STATUS
                )
                VALUES (
                    APPLICATION_ID_SEQ.NEXTVAL,
                    :student_id,
                    :job_id,
                    SYSDATE,
                    :status
                )
            """, {
                "student_id": int(student_id),
                "job_id": int(job_id),
                "status": status
            })

            conn.commit()

            flash("Application added successfully!", "success")
            return redirect(url_for("applications"))

        # Load students for dropdown
        cursor.execute("""
            SELECT STUDENT_ID, STUDENT_NAME
            FROM STUDENTS
            ORDER BY STUDENT_NAME
        """)
        students = cursor.fetchall()

        # Load jobs and their company names
        cursor.execute("""
            SELECT
                j.JOB_ID,
                j.JOB_TITLE,
                c.COMPANY_NAME
            FROM JOBS j
            JOIN COMPANIES c
                ON j.COMPANY_ID = c.COMPANY_ID
            ORDER BY j.JOB_TITLE
        """)
        jobs = cursor.fetchall()

        return render_template(
            "add_application.html",
            students=students,
            jobs=jobs
        )

    except Exception as e:
        if conn:
            conn.rollback()

        print("Error adding application:", e)
        flash("Could not add application. Please check the details.", "danger")

        return redirect(url_for("applications"))

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()
            

@app.route("/applications/edit/<int:application_id>", methods=["GET", "POST"])
def edit_application(application_id):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Update application when the form is submitted
        if request.method == "POST":
            student_id = request.form.get("student_id")
            job_id = request.form.get("job_id")
            status = request.form.get("status")

            cursor.execute("""
                UPDATE APPLICATIONS
                SET STUDENT_ID = :student_id,
                    JOB_ID = :job_id,
                    STATUS = :status
                WHERE APPLICATION_ID = :application_id
            """, {
                "student_id": student_id,
                "job_id": job_id,
                "status": status,
                "application_id": application_id
            })

            if cursor.rowcount == 0:
                conn.rollback()
                flash("Application not found.", "error")
                return redirect(url_for("applications"))

            conn.commit()
            flash("Application updated successfully!", "success")
            return redirect(url_for("applications"))

        # Get the application to edit
        cursor.execute("""
            SELECT APPLICATION_ID, STUDENT_ID, JOB_ID,
                   APPLICATION_DATE, STATUS
            FROM APPLICATIONS
            WHERE APPLICATION_ID = :application_id
        """, {"application_id": application_id})

        row = cursor.fetchone()

        if not row:
            flash("Application not found.", "error")
            return redirect(url_for("applications"))

        application = {
            "APPLICATION_ID": row[0],
            "STUDENT_ID": row[1],
            "JOB_ID": row[2],
            "APPLICATION_DATE": row[3],
            "STATUS": row[4]
        }

        # Get students for the dropdown
        cursor.execute("""
            SELECT STUDENT_ID, STUDENT_NAME
            FROM STUDENTS
            ORDER BY STUDENT_NAME
        """)
        students = cursor.fetchall()

        # Get jobs for the dropdown
        cursor.execute("""
            SELECT JOB_ID, JOB_TITLE
            FROM JOBS
            ORDER BY JOB_TITLE
        """)
        jobs = cursor.fetchall()

        return render_template(
            "edit_application.html",
            application=application,
            students=students,
            jobs=jobs
        )

    except Exception as e:
        if conn:
            conn.rollback()

        print("Error editing application:", e)
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/applications/delete/<int:application_id>", methods=["POST"])
def delete_application(application_id):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM APPLICATIONS
            WHERE APPLICATION_ID = :application_id
            """,
            {"application_id": application_id}
        )

        if cursor.rowcount == 0:
            flash("Application not found.", "error")
        else:
            conn.commit()
            flash("Application deleted successfully!", "success")

    except Exception as e:
        if conn:
            conn.rollback()

        flash(
            "Unable to delete application. It may be linked to another record.",
            "error"
        )
        print("Delete application error:", e)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for("applications"))

# =========================================================
# INTERVIEWS MANAGEMENT
# =========================================================

@app.route("/interviews")
def interviews():
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        search = request.args.get("search", "").strip()

        sql = """
            SELECT
                i.INTERVIEW_ID,
                i.APPLICATION_ID,
                s.STUDENT_NAME,
                j.JOB_TITLE,
                c.COMPANY_NAME,
                i.INTERVIEW_DATE,
                i.INTERVIEW_MODE,
                i.RESULT
            FROM INTERVIEWS i
            JOIN APPLICATIONS a
                ON i.APPLICATION_ID = a.APPLICATION_ID
            JOIN STUDENTS s
                ON a.STUDENT_ID = s.STUDENT_ID
            JOIN JOBS j
                ON a.JOB_ID = j.JOB_ID
            JOIN COMPANIES c
                ON j.COMPANY_ID = c.COMPANY_ID
            WHERE
                (:search IS NULL
                 OR LOWER(s.STUDENT_NAME) LIKE LOWER(:pattern)
                 OR LOWER(j.JOB_TITLE) LIKE LOWER(:pattern)
                 OR LOWER(c.COMPANY_NAME) LIKE LOWER(:pattern)
                 OR TO_CHAR(i.INTERVIEW_ID) LIKE :pattern)
            ORDER BY i.INTERVIEW_DATE DESC
        """

        pattern = f"%{search}%"

        cursor.execute(sql, {
            "search": search if search else None,
            "pattern": pattern
        })

        columns = [col[0] for col in cursor.description]
        interview_list = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        return render_template(
            "interviews.html",
            interviews=interview_list,
            search=search
        )

    except Exception as e:
        print("Interviews listing error:", e)
        flash("Unable to load interviews.", "error")
        return render_template(
            "interviews.html",
            interviews=[],
            search=""
        )

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/interviews/add", methods=["GET", "POST"])
def add_interview():
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        if request.method == "POST":
            application_id = request.form.get("application_id")
            interview_date = request.form.get("interview_date")
            interview_mode = request.form.get("interview_mode")
            result = request.form.get("result")

            if not all([
                application_id,
                interview_date,
                interview_mode,
                result
            ]):
                flash("Please fill in all fields.", "error")
            else:
                cursor.execute("""
                    INSERT INTO INTERVIEWS (
                        INTERVIEW_ID,
                        APPLICATION_ID,
                        INTERVIEW_DATE,
                        INTERVIEW_MODE,
                        RESULT
                    )
                    VALUES (
                        (SELECT NVL(MAX(INTERVIEW_ID), 0) + 1
                         FROM INTERVIEWS),
                        :application_id,
                        TO_DATE(:interview_date, 'YYYY-MM-DD"T"HH24:MI'),
                        :interview_mode,
                        :result
                    )
                """, {
                    "application_id": int(application_id),
                    "interview_date": interview_date,
                    "interview_mode": interview_mode,
                    "result": result
                })

                conn.commit()
                flash("Interview added successfully!", "success")
                return redirect(url_for("interviews"))

        cursor.execute("""
            SELECT
                a.APPLICATION_ID,
                s.STUDENT_NAME,
                j.JOB_TITLE,
                c.COMPANY_NAME
            FROM APPLICATIONS a
            JOIN STUDENTS s
                ON a.STUDENT_ID = s.STUDENT_ID
            JOIN JOBS j
                ON a.JOB_ID = j.JOB_ID
            JOIN COMPANIES c
                ON j.COMPANY_ID = c.COMPANY_ID
            ORDER BY a.APPLICATION_ID
        """)

        columns = [col[0] for col in cursor.description]
        applications = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        return render_template(
            "add_interview.html",
            applications=applications
        )

    except Exception as e:
        if conn:
            conn.rollback()
        print("Add interview error:", e)
        flash("Unable to add interview. Check the selected application.", "error")
        return redirect(url_for("add_interview"))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/interviews/edit/<int:interview_id>", methods=["GET", "POST"])
def edit_interview(interview_id):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        if request.method == "POST":
            application_id = request.form.get("application_id")
            interview_date = request.form.get("interview_date")
            interview_mode = request.form.get("interview_mode")
            result = request.form.get("result")

            cursor.execute("""
                UPDATE INTERVIEWS
                SET
                    APPLICATION_ID = :application_id,
                    INTERVIEW_DATE =
                        TO_DATE(:interview_date, 'YYYY-MM-DD"T"HH24:MI'),
                    INTERVIEW_MODE = :interview_mode,
                    RESULT = :result
                WHERE INTERVIEW_ID = :interview_id
            """, {
                "application_id": int(application_id),
                "interview_date": interview_date,
                "interview_mode": interview_mode,
                "result": result,
                "interview_id": interview_id
            })

            if cursor.rowcount == 0:
                flash("Interview not found.", "error")
                conn.rollback()
            else:
                conn.commit()
                flash("Interview updated successfully!", "success")

            return redirect(url_for("interviews"))

        cursor.execute("""
            SELECT
                INTERVIEW_ID,
                APPLICATION_ID,
                TO_CHAR(
                    INTERVIEW_DATE,
                    'YYYY-MM-DD"T"HH24:MI'
                ) AS INTERVIEW_DATE,
                INTERVIEW_MODE,
                RESULT
            FROM INTERVIEWS
            WHERE INTERVIEW_ID = :interview_id
        """, {"interview_id": interview_id})

        row = cursor.fetchone()

        if not row:
            flash("Interview not found.", "error")
            return redirect(url_for("interviews"))

        columns = [col[0] for col in cursor.description]
        interview = dict(zip(columns, row))

        cursor.execute("""
            SELECT
                a.APPLICATION_ID,
                s.STUDENT_NAME,
                j.JOB_TITLE,
                c.COMPANY_NAME
            FROM APPLICATIONS a
            JOIN STUDENTS s
                ON a.STUDENT_ID = s.STUDENT_ID
            JOIN JOBS j
                ON a.JOB_ID = j.JOB_ID
            JOIN COMPANIES c
                ON j.COMPANY_ID = c.COMPANY_ID
            ORDER BY a.APPLICATION_ID
        """)

        columns = [col[0] for col in cursor.description]
        applications = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        return render_template(
            "edit_interview.html",
            interview=interview,
            applications=applications
        )

    except Exception as e:
        if conn:
            conn.rollback()
        print("Edit interview error:", e)
        flash("Unable to edit interview.", "error")
        return redirect(url_for("interviews"))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/interviews/delete/<int:interview_id>", methods=["POST"])
def delete_interview(interview_id):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM INTERVIEWS
            WHERE INTERVIEW_ID = :interview_id
        """, {"interview_id": interview_id})

        if cursor.rowcount == 0:
            flash("Interview not found.", "error")
        else:
            conn.commit()
            flash("Interview deleted successfully!", "success")

    except Exception as e:
        if conn:
            conn.rollback()
        print("Delete interview error:", e)
        flash("Unable to delete interview.", "error")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for("interviews"))


# ============================================================
# PLACEMENTS MODULE
# ============================================================

@app.route("/placements")
def placements():
    search = request.args.get("search", "").strip()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = """
            SELECT
                p.PLACEMENT_ID,
                p.STUDENT_ID,
                s.STUDENT_NAME,
                p.COMPANY_ID,
                c.COMPANY_NAME,
                p.JOB_ID,
                j.JOB_TITLE,
                p.PLACEMENT_DATE,
                p.PACKAGE_LPA
            FROM PLACEMENTS p
            JOIN STUDENTS s
                ON p.STUDENT_ID = s.STUDENT_ID
            JOIN COMPANIES c
                ON p.COMPANY_ID = c.COMPANY_ID
            JOIN JOBS j
                ON p.JOB_ID = j.JOB_ID
            WHERE
                TO_CHAR(p.PLACEMENT_ID) LIKE :search
                OR TO_CHAR(p.STUDENT_ID) LIKE :search
                OR LOWER(s.STUDENT_NAME) LIKE LOWER(:search)
                OR LOWER(c.COMPANY_NAME) LIKE LOWER(:search)
                OR LOWER(j.JOB_TITLE) LIKE LOWER(:search)
                OR TO_CHAR(p.PACKAGE_LPA) LIKE :search
            ORDER BY p.PLACEMENT_ID
        """

        cursor.execute(query, {"search": f"%{search}%"})

        columns = [col[0] for col in cursor.description]
        placements_data = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        return render_template(
            "placements.html",
            placements=placements_data,
            search=search
        )

    except Exception as e:
        flash(f"Error loading placements: {e}", "error")
        return render_template(
            "placements.html",
            placements=[],
            search=search
        )

    finally:
        cursor.close()
        conn.close()


# ------------------------------------------------------------
# ADD PLACEMENT
# ------------------------------------------------------------

@app.route("/placements/add", methods=["GET", "POST"])
def add_placement():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if request.method == "POST":
            student_id = int(request.form["student_id"])
            company_id = int(request.form["company_id"])
            job_id = int(request.form["job_id"])
            placement_date = request.form["placement_date"]
            package_lpa = float(request.form["package_lpa"])

            if package_lpa <= 0:
                flash("Package must be greater than zero.", "error")
                return redirect(url_for("add_placement"))

            # Ensure the selected job belongs to the selected company.
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM JOBS
                WHERE JOB_ID = :job_id
                  AND COMPANY_ID = :company_id
                """,
                {
                    "job_id": job_id,
                    "company_id": company_id
                }
            )

            if cursor.fetchone()[0] == 0:
                flash(
                    "The selected job does not belong to that company.",
                    "error"
                )
                return redirect(url_for("add_placement"))

            cursor.execute(
                """
                INSERT INTO PLACEMENTS (
                    PLACEMENT_ID,
                    STUDENT_ID,
                    COMPANY_ID,
                    JOB_ID,
                    PLACEMENT_DATE,
                    PACKAGE_LPA
                )
                VALUES (
                    PLACEMENT_ID_SEQ.NEXTVAL,
                    :student_id,
                    :company_id,
                    :job_id,
                    TO_DATE(:placement_date, 'YYYY-MM-DD'),
                    :package_lpa
                )
                """,
                {
                    "student_id": student_id,
                    "company_id": company_id,
                    "job_id": job_id,
                    "placement_date": placement_date,
                    "package_lpa": package_lpa
                }
            )

            conn.commit()
            flash("Placement added successfully!", "success")
            return redirect(url_for("placements"))

        # Load students for the dropdown.
        cursor.execute(
            """
            SELECT STUDENT_ID, STUDENT_NAME
            FROM STUDENTS
            ORDER BY STUDENT_NAME
            """
        )
        students = cursor.fetchall()

        # Load companies for the dropdown.
        cursor.execute(
            """
            SELECT COMPANY_ID, COMPANY_NAME
            FROM COMPANIES
            ORDER BY COMPANY_NAME
            """
        )
        companies = cursor.fetchall()

        # Load jobs with their company IDs.
        cursor.execute(
            """
            SELECT JOB_ID, JOB_TITLE, COMPANY_ID
            FROM JOBS
            ORDER BY JOB_TITLE
            """
        )
        jobs = cursor.fetchall()

        return render_template(
            "add_placement.html",
            students=students,
            companies=companies,
            jobs=jobs
        )

    except Exception as e:
        conn.rollback()
        flash(f"Error adding placement: {e}", "error")
        return redirect(url_for("add_placement"))

    finally:
        cursor.close()
        conn.close()


# ------------------------------------------------------------
# EDIT PLACEMENT
# ------------------------------------------------------------

@app.route(
    "/placements/edit/<int:placement_id>",
    methods=["GET", "POST"]
)
def edit_placement(placement_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if request.method == "POST":
            student_id = int(request.form["student_id"])
            company_id = int(request.form["company_id"])
            job_id = int(request.form["job_id"])
            placement_date = request.form["placement_date"]
            package_lpa = float(request.form["package_lpa"])

            if package_lpa <= 0:
                flash("Package must be greater than zero.", "error")
                return redirect(
                    url_for(
                        "edit_placement",
                        placement_id=placement_id
                    )
                )

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM JOBS
                WHERE JOB_ID = :job_id
                  AND COMPANY_ID = :company_id
                """,
                {
                    "job_id": job_id,
                    "company_id": company_id
                }
            )

            if cursor.fetchone()[0] == 0:
                flash(
                    "The selected job does not belong to that company.",
                    "error"
                )
                return redirect(
                    url_for(
                        "edit_placement",
                        placement_id=placement_id
                    )
                )

            cursor.execute(
                """
                UPDATE PLACEMENTS
                SET
                    STUDENT_ID = :student_id,
                    COMPANY_ID = :company_id,
                    JOB_ID = :job_id,
                    PLACEMENT_DATE =
                        TO_DATE(:placement_date, 'YYYY-MM-DD'),
                    PACKAGE_LPA = :package_lpa
                WHERE PLACEMENT_ID = :placement_id
                """,
                {
                    "student_id": student_id,
                    "company_id": company_id,
                    "job_id": job_id,
                    "placement_date": placement_date,
                    "package_lpa": package_lpa,
                    "placement_id": placement_id
                }
            )

            if cursor.rowcount == 0:
                conn.rollback()
                flash("Placement not found.", "error")
                return redirect(url_for("placements"))

            conn.commit()
            flash("Placement updated successfully!", "success")
            return redirect(url_for("placements"))

        # Fetch the placement being edited.
        cursor.execute(
            """
            SELECT
                PLACEMENT_ID,
                STUDENT_ID,
                COMPANY_ID,
                JOB_ID,
                TO_CHAR(PLACEMENT_DATE, 'YYYY-MM-DD'),
                PACKAGE_LPA
            FROM PLACEMENTS
            WHERE PLACEMENT_ID = :placement_id
            """,
            {"placement_id": placement_id}
        )

        placement = cursor.fetchone()

        if not placement:
            flash("Placement not found.", "error")
            return redirect(url_for("placements"))

        placement_data = {
            "PLACEMENT_ID": placement[0],
            "STUDENT_ID": placement[1],
            "COMPANY_ID": placement[2],
            "JOB_ID": placement[3],
            "PLACEMENT_DATE": placement[4],
            "PACKAGE_LPA": placement[5]
        }

        cursor.execute(
            """
            SELECT STUDENT_ID, STUDENT_NAME
            FROM STUDENTS
            ORDER BY STUDENT_NAME
            """
        )
        students = cursor.fetchall()

        cursor.execute(
            """
            SELECT COMPANY_ID, COMPANY_NAME
            FROM COMPANIES
            ORDER BY COMPANY_NAME
            """
        )
        companies = cursor.fetchall()

        cursor.execute(
            """
            SELECT JOB_ID, JOB_TITLE, COMPANY_ID
            FROM JOBS
            ORDER BY JOB_TITLE
            """
        )
        jobs = cursor.fetchall()

        return render_template(
            "edit_placement.html",
            placement=placement_data,
            students=students,
            companies=companies,
            jobs=jobs
        )

    except Exception as e:
        conn.rollback()
        flash(f"Error updating placement: {e}", "error")
        return redirect(url_for("placements"))

    finally:
        cursor.close()
        conn.close()


# ------------------------------------------------------------
# DELETE PLACEMENT
# ------------------------------------------------------------

@app.route(
    "/placements/delete/<int:placement_id>",
    methods=["POST"]
)
def delete_placement(placement_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM PLACEMENTS
            WHERE PLACEMENT_ID = :placement_id
            """,
            {"placement_id": placement_id}
        )

        if cursor.rowcount == 0:
            flash("Placement not found.", "error")
        else:
            conn.commit()
            flash("Placement deleted successfully!", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Error deleting placement: {e}", "error")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("placements"))

# ==========================================
# RUN FLASK APPLICATION
# ==========================================
if __name__ == "__main__":
    app.run(debug=True)