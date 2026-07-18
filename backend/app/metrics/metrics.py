from prometheus_client import Counter, Gauge, Histogram

# ==================================================
# Chat Metrics
# ==================================================

chat_requests_total = Counter(
    "chat_requests_total",
    "Total number of chat requests",
)

chat_errors_total = Counter(
    "chat_errors_total",
    "Total number of failed chat requests",
)

messages_processed_total = Counter(
    "messages_processed_total",
    "Total number of messages processed",
)

active_conversations = Gauge(
    "active_conversations",
    "Number of active conversations",
)

# ==================================================
# OpenAI Metrics
# ==================================================

openai_requests_total = Counter(
    "openai_requests_total",
    "Total number of OpenAI API requests",
)

openai_errors_total = Counter(
    "openai_errors_total",
    "Total number of failed OpenAI API requests",
)

prompt_tokens_total = Counter(
    "prompt_tokens_total",
    "Total prompt tokens consumed",
)

completion_tokens_total = Counter(
    "completion_tokens_total",
    "Total completion tokens consumed",
)

total_tokens_total = Counter(
    "total_tokens_total",
    "Total tokens consumed",
)

openai_latency_seconds = Histogram(
    "openai_latency_seconds",
    "Latency of OpenAI API requests in seconds",
)

# ==================================================
# Database Metrics
# ==================================================

db_queries_total = Counter(
    "db_queries_total",
    "Total number of database queries",
)

db_query_latency_seconds = Histogram(
    "db_query_latency_seconds",
    "Database query latency in seconds",
)

db_connection_errors = Counter(
    "db_connection_errors",
    "Total number of database connection errors",
)