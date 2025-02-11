import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as path from 'path';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';

export class AmazonBedrockKnowledgebaseSlackIntegrationStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const slackBotToken = this.node.tryGetContext('slackBotToken');
    const slackSigningSecret = this.node.tryGetContext('slackSigningSecret');
    if (!slackBotToken || !slackSigningSecret) {
      throw new Error('Missing required context variables. Please provide slackBotToken and slackSigningSecret');
    }

    // Create secrets in Secrets Manager
    const slackBotTokenSecret = new secretsmanager.Secret(this, 'SlackBotTokenSecret', {
      secretName: '/slack/bot-token',
      description: 'Slack Bot User OAuth Token',
      secretStringValue: cdk.SecretValue.unsafePlainText(JSON.stringify({
        token: slackBotToken
      }))
    });

    const slackBotSigningSecret = new secretsmanager.Secret(this, 'SlackBotSigningSecret', {
      secretName: '/slack/signing-secret',
      description: 'Slack Signing Secret',
      secretStringValue: cdk.SecretValue.unsafePlainText(JSON.stringify({
        secret: slackSigningSecret
      }))
    });



    // Lambda function to interact with your existing knowledge base
    const lambdaFunction = new lambda.Function(this, 'SlackBedrockHandler', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda')),
      memorySize: 256,
      timeout: cdk.Duration.seconds(30),
      architecture: lambda.Architecture.ARM_64,
    });

    // Add IAM Policy to allow Lambda function to access Bedrock services
    lambdaFunction.addToRolePolicy(new iam.PolicyStatement({
      actions: [
        'bedrock:RetrieveAndGenerate',
        'bedrock:Retrieve',
        'bedrock:Query',
        'bedrock:GetInferenceProfile'
      ],
      resources: [
        `arn:aws:bedrock:${this.region}:${this.account}:knowledge-base/*`,
        'arn:aws:bedrock:us-east-1::foundation-model/*',
        'arn:aws:bedrock:us-east-2::foundation-model/*',
        'arn:aws:bedrock:us-west-2::foundation-model/*',
        `arn:aws:bedrock:${this.region}:${this.account}:inference-profile/*`
      ],
      effect: iam.Effect.ALLOW,
    }));

    lambdaFunction.addToRolePolicy(new iam.PolicyStatement({
      actions: [
        'bedrock:InvokeModel'
      ],
      resources: [
        `arn:aws:bedrock:${this.region}::foundation-model/*`,
        'arn:aws:bedrock:us-east-1::foundation-model/*',
        'arn:aws:bedrock:us-east-2::foundation-model/*',
        'arn:aws:bedrock:us-west-2::foundation-model/*',
        `arn:aws:bedrock:${this.region}:${this.account}:inference-profile/*`
      ],
      effect: iam.Effect.ALLOW,
    }));

    // Add IAM policy to allow Lambda to access secrets in Secrets Manager
    lambdaFunction.addToRolePolicy(new iam.PolicyStatement({
      actions: [
        'secretsmanager:GetSecretValue'
      ],
      resources: [
        slackBotTokenSecret.secretArn,
        slackBotSigningSecret.secretArn
      ],
      effect: iam.Effect.ALLOW,
    }));

    // Add IAM permissions for lazylistener faas to invoke Lambda
    lambdaFunction.addToRolePolicy(new iam.PolicyStatement({
      actions: [
        'lambda:InvokeFunction',
        'lambda:GetFunction'
      ],
      resources: [
        '*',  // Optionally allow invoking any Lambda function (you can restrict it further if needed)
      ],
      effect: iam.Effect.ALLOW,
    }));

    // API Gateway Setup
    const api = new apigateway.RestApi(this, 'slack-bedrock-api', {
      restApiName: 'SlackBedrockAPI',
      description: 'Slack integration for existing Bedrock knowledge base',
      deployOptions: {
        throttlingRateLimit: 10,
        throttlingBurstLimit: 20,
      }
    });

    const slackIntegration = api.root.addResource('slack');

    slackIntegration.addMethod('POST',
      new apigateway.LambdaIntegration(lambdaFunction, {
        proxy: true,
        integrationResponses: [{
          statusCode: '200',
        }],
      }),
      {
        authorizationType: apigateway.AuthorizationType.NONE,
        methodResponses: [{
          statusCode: '200',
          responseModels: {
            'application/json': apigateway.Model.EMPTY_MODEL,
          },
        }],
      });

    // Add CORS for Slack
    slackIntegration.addCorsPreflight({
      allowOrigins: ['*'],
      allowMethods: ['POST'],
      allowHeaders: ['Content-Type', 'X-Slack-Signature', 'X-Slack-Request-Timestamp'],
    });

    // Output the API URL for access
    new cdk.CfnOutput(this, 'APIUrl', {
      value: api.url ?? '',
      description: 'The public URL of the API Gateway.',
    });
  }
}
