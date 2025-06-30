Corporate Treasury System
A web-based treasury management application built with Streamlit and SQLite, designed to manage financial transactions, allocations, investments, reconciliations, and user/department administration for a corporate treasury. The system provides a user-friendly interface for admins and department users to handle financial operations efficiently.
Features

Dashboard: Displays key metrics (Main Account balance, Treasury balance, department count, transaction count) and visualizations (department balances, investment distribution, account distribution).
Transactions: Supports adding individual transactions or bulk uploads via CSV, with tax calculations and main account balance updates.
Allocations: Allows allocation of transactions to departments, with balance checks to prevent overdrafts.
Statements: Enables downloading transaction statements and viewing uploaded statements.
Investments: Manages investment transactions, including allocation, confirmation, and deal note generation.
Reconciliation: Validates transaction taxes against defined rates and identifies discrepancies.
Tariff & Tax: Manages bank tariff guides (PDF uploads) and tax rates.
User Management: Admin-only feature to add departments and users with role-based access (admin or user).
Security: Uses SHA-256 password hashing and role-based access control.
Database: Utilizes SQLite for persistent storage of transactions, allocations, investments, and user data.

Prerequisites

Python: Version 3.8 or higher (download).
Dependencies:
streamlit
pandas
matplotlib
plotly
Built-in Python libraries: sqlite3, uuid, hashlib


Environment: A terminal or command prompt with write access to the project directory.

Installation

Clone or Download the Repository:

Clone the repository or download the source code to a local directory (e.g., treasury_system).

git clone <repository-url>
cd treasury_system


Set Up a Virtual Environment (recommended):
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


Install Dependencies:
pip install streamlit pandas matplotlib plotly


Verify Code:

Ensure the main application file is named app.py and contains the provided source code.



Running the Application

Start the Streamlit Server:

Navigate to the project directory:cd path/to/treasury_system


Run the application:streamlit run app.py


The application will start at http://localhost:8501. If the port is in use, specify a different port:streamlit run app.py --server.port 8502




Access the Application:

Open a web browser and navigate to http://localhost:8501 (or the specified port).
Log in with the default admin credentials:
Username: admin
Password: admin123




Initialize the Database:

On first run, the application creates a SQLite database (treasury.db) with necessary tables and initializes:
A default admin user (admin/admin123).
A Main Account with a balance of 0.
A Treasury department.





Usage
Login

Use the default admin credentials or create new users via the "User Management" section (admin only).
Non-admin users have access to Dashboard, Statements, Investments, and Allocations.

Key Features

Dashboard: View financial metrics and visualizations.
Transactions:
Add individual transactions with debit/credit amounts, tax calculations, and account selection.
Upload bulk transactions via CSV (download the template from the app). Example CSV format:transaction_date,value_date,narration,ref_number,debit_amount,credit_amount,tax_percentage,tax_amount
2024-01-15,2024-01-15,Office Supplies,INV1001,500,0,15,75


Select an account (e.g., "CBZ Account One") during bulk upload.


Allocations: Assign transaction amounts to departments, ensuring sufficient balances.
Investments: Create, allocate, and confirm investments, with deal note generation.
Statements: Download transaction statements for a date range or view uploaded statements.
Reconciliation: Verify tax calculations and identify discrepancies.
Tariff & Tax: Upload bank tariff guides (PDF) and manage tax rates.
User Management: Add departments and users (admin only).

Stopping the Application

Press Ctrl+C in the terminal to stop the Streamlit server.
Deactivate the virtual environment (if used):deactivate



Troubleshooting

Streamlit Not Found:
Ensure Streamlit is installed in the active environment:pip install streamlit




Database Issues:
Verify write permissions in the project directory for treasury.db.
If corrupted, delete treasury.db and rerun to reinitialize.


CSV Upload Errors:
Ensure the CSV matches the template format (download from the app).
Check for hidden characters or BOM using a text editor (e.g., Notepad++, VS Code).
Debug by adding a print statement in app.py (around line 560):st.write(f"Raw CSV row {index + 2}: {row.to_dict()}")




Port Conflicts:
Use a different port if 8501 is occupied:streamlit run app.py --server.port 8502




Browser Issues:
Use Chrome, Firefox, or Edge and clear the cache if the interface fails to load.



Security Notes

Default Credentials: Change the default admin password (admin123) in the users table for production use.
Database: SQLite is suitable for small-scale use. For production, consider PostgreSQL for scalability and security.
Deployment: For production, enable SSL and secure the database. Deploy on platforms like Streamlit Community Cloud, Heroku, or AWS.

Development Notes

Code Structure: The application is contained in app.py, using Streamlit for the UI and SQLite for data storage.
Dependencies: Managed via pip. Consider creating a requirements.txt:streamlit
pandas
matplotlib
plotly


Database Schema: Includes tables for main_account, users, departments, transactions, statements, investments, allocations, taxes_tariffs, audit_logs, and bank_tariff_guides.
Fixes: The bulk transaction upload issue (related to None values in credit_type for debit transactions) is resolved by allowing valid None values for credit_type (debit) and debit_type (credit).

Contributing
Contributions are welcome! To contribute:

Fork the repository.
Create a feature branch (git checkout -b feature-name).
Commit changes (git commit -m "Add feature").
Push to the branch (git push origin feature-name).
Open a pull request.

License
This project is licensed under the MIT License.
Contact
For support or inquiries, contact the project maintainer at +263714242685.
