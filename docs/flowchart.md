# Saga Pattern Demo - Complete Workflow

This flowchart illustrates the complete Saga Pattern implementation for distributed transaction management in the e-commerce order processing system.

## Main Saga Workflow

```mermaid
flowchart TD
    %% API Entry Point
    A[Client POST /orders] --> B[Create Order Object]
    B --> C[Generate Order ID & Saga ID]
    C --> D[Store Order in Database]

    %% Saga Orchestrator Initialization
    D --> E[Saga Orchestrator: execute_saga]
    E --> F[Initialize Saga Transaction]
    F --> G[Set Status: PENDING]

    %% Step 1: Validate Order
    G --> H[Step 1: Validate Order]
    H --> I{Validation Check}
    I -->|Valid| J[Mark Step: COMPLETED]
    I -->|Invalid| K[Mark Step: FAILED]

    %% Step 2: Reserve Inventory
    J --> L[Step 2: Reserve Inventory]
    L --> M{Check Inventory}
    M -->|Sufficient| N[Reduce Inventory Count]
    N --> O[Mark Step: COMPLETED]
    M -->|Insufficient| P[Mark Step: FAILED]

    %% Step 3: Process Payment
    O --> Q[Step 3: Process Payment]
    Q --> R{Check User Balance}
    R -->|Sufficient| S[Deduct Amount from Balance]
    S --> T[Mark Step: COMPLETED]
    R -->|Insufficient| U[Mark Step: FAILED]

    %% Step 4: Ship Order
    T --> V[Step 4: Ship Order]
    V --> W{Shipping Check}
    W -->|Success| X[Mark Step: COMPLETED]
    W -->|Failure| Y[Mark Step: FAILED]

    %% Success Path
    X --> Z[Set Saga Status: COMPLETED]
    Z --> AA[Set Order Status: COMPLETED]
    AA --> BB[Return Success Response]

    %% Failure Paths
    K --> CC[Start Compensation]
    P --> CC
    U --> CC
    Y --> CC

    %% Compensation Flow
    CC --> DD[Set Saga Status: COMPENSATING]
    DD --> EE[Compensate in Reverse Order]

    %% Compensation Steps
    EE --> FF{Previous Steps Completed?}
    FF -->|Yes| GG[Step 3: Refund Payment]
    FF -->|No| HH[Step 2: Release Inventory]
    FF -->|No| II[Step 1: No Compensation Needed]

    GG --> JJ[Add Amount Back to Balance]
    JJ --> KK[Mark Step: COMPENSATED]
    KK --> HH

    HH --> LL[Add Quantity Back to Inventory]
    LL --> MM[Mark Step: COMPENSATED]
    MM --> II

    II --> NN[Set Saga Status: FAILED]
    NN --> OO[Set Order Status: FAILED]
    OO --> PP[Return Error Response]

    %% Styling
    classDef success fill:#d4edda,stroke:#155724,stroke-width:2px
    classDef failure fill:#f8d7da,stroke:#721c24,stroke-width:2px
    classDef process fill:#d1ecf1,stroke:#0c5460,stroke-width:2px
    classDef decision fill:#fff3cd,stroke:#856404,stroke-width:2px
    classDef compensation fill:#f8d7da,stroke:#721c24,stroke-width:2px

    class Z,AA,BB success
    class K,P,U,Y,NN,OO,PP failure
    class B,C,D,E,F,G,H,J,L,N,O,Q,S,T,V,X process
    class I,M,R,W,FF decision
    class CC,DD,EE,GG,JJ,KK,HH,LL,MM,II compensation
```

## Detailed Service Interactions

```mermaid
flowchart TD
    %% Service Layer Details
    A[ValidationService] --> A1[Check Quantity > 0]
    A1 --> A2[Check Amount > 0]
    A2 --> A3[Check User Exists]
    A3 --> A4[Simulate Async Processing]

    B[InventoryService] --> B1[Check Product Exists]
    B1 --> B2[Check Sufficient Stock]
    B2 --> B3[Reduce Inventory Count]
    B3 --> B4[Simulate Async Processing]

    C[PaymentService] --> C1[Check User Balance]
    C1 --> C2[Check Sufficient Funds]
    C2 --> C3[Deduct Amount]
    C3 --> C4[Simulate Async Processing]

    D[ShippingService] --> D1[Check Shipping Address]
    D1 --> D2{User ID Check}
    D2 -->|user_3| D3[Simulate Failure]
    D2 -->|Other Users| D4[Process Shipment]
    D4 --> D5[Simulate Async Processing]

    %% Compensation Services
    E[ValidationService.compensate] --> E1[No Action Required]

    F[InventoryService.compensate] --> F1[Add Quantity Back]
    F1 --> F2[Update Inventory DB]

    G[PaymentService.compensate] --> G1[Add Amount Back]
    G1 --> G2[Update User Balance]

    H[ShippingService.compensate] --> H1[Cancel Shipment]
    H1 --> H2[Log Cancellation]

    %% Styling
    classDef service fill:#e2e3e5,stroke:#383d41,stroke-width:2px
    classDef compensation fill:#f8d7da,stroke:#721c24,stroke-width:2px

    class A,B,C,D service
    class E,F,G,H compensation
```

