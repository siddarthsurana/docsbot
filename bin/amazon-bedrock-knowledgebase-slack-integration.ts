#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { AmazonBedrockKnowledgebaseSlackIntegrationStack } from '../lib/amazon-bedrock-knowledgebase-slack-integration-stack';

const app = new cdk.App();

// Add tags to all resources in the stack
const tags = {
  'CT:DIVISION': 'GROUP',
  'CT:STAGE': process.env.ENVIRONMENT || 'DEV',
  'CT:SERVICE': 'bedrock-slack-integration',
  'CT:OWNER': 'devops@travelopia.com' // Replace with your team name
};

new AmazonBedrockKnowledgebaseSlackIntegrationStack(app, 'AmazonBedrockKnowledgebaseSlackIntegrationStack', {
  // Use the current CLI configuration for account and region
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1' // Fallback to us-east-1 if not specified
  },

  // Stack description
  description: 'Stack for Bedrock Knowledge Base integration with Slack',

  // Add termination protection for production environments
  terminationProtection: process.env.ENVIRONMENT === 'prod',

  // Stack tags
  tags: tags,
});

// Add context validation
const region = app.node.tryGetContext('region');
if (region && !process.env.CDK_DEFAULT_REGION) {
  throw new Error('Region must be specified via CDK CLI configuration');
}

app.synth();
