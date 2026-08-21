"""
Synthetic business documents (quarterly reviews, policy notes, meeting
summaries) standing in for the internal reports an executive copilot would
reason over. In a real deployment these would be pulled from SharePoint,
Confluence, or email via the Enterprise Data Connector.
"""

DOCUMENTS = [
    """Q2 Business Review - Retail Division
    Overall revenue grew 4.2% quarter-over-quarter, driven primarily by
    strong performance in the Electronics and Home & Living categories.
    However, branches in smaller cities showed flat or declining growth,
    largely attributed to lower foot traffic and increased competition from
    local retailers. Management recommends reviewing staffing levels in
    underperforming branches before the next quarter, particularly the
    Manchester and Islamabad locations which have shown the weakest revenue
    trends over the past two quarters.""",

    """Inventory Policy Note
    Reorder thresholds are currently set at 20% of average monthly demand
    per SKU. Several branches have reported stockouts in fast-moving
    categories (Electronics, Groceries) during promotional periods. A
    revised dynamic reorder policy tied to real-time demand forecasting is
    under evaluation. Apparel items have shown the steepest decline in
    sell-through this quarter and are candidates for reduced future
    ordering or discontinuation.""",

    """Marketing Effectiveness Summary
    Social Media and Search channels delivered the highest return on ad
    spend this quarter, while TV campaigns underperformed relative to
    budget allocated. The marketing team is proposing a reallocation of
    15% of the TV budget toward Social and Search campaigns for the next
    cycle. Early estimates suggest this reallocation could lift overall
    marketing ROI by 8-12%.""",

    """HR Staffing Report
    Headcount costs are highest in the Marketing and IT departments this
    year, followed by Operations. Employee turnover in front-line retail
    roles remains above the internal target threshold in two regions.
    Exit interviews cite scheduling inflexibility and compensation as the
    top two reasons for attrition. A pilot flexible-scheduling program is
    being considered for high-turnover branches.""",

    """Customer Support Trends
    Delivery Delay and Product Defect remain the two most common ticket
    categories across all regions. Ticket volume has been notably higher
    at two specific branches over the past six months, which correlates
    with declining customer satisfaction scores at those locations and is
    flagged as a churn risk requiring management attention.""",

    """Vendor Reliability Assessment
    Vendors supplying the Electronics and Apparel categories show the
    widest variance in reliability scores. Vendors falling below the 0.7
    reliability threshold have contributed to stockouts in affected
    branches, and procurement is evaluating alternate suppliers for these
    categories ahead of the next ordering cycle.""",
]
