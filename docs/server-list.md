# Complete MCP Server List

## 🎯 AWS Core Server (`aws-core`)
**Package**: `awslabs.core-mcp-server`  
**Purpose**: Foundation server for AWS solution planning and architecture

### Capabilities:
- Solution architecture planning
- AWS service recommendations
- Best practices guidance
- Multi-service orchestration planning

### Example Prompts:
- "Design a serverless architecture for a real-time chat application"
- "What AWS services should I use for a data pipeline?"
- "Plan a multi-region disaster recovery solution"

---

## 🏗️ AWS CDK Server (`aws-cdk`)
**Package**: `awslabs.cdk-mcp-server`  
**Purpose**: Infrastructure as Code with AWS CDK

### Capabilities:
- Generate CDK TypeScript/Python code
- Apply AWS Well-Architected principles
- Security scanning with cdk-nag
- AWS Solutions Constructs patterns
- Powertools for Lambda integration

### Example Prompts:
- "Create CDK code for a VPC with public and private subnets"
- "Generate a Lambda function with API Gateway"
- "Build an ECS Fargate service with ALB"

---

## 💰 AWS Pricing Server (`aws-pricing`)
**Package**: `awslabs.aws-pricing-mcp-server`  
**Purpose**: AWS cost analysis and optimization

### Capabilities:
- Real-time pricing information
- Cost estimation for services
- Multi-region price comparison
- Cost optimization recommendations
- Budget forecasting

### Example Prompts:
- "What's the monthly cost of running a t3.large EC2 instance?"
- "Compare RDS pricing between us-east-1 and eu-west-1"
- "Estimate costs for 100GB of S3 storage with 1M requests"

---

## 🔧 AWS API Server (`aws-api`)
**Package**: `awslabs.aws-api-mcp-server`  
**Purpose**: Direct AWS service control via AWS CLI commands

### Capabilities:
- Execute any AWS CLI command
- Manage all AWS services
- Resource creation and modification
- Service configuration
- Account-wide operations

### Example Prompts:
- "List all EC2 instances in us-east-1"
- "Create an S3 bucket named my-backup-bucket"
- "Show CloudWatch alarms in alarm state"
- "Get all Lambda functions with their memory settings"

---

## 🧠 Bedrock Knowledge Base Server (`bedrock-kb`)
**Package**: `awslabs.bedrock-kb-retrieval-mcp-server`  
**Purpose**: Access Amazon Bedrock Knowledge Bases

### Capabilities:
- Query enterprise knowledge bases
- Semantic search across documents
- Filter by data sources
- Reranking for relevance
- RAG (Retrieval Augmented Generation) support

### Example Prompts:
- "Search the documentation for authentication procedures"
- "Find information about our API endpoints"
- "What does our runbook say about database backups?"

---

## 🎨 Nova Canvas Server (`nova-canvas`)
**Package**: `awslabs.nova-canvas-mcp-server`  
**Purpose**: Image generation using Amazon Nova Canvas

### Capabilities:
- Text-to-image generation
- Color palette guidance
- Multiple image variations
- Quality settings (standard/premium)
- Negative prompting

### Example Prompts:
- "Generate a modern dashboard UI mockup"
- "Create an architecture diagram showing microservices"
- "Design a logo for a cloud services company"

---

## 🗄️ MySQL Aurora Server (`mysql-aurora`)
**Package**: `awslabs.mysql-mcp-server`  
**Purpose**: Direct database access to Aurora MySQL clusters

### Configuration:
- **Host**: expanseft-prototype.c32erjvbancm.us-east-1.rds.amazonaws.com
- **Database**: avidpay
- **Authentication**: AWS Secrets Manager
- **Mode**: Read-only (configurable)

### Capabilities:
- Natural language to SQL conversion
- Schema exploration
- Query execution
- Data analysis
- Table relationships discovery

### Example Prompts:
- "Show me all tables in the database"
- "Find all transactions from the last 30 days"
- "What's the schema of the users table?"
- "Generate a query to find duplicate records"

---

## 🚀 Additional Available MCP Servers

### Infrastructure & Compute
- **ECS**: `awslabs.ecs-mcp-server` - Container management
- **EKS**: `awslabs.eks-mcp-server` - Kubernetes orchestration
- **Lambda**: `awslabs.lambda-tool-mcp-server` - Serverless functions
- **Step Functions**: `awslabs.stepfunctions-tool-mcp-server` - Workflow orchestration

### Databases
- **DynamoDB**: `awslabs.dynamodb-mcp-server` - NoSQL database
- **DocumentDB**: `awslabs.documentdb-mcp-server` - MongoDB compatible
- **Neptune**: `awslabs.amazon-neptune-mcp-server` - Graph database
- **Redshift**: `awslabs.redshift-mcp-server` - Data warehouse
- **ElastiCache**: `awslabs.valkey-mcp-server` - In-memory caching

### Monitoring & Observability
- **CloudWatch**: `awslabs.cloudwatch-mcp-server` - Metrics and logs
- **CloudTrail**: `awslabs.cloudtrail-mcp-server` - Audit trails

### Security & Compliance
- **IAM**: `awslabs.iam-mcp-server` - Identity and access
- **Well-Architected**: `awslabs.well-architected-security-mcp-server` - Security reviews

### Data & Analytics
- **S3 Tables**: `awslabs.s3-tables-mcp-server` - Managed Apache Iceberg tables
- **HealthLake**: `awslabs.healthlake-mcp-server` - Healthcare data
- **Timestream**: `awslabs.timestream-for-influxdb-mcp-server` - Time series data

### Developer Tools
- **CloudFormation**: `awslabs.cfn-mcp-server` - Infrastructure templates
- **Terraform**: `awslabs.terraform-mcp-server` - Infrastructure as code

### Integration & Messaging
- **SNS/SQS**: `awslabs.amazon-sns-sqs-mcp-server` - Messaging services
- **MSK**: `awslabs.aws-msk-mcp-server` - Kafka service
- **MQ**: `awslabs.amazon-mq-mcp-server` - Message broker

---

## 📝 Adding New Servers

To add any of these servers to your configuration:

1. Edit `configs/mcp.json`
2. Add a new server entry:
```json
"server-name": {
  "command": "C:\\Users\\Tim\\.local\\bin\\uvx.exe",
  "args": ["awslabs.package-name@latest"],
  "env": {
    "AWS_PROFILE": "aws-sso-primary",
    "AWS_REGION": "us-east-1",
    "FASTMCP_LOG_LEVEL": "ERROR"
  },
  "disabled": false,
  "autoApprove": []
}
```
3. Restart Cursor IDE

---

## 🔗 Resources

- [AWS Labs MCP GitHub](https://github.com/awslabs/mcp)
- [MCP Protocol Documentation](https://modelcontextprotocol.io)
- [AWS MCP Servers Blog](https://aws.amazon.com/blogs/machine-learning/introducing-aws-mcp-servers-for-code-assistants-part-1/)
