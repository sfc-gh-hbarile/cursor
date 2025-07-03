# Snowflake Troubleshooting Guide

Comprehensive guide to diagnose and resolve common Snowflake development issues.

## 🔐 Authentication Issues

### Problem: "Authentication failed" or "Invalid credentials"
**Symptoms:**
- Connection timeout during authentication
- "User does not exist" errors
- "Invalid private key" messages

**Solutions:**
```bash
# 1. Verify account identifier format
# Correct: abc12345.us-east-1
# Incorrect: abc12345 (missing region)

# 2. Check private key format
openssl rsa -in keys/rsa_key.p8 -check
openssl rsa -in keys/rsa_key.p8 -pubout -out keys/rsa_key.pub

# 3. Verify public key is added to Snowflake user
ALTER USER STREAMING_USER SET RSA_PUBLIC_KEY='<PUBLIC_KEY_CONTENT>';

# 4. Test connection with SnowSQL
snowsql -a your_account.region -u STREAMING_USER --private-key-path keys/rsa_key.p8
```

**Debug Steps:**
```java
// Add debug logging for authentication
logger.info("Connecting to account: {}", account);
logger.info("Using user: {}", user);
logger.info("Private key file exists: {}", Files.exists(Paths.get(privateKeyFile)));

// Verify private key loading
try {
    PrivateKey key = loadPrivateKey();
    logger.info("Private key loaded successfully, algorithm: {}", key.getAlgorithm());
} catch (Exception e) {
    logger.error("Failed to load private key", e);
}
```

### Problem: "Role does not exist" or "Access denied"
**Symptoms:**
- Can connect but can't access databases/schemas
- "Insufficient privileges" errors

**Solutions:**
```sql
-- Check user roles
SHOW GRANTS TO USER STREAMING_USER;

-- Check role permissions
SHOW GRANTS TO ROLE SNOWPIPE_STREAMING_ROLE;

-- Verify role hierarchy
SHOW ROLES;

-- Grant missing permissions
GRANT USAGE ON WAREHOUSE STREAMING_WH TO ROLE SNOWPIPE_STREAMING_ROLE;
GRANT USAGE ON DATABASE STREAMING_DEMO TO ROLE SNOWPIPE_STREAMING_ROLE;
```

## 🌊 Streaming Issues

### Problem: "Channel creation failed" or "Table does not exist"
**Symptoms:**
- Cannot create streaming channels
- "Object does not exist" errors
- Connection established but streaming fails

**Solutions:**
```java
// 1. Verify table exists and has correct schema
Properties props = new Properties();
props.setProperty("database", "STREAMING_DEMO");
props.setProperty("schema", "REALTIME");

// 2. Check table structure
String query = "DESCRIBE TABLE STREAMING_DEMO.REALTIME.SENSOR_DATA";

// 3. Verify channel creation parameters
OpenChannelRequest request = OpenChannelRequest.builder("SENSOR_CHANNEL")
    .setDBName("STREAMING_DEMO")          // Must match exactly
    .setSchemaName("REALTIME")           // Must match exactly
    .setTableName("SENSOR_DATA")         // Must match exactly
    .setOnErrorOption(OpenChannelRequest.OnErrorOption.CONTINUE)
    .build();
```

**Debug Steps:**
```sql
-- Check if table exists
SELECT TABLE_NAME, TABLE_SCHEMA, TABLE_TYPE 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME = 'SENSOR_DATA';

-- Verify current context
SELECT CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_ROLE();

-- Check streaming permissions
SHOW GRANTS TO ROLE SNOWPIPE_STREAMING_ROLE;
```

### Problem: "Schema validation failed" or "Column mismatch"
**Symptoms:**
- Data insertion fails with validation errors
- "Column not found" errors
- Type conversion errors

