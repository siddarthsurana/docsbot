import os
import json
import boto3
import logging
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler
from botocore.exceptions import ClientError
from slack_sdk.signature import SignatureVerifier

# Configure logging
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize AWS clients
secrets_manager_client = boto3.client('secretsmanager')

def get_slack_bot_token():
    """
    Retrieve the Slack bot token from AWS Secrets Manager.
    """
    secret_name = "/slack/bot-token"  # The secret name in Secrets Manager
    try:
        # Retrieve the secret value from Secrets Manager
        response = secrets_manager_client.get_secret_value(SecretId=secret_name)

        # Secrets Manager stores the secret in either 'SecretString' or 'SecretBinary'
        if 'SecretString' in response:
            secret = response['SecretString']
        else:
            secret = response['SecretBinary']

        # Assuming the secret is a JSON string, parse it
        secret_json = json.loads(secret)
        token = secret_json.get("token")
        logger.info(f"Slack Bot Token retrieved successfully.")  # Log successful retrieval
        return token
    except ClientError as e:
        logger.error(f"Error retrieving Slack bot token from Secrets Manager: {str(e)}")
        raise

def get_slack_signing_secret():
    """
    Retrieve the Slack signing secret from AWS Secrets Manager.
    """
    secret_name = "/slack/signing-secret"  # The secret name in Secrets Manager
    try:
        # Retrieve the secret value from Secrets Manager
        response = secrets_manager_client.get_secret_value(SecretId=secret_name)

        # Secrets Manager stores the secret in either 'SecretString' or 'SecretBinary'
        if 'SecretString' in response:
            secret = response['SecretString']
        else:
            secret = response['SecretBinary']

        # Assuming the secret is a JSON string, parse it
        secret_json = json.loads(secret)
        return secret_json.get("secret")
    except ClientError as e:
        logger.error(f"Error retrieving Slack signing secret from Secrets Manager: {str(e)}")
        raise

# Initialize the Slack Signature Verifier
signature_verifier = SignatureVerifier(get_slack_signing_secret())

def validate_slack_request(event):
    """
    Validates the request from Slack using the signing secret and the headers.
    """
    if not signature_verifier.is_valid_request(event['headers'], event['body']):
        logger.error("Invalid Slack request.")
        raise ValueError("Invalid request from Slack.")

def get_bedrock_knowledgebase_response(user_query):
    """
    Query AWS Bedrock Knowledge Base to retrieve a response.
    """
    """
    Query AWS Bedrock Knowledge Base to retrieve a response.
    """
    try:
        client = boto3.client(
            service_name='bedrock-agent-runtime',
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )


        response = client.retrieve_and_generate(
            input={"text": user_query},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "modelArn": "arn:aws:bedrock:us-east-1:381491981919:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                    "knowledgeBaseId": "LUHARQB5LR"
                }
            }
        )


        logger.info("Successfully received response from Bedrock Knowledge Base.")
        return response
    except client.exceptions.ValidationException as e:
        logger.error(f"Validation error: {str(e)}")
        raise
    except client.exceptions.ResourceNotFoundException as e:
        logger.error(f"Knowledge base or model not found: {str(e)}")
        raise
    except client.exceptions.ValidationException as e:
        logger.error(f"Validation error: {str(e)}")
        raise
    except client.exceptions.ResourceNotFoundException as e:
        logger.error(f"Knowledge base or model not found: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error querying knowledge base: {str(e)}")
        raise
def format_response(kb_response):
    """
    Format the knowledge base response to send to Slack.
    This function extracts the text response and the list of SharePoint URLs.
    """
    try:
        # Extract the main output text from the response
        response_text = kb_response["output"]["text"]

        # Extract the SharePoint URLs from the citations
        sharepoint_urls = []
        for citation in kb_response.get("citations", []):
            for reference in citation.get('retrievedReferences', []):
                location = reference.get('location', {})
                if location.get('sharePointLocation'):
                    sharepoint_url = location['sharePointLocation'].get('url')
                    if sharepoint_url:
                        sharepoint_urls.append(sharepoint_url)
        # Add sources section if any SharePoint URLs are found
        if sharepoint_urls:
            response_text += "\n\n*Sources:*"
            for url in sharepoint_urls:
                response_text += f"\n• {url}"

        return response_text

    except KeyError as e:
        logger.error(f"Error formatting response: Missing expected keys in response - {str(e)}")
        return "Sorry, I couldn't format the response properly."

# Initialize the Slack app
app = App(
    token=get_slack_bot_token(),
    signing_secret=get_slack_signing_secret() # Fetch token from AWS Secrets Manager
)
logger.info("Slack App initialized.")


def handle_message(event, say, logger):
    """
    Handle messages posted in Slack channels when the app is mentioned.
    This listens for messages and triggers a query to the AWS Bedrock Knowledge Base.
    """
    # Extract useful information
    user_query = event.get('text', '')
    user_id = event.get('user')
    channel_id = event.get('channel')
    thread_ts = event.get('ts')  # Timestamp of the original message if replying in a thread

    logger.info(f"Received a mention from user {user_id} with query: {user_query} in channel {channel_id}.")
        # Fetch response from Bedrock Knowledge Base
    kb_response = get_bedrock_knowledgebase_response(user_query)
    print(kb_response)
    response_text = format_response(kb_response)

        # Send the formatted response back to Slack
    say(
            text=response_text,
            thread_ts=thread_ts  # Reply in the same thread if applicable
        )


def respond_to_slack_within_3_seconds(event, ack):
    text = event.get("text")
    if text is None or len(text) == 0:
        ack(":x: Usage: /start-process (description here ")
    else:
        ack(f"Accepted! (task: {event['text']})")

app.event("app_mention")(
    ack=respond_to_slack_within_3_seconds,  # responsible for calling `ack()`
    lazy=[handle_message]  # unable to call `ack()` / can have multiple functions
)
def handler(event, context):
    """
    Lambda handler function to process both Slack URL verification and Slack events.
    """
    print(event)
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        # Validate Slack request
        #validate_slack_request(event)

        # Handle Slack URL verification challenge
        if 'body' in event:
            body = json.loads(event['body'])
            
            # If it's a URL verification request from Slack
            if body.get('type') == 'url_verification':
                logger.info("Handling Slack URL verification challenge.")
                # Respond with challenge value
                return {
                    'statusCode': 200,
                    'body': json.dumps({'challenge': body.get('challenge')}),
                    'headers': {'Content-Type': 'application/json'}
                }


        # Now handle other Slack events
        slack_handler = SlackRequestHandler(app=app)

        return slack_handler.handle(event, context)

    except Exception as err:
        logger.error(f"Error processing event: {str(err)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
        logger.error(f"Error processing event: {str(err)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
