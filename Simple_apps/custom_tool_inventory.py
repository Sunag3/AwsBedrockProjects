import sys, os
import boto3
import psycopg2
from psycopg2 import pool
from strands import Agent, tool
from strands.models.bedrock import BedrockModel

# Injects your masterclass configurations
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MODEL_ID, REGION, DB_ENDPOINT

class RDSInventoryTools:
    def __init__(self):
        # 1. Hardcode your connection variables (No passwords needed)
        print(DB_ENDPOINT)
        self.endpoint = DB_ENDPOINT # Replace with your RDS Endpoint
        self.port = 5432
        self.user = "postgres"
        self.database = "postgres"
        self.region = REGION

        print("🔐 Generating initial AWS IAM DB Token...")
        # 2. Open the pool once during initialization using a fresh token
        token = self._get_iam_token()
        
        self.db_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            host=self.endpoint,
            database=self.database,
            user=self.user,
            password=token, # Token acts as the password
            port=self.port
        )
        print("✅ Connection pool initialized successfully.")

    def _get_iam_token(self) -> str:
        """Helper function to fetch a fresh token from AWS."""
        rds_client = boto3.client('rds', region_name=self.region)
        return rds_client.generate_db_auth_token(
            DBHostname=self.endpoint,
            Port=self.port,
            DBUsername=self.user,
            Region=self.region
        )

    @tool
    def get_product_count(self) -> str:
        """Queries the live AWS RDS PostgreSQL database to count the total number 
        of rows inside the 'products' table.

        Returns:
            A string indicating the total number of products found.
        """
        # Borrow a connection from the pool
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM products;")
                count = cursor.fetchone()[0]
                return f"The products table currently contains {count} total rows."
        except psycopg2.OperationalError:
            # Dynamic token safety fallback: IAM tokens expire after 15 mins. 
            # If the pool errors out, refresh the password token on the fly.
            print("🔄 Token expired. Refreshing IAM token credentials...")
            new_token = self._get_iam_token()
            conn.password = new_token
            # Re-attempt the query
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM products;")
                count = cursor.fetchone()[0]
                return f"The products table currently contains {count} total rows."
        except Exception as e:
            return f"Database query failed: {str(e)}"
        finally:
            # Always return the connection back to the pool
            self.db_pool.putconn(conn)

# 3. Instantiate the tools and the Bedrock LLM
inventory = RDSInventoryTools()
model = BedrockModel(model_id=MODEL_ID)

# 4. Initialize the Agent with a explicit data focus
agent = Agent(
    model=model, 
    tools=[inventory.get_product_count],
    system_prompt="You are an inventory data assistant. Your job is to check database tables for product information when asked. Do not look at cloud hardware or infrastructure settings.",
)

# 5. Fire the request
print("\n🚀 Sending request to the LLM agent...")
response = agent("Check how many products there are in the RDS products table")

print("\n🤖 Final Agent Response:")
print(response)
