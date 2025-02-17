# Slack-Bedrock Lambda Integration

This AWS Lambda function integrates Slack with AWS Bedrock Knowledge Base and facilitates querying and responding with data from the knowledge base in a Slack environment. It uses the Slack Bolt framework and AWS SDK for Python (Boto3) to handle interactions with Slack and AWS services such as Secrets Manager and Bedrock.

## Requirements

Before using this Lambda, make sure you have the following:

- **AWS Lambda** set up to deploy this function.
- **Slack App** with permissions to read and post messages in channels.
- **AWS Secrets Manager** for storing the Slack bot token and signing secret.
- **AWS Bedrock** service configured and accessible to your Lambda function.
  
### Prerequisites

1. Create a Slack App and install it in your workspace.
2. Store your Slack **Bot Token** and **Signing Secret** in AWS Secrets Manager at `/slack/bot-token` and `/slack/signing-secret` respectively.
3. Set up AWS Bedrock with a configured knowledge base.

## Lambda Configuration

### Environment Variables

This Lambda function expects the following environment variables to be set:

- `AWS_REGION`: AWS region where the Bedrock service and Secrets Manager are located (default: `us-east-1`).

### Dependencies

This Lambda uses the following Python packages:

- `boto3`: AWS SDK for Python to interact with AWS services.
- `slack_bolt`: Framework for building Slack apps.
- `slack_sdk`: Slack SDK for authentication and signing secret validation.
- `botocore`: AWS low-level API calls library.

Make sure to package these dependencies along with your Lambda function.

## Overview of the Functionality

### 1. Slack Bot Token and Signing Secret Retrieval
The Lambda retrieves the Slack bot token and signing secret from AWS Secrets Manager using the `get_slack_bot_token` and `get_slack_signing_secret` functions.

### 2. Slack Signature Verification
To ensure that the requests received from Slack are legitimate, the function verifies the request signatures using the `SignatureVerifier` class from `slack_sdk`.

### 3. Knowledge Base Querying
When a user mentions the bot in Slack, the bot queries the AWS Bedrock Knowledge Base to get a response using the `get_bedrock_knowledgebase_response` function. This function uses a pre-configured knowledge base model in AWS Bedrock to generate answers to user queries.

### 4. Formatting and Responding to Slack
The response from AWS Bedrock is processed and formatted in a user-friendly manner using the `format_response` function. If SharePoint URLs are included in the response, they are also displayed as sources.

### 5. Slack Event Handling
The Lambda function listens for Slack events like `app_mention` to trigger the bot's response. When an event is received, the Lambda function checks if it is a URL verification challenge or a message event. If it is a URL verification challenge, it responds with the challenge value to complete the Slack app installation process.

### 6. Lambda Handler
The `handler` function acts as the entry point for the Lambda, managing all Slack events, including the URL verification and responding to Slack mentions. It uses `SlackRequestHandler` from `slack_bolt.adapter.aws_lambda` to delegate event handling to the Slack app.

## How It Works

1. **Slack Request**: When a user mentions the bot in a Slack message, the Lambda function is triggered.
2. **Signature Verification**: The function validates that the request is legitimate from Slack using the signing secret.
3. **Query Bedrock**: The bot queries the AWS Bedrock Knowledge Base for relevant information based on the user's query.
4. **Format Response**: The response from the knowledge base is formatted and includes any relevant SharePoint URLs.
5. **Respond in Slack**: The bot posts the formatted response in the Slack channel or thread where the message was mentioned.

## Example Request

When a user mentions the bot in a Slack channel:

@botname What is the latest update on project X?


The bot will query the AWS Bedrock Knowledge Base and reply with an answer, along with any related sources such as SharePoint URLs if they are available.

## Error Handling

- The function handles errors related to querying AWS Bedrock, retrieving Slack tokens, and other unexpected issues gracefully. In case of an error, the Lambda will log the error and return an internal server error response to Slack.
  
## Deploying to AWS Lambda

### 1. Create a new Lambda function
- Go to the AWS Lambda Console and create a new function.
- Choose "Python 3.x" as the runtime.
- Upload the code and necessary dependencies as a deployment package (ZIP file).

### 2. Configure AWS Secrets Manager
- Store the Slack bot token and signing secret in Secrets Manager.
- Ensure the Lambda function has appropriate IAM permissions to access Secrets Manager and AWS Bedrock.

### 3. Slack App Configuration
- Set up event subscriptions in your Slack App settings to listen for the `app_mention` event.
- Install the Slack app in your workspace.

### 4. Test the Lambda
You can test the Lambda by invoking it with a Slack event. Slack will send an event when a user mentions the bot in a Slack channel.

## Logging

All logging is done through `logging` with a log level of `DEBUG`. The logs will provide useful information about the function's execution, including errors, successful queries, and responses.

## Conclusion

This Lambda provides an easy-to-deploy solution for integrating Slack with AWS Bedrock Knowledge Base, allowing users to query information and receive answers directly within Slack channels. By leveraging AWS services such as Secrets Manager and Bedrock, it ensures secure and efficient knowledge retrieval.


# Deployment command
cdk deploy -c slackBotToken=<> -c slackSigningSecret=<>