**Solutions:**
```java
// 1. Match Java data types to Snowflake columns
Map<String, Object> row = new HashMap<>();
row.put("SENSOR_ID", "SENSOR_001");           // VARCHAR
row.put("TIMESTAMP", Instant.now());          // TIMESTAMP_NTZ
row.put("TEMPERATURE", 23.5);                 // FLOAT
row.put("METADATA", objectMapper.writeValueAsString(metadata)); // VARIANT

// 2. Handle null values properly
row.put("OPTIONAL_FIELD", value != null ? value : null);

// 3. Validate data before insertion
private void validateRow(Map<String, Object> row) {
    if (row.get("SENSOR_ID") == null) {
        throw new IllegalArgumentException("SENSOR_ID cannot be null");
    }
    if (!(row.get("TEMPERATURE") instanceof Number)) {
        throw new IllegalArgumentException("TEMPERATURE must be a number");
    }
}
```

**Debug Steps:**
```sql
-- Check table schema
DESCRIBE TABLE STREAMING_DEMO.REALTIME.SENSOR_DATA;

-- Test data types
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'SENSOR_DATA';
```

## 🔍 Performance Issues

### Problem: "Slow streaming performance" or "High latency"
**Symptoms:**
- Data takes too long to appear in Snowflake
- Low throughput (< 1000 records/second)
- High memory usage

**Solutions:**
```properties
# Optimize batch processing
streaming.batch_size=5000              # Increase from default 1000
streaming.flush_interval=500           # Decrease from default 1000ms
streaming.channel_buffer_size=50000    # Increase buffer size
streaming.enable_compression=true      # Enable compression
streaming.connection_pool_size=10      # Increase connection pool

# JVM tuning
-Xmx4g -Xms2g
-XX:+UseG1GC
-XX:G1HeapRegionSize=16m
```

**Debug Steps:**
```java
// Monitor batch processing
private void monitorPerformance() {
    long startTime = System.currentTimeMillis();
    
    // Process batch
    InsertValidationResponse response = channel.insertRows(batch, null);
    
    long endTime = System.currentTimeMillis();
    long duration = endTime - startTime;
    
    logger.info("Batch size: {}, Duration: {}ms, Throughput: {} records/sec", 
        batch.size(), duration, (batch.size() * 1000.0) / duration);
}
```

### Problem: "Out of memory" errors
**Symptoms:**
- Application crashes with OOM errors
- High memory usage in monitoring

**Solutions:**
```java
// 1. Implement streaming buffer with size limits
public class BoundedStreamingBuffer {
    private final int maxSize;
    private final List<Map<String, Object>> buffer;
    
    public void addRecord(Map<String, Object> record) {
        if (buffer.size() >= maxSize) {
            flushBuffer();
        }
        buffer.add(record);
    }
}

// 2. Use object pooling for frequently created objects
private final ObjectPool<Map<String, Object>> mapPool = new GenericObjectPool<>(
    new MapPoolableObjectFactory()
);

// 3. Process data in streaming fashion
try (Stream<String> lines = Files.lines(Paths.get("large_file.csv"))) {
    lines.parallel()
         .map(this::parseRecord)
         .forEach(this::processRecord);
}
```

## 📊 Data Quality Issues

### Problem: "Duplicate records" or "Data consistency issues"
**Symptoms:**
- Same data appears multiple times
- Missing records
- Data out of order

**Solutions:**
```sql
-- 1. Add unique constraints and handle duplicates
CREATE TABLE SENSOR_DATA (
    SENSOR_ID VARCHAR(50) NOT NULL,
    TIMESTAMP TIMESTAMP_NTZ NOT NULL,
    TEMPERATURE FLOAT,
    PRIMARY KEY (SENSOR_ID, TIMESTAMP)
);

-- 2. Use MERGE for upsert operations
MERGE INTO SENSOR_DATA AS target
USING (
    SELECT 'SENSOR_001' AS sensor_id, CURRENT_TIMESTAMP() AS timestamp, 23.5 AS temperature
) AS source
ON target.SENSOR_ID = source.sensor_id AND target.TIMESTAMP = source.timestamp
WHEN MATCHED THEN
    UPDATE SET temperature = source.temperature
WHEN NOT MATCHED THEN
    INSERT (sensor_id, timestamp, temperature) 
    VALUES (source.sensor_id, source.timestamp, source.temperature);
```

