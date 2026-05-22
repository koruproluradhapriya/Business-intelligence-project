import logging

logger = logging.getLogger(__name__)


def analyze_inventory(items: list) -> list:
    analyzed = []
    for item in items:
        stock = float(item.get('stock', 0))
        reorder = float(item.get('reorderLevel', item.get('reorder_level', 50)))
        avg_daily = float(item.get('avgDailySales', item.get('avg_daily_sales', 0))) or 1.0
        price = float(item.get('price', 20.0))
        product = item.get('product', item.get('product_name', 'Unknown'))

        days_to_stockout = round(stock / avg_daily, 1) if avg_daily > 0 else 999
        overstock_threshold = avg_daily * 30 * 2.5

        if days_to_stockout <= 7 or stock <= 0:
            status = 'critical'
            rec = f"Reorder immediately — only {int(days_to_stockout)} days of stock remaining."
        elif days_to_stockout <= 14 or stock < reorder:
            status = 'warning'
            rec = "Stock below reorder level. Plan reorder within a week."
        elif stock > overstock_threshold:
            status = 'overstock'
            rec = f"Overstock detected — {int(days_to_stockout)} days of supply. Reduce next order."
        else:
            status = 'healthy'
            rec = f"Stock levels healthy. Next reorder in ~{int(max(days_to_stockout - 14, 0))} days."

        analyzed.append({
            "product": product,
            "stock": int(stock),
            "reorderLevel": int(reorder),
            "avgDailySales": round(avg_daily, 1),
            "daysToStockout": days_to_stockout if days_to_stockout < 999 else None,
            "status": status,
            "recommendation": rec,
            "revenueAtRisk": round(days_to_stockout * avg_daily * price, 0) if status == 'critical' else 0,
            "price": price,
        })

    order = {'critical': 0, 'warning': 1, 'healthy': 2, 'overstock': 3}
    analyzed.sort(key=lambda x: order.get(x['status'], 4))
    return analyzed
