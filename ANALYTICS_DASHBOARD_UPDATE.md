# Analytics Dashboard Updates - Dec 31, 2025

This document details the new analytics features added to the Global Divers backend to support the Business Owner Dashboard.

## 1. New Features

We have implemented a consolidated dashboard endpoint that provides real-time snapshot data, historical trends, and customer insights.

### Service: `AnalyticsServices.get_dashboard_summary()`
Located in `app/services/analytics.py`.

#### Key Metrics Added
1. **Sales Today**:
   - `revenue_today`: Total amount from PAID invoices today.
   - `sales_count_today`: Total number of PAID invoices today.
   - `trips_booked_today`: Count of 'trip' activity invoices today.
   - `courses_booked_today`: Count of 'course' activity invoices today.
   - `pending_invoices_today`: Action items for the owner.

2. **Financial Health**:
   - `average_order_value`: Average transaction size (Total Revenue / Paid Count).
   - `total_discount_given`: Total operational cost in discounts.
   - `potential_revenue`: Total value locked in PENDING invoices.

3. **Customer Insights**:
   - `top_customers`: List of top 5 customers by lifetime spend. Include Name, Email, Total Spent, and Invoice Count.

4. **Operational Metrics**:
   - `confirmation_rate`: % of invoices confirmed by admin.
   - `payment_method_distribution`: Breakdown of Cash vs Online payments.

5. **Charts (Last 30 Days)**:
   - `sales_over_time`: Daily series of Revenue and Count.
   - `activity_distribution`: Pie chart data for Trip vs Course sales.

## 2. API Reference

### `GET /analytics/dashboard`

**Auth Required**: Admin

**Response Schema**:
```json
{
  "stats": {
    "revenue_today": 1250.00,
    "sales_count_today": 8,
    "trips_booked_today": 5,
    "courses_booked_today": 3,
    "pending_invoices_today": 2,
    "average_order_value": 310.50,
    "total_discount_given": 120.00,
    "potential_revenue": 450.00,
    "confirmation_rate": 92.5
  },
  "charts": {
    "sales_over_time": [
      {
        "date": "2025-12-01",
        "revenue": 500.0,
        "count": 2
      },
      ...
    ],
    "activity_distribution": [
      {
        "name": "Trip",
        "value": 150
      },
      {
        "name": "Course",
        "value": 45
      }
    ],
    "payment_method_distribution": [
      {
        "name": "Online (EasyKash)",
        "value": 180
      },
      {
        "name": "Cash",
        "value": 15
      }
    ]
  },
  "top_customers": [
    {
      "name": "Ahmed Mohamed",
      "email": "ahmed@test.com",
      "total_spent": 5400.00,
      "order_count": 12
    },
    ...
  ],
  "recent_transactions": [
    {
      "id": 1024,
      "buyer": "Sarah Jones",
      "amount": 150.0,
      "status": "PAID",
      "date": "2025-12-31T10:00:00"
    },
    ...
  ]
}
```
