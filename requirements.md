
## How to adjust and run this example requirements document
When you are done, then share this into the context of the AI Agent.  
Also share any sample code or documentation that you want Cursor to copy paste solutions out of
Then run this AI Agent command:  
/Generate Curor Rules generate some rules using the requirements.md document I've provided
That will generate several rules file.  Alter each of them with the drop down boxes to be "Always" included
When you are done, delete this requirements.md document and alter your rules files going forward

## Cursor should ignore all the lines above when generating rules files.  

## Cursor behaviour
1. If I issue you a challenging task where there are several options or confusion in my request, then ask me questions and / or give me options before proceeding with any code changes
2. While we are starting a task, I will enjoy your creativity.  However, as we progress through a task in debugging and testing I do not want creativity.  I want minimal changes to fix problems.  
3. If I ask you to do something that is is in conflict with any of the rules files, then make the related change to the rules files so that I can review the change

## high level design
Tis is a streamlit in snowflake app designed for network engineers to monitor telco network data and review and act on anomolies 

It has a landing page and a few pages the user can navigate to.  

## Architecture and Tech requirements:
This is built for Streamlit in Snowflake and can also be run locally on a laptop for development and testing.  

Limit python libraries to using those available on this anaconda channel:  
https://repo.anaconda.com/pkgs/snowflake/

The app will have access to a Snowflake database but default the app will not have access to external data.  When needed, you can assist the developer to set up external network connections, API keys, etc... to connect to external information


## Detailed design
1. The landing page has KPI's and easy navigation to... etc...  
2. The monitoring page has a map...  
3. The documentation page has information on how to use the app

## Project Tasks - update for each major release
Your task as part of this project is to:
1. Create an additional page that...
2. Generate the related data model and sample data to enable me to test. etc...

## Documentation
1. You will create end user documentation so they know how to use the app.  This should appear in a single page within the app
2. Code should have a lot of comments to make it easy for humans to understand
3. The rules documents will act as the functional and technical designs and you will update these accordingly as we progress with the design and development of the app 

## Test Plan
1. Maintain a test plan according to what is designed and developed 

## Optional: Version Control Guidelines
Git branching strategy
Include guidelines for commit messages
Specify which files should be in .gitignore

## Optional: Security Requirements:
Add guidelines for handling sensitive data
Specify authentication requirements
Include guidelines for API key management

## Optional: Documentation Requirements:
Add requirements for code documentation
Specify requirements for user documentation
Include API documentation guidelines if applicable

