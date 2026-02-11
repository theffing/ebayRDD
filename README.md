# eBay Mimic - Extended Use Relational Database
Illinois Tech CS 727 - Course Project
Relational Database Implementation and Applications
___

A Relational Database consisting of the most essential information required for eBay's service.

Includes relevant data to normal usage as well as; relationships, semantics, constraints, users, and users' needs, and interesting use cases.
(A description of how a user might interact with a database, system, or process to achieve a specific goal or perform particular task)

## ERD Diagram - Relational Database Design

![eBay RDD Diagram](eBayRDD.drawio.png "RDD Diagram")

### Prerequisites

- PostgreSQL 16+ installed on your system
- Access to `sudo` for service management (if needed)

### PostgreSQL Installation (if needed)

Install it using:

```bash
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib
```

### Starting PostgreSQL Service

Start the PostgreSQL service:

```bash
sudo systemctl start postgresql
```

Verify PostgreSQL is running:

```bash
pg_isready
```

### Creating a PostgreSQL User/Role

If you don't have a PostgreSQL role for your current user, create one:

```bash
sudo -u postgres createuser -s $USER
```

This creates a superuser role with the same name as your current system user.

### Creating the Database

Create a new database for the eBay mimic project:

```bash
createdb ebay_db
```

### Loading the Database Schema and Data

To create all tables and load the data, run:

```bash
psql -d ebay_db -f ebay_db.sql
```

This command will:
1. Drop existing tables (if any) to ensure a clean slate
2. Create all tables with proper constraints and relationships
3. Create indexes for optimized queries
4. Create functions, triggers, and stored procedures
5. Insert seed data into all tables
6. Create views for common queries
7. Display sample query results

### Verifying the Installation

After running the SQL file, verify the database was created successfully:

```bash
psql -d ebay_db -c "\dt"
```

This lists all tables in the database. You should see:
- `user_account`
- `category`
- `listing`
- `user_listing_watch`
- `bid`
- `transaction`
- `feedback`

### Connecting to the Database

To connect to the database interactively:

```bash
psql -d ebay_db
```

Once connected, you can run SQL queries, view tables, and interact with the database.

### Quick Reference Commands

```bash
# Start PostgreSQL
sudo systemctl start postgresql

# Create database
createdb ebay_db

# Load schema and data
psql -d ebay_db -f ebay_db.sql

# Connect to database
psql -d ebay_db

# List all tables
psql -d ebay_db -c "\dt"

# View a specific table
psql -d ebay_db -c "SELECT * FROM user_account LIMIT 5;"
```