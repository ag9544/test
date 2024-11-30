import json
import boto3
import requests

# Initialize the Lex V2 client
lex_client = boto3.client('lexv2-runtime')

# Bot and Alias details (replace with your values)
BOT_ID = 'SPMGX0T9ET'          # Replace with your Bot ID
BOT_ALIAS_ID = 'TSTALIASID'    # Replace with your Bot Alias ID
LOCALE_ID = 'en_US'            # Replace with your Locale ID

# API endpoint for job recommendations
RECOMMENDATION_API_URL = 'https://v2xv23a4zk.execute-api.us-east-1.amazonaws.com/dev/jobs'

# Simulated job details for example purposes
SIMULATED_JOB_DETAILS = {
    1: "Google - Software Engineer: Develop scalable applications. Location: Remote. Apply at https://google.jobs/software-engineer",
    2: "Amazon - Data Scientist: Build predictive models. Location: Seattle. Apply at https://amazon.jobs/data-scientist"
}

# Function to extract company name and position
def extract_company_and_position(json_data):
    """
    Extract company names and job titles from the API response.
    """
    # Parse the 'body' string into JSON
    body = json.loads(json_data.get("body", "{}"))
    results = body.get("data", {}).get("results", [])
    extracted_data = []

    # Loop through results and extract the company name and title
    for job in results:
        company_name = job.get("company", {}).get("display_name", "Unknown Company")
        job_title = job.get("title", "Unknown Position")
        extracted_data.append(f"{company_name} - {job_title}")
    
    return extracted_data

def handle_greeting_intent():
    """
    Handles the GreetingIntent and returns a simple response.
    """
    return "Hello! How can I assist you today? You can ask me for job recommendations."

def handle_job_search_intent(user_input):
    """
    Handles the JobSearchIntent and fetches job recommendations.
    """
    # Check for keywords in the user input
    if "job" in user_input.lower():
        print("Fetching job recommendations from API...")

        # Call the recommendations API
        api_response = requests.get(RECOMMENDATION_API_URL)

        if api_response.status_code == 200:
            # Parse the JSON response
            job_data = api_response.json()
            print(f"API Response: {json.dumps(job_data, indent=2)}")

            # Extract and format company name and job title using helper function
            formatted_recommendations = extract_company_and_position(job_data)
            print("Formatted recommendations are:", formatted_recommendations)

            # Combine recommendations into a response message
            if formatted_recommendations:
                return "Here are the top job recommendations:\n" + "\n".join(
                    [f"{i+1}. {rec}" for i, rec in enumerate(formatted_recommendations[:5])]
                ) + "\nWould you like to see more?"
            else:
                return "Sorry, no valid job recommendations are available at the moment."
        else:
            return f"Failed to fetch job recommendations. API returned status code {api_response.status_code}."
    else:
        return "I can help you find job recommendations. What type of jobs are you looking for?"

def handle_refine_search_intent(location=None, job_type=None):
    """
    Handles the RefineSearchIntent by refining the search based on user input.
    """
    if location:
        return f"Let me find jobs in {location} for you. Fetching recommendations..."
    elif job_type:
        return f"Looking for jobs related to {job_type}. Fetching recommendations..."
    else:
        return "Please provide more details to refine the search (e.g., location or job type)."

def handle_provide_details_intent(job_number):
    """
    Handles the ProvideDetailsIntent by providing more details about a selected recommendation.
    """
    if job_number in SIMULATED_JOB_DETAILS:
        return f"Here are the details for job {job_number}:\n{SIMULATED_JOB_DETAILS[job_number]}"
    else:
        return "Sorry, I couldn't find details for the selected job. Please try again."

def lambda_handler(event, context):
    """
    AWS Lambda handler for Lex bot integration.
    """
    try:
        # Extract intent and user input
        intent_name = event['sessionState']['intent']['name']
        user_input = event.get('inputTranscript', '')
        slots = event['sessionState']['intent'].get('slots', {})
        print(f"User input: {user_input}, Intent: {intent_name}")

        # Handle intents dynamically
        if intent_name == "GreetingIntent":
            response_message = handle_greeting_intent()

        elif intent_name == "JobSearchIntent":
            response_message = handle_job_search_intent(user_input)

        elif intent_name == "RefineSearchIntent":
            location = slots.get("Location", {}).get("value", {}).get("interpretedValue", None)
            job_type = slots.get("JobType", {}).get("value", {}).get("interpretedValue", None)
            response_message = handle_refine_search_intent(location, job_type)

        elif intent_name == "ProvideDetailsIntent":
            job_number = int(slots.get("JobNumber", {}).get("value", {}).get("interpretedValue", -1))
            response_message = handle_provide_details_intent(job_number)

        else:
            response_message = "I'm not sure how to help with that. Could you rephrase?"

        # Return response in Lex-compatible format
        return {
            "sessionState": {
                "dialogAction": {
                    "type": "Close"
                },
                "intent": {
                    "name": intent_name,
                    "state": "Fulfilled"
                }
            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": response_message
                }
            ]
        }

    except Exception as e:
        print(f"Error occurred: {e}")
        return {
            "sessionState": {
                "dialogAction": {
                    "type": "Close"
                },
                "intent": {
                    "name": "ErrorIntent",
                    "state": "Failed"
                }
            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": "An error occurred while processing your request. Please try again later."
                }
            ]
        }
