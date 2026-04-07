# Requirement ID: HFR1

- Description: [The system shall allow users to export their saved mood history and journal records from the account settings screen.]
- Source Persona: [Privacy-Conscious Record Keeper]
- Traceability: [Derived from review group AG1]
- Acceptance Criteria: [Given the user is logged in and has saved mood history or journal records, when the user selects the export option from account settings, then the system must generate an export file containing the user’s saved records.]

# Requirement ID: HFR2

- Description: [The system shall display a data usage summary for each category of personal data collected by the app.]
- Source Persona: [Privacy-Conscious Record Keeper]
- Traceability: [Derived from review group AG1]
- Acceptance Criteria: [Given the user opens the privacy settings screen, when the user selects a data category, then the system must display the purpose of collection, whether the data is shared, and whether the data is stored in the user account.]

# Requirement ID: HFR3

- Description: [The system shall display an error screen with a retry action when a requested page or result screen cannot be loaded.]
- Source Persona: [Interrupted User]
- Traceability: [Derived from review group AG2]
- Acceptance Criteria: [Given the user opens a page or result screen and the content cannot be loaded, when the loading attempt fails, then the system must display an error screen with a retry button instead of showing a blank page.]

# Requirement ID: HFR4

- Description: [The system shall restore unsaved questionnaire responses after an unexpected application close.]
- Source Persona: [Interrupted User]
- Traceability: [Derived from review group AG2]
- Acceptance Criteria: [Given the user has entered questionnaire responses and the app closes unexpectedly, when the user reopens the app, then the system must restore the unsaved responses from the interrupted session.]

# Requirement ID: HFR5

- Description: [The system shall display a Premium label on each premium feature before the user attempts to open that feature.]
- Source Persona: [Cost-Sensitive Free User]
- Traceability: [Derived from review group AG3]
- Acceptance Criteria: [Given the user is viewing a list of app features, when the feature list is displayed, then every premium feature must show a Premium label and free features must not show that label.]

# Requirement ID: HFR6

- Description: [The system shall allow non-subscribed users to view their last 30 days of mood history entries.]
- Source Persona: [Cost-Sensitive Free User]
- Traceability: [Derived from review group AG3]
- Acceptance Criteria: [Given the user is not subscribed and has saved mood history entries, when the user opens the mood history screen, then the system must display the last 30 days of entries with the date, mood rating, and saved note for each entry.]

# Requirement ID: HFR7

- Description: [The system shall allow users to submit usability or content feedback from within the app.]
- Source Persona: [Usability-Focused Reviewer]
- Traceability: [Derived from review group AG4]
- Acceptance Criteria: [Given the user opens the feedback screen, when the user selects a feedback category, enters feedback text, and submits the form, then the system must save the feedback and display a submission confirmation message.]

# Requirement ID: HFR8

- Description: [The system shall allow users to mark a question as not applicable so that the same question is excluded from future question sets.]
- Source Persona: [Usability-Focused Reviewer]
- Traceability: [Derived from review group AG4]
- Acceptance Criteria: [Given the user is answering a question, when the user marks the question as not applicable, then the system must exclude that question from future question sets for that user.]

# Requirement ID: HFR9

- Description: [The system shall store a user-selected reminder time and send a notification at that time for a mood check-in.]
- Source Persona: [Reflection-Oriented Support User]
- Traceability: [Derived from review group AG5]
- Acceptance Criteria: [Given the user has enabled reminders and saved a reminder time, when the saved time is reached, then the system must send a notification for a mood check-in.]

# Requirement ID: HFR10

- Description: [The system shall generate a weekly mood summary from the user’s saved mood entries.]
- Source Persona: [Reflection-Oriented Support User]
- Traceability: [Derived from review group AG5]
- Acceptance Criteria: [Given the user has saved mood entries on at least 7 different days, when the user opens the weekly summary screen, then the system must display the average mood score for that period and the highest and lowest recorded mood values.]