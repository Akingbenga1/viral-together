# Viral Together App

## Overview
The Viral Together App is a platform designed to connect influencers with brands and businesses. It allows users to create, manage, and search for influencers based on various criteria, facilitating collaborations and marketing campaigns.

## Core Features

### Influencer Management
- **Create Influencer**: Users can create new influencer profiles with details such as name, bio, location, languages spoken, rate per post, and availability.
- **Get Influencer by ID**: Retrieve detailed information about a specific influencer using their unique ID.
- **Update Influencer**: Modify existing influencer profiles, including updating their details and availability.
- **Delete Influencer**: Remove an influencer profile from the database.
- **List All Influencers**: Fetch a list of all influencers available in the system.
- **Set Influencer Availability**: Update the availability status of an influencer.
- **Update Profile Picture**: Upload and update the profile picture of an influencer.

### Search Functionality
- **Search by Location**: Find influencers based on their location.
- **Search by Language**: Search for influencers who speak specific languages.
- **Get Available Influencers**: Retrieve a list of influencers who are currently available for collaboration.
- **Get Influencers with High Growth Rate**: Identify influencers with a significant growth rate in their following.
- **Get Influencers by Successful Campaigns**: Filter influencers based on the number of successful campaigns they have completed.
- **Filter by Rate per Post**: Search for influencers within a specified rate range for their posts.

### User Authentication
- **Bearer Token Authentication**: Secure API endpoints using Bearer token authentication to ensure that only authorized users can access certain functionalities.

### Database Management
- **SQLAlchemy ORM**: Utilize SQLAlchemy for database interactions, allowing for efficient data management and retrieval.
- **Alembic Migrations**: Manage database schema changes using Alembic, ensuring that the database structure is always in sync with the application models.

## Running Tests

To run the tests for the Viral Together App, follow these steps:

1. **Navigate to the Tests Directory**: Open your terminal and change to the directory where the tests are located. This is typically in a folder named `tests` or similar within your project structure.

   ```bash
   cd tests
   ```

2. **Run the Tests**: Use a testing framework like `pytest` to run the tests. If you have `pytest` installed, you can run the following command:

   ```bash
   pytest
   ```

   This command will discover and execute all the test files and functions in the directory.

3. **View Test Results**: After running the tests, you will see the results in the terminal, indicating which tests passed and which failed.

## Getting Started
To get started with the Viral Together App, clone the repository and install the required dependencies. Follow the setup instructions in the documentation to configure your environment and run the application.

## Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
