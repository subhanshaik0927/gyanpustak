USE gyanpustak;

-- Universities
INSERT INTO university (name, address, rep_first_name, rep_last_name, rep_email, rep_phone) VALUES
('Indian Institute of Technology Delhi', 'Hauz Khas, New Delhi - 110016', 'Rajesh', 'Kumar', 'rajesh@iitd.ac.in', '9810012345'),
('Delhi University', 'North Campus, Delhi - 110007', 'Priya', 'Sharma', 'priya@du.ac.in', '9811122334'),
('BITS Pilani', 'Pilani, Rajasthan - 333031', 'Anil', 'Verma', 'anil@bits.ac.in', '9812233445');

-- Departments
INSERT INTO department (name, university_id) VALUES
('Computer Science & Engineering', 1),
('Mathematics', 1),
('Computer Science', 2),
('Physics', 2),
('CS & IS', 3),
('Electronics', 3);

-- Users (super admin) - Password: superadmin123
INSERT INTO user (email, password_hash, first_name, last_name, phone, address, role) VALUES
('superadmin@gyanpustak.in', 'scrypt:32768:8:1$VdcuAk4S1VDCmNhg$d8961744b288a465816f6c8dc05632d8d2e27c1fca01e02aca4a0334854fe8d711faca368f6ca3cf39c04891bf16188a5f3647602ee546403e4168591fab2065', 'Super', 'Admin', '9900001111', 'GyanPustak HQ, Bangalore', 'super_admin');

INSERT INTO employee (employee_id, emp_number, gender, salary, aadhaar) VALUES
(1, 'EMP001', 'M', 150000.00, '123456789012');

INSERT INTO super_admin (super_admin_id) VALUES (1);

-- Admin user - Password: admin123
INSERT INTO user (email, password_hash, first_name, last_name, phone, address, role) VALUES
('admin@gyanpustak.in', 'scrypt:32768:8:1$VdcuAk4S1VDCmNhg$d8961744b288a465816f6c8dc05632d8d2e27c1fca01e02aca4a0334854fe8d711faca368f6ca3cf39c04891bf16188a5f3647602ee546403e4168591fab2065', 'Anita', 'Gupta', '9900002222', 'GyanPustak HQ, Bangalore', 'admin');

INSERT INTO employee (employee_id, emp_number, gender, salary, aadhaar) VALUES
(2, 'EMP002', 'F', 80000.00, '234567890123');

INSERT INTO admin (admin_id) VALUES (2);

-- Support staff user - Password: support123
INSERT INTO user (email, password_hash, first_name, last_name, phone, address, role) VALUES
('support@gyanpustak.in', 'scrypt:32768:8:1$VdcuAk4S1VDCmNhg$d8961744b288a465816f6c8dc05632d8d2e27c1fca01e02aca4a0334854fe8d711faca368f6ca3cf39c04891bf16188a5f3647602ee546403e4168591fab2065', 'Ravi', 'Singh', '9900003333', 'GyanPustak HQ, Bangalore', 'support_staff');

INSERT INTO employee (employee_id, emp_number, gender, salary, aadhaar) VALUES
(3, 'EMP003', 'M', 40000.00, '345678901234');

INSERT INTO support_staff (staff_id) VALUES (3);

-- Student users - Password: student123
INSERT INTO user (email, password_hash, first_name, last_name, phone, address, role) VALUES
('student1@iitd.ac.in', 'scrypt:32768:8:1$VdcuAk4S1VDCmNhg$d8961744b288a465816f6c8dc05632d8d2e27c1fca01e02aca4a0334854fe8d711faca368f6ca3cf39c04891bf16188a5f3647602ee546403e4168591fab2065', 'Arjun', 'Mehta', '9811234567', 'Room 301, Hostel 3, IIT Delhi', 'student'),
('student2@du.ac.in', 'scrypt:32768:8:1$VdcuAk4S1VDCmNhg$d8961744b288a465816f6c8dc05632d8d2e27c1fca01e02aca4a0334854fe8d711faca368f6ca3cf39c04891bf16188a5f3647602ee546403e4168591fab2065', 'Sneha', 'Patel', '9822345678', '45B, Model Town, Delhi', 'student');

INSERT INTO student (student_id, university_id, major, student_status, year_of_study, date_of_birth) VALUES
(4, 1, 'Computer Science', 'undergraduate', 3, '2003-06-15'),
(5, 2, 'Mathematics', 'graduate', 1, '2001-09-22');

-- Book categories
INSERT INTO book_category (name, parent_id) VALUES
('Computer Science', NULL),
('Mathematics', NULL),
('Physics', NULL),
('Programming', 1),
('Algorithms', 1),
('Calculus', 2);