## API Endpoints and Data Flow

```mermaid
flowchart LR
    %% Client Interactions
    Client[Client Application] --> POST[POST /orders]
    Client --> GET_ORDER["GET /orders/{id}"]
    Client --> GET_SAGA["GET /sagas/{id}"]
    Client --> GET_INV[GET /inventory]
    Client --> GET_BAL[GET /balances]
    Client --> HEALTH[GET /health]

    %% API Processing
    POST --> CreateOrder[Create Order]
    GET_ORDER --> FetchOrder[Fetch Order from DB]
    GET_SAGA --> FetchSaga[Fetch Saga from DB]
    GET_INV --> FetchInventory[Fetch Inventory DB]
    GET_BAL --> FetchBalances[Fetch User Balances]
    HEALTH --> HealthCheck[Health Check]

    %% Response Flow
    CreateOrder --> Response[Return Order + Saga ID]
    FetchOrder --> OrderResponse[Return Order Details]
    FetchSaga --> SagaResponse[Return Saga Status]
    FetchInventory --> InventoryResponse[Return Inventory Levels]
    FetchBalances --> BalanceResponse[Return User Balances]
    HealthCheck --> HealthResponse[Return Health Status]

    %% Database Layer
    CreateOrder --> OrdersDB[(Orders Database)]
    FetchOrder --> OrdersDB
    FetchSaga --> SagaDB[(Saga Transactions DB)]
    FetchInventory --> InventoryDB[(Inventory Database)]
    FetchBalances --> UserDB[(User Balances DB)]

    %% Styling
    classDef client fill:#d1ecf1,stroke:#0c5460,stroke-width:2px
    classDef api fill:#d4edda,stroke:#155724,stroke-width:2px
    classDef db fill:#fff3cd,stroke:#856404,stroke-width:2px
    classDef response fill:#e2e3e5,stroke:#383d41,stroke-width:2px

    class Client client
    class POST,GET_ORDER,GET_SAGA,GET_INV,GET_BAL,HEALTH api
    class OrdersDB,SagaDB,InventoryDB,UserDB db
    class Response,OrderResponse,SagaResponse,InventoryResponse,BalanceResponse,HealthResponse response
```

## Error Handling and Status Transitions

```mermaid
stateDiagram-v2
    [*] --> PENDING: Order Created

    PENDING --> PROCESSING: Saga Started
    PROCESSING --> COMPLETED: All Steps Success
    PROCESSING --> COMPENSATING: Step Failed

    COMPENSATING --> FAILED: Compensation Complete
    COMPENSATING --> COMPENSATING: Continue Compensation

    COMPLETED --> [*]
    FAILED --> [*]

    note right of PENDING
        Initial state when order
        is first created
    end note

    note right of PROCESSING
        Saga orchestrator executing
        steps sequentially
    end note

    note right of COMPENSATING
        Executing compensation
        actions in reverse order
    end note

    note right of COMPLETED
        All steps successful,
        order fulfilled
    end note

    note right of FAILED
        Compensation complete,
        order cancelled
    end note
```

## Test Scenarios Flow

```mermaid
flowchart TD
    %% Test Scenario 1: Success
    A1[Test 1: Valid Order] --> B1[user_1, product_1, qty=2, $100]
    B1 --> C1[All Steps Pass]
    C1 --> D1[Order: COMPLETED]

    %% Test Scenario 2: Payment Failure
    A2[Test 2: Insufficient Funds] --> B2[user_3, product_1, qty=1, $500]
    B2 --> C2[Payment Step Fails]
    C2 --> D2[Compensation: Release Inventory]
    D2 --> E2[Order: FAILED]

    %% Test Scenario 3: Shipping Failure
    A3[Test 3: Shipping Failure] --> B3[user_3, product_1, qty=1, $50]
    B3 --> C3[Shipping Step Fails]
    C3 --> D3[Compensation: Refund Payment]
    D3 --> E3[Compensation: Release Inventory]
    E3 --> F3[Order: FAILED]

    %% Test Scenario 4: Inventory Failure
    A4[Test 4: Insufficient Inventory] --> B4[user_1, product_1, qty=200]
    B4 --> C4[Inventory Step Fails]
    C4 --> D4[No Compensation Needed]
    D4 --> E4[Order: FAILED]

    %% Styling
    classDef success fill:#d4edda,stroke:#155724,stroke-width:2px
    classDef failure fill:#f8d7da,stroke:#721c24,stroke-width:2px
    classDef test fill:#e2e3e5,stroke:#383d41,stroke-width:2px

    class D1 success
    class E2,F3,E4 failure
    class A1,A2,A3,A4 test
```

## Key Features Highlighted

- **Orchestrator-based Saga**: Centralized coordination of transaction steps
- **Automatic Compensation**: Failed transactions trigger compensating actions
- **Step-by-step Tracking**: Detailed status tracking for each transaction step
- **Fault Tolerance**: Handles failures gracefully with automatic rollback
- **REST API**: Complete FastAPI implementation with comprehensive endpoints
- **Mock Services**: Simulated inventory, payment, and shipping services
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

The flowchart demonstrates how the Saga Pattern maintains data consistency across distributed services without using traditional ACID transactions, making it ideal for microservices architecture.
