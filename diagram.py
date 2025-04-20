from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.ml import Bedrock
from diagrams.aws.security import IAM
from diagrams.aws.network import APIGateway
from diagrams.aws.security import SecretsManager
from diagrams.aws.management import SystemsManager
from diagrams.onprem.client import Users as Slack


with Diagram("DocsBot - Bedrock + Slack Integration", show=False, graph_attr={"fontsize": "20"}):
    slack = Slack("Slack App")

    with Cluster("API Layer"):
        api_gateway = APIGateway("Slack API Gateway")

    with Cluster("Lambda Function"):
        handler_lambda = Lambda("SlackBedrockHandler")

    with Cluster("AWS Services"):
        bedrock = Bedrock("Amazon Bedrock")
        secrets = SecretsManager("Slack Credentials")
        iam = IAM("Lambda Role + Bedrock Permissions")
        ssm = SystemsManager("Parameter Store (Optional)")

    # Flow connections
    slack >> api_gateway >> handler_lambda
    handler_lambda >> bedrock
    handler_lambda >> secrets
    handler_lambda >> iam
    handler_lambda >> ssm
