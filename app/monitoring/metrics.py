from prometheus_client import Counter, Histogram, Gauge, Info
from functools import wraps
import time

# API Request Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)

# License Metrics
license_total = Counter(
    'license_total',
    'Total number of licenses',
    ['type', 'status']
)

license_expiry = Gauge(
    'license_expiry',
    'Days until license expiry',
    ['license_id']
)

# User Metrics
user_total = Counter(
    'user_total',
    'Total number of users',
    ['status']
)

active_users = Gauge(
    'active_users',
    'Number of active users in the last 24 hours'
)

# Payment Metrics
payment_total = Counter(
    'payment_total',
    'Total payment amount',
    ['status', 'provider', 'currency']
)

payment_duration_seconds = Histogram(
    'payment_duration_seconds',
    'Payment processing duration in seconds',
    ['provider']
)

# API Performance Metrics
api_errors_total = Counter(
    'api_errors_total',
    'Total number of API errors',
    ['endpoint', 'error_type']
)

api_response_size_bytes = Histogram(
    'api_response_size_bytes',
    'Size of API responses in bytes',
    ['endpoint']
)

# Cache Metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Total number of cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total number of cache misses',
    ['cache_type']
)

# Database Metrics
db_queries_total = Counter(
    'db_queries_total',
    'Total number of database queries',
    ['operation', 'collection']
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'collection']
)

# System Metrics
system_memory_usage_bytes = Gauge(
    'system_memory_usage_bytes',
    'Current system memory usage in bytes'
)

system_cpu_usage_percent = Gauge(
    'system_cpu_usage_percent',
    'Current system CPU usage percentage'
)

# Version Info
api_version = Info(
    'api_version',
    'API version information'
)

def track_request_metrics(endpoint: str):
    """Decorator to track request metrics."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            method = kwargs.get('request').method if 'request' in kwargs else 'UNKNOWN'
            
            # Track in-progress requests
            http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
            
            start_time = time.time()
            status = "200"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "500"
                api_errors_total.labels(
                    endpoint=endpoint,
                    error_type=type(e).__name__
                ).inc()
                raise
            finally:
                # Record metrics
                duration = time.time() - start_time
                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).inc()
                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                http_requests_in_progress.labels(
                    method=method,
                    endpoint=endpoint
                ).dec()
                
        return wrapper
    return decorator

def track_db_metrics(operation: str, collection: str):
    """Decorator to track database metrics."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                # Record metrics
                duration = time.time() - start_time
                db_queries_total.labels(
                    operation=operation,
                    collection=collection
                ).inc()
                db_query_duration_seconds.labels(
                    operation=operation,
                    collection=collection
                ).observe(duration)
                
        return wrapper
    return decorator

def track_cache_metrics(cache_type: str):
    """Decorator to track cache metrics."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_hit = False
            
            try:
                result = await func(*args, **kwargs)
                cache_hit = result is not None
                return result
            finally:
                # Record metrics
                if cache_hit:
                    cache_hits_total.labels(cache_type=cache_type).inc()
                else:
                    cache_misses_total.labels(cache_type=cache_type).inc()
                
        return wrapper
    return decorator
