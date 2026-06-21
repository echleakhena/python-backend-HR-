from database import initialize_database


def main() -> None:
    initialize_database()

    while True:
        print("=" * 45)
        print("          HRM SYSTEM MAIN MENU")
        print("=" * 45)
        print("1. Add New Employee")
        print("2. View All Employees")
        print("3. Search Employee by ID")
        print("4. Remove Employee")
        print("5. View Total Payroll Budget")
        print("6. Exit System")
        print("=" * 45)

        option = input("Select an option (1-6): ").strip()

        if option == "6":
            print("System closed successfully.")
            break


if __name__ == "__main__":
    main()