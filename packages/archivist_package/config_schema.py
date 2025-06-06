"""
Configuration schema for the Archivist Package.
"""

ARCHIVIST_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "human_simulator": {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Enable the human simulation capability",
                    "default": True
                },
                "orchestration": {
                    "type": "object",
                    "properties": {
                        "max_concurrent_sessions": {
                            "type": "integer",
                            "description": "Maximum number of concurrent simulation sessions",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 100
                        },
                        "session_timeout_minutes": {
                            "type": "integer",
                            "description": "Session timeout in minutes",
                            "default": 60,
                            "minimum": 5
                        }
                    }
                },
                "browser_automation": {
                    "type": "object",
                    "properties": {
                        "engine": {
                            "type": "string",
                            "enum": ["playwright", "selenium", "puppeteer"],
                            "default": "playwright",
                            "description": "Browser automation engine to use"
                        },
                        "headless": {
                            "type": "boolean",
                            "default": True,
                            "description": "Run browser in headless mode"
                        },
                        "proxy_config": {
                            "type": "object",
                            "properties": {
                                "enabled": {
                                    "type": "boolean",
                                    "default": False
                                },
                                "type": {
                                    "type": "string",
                                    "enum": ["http", "socks5", "socks4"],
                                    "default": "http"
                                },
                                "host": {
                                    "type": "string"
                                },
                                "port": {
                                    "type": "integer"
                                },
                                "username": {
                                    "type": "string"
                                },
                                "password": {
                                    "type": "string"
                                }
                            }
                        }
                    }
                },
                "mirrorcore": {
                    "type": "object",
                    "properties": {
                        "stages_config_path": {
                            "type": "string",
                            "description": "Path to stage definitions JSON file",
                            "default": "./data/mirrorcore/stage_definitions.json"
                        },
                        "scoring_schema_path": {
                            "type": "string",
                            "description": "Path to scoring schema JSON file",
                            "default": "./data/mirrorcore/stage_scoring_schema.json"
                        },
                        "models": {
                            "type": "object",
                            "properties": {
                                "conversation": {
                                    "type": "string",
                                    "description": "Model for conversation generation",
                                    "default": "gpt-4-turbo"
                                },
                                "evaluation": {
                                    "type": "string",
                                    "description": "Model for stage evaluation",
                                    "default": "gpt-4"
                                },
                                "planning": {
                                    "type": "string",
                                    "description": "Model for strategic planning",
                                    "default": "gpt-4"
                                }
                            }
                        }
                    }
                }
            }
        },
        "financial_business": {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Enable financial business capabilities",
                    "default": True
                },
                "api_keys": {
                    "type": "object",
                    "properties": {
                        "payment_processor": {
                            "type": "string",
                            "description": "API key for payment processor integration"
                        },
                        "banking": {
                            "type": "string",
                            "description": "API key for banking integration"
                        },
                        "document_generator": {
                            "type": "string", 
                            "description": "API key for document generation service"
                        }
                    }
                },
                "document_templates_path": {
                    "type": "string",
                    "description": "Path to financial document templates",
                    "default": "./data/financial/templates"
                }
            }
        },
        "platforms": {
            "type": "object",
            "properties": {
                "dating_sites": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the dating platform"
                            },
                            "enabled": {
                                "type": "boolean",
                                "default": True
                            },
                            "auth_config": {
                                "type": "object",
                                "properties": {
                                    "auth_type": {
                                        "type": "string",
                                        "enum": ["cookie", "oauth", "basic"],
                                        "default": "cookie"
                                    },
                                    "credentials_path": {
                                        "type": "string",
                                        "description": "Path to stored credentials"
                                    }
                                }
                            }
                        }
                    }
                },
                "financial_platforms": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the financial platform"
                            },
                            "enabled": {
                                "type": "boolean",
                                "default": True
                            },
                            "api_config": {
                                "type": "object",
                                "properties": {
                                    "base_url": {
                                        "type": "string"
                                    },
                                    "credentials_path": {
                                        "type": "string"
                                    }
                                }
                            }
                        }
                    }
                },
                "messaging_apps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the messaging platform"
                            },
                            "enabled": {
                                "type": "boolean",
                                "default": True
                            },
                            "auth_config": {
                                "type": "object",
                                "properties": {
                                    "auth_type": {
                                        "type": "string"
                                    },
                                    "credentials_path": {
                                        "type": "string"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "rag_integration": {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "default": True
                },
                "vector_db": {
                    "type": "string",
                    "enum": ["pinecone", "weaviate", "faiss", "milvus"],
                    "default": "pinecone"
                },
                "embeddings_model": {
                    "type": "string",
                    "default": "text-embedding-ada-002"
                },
                "knowledge_base_directories": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "default": ["./data/archivist/knowledge"]
                }
            }
        },
        "logging": {
            "type": "object",
            "properties": {
                "level": {
                    "type": "string",
                    "enum": ["DEBUG", "INFO", "WARNING", "ERROR"],
                    "default": "INFO"
                },
                "file_path": {
                    "type": "string",
                    "default": "./logs/archivist.log"
                }
            }
        }
    },
    "required": ["human_simulator", "financial_business", "platforms"]
}
