# Saga Pattern Demo - Complete Workflow

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
    FF -->|Ship Completed| GG[Step 4: Cancel Shipment]
    FF -->|Payment Completed| HH[Step 3: Refund Payment]
    FF -->|Inventory Completed| II[Step 2: Release Inventory]
    FF -->|Validation Completed| JJ[Step 1: Mark Compensated]

    GG --> KK[Log Cancellation]
    KK --> LL[Mark Step: COMPENSATED]
    LL --> HH

    HH --> MM[Add Amount Back to Balance]
    MM --> NN[Mark Step: COMPENSATED]
    NN --> II

    II --> OO[Add Quantity Back to Inventory]
    OO --> PP[Mark Step: COMPENSATED]
    PP --> JJ

    JJ --> QQ[Mark Step: COMPENSATED]
    QQ --> RR[Set Saga Status: FAILED]
    RR --> SS[Set Order Status: FAILED]
    SS --> TT[Return Error Response]

    %% Styling
    classDef success fill:#d4edda,stroke:#155724,stroke-width:2px
    classDef failure fill:#f8d7da,stroke:#721c24,stroke-width:2px
    classDef process fill:#d1ecf1,stroke:#0c5460,stroke-width:2px
    classDef decision fill:#fff3cd,stroke:#856404,stroke-width:2px
    classDef compensation fill:#f8d7da,stroke:#721c24,stroke-width:2px

    class Z,AA,BB success
    class K,P,U,Y,RR,SS,TT failure
    class B,C,D,E,F,G,H,J,L,N,O,Q,S,T,V,X process
    class I,M,R,W,FF decision
    class CC,DD,EE,GG,HH,II,JJ,KK,LL,MM,NN,OO,PP,QQ compensation
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
    E[ValidationService.compensate] --> E1[Mark as Compensated - No Action]

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

    %% API Processing
    POST --> CreateOrder[Create Order]
    GET_ORDER --> FetchOrder[Fetch Order from DB]
    GET_SAGA --> FetchSaga[Fetch Saga from DB]
    GET_INV --> FetchInventory[Fetch Inventory DB]
    GET_BAL --> FetchBalances[Fetch User Balances]

    %% Response Flow
    CreateOrder --> Response[Return Order + Saga ID]
    FetchOrder --> OrderResponse[Return Order Details]
    FetchSaga --> SagaResponse[Return Saga Status]
    FetchInventory --> InventoryResponse[Return Inventory Levels]
    FetchBalances --> BalanceResponse[Return User Balances]

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
    class POST,GET_ORDER,GET_SAGA,GET_INV,GET_BAL,RESET,HEALTH api
    class OrdersDB,SagaDB,InventoryDB,UserDB db
    class Response,OrderResponse,SagaResponse,InventoryResponse,BalanceResponse,ResetResponse,HealthResponse response
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

    %% Test Scenario 2: Inventory Failure
    A2[Test 2: Insufficient Inventory] --> B2[user_1, product_1, qty=200]
    B2 --> C2[Inventory Step Fails]
    C2 --> D2[Compensation: Validate Order]
    D2 --> E2[Order: FAILED]

    %% Test Scenario 3: Payment Failure
    A3[Test 3: Insufficient Funds] --> B3[user_3, product_1, qty=1, $500]
    B3 --> C3[Payment Step Fails]
    C3 --> D3[Compensation: Release Inventory]
    D3 --> E3[Compensation: Validate Order]
    E3 --> F3[Order: FAILED]

    %% Test Scenario 4: Shipping Failure
    A4[Test 4: Shipping Failure] --> B4[user_3, product_1, qty=1, $50]
    B4 --> C4[Shipping Step Fails]
    C4 --> D4[Compensation: Refund Payment]
    D4 --> E4[Compensation: Release Inventory]
    E4 --> F4[Compensation: Validate Order]
    F4 --> G4[Order: FAILED]

    %% Styling
    classDef success fill:#d4edda,stroke:#155724,stroke-width:2px
    classDef failure fill:#f8d7da,stroke:#721c24,stroke-width:2px
    classDef test fill:#e2e3e5,stroke:#383d41,stroke-width:2px

    class D1 success
    class E2,F3,G4 failure
    class A1,A2,A3,A4 test
```

* **Note:** To simplify the demo, we simulate the Shipping Failure by hardcoding the logic: if the order is placed by `user_3`, and both the product inventory and the user’s balance are sufficient, we intentionally force an error at the final shipping step.

## Sequence Diagram

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Orchestrator
    participant Validation
    participant Inventory
    participant Payment
    participant Shipping

    Note over Client,API: Client initiates order creation
    Client->>API: POST /orders
    Note right of API: Validate and forward order to orchestrator
    API->>Orchestrator: execute_saga(order)
    Note right of Orchestrator: Start saga transaction
    Orchestrator->>Validation: validate_order()
    Validation-->>Orchestrator: result (valid/invalid)
    alt Validation Success
        Note right of Orchestrator: Proceed to inventory reservation
        Orchestrator->>Inventory: reserve_inventory()
        Inventory-->>Orchestrator: result (ok/fail)
        alt Inventory Success
            Note right of Orchestrator: Proceed to payment
            Orchestrator->>Payment: process_payment()
            Payment-->>Orchestrator: result (ok/fail)
            alt Payment Success
                Note right of Orchestrator: Proceed to shipping
                Orchestrator->>Shipping: ship_order()
                Shipping-->>Orchestrator: result (ok/fail)
                alt Shipping Success
                    Note over Orchestrator,API: All steps succeeded <br> Saga COMPLETED
                    Orchestrator->>API: saga COMPLETED
                    API-->>Client: Order Success
                else Shipping Failure
                    Note over Orchestrator,Payment: Shipping failed <br> Start compensation
                    Orchestrator->>Payment: compensate_payment()
                    Note right of Orchestrator: Compensate inventory
                    Orchestrator->>Inventory: compensate_inventory()
                    Note right of Orchestrator: Compensate validation
                    Orchestrator->>Validation: compensate_validation()
                    Orchestrator->>API: saga FAILED
                    API-->>Client: Order Failed (Shipping)
                end
            else Payment Failure
                Note over Orchestrator,Inventory: Payment failed <br> Start compensation
                Orchestrator->>Inventory: compensate_inventory()
                Note right of Orchestrator: Compensate validation
                Orchestrator->>Validation: compensate_validation()
                Orchestrator->>API: saga FAILED
                API-->>Client: Order Failed (Payment)
            end
        else Inventory Failure
            Note right of Orchestrator: Inventory reservation failed
            Note right of Orchestrator: Compensate validation
            Orchestrator->>Validation: compensate_validation()
            Orchestrator->>API: saga FAILED
            API-->>Client: Order Failed (Inventory)
        end
    else Validation Failure
        Note right of Orchestrator: Validation failed
        Orchestrator->>API: saga FAILED
        API-->>Client: Order Failed (Validation)
    end
``` 

## Key Features Highlighted

- **Orchestrator-based Saga**: Centralized coordination of transaction steps
- **Automatic Compensation**: Failed transactions trigger compensating actions
- **Step-by-step Tracking**: Detailed status tracking for each transaction step
- **Fault Tolerance**: Handles failures gracefully with automatic rollback
- **REST API**: Complete FastAPI implementation with comprehensive endpoints
- **Mock Services**: Simulated inventory, payment, and shipping services
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

These diagrams demonstrate how the Saga Pattern maintains data consistency across distributed services without using traditional ACID transactions, making it ideal for microservices architecture.