**Debug Steps:**
```java
// Add idempotency checking
private boolean isRecordDuplicate(Map<String, Object> record) {
    String sensorId = (String) record.get("SENSOR_ID");
    Instant timestamp = (Instant) record.get("TIMESTAMP");
    
    // Check if record already exists
    return existingRecords.contains(sensorId + "_" + timestamp);
}

// Add batch ID for tracking
record.put("BATCH_ID", UUID.randomUUID().toString());
record.put("INGESTION_TIME", Instant.now());
```

### Problem: "Invalid JSON" or "VARIANT parsing errors"
**Symptoms:**
- JSON columns contain invalid data
- Type conversion errors for VARIANT columns

**Solutions:**
```java
// 1. Validate JSON before insertion
private void validateJSON(Map<String, Object> record) {
    Object metadata = record.get("METADATA");
    if (metadata != null) {
        try {
            objectMapper.writeValueAsString(metadata);
        } catch (JsonProcessingException e) {
            throw new IllegalArgumentException("Invalid JSON in METADATA field", e);
        }
    }
}

// 2. Use proper JSON serialization
private String serializeToJSON(Object obj) {
    try {
        return objectMapper.writeValueAsString(obj);
    } catch (JsonProcessingException e) {
        logger.error("Failed to serialize object to JSON", e);
        return "{}"; // Return empty JSON object as fallback
    }
}
```

## 🔧 Configuration Issues

### Problem: "Connection timeout" or "Network errors"
**Symptoms:**
- Random connection failures
- Timeouts during data transfer
- Network-related exceptions

**Solutions:**
```properties
# Network timeout settings
snowflake.network_timeout=300000       # 5 minutes
snowflake.login_timeout=60000          # 1 minute
snowflake.query_timeout=3600000        # 1 hour
snowflake.socket_timeout=300000        # 5 minutes

# Retry configuration
streaming.max_retries=5
streaming.retry_delay_ms=2000
streaming.exponential_backoff=true

# Connection pool settings
streaming.connection_pool_size=10
streaming.connection_pool_timeout=30000
```

**Debug Steps:**
```java
// Add network diagnostics
private void diagnoseNetwork() {
    try {
        InetAddress address = InetAddress.getByName("your_account.snowflakecomputing.com");
        boolean reachable = address.isReachable(5000);
        logger.info("Snowflake endpoint reachable: {}", reachable);
    } catch (IOException e) {
        logger.error("Network connectivity issue", e);
    }
}
```

## 📈 Monitoring and Alerting

### Problem: "No visibility into streaming performance"
**Symptoms:**
- Can't track streaming metrics
- No alerts for failures
- Difficult to troubleshoot issues

**Solutions:**
```java
// 1. Implement comprehensive metrics
public class StreamingMetrics {
    private final AtomicLong totalRecords = new AtomicLong(0);
    private final AtomicLong totalErrors = new AtomicLong(0);
    private final AtomicLong totalLatency = new AtomicLong(0);
    
    public void recordSuccess(long latencyMs) {
        totalRecords.incrementAndGet();
        totalLatency.addAndGet(latencyMs);
    }
    
    public void recordError() {
        totalErrors.incrementAndGet();
    }
    
    public void logMetrics() {
        long records = totalRecords.get();
        long errors = totalErrors.get();
        long avgLatency = records > 0 ? totalLatency.get() / records : 0;
        
        logger.info("Streaming Metrics - Records: {}, Errors: {}, Avg Latency: {}ms, Error Rate: {}%",
            records, errors, avgLatency, (errors * 100.0) / (records + errors));
    }
}
```