-- Books
INSERT INTO book (title, isbn, publisher, publication_date, edition, language, format, book_type, purchase_option, price, quantity, category_id) VALUES
('Introduction to Algorithms', '978-0262046305', 'MIT Press', '2022-04-05', 4, 'English', 'hardcover', 'new', 'both', 1299.00, 50, 5),
('The C Programming Language', '978-0131103627', 'Prentice Hall', '1988-03-22', 2, 'English', 'softcover', 'new', 'buy', 799.00, 30, 4),
('Linear Algebra Done Right', '978-3031410253', 'Springer', '2023-11-01', 4, 'English', 'hardcover', 'new', 'both', 999.00, 20, 6),
('Computer Networks', '978-0132126953', 'Pearson', '2011-03-02', 5, 'English', 'hardcover', 'used', 'rent', 650.00, 15, 1),
('Python Crash Course', '978-1718502703', 'No Starch Press', '2023-01-10', 3, 'English', 'softcover', 'new', 'buy', 849.00, 40, 4);

-- Book authors
INSERT INTO book_author (book_id, author_name) VALUES
(1, 'Thomas H. Cormen'), (1, 'Charles E. Leiserson'), (1, 'Ronald L. Rivest'), (1, 'Clifford Stein'),
(2, 'Brian W. Kernighan'), (2, 'Dennis M. Ritchie'),
(3, 'Sheldon Axler'),
(4, 'Andrew Tanenbaum'), (4, 'David Wetherall'),
(5, 'Eric Matthes');

-- Book keywords
INSERT INTO book_keyword (book_id, keyword) VALUES
(1, 'algorithms'), (1, 'data structures'), (1, 'sorting'), (1, 'graphs'),
(2, 'C'), (2, 'programming'), (2, 'systems'),
(3, 'linear algebra'), (3, 'vectors'), (3, 'matrices'),
(4, 'networking'), (4, 'TCP/IP'), (4, 'protocols'),
(5, 'python'), (5, 'programming'), (5, 'beginner');

-- Instructors
INSERT INTO instructor (first_name, last_name, university_id, dept_id) VALUES
('Naveen', 'Garg', 1, 1),
('S. N.', 'Maheshwari', 1, 1),
('Rekha', 'Agarwal', 2, 3);

-- Courses
INSERT INTO course (course_code, course_name, university_id, dept_id, year, semester) VALUES
('CS101', 'Introduction to Programming', 1, 1, 2025, 'Odd'),
('CS201', 'Data Structures & Algorithms', 1, 1, 2025, 'Even'),
('MA101', 'Linear Algebra', 2, 3, 2025, 'Odd');

-- Course instructors
INSERT INTO course_instructor (course_id, instructor_id) VALUES
(1, 1), (2, 2), (3, 3);

-- Course books
INSERT INTO course_book (course_id, book_id, requirement) VALUES
(1, 2, 'required'), (1, 5, 'recommended'),
(2, 1, 'required'),
(3, 3, 'required');

-- Cart for student 1
INSERT INTO cart (student_id) VALUES (4);

-- Cart items
INSERT INTO cart_item (cart_id, book_id, quantity, purchase_option) VALUES
(1, 1, 1, 'buy'),
(1, 5, 1, 'rent');

-- Sample order for student 2
INSERT INTO `order` (student_id, shipping_type, cc_number, cc_expiry, cc_holder, cc_type, order_status) VALUES
(5, 'standard', '4111111111111111', '12/27', 'Sneha Patel', 'Visa', 'processed');

INSERT INTO order_item (order_id, book_id, quantity, unit_price, purchase_option) VALUES
(1, 3, 1, 999.00, 'buy');

-- Trouble tickets
INSERT INTO trouble_ticket (category, title, description, status, created_by_user) VALUES
('products', 'Book page not loading', 'When I click on Introduction to Algorithms, the page shows a 500 error.', 'new', 4),
('orders', 'Order not showing up', 'I placed an order yesterday but it doesnt appear in my order history.', 'assigned', 5);

INSERT INTO ticket_status_log (ticket_id, old_status, new_status, changed_by) VALUES
(2, 'new', 'assigned', 3);

-- Reviews
INSERT INTO review (student_id, book_id, rating, review_text) VALUES
(4, 5, 5, 'Excellent book for Python beginners! Very well structured.'),
(5, 3, 4, 'Great for linear algebra. Some proofs are dense but worth it.');

-- Update book ratings
UPDATE book SET avg_rating = 5.0 WHERE book_id = 5;
UPDATE book SET avg_rating = 4.0 WHERE book_id = 3;
