# Requirement ID: AFR1

- Description: [The system shall export user mental health data in a CSV file format when requested by the user.]
- Source Persona: [Data-Conscious User]
- Traceability: [Derived from review group AG1]
- Acceptance Criteria: [Given a user has created an account and logged in, When the user navigates to the account settings and clicks the 'Export Data' button, Then the system shall generate a CSV file containing the user's mental health data, including date, time, and entries, and send it to the user's registered email address.]

# Requirement ID: AFR2

- Description: [The system shall display a list of third-party services used for data processing, including their names, purposes, and data sharing policies.]
- Source Persona: [Data-Conscious User]
- Traceability: [Derived from review group AG1]
- Acceptance Criteria: [Given a user is logged in and navigates to the 'About' or 'Settings' section, When the user clicks on 'Third-Party Services', Then the system shall display a table with the following columns: 'Service Name', 'Purpose', and 'Data Sharing Policy', and populate it with the following services: Google Analytics for usage tracking, Sentry for error tracking, and Facebook for optional social sharing, with accurate and up-to-date information.]

# Requirement ID: AFR3

- Description: [The system shall display an error message when a user's data cannot be loaded.]
- Source Persona: [Frustrated User]
- Traceability: [Derived from review group AG2]
- Acceptance Criteria: [Given a user has logged in and attempted to view their results, When the system is unable to retrieve the user's data, Then the system displays an error message with a specific error code and a link to contact support.]

# Requirement ID: AFR4

- Description: [The system shall prevent data loss when a user encounters a technical issue.]
- Source Persona: [Frustrated User]
- Traceability: [Derived from review group AG2]
- Acceptance Criteria: [Given a user has entered data and the system encounters a technical issue, When the issue occurs, Then the system saves the user's data and displays a recovery message with instructions on how to resume where they left off.]

# Requirement ID: AFR5

- Description: [The system shall display a tooltip with the exact price and a link to the subscription page when a user hovers over a premium feature icon.]
- Source Persona: [Budget-Conscious User]
- Traceability: [Derived from review group AG3]
- Acceptance Criteria: [Given the user is not logged in, When the user hovers over a premium feature icon, Then the tooltip displays the price and a link to the subscription page.]

# Requirement ID: AFR6

- Description: [The system shall allow users to view the last 30 days of mood history entries without requiring a subscription, with each entry including the date, mood rating, and a brief note.]
- Source Persona: [Budget-Conscious User]
- Traceability: [Derived from review group AG3]
- Acceptance Criteria: [Given the user is not subscribed, When the user navigates to the mood history section, Then the system displays the last 30 days of entries with date, mood rating, and brief note for each entry.]

# Requirement ID: AFR7

- Description: [The system shall display a confirmation message to the user after they submit feedback on app usability.]
- Source Persona: [Feedback-Oriented User]
- Traceability: [Derived from review group AG4]
- Acceptance Criteria: [Given the user is logged in and on the feedback page, When the user submits their feedback, Then the system displays a confirmation message that reads 'Thank you for your feedback.']

# Requirement ID: AFR8

- Description: [The system shall store and display all submitted feedback on a dedicated page for review.]
- Source Persona: [Feedback-Oriented User]
- Traceability: [Derived from review group AG4]
- Acceptance Criteria: [Given the user is an administrator and logged in, When they navigate to the feedback page, Then the system displays a list of all submitted feedback, including the user's persona ID, feedback text, and timestamp.]

# Requirement ID: AFR9

- Description: [The system shall store a user-selected reminder time and send a notification at that time to track mood.]
- Source Persona: [Results-Driven User]
- Traceability: [Derived from review group AG5]
- Acceptance Criteria: [Given a user has set a reminder time, When the system reaches that time, Then it shall send a notification to the user to track their mood.]

# Requirement ID: AFR10

- Description: [The system shall generate a weekly summary of the user's mood history and provide insights into their mood trends.]
- Source Persona: [Results-Driven User]
- Traceability: [Derived from review group AG5]
- Acceptance Criteria: [Given a user has tracked their mood for at least 7 days, When the system generates a weekly summary, Then it shall display the user's average mood score and highlight any notable trends or patterns in their mood history.]
