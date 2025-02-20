// MongoDB Schema for License Management API
// Run this file using: mongosh < schema.js

// Switch to the database
db = db.getSiblingDB('license_management_api');

// Drop existing collections to ensure clean state
db.getCollectionNames().forEach((collection) => {
    db.getCollection(collection).drop();
});

// Users Collection
db.createCollection("users", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["email", "username", "role", "is_active", "created_at"],
            properties: {
                email: { bsonType: "string" },
                username: { bsonType: "string" },
                password_hash: { bsonType: "string" },
                role: { enum: ["admin", "user", "reseller", "affiliate"] },
                is_active: { bsonType: "bool" },
                is_verified: { bsonType: "bool" },
                auth_provider: { enum: ["local", "google", "github", "microsoft"] },
                auth_provider_id: { bsonType: "string" },
                stripe_customer_id: { bsonType: "string" },
                two_factor_enabled: { bsonType: "bool" },
                two_factor_secret: { bsonType: "string" },
                api_key: { bsonType: "string" },
                api_secret_hash: { bsonType: "string" },
                last_login: { bsonType: "date" },
                login_attempts: { bsonType: "int" },
                locked_until: { bsonType: "date" },
                created_at: { bsonType: "date" },
                updated_at: { bsonType: "date" },
                metadata: { bsonType: "object" }
            }
        }
    }
});

// Licenses Collection
db.createCollection("licenses", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["key", "user_id", "type", "is_active", "created_at"],
            properties: {
                key: { bsonType: "string" },
                user_id: { bsonType: "string" },
                type: { enum: ["trial", "basic", "pro", "enterprise"] },
                features: { bsonType: "array" },
                max_devices: { bsonType: "int" },
                max_api_calls: { bsonType: "int" },
                is_active: { bsonType: "bool" },
                activation_date: { bsonType: "date" },
                expiration_date: { bsonType: "date" },
                last_checked: { bsonType: "date" },
                metadata: { bsonType: "object" },
                created_at: { bsonType: "date" },
                updated_at: { bsonType: "date" }
            }
        }
    }
});

// Subscriptions Collection
db.createCollection("subscriptions", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["user_id", "plan_id", "status", "current_period_start", "current_period_end"],
            properties: {
                user_id: { bsonType: "string" },
                plan_id: { bsonType: "string" },
                status: { enum: ["active", "inactive", "pending", "cancelled"] },
                current_period_start: { bsonType: "date" },
                current_period_end: { bsonType: "date" },
                cancel_at_period_end: { bsonType: "bool" },
                canceled_at: { bsonType: "date" },
                payment_method_id: { bsonType: "string" },
                metadata: { bsonType: "object" },
                created_at: { bsonType: "date" },
                updated_at: { bsonType: "date" }
            }
        }
    }
});

// Payments Collection
db.createCollection("payments", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["user_id", "amount", "currency", "provider", "status"],
            properties: {
                user_id: { bsonType: "string" },
                subscription_id: { bsonType: "string" },
                amount: { bsonType: "double" },
                currency: { bsonType: "string" },
                provider: { enum: ["stripe", "paypal", "crypto"] },
                provider_payment_id: { bsonType: "string" },
                status: { enum: ["pending", "completed", "failed", "refunded"] },
                metadata: { bsonType: "object" },
                created_at: { bsonType: "date" },
                updated_at: { bsonType: "date" }
            }
        }
    }
});

// API Keys Collection
db.createCollection("api_keys", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["user_id", "key", "secret_hash", "name"],
            properties: {
                user_id: { bsonType: "string" },
                key: { bsonType: "string" },
                secret_hash: { bsonType: "string" },
                name: { bsonType: "string" },
                permissions: { bsonType: "array" },
                rate_limit: { bsonType: "int" },
                expires_at: { bsonType: "date" },
                last_used: { bsonType: "date" },
                created_at: { bsonType: "date" },
                updated_at: { bsonType: "date" }
            }
        }
    }
});

// Webhooks Collection
db.createCollection("webhooks", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["user_id", "url", "events", "secret"],
            properties: {
                user_id: { bsonType: "string" },
                url: { bsonType: "string" },
                events: { bsonType: "array" },
                secret: { bsonType: "string" },
                is_active: { bsonType: "bool" },
                created_at: { bsonType: "date" },
                updated_at: { bsonType: "date" }
            }
        }
    }
});

// Metrics Collection
db.createCollection("metrics", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["name", "value", "timestamp"],
            properties: {
                name: { bsonType: "string" },
                value: { bsonType: "double" },
                tags: { bsonType: "object" },
                timestamp: { bsonType: "date" }
            }
        }
    }
});

// Alerts Collection
db.createCollection("alerts", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["name", "condition", "threshold"],
            properties: {
                name: { bsonType: "string" },
                condition: { bsonType: "string" },
                threshold: { bsonType: "double" },
                status: { bsonType: "string" },
                last_triggered: { bsonType: "date" },
                created_at: { bsonType: "date" },
                updated_at: { bsonType: "date" }
            }
        }
    }
});

// Security Logs Collection
db.createCollection("security_logs", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["event_type", "ip_address", "created_at"],
            properties: {
                user_id: { bsonType: "string" },
                event_type: { bsonType: "string" },
                ip_address: { bsonType: "string" },
                user_agent: { bsonType: "string" },
                details: { bsonType: "object" },
                severity: { bsonType: "string" },
                created_at: { bsonType: "date" }
            }
        }
    }
});

