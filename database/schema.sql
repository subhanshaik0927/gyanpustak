-- GyanPustak Database Schema
-- Maximum 25 tables
-- Inheritance: User -> Student, Employee -> Admin / SuperAdmin / SupportStaff

CREATE DATABASE IF NOT EXISTS gyanpustak CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE gyanpustak;

-- ============================================================
-- 1. USER (base table for all users)
-- ============================================================
CREATE TABLE IF NOT EXISTS user (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name    VARCHAR(100) NOT NULL,
    last_name     VARCHAR(100) NOT NULL,
    phone         VARCHAR(20),
    address       TEXT,
    role          ENUM('student','support_staff','admin','super_admin') NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 2. STUDENT (specialization of user)
-- ============================================================
CREATE TABLE IF NOT EXISTS student (
    student_id      INT PRIMARY KEY,
    university_id   INT,
    major           VARCHAR(200),
    student_status  ENUM('graduate','undergraduate') NOT NULL,
    year_of_study   INT,
    date_of_birth   DATE,
    FOREIGN KEY (student_id) REFERENCES user(user_id) ON DELETE CASCADE
);

-- ============================================================
-- 3. EMPLOYEE (base for all staff)
-- ============================================================
CREATE TABLE IF NOT EXISTS employee (
    employee_id   INT PRIMARY KEY,
    emp_number    VARCHAR(50) NOT NULL UNIQUE,
    gender        ENUM('M','F','Other'),
    salary        DECIMAL(10,2),
    aadhaar       VARCHAR(12),
    FOREIGN KEY (employee_id) REFERENCES user(user_id) ON DELETE CASCADE
);

-- ============================================================
-- 4. SUPPORT_STAFF (specialization of employee)
-- ============================================================
CREATE TABLE IF NOT EXISTS support_staff (
    staff_id INT PRIMARY KEY,
    FOREIGN KEY (staff_id) REFERENCES employee(employee_id) ON DELETE CASCADE
);

-- ============================================================
-- 5. ADMIN (specialization of employee)
-- ============================================================
CREATE TABLE IF NOT EXISTS admin (
    admin_id INT PRIMARY KEY,
    FOREIGN KEY (admin_id) REFERENCES employee(employee_id) ON DELETE CASCADE
);

-- ============================================================
-- 6. SUPER_ADMIN (specialization of employee)
-- ============================================================
CREATE TABLE IF NOT EXISTS super_admin (
    super_admin_id INT PRIMARY KEY,
    FOREIGN KEY (super_admin_id) REFERENCES employee(employee_id) ON DELETE CASCADE
);

-- ============================================================
-- 7. UNIVERSITY
-- ============================================================
CREATE TABLE IF NOT EXISTS university (
    university_id   INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(300) NOT NULL,
    address         TEXT,
    rep_first_name  VARCHAR(100),
    rep_last_name   VARCHAR(100),
    rep_email       VARCHAR(255),
    rep_phone       VARCHAR(20)
);

-- Add FK for student after university is created
ALTER TABLE student ADD FOREIGN KEY (university_id) REFERENCES university(university_id);

-- ============================================================
-- 8. DEPARTMENT
-- ============================================================
CREATE TABLE IF NOT EXISTS department (
    dept_id       INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(200) NOT NULL,
    university_id INT NOT NULL,
    FOREIGN KEY (university_id) REFERENCES university(university_id)
);

-- ============================================================
-- 9. INSTRUCTOR
-- ============================================================
CREATE TABLE IF NOT EXISTS instructor (
    instructor_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name    VARCHAR(100) NOT NULL,
    last_name     VARCHAR(100) NOT NULL,
    university_id INT NOT NULL,
    dept_id       INT NOT NULL,
    FOREIGN KEY (university_id) REFERENCES university(university_id),
    FOREIGN KEY (dept_id) REFERENCES department(dept_id)
);

-- ============================================================
-- 10. COURSE
-- ============================================================
CREATE TABLE IF NOT EXISTS course (
    course_id     INT AUTO_INCREMENT PRIMARY KEY,
    course_code   VARCHAR(50) NOT NULL,
    course_name   VARCHAR(300) NOT NULL,
    university_id INT NOT NULL,
    dept_id       INT NOT NULL,
    year          INT,
    semester      VARCHAR(20),
    FOREIGN KEY (university_id) REFERENCES university(university_id),
    FOREIGN KEY (dept_id) REFERENCES department(dept_id)
);

-- ============================================================
-- 11. COURSE_INSTRUCTOR (M:N)
-- ============================================================
CREATE TABLE IF NOT EXISTS course_instructor (
    course_id     INT NOT NULL,
    instructor_id INT NOT NULL,
    PRIMARY KEY (course_id, instructor_id),
    FOREIGN KEY (course_id)     REFERENCES course(course_id),
    FOREIGN KEY (instructor_id) REFERENCES instructor(instructor_id)
);

-- ============================================================
-- 12. BOOK CATEGORY
-- ============================================================
CREATE TABLE IF NOT EXISTS book_category (
    category_id   INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(200) NOT NULL,
    parent_id     INT,
    FOREIGN KEY (parent_id) REFERENCES book_category(category_id)
);

-- ============================================================
-- 13. BOOK
-- ============================================================
CREATE TABLE IF NOT EXISTS book (
    book_id          INT AUTO_INCREMENT PRIMARY KEY,
    title            VARCHAR(500) NOT NULL,
    isbn             VARCHAR(20) NOT NULL UNIQUE,
    publisher        VARCHAR(200),
    publication_date DATE,
    edition          INT DEFAULT 1,
    language         VARCHAR(50) DEFAULT 'English',
    format           ENUM('hardcover','softcover','electronic') NOT NULL,
    book_type        ENUM('new','used') NOT NULL,
    purchase_option  ENUM('rent','buy','both') NOT NULL,
    price            DECIMAL(10,2) NOT NULL,
    quantity         INT NOT NULL DEFAULT 0,
    category_id      INT,
    avg_rating       DECIMAL(3,2) DEFAULT 0.00,
    FOREIGN KEY (category_id) REFERENCES book_category(category_id)
);

-- ============================================================
-- 14. BOOK_AUTHOR (multi-valued)
-- ============================================================
CREATE TABLE IF NOT EXISTS book_author (
    book_id     INT NOT NULL,
    author_name VARCHAR(200) NOT NULL,
    PRIMARY KEY (book_id, author_name),
    FOREIGN KEY (book_id) REFERENCES book(book_id) ON DELETE CASCADE
);

-- ============================================================
-- 15. BOOK_KEYWORD (multi-valued)
-- ============================================================
CREATE TABLE IF NOT EXISTS book_keyword (
    book_id  INT NOT NULL,
    keyword  VARCHAR(100) NOT NULL,
    PRIMARY KEY (book_id, keyword),
    FOREIGN KEY (book_id) REFERENCES book(book_id) ON DELETE CASCADE
);

-- ============================================================
-- 16. COURSE_BOOK (book required/recommended for course)
-- ============================================================
CREATE TABLE IF NOT EXISTS course_book (
    course_id    INT NOT NULL,
    book_id      INT NOT NULL,
    requirement  ENUM('required','recommended') NOT NULL DEFAULT 'required',
    PRIMARY KEY (course_id, book_id),
    FOREIGN KEY (course_id) REFERENCES course(course_id),
    FOREIGN KEY (book_id)   REFERENCES book(book_id)
);

-- ============================================================
-- 17. REVIEW
-- ============================================================
CREATE TABLE IF NOT EXISTS review (
    review_id   INT AUTO_INCREMENT PRIMARY KEY,
    student_id  INT NOT NULL,
    book_id     INT NOT NULL,
    rating      INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_text TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_student_book (student_id, book_id),
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (book_id)    REFERENCES book(book_id)
);

-- ============================================================
-- 18. CART
-- ============================================================
CREATE TABLE IF NOT EXISTS cart (
    cart_id     INT AUTO_INCREMENT PRIMARY KEY,
    student_id  INT NOT NULL UNIQUE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student(student_id)
);

-- ============================================================
-- 19. CART_ITEM
-- ============================================================
CREATE TABLE IF NOT EXISTS cart_item (
    cart_id         INT NOT NULL,
    book_id         INT NOT NULL,
    quantity        INT NOT NULL DEFAULT 1,
    purchase_option ENUM('rent','buy') NOT NULL,
    PRIMARY KEY (cart_id, book_id),
    FOREIGN KEY (cart_id)  REFERENCES cart(cart_id) ON DELETE CASCADE,
    FOREIGN KEY (book_id)  REFERENCES book(book_id)
);

-- ============================================================
-- 20. ORDER
-- ============================================================
CREATE TABLE IF NOT EXISTS `order` (
    order_id          INT AUTO_INCREMENT PRIMARY KEY,
    student_id        INT NOT NULL,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fulfilled_at      TIMESTAMP NULL,
    shipping_type     ENUM('standard','2-day','1-day') NOT NULL DEFAULT 'standard',
    cc_number         VARCHAR(20),
    cc_expiry         VARCHAR(7),
    cc_holder         VARCHAR(200),
    cc_type           ENUM('Visa','MasterCard','RuPay','Amex'),
    order_status      ENUM('new','processed','awaiting shipping','shipped','canceled') NOT NULL DEFAULT 'new',
    FOREIGN KEY (student_id) REFERENCES student(student_id)
);

-- ============================================================
-- 21. ORDER_ITEM
-- ============================================================
CREATE TABLE IF NOT EXISTS order_item (
    order_id        INT NOT NULL,
    book_id         INT NOT NULL,
    quantity        INT NOT NULL DEFAULT 1,
    unit_price      DECIMAL(10,2) NOT NULL,
    purchase_option ENUM('rent','buy') NOT NULL,
    PRIMARY KEY (order_id, book_id),
    FOREIGN KEY (order_id) REFERENCES `order`(order_id) ON DELETE CASCADE,
    FOREIGN KEY (book_id)  REFERENCES book(book_id)
);

-- ============================================================
-- 22. TROUBLE_TICKET
-- ============================================================
CREATE TABLE IF NOT EXISTS trouble_ticket (
    ticket_id         INT AUTO_INCREMENT PRIMARY KEY,
    category          ENUM('user profile','products','cart','orders','other') NOT NULL,
    title             VARCHAR(500) NOT NULL,
    description       TEXT NOT NULL,
    solution          TEXT,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at      TIMESTAMP NULL,
    status            ENUM('new','assigned','in-process','completed') NOT NULL DEFAULT 'new',
    created_by_user   INT NOT NULL,
    resolved_by_admin INT NULL,
    FOREIGN KEY (created_by_user)   REFERENCES user(user_id),
    FOREIGN KEY (resolved_by_admin) REFERENCES admin(admin_id)
);

-- ============================================================
-- 23. TICKET_STATUS_LOG (status change history)
-- ============================================================
CREATE TABLE IF NOT EXISTS ticket_status_log (
    log_id      INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id   INT NOT NULL,
    old_status  ENUM('new','assigned','in-process','completed'),
    new_status  ENUM('new','assigned','in-process','completed') NOT NULL,
    changed_by  INT NOT NULL,
    changed_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id)  REFERENCES trouble_ticket(ticket_id),
    FOREIGN KEY (changed_by) REFERENCES user(user_id)
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX idx_book_title   ON book(title);
CREATE INDEX idx_book_isbn    ON book(isbn);
CREATE INDEX idx_ticket_status ON trouble_ticket(status);
CREATE INDEX idx_order_student ON `order`(student_id);
