# Suppliers Scorecard Project

<img src="images/a8abd29a96d4222680540c6bd2e3595e.png" alt="Cummins Logo" width="200"/>


---

## Overview

This project was developed as part of an internship program at **Cummins**, aiming to monitor, analyze, and improve the **performance of suppliers** through a robust and interactive scorecard system. The solution centralizes data collection, visualization, and communication, helping the supply chain team make data-driven decisions.

---

## Key Features

### 📊 Performance Trend Graphs  
- Interactive charts display supplier KPIs over multiple tracking periods: **12 months**, **6 months**, and **quarterly averages**.  
- This multi-period tracking enables early detection of trends, allowing the supply chain team to anticipate supplier performance changes and proactively manage risks or improvements.  
- Trend analysis helps identify consistent patterns, sudden drops, or improvements in quality, delivery, and compliance metrics.  
- Graphs are generated dynamically using Python libraries like matplotlib and Plotly, enabling rich, customizable visuals.

### 🗃️ SQL Database Integration  
- Supplier data, criteria, and performance history are stored in a **SQLite** relational database.  
- Efficient querying allows quick access to historical and current supplier performance data.  
- Enables easy updates and maintenance of supplier records and evaluation criteria.

### 📈 Power BI Export  
- The system can export consolidated performance data into Excel-compatible formats.  
- Exported files are optimized for seamless import into **Power BI**, allowing advanced visualization, filtering, and dashboard creation by the business team.  
- Facilitates integration with the broader corporate analytics ecosystem.

### 📧 Automated Email Notifications  
- Automated generation and sending of performance summary emails to suppliers based on the latest evaluation results.  
- Emails include personalized feedback and attachments when needed, helping suppliers stay informed and aligned with Cummins' quality standards.  
- SMTP protocol is used to handle secure and scheduled email dispatch.

### 💾 Data Import and Management via Excel  
- Supports importing supplier data and performance indicators from Excel spreadsheets, enabling easy data entry and updates from external sources.  
- Automated data parsing ensures accurate integration into the SQLite database without manual rework.

### 🔐 User Interface  
- Developed with **PyQt5**, offering an intuitive graphical interface for users to interact with data, generate reports, and manage supplier information without needing technical background.  
- Provides dropdowns, search filters, and forms to simplify navigation and data entry.

---

## Technologies Used

| Technology        | Purpose                                   |
|-------------------|-------------------------------------------|
| Python 3.12       | Core programming language                 |
| PyQt5             | Desktop GUI development                   |
| SQLite            | Lightweight database for local storage   |
| matplotlib/Plotly | Dynamic graph and chart generation        |
| smtplib (SMTP)    | Automated email sending                    |
| Excel (.xlsx)      | Data import/export format                  |
| Power BI          | Advanced business intelligence dashboards |

---

## *Project Structure