// Blocked IPs Collection
db.createCollection("blocked_ips", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["ip_address", "reason"],
            properties: {
                ip_address: { bsonType: "string" },
                reason: { bsonType: "string" },
                blocked_until: { bsonType: "date" },
                created_at: { bsonType: "date" }
            }
        }
    }
});

// ML Models Collection
db.createCollection("ml_models", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["name", "version", "type"],
            properties: {
                name: { bsonType: "string" },
                version: { bsonType: "string" },
                type: { bsonType: "string" },
                metrics: { bsonType: "object" },
                is_active: { bsonType: "bool" },
                created_at: { bsonType: "date" },
                updated_at: { bsonType: "date" }
            }
        }
    }
});

// Resellers Collection
db.createCollection("resellers", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["user_id", "company_name", "commission_rate"],
            properties: {
                user_id: { bsonType: "string" },
                company_name: { bsonType: "string" },
                commission_rate: { bsonType: "double" },
                total_sales: { bsonType: "double" },
                is_active: { bsonType: "bool" },
                metadata: { bsonType: "object" },
                created_at: { bsonType: "date" },
                updated_at: { bsonType: "date" }
            }
        }
    }
});

// Affiliates Collection
db.createCollection("affiliates", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["user_id", "affiliate_code", "commission_rate"],
            properties: {
                user_id: { bsonType: "string" },
                affiliate_code: { bsonType: "string" },
                commission_rate: { bsonType: "double" },
                total_earnings: { bsonType: "double" },
                is_active: { bsonType: "bool" },
                metadata: { bsonType: "object" },
                created_at: { bsonType: "date" },
                updated_at: { bsonType: "date" }
            }
        }
    }
});

// Feature Flags Collection
db.createCollection("feature_flags", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["name", "description", "is_enabled"],
            properties: {
                name: { bsonType: "string" },
                description: { bsonType: "string" },
                is_enabled: { bsonType: "bool" },
                rules: { bsonType: "object" },
                created_at: { bsonType: "date" },
                updated_at: { bsonType: "date" }
            }
        }
    }
});

// System Settings Collection
db.createCollection("system_settings", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["key", "value"],
            properties: {
                key: { bsonType: "string" },
                value: { bsonType: "object" },
                created_at: { bsonType: "date" },
                updated_at: { bsonType: "date" }
            }
        }
    }
});

// Create indexes
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "username": 1 }, { unique: true });
db.users.createIndex({ "api_key": 1 }, { unique: true, sparse: true });

db.licenses.createIndex({ "key": 1 }, { unique: true });
db.licenses.createIndex({ "user_id": 1 });

db.subscriptions.createIndex({ "user_id": 1 });
db.subscriptions.createIndex({ "status": 1 });

db.payments.createIndex({ "user_id": 1 });
db.payments.createIndex({ "subscription_id": 1 });
db.payments.createIndex({ "provider_payment_id": 1 });

db.api_keys.createIndex({ "key": 1 }, { unique: true });
db.api_keys.createIndex({ "user_id": 1 });

db.webhooks.createIndex({ "user_id": 1 });
db.webhooks.createIndex({ "events": 1 });

db.metrics.createIndex({ "name": 1, "timestamp": -1 });
db.metrics.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 7776000 }); // 90 days TTL

db.security_logs.createIndex({ "user_id": 1 });
db.security_logs.createIndex({ "ip_address": 1 });
db.security_logs.createIndex({ "created_at": 1 }, { expireAfterSeconds: 31536000 }); // 1 year TTL

db.blocked_ips.createIndex({ "ip_address": 1 }, { unique: true });

db.resellers.createIndex({ "user_id": 1 }, { unique: true });
db.resellers.createIndex({ "company_name": 1 });

db.affiliates.createIndex({ "user_id": 1 }, { unique: true });
db.affiliates.createIndex({ "affiliate_code": 1 }, { unique: true });

db.feature_flags.createIndex({ "name": 1 }, { unique: true });

db.system_settings.createIndex({ "key": 1 }, { unique: true });

// Create initial admin user
db.users.insertOne({
    email: "admin@example.com",
    username: "admin",
    password_hash: "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewFX1FKFAQNkJGPK", // Default: "admin123"
    role: "admin",
    is_active: true,
    is_verified: true,
    auth_provider: "local",
    created_at: new Date(),
    updated_at: new Date()
});

// Create initial system settings
db.system_settings.insertMany([
    {
        key: "license_settings",
        value: {
            trial_duration_days: 14,
            max_devices_basic: 2,
            max_devices_pro: 5,
            max_devices_enterprise: -1
        },
        created_at: new Date(),
        updated_at: new Date()
    },
    {
        key: "security_settings",
        value: {
            max_login_attempts: 5,
            lockout_duration_minutes: 30,
            jwt_expiry_hours: 24,
            require_2fa_for_admin: true
        },
        created_at: new Date(),
        updated_at: new Date()
    },
    {
        key: "api_settings",
        value: {
            rate_limit_per_minute: 60,
            max_payload_size_mb: 10,
            require_https: true
        },
        created_at: new Date(),
        updated_at: new Date()
    }
]);
