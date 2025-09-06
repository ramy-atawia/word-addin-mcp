@description('The name of the Container App Environment')
param environmentName string = 'wordaddin-mcp-env'

@description('The name of the Container App')
param containerAppName string = 'wordaddin-mcp-app'

@description('The name of the PostgreSQL server')
param postgresServerName string = 'wordaddin-postgres'

@description('The name of the Redis cache')
param redisCacheName string = 'wordaddin-redis'

@description('The name of the storage account')
param storageAccountName string = 'wordaddinstorage'

@description('The location for all resources')
param location string = resourceGroup().location

@description('The environment (dev, staging, prod)')
param environment string = 'dev'

// Variables
var containerAppEnvironmentName = '${environmentName}-${environment}'
var containerAppNameFull = '${containerAppName}-${environment}'
var postgresServerNameFull = '${postgresServerName}-${environment}'
var redisCacheNameFull = '${redisCacheName}-${environment}'
var storageAccountNameFull = '${storageAccountName}${environment}'

// Container App Environment
resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: containerAppEnvironmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
  }
}

// Log Analytics Workspace
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'wordaddin-logs-${environment}'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// Application Insights
resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'wordaddin-insights-${environment}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
  }
}

// PostgreSQL Server
resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2023-06-01-preview' = {
  name: postgresServerNameFull
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    administratorLogin: 'wordaddin_admin'
    administratorLoginPassword: 'WordAddin2024!'
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
    version: '15'
  }
}

// PostgreSQL Database
resource postgresDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-06-01-preview' = {
  parent: postgresServer
  name: 'wordaddin'
  properties: {
    charset: 'utf8'
    collation: 'en_US.utf8'
  }
}

// Redis Cache
resource redisCache 'Microsoft.Cache/redis@2023-08-01' = {
  name: redisCacheNameFull
  location: location
  properties: {
    sku: {
      name: 'Standard'
      family: 'C'
      capacity: 1
    }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
  }
}

// Storage Account
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountNameFull
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
  }
}

// Container App
resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppNameFull
  location: location
  properties: {
    managedEnvironmentId: containerAppEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 80
        allowInsecure: false
        transport: 'http'
      }
      secrets: [
        {
          name: 'postgres-connection-string'
          value: 'Host=${postgresServer.properties.fullyQualifiedDomainName};Database=wordaddin;Username=wordaddin_admin;Password=WordAddin2024!;SSL Mode=Require;'
        }
        {
          name: 'redis-connection-string'
          value: '${redisCache.properties.hostName}:6380,password=${redisCache.listKeys().primaryKey},ssl=True,abortConnect=False'
        }
        {
          name: 'storage-connection-string'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: 'wordaddin-mcp-backend:latest'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'DATABASE_URL'
              secretRef: 'postgres-connection-string'
            }
            {
              name: 'REDIS_URL'
              secretRef: 'redis-connection-string'
            }
            {
              name: 'AZURE_STORAGE_CONNECTION_STRING'
              secretRef: 'storage-connection-string'
            }
            {
              name: 'ENVIRONMENT'
              value: environment
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: applicationInsights.properties.ConnectionString
            }
          ]
        }
        {
          name: 'frontend'
          image: 'wordaddin-mcp-frontend:latest'
          resources: {
            cpu: json('0.25')
            memory: '512Mi'
          }
          env: [
            {
              name: 'REACT_APP_API_URL'
              value: 'https://${containerApp.properties.configuration.ingress.fqdn}'
            }
            {
              name: 'REACT_APP_ENVIRONMENT'
              value: environment
            }
          ]
        }
        {
          name: 'mcp-server'
          image: 'wordaddin-mcp-server:latest'
          resources: {
            cpu: json('0.25')
            memory: '512Mi'
          }
          env: [
            {
              name: 'MCP_SERVER_PORT'
              value: '9001'
            }
            {
              name: 'ENVIRONMENT'
              value: environment
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 10
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '30'
              }
            }
          }
        ]
      }
    }
  }
}

// Outputs
output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output postgresServerName string = postgresServer.name
output redisCacheName string = redisCache.name
output storageAccountName string = storageAccount.name
output applicationInsightsConnectionString string = applicationInsights.properties.connectionString