**Monitoring Queries:**
```sql
-- Real-time streaming status
SELECT 
    CLIENT_NAME,
    CHANNEL_NAME,
    IS_VALID,
    ROW_COUNT,
    LAST_RECEIVED_TIME
FROM SNOWFLAKE.ACCOUNT_USAGE.SNOWPIPE_STREAMING_CHANNELS
WHERE CLIENT_NAME = 'SENSOR_STREAM_CLIENT';

-- Error analysis
SELECT 
    ERROR_TYPE,
    COUNT(*) as error_count,
    MAX(TIMESTAMP) as last_error
FROM SNOWFLAKE.ACCOUNT_USAGE.SNOWPIPE_STREAMING_CLIENT_HISTORY
WHERE CLIENT_NAME = 'SENSOR_STREAM_CLIENT'
    AND ERROR_TYPE IS NOT NULL
GROUP BY ERROR_TYPE;
```

## 🚨 Emergency Troubleshooting

### Critical Issues Checklist
1. **Service Down:**
   ```bash
   # Check if Snowflake service is available
   ping your_account.snowflakecomputing.com
   
   # Test basic connection
   snowsql -a your_account -u your_user -r your_role
   ```

2. **Data Loss:**
   ```sql
   -- Check recent data ingestion
   SELECT 
       COUNT(*) as recent_records,
       MAX(INGESTION_TIME) as last_ingestion
   FROM SENSOR_DATA 
   WHERE INGESTION_TIME >= DATEADD(hour, -1, CURRENT_TIMESTAMP());
   
   -- Check for gaps in data
   SELECT 
       sensor_id,
       COUNT(*) as record_count,
       MIN(timestamp) as first_record,
       MAX(timestamp) as last_record
   FROM SENSOR_DATA 
   WHERE timestamp >= DATEADD(hour, -24, CURRENT_TIMESTAMP())
   GROUP BY sensor_id;
   ```

3. **Performance Degradation:**
   ```sql
   -- Check warehouse utilization
   SELECT 
       WAREHOUSE_NAME,
       AVG(AVG_RUNNING) as avg_running_queries,
       AVG(AVG_QUEUED_LOAD) as avg_queued_load
   FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_LOAD_HISTORY
   WHERE START_TIME >= DATEADD(hour, -1, CURRENT_TIMESTAMP())
   GROUP BY WAREHOUSE_NAME;
   ```

## 🔍 Debug Logging Configuration

### Enable Detailed Logging
```xml
<!-- logback.xml -->
<configuration>
    <!-- Snowflake SDK detailed logging -->
    <logger name="net.snowflake" level="DEBUG"/>
    <logger name="net.snowflake.ingest" level="DEBUG"/>
    
    <!-- HTTP client logging -->
    <logger name="org.apache.http.wire" level="DEBUG"/>
    <logger name="org.apache.http.headers" level="DEBUG"/>
    
    <!-- Application logging -->
    <logger name="com.example" level="DEBUG"/>
</configuration>
```

### Common Log Messages and Meanings
- **"Channel opened successfully"** - Channel creation succeeded
- **"Insert validation failed"** - Data validation issues
- **"Connection closed"** - Network or authentication issues
- **"Retry attempt X"** - Automatic retry in progress
- **"Buffer flush completed"** - Batch successfully sent

## 📞 Getting Help

### When to Contact Support
- Authentication issues persist after following troubleshooting steps
- Data corruption or loss
- Performance issues that can't be resolved with tuning
- Snowflake service outages

### Information to Provide
- Account identifier
- User and role information
- Error messages and stack traces
- Application logs
- Timing of issues
- Performance metrics

### Useful Commands for Support
```sql
-- Account information
SELECT CURRENT_ACCOUNT(), CURRENT_REGION();

-- User permissions
SHOW GRANTS TO USER STREAMING_USER;

-- Recent query history
SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY 
WHERE USER_NAME = 'STREAMING_USER' 
ORDER BY START_TIME DESC LIMIT 10;
``` 