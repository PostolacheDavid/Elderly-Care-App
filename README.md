# Elderly Care App

A role-based desktop application developed using **KivyMD** and **MySQL**, designed to assist elderly individuals, doctors, and caregivers in managing medical and daily needs efficiently.

## 🧠 About the Project

This project was developed as a final-year college project. The goal is to provide an intuitive, user-friendly interface that allows:

- Doctors to manage patients and access health data.
- Elderly users to view medical info and appointments.
- Caregivers to support elders with reminders and communication.
- Admins to oversee the system.

## 🛠️ Technologies Used

- **Python 3.11+**
- **Kivy** & **KivyMD** (for GUI)
- **MySQL** (for storing users and data)
- **Plyer** (for file chooser functionality)
- **bcrypt** (for secure password hashing)

## 🔐 Roles

- **Doctor**
- **Elder**
- **Caregiver**
- **Admin**

Each role sees a different dashboard and UI components relevant to their permissions.

## 🚀 Features

- Role-based login system
- Doctor account creation with diploma upload
- Secure password storage using bcrypt
- File upload using Plyer (Windows tested)
- Top and bottom navigation bars consistent across screens
- Pop-up dialogs for logout confirmation
- Custom file chooser for selecting profile documents
- Responsive and minimalist UI

## 🧪 How to Run

1. Clone the repo
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
