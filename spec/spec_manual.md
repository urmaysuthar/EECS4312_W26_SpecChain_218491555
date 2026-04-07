# Requirement ID: FR1

- Description: [The system shall allow users to complete a mood check in and save the entry with a timestamp in one session.]
- Source Persona: [Consistent Mood Journal User]
- Traceability: [Derived from review group G1]
- Acceptance Criteria: [Given the user opens the mood check in screen, when the user selects a mood and submits the entry, then the system must save the entry with the selected mood and the date and time of submission.]

# Requirement ID: FR2

- Description: [The system shall allow users to add a written journal note to a mood entry before saving it.]
- Source Persona: [Consistent Mood Journal User]
- Traceability: [Derived from review group G1]
- Acceptance Criteria: [Given the user is creating a mood entry, when the user types a journal note and submits the entry, then the system must save both the mood entry and the written note together.]

# Requirement ID: FR3

- Description: [The system shall allow users to view a chronological history of their past mood entries and journal notes.]
- Source Persona: [Consistent Mood Journal User]
- Traceability: [Derived from review group G1]
- Acceptance Criteria: [Given the user has previously saved at least two mood entries, when the user opens the history view, then the system must display the saved entries in date order with their associated notes.]

# Requirement ID: FR4

- Description: [The system shall generate a summary of recorded moods and notes for a user selected date range.]
- Source Persona: [Therapy Support User]
- Traceability: [Derived from review group G2]
- Acceptance Criteria: [Given the user has mood data recorded over multiple days, when the user selects a start date and end date for a summary, then the system must display a summary using only entries recorded within that date range.]

# Requirement ID: FR5

- Description: [The system shall display past mood entries and journal notes on a single review screen for a user selected date range.]
- Source Persona: [Therapy Support User]
- Traceability: [Derived from review group G2]
- Acceptance Criteria: [Given the user has saved mood entries and notes, when the user selects a start date and end date and opens the review screen, then the system must display all entries in that date range with their dates, moods, and notes on one screen.]

# Requirement ID: FR6

- Description: [The system shall display a Premium label on each premium feature before the user attempts to open that feature.]
- Source Persona: [Cost-Conscious User]
- Traceability: [Derived from review group G3]
- Acceptance Criteria: [Given the user is viewing a list of available features, when the screen is displayed, then every premium feature must show a Premium label and free features must not show that label.]

# Requirement ID: FR7

- Description: [The system shall display subscription pricing and billing period information before the user confirms a premium purchase.]
- Source Persona: [Cost-Conscious User]
- Traceability: [Derived from review group G3]
- Acceptance Criteria: [Given the user selects a premium upgrade option, when the purchase screen is opened, then the system must display the subscription price, billing period, and confirmation action before payment is submitted.]

# Requirement ID: FR8

- Description: [The system shall generate a mood insights report using the user’s recorded mood entries over time.]
- Source Persona: [Insight-Seeking User]
- Traceability: [Derived from review group G4]
- Acceptance Criteria: [Given the user has recorded multiple mood entries over time, when the user opens the insights report, then the system must display a report based on the user’s stored entries rather than generic placeholder text.]

# Requirement ID: FR9

- Description: [The system shall provide users with feedback that reflects patterns in their recorded mood history.]
- Source Persona: [Insight-Seeking User]
- Traceability: [Derived from review group G4]
- Acceptance Criteria: [Given the user has at least seven saved mood entries, when the user opens the feedback section, then the system must present feedback that refers to patterns found in the saved mood history.]

# Requirement ID: FR10

- Description: [The system shall allow users to set preferred reminder times for mood check ins.]
- Source Persona: [Reminder-Dependent User]
- Traceability: [Derived from review group G5]
- Acceptance Criteria: [Given the user opens reminder settings, when the user selects one or more reminder times and saves the settings, then the system must store those selected reminder times and show them in the reminder settings screen.]

# Requirement ID: FR11

- Description: [The system shall send reminder notifications at the times saved in the user’s reminder settings.]
- Source Persona: [Reminder-Dependent User]
- Traceability: [Derived from review group G5]
- Acceptance Criteria: [Given the user has enabled reminders and saved a reminder time, when the saved reminder time is reached, then the system must send a notification for the mood check in.]

# Requirement ID: FR12

- Description: [The system shall allow users to enable or disable reminders without deleting previously saved reminder times.]
- Source Persona: [Reminder-Dependent User]
- Traceability: [Derived from review group G5]
- Acceptance Criteria: [Given the user has already saved reminder times, when the user turns reminders off and later turns them on again, then the system must keep the previously saved reminder times unless the user changes them.]